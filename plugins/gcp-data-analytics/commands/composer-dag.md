---
id: composer-dag
name: Cloud Composer DAG
description: Create and deploy Airflow DAGs for GCP data pipeline orchestration
---

# Cloud Composer DAG Designer

Create production-ready Airflow DAGs for orchestrating data pipelines across GCP services.

## DAG Templates

### Daily BigQuery ETL Pipeline
```python
from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryInsertJobOperator,
    BigQueryCheckOperator,
)
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import (
    GCSToBigQueryOperator,
)
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email': ['data-alerts@company.com'],
    'email_on_failure': True,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
}

with DAG(
    'daily_etl_pipeline',
    default_args=default_args,
    description='Daily ETL: GCS → BigQuery → Transform → Quality Check',
    schedule_interval='0 6 * * *',  # 6 AM daily
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['etl', 'bigquery', 'production'],
    max_active_runs=1,
) as dag:

    # Step 1: Load raw data from GCS
    load_raw = GCSToBigQueryOperator(
        task_id='load_raw_data',
        bucket='data-lake-raw',
        source_objects=['events/{{ ds }}/*.parquet'],
        destination_project_dataset_table='project.raw.events',
        source_format='PARQUET',
        write_disposition='WRITE_APPEND',
        autodetect=True,
    )

    # Step 2: Transform and clean data
    transform = BigQueryInsertJobOperator(
        task_id='transform_events',
        configuration={
            'query': {
                'query': '''
                    INSERT INTO `project.clean.events`
                    SELECT
                        event_id,
                        TIMESTAMP(event_timestamp) AS event_ts,
                        LOWER(TRIM(user_id)) AS user_id,
                        event_type,
                        SAFE_CAST(revenue AS NUMERIC) AS revenue,
                        country
                    FROM `project.raw.events`
                    WHERE DATE(_PARTITIONTIME) = '{{ ds }}'
                      AND event_id IS NOT NULL
                ''',
                'useLegacySql': False,
            }
        },
    )

    # Step 3: Quality check
    quality_check = BigQueryCheckOperator(
        task_id='quality_check',
        sql='''
            SELECT COUNT(*) > 0
            FROM `project.clean.events`
            WHERE DATE(event_ts) = '{{ ds }}'
        ''',
        use_legacy_sql=False,
    )

    # Step 4: Build aggregations
    aggregate = BigQueryInsertJobOperator(
        task_id='build_aggregates',
        configuration={
            'query': {
                'query': '''
                    CREATE OR REPLACE TABLE `project.analytics.daily_summary`
                    PARTITION BY event_date
                    AS
                    SELECT
                        DATE(event_ts) AS event_date,
                        country,
                        event_type,
                        COUNT(*) AS event_count,
                        SUM(revenue) AS total_revenue
                    FROM `project.clean.events`
                    GROUP BY 1, 2, 3
                ''',
                'useLegacySql': False,
            }
        },
    )

    load_raw >> transform >> quality_check >> aggregate
```

### Dataflow + BigQuery Orchestration
```python
from airflow.providers.google.cloud.operators.dataflow import (
    DataflowStartFlexTemplateOperator,
)
from airflow.providers.google.cloud.sensors.dataflow import (
    DataflowJobStatusSensor,
)
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryInsertJobOperator,
)

with DAG('dataflow_etl', ...) as dag:

    # Launch Dataflow pipeline
    start_pipeline = DataflowStartFlexTemplateOperator(
        task_id='start_dataflow',
        project_id='my-project',
        location='us-central1',
        body={
            'launchParameter': {
                'jobName': 'etl-{{ ds_nodash }}',
                'containerSpecGcsPath': 'gs://templates/etl-template.json',
                'parameters': {
                    'input_date': '{{ ds }}',
                    'output_table': 'project:dataset.output',
                },
                'environment': {
                    'numWorkers': 5,
                    'maxWorkers': 20,
                    'enableStreamingEngine': True,
                },
            }
        },
    )

    # Wait for Dataflow job
    wait_pipeline = DataflowJobStatusSensor(
        task_id='wait_dataflow',
        project_id='my-project',
        location='us-central1',
        job_id="{{ task_instance.xcom_pull('start_dataflow')['id'] }}",
        expected_statuses=['JOB_STATE_DONE'],
        poke_interval=60,
        timeout=3600,
    )

    # Post-processing in BigQuery
    post_process = BigQueryInsertJobOperator(
        task_id='post_process',
        configuration={...},
    )

    start_pipeline >> wait_pipeline >> post_process
```

### Dataproc Serverless Spark Job
```python
from airflow.providers.google.cloud.operators.dataproc import (
    DataprocCreateBatchOperator,
)

with DAG('spark_etl', ...) as dag:

    spark_job = DataprocCreateBatchOperator(
        task_id='run_spark_etl',
        project_id='my-project',
        region='us-central1',
        batch_id='etl-{{ ds_nodash }}-{{ run_id[:8] }}',
        batch={
            'pyspark_batch': {
                'main_python_file_uri': 'gs://scripts/etl_job.py',
                'args': ['--date={{ ds }}', '--output=project.dataset.table'],
                'python_file_uris': ['gs://scripts/utils.py'],
            },
            'runtime_config': {
                'version': '2.2',
                'properties': {
                    'spark.executor.memory': '8g',
                    'spark.sql.adaptive.enabled': 'true',
                },
            },
            'environment_config': {
                'execution_config': {
                    'service_account': 'spark-sa@project.iam.gserviceaccount.com',
                    'subnetwork_uri': 'projects/project/regions/us-central1/subnetworks/default',
                },
            },
        },
    )
```

## TaskFlow API (Modern Python DAGs)
```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(
    schedule='0 6 * * *',
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['taskflow'],
)
def modern_etl():

    @task
    def extract():
        """Extract data from API."""
        import requests
        return requests.get('https://api.example.com/data').json()

    @task
    def transform(raw_data: dict):
        """Clean and transform data."""
        return [clean(record) for record in raw_data['items']]

    @task
    def load(clean_data: list):
        """Load to BigQuery."""
        from google.cloud import bigquery
        client = bigquery.Client()
        client.insert_rows_json('project.dataset.table', clean_data)

    raw = extract()
    clean = transform(raw)
    load(clean)

modern_etl()
```

## Deployment

```bash
# Sync DAGs to Composer
gcloud composer environments storage dags import \
  --environment=my-composer \
  --location=us-central1 \
  --source=dags/

# List DAGs
gcloud composer environments run my-composer \
  --location=us-central1 \
  dags list

# Trigger DAG manually
gcloud composer environments run my-composer \
  --location=us-central1 \
  dags trigger -- daily_etl_pipeline
```

## Output

I'll provide:
- ✓ Production-ready DAG code
- ✓ Operator selection for your use case
- ✓ Error handling and retry configuration
- ✓ Deployment commands
- ✓ Monitoring and alerting setup

---

Describe your pipeline workflow and I'll create the DAG.
