---
description: Set up real-time continuous queries — event-driven SQL, stateful processing, output to Pub/Sub, Bigtable, Spanner
---

# BigQuery Continuous Query Designer

Design and deploy real-time continuous queries that process data the moment it arrives in BigQuery.

## How Continuous Queries Work

```
Data Ingestion                    Continuous Query              Output
─────────────────                ──────────────────            ────────
Storage Write API ─────┐         ┌──────────────┐          ┌→ BigQuery Table
INSERT DML      ──────→│ BigQuery │ SELECT ... │─────────→├→ Pub/Sub Topic
Streaming Insert ─────┘│ Table   │ WHERE ...  │          ├→ Bigtable Table
                        │         │ GROUP BY   │          └→ Spanner Table
                        └─────────└──────────────┘
```

## Basic Continuous Query

### Simple Aggregation
```sql
-- Count events per minute, output to BigQuery
CREATE CONTINUOUS QUERY event_counts
OPTIONS(
  destination_table = 'project.realtime.event_counts_per_minute'
)
AS
SELECT
  TUMBLE_START('1 MINUTE') AS window_start,
  event_type,
  COUNT(*) AS event_count,
  SUM(revenue) AS total_revenue
FROM `project.streaming.raw_events`
GROUP BY
  TUMBLE('1 MINUTE'),
  event_type;
```

### Output to Pub/Sub
```sql
-- Send alerts to Pub/Sub topic
CREATE CONTINUOUS QUERY fraud_alerts
OPTIONS(
  destination_pubsub_topic = 'projects/project/topics/fraud-alerts'
)
AS
SELECT
  TO_JSON(STRUCT(
    user_id,
    transaction_amount,
    country,
    risk_score,
    CURRENT_TIMESTAMP() AS alert_timestamp
  )) AS message
FROM `project.streaming.transactions`
WHERE risk_score > 0.9
  AND transaction_amount > 10000;
```

### Output to Bigtable
```sql
-- Write real-time metrics to Bigtable for low-latency reads
CREATE CONTINUOUS QUERY user_metrics
OPTIONS(
  destination_bigtable_table = 'projects/project/instances/instance/tables/user_metrics'
)
AS
SELECT
  user_id AS rowkey,
  STRUCT(
    COUNT(*) AS event_count,
    SUM(revenue) AS total_revenue,
    MAX(event_timestamp) AS last_active
  ) AS metrics
FROM `project.streaming.events`
GROUP BY
  TUMBLE('5 MINUTES'),
  user_id;
```

## Stateful Continuous Queries

### Windowed Aggregation with JOIN
```sql
-- Join streaming events with dimension table
CREATE CONTINUOUS QUERY enriched_events
OPTIONS(
  destination_table = 'project.realtime.enriched_events'
)
AS
SELECT
  e.event_id,
  e.event_timestamp,
  e.user_id,
  e.event_type,
  e.revenue,
  u.segment AS user_segment,
  u.region AS user_region,
  u.ltv AS user_ltv
FROM `project.streaming.raw_events` AS e
JOIN `project.dimensions.users` AS u
  ON e.user_id = u.user_id;
```

### Session Windows
```sql
-- Track user sessions in real-time
CREATE CONTINUOUS QUERY user_sessions
OPTIONS(
  destination_table = 'project.realtime.sessions'
)
AS
SELECT
  user_id,
  SESSION_START('10 MINUTES') AS session_start,
  SESSION_END('10 MINUTES') AS session_end,
  COUNT(*) AS events_in_session,
  SUM(revenue) AS session_revenue,
  ARRAY_AGG(event_type) AS event_sequence
FROM `project.streaming.events`
GROUP BY
  SESSION('10 MINUTES'),
  user_id;
```

### Sliding Windows
```sql
-- 5-minute moving average, updated every minute
CREATE CONTINUOUS QUERY moving_avg_revenue
OPTIONS(
  destination_table = 'project.realtime.revenue_moving_avg'
)
AS
SELECT
  HOP_START('5 MINUTES', '1 MINUTE') AS window_start,
  country,
  AVG(revenue) AS avg_revenue,
  COUNT(*) AS transaction_count
FROM `project.streaming.transactions`
GROUP BY
  HOP('5 MINUTES', '1 MINUTE'),
  country;
```

## Anomaly Detection (Real-Time)
```sql
-- Detect anomalies using AI functions in continuous query
CREATE CONTINUOUS QUERY anomaly_detection
OPTIONS(
  destination_pubsub_topic = 'projects/project/topics/anomaly-alerts'
)
AS
WITH windowed_metrics AS (
  SELECT
    TUMBLE_START('5 MINUTES') AS window_start,
    service_name,
    AVG(latency_ms) AS avg_latency,
    STDDEV(latency_ms) AS stddev_latency,
    COUNT(*) AS request_count
  FROM `project.streaming.service_metrics`
  GROUP BY TUMBLE('5 MINUTES'), service_name
)
SELECT
  TO_JSON(STRUCT(
    service_name,
    avg_latency,
    request_count,
    'ANOMALY' AS alert_type,
    CURRENT_TIMESTAMP() AS detected_at
  )) AS message
FROM windowed_metrics
WHERE avg_latency > (SELECT AVG(avg_latency) + 3 * STDDEV(avg_latency)
                     FROM windowed_metrics);
```

## Management Commands

```bash
# List continuous queries
bq ls --jobs --project_id=project --filter="configuration.query.continuousQuerySchedule:*"

# Describe continuous query
bq show --job continuous_query_job_id

# Cancel continuous query
bq cancel continuous_query_job_id

# Monitor continuous query metrics
gcloud monitoring metrics-descriptors list \
  --filter="metric.type:bigquery.googleapis.com/query/continuous"
```

## Cost & Slot Management

```
Continuous queries consume slots from your reservation.

Recommendations:
- Start with 100 slots for simple aggregations
- Use 500+ slots for JOINs and complex windows
- Enable dynamic slot autoscaling
- Monitor slot utilization via INFORMATION_SCHEMA
```

```sql
-- Monitor slot usage for continuous queries
SELECT
  job_id,
  total_slot_ms / 1000 AS total_slot_seconds,
  total_bytes_processed,
  creation_time
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE job_type = 'QUERY'
  AND statement_type = 'CONTINUOUS'
ORDER BY creation_time DESC
LIMIT 20;
```

## Output

I'll provide:
- ✓ Continuous query SQL for your use case
- ✓ Output configuration (BigQuery, Pub/Sub, Bigtable, Spanner)
- ✓ Window type selection (tumbling, session, sliding)
- ✓ Slot sizing recommendations
- ✓ Monitoring setup

---

Describe your real-time processing requirements and I'll design the continuous query.
