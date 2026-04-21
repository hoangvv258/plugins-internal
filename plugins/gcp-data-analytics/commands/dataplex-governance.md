---
id: dataplex-governance
name: Dataplex Data Governance
description: Set up Dataplex Universal Catalog — data quality, lineage, access control, business glossary
---

# Dataplex Data Governance Setup

Configure Dataplex Universal Catalog for unified data governance across your GCP data platform.

## Setup Data Catalog

### Create Dataplex Lake & Zones
```bash
# Create a Dataplex lake (logical grouping)
gcloud dataplex lakes create analytics-lake \
  --location=us-central1 \
  --display-name="Analytics Data Lake" \
  --description="Central analytics data platform"

# Create a raw zone
gcloud dataplex zones create raw-zone \
  --lake=analytics-lake \
  --location=us-central1 \
  --type=RAW \
  --resource-location-type=SINGLE_REGION \
  --display-name="Raw Data Zone" \
  --discovery-enabled

# Create a curated zone
gcloud dataplex zones create curated-zone \
  --lake=analytics-lake \
  --location=us-central1 \
  --type=CURATED \
  --resource-location-type=SINGLE_REGION \
  --display-name="Curated Data Zone" \
  --discovery-enabled
```

### Register Data Assets
```bash
# Add BigQuery dataset as asset
gcloud dataplex assets create bq-analytics \
  --lake=analytics-lake \
  --zone=curated-zone \
  --location=us-central1 \
  --resource-type=BIGQUERY_DATASET \
  --resource-name=projects/project/datasets/analytics \
  --display-name="Analytics BigQuery Dataset" \
  --discovery-enabled

# Add GCS bucket as asset
gcloud dataplex assets create gcs-raw-data \
  --lake=analytics-lake \
  --zone=raw-zone \
  --location=us-central1 \
  --resource-type=STORAGE_BUCKET \
  --resource-name=projects/project/buckets/raw-data-lake \
  --display-name="Raw Data Lake Storage" \
  --discovery-enabled
```

## Data Quality Rules

### Define Quality Checks
```yaml
# data_quality_spec.yaml
rules:
  - nonNullExpectation: {}
    column: event_id
    dimension: COMPLETENESS
    description: "Event ID must not be null"
    threshold: 1.0  # 100% non-null required

  - rangeExpectation:
      minValue: "0"
      maxValue: "100000"
    column: revenue
    dimension: VALIDITY
    description: "Revenue must be between 0 and 100,000"
    threshold: 0.99  # 99% must pass

  - uniquenessExpectation: {}
    column: event_id
    dimension: UNIQUENESS
    description: "Event IDs must be unique"
    threshold: 1.0

  - regexExpectation:
      regex: "^[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}$"
    column: email
    dimension: VALIDITY
    description: "Email must be valid format"
    threshold: 0.95

  - setExpectation:
      values: ["US", "CA", "UK", "DE", "FR", "JP", "AU"]
    column: country
    dimension: CONSISTENCY
    description: "Country must be in allowed set"
    threshold: 0.99

  - statistic_range_expectation:
      statistic: MEAN
      minValue: "10"
      maxValue: "500"
    column: session_duration
    dimension: VALIDITY
    description: "Average session duration should be 10-500 seconds"

  - sqlExpression: >
      SELECT COUNT(*) = 0
      FROM `project.dataset.events`
      WHERE event_timestamp > CURRENT_TIMESTAMP()
    dimension: TIMELINESS
    description: "No future timestamps allowed"
```

### Run Quality Scan
```bash
# Create data quality scan
gcloud dataplex datascans create data-quality events-quality-scan \
  --location=us-central1 \
  --data-source-entity=projects/project/locations/us-central1/lakes/analytics-lake/zones/curated-zone/entities/events \
  --data-quality-spec-file=data_quality_spec.yaml \
  --display-name="Events Quality Scan" \
  --description="Daily quality checks for events table" \
  --schedule="0 7 * * *"  # Daily at 7 AM

# Run scan immediately
gcloud dataplex datascans run events-quality-scan \
  --location=us-central1

# View results
gcloud dataplex datascans jobs list \
  --datascan=events-quality-scan \
  --location=us-central1
```

## Business Glossary

### Create Terms and Categories
```bash
# Create glossary category
gcloud dataplex glossaries categories create customer-metrics \
  --glossary=business-glossary \
  --location=us-central1 \
  --display-name="Customer Metrics" \
  --description="Standard definitions for customer-related KPIs"

# Create glossary term
gcloud dataplex glossaries terms create ltv \
  --glossary=business-glossary \
  --location=us-central1 \
  --category=customer-metrics \
  --display-name="Customer Lifetime Value (LTV)" \
  --description="Total revenue attributed to a customer over their entire relationship" \
  --related-terms=projects/project/locations/us-central1/glossaries/business-glossary/terms/arpu
```

## Data Lineage

### Enable Lineage Tracking
```bash
# Lineage is automatically tracked for:
# - BigQuery queries (SQL transformations)
# - Dataflow pipelines
# - Dataproc Spark jobs
# - Cloud Composer DAGs

# View lineage for a table
gcloud dataplex lineage search-links \
  --target=bigquery:project.dataset.daily_summary \
  --location=us-central1

# View processes that wrote to a table
gcloud dataplex lineage list-runs \
  --location=us-central1 \
  --filter="outputs.dataset='project.dataset.daily_summary'"
```

## Access Control

### Tag-Based Access Policies
```bash
# Create taxonomy for data classification
gcloud data-catalog taxonomies create \
  --display-name="Data Classification" \
  --description="PII and sensitivity classification" \
  --location=us-central1

# Create policy tags
gcloud data-catalog taxonomies policy-tags create \
  --taxonomy=TAXONOMY_ID \
  --display-name="PII" \
  --description="Personally Identifiable Information"

gcloud data-catalog taxonomies policy-tags create \
  --taxonomy=TAXONOMY_ID \
  --display-name="Confidential" \
  --description="Internal confidential data"

# Apply to BigQuery column
bq update --schema schema.json project:dataset.table
# schema.json includes policyTags for sensitive columns
```

### Data Masking
```sql
-- Dynamic data masking policy
CREATE DATA MASKING RULE email_mask
ON `project.dataset.users`.email
USING MASK(SHA256)
FOR 'group:analysts@company.com';

-- Column-level security with masking
ALTER TABLE `project.dataset.users`
ALTER COLUMN ssn
SET OPTIONS(
  policy_tags = '{"names":["projects/project/locations/US/taxonomies/TAX_ID/policyTags/PII"]}'
);
```

## Dashboard Monitoring

### Key Governance Metrics
- Data quality score trends by dataset
- Number of cataloged vs uncataloged assets
- Access control coverage (% with policies)
- Lineage completeness
- Glossary term adoption

## Output

I'll provide:
- ✓ Dataplex lake, zone, and asset configuration
- ✓ Data quality rules for your tables
- ✓ Business glossary terms
- ✓ Lineage tracking setup
- ✓ Access control and masking policies
- ✓ Monitoring dashboard configuration

---

Describe your data governance requirements and I'll design the solution.
