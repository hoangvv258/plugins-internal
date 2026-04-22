---
name: pubsub-helper
description: This skill should be used when the user asks to "configure Pub/Sub topics or subscriptions", "set up Export Subscriptions to BigQuery", "implement Single Message Transforms", "enable exactly-once delivery", "design dead letter queues", "filter Pub/Sub messages", "migrate from Kafka to Pub/Sub", or mentions Pub/Sub, event streaming, message ordering, push/pull subscriptions, or Pub/Sub Lite migration.
version: 2.0.0
---

# Pub/Sub Helper Skill

Master Google Cloud Pub/Sub for building event-driven architectures, real-time data pipelines, and integration patterns.

## Core Concepts

### Topic vs Subscription
- **Topics**: Message channels where publishers send data
- **Subscriptions**: Endpoints where subscribers consume messages
- **Many-to-many**: One topic can have multiple subscriptions
- **Message retention**: Up to 31 days (configurable)

### Delivery Guarantees
| Mode | Description | Use Case |
|------|-------------|----------|
| At-least-once | Default, messages delivered until acknowledged | Most use cases |
| Exactly-once | Deduplication with ordering keys (GA) | Financial, billing |
| Ordered | FIFO within ordering keys | Sequential processing |

## Subscription Types

### Pull Subscriptions
- Subscriber controls consumption rate
- Batch processing friendly
- Better for Dataflow jobs
- Requires explicit acknowledgment
- Supports flow control

### Push Subscriptions
- Pub/Sub pushes messages to HTTP endpoint
- Good for Cloud Functions, Cloud Run
- Auto-retry on failure (exponential backoff)
- Supports authentication (OIDC/JWT)
- No client library needed

### Export Subscriptions (New — No Dataflow Required)

#### BigQuery Export
```bash
gcloud pubsub subscriptions create events-to-bq \
  --topic=events \
  --bigquery-table=project:dataset.events_raw \
  --use-topic-schema \
  --write-metadata \
  --drop-unknown-fields
```
- Stream directly to BigQuery tables
- Schema auto-mapping from topic schema
- Metadata columns (publish_time, message_id, attributes)
- No Dataflow pipeline needed

#### Cloud Storage Export
```bash
gcloud pubsub subscriptions create events-to-gcs \
  --topic=events \
  --cloud-storage-bucket=events-archive \
  --cloud-storage-file-prefix=events/ \
  --cloud-storage-max-duration=5m \
  --cloud-storage-output-format=avro
```
- Archive to GCS in Avro or JSON format
- Configurable file size/duration batching
- Automatic file rotation

#### Bigtable Export (Preview)
```bash
gcloud pubsub subscriptions create events-to-bt \
  --topic=events \
  --bigtable-table=projects/p/instances/i/tables/events
```
- Low-latency write to Bigtable
- Ideal for real-time serving layer

## Single Message Transforms (SMT)

Apply lightweight transformations in-flight:

### PII Redaction
```python
def transform(message):
    import json, hashlib
    data = json.loads(message.data)
    # Hash PII fields
    if 'email' in data:
        data['email'] = hashlib.sha256(data['email'].encode()).hexdigest()[:16]
    # Remove sensitive fields
    for field in ['ssn', 'credit_card', 'password']:
        data.pop(field, None)
    return json.dumps(data).encode()
```

### Schema Transformation
```python
def transform(message):
    import json
    data = json.loads(message.data)
    # Flatten nested structure
    return json.dumps({
        'user_id': data['user']['id'],
        'event': data['event']['type'],
        'timestamp': data['metadata']['created_at'],
        'value': data['payload'].get('value', 0),
    }).encode()
```

### Use Cases
- PII redaction before storage
- Schema migration (v1 → v2)
- Field extraction and enrichment
- Format conversion (JSON → Avro)
- Payload compression/decompression

## Exactly-Once Delivery

### Setup
```python
from google.cloud import pubsub_v1

# Create subscription with exactly-once
subscriber = pubsub_v1.SubscriberClient()
subscriber.create_subscription(
    request={
        "name": "projects/p/subscriptions/exactly-once-sub",
        "topic": "projects/p/topics/critical-events",
        "enable_exactly_once_delivery": True,
        "enable_message_ordering": True,
    }
)

# Publish with ordering key (required for exactly-once)
publisher = pubsub_v1.PublisherClient()
publisher.publish(
    "projects/p/topics/critical-events",
    data=b'{"transaction_id": "tx_001"}',
    ordering_key="user_123"
)
```

### Idempotent Subscriber Pattern
```python
def callback(message):
    tx_id = json.loads(message.data)['transaction_id']
    # Check if already processed (idempotent check)
    if not is_processed(tx_id):
        process(message.data)
        mark_processed(tx_id)
    message.ack()
```

## Message Patterns

### Fan-Out
```
publisher → topic → subscription1 → consumer1 (analytics)
                  → subscription2 → consumer2 (billing)
                  → subscription3 → export_bq (archive)
```

### Request-Reply
```python
# Requester publishes and waits for reply
publisher.publish(request_topic, data, reply_topic='reply-topic-123')
# Responder reads, processes, publishes reply
```

### Dead Letter Queue
```bash
gcloud pubsub subscriptions create my-sub \
  --topic=events \
  --dead-letter-topic=events-dlq \
  --max-delivery-attempts=10 \
  --dead-letter-topic-project=my-project
```

### Message Filtering
```bash
# Server-side filtering (reduces cost)
gcloud pubsub subscriptions create filtered-sub \
  --topic=events \
  --message-filter='attributes.event_type = "purchase"'
```

Filter syntax:
- `attributes.key = "value"` — Exact match
- `hasPrefix(attributes.key, "prefix")` — Prefix match
- `attributes.key != "value"` — Not equal
- `NOT attributes:key` — Attribute not present

## Configuration Best Practices

| Setting | Default | Recommendation |
|---------|---------|---------------|
| Ack deadline | 10s | Match processing time (max 600s) |
| Message retention | 7d | Set based on replay needs (max 31d) |
| Max delivery attempts | 5 | Higher for critical data (10-20) |
| DLQ | None | Always configure for production |
| Ordering | Disabled | Enable only when needed (limits throughput) |
| Flow control | None | Set max_outstanding_messages for pull |

## Monitoring

### Key Metrics
```bash
# Most important metrics to monitor:
# 1. subscription/oldest_unacked_message_age — Processing lag
# 2. subscription/num_undelivered_messages  — Backlog size
# 3. subscription/dead_letter_message_count — Failed messages
# 4. topic/send_request_count               — Publish rate

gcloud monitoring dashboards create --config-from-file=pubsub-dashboard.json
```

### Alert Thresholds
| Metric | Warning | Critical |
|--------|---------|----------|
| Oldest unacked age | > 60s | > 300s |
| Backlog size | > 10K | > 100K |
| DLQ count | > 0 | > 100 |
| Publish errors | > 1% | > 5% |

## Migration Guide

### Pub/Sub Lite → Pub/Sub (Lite deprecated March 2026)
1. Create standard Pub/Sub topics mirroring Lite topics
2. Update publishers to use standard Pub/Sub client
3. Create subscriptions with matching configurations
4. Migrate subscribers with feature mapping
5. Verify message delivery and ordering
6. Decommission Lite resources

### Kafka → Pub/Sub
| Kafka Concept | Pub/Sub Equivalent |
|--------------|-------------------|
| Topic | Topic |
| Partition | Ordering key |
| Consumer Group | Subscription |
| Offset commit | Acknowledgment |
| Consumer lag | oldest_unacked_message_age |
| Dead letter topic | Dead letter topic |

## gcloud Commands Reference

```bash
# Topic management
gcloud pubsub topics create my-topic
gcloud pubsub topics list
gcloud pubsub topics describe my-topic
gcloud pubsub topics delete my-topic

# Subscription management
gcloud pubsub subscriptions create my-sub --topic=my-topic
gcloud pubsub subscriptions list
gcloud pubsub subscriptions describe my-sub
gcloud pubsub subscriptions seek my-sub --time=2026-04-01T00:00:00Z

# Message operations
gcloud pubsub topics publish my-topic --message='{"event": "test"}'
gcloud pubsub subscriptions pull my-sub --auto-ack --limit=10

# Schema management
gcloud pubsub schemas create my-schema \
  --type=AVRO --definition-file=schema.avsc
gcloud pubsub topics create my-topic --schema=my-schema
```

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| Messages not delivered | Subscription inactive/permissions | Check IAM, verify subscription |
| Processing lag growing | Slow consumers | Scale consumers, optimize processing |
| Message ordering issues | Missing ordering keys | Use consistent ordering keys |
| High DLQ count | Poison messages | Inspect DLQ, fix consumer logic |
| Publish failures | Quota exceeded | Request increase, add batching |
| Duplicate messages | No deduplication | Enable exactly-once or add idempotency |
| Export failures | Schema mismatch | Update target schema, check mapping |

## Resources

- [Pub/Sub Documentation](https://cloud.google.com/pubsub/docs)
- [Export Subscriptions](https://cloud.google.com/pubsub/docs/export-subscriptions)
- [Single Message Transforms](https://cloud.google.com/pubsub/docs/single-message-transforms)
- [Exactly-Once Delivery](https://cloud.google.com/pubsub/docs/exactly-once-delivery)
- [Architecture Guide](https://cloud.google.com/pubsub/docs/overview)
- [Pricing Calculator](https://cloud.google.com/pubsub/pricing)
