---
description: Comprehensive monitoring for Pub/Sub topics, subscriptions, Export Subscriptions, and SMT
---

# Pub/Sub Monitoring & Alerts

Help me set up monitoring and alerting for your Pub/Sub infrastructure, including Export Subscriptions and SMT.

## Key Metrics to Monitor

### Topic Metrics
| Metric | Description | Alert Threshold |
|--------|-------------|----------------|
| `topic/send_request_count` | Messages published | Sudden drop = publisher issue |
| `topic/send_message_operation_count` | Successful publishes | Compare with request count |
| `topic/message_sizes` | Message payload size | > 10MB = near limit |
| `topic/byte_cost` | Billable bytes | For cost tracking |

### Subscription Metrics
| Metric | Description | Alert Threshold |
|--------|-------------|----------------|
| `subscription/oldest_unacked_message_age` | Processing lag | > 300s = falling behind |
| `subscription/num_undelivered_messages` | Backlog size | Growing = consumer issue |
| `subscription/push_request_latencies` | Push delivery time | > 1000ms (push only) |
| `subscription/dead_letter_message_count` | Failed messages | > 0 = processing errors |
| `subscription/exactly_once_ack_request_count` | Exactly-once acks | Monitor for duplicates |

### Export Subscription Metrics
| Metric | Description | Alert Threshold |
|--------|-------------|----------------|
| `subscription/export_request_count` | Export attempts | Drops = export issues |
| `subscription/export_throughput` | Export data rate | Below expected rate |
| `subscription/export_error_count` | Export failures | > 0 = investigate |

## Alert Configurations

### Processing Lag Alert (Critical)
```yaml
displayName: "Pub/Sub Processing Lag > 5 minutes"
combiner: OR
conditions:
  - displayName: "Oldest unacked message"
    conditionThreshold:
      filter: >
        resource.type = "pubsub_subscription"
        AND metric.type = "pubsub.googleapis.com/subscription/oldest_unacked_message_age"
      comparison: COMPARISON_GT
      thresholdValue: 300  # seconds
      duration: 60s
      aggregations:
        - alignmentPeriod: 60s
          perSeriesAligner: ALIGN_MAX
notificationChannels:
  - projects/PROJECT/notificationChannels/CHANNEL_ID
```

### Dead Letter Queue Alert
```yaml
displayName: "DLQ Messages Increasing"
conditions:
  - conditionThreshold:
      filter: >
        metric.type = "pubsub.googleapis.com/subscription/dead_letter_message_count"
      comparison: COMPARISON_GT
      thresholdValue: 10
      duration: 300s
      aggregations:
        - alignmentPeriod: 300s
          perSeriesAligner: ALIGN_RATE
```

### High Backlog Alert
```yaml
displayName: "Message Backlog > 100K"
conditions:
  - conditionThreshold:
      filter: >
        metric.type = "pubsub.googleapis.com/subscription/num_undelivered_messages"
      comparison: COMPARISON_GT
      thresholdValue: 100000
      duration: 300s
```

### Export Subscription Failure Alert
```yaml
displayName: "Export Subscription Errors"
conditions:
  - conditionThreshold:
      filter: >
        metric.type = "pubsub.googleapis.com/subscription/export_error_count"
      comparison: COMPARISON_GT
      thresholdValue: 0
      duration: 60s
```

## Setup Commands

```bash
# List all Pub/Sub metrics available
gcloud monitoring metrics-descriptors list \
  --filter="metric.type:pubsub"

# Create notification channel (email)
gcloud alpha monitoring channels create \
  --display-name="Engineering Team" \
  --type=email \
  --channel-labels=email_address=team@company.com

# Create alert policy from YAML
gcloud alpha monitoring policies create \
  --policy-from-file=alert-policy.yaml

# View subscription metrics
gcloud monitoring time-series list \
  --filter="metric.type=\"pubsub.googleapis.com/subscription/oldest_unacked_message_age\"" \
  --interval-start-time=$(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ) \
  --format=table

# View Pub/Sub logs
gcloud logging read \
  'resource.type="pubsub_topic" OR resource.type="pubsub_subscription"' \
  --limit=50 --format=json
```

## Dashboard Setup

### Recommended Dashboard Panels

1. **Overview Row**
   - Total messages published/min (all topics)
   - Total subscribers active
   - Total DLQ messages (gauge)

2. **Per-Topic Row**
   - Publish rate (messages/sec)
   - Message size distribution (p50, p95, p99)
   - Publish error rate

3. **Per-Subscription Row**
   - Processing lag (oldest unacked age)
   - Backlog size (undelivered messages)
   - Delivery success rate
   - Acknowledgment latency

4. **Export Subscription Row**
   - Export throughput (bytes/sec)
   - Export error rate
   - BigQuery/GCS write latency

5. **Cost Row**
   - Monthly cost by topic
   - Byte cost trends
   - Message count trends

## Troubleshooting Runbook

| Symptom | Likely Cause | Resolution |
|---------|-------------|------------|
| Rising backlog | Slow consumers | Scale consumers, check processing time |
| DLQ messages | Poison messages | Inspect DLQ, fix consumer logic |
| Publish errors | Quota exceeded | Request quota increase, add batching |
| High latency | Large messages | Reduce payload, use references |
| Export failures | Schema mismatch | Update BigQuery schema, check mapping |
| Ordering violations | Missing ordering key | Ensure consistent ordering key usage |

---

What aspects of Pub/Sub would you like to monitor?
