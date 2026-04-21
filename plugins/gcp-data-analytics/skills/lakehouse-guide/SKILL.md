---
name: Lakehouse Guide
description: BigLake + Apache Iceberg lakehouse architecture — Dataplex governance, data quality, medallion architecture, multi-engine access
version: 1.0.0
---

# Lakehouse Guide Skill

Build a governed data lakehouse on Google Cloud using BigLake, Apache Iceberg, and Dataplex Universal Catalog.

## Lakehouse Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        CONSUMERS                              │
│  BI Dashboards  │  Data Science  │  ML Training  │  Apps     │
├──────────────────────────────────────────────────────────────┤
│                     QUERY ENGINES                             │
│  BigQuery  │  Dataproc Spark  │  Trino  │  Flink  │  Presto │
├──────────────────────────────────────────────────────────────┤
│                   GOVERNANCE LAYER                            │
│  Dataplex Universal Catalog                                   │
│  ┌─────────────┬───────────┬────────────┬──────────────────┐ │
│  │ Data Quality│  Lineage  │  Security  │ Business Glossary│ │
│  └─────────────┴───────────┴────────────┴──────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│                    TABLE FORMAT                               │
│  Apache Iceberg (ACID, Schema Evolution, Time Travel)         │
│  BigLake Metastore (Centralized Catalog)                      │
├──────────────────────────────────────────────────────────────┤
│                    STORAGE LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐│
│  │ Cloud Storage (GCS)                                       ││
│  │ Autoclass │ Multi-region │ Lifecycle │ Encryption        ││
│  └──────────────────────────────────────────────────────────┘│
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐                 │
│  │  Bronze  │→│  Silver  │→│     Gold     │  Medallion      │
│  │  (Raw)   │ │ (Clean)  │ │  (Business)  │  Architecture   │
│  └──────────┘ └──────────┘ └──────────────┘                 │
└──────────────────────────────────────────────────────────────┘
```

## Why Lakehouse?

| Property | Data Warehouse | Data Lake | **Lakehouse** |
|----------|---------------|-----------|---------------|
| Structure | Structured only | Any format | **Any format** |
| ACID | ✅ | ❌ | **✅ (Iceberg)** |
| Schema | Enforced | Schema-on-read | **Both** |
| Cost | High | Low | **Low (GCS)** |
| Performance | Fast | Variable | **Fast (BigQuery)** |
| Governance | Built-in | Manual | **Dataplex** |
| Multi-engine | Single | Multiple | **Multiple** |
| Time travel | Limited | ❌ | **✅ (Iceberg)** |

## Apache Iceberg on GCP

### Core Features
- **ACID Transactions** — Concurrent reads/writes safely
- **Schema Evolution** — Add, rename, reorder columns without rewriting data
- **Hidden Partitioning** — Partition transforms without user-visible partition columns
- **Time Travel** — Query data at any point in time
- **Snapshot Isolation** — Consistent reads during writes
- **File-level Operations** — Efficient delete, update, merge

### Create Iceberg Tables

#### Via BigQuery
```sql
CREATE TABLE `project.lakehouse.events`(
  event_id STRING NOT NULL,
  event_timestamp TIMESTAMP NOT NULL,
  user_id STRING,
  event_type STRING,
  revenue NUMERIC(10,2),
  country STRING,
  properties JSON
)
CLUSTER BY country, event_type
WITH CONNECTION `project.US.biglake-connection`
OPTIONS(
  file_format = 'PARQUET',
  table_format = 'ICEBERG',
  storage_uri = 'gs://lakehouse/iceberg/events'
);
```

#### Via Spark
```python
spark.sql("""
CREATE TABLE blms.lakehouse.events (
    event_id STRING,
    event_timestamp TIMESTAMP,
    user_id STRING,
    event_type STRING,
    revenue DECIMAL(10,2),
    country STRING
) USING iceberg
PARTITIONED BY (days(event_timestamp), country)
TBLPROPERTIES (
    'write.format.default' = 'parquet',
    'write.parquet.compression-codec' = 'snappy'
)
""")
```

### Schema Evolution
```sql
-- Add column (backward compatible)
ALTER TABLE `project.lakehouse.events` ADD COLUMN device STRING;

-- Rename column
ALTER TABLE `project.lakehouse.events` RENAME COLUMN properties TO metadata;

-- Change column type (widening only)
ALTER TABLE `project.lakehouse.events` ALTER COLUMN revenue SET DATA TYPE NUMERIC(12,2);
```

### Time Travel
```sql
-- Query at specific time
SELECT * FROM `project.lakehouse.events`
FOR SYSTEM_TIME AS OF '2026-04-01 00:00:00 UTC';

-- Query specific snapshot (Spark)
spark.read.option('snapshot-id', 1234567890).table('blms.lakehouse.events')
```

### Table Maintenance
```sql
-- Compact small files
OPTIMIZE `project.lakehouse.events`;

-- With compaction options (Spark)
from pyspark.sql import SparkSession
spark.sql("CALL blms.system.rewrite_data_files(table => 'lakehouse.events',"
          " strategy => 'sort', sort_order => 'country ASC NULLS LAST')")

-- Expire old snapshots (save storage)
spark.sql("CALL blms.system.expire_snapshots(table => 'lakehouse.events',"
          " older_than => TIMESTAMP '2026-03-01 00:00:00')")

-- Remove orphan files
spark.sql("CALL blms.system.remove_orphan_files(table => 'lakehouse.events')")
```

## Medallion Architecture

### Bronze Layer (Raw Data)
- **Purpose**: Land data exactly as received
- **Format**: Same as source (JSON, CSV, Avro, Parquet)
- **Processing**: Append-only, no transformations
- **Retention**: Long-term (years)

```sql
-- Bronze table: raw events from Pub/Sub
CREATE TABLE `project.lakehouse.bronze_events`
WITH CONNECTION `project.US.biglake-connection`
OPTIONS(file_format='PARQUET', table_format='ICEBERG',
        storage_uri='gs://lakehouse/bronze/events')
AS SELECT
  _PARTITIONTIME AS ingest_time,
  *
FROM `project.staging.raw_events`;
```

### Silver Layer (Cleaned & Standardized)
- **Purpose**: Cleaned, validated, deduplicated data
- **Format**: Standardized schema, consistent types
- **Processing**: CDC, dedup, type casting, validation
- **Retention**: Medium-term (months to years)

```sql
-- Silver table: cleaned events
CREATE TABLE `project.lakehouse.silver_events`
WITH CONNECTION `project.US.biglake-connection`
OPTIONS(file_format='PARQUET', table_format='ICEBERG',
        storage_uri='gs://lakehouse/silver/events')
AS SELECT
  event_id,
  TIMESTAMP(event_timestamp) AS event_ts,
  LOWER(TRIM(user_id)) AS user_id,
  event_type,
  SAFE_CAST(revenue AS NUMERIC(10,2)) AS revenue,
  UPPER(country) AS country
FROM `project.lakehouse.bronze_events`
WHERE event_id IS NOT NULL
  AND event_timestamp IS NOT NULL;
```

### Gold Layer (Business-Ready)
- **Purpose**: Aggregated, business-ready datasets
- **Format**: Optimized for queries, pre-aggregated
- **Processing**: Joins, aggregations, business logic
- **Retention**: As needed

```sql
-- Gold table: daily business metrics
CREATE TABLE `project.lakehouse.gold_daily_metrics`
WITH CONNECTION `project.US.biglake-connection`
OPTIONS(file_format='PARQUET', table_format='ICEBERG',
        storage_uri='gs://lakehouse/gold/daily_metrics')
AS SELECT
  DATE(event_ts) AS date,
  country,
  COUNT(DISTINCT user_id) AS unique_users,
  COUNT(*) AS total_events,
  SUM(revenue) AS total_revenue,
  AVG(revenue) AS avg_revenue
FROM `project.lakehouse.silver_events`
GROUP BY 1, 2;
```

## Dataplex Universal Catalog

### Data Discovery
```bash
# Search for data assets
gcloud dataplex entries search "events" --location=us-central1

# View entry details
gcloud dataplex entries describe ENTRY_ID --location=us-central1
```

### Data Quality Framework
```yaml
# Quality rules per layer
bronze_rules:
  - completeness: event_id NOT NULL (100%)
  - freshness: data < 1 hour old

silver_rules:
  - completeness: all required fields NOT NULL (100%)
  - uniqueness: event_id unique (100%)
  - validity: revenue >= 0 (99.9%)
  - consistency: country IN allowed_set (99%)
  - format: email matches regex (95%)

gold_rules:
  - accuracy: totals match silver aggregations (100%)
  - timeliness: updated within SLA (100%)
  - completeness: no missing dates (100%)
```

### Data Lineage
```
Pub/Sub (source)
  ↓ [Dataflow pipeline]
Bronze Table (raw)
  ↓ [Scheduled BigQuery query]
Silver Table (clean)
  ↓ [Scheduled BigQuery query]  
Gold Table (business)
  ↓ [BI Engine cache]
Looker Dashboard
```

## Security Framework

### Multi-Layer Security
```
Layer 1: IAM (Who can access what resources)
Layer 2: VPC Service Controls (Network perimeter)
Layer 3: Column-Level Security (Which columns are visible)
Layer 4: Row-Level Security (Which rows are visible)
Layer 5: Data Masking (What values are shown)
Layer 6: Audit Logging (Who accessed what when)
```

### Implementation
```sql
-- Row-level security
CREATE ROW ACCESS POLICY region_filter
ON `project.lakehouse.silver_events`
GRANT TO ('group:us-analysts@company.com')
FILTER USING (country = 'US');

-- Column-level security (policy tags)
ALTER TABLE `project.lakehouse.silver_events`
ALTER COLUMN user_id
SET OPTIONS(
  policy_tags = '{"names":["projects/p/locations/US/taxonomies/T/policyTags/PII"]}'
);

-- Dynamic data masking
ALTER TABLE `project.lakehouse.silver_events`
ALTER COLUMN email
SET DATA MASKING POLICY mask_email
USING MASK(CONCAT(LEFT(email, 2), '***@', SPLIT(email, '@')[OFFSET(1)]));
```

## Storage Optimization

### GCS Best Practices
| Strategy | Impact | How |
|----------|--------|-----|
| Autoclass | 30-50% storage savings | Automatic tiering |
| Co-locate | Avoid transfer fees | Same region as compute |
| Parquet format | 70-80% vs JSON | Columnar compression |
| Iceberg compaction | 30-50% read improvement | Merge small files |
| Snapshot expiry | Free unused storage | Remove old snapshots |

### File Organization
```
gs://lakehouse/
├── bronze/
│   ├── events/           # Raw events (Iceberg)
│   ├── users/            # Raw user data
│   └── transactions/     # Raw transactions
├── silver/
│   ├── events/           # Cleaned events
│   ├── users/            # Standardized users
│   └── transactions/     # Validated transactions
├── gold/
│   ├── daily_metrics/    # Pre-aggregated metrics
│   ├── user_segments/    # ML-derived segments
│   └── revenue_reports/  # Business reports
└── metadata/
    └── iceberg/          # Iceberg metadata files
```

## Multi-Engine Access

### Same data, any engine
```python
# BigQuery
bq query "SELECT * FROM project.lakehouse.events WHERE country = 'US'"

# Spark (Dataproc)
spark.read.table('blms.lakehouse.events').filter("country = 'US'")

# Trino
SELECT * FROM biglake.lakehouse.events WHERE country = 'US';

# Security policies enforced consistently across ALL engines
```

## Operational Runbook

### Daily Operations
1. Monitor data quality scan results
2. Check pipeline SLAs (freshness)
3. Review failed ingestion jobs
4. Monitor storage costs and growth

### Weekly Operations
1. Run Iceberg table maintenance (compaction)
2. Review data lineage for changes
3. Audit access logs
4. Update business glossary terms

### Monthly Operations
1. Expire old Iceberg snapshots
2. Review storage tier optimization
3. Audit governance compliance
4. Capacity planning review

## Resources

- [BigLake Documentation](https://cloud.google.com/bigquery/docs/biglake-intro)
- [Apache Iceberg on GCP](https://cloud.google.com/bigquery/docs/iceberg-tables)
- [Dataplex Documentation](https://cloud.google.com/dataplex/docs)
- [Data Quality](https://cloud.google.com/dataplex/docs/data-quality-overview)
- [Data Lineage](https://cloud.google.com/dataplex/docs/data-lineage)
- [BigLake Metastore](https://cloud.google.com/bigquery/docs/biglake-metastore)
