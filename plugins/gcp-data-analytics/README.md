# GCP Data & Analytics Plugin v2.0

A comprehensive Claude Code plugin covering **8 Google Cloud Platform data services** — from ingestion to governance, real-time to batch, SQL to ML.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATION                                │
│                   Cloud Composer (Airflow)                        │
├─────────────────────────────────────────────────────────────────┤
│   INGESTION          PROCESSING            SERVING               │
│  ┌──────────┐   ┌───────────────┐   ┌──────────────────┐       │
│  │ Pub/Sub  │──▶│   Dataflow    │──▶│    BigQuery       │       │
│  │          │   │  (Beam/YAML)  │   │  (SQL/Graph/ML)   │       │
│  └──────────┘   ├───────────────┤   ├──────────────────┤       │
│                  │   Dataproc    │   │  BigQuery ML     │       │
│                  │  (Spark/SQL)  │   │  (AI Functions)  │       │
│                  └───────────────┘   └──────────────────┘       │
├─────────────────────────────────────────────────────────────────┤
│                     LAKEHOUSE                                    │
│  BigLake + Apache Iceberg  │  Medallion: Bronze → Silver → Gold │
├─────────────────────────────────────────────────────────────────┤
│                     GOVERNANCE                                   │
│  Dataplex Universal Catalog │ Quality │ Lineage │ Security      │
└─────────────────────────────────────────────────────────────────┘
```

## ✨ Services Covered

### BigQuery (Data Warehouse & Analytics)
- SQL optimization, Graph queries (GQL), Continuous Queries
- Pipe Syntax, AI functions (AI.GENERATE, AI.CLASSIFY, AI.FORECAST)
- BigQuery ML for model training in SQL
- Schema design, partitioning, clustering, Search Index
- Cost optimization and slot management

### Pub/Sub (Event Streaming)
- Topic and subscription management
- **Export Subscriptions** — direct to BigQuery, GCS, Bigtable
- **Single Message Transforms** — in-flight PII redaction and transform
- **Exactly-once delivery** (GA) with ordering
- Dead letter queues, message filtering

### Dataflow (Stream & Batch Processing)
- Apache Beam pipeline design (Python, Java, Go, YAML)
- **Streaming Engine** — managed streaming infrastructure
- **Dataflow Prime** — automatic resource right-fitting
- Multi-language pipelines, GPU-accelerated transforms
- Dead letter queues, stateful processing

### Cloud Composer (Orchestration)
- Apache Airflow DAG design and TaskFlow API
- GCP operator integration (BigQuery, Dataflow, Dataproc, GCS)
- CI/CD pipeline for DAG deployment
- Environment management and cost optimization

### Dataproc (Apache Spark)
- **Serverless Spark** — zero-management batch and interactive
- **Lightning Engine** for high performance
- BigQuery-Spark connector (Storage Read/Write API)
- PySpark, SparkSQL, and Iceberg support

### BigLake & Apache Iceberg (Lakehouse)
- BigLake Iceberg table creation and management
- **Medallion architecture** (Bronze → Silver → Gold)
- Schema evolution, time travel, table maintenance
- Multi-engine access (BigQuery, Spark, Trino, Flink)

### Dataplex Universal Catalog (Governance)
- Unified metadata discovery and cataloging
- Data quality rules and automated scanning
- End-to-end data lineage tracking
- Business glossary and tag management

### BigQuery ML (Machine Learning in SQL)
- Model training (classification, regression, clustering, time-series)
- AI functions (no model required)
- Remote models via Vertex AI (Gemini, custom endpoints)
- Hyperparameter tuning and model evaluation

## 🚀 Quick Start

1. Install the plugin in Claude Code
2. Use `/bigquery-query` to write and optimize BigQuery SQL
3. Use `/bqml-train` to train ML models in SQL
4. Use `/bigquery-continuous-query` for real-time processing
5. Use `/pubsub-setup` for event streaming configuration
6. Use `/dataflow-pipeline` for Apache Beam pipeline guidance
7. Use `/composer-dag` to create Airflow DAGs
8. Use `/dataproc-spark-job` for Spark workloads
9. Use `/biglake-iceberg` for lakehouse architecture
10. Use `/dataplex-governance` for data governance

## 📋 Commands

| Command | Description |
|---------|-------------|
| `/bigquery-query` | Write and optimize BigQuery SQL (Pipe, GQL, AI functions) |
| `/bigquery-schema-design` | Design table schemas with partitioning and clustering |
| `/bigquery-continuous-query` | Real-time continuous queries with windowing |
| `/bqml-train` | Train ML models in BigQuery using SQL |
| `/pubsub-setup` | Configure Pub/Sub topics, subscriptions, exports |
| `/pubsub-monitoring` | Set up monitoring and alerting for Pub/Sub |
| `/dataflow-pipeline` | Design Beam pipelines (Python, Java, Go, YAML) |
| `/dataflow-cost-optimization` | Optimize Dataflow pipeline costs |
| `/composer-dag` | Create Airflow DAGs for pipeline orchestration |
| `/dataproc-spark-job` | Submit and optimize Spark jobs |
| `/biglake-iceberg` | Build BigLake Iceberg lakehouse tables |
| `/dataplex-governance` | Set up data governance and quality |

## 🤖 Agents

| Agent | Expertise |
|-------|-----------|
| **BigQuery Optimizer** | SQL optimization, Graph, Continuous Queries, AI functions, cost |
| **Pub/Sub Architect** | Event streaming, Export Subs, SMT, exactly-once |
| **Dataflow Engineer** | Beam pipelines, Streaming Engine, Prime, YAML |
| **Composer Orchestrator** | Airflow DAGs, GCP integration, CI/CD |
| **Dataproc Engineer** | Serverless Spark, BigQuery-Spark, clusters |
| **Data Governance Architect** | Dataplex, BigLake, Iceberg, quality, lineage |

## 📚 Skills

| Skill | Coverage |
|-------|----------|
| `bigquery-assistant` | BigQuery SQL, Graph, Continuous Queries, AI, BQML, BigLake |
| `pubsub-helper` | Pub/Sub patterns, Export Subs, SMT, exactly-once, migration |
| `dataflow-guide` | Beam pipelines, Streaming Engine, Prime, YAML, multi-language |
| `bqml-guide` | ML model training, AI functions, remote models, evaluation |
| `composer-guide` | Airflow DAGs, operators, CI/CD, monitoring, cost optimization |
| `dataproc-guide` | Serverless Spark, BigQuery connector, Iceberg, tuning |
| `lakehouse-guide` | BigLake, Iceberg, Dataplex, medallion architecture, governance |

## 📋 Requirements

- Access to GCP project with appropriate APIs enabled
- `gcloud` CLI installed and configured
- For Dataflow: Apache Beam SDK installed
- For Dataproc: Spark environment (or use Serverless)
- For Composer: Composer environment created
- For BigLake: Cloud Resource Connection configured

## 📌 What's New in v2.0

- **+5 new services**: Cloud Composer, Dataproc, BigLake/Iceberg, Dataplex, BQML
- **BigQuery Graph** (GQL) for relationship analysis
- **Continuous Queries** for real-time event processing
- **Pipe Syntax** for concise SQL
- **AI Functions** (AI.GENERATE, AI.CLASSIFY, AI.IF, AI.FORECAST)
- **Export Subscriptions** for direct Pub/Sub → BigQuery/GCS/Bigtable
- **Single Message Transforms** for in-flight processing
- **Streaming Engine** and **Dataflow Prime** optimization
- **YAML Pipelines** for no-code Dataflow
- **Lakehouse Architecture** with BigLake + Iceberg
- **Data Governance** with Dataplex Universal Catalog

## License

MIT
