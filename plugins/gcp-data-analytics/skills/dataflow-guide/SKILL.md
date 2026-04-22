---
name: dataflow-guide
description: This skill should be used when the user asks to "build a Dataflow pipeline", "write Apache Beam code", "create a YAML pipeline", "configure Streaming Engine", "use Dataflow Prime", "handle data skew in Beam", "set up windowing or triggers", or mentions Dataflow, Apache Beam, streaming pipelines, ParDo, GroupByKey, or multi-language pipelines.
version: 2.0.0
---

# Dataflow Guide Skill

Build and operate Apache Beam pipelines on Google Cloud Dataflow for large-scale data processing, including Streaming Engine, Dataflow Prime, and YAML pipelines.

## Core Concepts

### Pipeline Structure
1. **Source** — Read data (BigQuery, Pub/Sub, GCS, Kafka, JDBC, Firestore)
2. **Transform** — Process data (Map, Filter, GroupBy, Window, Join, ML)
3. **Sink** — Write results (BigQuery, Pub/Sub, GCS, BigTable, Spanner)

### Execution Models

#### Batch Processing
- Process bounded (finite) datasets
- BigQuery table → process → BigQuery table
- Complete data available upfront
- Use Spot VMs for 60-91% savings

#### Streaming Processing
- Process unbounded (continuous) data streams
- Pub/Sub → process → BigQuery
- Real-time data arrival
- Use Streaming Engine for managed infrastructure

## Key Transformations

### ParDo (Parallel Do)
```python
class ProcessFn(beam.DoFn):
    def setup(self):
        """One-time initialization (DB connections, model loading)."""
        self.client = bigquery.Client()

    def process(self, element):
        """Per-element processing."""
        yield transform(element)

    def teardown(self):
        """Cleanup resources."""
        self.client.close()

pipeline | beam.ParDo(ProcessFn())
```

### GroupByKey / CombinePerKey
```python
# GroupByKey — all values for each key
pipeline | beam.GroupByKey()

# CombinePerKey — more efficient aggregation (pre-combine on workers)
pipeline | beam.CombinePerKey(sum)       # Built-in
pipeline | beam.CombinePerKey(MeanFn())  # Custom combiner
```

### CoGroupByKey (Join)
```python
# Join two PCollections by key
result = ({'events': events, 'users': users}) | beam.CoGroupByKey()
```

### Windowing
```python
# Tumbling windows (fixed, non-overlapping)
pipeline | beam.WindowInto(beam.window.FixedWindows(60))  # 60 seconds

# Sliding windows (overlapping) — 60s window, 10s slide
pipeline | beam.WindowInto(beam.window.SlidingWindows(60, 10))

# Session windows (activity-based) — 10 min gap timeout
pipeline | beam.WindowInto(beam.window.Sessions(600))

# Global window with triggers
pipeline | beam.WindowInto(
    beam.window.GlobalWindows(),
    trigger=beam.trigger.Repeatedly(
        beam.trigger.AfterCount(100)),
    accumulation_mode=beam.trigger.AccumulationMode.DISCARDING)
```

### Stateful Processing
```python
class DeduplicateFn(beam.DoFn):
    SEEN = beam.transforms.userstate.SetStateSpec(
        'seen', beam.coders.StrUtf8Coder())
    TIMER = beam.transforms.userstate.TimerSpec(
        'gc_timer', beam.transforms.userstate.TimeDomain.WATERMARK)

    def process(self, element,
                seen=beam.DoFn.StateParam(SEEN),
                gc_timer=beam.DoFn.TimerParam(TIMER)):
        key = element['event_id']
        if key not in seen.read():
            seen.add(key)
            gc_timer.set(element['timestamp'] + Duration(hours=1))
            yield element

    @beam.transforms.userstate.on_timer(TIMER)
    def gc_callback(self, seen=beam.DoFn.StateParam(SEEN)):
        seen.clear()
```

## Streaming Engine

Offload streaming computation to Google-managed infrastructure:

```python
options = PipelineOptions([
    '--runner=DataflowRunner',
    '--streaming',
    '--enable_streaming_engine',
    '--project=my-project',
    '--region=us-central1',
    '--temp_location=gs://bucket/temp',
])
```

### Benefits
- Reduced worker resource requirements (20-40% less)
- Automatic horizontal autoscaling
- Google-managed state backend
- Better exactly-once processing
- Reduced operational overhead

## Dataflow Prime

Next-gen resource management with per-transform optimization:

```python
options = PipelineOptions([
    '--runner=DataflowRunner',
    '--experiments=enable_prime',
    '--project=my-project',
    '--region=us-central1',
])
```

### Prime Features
- **Right-fitting** — Auto-allocate resources per transform step
- **Vertical autoscaling** — Scale worker memory up/down
- **GPU support** — Attach GPUs for ML inference transforms
- **Per-transform metrics** — Detailed resource usage per step

## YAML Pipelines (No Code)

Declarative pipeline definitions:

```yaml
pipeline:
  type: chain
  transforms:
    - type: ReadFromPubSub
      config:
        topic: projects/project/topics/events
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

```bash
# Run YAML pipeline
python -m apache_beam.yaml.main \
  --yaml_pipeline_file=pipeline.yaml \
  --runner=DataflowRunner \
  --project=my-project \
  --region=us-central1
```

## Multi-Language Pipelines

```python
# Use Java transforms from Python via expansion service
from apache_beam.transforms.external import JavaExternalTransform

with beam.Pipeline(options=options) as p:
    (p
     | 'Read' >> beam.io.ReadFromPubSub(topic=topic)
     | 'Java Transform' >> JavaExternalTransform(
         'com.example.EnrichmentTransform',
         expansion_service='localhost:8097',
         classpath=['path/to/jars/*.jar'])
     | 'Write' >> beam.io.WriteToBigQuery(table=output_table))
```

## I/O Connectors

### Reading
| Connector | Source | Notes |
|-----------|--------|-------|
| `ReadFromBigQuery()` | BigQuery | Query or table |
| `ReadFromPubSub()` | Pub/Sub | Topic or subscription |
| `ReadFromText()` | GCS files | Text, CSV |
| `ReadFromParquet()` | GCS Parquet | Columnar format |
| `ReadFromAvro()` | GCS Avro | Schema-based |
| `ReadFromKafka()` | Kafka | External Kafka clusters |
| `ReadFromJdbc()` | SQL databases | JDBC-compatible |

### Writing
| Connector | Destination | Notes |
|-----------|------------|-------|
| `WriteToBigQuery()` | BigQuery | Batch or Storage Write API |
| `WriteToPubSub()` | Pub/Sub | Topic output |
| `WriteToText()` | GCS text | Line-delimited |
| `WriteToParquet()` | GCS Parquet | Columnar output |
| `WriteToBigTable()` | Cloud Bigtable | NoSQL |
| `WriteToSpanner()` | Cloud Spanner | Global SQL |

## Pipeline Patterns

### ETL with Dead Letter Queue
```python
class SafeTransform(beam.DoFn):
    def process(self, element):
        try:
            yield beam.pvalue.TaggedOutput('success', transform(element))
        except Exception as e:
            yield beam.pvalue.TaggedOutput('dlq', {
                'element': element, 'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })

results = (pipeline
    | 'Read' >> beam.io.ReadFromPubSub(topic=topic)
    | 'Process' >> beam.ParDo(SafeTransform())
           .with_outputs('dlq', 'success'))

results.success | 'WriteSuccess' >> beam.io.WriteToBigQuery(output_table)
results.dlq     | 'WriteDLQ'     >> beam.io.WriteToBigQuery(dlq_table)
```

### Stream-Batch Join (Enrichment)
```python
# Side input from BigQuery (refreshed periodically)
users = (pipeline
    | 'LoadUsers' >> beam.io.ReadFromBigQuery(table='users')
    | 'ToDict' >> beam.Map(lambda x: (x['user_id'], x))
    | 'AsDict' >> beam.combiners.ToDict())

events = pipeline | 'ReadEvents' >> beam.io.ReadFromPubSub(topic=topic)

enriched = (events
    | 'Enrich' >> beam.Map(
        lambda event, user_map: {**event, **user_map.get(event['user_id'], {})},
        user_map=beam.pvalue.AsDict(users)))
```

## Performance Optimization

| Area | Strategy | Impact |
|------|----------|--------|
| Parallelism | Increase num_workers/max_num_workers | More throughput |
| Machine type | Right-size vCPU and memory | Cost efficiency |
| Combiners | Use CombinePerKey instead of GroupByKey | Less shuffle |
| Data format | Use Avro/Parquet for I/O | Faster reads/writes |
| Side inputs | Keep < 100MB, use AsDict for lookups | Avoid OOM |
| Serialization | Use custom coders, avoid pickle | Less overhead |
| Streaming Engine | Enable for streaming jobs | 20-40% less resources |
| Prime | Enable for heterogeneous workloads | Auto right-size |

## Deployment

```bash
# Deploy batch pipeline
python pipeline.py \
  --runner=DataflowRunner \
  --project=my-project \
  --region=us-central1 \
  --temp_location=gs://bucket/temp \
  --job_name=my-etl-$(date +%Y%m%d)

# Deploy streaming pipeline with update
python pipeline.py \
  --runner=DataflowRunner \
  --streaming \
  --enable_streaming_engine \
  --update \
  --job_name=existing-streaming-job

# Create Flex Template
gcloud dataflow flex-template build \
  gs://templates/my-template.json \
  --image=gcr.io/project/my-pipeline:latest \
  --sdk-language=PYTHON \
  --metadata-file=metadata.json

# Monitor jobs
gcloud dataflow jobs list --region=us-central1
gcloud dataflow jobs describe JOB_ID --region=us-central1
gcloud dataflow jobs cancel JOB_ID --region=us-central1
```

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| OutOfMemory | Large side inputs, list accumulation | Use generators, AsDict, reduce batch |
| Pipeline lag | Data skew, slow transforms | Reshard keys, optimize code |
| Cost overruns | Over-provisioned workers | Enable Prime, use Spot VMs |
| Stuck watermark | Late data, no triggers | Configure allowed lateness, triggers |
| Serialization error | Non-serializable objects | Use setup() for initialization |
| Quota exceeded | Too many workers | Set max_num_workers, request increase |

## Resources

- [Apache Beam Documentation](https://beam.apache.org/documentation/)
- [Dataflow Documentation](https://cloud.google.com/dataflow/docs)
- [Beam Programming Guide](https://beam.apache.org/documentation/programming-guide/)
- [Dataflow Best Practices](https://cloud.google.com/dataflow/docs/guides/deploying-a-pipeline)
- [Streaming Engine](https://cloud.google.com/dataflow/docs/streaming-engine)
- [Dataflow Prime](https://cloud.google.com/dataflow/docs/guides/enable-dataflow-prime)
- [YAML Pipelines](https://beam.apache.org/documentation/sdks/yaml/)
