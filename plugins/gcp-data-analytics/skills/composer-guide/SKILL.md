---
name: Cloud Composer Guide
description: Google Cloud Composer (Apache Airflow) — DAG patterns, GCP integration, environment management, CI/CD
version: 1.0.0
---

# Cloud Composer Guide Skill

Master Google Cloud Composer for orchestrating complex data pipelines across GCP services.

## Core Concepts

### What is Cloud Composer?
- Fully managed Apache Airflow service on GCP
- Orchestrate workflows across BigQuery, Dataflow, Dataproc, GCS, and more
- No infrastructure management (Google manages Airflow infra)
- Built-in monitoring, logging, and autoscaling

### Key Components
| Component | Purpose |
|-----------|---------|
| **DAG** | Directed Acyclic Graph — defines workflow |
| **Task** | Single unit of work (operator execution) |
| **Operator** | Defines what a task does (BigQuery, Dataflow, etc.) |
| **Sensor** | Waits for a condition (file exists, job done, etc.) |
| **Hook** | Connection to external systems (BigQuery, GCS, etc.) |
| **XCom** | Cross-communication between tasks |
| **Pool** | Limits concurrent task execution |
| **Variable** | Runtime configuration storage |

### Composer Versions
| Feature | Composer 2 | Composer 3 |
|---------|-----------|-----------|
| Airflow Version | 2.x | 2.x (latest) |
| Autoscaling | Worker autoscaling | Advanced autoscaling |
| Pricing | Per environment hour | Per environment hour |
| Networking | VPC-native | VPC-native |
| Recommended | Production | New deployments |

## DAG Design Patterns

### Standard ETL Pipeline
```python
from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryInsertJobOperator,
    BigQueryCheckOperator,
    BigQueryValueCheckOperator,
)
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import (
    GCSToBigQueryOperator,
)
from airflow.utils.dates import days_ago
from datetime import timedelta

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email': ['alerts@company.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=30),
    'execution_timeout': timedelta(hours=2),
}

with DAG(
    dag_id='daily_etl',
    default_args=default_args,
    description='Daily ETL pipeline: GCS → BigQuery → Transform → Quality',
    schedule_interval='0 6 * * *',
    start_date=days_ago(1),
    catchup=False,
    tags=['production', 'etl', 'daily'],
    max_active_runs=1,
    doc_md="""
    ## Daily ETL Pipeline
    Loads raw data from GCS, transforms in BigQuery,
    runs quality checks, and builds aggregations.
    """,
) as dag:
    # Tasks defined here (see commands/composer-dag.md for full examples)
    pass
```

### TaskFlow API (Modern Python)
```python
from airflow.decorators import dag, task, task_group
from datetime import datetime

@dag(
    schedule='0 6 * * *',
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['taskflow', 'etl'],
)
def modern_pipeline():

    @task_group(group_id='extract')
    def extract_data():
        @task
        def extract_api():
            import requests
            return requests.get('https://api.example.com/data').json()

        @task
        def extract_db():
            from google.cloud import bigquery
            client = bigquery.Client()
            return [dict(row) for row in client.query('SELECT * FROM ...')]

        return {'api': extract_api(), 'db': extract_db()}

    @task
    def transform(raw_data: dict):
        api_data = raw_data['api']
        db_data = raw_data['db']
        return merge_and_clean(api_data, db_data)

    @task
    def load(clean_data: list):
        from google.cloud import bigquery
        client = bigquery.Client()
        client.insert_rows_json('project.dataset.table', clean_data)

    @task
    def notify(result):
        send_slack_notification(f"ETL complete: {len(result)} rows")

    raw = extract_data()
    clean = transform(raw)
    load(clean)
    notify(clean)

modern_pipeline()
```

### Dynamic DAG Generation
```python
# Generate DAGs from config file
import yaml

with open('/home/airflow/gcs/data/pipeline_configs.yaml') as f:
    configs = yaml.safe_load(f)

for config in configs['pipelines']:
    dag_id = f"etl_{config['name']}"

    @dag(dag_id=dag_id, schedule=config['schedule'], ...)
    def pipeline():
        # Generate tasks from config
        for step in config['steps']:
            BigQueryInsertJobOperator(
                task_id=step['name'],
                configuration={'query': {'query': step['sql']}},
            )
    
    globals()[dag_id] = pipeline()
```

## GCP Operator Reference

### BigQuery
```python
# Insert job (query, load, copy, extract)
BigQueryInsertJobOperator(task_id='bq_query', configuration={...})

# Check query result
BigQueryCheckOperator(task_id='check', sql='SELECT COUNT(*) > 0 FROM ...')

# Value check
BigQueryValueCheckOperator(task_id='value_check',
    sql='SELECT COUNT(*) FROM ...', pass_value=1000, tolerance=0.1)

# Table sensor (wait for partition)
BigQueryTableExistenceSensor(task_id='wait_table',
    project_id='p', dataset_id='d', table_id='t${{ ds_nodash }}')
```

### Dataflow
```python
# Flex template
DataflowStartFlexTemplateOperator(task_id='dataflow',
    project_id='p', location='us-central1', body={...})

# Classic template
DataflowTemplatedJobStartOperator(task_id='dataflow',
    template='gs://templates/my-template',
    parameters={'input': '...', 'output': '...'})

# Sensor
DataflowJobStatusSensor(task_id='wait', job_id='...', expected_statuses=['JOB_STATE_DONE'])
```

### Dataproc
```python
# Serverless batch
DataprocCreateBatchOperator(task_id='spark', batch_id='...', batch={
    'pyspark_batch': {'main_python_file_uri': 'gs://scripts/job.py'}})

# Cluster job
DataprocSubmitJobOperator(task_id='spark', job={
    'pyspark_job': {'main_python_file_uri': 'gs://scripts/job.py'}})
```

### Cloud Storage
```python
# Sensor (wait for file)
GCSObjectExistenceSensor(task_id='wait_file',
    bucket='bucket', object='path/to/file.csv')

# Transfer
GCSToGCSOperator(task_id='copy',
    source_bucket='src', source_object='data/*',
    destination_bucket='dst')
```

### Pub/Sub
```python
# Publish message
PubSubPublishMessageOperator(task_id='publish',
    topic='events', messages=[{'data': b'message'}])

# Pull sensor
PubSubPullSensor(task_id='wait_message',
    subscription='my-sub', max_messages=1)
```

## Environment Management

### Create Environment
```bash
# Create Composer 2 environment
gcloud composer environments create my-composer \
  --location=us-central1 \
  --image-version=composer-2.9.0-airflow-2.9.3 \
  --environment-size=small \
  --scheduler-cpu=0.5 \
  --scheduler-memory=2 \
  --scheduler-storage=1 \
  --web-server-cpu=0.5 \
  --web-server-memory=2 \
  --web-server-storage=1 \
  --worker-cpu=1 \
  --worker-memory=4 \
  --worker-storage=2 \
  --min-workers=1 \
  --max-workers=6 \
  --network=default \
  --subnetwork=default
```

### Install PyPI Packages
```bash
gcloud composer environments update my-composer \
  --location=us-central1 \
  --update-pypi-packages-from-file=requirements.txt
```

### Set Airflow Variables
```bash
gcloud composer environments run my-composer \
  --location=us-central1 \
  variables -- set my_variable my_value
```

### DAG Deployment
```bash
# Upload DAG files
gcloud composer environments storage dags import \
  --environment=my-composer \
  --location=us-central1 \
  --source=dags/my_dag.py

# Upload data files
gcloud composer environments storage data import \
  --environment=my-composer \
  --location=us-central1 \
  --source=data/config.yaml
```

## CI/CD Pipeline

### GitHub Actions Example
```yaml
name: Deploy DAGs
on:
  push:
    branches: [main]
    paths: ['dags/**']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: |
          pip install apache-airflow pytest
          pytest tests/test_dags.py

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with: { credentials_json: '${{ secrets.GCP_SA_KEY }}' }
      - run: |
          gcloud composer environments storage dags import \
            --environment=${{ vars.COMPOSER_ENV }} \
            --location=${{ vars.COMPOSER_LOCATION }} \
            --source=dags/
```

### DAG Testing
```python
# tests/test_dags.py
import pytest
from airflow.models import DagBag

@pytest.fixture
def dagbag():
    return DagBag(dag_folder='dags/', include_examples=False)

def test_no_import_errors(dagbag):
    assert len(dagbag.import_errors) == 0

def test_dag_has_tasks(dagbag):
    for dag_id, dag in dagbag.dags.items():
        assert len(dag.tasks) > 0, f"{dag_id} has no tasks"

def test_dag_has_tags(dagbag):
    for dag_id, dag in dagbag.dags.items():
        assert len(dag.tags) > 0, f"{dag_id} has no tags"
```

## Monitoring & Debugging

### Key Metrics
| Metric | Alert If | Action |
|--------|----------|--------|
| DAG run duration | > 2x average | Check for data skew, slow queries |
| Task failure rate | > 5% | Check logs, fix root cause |
| Scheduler heartbeat | Missing | Environment health issue |
| Worker memory | > 80% | Scale workers or optimize tasks |
| Database connections | > 80% max | Reduce parallelism or pool size |

### Log Analysis
```bash
# View task logs
gcloud composer environments run my-composer \
  --location=us-central1 \
  tasks logs -- -t task_id dag_id 2026-04-01

# View scheduler logs
gcloud logging read \
  'resource.type="cloud_composer_environment" AND log_id("airflow-scheduler")' \
  --project=project --limit=50
```

## Cost Optimization

| Strategy | Savings | How |
|----------|---------|-----|
| Right-size environment | 20-40% | Match size to workload |
| Reduce scheduler parsing | 10-20% | Increase dag_dir_list_interval |
| Use task pools | 10-30% | Limit concurrent expensive tasks |
| Schedule off-peak | 10-20% | Run during low-demand hours |
| Consolidate environments | 30-50% | Share env across teams |

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| DAG not visible | Import error, parse failure | Check import errors in logs |
| Task stuck in queue | Worker full, pool exhausted | Scale workers, check pools |
| High scheduler lag | Too many DAGs parsing | Increase parser interval, simplify |
| OOM on worker | Task too memory-intensive | Increase worker memory, use KubePod |
| Task timeout | Processing too slow | Increase timeout, optimize logic |
| XCom too large | Passing large data between tasks | Use GCS for large data transfer |

## Resources

- [Cloud Composer Documentation](https://cloud.google.com/composer/docs)
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [GCP Operators Reference](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/index.html)
- [Composer Best Practices](https://cloud.google.com/composer/docs/best-practices)
- [Composer Pricing](https://cloud.google.com/composer/pricing)
