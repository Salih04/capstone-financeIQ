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
| `forecasting` | (root) | CSV forecasting pipeline (primary) + legacy DB endpoints |
| `fundamentals` | `/fundamentals` | Quarterly CSV upload + template |
| `ingestion` | `/ingestion` | Data ingestion jobs |
| `admin` | `/admin` | Admin-only ops |
| `reports` | `/reports` | PDF/report generation |
| `validation` | `/validation` | Model validation tooling |
| `labeling` | `/labeling` | Manual data labeling |
| `news` | `/news` | News updates + AI insight |

### Key service: `forecasting_csv_service.py` (primary, no DB required)

CSV-backed forecasting pipeline — reads `modeling_dataset_public_2020_2025.csv` directly.
All output is clearly marked experimental / not investment advice.

```
get_options()
  └─ returns trainable_years, all_years, inference_years, feature_columns, ticker_count

train_parameters(train_year_from, train_year_to, top_n)
  └─ loads public CSV → filters to training years
  └─ computes top-quartile winners (WINNER_PERCENTILE = 0.75)
  └─ per feature: effect_size = (winner_mean − overall_mean) / std × coverage_fraction
  └─ returns top_parameters [{name, weight, rank}], winner_rows, total_training_rows

run_forecast(year, trained_weights, risk_level, user_type)
  └─ loads public CSV → filters to target year
  └─ for each ticker: percentile rank per feature (within year) × weight = score
  └─ risk_level multiplier: low=0.85 / medium=1.0 / high=1.15
  └─ returns ranked items with ticker, score, confidence, top_parameters, warnings
  └─ inference rows (2025) flagged; no buy/sell signals ever

explain_ticker(ticker, year)
  └─ returns top_features, bottom_features, missing_features, data_quality guardrails
```

### Legacy service: `forecasting_service.py` (DB-dependent)

Requires `WinnerCohortRow` + `QuarterlyFundamental` tables to be populated.
In production environments these tables are empty — legacy endpoints return empty results.

```
import_winner_excel_preset(db, file_name) → upsert WinnerCohortRow
train_sector_success_model(db, ...)       → 8-method ML ensemble → SectorParameterRanking
run_forecast_for_sector(db, ...)          → ForecastRun + ForecastPrediction rows
run_time_cv_evaluation(db, ...)           → ForecastEvaluationRun + folds
```

### Other key services

- **`research_agent.py`** — hybrid score (0.65·ML + 0.20·confidence + 0.15·LLM), grounded intents,
  OpenRouter (`openai/gpt-oss-120b:free`) + legacy LM Studio/Ollama, deterministic fallback.
  Reads public CSV for inference; loads pre-built RAG context JSON preferentially.

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
/forecasting     → ForecastingPage  [CSV pipeline: options → train → rank → explain]
/forecasting/detail → ForecastingDetailPage
/news            → NewsUpdatesPage
*                → redirect /dashboard
```

### ForecastingPage flow

```
mount → GET /forecasting/options (CSV-backed, no DB)
  └─ Step 1: set train_year_from/to, top_n → POST /forecasting/train
       └─ returns top_parameters with feature weights
  └─ Step 2: set forecast_year → POST /forecasting/run
       └─ returns ranked tickers with scores (no buy/sell signals; experimental)
  └─ click ticker → GET /forecasting/explain/{ticker}
       └─ score drivers, feature coverage, data quality warnings
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
