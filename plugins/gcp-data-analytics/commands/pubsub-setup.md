---
description: Configure Pub/Sub topics, subscriptions, Export Subscriptions, SMT, and Exactly-once delivery
---

# Pub/Sub Setup Assistant

I'll help you configure Google Cloud Pub/Sub for your event streaming needs, including Export Subscriptions, Single Message Transforms, and Exactly-once delivery.

## Configuration Areas

1. **Topic Design** — naming, message schema, retention
2. **Subscription Setup** — push/pull, delivery guarantees, filtering
3. **Export Subscriptions** — direct to BigQuery, GCS, or Bigtable
4. **Single Message Transforms** — in-flight data processing
5. **Message Format** — Protocol Buffers, Avro, JSON schema
6. **Exactly-Once Delivery** — deduplication and ordering
7. **Dead Letter Queues** — error handling and retry policies

## Standard Topic & Subscription Setup

```bash
# Create topic with schema
gcloud pubsub topics create user-events \
  --message-retention-duration=7d \
  --schema=user-event-schema \
  --message-encoding=JSON

# Pull subscription with ordering
gcloud pubsub subscriptions create user-events-sub \
  --topic=user-events \
  --ack-deadline=60 \
  --enable-message-ordering \
  --dead-letter-topic=user-events-dlq \
  --max-delivery-attempts=10

# Push subscription to Cloud Run
gcloud pubsub subscriptions create user-events-push \
  --topic=user-events \
  --push-endpoint=https://my-service-xyz.run.app/webhook \
  --push-auth-service-account=pubsub-push@project.iam.gserviceaccount.com
```

## Export Subscriptions (No Dataflow Required)

### BigQuery Export
```bash
# Stream messages directly to BigQuery table
gcloud pubsub subscriptions create events-to-bq \
  --topic=user-events \
  --bigquery-table=project:dataset.events_raw \
  --use-topic-schema \
  --write-metadata \
  --drop-unknown-fields
```

### Cloud Storage Export
```bash
# Archive messages to GCS (Avro format)
gcloud pubsub subscriptions create events-to-gcs \
  --topic=user-events \
  --cloud-storage-bucket=my-events-archive \
  --cloud-storage-file-prefix=events/ \
  --cloud-storage-file-suffix=.avro \
  --cloud-storage-max-duration=5m \
  --cloud-storage-max-bytes=1GB \
  --cloud-storage-output-format=avro
```

### Bigtable Export (Preview)
```bash
# Stream directly to Bigtable
gcloud pubsub subscriptions create events-to-bt \
  --topic=user-events \
  --bigtable-table=projects/project/instances/instance/tables/events
```

## Single Message Transforms (SMT)

Apply transformations in-flight without external services:

```python
# Example: PII redaction transform function
def transform(message):
    import json
    data = json.loads(message.data)
    # Redact email
    if 'email' in data:
        data['email'] = data['email'].split('@')[0][:2] + '***@' + data['email'].split('@')[1]
    # Remove sensitive fields
    data.pop('ssn', None)
    data.pop('credit_card', None)
    return json.dumps(data).encode()
```

## Exactly-Once Delivery Setup

```python
from google.cloud import pubsub_v1

# Publisher with ordering key
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path('project', 'my-topic')

# Enable ordering on publisher
publisher.publish(
    topic_path,
    data=b'message',
    ordering_key='user_123'  # FIFO per ordering key
)

# Subscriber with exactly-once
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path('project', 'my-sub')

# Enable exactly-once delivery
subscriber.create_subscription(
    request={
        "name": subscription_path,
        "topic": topic_path,
        "enable_exactly_once_delivery": True,
    }
)
```

## Message Filtering

```bash
# Only receive messages matching a filter
gcloud pubsub subscriptions create filtered-sub \
  --topic=user-events \
  --message-filter='attributes.event_type = "purchase" AND attributes.country = "US"'
```

## Output

I'll provide:
- ✓ Topic and subscription configuration
- ✓ Export Subscription setup (BigQuery/GCS/Bigtable)
- ✓ gcloud commands and Terraform configs
- ✓ Code examples (Python, Java, Node.js)
- ✓ Monitoring and alerting recommendations
- ✓ Cost estimation and optimization tips

---

Describe your event streaming architecture and requirements.
