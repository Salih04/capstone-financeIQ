<!-- LLM_IGNORE_START -->
# Implementation Checklist (So Far)

This document tracks what has been implemented in the project up to now.

## Product & Flow

- [x] Login-first entry flow enabled (`/` -> `/login`)
- [x] Register/Login error rendering fixed on frontend (no React object render crash)
- [x] Forecasting page added and integrated into app routing
- [x] Forecasting detail page added (trend/importance/heatmap)
- [x] News & Updates page added with AI insight panel
- [x] Forecasting discoverable from sidebar and dashboard card
- [x] Start Analysis landing flow removed per latest request

## Backend API

- [x] Forecasting router created and mounted
- [x] Added endpoints:
  - [x] `POST /upload-data`
  - [x] `POST /train-model`
  - [x] `POST /predict`
  - [x] `GET /get-stocks`
  - [x] `GET /get-parameters`
  - [x] `GET /get-stock-detail`
  - [x] `GET /get-explanation`
  - [x] `POST /get-portfolio-analysis`
  - [x] `GET /predict/history`
  - [x] `POST /predict/evaluate`
  - [x] `GET /predict/trends`
  - [x] `GET /predict/heatmap`
  - [x] `GET /parameters/catalog`
  - [x] `POST /fundamentals/upload-csv`
  - [x] `GET /news/updates`
- [x] User profile endpoints added (`/users/me`, `/users/me/profile`)

## Data Model & Migrations

- [x] Alembic setup added (`alembic.ini`, `alembic/env.py`, versions)
- [x] Forecasting tables added:
  - [x] `winner_cohort_rows`
  - [x] `sector_parameter_rankings`
  - [x] `forecast_runs`
  - [x] `forecast_predictions`
- [x] Evaluation tables added:
  - [x] `forecast_evaluation_runs`
  - [x] `forecast_evaluation_folds`
- [x] User onboarding fields migration added:
  - [x] `user_type`, `risk_level`, `investment_scope`, `sector_focus`
- [x] Quarterly fundamentals table added:
  - [x] `quarterly_fundamentals`

## Forecasting Engine

- [x] Winner Excel preset import for 2023/2024/2025
- [x] Sector/year filtering and constraints (2023..2025)
- [x] Parameter ranking methods implemented:
  - [x] Spearman
  - [x] Pearson
  - [x] Mutual Information
  - [x] Random Forest importance
  - [x] RFE
  - [x] LASSO
  - [x] SHAP (with fallback handling)
  - [x] Clustering similarity signal
- [x] Multi-method ensemble scoring implemented
- [x] Time-CV evaluation (rolling window) added
- [x] Predict history retrieval added
- [x] Alternative model modes wired as first-class option inputs:
  - [x] `scoring`
  - [x] `dbscan`
  - [x] `gmm`
  - [x] `xgboost`
  - [x] `prophet`
  - [x] `arima`

## Exact Ratios & Fundamentals

- [x] Quarterly fundamentals CSV upload service implemented
- [x] Required schema validation added for upload
- [x] Exact ratio computation path implemented (no proxy formulas)
- [x] Forecasting/training now depends on quarterly fundamentals availability (Q4 requirement for yearly run)
- [x] Parameter catalog endpoint added using requested ratio definitions

## Corporate & Explainability

- [x] Portfolio analysis endpoint implemented (weak/strong/action suggestions)
- [x] Explanation payloads integrated in forecast results
- [x] Confidence and trend outputs included in prediction response

## Ops / Automation

- [x] Batch retrain script added (`retrain_forecasting.py`)
- [x] Incremental retrain script added (`incremental_retrain.py`)
- [x] Pipeline runner script added (`pipeline_runner.py`)
- [x] Airflow DAG template added
- [x] Deployment and forecasting operation docs added

## Infrastructure Scaffolding

- [x] AWS starter IaC scaffold added
- [x] Azure starter deployment docs scaffold added
- [x] GCP starter deployment docs scaffold added

## Cleanup / Stability Fixes

- [x] Removed duplicate blocks in `backend/app/main.py`
- [x] Removed duplicate scoring/schema sections introduced by v2/v3 drift
- [x] Added startup compatibility hotfix for missing `users` columns on existing DBs

## Validation Status

- [x] Backend syntax/compile checks pass (`python -m compileall app`)
- [x] Frontend production build passes (`npm run build`)

## Suggested (Finished) 

- [x] Add downloadable quarterly fundamentals CSV template file in repo
- [x] Add strict API contract tests for forecasting endpoints
- [x] Add E2E tests for login -> upload -> train -> predict -> detail flow
- [x] Add CI workflow for migration + backend + frontend checks

## Financial Health Scoring – Reliability & Quality Fixes

### Critical Bug Fixes

- [x] Fixed NoneType crash in `explanation_service.py`: `weight` and `contribution` now cast with `float(... or 0.0)` before any arithmetic
- [x] Removed redundant dead-code `if contribution is None` guard that followed

### Cash Flow Data Integrity

- [x] Removed `or 0` fallback on `ocf_to_debt`, `ocf_to_assets`, `cash_flow_margin` in `ratio_service.py`
- [x] Missing OCF now correctly returns `None` (excluded from scoring) instead of fake `0`
- [x] Added TODO comment in `ratio_service.py` explaining OCF is absent from CLEANED_Financial and documenting future formulas

### Data Pipeline

- [x] Created `scripts/rebuild_financial_pipeline.py` — 8-step full rebuild:
  1. Clear `computed_metrics`
  2. Import `CLEANED_Financial` → `QuarterlyFundamental`
  3. Generate `ComputedMetric` from `QuarterlyFundamental`
  4. Generate `MetricTransition` per company
  5. Generate `SectorBenchmark` per period
  6. Generate `SectorNormalizedFeature` per company per period
  7. Clear `sector_parameter_rankings`
  8. Print validation summary (companies, periods, missing fields, duplicates)

### Scoring Reliability

- [x] Confirmed: missing metrics are excluded from `available_weight`, never zeroed — score is `raw_total / available_weight * 100`
- [x] Sector normalization clamps already in place: `percentile = max(0, min(1, percentile))`, `blended = max(0, min(weight, blended))`

### Machine Learning

- [x] Replaced fake circular label (`score >= 55`) with real label: `next_period_net_income > current_period_net_income`
- [x] Implemented time-based 80/20 train/test split by period (oldest 80% train, newest 20% validate)
- [x] Validation metrics printed to server logs on each prediction: accuracy, precision, recall, F1, AUC, confusion matrix
- [x] `label_used` field now reports `"logistic_real_label"` to distinguish from the old fake-label mode

### Compare Page

- [x] `compare_companies` now returns `{"items": [...], "warnings": [...]}` instead of a bare list
- [x] Companies missing data for a requested period emit a human-readable warning (e.g. `"AKSEN has no data for 2022Q2 and was excluded."`) instead of silently dropping
- [x] `CompareResult` schema extended with `warnings: list[str] = []`
- [x] Router updated to unpack and forward warnings to the response

### UI Trust & Transparency

- [x] `rich_explanation.data_completeness_label` added — human-readable `"9 / 12 metrics"` string
- [x] `rich_explanation.excluded_metrics` added — list of metric names missing data
- [x] `rich_explanation.method_note` added — auto-selected based on mode:
  - Rule-based: `"This score is a rule-based financial health indicator."`
  - Logistic: `"This probability is generated using a logistic regression model."`

### Documentation

- [x] `README.md` updated with financial health scoring data flow, pipeline script usage, scoring modes, explanation output structure, and compare endpoint behaviour
- [x] `IMPLEMENTATION_CHECKLIST.md` updated with all reliability/quality fixes
<!-- LLM_IGNORE_END -->