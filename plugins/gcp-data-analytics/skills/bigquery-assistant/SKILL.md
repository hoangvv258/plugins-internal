---
name: bigquery-assistant
description: This skill should be used when the user asks to "write a BigQuery query", "optimize BigQuery SQL", "create graph queries with GQL", "set up continuous queries", "use AI functions in BigQuery", "design BigQuery schema", "use pipe syntax", or mentions BigQuery performance, cost optimization, partitioning, clustering, or Search Index.
version: 2.0.0
---

# BigQuery Assistant Skill

Comprehensive support for working with Google Cloud BigQuery for data analytics, warehousing, graph analytics, real-time processing, and ML.

## BigQuery Graph (GQL)

### Graph Concepts
- **Property Graph** — Model data as nodes and edges over existing tables
- **GQL (Graph Query Language)** — ISO standard query language for graphs
- **Use Cases** — Social networks, fraud detection, supply chains, knowledge graphs

### Creating a Graph
```sql
CREATE PROPERTY GRAPH FinancialGraph
  NODE TABLES (
    accounts AS Account
      KEY(account_id)
      PROPERTIES(name, country, balance)
  )
  EDGE TABLES (
    transfers AS Transfer
      KEY(transfer_id)
      SOURCE KEY(sender_id) REFERENCES Account(account_id)
      DESTINATION KEY(receiver_id) REFERENCES Account(account_id)
      PROPERTIES(amount, timestamp, currency)
  );
```

### Graph Query Examples
```sql
-- Find all paths between two accounts (fraud detection)
GRAPH FinancialGraph
MATCH p = (a:Account)-[:Transfer]->{1,5}(b:Account)
WHERE a.account_id = 'A001' AND b.account_id = 'B999'
RETURN p;

-- Find accounts with most connections
GRAPH FinancialGraph
MATCH (a:Account)-[t:Transfer]->()
RETURN a.name, COUNT(t) AS transfer_count
ORDER BY transfer_count DESC
LIMIT 10;

-- Shortest path
GRAPH FinancialGraph
MATCH p = SHORTEST_PATH((a:Account)-[:Transfer]->+(b:Account))
WHERE a.account_id = 'A001' AND b.account_id = 'B999'
RETURN p;
```

### Graph Best Practices
- Start path traversals from low-cardinality nodes
- Use explicit labels to limit search space
- Apply WHERE filters as early as possible
- Limit path length with `{1,N}` bounds
- Combine with standard SQL using subqueries

## Continuous Queries

### Overview
Continuous queries transform BigQuery into an event-driven processing engine:
- Process data the moment it arrives via Storage Write API
- Output to BigQuery tables, Pub/Sub, Bigtable, or Spanner
- Support windowed aggregations (tumbling, session, sliding)
- Stateful JOINs with dimension tables
- Dynamic slot autoscaling

### Window Types
| Window | SQL | Use Case |
|--------|-----|----------|
| Tumbling | `TUMBLE('1 MINUTE')` | Fixed non-overlapping intervals |
| Session | `SESSION('10 MINUTES')` | Activity-based gaps |
| Sliding | `HOP('5 MIN', '1 MIN')` | Moving averages |

## Pipe Syntax

A more concise, composable SQL syntax using `|>`:

```sql
-- Traditional SQL
SELECT country, COUNT(*) AS cnt
FROM dataset.events
WHERE event_type = 'purchase'
GROUP BY country
ORDER BY cnt DESC
LIMIT 10;

-- Equivalent Pipe Syntax
FROM dataset.events
|> WHERE event_type = 'purchase'
|> AGGREGATE COUNT(*) AS cnt GROUP BY country
|> ORDER BY cnt DESC
|> LIMIT 10;
```

### Pipe Syntax Benefits
- Read top-to-bottom (no inside-out parsing)
- Chain operations naturally
- Easier to compose dynamically
- Mix with standard SQL (CTEs, subqueries)

## AI & ML Functions

### Managed AI Functions (No Model Required)
```sql
-- AI.GENERATE — Text generation
SELECT AI.GENERATE('Summarize: ' || article_text) AS summary
FROM dataset.articles;

-- AI.CLASSIFY — Classification
SELECT AI.CLASSIFY(review, ['positive', 'negative', 'neutral']) AS sentiment
FROM dataset.reviews;

-- AI.IF — Boolean AI check (cost-efficient)
SELECT AI.IF(comment, 'Is this a complaint?') AS is_complaint
FROM dataset.comments;

-- AI.FORECAST — Time-series prediction
SELECT * FROM AI.FORECAST(
  MODEL dataset.forecast_model,
  STRUCT(30 AS horizon));

-- AI.DETECT_ANOMALIES — Anomaly detection
SELECT * FROM AI.DETECT_ANOMALIES(
  MODEL dataset.anomaly_model,
  TABLE dataset.metrics);

-- AI.KEY_DRIVERS — Segment analysis
SELECT * FROM AI.KEY_DRIVERS(
  TABLE dataset.metrics,
  'revenue',
  STRUCT('2026-Q1' AS current, '2025-Q4' AS baseline));
```

### Vectorized Python UDFs
```sql
-- High-performance UDFs using Apache Arrow
CREATE FUNCTION dataset.vectorized_transform(x ARRAY<FLOAT64>)
RETURNS ARRAY<FLOAT64>
LANGUAGE PYTHON
OPTIONS(runtime_version = '3.11', vectorized = TRUE)
AS r'''
import numpy as np
def fn(x):
    return np.array(x) * 2.0  # Operates on Arrow arrays
return fn(x)
''';
```

## Advanced Topics

### Analytical Functions & Window Operations
- OVER() clauses for complex aggregations
- ROW_NUMBER(), RANK(), DENSE_RANK() for ranking
- LAG(), LEAD() for time-series analysis
- FIRST_VALUE(), LAST_VALUE() for windowing
- NTILE() for percentile bucketing
- Running totals and moving averages

### Nested Data Structures
- STRUCT for complex objects
- ARRAY for lists and aggregations
- UNNEST() for flattening arrays
- ARRAY_AGG() for array construction
- JSON type for semi-structured data
- SEARCH() for full-text search via Search Index

### Performance at Scale
- Query patterns for 100TB+ datasets
- Slot reservation strategies (flex, monthly, annual)
- BI Engine caching for sub-second dashboards
- Materialized views for pre-computed aggregations
- Query scheduling and optimization
- History-based query optimization

### Cost Management
- Slot vs on-demand cost comparison
- Data lifecycle and archival policies
- Monthly cost forecasting via INFORMATION_SCHEMA
- Budget controls and alerts
- Reserved capacity planning
- Flex slots for variable workloads

### Advanced Loading
- Storage Write API for high-throughput streaming
- Change Data Capture (CDC) patterns
- Schema evolution strategies
- Data quality validation (Dataplex integration)
- Error handling and DLQ patterns

### Security & Compliance
- Column-level security (CLS) with policy tags
- Row-level security (RLS) with access policies
- Dynamic data masking
- VPC Service Controls
- Audit logging (INFORMATION_SCHEMA.JOBS)
- HIPAA/SOC2/PCI-DSS compliance

## BigLake Integration

### Querying Lakehouse Data
```sql
-- Query BigLake Iceberg table (same SQL as managed tables)
SELECT * FROM `project.lakehouse.events`
WHERE event_date = '2026-04-01';

-- Cross-engine: same data accessible from Spark, Trino, etc.
-- Security policies are enforced consistently
```

## Real-World Architectures

### Multi-Tenant SaaS Platform
- Separate datasets per tenant for isolation
- Shared dimension tables for common data
- Row-level security for data access
- Cost allocation via labels and reservations

### Real-Time Analytics
- Continuous queries from Pub/Sub → BigQuery
- Materialized views for dashboards
- BI Engine for sub-second queries
- BigLake for historical data

### Data Lakehouse
- Bronze (raw) → Silver (cleaned) → Gold (business) layers
- BigLake Iceberg for open format storage
- Schema versioning and evolution
- Dataplex for governance and lineage

### ML Feature Store
- BigQuery ML for feature engineering
- High-throughput feature serving via Bigtable
- Historical snapshots for training
- Point-in-time correctness

## Cost Optimization Playbook

1. **Analyze Usage** — Top queries by bytes scanned, redundant patterns, growth trends
2. **Optimize Queries** — Partition/cluster filters, project columns, approximate functions
3. **Architectural Changes** — Materialized views, incremental loads, continuous queries
4. **Reserved Capacity** — Break-even analysis, flex slots vs annual commitments
5. **Archive Strategy** — BigLake for cold data, Autoclass storage, TTL policies

## Tools & Commands

```bash
# Top queries by cost (last 7 days)
bq query --use_legacy_sql=false "
SELECT
  query,
  total_bytes_billed / POW(1024, 3) AS gb_billed,
  total_slot_ms / 1000 AS slot_seconds,
  creation_time
FROM \`region-us\`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND job_type = 'QUERY'
ORDER BY total_bytes_billed DESC
LIMIT 20"

# Reservation setup
bq mk --reservation \
  --project_id=project \
  --location=US \
  --slot_capacity=500 \
  --edition=enterprise \
  analytics-reservation

# Export to Parquet
bq extract \
  --destination_format=PARQUET \
  --compression=SNAPPY \
  project:dataset.table \
  gs://bucket/export/data-*.parquet
```

## Troubleshooting Guide

| Issue | Cause | Solution |
|-------|-------|----------|
| Slow query | Missing partition/cluster filter | Add WHERE on partition column |
| High costs | SELECT * or wide date range | Project columns, reduce range |
| Quota exceeded | Too many concurrent jobs | Consolidate, use batch API |
| Out of memory | Large array aggregations | Use approximate functions or LIMIT |
| Timeout (6h) | Query too complex | Consider Dataflow or break into stages |
| Slot contention | Not enough reservation | Increase slots or use flex slots |
| Graph slow | High-cardinality start nodes | Start from low-cardinality, add filters |
| CQ lagging | Insufficient slots | Increase reservation, optimize query |

## Resources

- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [BigQuery Graph](https://cloud.google.com/bigquery/docs/graph)
- [Continuous Queries](https://cloud.google.com/bigquery/docs/continuous-queries)
- [BigQuery ML](https://cloud.google.com/bigquery/docs/bqml-introduction)
- [Pipe Syntax](https://cloud.google.com/bigquery/docs/reference/standard-sql/pipe-syntax)
- [AI Functions](https://cloud.google.com/bigquery/docs/ai-functions)
- [Cost Optimization](https://cloud.google.com/bigquery/docs/best-practices-costs)
- [Performance Tuning](https://cloud.google.com/bigquery/docs/best-practices-performance)
