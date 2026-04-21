---
id: bigquery-schema-design
name: BigQuery Schema Designer
description: Design optimal BigQuery table schemas — partitioning, clustering, BigLake Iceberg, nested types, Search Index
---

# BigQuery Schema Designer

Let me help you design an optimal table schema for your BigQuery dataset, including support for BigLake Iceberg tables, Search Indexes, and modern data types.

## Schema Design Considerations

1. **Data Types** — Choose efficient types (INT64 vs FLOAT64, NUMERIC for money)
2. **Partitioning** — Divide data for query performance and cost
3. **Clustering** — Physically order data for faster access (up to 4 columns)
4. **Nested Fields** — Use STRUCTs and ARRAYs for denormalization
5. **JSON Type** — Native JSON columns for semi-structured data
6. **Search Index** — Full-text search and efficient SEARCH operations

## Partitioning Strategies

### Time-based (Most Common)
```sql
-- Partition by DATE/TIMESTAMP column
PARTITION BY DATE(event_timestamp)

-- Hourly partitioning (high-volume)
PARTITION BY TIMESTAMP_TRUNC(event_timestamp, HOUR)

-- Monthly partitioning (low-volume)
PARTITION BY DATE_TRUNC(created_date, MONTH)
```

### Integer Range
```sql
-- Partition by user_id ranges
PARTITION BY RANGE_BUCKET(user_id, GENERATE_ARRAY(0, 1000000, 1000))
```

### Ingestion Time
```sql
-- Automatic partitioning as data arrives
PARTITION BY _PARTITIONDATE
```

## Clustering Best Practices

Choose clustering columns based on:
- Query filter columns (frequent WHERE clauses)
- Join keys (JOIN columns)
- Aggregate dimensions (GROUP BY columns)
- Up to 4 columns, order by selectivity (high → low)

## Example Designs

### E-commerce Events (Managed Table)
```sql
CREATE OR REPLACE TABLE dataset.events (
  event_timestamp TIMESTAMP NOT NULL,
  event_id STRING NOT NULL,
  user_id STRING,
  event_type STRING,
  properties JSON,
  revenue NUMERIC(10,2),
  country STRING,
  device_type STRING
)
PARTITION BY DATE(event_timestamp)
CLUSTER BY country, event_type, user_id
OPTIONS(
  require_partition_filter = TRUE,
  partition_expiration_days = 365
);
```

### User Dimension with Nested Data
```sql
CREATE OR REPLACE TABLE dataset.users (
  user_id STRING NOT NULL,
  created_date DATE,
  email STRING,
  region STRING,
  segment STRING,
  ltv NUMERIC(12,2),
  profile STRUCT<
    first_name STRING,
    last_name STRING,
    age INT64,
    preferences ARRAY<STRING>
  >,
  activity_history ARRAY<STRUCT<
    action STRING,
    timestamp TIMESTAMP,
    metadata JSON
  >>
)
CLUSTER BY region, segment;
```

### BigLake Iceberg Table (Lakehouse)
```sql
CREATE TABLE dataset.lakehouse_events
WITH CONNECTION `project.region.connection_id`
OPTIONS(
  file_format = 'PARQUET',
  table_format = 'ICEBERG',
  storage_uri = 'gs://bucket/iceberg/events'
)
AS SELECT * FROM dataset.events;
```

### Search Index for Full-Text Search
```sql
-- Create search index on text columns
CREATE SEARCH INDEX idx_products
ON dataset.products(product_name, description, tags);

-- Query using SEARCH function
SELECT *
FROM dataset.products
WHERE SEARCH(product_name, 'wireless bluetooth headphones');
```

### Time-Series IoT Data
```sql
CREATE OR REPLACE TABLE dataset.sensor_readings (
  device_id STRING NOT NULL,
  reading_timestamp TIMESTAMP NOT NULL,
  sensor_type STRING,
  value FLOAT64,
  metadata JSON,
  location GEOGRAPHY
)
PARTITION BY TIMESTAMP_TRUNC(reading_timestamp, HOUR)
CLUSTER BY device_id, sensor_type
OPTIONS(
  partition_expiration_days = 90,
  description = 'IoT sensor readings with hourly partitioning'
);
```

### Materialized View
```sql
CREATE MATERIALIZED VIEW dataset.daily_revenue_mv
PARTITION BY event_date
CLUSTER BY country
AS
SELECT
  DATE(event_timestamp) AS event_date,
  country,
  COUNT(*) AS event_count,
  SUM(revenue) AS total_revenue
FROM dataset.events
GROUP BY 1, 2;
```

## Anti-Patterns to Avoid

| Don't | Do Instead |
|-------|-----------|
| `SELECT *` on large tables | Project only needed columns |
| No partition filter | Always filter on partition column |
| Cluster by high-cardinality first | Cluster by filter columns first |
| String for dates | Use DATE/TIMESTAMP native types |
| Flat tables with repetitive data | Use STRUCT/ARRAY for nested data |
| External tables for frequent queries | Use managed or BigLake Iceberg tables |

---

Describe your data and use case for schema design recommendations.
