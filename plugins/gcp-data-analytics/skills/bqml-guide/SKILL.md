---
name: BigQuery ML Guide
description: Complete guide to BigQuery ML — model training, AI functions, remote models, evaluation, and deployment
version: 1.0.0
---

# BigQuery ML Guide Skill

Train, evaluate, and deploy machine learning models directly in BigQuery using SQL — no Python, no infrastructure.

## Why BigQuery ML?

- **SQL-native** — Data scientists and analysts use familiar SQL
- **No data movement** — Train on data where it lives
- **Managed infrastructure** — No cluster management, no GPUs to configure
- **Integrated** — Works with BigQuery's security, governance, and scheduling
- **Cost-effective** — Pay only for queries, use existing slots

## Model Types Reference

### Supervised Learning

| Model | Type | SQL | Best For |
|-------|------|-----|----------|
| Linear Regression | Regression | `LINEAR_REG` | Price prediction, continuous targets |
| Logistic Regression | Classification | `LOGISTIC_REG` | Binary/multi-class (fast, explainable) |
| Boosted Trees (XGBoost) | Both | `BOOSTED_TREE_*` | High accuracy, tabular data |
| Random Forest | Both | `RANDOM_FOREST_*` | Ensemble, resistant to overfitting |
| DNN | Both | `DNN_*` | Complex patterns, large datasets |
| Wide & Deep | Both | `WIDE_AND_DEEP_*` | Memorization + generalization |
| AutoML Tables | Both | `AUTOML_*` | Automated model selection |

### Unsupervised Learning

| Model | Type | SQL | Best For |
|-------|------|-----|----------|
| K-Means | Clustering | `KMEANS` | Customer segmentation |
| PCA | Dimensionality | `PCA` | Feature reduction |
| Autoencoder | Anomaly | `AUTOENCODER` | Anomaly detection |
| Matrix Factorization | Recommendation | `MATRIX_FACTORIZATION` | Recommendations |

### Time-Series

| Model | Type | SQL | Best For |
|-------|------|-----|----------|
| ARIMA+ | Forecasting | `ARIMA_PLUS` | Traditional time-series |
| ARIMA+ XREG | Forecasting | `ARIMA_PLUS_XREG` | With external regressors |
| TimesFM | Zero-shot | Via `AI.FORECAST` | No training needed |

### Remote & Generative AI

| Model | Type | SQL | Best For |
|-------|------|-----|----------|
| Remote Model | External | `REMOTE` | Vertex AI endpoints |
| Gemini | GenAI | Via connection | Text generation, analysis |
| Embeddings | Vector | Via connection | Semantic search, similarity |

## Training Workflow

### Step 1: Feature Engineering
```sql
-- Create training features view
CREATE OR REPLACE VIEW `project.ml.training_features` AS
SELECT
  -- Target
  CASE WHEN last_login < DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
       THEN 1 ELSE 0 END AS churned,
  -- Numeric features
  days_since_registration,
  total_purchases,
  avg_order_value,
  support_tickets_30d,
  login_frequency_7d,
  -- Categorical features
  subscription_tier,
  acquisition_channel,
  country,
  -- Derived features
  total_purchases / GREATEST(days_since_registration, 1) AS purchase_rate,
  CASE WHEN total_purchases > 10 THEN 'power' 
       WHEN total_purchases > 3 THEN 'regular'
       ELSE 'casual' END AS user_tier
FROM `project.analytics.user_features`
WHERE days_since_registration > 30;  -- Minimum observation period
```

### Step 2: Train Model
```sql
CREATE OR REPLACE MODEL `project.ml.churn_model`
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',
  input_label_cols = ['churned'],
  -- Training configuration
  data_split_method = 'AUTO_SPLIT',
  data_split_eval_fraction = 0.2,
  -- Hyperparameters
  num_parallel_tree = 1,
  max_iterations = 100,
  early_stop = TRUE,
  min_split_loss = 0.01,
  max_tree_depth = 8,
  subsample = 0.8,
  colsample_bytree = 0.8,
  l1_reg = 0.1,
  l2_reg = 1.0,
  learn_rate = 0.1,
  -- Class balancing
  auto_class_weights = TRUE,
  -- Evaluation
  enable_global_explain = TRUE
) AS
SELECT * FROM `project.ml.training_features`;
```

### Step 3: Evaluate Model
```sql
-- Overall metrics (accuracy, precision, recall, F1, AUC)
SELECT * FROM ML.EVALUATE(MODEL `project.ml.churn_model`);

-- Confusion matrix
SELECT * FROM ML.CONFUSION_MATRIX(MODEL `project.ml.churn_model`);

-- ROC curve data points
SELECT * FROM ML.ROC_CURVE(MODEL `project.ml.churn_model`);

-- Feature importance
SELECT * FROM ML.FEATURE_IMPORTANCE(MODEL `project.ml.churn_model`)
ORDER BY importance_weight DESC;

-- Global explanations (Shapley values)
SELECT * FROM ML.GLOBAL_EXPLAIN(MODEL `project.ml.churn_model`);
```

### Step 4: Predict
```sql
-- Batch prediction
SELECT
  user_id,
  predicted_churned,
  predicted_churned_probs[OFFSET(0)].prob AS churn_probability
FROM ML.PREDICT(MODEL `project.ml.churn_model`,
  TABLE `project.analytics.current_users`)
WHERE predicted_churned_probs[OFFSET(0)].prob > 0.7
ORDER BY churn_probability DESC;

-- Per-row explanation (why this prediction?)
SELECT *
FROM ML.EXPLAIN_PREDICT(MODEL `project.ml.churn_model`,
  (SELECT * FROM `project.analytics.current_users` WHERE user_id = 'U001'),
  STRUCT(3 AS top_k_features));
```

### Step 5: Export or Deploy
```sql
-- Export model to Cloud Storage (TensorFlow SavedModel format)
EXPORT MODEL `project.ml.churn_model`
OPTIONS(uri = 'gs://models/churn_model/v1/');

-- Deploy to Vertex AI endpoint for online serving
-- (Use gcloud or Vertex AI SDK after export)
```

## AI Functions (No Training Required)

### Text Analysis
```sql
-- Sentiment classification
SELECT
  review_text,
  AI.CLASSIFY(review_text, ['positive', 'negative', 'neutral']) AS sentiment
FROM `project.dataset.reviews`;

-- Boolean classification (cost-efficient)
SELECT
  comment,
  AI.IF(comment, 'Does this mention a product defect?') AS has_defect
FROM `project.dataset.comments`;

-- Text generation
SELECT
  product_name,
  AI.GENERATE(
    CONCAT('Write a 2-sentence marketing tagline for: ', product_name)
  ) AS tagline
FROM `project.dataset.products`;
```

### Time-Series (Zero-Shot)
```sql
-- Forecast without training (uses pre-trained TimesFM)
SELECT * FROM AI.FORECAST(
  MODEL `project.ml.timesfm`,
  TABLE `project.dataset.daily_sales`,
  STRUCT(
    30 AS horizon,
    0.95 AS confidence_level
  )
);
```

### Anomaly Detection
```sql
-- Train anomaly model
CREATE MODEL `project.ml.anomaly_model`
OPTIONS(model_type='AUTOENCODER', ...) AS ...;

-- Detect anomalies
SELECT * FROM AI.DETECT_ANOMALIES(
  MODEL `project.ml.anomaly_model`,
  TABLE `project.dataset.metrics`,
  STRUCT(0.01 AS contamination));
```

### Key Drivers Analysis
```sql
-- What's driving revenue changes?
SELECT * FROM AI.KEY_DRIVERS(
  TABLE `project.dataset.metrics`,
  'revenue',  -- metric to analyze
  STRUCT(
    '2026-Q1' AS current_period,
    '2025-Q4' AS baseline_period
  )
);
```

## Remote Models (Vertex AI)

### Create Connection
```bash
# Create Vertex AI connection
bq mk --connection \
  --connection_type=CLOUD_RESOURCE \
  --location=US \
  vertex-connection

# Grant Vertex AI access to connection service account
gcloud projects add-iam-policy-binding project \
  --member='serviceAccount:SA_EMAIL' \
  --role='roles/aiplatform.user'
```

### Use Gemini for Analysis
```sql
CREATE MODEL `project.ml.gemini`
REMOTE WITH CONNECTION `project.US.vertex-connection`
OPTIONS(endpoint = 'gemini-2.5-flash');

-- Analyze customer feedback
SELECT
  feedback_text,
  ML.GENERATE_TEXT(
    MODEL `project.ml.gemini`,
    CONCAT(
      'Analyze this customer feedback. Extract: ',
      '1) Sentiment (positive/negative/neutral) ',
      '2) Key topics mentioned ',
      '3) Action items. Feedback: ', feedback_text
    ),
    STRUCT(200 AS max_output_tokens, 0.2 AS temperature)
  ).ml_generate_text_result AS analysis
FROM `project.dataset.feedback`
LIMIT 100;
```

### Use Custom Vertex AI Model
```sql
CREATE MODEL `project.ml.custom_model`
REMOTE WITH CONNECTION `project.US.vertex-connection`
OPTIONS(endpoint = 'projects/project/locations/us-central1/endpoints/ENDPOINT_ID');

SELECT * FROM ML.PREDICT(MODEL `project.ml.custom_model`,
  TABLE `project.dataset.inference_data`);
```

## Hyperparameter Tuning

```sql
-- Use HP_TUNE_OBJECTIVES for automatic tuning
CREATE MODEL `project.ml.tuned_model`
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',
  input_label_cols = ['target'],
  num_trials = 20,
  max_parallel_trials = 5,
  hparam_tuning_objectives = ['ROC_AUC'],
  -- Hyperparameter search ranges
  max_tree_depth = HPARAM_RANGE(3, 15),
  learn_rate = HPARAM_RANGE(0.01, 0.3),
  subsample = HPARAM_RANGE(0.5, 1.0),
  l2_reg = HPARAM_RANGE(0.01, 10.0)
) AS
SELECT * FROM `project.ml.training_features`;

-- View trial results
SELECT * FROM ML.TRIAL_INFO(MODEL `project.ml.tuned_model`)
ORDER BY roc_auc DESC;
```

## Real-World ML Patterns

### Recommendation System
```sql
-- Train collaborative filtering model
CREATE MODEL `project.ml.recommender`
OPTIONS(
  model_type = 'MATRIX_FACTORIZATION',
  user_col = 'user_id',
  item_col = 'product_id',
  rating_col = 'rating',
  num_factors = 50
) AS SELECT user_id, product_id, rating FROM `project.dataset.ratings`;

-- Get recommendations for a user
SELECT * FROM ML.RECOMMEND(MODEL `project.ml.recommender`,
  (SELECT 'user_123' AS user_id))
ORDER BY predicted_rating DESC LIMIT 10;
```

### Demand Forecasting
```sql
CREATE MODEL `project.ml.demand_forecast`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'units_sold',
  time_series_id_col = 'sku',
  auto_arima = TRUE,
  holiday_region = 'US',
  decompose_time_series = TRUE
) AS SELECT date, sku, units_sold FROM `project.dataset.sales`;

SELECT * FROM ML.FORECAST(MODEL `project.ml.demand_forecast`,
  STRUCT(90 AS horizon, 0.9 AS confidence_level));
```

## Cost Optimization

| Strategy | Savings | How |
|----------|---------|-----|
| Use flat-rate slots | 30-50% | Train on reserved slots |
| AutoML last resort | 60-80% | Try simpler models first |
| Feature selection | 20-40% | Remove low-importance features |
| Limit training data | 10-30% | Sample if > 10M rows |
| Schedule training | 20-40% | Train during off-peak hours |

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Low accuracy | Insufficient features | Add more features, feature engineering |
| Overfitting | Model too complex | Reduce depth, add regularization |
| Training timeout | Too much data | Sample data, reduce iterations |
| High cost | AutoML or too many trials | Use simpler model first |
| Prediction errors | Schema mismatch | Ensure prediction data matches training |

## Resources

- [BigQuery ML Docs](https://cloud.google.com/bigquery/docs/bqml-introduction)
- [ML.EVALUATE Reference](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-evaluate)
- [AI Functions](https://cloud.google.com/bigquery/docs/ai-functions)
- [Remote Models](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-remote-model)
- [Hyperparameter Tuning](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-hp-tuning)
