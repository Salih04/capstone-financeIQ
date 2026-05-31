# TASK_STATE.md — FinanceIQ

Last updated: 2026-05-31

## Status legend
- `DONE` — shipped, tested
- `WIP` — in progress
- `TODO` — planned, not started
- `BLOCKED` — waiting on something

---

## Core pipeline

| Task | Status | Notes |
|---|---|---|
| xlsx preset import (2020–2025) | DONE | `import_winner_excel_preset`, median imputation, upsert |
| 17-ratio fundamentals derivation | DONE | `_fundamentals_to_exact_ratios` |
| 8-method ML ensemble parameter ranking | DONE | `train_sector_success_model` |
| Stock scoring with 6 model_type modes | DONE | scoring/xgboost/arima/prophet/dbscan/gmm |
| Rolling time-CV evaluation | DONE | rank stability + overlap@K |
| Trend series endpoint | DONE | `GET /predict/trends` |
| Sector heatmap endpoint | DONE | `GET /predict/heatmap` |
| Portfolio analysis | DONE | weak/strong split + action list |
| SHAP explainability | DONE | fallback to RF importances if shap unavailable |
| Fundamentals CSV upload | DONE | `POST /fundamentals/upload-csv` |
| Fundamentals template download | DONE | `GET /fundamentals/template` |

## Auth & users

| Task | Status | Notes |
|---|---|---|
| JWT login/register | DONE | |
| Account lockout on failed login | DONE | `failed_login_count`, `locked_until` |
| User profile onboarding fields | DONE | user_type, risk_level, investment_scope, sector_focus |
| Backward-compat hotfix for old DBs | DONE | `_ensure_backward_compatible_columns` in main.py |

## Frontend pages

| Page | Status | Notes |
|---|---|---|
| Login | DONE | |
| Dashboard | DONE | |
| Forecasting | DONE | upload → train → predict → evaluate |
| Forecasting Detail | DONE | trends, importance, heatmap charts |
| News | DONE | |
| Validation Lab | DONE | |
| Labeling Lab | DONE | |
| Data Health | DONE | |
| Companies / Search | DONE | |
| AI Search | DONE | |
| Compare | DONE | |
| Reports | DONE | |
| Admin | DONE | |

## Known gaps / TODOs

| Item | Priority | Notes |
|---|---|---|
| `SECRET_KEY` hardcoded in docker-compose | HIGH | Must replace before any external deployment |
| CORS `allow_origins=["*"]` | HIGH | Tighten to known frontend origin |
| SARIMAX / TFT models | MEDIUM | README lists them as planned models; not in codebase yet — current model_type modes are approximations |
| Airflow DAG | LOW | `2.backend/airflow/dags/forecasting_retrain_dag.py` referenced in README but not present in tree |
| `infra/` cloud configs | LOW | Referenced in README; not present in repo |
| `docs/DEPLOYMENT.md` | LOW | Referenced in README; not present |
| E2E test coverage | MEDIUM | `playwright.config.js` + `e2e-forecasting.spec.js` exist; coverage unknown |
| nginx proxy for backend | LOW | Frontend calls backend directly; no reverse-proxy layer configured |
| Duplicate `_fundamentals_df_for_sector` | LOW | Defined twice in `forecasting_service.py` (lines ~342 and ~506); second def shadows first |

## Recently completed

- 2026-05-31: PROJECT_CONTEXT.md, CHANGELOG.md, ARCHITECTURE.md, TASK_STATE.md generated from codebase
