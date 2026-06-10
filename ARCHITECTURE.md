# ARCHITECTURE.md — FinanceIQ

## Overview

Three-container Docker application. Frontend serves static build via nginx; backend is a FastAPI monolith backed by PostgreSQL. All communication is REST/JSON over HTTP.

```
Browser
  │  HTTP :3000
  ▼
nginx (1.frontend)
  │  proxy /api → :8000  (not configured yet — direct calls in dev)
  │
  ▼
FastAPI (2.backend :8000)
  │  SQLAlchemy 2.0
  ▼
PostgreSQL 16 (:5432)
```

---

## Backend — `2.backend/app/`

### Layer structure

```
routers/       HTTP boundary — validates inputs, calls service, returns schema
services/      Business logic — ML, scoring, data transforms
models/        SQLAlchemy ORM table definitions
schemas/       Pydantic v2 request/response contracts
core/          Cross-cutting: auth dependency, JWT security
database.py    Engine + session factory + Base
config.py      Settings (pydantic-settings, reads .env)
main.py        App factory, middleware, router registration, startup hooks
```

### Domains / routers

| Router | Prefix / Tags | Responsibility |
|---|---|---|
| `auth` | `/auth` | Register, login, JWT issue |
| `users` | `/users` | Profile read/update |
| `companies` | `/companies` | Company CRUD, search |
| `financials` | `/financials` | Raw financial data |
| `scoring` | `/score-runs` | Legacy scoring runs (v1/v2) |
| `forecasting` | (root) | Core forecasting pipeline (v3) |
| `fundamentals` | `/fundamentals` | Quarterly CSV upload + template |
| `ingestion` | `/ingestion` | Data ingestion jobs |
| `admin` | `/admin` | Admin-only ops |
| `reports` | `/reports` | PDF/report generation |
| `validation` | `/validation` | Model validation tooling |
| `labeling` | `/labeling` | Manual data labeling |
| `news` | `/news` | News updates + AI insight |

### Key service: `forecasting_service.py`

Core pipeline called by forecasting router:

```
import_winner_excel_preset(db, file_name)
  └─ read xlsx → median impute → upsert WinnerCohortRow

train_sector_success_model(db, year, sector, top_n)
  └─ _parameter_scores()
       ├─ _fundamentals_df_for_sector() → QuarterlyFundamental rows
       ├─ _fundamentals_to_exact_ratios() → 17 computed ratios
       └─ _compute_ml_method_scores()
            ├─ Spearman, Pearson correlations
            ├─ Mutual Info (sklearn)
            ├─ Random Forest classifier (n=300)
            ├─ RFE (LogisticRegression)
            ├─ Lasso regression
            ├─ SHAP TreeExplainer (fallback: RF importances)
            └─ KMeans silhouette score
  └─ ensemble_score = weighted sum of 8 method scores
  └─ upsert SectorParameterRanking (top_n rows)

run_forecast_for_sector(db, year, sector, model_type, ...)
  └─ load SectorParameterRanking (auto-trains if missing)
  └─ for each stock: weighted normalized ratio sum → score (0–100)
  └─ model_type adjusts raw value transform:
       scoring (default) | xgboost (^1.15) | arima (momentum blend)
       prophet (trend blend) | dbscan (distance-to-center) | gmm (gaussian)
  └─ risk_level multiplier: low=0.85 / medium=1.0 / high=1.15
  └─ persist ForecastRun + ForecastPrediction rows
  └─ return ranked items + run_id

run_time_cv_evaluation(db, sector, model_type, window_size)
  └─ rolling window over available years (2020–2025)
  └─ per fold: train previous years, predict two adjacent years
  └─ rank_stability = 1 - mean_rank_diff / window
  └─ overlap_at_k = |top-K intersection| / min(|A|,|B|)
  └─ persist ForecastEvaluationRun + ForecastEvaluationFold
```

### Parameter catalog (17 ratios, 5 categories)

Categories: Karlılık (profitability), Nakit Akışı (cash flow), Büyüme (growth), Borç/Risk (leverage), Verimlilik (efficiency), Likidite (liquidity).

### DB schema (key tables)

```
users                     — auth + investor profile
winner_cohort_rows        — yearly xlsx data per stock (uq: year+stock_code)
quarterly_fundamentals    — uploaded fundamentals CSV rows (uq: stock_code+period)
sector_parameter_rankings — trained param scores per sector/year (uq: year+sector+param)
forecast_runs             — one run per predict call
forecast_predictions      — scored stocks per run (uq: run_id+stock_code)
forecast_evaluation_runs  — one per time-CV call
forecast_evaluation_folds — one per fold
```

---

## Frontend — `1.frontend/src/`

### Route map

```
/                → redirect /login
/login           → LoginPage (public)
/dashboard       → DashboardPage
/companies       → SearchPage
/companies/:id   → CompanyPage
/score-runs/:id  → ScoreResultPage
/compare         → ComparePage
/reports         → ReportsPage
/admin           → AdminPage
/validation      → ValidationLabPage
/ai-search       → AISearchPage
/data-health     → DataHealthPage
/labeling        → LabelingLabPage
/forecasting     → ForecastingPage
/forecasting/detail → ForecastingDetailPage
/news            → NewsUpdatesPage
*                → redirect /dashboard
```

All routes except `/login` wrapped in `<ProtectedRoute>` → `<AppShell>`.

### Auth

JWT stored in localStorage. `ProtectedRoute` reads token; redirects to `/login` if absent. Token lifetime: 1440 min (24h).

---

## ML ensemble scoring formula

```
ensemble_score =
  0.14 × spearman  +  0.08 × pearson  +  0.14 × MI
+ 0.14 × RF        +  0.10 × RFE      +  0.14 × Lasso
+ 0.14 × SHAP      +  0.12 × cluster

final_score =
  0.30 × cross_sectional_cv_score
+ 0.20 × temporal_stability_score
+ 0.10 × transition_score
+ 0.40 × ensemble_score
```

All method scores are min-max normalized before weighting.

---

## Infrastructure notes

- Docker Compose healthcheck on `db` (pg_isready) — backend waits for healthy db
- Backend mounts `./2.backend:/app` and `./3.Datasets:/app/3.Datasets` as volumes
- Backend startup runs `scripts/start_backend.sh`: wait for DB, run Alembic, load trusted data, start Uvicorn
- Alembic handles schema migrations; startup `create_all` is a safety net only
- `SECRET_KEY` in docker-compose is placeholder — must be replaced before any production use
- CORS: `allow_origins=["*"]` — tighten before production
