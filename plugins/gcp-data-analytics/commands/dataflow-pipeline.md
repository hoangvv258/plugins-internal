---
description: Create Apache Beam pipelines — Streaming Engine, YAML pipelines, multi-language, GPU transforms
---

# Dataflow Pipeline Designer

I'll help you design and implement Apache Beam pipelines for Google Cloud Dataflow, including Streaming Engine, YAML pipelines, and multi-language support.

## Pipeline Components

1. **Data Sources** — BigQuery, Pub/Sub, Cloud Storage, Firestore, Kafka, JDBC
2. **Transformations** — aggregations, joins, windowing, filtering, ML inference
3. **Sinks** — BigQuery, Pub/Sub, Cloud Storage, BigTable, Spanner
4. **Scaling** — Streaming Engine, autoscaling, Dataflow Prime
5. **Error Handling** — dead letter queues, retries, monitoring

## Pipeline Types

### Batch Pipeline (Python)
```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions([
    '--runner=DataflowRunner',
    '--project=my-project',
    '--region=us-central1',
    '--temp_location=gs://bucket/temp',
    '--job_name=daily-etl',
    '--num_workers=4',
    '--max_num_workers=20',
])

with beam.Pipeline(options=options) as p:
    (p
     | 'Read' >> beam.io.ReadFromBigQuery(
         query='SELECT * FROM dataset.raw_events WHERE DATE(ts) = CURRENT_DATE()',
         use_standard_sql=True)
     | 'Transform' >> beam.ParDo(CleanAndEnrichFn())
     | 'Filter' >> beam.Filter(lambda x: x['status'] == 'valid')
     | 'Write' >> beam.io.WriteToBigQuery(
         table='project:dataset.clean_events',
         write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
         create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER))
```

### Streaming Pipeline with Streaming Engine
```python
options = PipelineOptions([
    '--runner=DataflowRunner',
    '--project=my-project',
    '--region=us-central1',
    '--temp_location=gs://bucket/temp',
    '--streaming',
    '--enable_streaming_engine',  # Offload to managed infrastructure
    '--experiments=enable_prime',  # Enable Dataflow Prime
])

with beam.Pipeline(options=options) as p:
    events = (p
     | 'Read' >> beam.io.ReadFromPubSub(
         topic='projects/my-project/topics/events')
     | 'Parse' >> beam.Map(json.loads)
     | 'Window' >> beam.WindowInto(beam.window.FixedWindows(60))
     | 'Count' >> beam.CombinePerKey(sum)
     | 'Format' >> beam.Map(format_output)
     | 'Write' >> beam.io.WriteToBigQuery(
         table='project:dataset.realtime_counts',
         method=beam.io.WriteToBigQuery.Method.STORAGE_WRITE_API))
```

### YAML Pipeline (No Code Required)
```yaml
pipeline:
  type: chain
  transforms:
    - type: ReadFromPubSub
      config:
        topic: projects/my-project/topics/events
        format: JSON
    - type: Filter
      config:
        language: python
        keep: "element['status'] == 'active'"
    - type: MapToFields
      config:
        language: python
        fields:
          user_id: element['user_id']
          event_type: element['event_type']
          timestamp: element['timestamp']
    - type: WriteToBigQuery
      config:
        table: project.dataset.filtered_events
        write_disposition: WRITE_APPEND
```

### Multi-Language Pipeline (Python + Java)
```python
# Use Java transforms from Python
from apache_beam.transforms.external import JavaExternalTransform

with beam.Pipeline(options=options) as p:
    (p
     | 'Read' >> beam.io.ReadFromPubSub(topic=topic)
     | 'Java Enrichment' >> JavaExternalTransform(
         'com.example.EnrichmentTransform',
         expansion_service='localhost:8097')
     | 'Write' >> beam.io.WriteToBigQuery(table=output_table))
```

## Advanced Patterns

### Dead Letter Queue
```python
class ProcessWithDLQ(beam.DoFn):
    def process(self, element):
        try:
            yield transform(element)
        except Exception as e:
            yield beam.pvalue.TaggedOutput('dlq', {
                'element': element,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })

results = events | beam.ParDo(ProcessWithDLQ()).with_outputs('dlq', main='main')
results.main | 'WriteSuccess' >> beam.io.WriteToBigQuery(success_table)
results.dlq | 'WriteDLQ' >> beam.io.WriteToBigQuery(dlq_table)
```

### Stateful Processing
```python
class DeduplicateFn(beam.DoFn):
    SEEN = beam.transforms.userstate.SetStateSpec('seen', beam.coders.StrUtf8Coder())

    def process(self, element, seen=beam.DoFn.StateParam(SEEN)):
        key = element['event_id']
        if key not in seen.read():
            seen.add(key)
            yield element
```

## Supported Languages

- **Python** — Apache Beam SDK for Python (most popular)
- **Java** — Apache Beam SDK for Java (best performance)
- **Go** — Apache Beam SDK for Go
- **YAML** — Declarative pipeline definitions
- **SQL** — Beam SQL for relational transforms

## Output

I'll provide:
- ✓ Pipeline code (your chosen language or YAML)
- ✓ Deployment commands and scripts
- ✓ Streaming Engine / Prime configuration
- ✓ Monitoring and error handling setup
- ✓ Performance optimization tips
- ✓ Cost estimation and optimization

---

Describe your data processing workflow and requirements.
