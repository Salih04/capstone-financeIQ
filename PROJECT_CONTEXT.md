# PROJECT_CONTEXT.md — FinanceIQ

## What it is

FinanceIQ is a capstone project: an honest, leakage-safe **T→T+1 equity-research
system** for 40 public BIST (Borsa Istanbul) companies, 2020–2025, plus an
expanded 81-ticker internal training universe. It builds a validated modeling
dataset (year-T features → year-(T+1) realized return), a BIST100 benchmark,
a free-data valuation reconstruction, walk-forward experiments, an explainable hybrid
research agent (OpenRouter by default, local providers optional), a CSV-backed
forecasting pipeline at `/forecasting`, and the Fable 5 "Research Terminal"
frontend.

**Status: complete.** Honest finding: no reliable predictive edge after the
expanded training run — a rigorous pipeline + transparent negative result, not
a trading-edge claim.
See `TASK_STATE.md`.

## Goals

- Build a leakage-safe T→T+1 dataset from real data only (no synthetic, no fabrication)
- Reconstruct missing valuation (market_cap, P/E, P/B, EV, EV/EBITDA) from FREE sources
  (Yahoo year-end price × manual shares × validated financials) instead of paid APIs
- Evaluate honestly via walk-forward CV vs a simple baseline (report weak signal as-is)
- Provide explainable, bounded research support — never investment advice
- Keep every accepted/rejected column traceable to its source and reason

## Frontend direction

The completed Fable 5 frontend is a dark research-terminal interface for BIST
signal analysis, not a generic capstone dashboard. It uses deep ink surfaces,
subtle grain/scanline texture, muted emerald signal states, oxidized
copper/amber weak-signal states, monospace data typography, tracked caps labels,
and persistent Signal Readout panels where useful. It does not use floating
tooltips or investment-advice language. The weak result is part of the interface:
walk-forward IC ≈ 0 is shown as a core finding.

Key pages:

| Route | Current concept | Data behavior |
|---|---|---|
| `/dashboard` | Particle field / weak signal overview; "A weak signal, reported honestly." | BIST100/model comparison, feature intake, data quality, visible IC ≈ 0. |
| `/research-agent` | Research query instrument; "Query the signal. Distrust the answer." | Preserves `POST /research/ask` with `{ question: "<query text>" }`; five intent selectors plus free text; hybrid weights and AI/fallback status. |
| `/research/companies`, `/companies` | Research map; "The universe, laid flat." | Real API data preserved; mock/demo data only fallback. X = research score, Y = coverage, sector-colored ticker nodes, map/table toggle. |
| `/experiments` | Seismograph | Walk-forward folds trace around zero; equal-weight baseline can lead; flat IC trace is the finding. |
| `/research` | Score Explorer / dissection table | Preserves `/research/years`, `/research/scores`, `/research/company`; composite score unfolds to feature/category detail. |
| `/data-quality` | Specimen archive | Uses `dataQuality()`, `summary()`, `frozenEvidence()`; `LEAKAGE`/`FROZEN`/`ALL-NULL` stamps; avoids false accepted=0 loading states. |
| `/benchmark` | Tide chart | Preserves `researchApi.benchmark()`; sign-preserving log scale keeps 2022 +196% readable; IC markers stay small. |
| `/forecasting` | Signal tuner | Preserves options/train/run/explain pipeline; feature weights as frequency spectrum; inference-only rows pulse amber. |

Session cache: centralized in `frontend/src/api/cache.js` — sessionStorage-backed,
stale-while-revalidate, in-flight dedupe, TTL constants (SHORT/MEDIUM/LONG). The
`useCachedResource` hook + Fable 5 `CacheTag` chip (cached / refreshing / last
updated + force-refresh) drive Benchmark, Experiments, Data Quality, Forecasting
(options keyed by `target_mode`, train keyed by body), and Company Research Detail
(per-ticker). `frontend/src/utils/sessionCache.js` is a backward-compatible shim
over it. Auth/session/token endpoints and `POST /research/ask` are never cached;
failed responses are never cached; hard refresh fetches normally.

## Users

Investors (individual, corporate) and admins. Role stored on `User.role` (investor | admin). User profile includes `user_type`, `risk_level`, `investment_scope`, `sector_focus` — these modulate scoring output.

## Data scope

| Source | Content |
|---|---|
| `data/raw/yearly_xlsx/2020stocks.xlsx` … `2025stocks.xlsx` | Yearly BIST winner cohorts — price returns, sector, stock code (returns/universe trusted; income-statement columns are frozen snapshots, excluded) |
| `data/trusted_clean/modeling_dataset_public_2020_2025.csv` | Primary inference dataset — 40 tickers × 6 years, 40 validated features, no DB required |
| `data/trusted_clean/modeling_dataset_training_2020_2025.csv` | Training-only split — 403 rows / 81 tickers / 321 target rows (experiments + walk-forward CV) |
| `data/trusted_raw/financials/` | Corrected yearly XLSX exports + yfinance candidate CSV + manual KAP template |
| `data/trusted_raw/prices/yahoo_year_end_prices.csv` | Yahoo Chart year-end prices (OHLCV only — no financial statements) |
| `data/trusted_clean/bist100_benchmark_returns.csv` | BIST100 annual returns → excess-return / outperform targets |
| `data/config/universe_public_40.csv` | 40-ticker public inference universe |
| `data/config/universe_training_bist100.csv` | Expanded training universe config (81 tickers; public_40 plus training-only yfinance-compatible names) |
| `data/trusted_clean/pipeline_audit_report.*` | CSV inventory, source class, row/ticker/year coverage, missingness, duplicate-key checks |
| `data/trusted_clean/feature_engineering_report.*` | Accepted/rejected feature report with leakage-safe year-T feature list |
| `data/trusted_clean/company_contexts/` | Pre-built RAG JSON per ticker/year — injected into LLM research prompt |
| Quarterly fundamentals CSV | 28-column fundamentals per stock/period (uploaded via UI; legacy DB path) |

Missing values: median imputation at XLSX import. Pipeline never fabricates or zero-imputes.

## Tech stack

| Layer | Tech |
|---|---|
| Frontend | React 18 + Vite, React Router v6, nginx in Docker |
| Backend | FastAPI 0.111, Python 3.12, Uvicorn |
| ORM / DB | SQLAlchemy 2.0, PostgreSQL 16-alpine, Alembic |
| ML / Data | scikit-learn, pandas, numpy, SHAP, openpyxl |
| Auth | JWT (python-jose), bcrypt/passlib, 1440-min tokens |
| Containerization | Docker Compose (3 services: db, backend, frontend) |

## Environments

| Service | Local port | Docker |
|---|---|---|
| Frontend | 5173 (dev) | 3000 → nginx:80 |
| Backend | 8000 | 8000 |
| DB | 5432 | 5432 (internal) |

## Key directories

```
frontend/src/pages/          — one file per page/route
frontend/src/components/     — shared UI (AppShell, ProtectedRoute, …)
backend/app/routers/         — one router per domain
backend/app/services/        — business logic
  forecasting_csv_service.py   — CSV-backed forecasting (primary; no DB)
  forecasting_service.py       — legacy DB-backed forecasting
  research_agent.py            — hybrid research agent (OpenRouter + fallback)
backend/app/models/          — SQLAlchemy ORM models
backend/app/schemas/         — Pydantic request/response schemas
scripts/data_collection/       — data pipeline scripts (build_all, ingest, valuation, …)
data/config/                   — universe CSVs (public_40, training_bist100)
data/trusted_raw/              — raw inputs: prices, financials, benchmark
data/trusted_clean/            — validated outputs: modeling dataset, contexts, reports
data/trusted/                  — reference bootstrap (stocks_2020_2025.csv)
experiments/                   — walk-forward CV scripts + results
research_agent_training/       — instruction dataset generation + evaluation
data/raw/yearly_xlsx/                    — original xlsx winner cohort files (2020–2025)
```

## Auth flow

Frontend auth is Supabase-based. `AuthProvider` restores the browser session,
`ProtectedRoute` gates app routes, `/auth/callback` handles email confirmation
and Google OAuth redirects, and logout calls `supabase.auth.signOut()`. Backend
legacy JWT routes (`/auth/login`, `/auth/register`) remain for tests and old
clients. FastAPI can accept Supabase JWTs on existing protected endpoints when
`SUPABASE_JWT_SECRET` is configured; this is optional compatibility, not a new
backend user system.
