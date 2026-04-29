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
<!-- LLM_IGNORE_END -->