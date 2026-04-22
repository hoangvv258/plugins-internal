---
name: dataproc-guide
description: This skill should be used when the user asks to "submit a Spark job on Dataproc", "use Dataproc Serverless", "read BigQuery from PySpark", "tune Spark performance", "configure Dataproc clusters", "use SparkSQL with BigQuery", or mentions Dataproc, PySpark, SparkSQL, Spark Connect, BigQuery-Spark connector, or Lightning Engine.
version: 1.0.0
---

# Dataproc Guide Skill

Run Apache Spark workloads on Google Cloud Dataproc — Serverless or managed clusters, with deep BigQuery integration.

## Serverless vs Clusters

| Feature | Dataproc Serverless | Dataproc Clusters |
|---------|-------------------|-------------------|
| Management | Zero — fully managed | You manage cluster lifecycle |
| Startup | ~60 seconds | 2-5 minutes |
| Scaling | Automatic | Manual or autoscaling policies |
| Cost | Per-job (no idle) | Per-cluster (idle possible) |
| Use Case | Batch ETL, interactive | Long-running, specialized |
| Customization | Docker images | Init actions, custom images |
| Best For | Most workloads | Persistent services, notebooks |

## Dataproc Serverless

### Batch Jobs

#### PySpark Job
```python
# job.py — Standard PySpark ETL
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import *

spark = SparkSession.builder.appName('etl-job').getOrCreate()

# Read from BigQuery via Storage Read API
df = spark.read.format('bigquery') \
    .option('table', 'project.raw.events') \
    .option('readDataFormat', 'ARROW') \
    .option('filter', "DATE(event_timestamp) = '2026-04-01'") \
    .load()

# Transform
result = df \
    .filter(F.col('event_id').isNotNull()) \
    .withColumn('event_date', F.to_date('event_timestamp')) \
    .withColumn('user_id', F.lower(F.trim('user_id'))) \
    .withColumn('revenue', F.col('revenue').cast('decimal(10,2)')) \
    .dropDuplicates(['event_id']) \
    .groupBy('event_date', 'country') \
    .agg(
        F.count('*').alias('events'),
        F.sum('revenue').alias('revenue'),
        F.countDistinct('user_id').alias('users'),
    )

# Write back to BigQuery (direct write via Storage Write API)
result.write.format('bigquery') \
    .option('table', 'project.analytics.daily_metrics') \
    .option('writeMethod', 'direct') \
    .mode('append') \
    .save()

spark.stop()
```

#### Submit Job
```bash
gcloud dataproc batches submit pyspark gs://scripts/job.py \
  --region=us-central1 \
  --subnet=default \
  --service-account=spark@project.iam.gserviceaccount.com \
  --version=2.2 \
  --properties="\
spark.executor.memory=8g,\
spark.executor.cores=4,\
spark.sql.adaptive.enabled=true,\
spark.sql.adaptive.coalescePartitions.enabled=true,\
spark.dynamicAllocation.enabled=true" \
  --jars=gs://spark-lib/bigquery-connector-latest.jar \
  -- --date=2026-04-01 --output=project.analytics.daily_metrics
```

#### SparkSQL Job
```sql
-- transform.sql
CREATE TEMPORARY VIEW raw_events USING bigquery
OPTIONS (table 'project.raw.events');

INSERT INTO bigquery.`project.analytics.clean_events`
SELECT
  event_id,
  CAST(event_timestamp AS TIMESTAMP) AS event_ts,
  LOWER(TRIM(user_id)) AS user_id,
  event_type,
  CAST(revenue AS DECIMAL(10,2)) AS revenue,
  country
FROM raw_events
WHERE event_id IS NOT NULL
  AND DATE(event_timestamp) = '${input_date}';
```

```bash
gcloud dataproc batches submit spark-sql \
  --region=us-central1 \
  --file=gs://scripts/transform.sql \
  --vars=input_date=2026-04-01
```

### Interactive Sessions (Spark Connect)
```bash
# Create session
gcloud dataproc sessions create spark my-session \
  --region=us-central1 \
  --version=2.2 \
  --properties=spark.executor.memory=4g,spark.executor.cores=2

# Connect from notebook (returns session URI)
# Use in Colab Enterprise, Vertex Workbench, or JupyterLab
```

```python
# In notebook
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .remote('sc://SESSION_HOST:443/;use_ssl=true;token=TOKEN') \
    .getOrCreate()

df = spark.read.format('bigquery').option('table', 'project.dataset.table').load()
df.show()
```

## BigQuery Integration

### BigQuery Connector Configuration
```python
# Read with filtering (server-side pushdown)
df = spark.read.format('bigquery') \
    .option('table', 'project.dataset.large_table') \
    .option('readDataFormat', 'ARROW')  \   # Fastest format
    .option('parallelism', 20) \             # Number of read streams
    .option('viewsEnabled', True) \          # Read from views
    .option('materializationDataset', 'temp') \  # For view materialization
    .option('filter', "date >= '2026-01-01'") \  # Server-side filter
    .load()

# Write with direct method (fastest)
df.write.format('bigquery') \
    .option('table', 'project.dataset.output') \
    .option('writeMethod', 'direct') \       # Storage Write API
    .option('createDisposition', 'CREATE_IF_NEEDED') \
    .option('partitionField', 'event_date') \
    .option('clusteredFields', 'country,event_type') \
    .mode('append') \
    .save()
```

### Reading from BigLake Iceberg
```python
# Configure Iceberg catalog
spark = SparkSession.builder \
    .config('spark.sql.catalog.blms', 'org.apache.iceberg.spark.SparkCatalog') \
    .config('spark.sql.catalog.blms.catalog-impl', 
            'org.apache.iceberg.gcp.biglake.BigLakeCatalog') \
    .config('spark.sql.catalog.blms.gcp_project', 'project') \
    .config('spark.sql.catalog.blms.gcp_location', 'US') \
    .config('spark.sql.catalog.blms.blms_catalog', 'catalog') \
    .config('spark.sql.catalog.blms.warehouse', 'gs://lakehouse/iceberg') \
    .getOrCreate()

# Read Iceberg table
df = spark.read.table('blms.database.events')

# Time travel
df_historical = spark.read \
    .option('as-of-timestamp', '2026-04-01T00:00:00') \
    .table('blms.database.events')

# Write to Iceberg
df.writeTo('blms.database.output').append()
```

## Performance Tuning

### Compute Tiers
| Tier | Use Case | Cost |
|------|----------|------|
| Standard | Balanced workloads, memory-heavy | Lower |
| Premium | CPU-intensive, faster per-core | ~30% higher |

### Key Spark Properties
```properties
# Memory
spark.executor.memory=8g
spark.executor.memoryOverhead=2g
spark.driver.memory=4g

# Parallelism
spark.executor.cores=4
spark.sql.shuffle.partitions=200
spark.default.parallelism=200

# Adaptive Query Execution (recommended)
spark.sql.adaptive.enabled=true
spark.sql.adaptive.coalescePartitions.enabled=true
spark.sql.adaptive.skewJoin.enabled=true

# Dynamic allocation
spark.dynamicAllocation.enabled=true
spark.dynamicAllocation.minExecutors=2
spark.dynamicAllocation.maxExecutors=50

# Compression
spark.sql.parquet.compression.codec=snappy
spark.shuffle.compress=true
```

### Common Optimizations
| Problem | Solution |
|---------|----------|
| Data skew | Salting keys, repartition, AQE skew join |
| Small files | Coalesce output, adaptive coalesce |
| Slow joins | Broadcast small tables (<100MB) |
| OOM errors | Increase memory, reduce partition size |
| Slow reads | Use ARROW format, server-side filter |
| Slow writes | Use direct write method, batch inserts |

## Monitoring & Debugging

### Persistent History Server
```bash
# Create PHS (required for debugging completed jobs)
gcloud dataproc clusters create phs \
  --region=us-central1 \
  --single-node \
  --enable-component-gateway \
  --properties="\
spark.history.fs.logDirectory=gs://spark-history/logs,\
spark.eventLog.dir=gs://spark-history/logs"

# Access Spark UI via component gateway URL
```

### Logs
```bash
# View batch job logs
gcloud logging read \
  'resource.type="cloud_dataproc_batch" AND resource.labels.batch_id="BATCH_ID"' \
  --project=project --limit=100

# View driver output
gcloud dataproc batches describe BATCH_ID --region=us-central1
```

## Migration Guide

### From HDFS to GCS
```python
# Replace HDFS paths
# Before: hdfs:///data/events/
# After:  gs://bucket/data/events/

# Replace Hive Metastore
# Use Dataproc Metastore service or BigLake Metastore
```

### From EMR to Dataproc
| EMR | Dataproc Equivalent |
|-----|-------------------|
| EMR Serverless | Dataproc Serverless |
| EMR Cluster | Dataproc Cluster |
| S3 | Cloud Storage |
| Glue Catalog | Dataproc Metastore |
| Step Functions | Cloud Composer |
| CloudWatch | Cloud Monitoring |

## Cost Optimization

| Strategy | Savings | Notes |
|----------|---------|-------|
| Serverless for batch | 30-60% | No idle costs |
| Spot VMs (clusters) | 60-91% | For fault-tolerant jobs |
| Standard compute tier | 20-40% | vs Premium |
| Right-size memory | 10-30% | Don't over-provision |
| AQE enabled | 10-20% | Adaptive optimization |
| Co-locate with GCS | 5-10% | Same region = no transfer fees |

## Resources

- [Dataproc Documentation](https://cloud.google.com/dataproc/docs)
- [Dataproc Serverless](https://cloud.google.com/dataproc-serverless/docs)
- [BigQuery Connector](https://cloud.google.com/dataproc/docs/tutorials/bigquery-connector-spark-example)
- [Spark Configuration](https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/cluster-properties)
- [Pricing](https://cloud.google.com/dataproc/pricing)
