# ARCHITECTURE.md — FinanceIQ

## Overview

Three-container Docker application. Frontend serves static build via nginx; backend is a FastAPI monolith backed by PostgreSQL. All communication is REST/JSON over HTTP.

```
Browser
  │  HTTP :3000
  ▼
nginx (frontend)
  │  proxy /api → :8000  (not configured yet — direct calls in dev)
  │
  ▼
FastAPI (backend :8000)
  │  SQLAlchemy 2.0
  ▼
PostgreSQL 16 (:5432)
```

---

## Backend — `backend/app/`

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
  └─ loads internal training CSV → filters to training years
  └─ computes top-quartile winners (WINNER_PERCENTILE = 0.75)
  └─ per feature: effect_size = (winner_mean − overall_mean) / std × coverage_fraction
  └─ returns top_parameters [{name, weight, rank}], winner_rows, total_training_rows

run_forecast(year, trained_weights, risk_level, user_type)
  └─ loads public CSV → filters to target year
  └─ for each ticker: percentile rank per feature (within year) × weight = score
  └─ risk_level multiplier: low=0.85 / medium=1.0 / high=1.15
  └─ returns ranked items with ticker, score, confidence, top_parameters, warnings
  └─ inference rows (2025) flagged; research support only

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
  `/research/ai-status` reports provider/model configuration without exposing secrets and
  returns structured "AI not configured" diagnostics when no provider/key is available.
  `/research/runtime-status` is a public diagnostic for loaded dataset coverage and missing files.

### Endpoint protection

Research (`/research/*`) and CSV-forecasting (`/forecasting/options|train|run|explain`)
endpoints are **intentionally public for the demo** via the `optional_user` dependency
(DB-free, never 401/403). The Supabase-gated frontend still protects routes; the backend
serves validated research data even when it cannot verify the Supabase JWT. DB-backed
legacy forecasting endpoints keep `get_current_user`. All data paths resolve through the
single `app/core/paths.py` repo-root strategy (`RESEARCH_REPO_ROOT` override → `data/` probe).

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

## Frontend — `frontend/src/`

### Visual system

Fable 5 turns the app into a dark BIST research terminal rather than a generic
capstone dashboard. The design language is deep ink and graphite surfaces,
subtle grain/scanlines, muted emerald for signal/positive states, oxidized
copper/amber for weak/warning states, monospace data labels, tracked caps
section headings, sharp instrument panels, and research-only caveats. It keeps
the central finding visible: walk-forward IC ≈ 0 and no reliable weak ranking
signal should be hidden.

### Route map

```
/                → redirect /login
/login           → LoginPage (public)
/dashboard       → DashboardPage  [particle field / weak-signal overview]
/companies       → SearchPage  [research map entry]
/search          → redirect /companies
/ai-search       → redirect /research-agent
/companies/:id   → CompanyPage
/score-runs/:id  → ScoreResultPage
/compare         → ComparePage
/reports         → redirect /dashboard
/admin           → AdminPage
/validation      → ValidationLabPage
/data-health     → DataHealthPage
/labeling        → LabelingLabPage
/forecasting     → ForecastingPage  [signal tuner: options → train → rank → explain]
/forecasting/detail → ForecastingDetailPage
/research        → ResearchPage  [Score Explorer / dissection table]
/research-agent  → ResearchAgentPage  [research query instrument]
/data-quality    → DataQualityPage  [specimen archive]
/experiments     → ExperimentsPage  [seismograph]
/benchmark       → BenchmarkPage  [tide chart]
/research/companies → CompaniesResearchPage  [research map]
/research/companies/:ticker → CompanyResearchDetailPage
*                → redirect /dashboard
```

### Research Terminal pages

- `/dashboard` — "A weak signal, reported honestly."; particle/noise overview,
  BIST100 vs model comparison, feature intake, data quality, and visible IC ≈ 0.
- `/research-agent` — "Query the signal. Distrust the answer."; five intent
  selectors (Benchmark Outperformers, Top Ranked, Data Quality Overview,
  Valuation Screen, Model Diagnostics), restored free-text query, preserved
  `POST /research/ask` body `{ question: "<query text>" }`, instrument-style
  answer blocks, and hybrid/AI fallback status.
- `/research/companies` and `/companies` — "The universe, laid flat."; research
  score on x-axis, coverage on y-axis, sector-colored ticker nodes, search/filter
  dimming without layout movement, map/table toggle, real API first and mock data
  only as fallback/demo.
- `/experiments` — seismograph traces around zero; equal-weight baseline can lead
  where applicable; flat IC trace is presented as the finding.
- `/research` — Score Explorer dissection table; composite diagnostic score
  unfolds into feature/category detail while preserving `/research/years`,
  `/research/scores`, and `/research/company`.
- `/data-quality` — specimen archive for accepted/rejected features with
  `LEAKAGE`, `FROZEN`, and `ALL-NULL` stamps; `dataQuality()`, `summary()`, and
  `frozenEvidence()` hydrate progressively so accepted/rejected lists can render
  before slower frozen evidence finishes.
- `/benchmark` — tide chart with BIST100 vs model top basket as filled water
  bodies, sign-preserving log scale for 2022 +196%, and small IC markers.
- `/forecasting` — experimental signal tuner; feature weights render as a
  frequency spectrum, ranked rows crystallize from noise, inference-only rows
  pulse amber, and standby readout does not imply advice.

### ForecastingPage flow

```
mount → GET /forecasting/options (CSV-backed, no DB)
  └─ Step 1: set train_year_from/to, top_n → POST /forecasting/train
       └─ returns top_parameters with feature weights
  └─ Step 2: set forecast_year → POST /forecasting/run
       └─ returns ranked tickers with diagnostic scores (experimental)
  └─ click ticker → GET /forecasting/explain/{ticker}
       └─ score drivers, feature coverage, data quality warnings
```

All routes except `/login` and `/auth/callback` are wrapped in
`<ProtectedRoute>` → `<AppShell>`.

### Auth

Frontend auth uses Supabase Auth:

- `frontend/src/lib/supabaseClient.js` creates the browser client from
  `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`.
- `AuthProvider` restores Supabase sessions, listens to `onAuthStateChange`,
  supports email/password login, signup confirmation, Google OAuth, password
  recovery, logout, and exposes a compact app user shape.
- `ProtectedRoute` waits for session restore, then redirects unauthenticated
  users to `/login`.
- `/auth/callback` receives Supabase email/OAuth redirects and sends confirmed
  users to `/dashboard`.

Legacy FastAPI `/auth/login` remains for backend tests and old clients. Existing
protected API routes can accept Supabase JWTs when `SUPABASE_JWT_SECRET` is set;
without it, frontend route protection still works, but legacy backend JWT auth is
the only API verifier.

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
- Backend mounts `./backend:/app`, `./data:/app/data`, and `./experiments:/app/experiments` as volumes
- Backend startup runs `scripts/start_backend.sh`: wait for DB, run Alembic, load trusted data, start Uvicorn
- Alembic handles schema migrations; startup `create_all` is a safety net only
- `SECRET_KEY` in docker-compose is placeholder — must be replaced before any production use
- CORS: `allow_origins=["*"]` — tighten before production
