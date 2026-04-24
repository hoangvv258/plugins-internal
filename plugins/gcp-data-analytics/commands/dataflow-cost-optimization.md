---
description: Optimize Dataflow pipeline costs — Streaming Engine, Prime, Spot VMs, autoscaling, right-sizing
---

# Dataflow Cost Optimization

Help me optimize your Dataflow pipeline costs by understanding your current setup and recommending the best strategies.

## Cost Drivers

### Compute Costs
| Component | Cost Factor | Optimization |
|-----------|------------|--------------|
| Worker vCPUs | Per vCPU-hour | Right-size machine types |
| Worker memory | Per GB-hour | Reduce memory per worker |
| Worker count | × compute cost | Tune autoscaling |
| Execution time | Total duration | Optimize transforms |
| GPU (if used) | Per GPU-hour | Use only for ML inference |

### Storage Costs
| Component | Cost Factor | Optimization |
|-----------|------------|--------------|
| Shuffle storage | Intermediate data | Use Service Shuffle |
| Persistent disk | Per GB-month | Minimize disk size |
| Streaming state | State backend | Clean up old state |
| Log storage | Cloud Logging | Filter log verbosity |

### Network Costs
| Component | Cost Factor | Optimization |
|-----------|------------|--------------|
| Cross-region | Per GB transferred | Co-locate resources |
| Internet egress | Per GB | Minimize external calls |

## Optimization Strategies

### 1. Streaming Engine (20-40% savings)
```python
# Offload streaming to managed infrastructure
options.view_as(StandardOptions).streaming = True
options.view_as(GoogleCloudOptions).enable_streaming_engine = True
# Reduces worker resource needs, Google manages autoscaling
```

### 2. Dataflow Prime (Automatic right-fitting)
```python
# Enable Prime for automatic resource allocation
options.view_as(GoogleCloudOptions).experiments = ['enable_prime']
# Per-transform resource allocation, vertical autoscaling
```

### 3. Spot VMs (60-91% savings)
```bash
# Batch jobs: use Spot VMs for massive savings
python pipeline.py \
  --runner DataflowRunner \
  --use_public_ips=false \
  --dataflow_service_options=use_runner_v2 \
  --experiments=use_runner_v2 \
  --machine_type=n2-standard-4 \
  --disk_size_gb=30
  # Spot VMs are default for batch in Dataflow
```

### 4. Machine Type Optimization
```
Workload Type         → Recommended Machine    → Monthly Estimate
──────────────────────┼────────────────────────┼──────────────────
Light ETL             → n2-standard-2          → $50-100/worker
Standard processing   → n2-standard-4 (default)→ $100-200/worker
Heavy transformations → n2-standard-8          → $200-400/worker
Memory-intensive      → n2-highmem-4           → $130-250/worker
ML inference (GPU)    → n1-standard-4 + T4     → $400-800/worker
```

### 5. Autoscaling Tuning
```python
# Batch: control worker scaling
options.view_as(WorkerOptions).num_workers = 5      # Starting workers
options.view_as(WorkerOptions).max_num_workers = 50  # Max workers
options.view_as(WorkerOptions).autoscaling_algorithm = 'THROUGHPUT_BASED'

# Streaming: tune utilization target
options.view_as(GoogleCloudOptions).experiments = [
    'min_num_workers=2',
    'max_num_workers=20',
]
```

### 6. Shuffle Optimization
```python
# Batch: Service-based shuffle (faster, predictable cost)
options.view_as(GoogleCloudOptions).experiments = ['shuffle_mode=service']

# Avoid: resource-based shuffle for large jobs
# (uses worker disk, slower, variable cost)
```

### 7. Code-Level Optimizations
```python
# ✓ DO: Pre-filter data early in pipeline
pipeline | 'FilterEarly' >> beam.Filter(is_valid) | 'Transform' >> ...

# ✗ DON'T: Transform then filter
pipeline | 'Transform' >> ... | 'FilterLate' >> beam.Filter(is_valid)

# ✓ DO: Use Combiners for aggregation (pre-aggregation on workers)
pipeline | beam.CombinePerKey(sum)

# ✗ DON'T: GroupByKey + manual sum (all data shuffled to one worker)
pipeline | beam.GroupByKey() | beam.Map(lambda kv: (kv[0], sum(kv[1])))

# ✓ DO: Use generators for memory efficiency
class ProcessFn(beam.DoFn):
    def process(self, element):
        yield transform(element)  # Generator, not list

# ✓ DO: Avoid large side inputs (< 100MB)
# Use BigQuery lookup or external API for large reference data
```

### 8. Resource Monitoring
```bash
# Check job cost breakdown
gcloud dataflow jobs describe JOB_ID \
  --region=us-central1 \
  --format="table(currentState,currentStateTime,type)"

# Monitor worker utilization
gcloud dataflow metrics list JOB_ID \
  --region=us-central1
```

## Cost Comparison Table

| Strategy | Savings | Effort | Risk |
|----------|---------|--------|------|
| Streaming Engine | 20-40% | Low | None |
| Spot VMs (batch) | 60-91% | Low | Job preemption |
| Dataflow Prime | 15-30% | Low | Preview |
| Machine right-sizing | 10-50% | Medium | Under-provisioning |
| Code optimization | 20-60% | Medium | Bug risk |
| Autoscaling tuning | 10-30% | Medium | Under/over-scaling |

## Cost Analysis Questions

1. What's your current monthly Dataflow spend?
2. Batch or streaming pipelines (or both)?
3. How long do batch pipelines run?
4. What's your current worker configuration?
5. Are you using Streaming Engine?
6. What transformations are most resource-intensive?

---

Share your pipeline details and I'll recommend cost optimizations.
