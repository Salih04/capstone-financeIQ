# CHANGELOG

All notable changes to FinanceIQ, most recent first.

## [Unreleased / HEAD] — 2026-05-31

No unreleased changes beyond HEAD.

---

## [3.0.0] — 2026-05 (commit 88b318c…35e2d0a)

### Added
- **Forecasting module** (`/forecasting`, `/forecasting/detail`) — full upload → train → predict → evaluate pipeline
  - `POST /upload-data` — import yearly BIST winner xlsx preset
  - `POST /train-model` — compute sector parameter rankings via 8-method ML ensemble (Spearman, Pearson, MI, RF, RFE, Lasso, SHAP, K-Means cluster)
  - `POST /predict` + `GET /get-stocks` — generate ranked stock list for sector/year
  - `POST /predict/evaluate` — rolling time-CV evaluation (rank stability + overlap@K)
  - `GET /predict/trends` — per-stock yearly return series
  - `GET /predict/heatmap` — sector × feature heatmap
  - `POST /get-portfolio-analysis` — corporate portfolio weak/strong split + actions
  - `GET /get-stock-detail` + `GET /get-explanation` — per-run per-stock explainability
  - `GET /predict/history` — run history
  - `GET /parameters/catalog` — 17-parameter catalog with formulas (Turkish labels)
- **Quarterly fundamentals** — `POST /fundamentals/upload-csv` parses 28-column CSV; computes 17 derived financial ratios (ROE, ROA, OCF, margins, leverage, liquidity, efficiency)
- **News page** (`/news`) — `GET /news/updates`
- **Validation Lab** (`/validation`) and **Labeling Lab** (`/labeling`)
- **Data Health** page (`/data-health`)
- **User onboarding fields** — `user_type`, `risk_level`, `investment_scope`, `sector_focus` added to `users` table; backward-compatible hotfix in `main.py`
- Risk multiplier applied to final scores (low=0.85, medium=1.0, high=1.15)
- Multiple `model_type` modes: `scoring` (default), `xgboost`, `arima`, `prophet`, `dbscan`, `gmm`
- SHAP-based explainability via `shap.TreeExplainer` (falls back to RF importances if unavailable)
- `GET /fundamentals/template` — downloadable CSV template

### Changed
- API title bumped to "Stock Scoring V3 API" version 3.0.0
- DB wait-loop on startup (15 retries × 2s) before `Base.metadata.create_all`
- Median imputation applied at xlsx import time (per-column, global median)

### Fixed (commit 35e2d0a — "Fix reliability, performance, and transparency")
- Scoring reliability: time-based train/validation splits, cross-validation enforced
- Removed leakage of future data into training features
- Evaluation metrics reported per model
- Rolling-window CV replaces static holdout

---

## [2.x] — earlier (commits fb69da0, 9a430c0, 79e6a67)

Initial clean commit. Core modules: auth, companies, financials, scoring (v1/v2), ingestion, admin, reports. Frontend with Login, Dashboard, Search, Company, ScoreResult, Compare, Reports, Admin pages.

---

## [1.x] — initial sync (commit ed4ff15)

Project scaffolded. Basic FastAPI + React skeleton, Docker Compose, Alembic setup.
