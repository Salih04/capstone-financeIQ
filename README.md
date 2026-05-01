# FinanceIQ – Multi-Model Stock Scoring and Comparison Platform

FinanceIQ is a BIST-focused stock scoring and comparison platform that uses yearly stock datasets from 2020–2025 and multiple machine learning models to generate explainable stock scores.

The platform is designed for academic decision-support and financial analysis research. It focuses on reliability, transparency, model validation, and prevention of fake or misleading outputs.

FinanceIQ does not provide guaranteed investment advice.

---

## Core Purpose

FinanceIQ helps users:

- Import yearly stock datasets from Excel files
- Score a single stock using a selected machine learning model
- Compare multiple stocks using all supported models together
- Rank stocks based on ensemble model outputs
- Detect unavailable company-period data
- Handle missing numerical feature values using median imputation
- View warnings, model status, data completeness, and explanation details

---

## Current Dataset Structure

The main dataset source is the `3.Datasets/` folder.

3.Datasets/
├── 2020stocks.xlsx
├── 2021stocks.xlsx
├── 2022stocks.xlsx
├── 2023stocks.xlsx
├── 2024stocks.xlsx
└── 2025stocks.xlsx

Each Excel file represents one year of stock data.

Important assumptions:

- Each year may contain a different number of companies.
- A company may exist in one year but not another.
- The system must not assume that every company exists in every year.
- If a company does not have data for the selected year or quarter, it must be excluded from scoring/comparison.
- Missing numerical feature values inside an existing row are handled with median imputation.
- Missing company-period rows must never be artificially created.

If the Excel file does not contain a `year` column, the system should infer the year from the filename.

Example:

2024stocks.xlsx -> year = 2024

---

## Supported Models

FinanceIQ supports five models.

| Model | Key | Purpose |
|---|---|---|
| ElasticNet | `elasticnet` | Regularized linear baseline model |
| Random Forest Regressor | `random_forest` | Non-linear tree-based regression model |
| XGBoost Regressor | `xgboost` | Gradient boosting model for tabular financial data |
| SARIMAX | `sarimax` | Time-series model for stock-level temporal behavior |
| Temporal Fusion Transformer | `tft` | Deep learning time-series model for temporal forecasting |

---

## Model Usage Logic

### Single Stock Scoring

When scoring one stock, the user selects one model.

Example models available in the UI:

ElasticNet
Random Forest Regressor
XGBoost Regressor
SARIMAX
Temporal Fusion Transformer

The backend should return:

- Stock code
- Selected year
- Selected quarter or period
- Selected model
- Score
- Confidence, if available and valid
- Data completeness
- Missing features
- Imputed features
- Model status
- Explanation
- Warnings

Example request:

{
  "stock_code": "AKSEN",
  "year": 2024,
  "quarter": "Q4",
  "model": "xgboost"
}

Example response:

{
  "stock_code": "AKSEN",
  "year": 2024,
  "quarter": "Q4",
  "model": "xgboost",
  "score": 78.4,
  "confidence": 0.72,
  "data_completeness": "18 / 22 features",
  "missing_features": ["market_cap"],
  "imputed_features": ["roe"],
  "warnings": [],
  "method_note": "Score generated using XGBoost Regressor trained with time-aware validation."
}

---

### Stock Comparison

When comparing multiple stocks, the user should not select one model.

For comparison, all five models must run together:

ElasticNet
Random Forest Regressor
XGBoost Regressor
SARIMAX
Temporal Fusion Transformer

The comparison result should include:

- Individual score from each model
- Ensemble average score
- Ensemble rank
- Model agreement/disagreement
- Score standard deviation
- Data completeness
- Missing/imputed features
- Warnings for excluded companies

Example request:

{
  "stock_codes": ["AKSEN", "THYAO", "EREGL"],
  "year": 2024,
  "quarter": "Q4"
}

Example response:

{
  "items": [
    {
      "stock_code": "AKSEN",
      "year": 2024,
      "quarter": "Q4",
      "scores": {
        "elasticnet": 71.2,
        "random_forest": 76.8,
        "xgboost": 78.4,
        "sarimax": 69.5,
        "tft": 80.1
      },
      "ensemble_score": 75.2,
      "ensemble_rank": 1,
      "model_agreement": "medium",
      "score_std": 4.1,
      "data_completeness": "18 / 22 features",
      "imputed_features": ["roe"]
    }
  ],
  "warnings": [
    "EREGL has no data for 2024Q4 and was excluded."
  ]
}

---

## Reliability Principles

FinanceIQ must be reliable, trustworthy, and transparent.

The system must not fake:

- Scores
- Predictions
- Confidence values
- Model outputs
- Feature importance values
- Explanations
- Evaluation metrics
- Comparison rankings

If a valid output cannot be produced, the backend must return a clear error or warning.

The backend must return validation errors when:

- The dataset has not been imported
- The requested stock does not exist in the selected year/quarter
- The requested model is not trained
- A model artifact cannot be loaded
- Required columns are missing
- There is not enough historical data for SARIMAX
- There is not enough historical data for Temporal Fusion Transformer
- A prediction would require future data leakage
- The selected period is outside the available dataset range

Wrong behavior:

Returning random scores
Hardcoding example values
Creating fake company-period rows
Using another year’s data silently
Using stock_code as a shortcut feature
Showing mock outputs in production endpoints

Correct behavior:

Return a warning if data is unavailable
Return an error if the model is not trained
Exclude unavailable companies from comparison
Report which features were missing or imputed
Use only valid historical data
Use stored trained model artifacts

---

## Learning, Not Memorization

The machine learning system must learn general financial patterns instead of memorizing companies.

Therefore:

- Do not use `stock_code` as a direct predictive feature.
- Do not use company name as a direct predictive feature.
- Do not use future values while training for earlier predictions.
- Do not use target values as features.
- Do not randomly split time-series data without considering chronology.
- Do not fit imputers, scalers, or encoders on validation/test/prediction data.

Recommended predictive feature groups:

Profitability
Liquidity
Leverage
Growth
Margins
Cash flow
Valuation
Sector-relative features
Period-over-period changes
Historical lag features
Rolling averages
Volatility-style features

Examples of good training design:

Train: 2020–2023
Validation: 2024
Test / Prediction: 2025

or:

Train 2020–2021 -> Validate 2022
Train 2020–2022 -> Validate 2023
Train 2020–2023 -> Validate 2024
Train 2020–2024 -> Validate 2025

---

## Missing Values and Median Imputation

FinanceIQ uses median imputation for missing numerical feature values.

Rules:

- Median imputation is used only for numerical feature values.
- The imputer must be fitted only on training data.
- The fitted imputer is reused for validation, test, and prediction data.
- The system must record which features were imputed.
- Imputed features should be included in the API response.
- Missing company-period rows must not be created with imputation.

Correct use:

AKSEN exists in 2024Q4 but roe is missing -> use median imputation for roe.

Incorrect use:

AKSEN does not exist in 2024Q4 -> create fake AKSEN 2024Q4 row using medians.

Example imputation output:

{
  "imputation": {
    "strategy": "median",
    "imputed_features": ["roe", "current_ratio", "market_cap"],
    "note": "Median values were learned from the training dataset only."
  }
}

---

## Company-Period Validation

Because yearly datasets may contain different companies, every scoring and comparison request must validate company availability.

Example:

{
  "stock_codes": ["AKSEN", "THYAO", "XYZ"],
  "year": 2024,
  "quarter": "Q4"
}

If `XYZ` does not exist in the selected year/quarter, it should be excluded.

Correct response:

{
  "items": [
    {
      "stock_code": "AKSEN",
      "ensemble_score": 75.2
    },
    {
      "stock_code": "THYAO",
      "ensemble_score": 72.6
    }
  ],
  "warnings": [
    "XYZ has no data for 2024Q4 and was excluded."
  ]
}

The system should never silently replace missing company-period data with another year’s data.

---

## Recommended Backend ML Structure

Recommended folder structure:

2.backend/app/ml/
├── config.py
├── data_loader.py
├── preprocessing.py
├── feature_engineering.py
├── model_registry.py
├── trainers/
│   ├── elasticnet_trainer.py
│   ├── random_forest_trainer.py
│   ├── xgboost_trainer.py
│   ├── sarimax_trainer.py
│   └── tft_trainer.py
├── predictors/
│   ├── single_predictor.py
│   └── comparison_predictor.py
├── evaluation.py
└── artifacts.py

Suggested responsibilities:

| File | Responsibility |
|---|---|
| `data_loader.py` | Load yearly Excel files and merge them into one clean dataset |
| `preprocessing.py` | Validate columns, handle missing values, fit/apply imputers |
| `feature_engineering.py` | Create ratios, lag features, rolling features, sector-relative features |
| `model_registry.py` | Register and safely select supported models |
| `trainers/` | Train each model separately |
| `predictors/` | Single-stock and comparison prediction logic |
| `evaluation.py` | Time-aware validation and evaluation metrics |
| `artifacts.py` | Save/load trained models, imputers, scalers, feature lists, metadata |

---

## Model Registry

The backend should use a model registry to avoid unsafe model selection.

Example:

SUPPORTED_MODELS = {
    "elasticnet": ElasticNetTrainer,
    "random_forest": RandomForestTrainer,
    "xgboost": XGBoostTrainer,
    "sarimax": SARIMAXTrainer,
    "tft": TemporalFusionTransformerTrainer,
}

Single-stock scoring should accept one model key.

Comparison should automatically use all five supported models.

---

## Suggested Training Priority

Implementation should be done in phases.

### Phase 1 — Stable Tabular ML

Implement first:

ElasticNet
Random Forest Regressor
XGBoost Regressor

These models are the most practical starting point for tabular financial data.

### Phase 2 — Classical Time-Series

Then implement:

SARIMAX

SARIMAX should only run when enough historical observations exist for the selected stock.

### Phase 3 — Deep Time-Series

Finally implement:

Temporal Fusion Transformer

TFT is more complex and should be added after the data pipeline, validation logic, and baseline models are stable.

---

## API Endpoints

### Dataset Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/datasets/import-yearly` | Import Excel files from `3.Datasets/` |
| GET | `/datasets/available-years` | List available dataset years |
| GET | `/datasets/available-periods` | List available years and quarters |
| GET | `/datasets/summary` | Show row counts, company counts, missing values, and feature coverage |
| GET | `/stocks/available` | List stocks available for selected year/quarter |

---

### Model Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/models/train` | Train one or more models |
| GET | `/models/status` | Check trained model availability |
| POST | `/models/evaluate` | Run time-aware model evaluation |
| GET | `/models/metrics` | Retrieve stored model performance metrics |
| GET | `/models/features` | Retrieve feature list used by each model |

---

### Scoring Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/stocks/score` | Score one stock with selected model |
| POST | `/scoring/compare` | Compare multiple stocks using all five models |
| GET | `/score-runs/{run_id}` | Retrieve stored score run |
| GET | `/users/me/score-runs` | List recent score runs |

---

## Single Stock Scoring Endpoint

### POST /stocks/score

Request:

{
  "stock_code": "AKSEN",
  "year": 2024,
  "quarter": "Q4",
  "model": "xgboost"
}

Response:

{
  "stock_code": "AKSEN",
  "year": 2024,
  "quarter": "Q4",
  "model": "xgboost",
  "score": 78.4,
  "confidence": 0.72,
  "data_completeness": "18 / 22 features",
  "missing_features": ["market_cap"],
  "imputed_features": ["roe"],
  "warnings": [],
  "explanation": {
    "method_note": "Score generated using XGBoost Regressor trained with time-aware validation.",
    "strongest_drivers": ["roe", "revenue_growth", "ebitda_margin"],
    "weakest_drivers": ["debt_ratio", "negative_ocf"]
  }
}

Possible error:

{
  "detail": "XGBoost model is not trained. Please train the model before scoring."
}

Possible warning:

{
  "detail": "AKSEN has no data for 2024Q4."
}

---

## Comparison Endpoint

### POST /scoring/compare

Request:

{
  "stock_codes": ["AKSEN", "THYAO", "EREGL"],
  "year": 2024,
  "quarter": "Q4"
}

Response:

{
  "items": [
    {
      "stock_code": "AKSEN",
      "year": 2024,
      "quarter": "Q4",
      "scores": {
        "elasticnet": 71.2,
        "random_forest": 76.8,
        "xgboost": 78.4,
        "sarimax": 69.5,
        "tft": 80.1
      },
      "ensemble_score": 75.2,
      "ensemble_rank": 1,
      "model_agreement": "medium",
      "score_std": 4.1,
      "data_completeness": "18 / 22 features",
      "missing_features": ["market_cap"],
      "imputed_features": ["roe"]
    }
  ],
  "warnings": [
    "EREGL has no data for 2024Q4 and was excluded."
  ]
}

If one model cannot produce a score for a valid company, the response should clearly show that model as unavailable rather than inventing a number.

Example:

{
  "stock_code": "AKSEN",
  "scores": {
    "elasticnet": 71.2,
    "random_forest": 76.8,
    "xgboost": 78.4,
    "sarimax": null,
    "tft": null
  },
  "model_warnings": {
    "sarimax": "Not enough historical observations for SARIMAX.",
    "tft": "TFT model artifact is not available."
  },
  "ensemble_score": 75.47,
  "ensemble_note": "Ensemble score calculated from available valid model outputs only."
}

---

## Ensemble Logic

For comparison, the default ensemble score should be the average of available valid model scores.

Rules:

- Use only valid model outputs.
- Do not include failed models as zero.
- Do not include unavailable models in the average.
- Return warnings for unavailable models.
- Return model agreement using score standard deviation.

Example model agreement logic:

score_std <= 3      -> high agreement
score_std <= 7      -> medium agreement
score_std > 7       -> low agreement

Example:

{
  "ensemble_score": 75.2,
  "score_std": 4.1,
  "model_agreement": "medium"
}

---

## Frontend Pages

### Login

Route:

/login

Purpose:

- User authentication
- Entry point of the app

---

### Dashboard

Route:

/dashboard

Purpose:

- General app overview
- Dataset status
- Model training status
- Recent score runs
- Data quality summary

---

### Scoring Page

Recommended route:

/scoring

Purpose:

Score a single stock using a selected model.

Inputs:

Stock
Year
Quarter
Model selector

Model selector options:

ElasticNet
Random Forest Regressor
XGBoost Regressor
SARIMAX
Temporal Fusion Transformer

Outputs:

Score
Selected model
Confidence
Data completeness
Missing features
Imputed features
Warnings
Explanation

---

### Comparison Page

Recommended route:

/compare

Purpose:

Compare multiple stocks using all five models.

Inputs:

Selected stocks
Year
Quarter
Compare button

Do not show a single-model selector for comparison.

Output table:

Stock | ElasticNet | Random Forest | XGBoost | SARIMAX | TFT | Ensemble Score | Rank | Agreement

Also show:

Warnings
Excluded companies
Unavailable model outputs
Data completeness

---

### Validation Lab

Route:

/validation

Purpose:

- Show model evaluation results
- Compare models
- Display time-aware validation metrics
- Show train/validation/test periods
- Detect overfitting risk
- Detect suspiciously high performance

---

### Data Health

Route:

/data-health

Purpose:

- Show imported dataset status
- Row count by year
- Company count by year
- Missing value summary
- Duplicate row detection
- Available periods
- Feature coverage
- Company availability by period

---

## Quick Start

### Requirements

- Docker
- Docker Compose
- Python 3.12
- Node.js 20+

---

### Run with Docker

From the project root:

cd Capstone_Code
docker compose up --build

Services:

| Service | URL |
|---|---|
| Frontend | `http://localhost:3000` |
| Backend | `http://localhost:8000` |
| API Docs | `http://localhost:8000/docs` |

Default entry route:

/login

---

## Local Development

### Backend

cd 2.backend
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

If needed, create `.env`:

echo "DATABASE_URL=postgresql://postgres:postgres@localhost:5432/capstone_db" > .env

---

### Frontend

cd 1.frontend
npm install
npm run dev

---

## Database Migrations

If the backend uses Alembic:

cd 2.backend
alembic upgrade head

The database should support storing:

- Imported dataset rows
- Available companies
- Available periods
- Model artifacts metadata
- Training runs
- Evaluation metrics
- Score runs
- Comparison runs
- Warnings and explanations

---

## Recommended Database Tables

Suggested tables:

StockDatasetRow
ModelTrainingRun
ModelArtifact
ModelEvaluationMetric
StockScoreRun
StockComparisonRun
StockComparisonItem
DataQualityReport

### StockDatasetRow

Stores normalized rows from the Excel datasets.

Recommended fields:

id
stock_code
company_name
sector
year
quarter
period
feature values
target_score
source_file
created_at

### ModelTrainingRun

Stores model training metadata.

Recommended fields:

id
model_key
training_start_period
training_end_period
validation_period
test_period
feature_count
row_count
status
created_at

### ModelArtifact

Stores artifact metadata.

Recommended fields:

id
model_key
artifact_path
imputer_path
scaler_path
feature_list_path
training_run_id
created_at

### ModelEvaluationMetric

Stores validation metrics.

Recommended fields:

id
model_key
training_run_id
metric_name
metric_value
period
created_at

### StockScoreRun

Stores single-stock score results.

Recommended fields:

id
user_id
stock_code
year
quarter
model_key
score
confidence
data_completeness
missing_features
imputed_features
warnings
created_at

### StockComparisonRun

Stores comparison request metadata.

Recommended fields:

id
user_id
year
quarter
ensemble_method
warnings
created_at

### StockComparisonItem

Stores company-level comparison results.

Recommended fields:

id
comparison_run_id
stock_code
elasticnet_score
random_forest_score
xgboost_score
sarimax_score
tft_score
ensemble_score
ensemble_rank
score_std
model_agreement
missing_features
imputed_features
model_warnings

---

## Data Import Pipeline

Recommended import flow:

1. Read all Excel files from 3.Datasets/
2. Infer year from filename if year column is missing
3. Normalize column names
4. Validate required columns
5. Convert numerical columns safely
6. Standardize stock_code format
7. Detect duplicates
8. Store clean rows in database
9. Generate data quality report

Pseudo-flow:

2020stocks.xlsx
2021stocks.xlsx
2022stocks.xlsx
2023stocks.xlsx
2024stocks.xlsx
2025stocks.xlsx
        ↓
Load and normalize
        ↓
Validate columns
        ↓
Create unified dataset
        ↓
Generate features
        ↓
Train models
        ↓
Score / compare

---

## Feature Engineering

Recommended feature groups:

### Profitability

roe
roa
gross_margin
ebitda_margin
net_profit_margin
operating_margin

### Liquidity

current_ratio
quick_ratio
cash_ratio
net_working_capital

### Leverage

debt_ratio
debt_to_equity
net_debt
interest_coverage

### Growth

revenue_growth
net_income_growth
ebitda_growth
asset_growth
equity_growth

### Cash Flow

ocf
free_cash_flow
ocf_margin
capex_ratio

### Valuation

price_to_earnings
price_to_book
ev_to_ebitda
market_cap
enterprise_value

### Time-Based Features

lag_1_score
lag_2_score
rolling_mean_4q
rolling_std_4q
year
quarter_number

### Sector-Relative Features

sector_median_roe
sector_percentile_roe
sector_zscore_roe
sector_relative_margin
sector_relative_growth

---

## Model-Specific Notes

### ElasticNet

ElasticNet should be used as a regularized linear baseline.

Recommended preprocessing:

Median imputation
Scaling
Time-aware train/validation split

Use when:

Need interpretable baseline
Need stable performance estimate
Need comparison against complex models

---

### Random Forest Regressor

Random Forest should be used for non-linear tabular patterns.

Recommended preprocessing:

Median imputation
No mandatory scaling
Time-aware validation
Feature importance extraction

Use when:

Need robust non-linear model
Need feature importance
Dataset size is moderate

---

### XGBoost Regressor

XGBoost should be used as the main high-performance tabular model.

Recommended preprocessing:

Median imputation
Careful validation
Early stopping where possible
Hyperparameter tuning

Use when:

Need strong tabular prediction performance
Need feature importance
Need comparison with Random Forest

---

### SARIMAX

SARIMAX should be used only when sufficient historical data exists for a stock.

Rules:

- It should not run for stocks with too few historical observations.
- It should return a clear warning if unavailable.
- It should not fake output using another stock’s history.
- It may require stock-specific time series.
- It should use chronological order only.

Example warning:

{
  "sarimax": "Not enough historical observations for SARIMAX."
}

---

### Temporal Fusion Transformer

Temporal Fusion Transformer should be added only after the tabular pipeline is stable.

Rules:

- Requires carefully structured time-series data.
- Requires enough historical observations.
- Requires saved model artifacts.
- Should return a clear warning if unavailable.
- Should not be used as a placeholder model.

Example warning:

{
  "tft": "TFT model artifact is not available or insufficient sequence length."
}

---

## Evaluation Metrics

Recommended regression metrics:

MAE
RMSE
R2
MAPE, if valid
Spearman rank correlation
Top-K precision, if ranking stocks

For ranking quality:

Spearman correlation
Kendall tau
Top 5 overlap
Top 10 overlap
Hit rate

Validation output should include:

Model name
Training period
Validation period
Test period
Number of rows
Number of companies
Feature count
Metric values
Warnings

---

## Model Status Output

Example:

{
  "models": {
    "elasticnet": {
      "trained": true,
      "last_trained_at": "2026-05-01T12:30:00",
      "training_rows": 4200
    },
    "random_forest": {
      "trained": true,
      "last_trained_at": "2026-05-01T12:35:00",
      "training_rows": 4200
    },
    "xgboost": {
      "trained": true,
      "last_trained_at": "2026-05-01T12:40:00",
      "training_rows": 4200
    },
    "sarimax": {
      "trained": false,
      "reason": "Not enough stock-level historical observations."
    },
    "tft": {
      "trained": false,
      "reason": "TFT implementation not trained yet."
    }
  }
}

---

## Explainability

The system should provide transparent explanation output.

For tabular models, include:

Strongest positive drivers
Weakest drivers
Feature importance
Missing features
Imputed features
Data completeness
Model method note
Validation performance

Example:

{
  "explanation": {
    "method_note": "Score generated using XGBoost Regressor.",
    "data_completeness_label": "18 / 22 features",
    "strongest_drivers": ["roe", "ebitda_margin", "revenue_growth"],
    "weakest_drivers": ["debt_ratio", "negative_ocf", "low_current_ratio"],
    "imputed_features": ["market_cap"],
    "validation_note": "Model was validated using chronological split."
  }
}

Explanations must be based on real model behavior or real feature values.

Do not invent explanation details.

---

## Security and Production Notes

The app should not expose:

.env files
Database passwords
API keys
Model artifact internals
User tokens
Private logs

`.gitignore` should include:

.env
.venv/
venv/
node_modules/
dist/
__pycache__/
.pytest_cache/
*.pkl
*.joblib
*.pt
*.ckpt
model_artifacts/

Dataset files may be included or excluded depending on project submission requirements.

---

## Git Notes

The dataset files currently appear as untracked files.

Example:

2020stocks.xlsx
2021stocks.xlsx
2022stocks.xlsx
2023stocks.xlsx
2024stocks.xlsx
2025stocks.xlsx

Before committing, decide whether the datasets should be included in the repository.

If datasets are required for capstone evaluation, commit them intentionally.

If datasets are private or too large, exclude them and provide instructions for placing them in:

3.Datasets/

---

## Recommended Implementation Order

The safest implementation order is:

1. Update dataset import logic for 2020–2025 Excel files.
2. Create a unified clean dataset table.
3. Add company-period validation.
4. Add median imputation pipeline.
5. Add feature engineering.
6. Implement ElasticNet.
7. Implement Random Forest Regressor.
8. Implement XGBoost Regressor.
9. Add model registry.
10. Add single-stock scoring endpoint.
11. Add comparison endpoint using all valid model outputs.
12. Add model status endpoint.
13. Add evaluation endpoint.
14. Add frontend model selector for single-stock scoring.
15. Add frontend comparison table with all five models.
16. Add SARIMAX.
17. Add Temporal Fusion Transformer.
18. Update Data Health and Validation Lab pages.

---

## Important Development Rule

Do not start with Temporal Fusion Transformer.

The base pipeline should first work correctly with:

ElasticNet
Random Forest Regressor
XGBoost Regressor

Then SARIMAX and TFT can be added safely.

This reduces project risk and ensures the platform remains functional even if the advanced time-series models require more development time.

---

## Academic Disclaimer

FinanceIQ is an academic research and decision-support platform.

The outputs are generated from historical financial data and machine learning models. They should not be interpreted as guaranteed investment advice, trading signals, or financial recommendations.

Users should evaluate model results critically and combine them with independent financial analysis.

---

## Project Status

Current refactor direction:

Old system:
Winner-only forecasting with older dataset assumptions.

New system:
Multi-model stock scoring and comparison using 2020–2025 yearly Excel datasets.

Main refactor goals:

Reliable outputs
No fake scores
No data leakage
No memorization through stock codes
Median imputation for missing numerical values
Clear warnings for missing company-period data
All-model ensemble comparison
User-selected model for single-stock scoring