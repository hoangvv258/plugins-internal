---
id: biglake-iceberg
name: BigLake & Iceberg Setup
description: Create BigLake Iceberg tables, configure metastore, enable multi-engine access for lakehouse architecture
---

# BigLake & Iceberg Setup

Create and manage BigLake Iceberg tables for a unified lakehouse architecture with multi-engine access.

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   Query Engines                      │
│  BigQuery  │  Spark  │  Trino  │  Presto  │  Flink  │
├─────────────────────────────────────────────────────┤
│              BigLake Metastore (Catalog)              │
│         Security Policies │ Schema │ Location        │
├─────────────────────────────────────────────────────┤
│              Apache Iceberg Table Format              │
│    ACID │ Schema Evolution │ Time Travel │ Compaction │
├─────────────────────────────────────────────────────┤
│              Cloud Storage (Data Lake)                │
│         Parquet Files │ Autoclass │ Multi-Region      │
└─────────────────────────────────────────────────────┘
```

## Step 1: Create Cloud Resource Connection

```bash
# Create connection for BigLake managed tables
bq mk --connection \
  --connection_type=CLOUD_RESOURCE \
  --location=US \
  --project_id=my-project \
  biglake-connection

# Get service account for the connection
bq show --connection my-project.US.biglake-connection
# Note the service account, grant it GCS access

# Grant Storage access
gsutil iam ch \
  serviceAccount:SA_EMAIL:objectAdmin \
  gs://my-lakehouse-bucket
```

## Step 2: Create BigLake Iceberg Table

### From SQL (BigQuery)
```sql
-- Create Iceberg table in BigQuery
CREATE TABLE `project.lakehouse.events`(
  event_id STRING NOT NULL,
  event_timestamp TIMESTAMP NOT NULL,
  user_id STRING,
  event_type STRING,
  properties JSON,
  revenue NUMERIC(10,2),
  country STRING
)
CLUSTER BY country, event_type
WITH CONNECTION `project.US.biglake-connection`
OPTIONS(
  file_format = 'PARQUET',
  table_format = 'ICEBERG',
  storage_uri = 'gs://my-lakehouse-bucket/iceberg/events'
);

-- Insert data
INSERT INTO `project.lakehouse.events`
SELECT * FROM `project.raw.events`
WHERE DATE(event_timestamp) = CURRENT_DATE();
```

### From Spark
```python
# Configure Spark with BigLake Metastore
spark = SparkSession.builder \
    .appName('iceberg-writer') \
    .config('spark.sql.catalog.blms', 'org.apache.iceberg.spark.SparkCatalog') \
    .config('spark.sql.catalog.blms.catalog-impl', 'org.apache.iceberg.gcp.biglake.BigLakeCatalog') \
    .config('spark.sql.catalog.blms.gcp_project', 'my-project') \
    .config('spark.sql.catalog.blms.gcp_location', 'US') \
    .config('spark.sql.catalog.blms.blms_catalog', 'my-catalog') \
    .config('spark.sql.catalog.blms.warehouse', 'gs://my-lakehouse-bucket/iceberg') \
    .getOrCreate()

# Create table via Spark
spark.sql('''
    CREATE TABLE blms.lakehouse.events (
        event_id STRING,
        event_timestamp TIMESTAMP,
        user_id STRING,
        event_type STRING,
        revenue DECIMAL(10,2),
        country STRING
    )
    USING iceberg
    PARTITIONED BY (days(event_timestamp))
''')
```

## Step 3: Schema Evolution

```sql
-- Add columns (backward compatible)
ALTER TABLE `project.lakehouse.events`
ADD COLUMN device_type STRING;

-- Rename columns
ALTER TABLE `project.lakehouse.events`
RENAME COLUMN properties TO event_properties;

-- Schema changes are automatically tracked in Iceberg metadata
```

## Step 4: Time Travel

```sql
-- Query historical snapshot
SELECT * FROM `project.lakehouse.events`
FOR SYSTEM_TIME AS OF '2026-04-01 00:00:00 UTC';

-- View snapshot history
SELECT * FROM `project.lakehouse.events.INFORMATION_SCHEMA.SNAPSHOTS`;
```

## Step 5: Table Maintenance

```sql
-- Compact small files (optimize read performance)
-- Iceberg handles this automatically, but you can trigger manually:
CALL `project.lakehouse`.system.rewrite_data_files('events');

-- Expire old snapshots (free storage)
CALL `project.lakehouse`.system.expire_snapshots('events', TIMESTAMP '2026-03-01');

-- Remove orphan files
CALL `project.lakehouse`.system.remove_orphan_files('events');
```

## Medallion Architecture

### Bronze Layer (Raw)
```sql
CREATE TABLE `project.lakehouse.bronze_events`
WITH CONNECTION `project.US.biglake-connection`
OPTIONS(file_format='PARQUET', table_format='ICEBERG',
        storage_uri='gs://lakehouse/bronze/events');
```

### Silver Layer (Cleaned)
```sql
CREATE TABLE `project.lakehouse.silver_events` AS
SELECT
  event_id,
  TIMESTAMP(event_timestamp) AS event_ts,
  LOWER(TRIM(user_id)) AS user_id,
  event_type,
  SAFE_CAST(revenue AS NUMERIC) AS revenue,
  country
FROM `project.lakehouse.bronze_events`
WHERE event_id IS NOT NULL;
```

### Gold Layer (Business-Ready)
```sql
CREATE TABLE `project.lakehouse.gold_daily_metrics` AS
SELECT
  DATE(event_ts) AS date,
  country,
  COUNT(DISTINCT user_id) AS unique_users,
  SUM(revenue) AS total_revenue,
  COUNT(*) AS total_events
FROM `project.lakehouse.silver_events`
GROUP BY 1, 2;
```

## Security

```sql
-- Row-level security (consistent across all engines)
CREATE ROW ACCESS POLICY region_filter
ON `project.lakehouse.events`
GRANT TO ('user:analyst@company.com')
FILTER USING (country IN ('US', 'CA'));

-- Column-level security via policy tags
ALTER TABLE `project.lakehouse.events`
ALTER COLUMN revenue
SET OPTIONS(policy_tags = '{"names":["projects/project/locations/US/taxonomies/123/policyTags/456"]}');
```

## Output

I'll provide:
- ✓ BigLake connection and table setup
- ✓ Iceberg table creation (SQL + Spark)
- ✓ Medallion architecture design
- ✓ Schema evolution strategy
- ✓ Security configuration
- ✓ Maintenance automation

---

Describe your lakehouse requirements and I'll design the architecture.
