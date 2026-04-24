---
description: Generate, optimize, and validate BigQuery SQL queries — including Pipe Syntax, Graph Queries (GQL), Continuous Queries, and AI functions
---

# BigQuery Query Assistant

Help me with a BigQuery query for your data analytics task. I support all modern BigQuery SQL features including Pipe Syntax, Graph queries, Continuous Queries, and AI functions.

## Context

Provide details about:
1. **Your dataset structure** — which tables, schemas involved
2. **The goal** — what data you want to extract or analyze
3. **Performance constraints** — query size, latency requirements
4. **Cost concerns** — optimize for data scanned or execution time
5. **Query type** — standard SQL, Graph (GQL), Continuous, or BQML

## Standard SQL Examples

### Optimized Aggregation
```sql
SELECT
  DATE(event_timestamp) AS event_date,
  country,
  COUNT(*) AS event_count,
  SUM(revenue) AS total_revenue
FROM `project.dataset.events`
WHERE DATE(event_timestamp) BETWEEN '2026-01-01' AND '2026-03-31'
GROUP BY 1, 2
ORDER BY total_revenue DESC;
```

## Pipe Syntax (New — GA)

More concise, readable SQL using the `|>` operator:

```sql
FROM `project.dataset.events`
|> WHERE DATE(event_timestamp) >= '2026-01-01'
|> AGGREGATE COUNT(*) AS cnt, SUM(revenue) AS rev GROUP BY country
|> ORDER BY rev DESC
|> LIMIT 20;
```

## Graph Queries (GQL)

Query relationships using Graph Query Language:

```sql
GRAPH FinancialGraph
MATCH (sender:Account)-[t:Transfer]->(receiver:Account)
WHERE t.amount > 10000
  AND sender.country <> receiver.country
RETURN sender.id, receiver.id, t.amount, t.timestamp
ORDER BY t.amount DESC;
```

## Continuous Queries (Real-Time)

Event-driven SQL that processes data as it arrives:

```sql
CREATE CONTINUOUS QUERY my_agg_query
OPTIONS(destination_table = 'project.dataset.realtime_aggs')
AS
SELECT
  TUMBLE_START('1 MINUTE') AS window_start,
  event_type,
  COUNT(*) AS event_count
FROM `project.dataset.events`
GROUP BY TUMBLE('1 MINUTE'), event_type;
```

## AI Functions

Use Gemini and ML models directly in SQL:

```sql
-- Text classification with AI.CLASSIFY
SELECT
  comment_text,
  AI.CLASSIFY(comment_text, ['positive', 'negative', 'neutral']) AS sentiment
FROM `project.dataset.comments`;

-- Text generation with AI.GENERATE
SELECT
  product_name,
  AI.GENERATE('Write a 50-word product description for: ' || product_name) AS description
FROM `project.dataset.products`;

-- Time-series forecasting
SELECT *
FROM AI.FORECAST(
  MODEL `project.dataset.sales_model`,
  STRUCT(30 AS horizon, 0.95 AS confidence_level)
);
```

## Output

I'll provide:
- ✓ Optimized SQL query (standard, Pipe, GQL, or Continuous)
- ✓ Execution plan analysis
- ✓ Cost estimation (GB scanned, slot hours)
- ✓ Performance recommendations
- ✓ Partitioning and clustering suggestions
- ✓ Alternative approaches (materialized views, BI Engine)

---

What BigQuery query do you need help with?
