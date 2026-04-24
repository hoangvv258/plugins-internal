---
description: Train ML models in BigQuery using SQL — classification, regression, forecasting, LLM integration, remote models
---

# BigQuery ML Training Assistant

Train machine learning models directly in BigQuery using SQL — no Python, no notebooks, no infrastructure management required.

## Supported Model Types

| Model | SQL Function | Use Case |
|-------|-------------|----------|
| Linear Regression | `LINEAR_REG` | Price prediction, demand forecasting |
| Logistic Regression | `LOGISTIC_REG` | Binary/multi-class classification |
| Boosted Trees (XGBoost) | `BOOSTED_TREE_CLASSIFIER/REGRESSOR` | High-accuracy ML tasks |
| DNN | `DNN_CLASSIFIER/REGRESSOR` | Complex pattern recognition |
| K-Means | `KMEANS` | Customer segmentation, clustering |
| PCA | `PCA` | Dimensionality reduction |
| Matrix Factorization | `MATRIX_FACTORIZATION` | Recommendation systems |
| Time-Series (ARIMA+) | `ARIMA_PLUS` | Time-series forecasting |
| TimesFM | `TIMESERIES_MODEL` | Zero-shot forecasting |
| AutoML Tables | `AUTOML_CLASSIFIER/REGRESSOR` | Automated model selection |
| Remote Model | `REMOTE` | Vertex AI / Gemini models |

## Training Examples

### Classification (Churn Prediction)
```sql
CREATE OR REPLACE MODEL `project.dataset.churn_model`
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',
  input_label_cols = ['churned'],
  data_split_method = 'AUTO_SPLIT',
  max_iterations = 50,
  early_stop = TRUE,
  min_split_loss = 0.1,
  l2_reg = 0.1
) AS
SELECT
  user_id,
  days_since_last_login,
  total_purchases,
  avg_session_duration,
  support_tickets_count,
  subscription_type,
  churned  -- Label column (TRUE/FALSE)
FROM `project.dataset.user_features`
WHERE created_date > '2025-01-01';
```

### Regression (Revenue Forecasting)
```sql
CREATE OR REPLACE MODEL `project.dataset.revenue_model`
OPTIONS(
  model_type = 'LINEAR_REG',
  input_label_cols = ['daily_revenue'],
  optimize_strategy = 'NORMAL_EQUATION'
) AS
SELECT
  day_of_week,
  month,
  is_holiday,
  marketing_spend,
  active_users,
  daily_revenue
FROM `project.dataset.revenue_features`;
```

### Time-Series Forecasting (ARIMA+)
```sql
CREATE OR REPLACE MODEL `project.dataset.sales_forecast`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'sales',
  time_series_id_col = 'product_id',
  auto_arima = TRUE,
  holiday_region = 'US'
) AS
SELECT date, product_id, sales
FROM `project.dataset.daily_sales`
WHERE date > '2024-01-01';

-- Generate forecast
SELECT *
FROM ML.FORECAST(MODEL `project.dataset.sales_forecast`,
  STRUCT(30 AS horizon, 0.95 AS confidence_level));
```

### Zero-Shot Forecasting (TimesFM)
```sql
-- No training data needed — pre-trained foundation model
SELECT *
FROM AI.FORECAST(
  MODEL `project.dataset.timesfm_model`,
  TABLE `project.dataset.time_series_data`,
  STRUCT(30 AS horizon, 0.95 AS confidence_level)
);
```

### Customer Segmentation (K-Means)
```sql
CREATE OR REPLACE MODEL `project.dataset.customer_segments`
OPTIONS(
  model_type = 'KMEANS',
  num_clusters = 5,
  standardize_features = TRUE
) AS
SELECT
  avg_order_value,
  purchase_frequency,
  days_since_last_purchase,
  total_lifetime_value
FROM `project.dataset.customer_features`;

-- Predict segments
SELECT * FROM ML.PREDICT(MODEL `project.dataset.customer_segments`,
  TABLE `project.dataset.new_customers`);
```

### Remote Model (Gemini via Vertex AI)
```sql
-- Create connection to Vertex AI
CREATE OR REPLACE MODEL `project.dataset.gemini_model`
REMOTE WITH CONNECTION `project.us.vertex_connection`
OPTIONS(
  endpoint = 'gemini-2.5-flash'
);

-- Use for text generation
SELECT
  product_name,
  ML.GENERATE_TEXT(
    MODEL `project.dataset.gemini_model`,
    CONCAT('Write a product description for: ', product_name),
    STRUCT(100 AS max_output_tokens, 0.3 AS temperature)
  ) AS description
FROM `project.dataset.products`;
```

## AI Functions (No Model Creation Needed)

```sql
-- Classification
SELECT AI.CLASSIFY(text, ['spam', 'not_spam']) AS label
FROM `project.dataset.emails`;

-- Conditional AI (cost-efficient)
SELECT AI.IF(text, 'Is this a complaint?') AS is_complaint
FROM `project.dataset.support_tickets`;

-- Anomaly Detection
SELECT * FROM AI.DETECT_ANOMALIES(
  MODEL `project.dataset.anomaly_model`,
  TABLE `project.dataset.metrics`);

-- Key Drivers Analysis
SELECT * FROM AI.KEY_DRIVERS(
  TABLE `project.dataset.metrics`,
  'revenue',
  STRUCT('2026-Q1' AS current_period, '2025-Q4' AS baseline_period)
);
```

## Model Evaluation

```sql
-- Evaluate model performance
SELECT * FROM ML.EVALUATE(MODEL `project.dataset.churn_model`);

-- Feature importance
SELECT * FROM ML.FEATURE_IMPORTANCE(MODEL `project.dataset.churn_model`);

-- Confusion matrix
SELECT * FROM ML.CONFUSION_MATRIX(MODEL `project.dataset.churn_model`);

-- ROC curve data
SELECT * FROM ML.ROC_CURVE(MODEL `project.dataset.churn_model`);
```

## Output

I'll provide:
- ✓ Model training SQL with optimal hyperparameters
- ✓ Feature engineering recommendations
- ✓ Model evaluation and metrics interpretation
- ✓ Prediction queries for production use
- ✓ Cost estimation for training and inference
- ✓ Model registry and versioning guidance

---

Describe your ML use case and I'll design the BQML solution.
