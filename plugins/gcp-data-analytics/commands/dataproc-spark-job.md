---
id: dataproc-spark-job
name: Dataproc Spark Job
description: Submit and optimize Dataproc Serverless Spark jobs — PySpark, SparkSQL, BigQuery integration
---

# Dataproc Spark Job Designer

Submit and optimize Apache Spark jobs on Google Cloud Dataproc — Serverless or persistent clusters.

## Serverless Spark Batch Job

### PySpark ETL Job
```python
# etl_job.py
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder \
    .appName('daily-etl') \
    .getOrCreate()

# Read from BigQuery
raw_df = spark.read.format('bigquery') \
    .option('table', 'project.raw.events') \
    .option('filter', "DATE(event_timestamp) = '2026-04-01'") \
    .load()

# Transform
clean_df = raw_df \
    .filter(F.col('event_id').isNotNull()) \
    .withColumn('event_date', F.to_date('event_timestamp')) \
    .withColumn('user_id', F.lower(F.trim('user_id'))) \
    .withColumn('revenue', F.col('revenue').cast('decimal(10,2)')) \
    .dropDuplicates(['event_id'])

# Aggregate
daily_summary = clean_df \
    .groupBy('event_date', 'country', 'event_type') \
    .agg(
        F.count('*').alias('event_count'),
        F.sum('revenue').alias('total_revenue'),
        F.countDistinct('user_id').alias('unique_users'),
    )

# Write to BigQuery
daily_summary.write.format('bigquery') \
    .option('table', 'project.analytics.daily_summary') \
    .option('temporaryGcsBucket', 'spark-temp-bucket') \
    .mode('append') \
    .save()

spark.stop()
```

### Submit Serverless Batch
```bash
# Simple submission
gcloud dataproc batches submit pyspark \
  gs://scripts/etl_job.py \
  --region=us-central1 \
  --subnet=default \
  --service-account=spark-sa@project.iam.gserviceaccount.com \
  --version=2.2 \
  --properties=spark.executor.memory=8g,spark.sql.adaptive.enabled=true \
  -- --date=2026-04-01

# With custom container
gcloud dataproc batches submit pyspark \
  gs://scripts/etl_job.py \
  --region=us-central1 \
  --container-image=gcr.io/project/spark-custom:latest \
  --properties=spark.executor.instances=10 \
  --jars=gs://jars/bigquery-connector.jar
```

### SparkSQL Job
```bash
gcloud dataproc batches submit spark-sql \
  --region=us-central1 \
  --file=gs://scripts/transform.sql \
  --vars=input_date=2026-04-01,output_table=project.dataset.output
```

## Interactive Spark Sessions

```bash
# Create interactive session via Spark Connect
gcloud dataproc sessions create spark my-session \
  --region=us-central1 \
  --version=2.2 \
  --properties=spark.executor.memory=4g

# Connect from notebook (Colab/Vertex Workbench)
# Use the session ID in your notebook config
```

## BigQuery Integration Patterns

### Read BigQuery → Process → Write BigQuery
```python
# High-throughput read via Storage API
df = spark.read.format('bigquery') \
    .option('table', 'project.dataset.large_table') \
    .option('readDataFormat', 'ARROW') \
    .option('parallelism', 20) \
    .load()

# Process with Spark
result = df.filter(...).groupBy(...).agg(...)

# High-throughput write via Storage Write API
result.write.format('bigquery') \
    .option('table', 'project.dataset.output') \
    .option('writeMethod', 'direct') \
    .mode('overwrite') \
    .save()
```

### Read BigQuery → Write to Iceberg
```python
# Read from BigQuery
df = spark.read.format('bigquery') \
    .option('table', 'project.dataset.events') \
    .load()

# Write as Iceberg table
df.writeTo('catalog.db.events_iceberg') \
    .partitionedBy('event_date') \
    .createOrReplace()
```

## Performance Tuning

```bash
# Compute tiers
--properties=spark.dataproc.executor.compute.tier=premium  # CPU-intensive
--properties=spark.dataproc.executor.compute.tier=standard  # Balanced (default)

# Memory tuning
--properties=spark.executor.memory=8g,spark.executor.memoryOverhead=2g

# Adaptive Query Execution (AQE)
--properties=spark.sql.adaptive.enabled=true,spark.sql.adaptive.coalescePartitions.enabled=true

# Shuffle optimization
--properties=spark.sql.shuffle.partitions=200,spark.shuffle.compress=true
```

## Cost Optimization

| Strategy | Savings | How |
|----------|---------|-----|
| Serverless vs Cluster | 30-60% | No idle costs |
| Standard compute tier | 20-40% | vs Premium tier |
| Reduce executor memory | 10-30% | Right-size memory |
| AQE enabled | 10-20% | Adaptive partitioning |
| ARROW read format | 20-40% | Faster BigQuery reads |

## Monitoring

```bash
# List batch jobs
gcloud dataproc batches list --region=us-central1

# Describe job
gcloud dataproc batches describe BATCH_ID --region=us-central1

# View logs
gcloud logging read \
  'resource.type="cloud_dataproc_batch" AND resource.labels.batch_id="BATCH_ID"' \
  --limit=50

# Persistent History Server for completed job metrics
gcloud dataproc clusters create phs-cluster \
  --region=us-central1 \
  --single-node \
  --enable-component-gateway \
  --properties=spark.history.fs.logDirectory=gs://spark-history/
```

## Output

I'll provide:
- ✓ PySpark/SparkSQL job code
- ✓ Submission commands (Serverless or cluster)
- ✓ BigQuery integration configuration
- ✓ Performance tuning properties
- ✓ Cost estimation

---

Describe your Spark workload and I'll design the job.
