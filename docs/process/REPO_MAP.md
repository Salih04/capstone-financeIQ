# REPO_MAP.md

## Overview

Three layers sharing one repo: (1) a Python data/experiment pipeline run from the repo root via `Makefile`, (2) a FastAPI + SQLAlchemy + Postgres backend in `backend/`, (3) a React 18 + Vite frontend in `frontend/`. Data flows: raw XLSX/CSV → `scripts/data_collection/` → `data/trusted_clean/` → consumed by experiments and by the backend (CSV + Postgres) → rendered by the frontend.

## Important Directories

| Path | What it is |
|---|---|
| `backend/app/` | FastAPI app: `main.py`, `config.py`, `database.py`, `trusted_data.py` (data contract) |
| `backend/app/routers/` | API routes: `research.py`, `research_agent.py`, `forecasting.py`, `auth.py`, `companies.py`, `scoring.py`, … |
| `backend/app/services/` | Business logic. Roughly — not strictly — 1:1 with routers: `research/` is a subpackage (`scoring.py`, `company.py`, `benchmark.py`, `validation.py`, …), `research_agent.py` is a single module, and `auth`/`companies`/`admin`/`users` routers have no service module |
| `backend/scripts/` | `convert_trusted_xlsx.py`, `load_trusted_yearly.py`, `validate_trusted_data.py`, `start_backend.sh` (Docker entry); also `pipeline_runner.py`, `retrain_forecasting.py`, `incremental_retrain.py`, `migration_state.py` |
| `backend/alembic/` | Migrations; head includes `yearly_stocks` |
| `backend/tests/` | Backend suite; sqlite via `conftest.py`, no Postgres needed. Current observed count: `docs/VERIFICATION_BASELINE.md` |
| `backend/airflow/` | Single dormant DAG (`dags/forecasting_retrain_dag.py`). `airflow` is not in `requirements.txt` or any deploy file — nothing runs it |
| `frontend/src/pages/` | One JSX file per route, all `*Page.jsx` (`DashboardPage.jsx`, `ResearchAgentPage.jsx`, `ExperimentsPage.jsx`, `BenchmarkPage.jsx`, `ForecastingPage.jsx`, …) |
| `frontend/src/api/` | `client.js`, `researchApi.js`, `cache.js` (sessionStorage SWR cache), `useCachedResource.js` |
- `frontend/src/api/cache.js` owns the sessionStorage-backed stale-while-revalidate cache, with in-flight deduplication and SHORT/MEDIUM/LONG TTLs; auth/session/token endpoints, `POST /research/ask`, and failed responses are never cached, and hard refresh fetches normally.
| `scripts/data_collection/` | Pipeline stages: `build_all.py`, `validate.py` (leakage guards), ingest/valuation/benchmark/integration modules |
| `scripts/` (root) | `build_company_contexts.py` (RAG contexts), `fetch_yahoo_chart_prices.py`, `validate_trusted_data.py` |
| `experiments/` | `run_experiments.py` (walk-forward loop), `results/`, `reports/summary.md`, `leaderboard.csv` |
| `tests/` (root) | Pipeline/research-agent suite. Current observed count and status: `docs/VERIFICATION_BASELINE.md` |
| `data/` | `raw/` (yearly XLSX), `trusted/` (generated CSVs), `trusted_raw/` (manual inputs), `trusted_clean/` (pipeline outputs + reports), `config/` (universe CSVs); also `interim/`, `exports/` |
| `research_agent_training/` | Instruction-dataset generation/validation/eval; no training performed |
| `docs/` | `RENDER_DEPLOY.md`, `SUPABASE_AUTH.md`, `research_agent_guide.md` |

## Important Files

- `Makefile` — the pipeline's single source of truth; read target definitions before running.
- `backend/app/trusted_data.py` — column map, validation, safe parsing (the data contract).
- `scripts/data_collection/build_all.py` + `validate.py` — dataset build and leakage/frozen guards.
- `data/trusted_clean/modeling_dataset_2020_2025.csv` — the modeling dataset (+ `_public_`/`_training_` splits).
- `data/trusted_raw/shares_outstanding_events.csv` — manual shares input for valuation.
- `TASK_STATE.md` — detailed status ledger; `CHANGELOG.md` — history.
- `docs/CONSOLIDATION.md` — durable cross-cutting context and resumption guide; it supplements, but does not replace, `PRD.md`, `METHODOLOGY.md`, `TASK_STATE.md`, the task queue, or generated reports.
- `docs/archive/` — historical documentation outside the active operating surface; this task creates only its entry point and moves no existing files.
- `docker-compose.yml`, `render.yaml`, root `vercel.json` — deployment definitions. Note there is a **second** `frontend/vercel.json` containing only SPA rewrites; the root one carries the build config.

## Entry Points

- Backend API: `backend/app/main.py` (uvicorn `app.main:app`); Docker startup via `backend/scripts/start_backend.sh` (Alembic → data load → serve).
- Frontend: `frontend/src/main.jsx` → `frontend/src/App.jsx` (routes; entry route `/login`).
- Pipeline: `make full-research` / `make full-research-agent`; experiments: `experiments/run_experiments.py`.

## Architecture Map

```
React (frontend/, :3000|:5173) ──HTTP──▶ FastAPI (backend/, :8000) ──SQLAlchemy──▶ PostgreSQL
                                              │
                                              └── reads data/trusted_clean/ CSVs (research, CSV forecasting)
Pipeline (Makefile + scripts/ + experiments/, repo root) ──▶ data/trusted_clean/
Auth: Supabase (browser) ──JWT──▶ backend verify (JWKS/HS256, optional; PUBLIC_DEMO_MODE default)
LLM (optional): OpenRouter / LM Studio / Ollama, explanation-only, deterministic fallback
```

## Data / State / Pipeline Map

- `data/raw/yearly_xlsx/2020–2025stocks.xlsx` → `backend/scripts/convert_trusted_xlsx.py` → `data/trusted/*.csv` → Postgres `yearly_stocks` (reference/bootstrap only; fundamentals partly frozen 2025 snapshot).
- Modeling path: `make data` = corrected-yearly ingest + `build_all` → `data/trusted_clean/modeling_dataset_2020_2025.csv` + quality/audit reports. Order matters: `fetch-training-prices` → `valuation` → `data` → `integrate-pilot-tickers` → `data-validate`.
- RAG contexts: `make build-company-contexts` → `data/trusted_clean/company_contexts/`.
- Universe config: `data/config/universe_public_40.csv`, `universe_training_bist100.csv`, `bist100_candidates.csv`.

## Config / Build / Deploy

- Env vars documented in `README.md` table (DATABASE_URL, SECRET_KEY, RESEARCH_LLM_*, TRUSTED_*, PUBLIC_DEMO_MODE, SUPABASE_*, VITE_*).
- `docker-compose.yml`: services `db` (postgres:16-alpine, :5432), `backend` (:8000), `frontend` (host :3000 → container :80 via nginx).
- Render: Docker runtime, `dockerfilePath: ./backend/Dockerfile`, `dockerContext: .` (repo root) — do NOT set Render's Root Directory to `backend`. Services: `financeiq-backend` (web) + `financeiq-db`.
- Vercel: build runs from the **repo root**, not `frontend/` — root `vercel.json` sets `installCommand`/`buildCommand` with `--prefix frontend` and `outputDirectory: frontend/dist`, plus SPA rewrites and security headers. `frontend/vercel.json` holds rewrites only.
- Backend deps: `backend/requirements.txt` (FastAPI 0.111, SQLAlchemy 2.0, pydantic 2.7; Python 3.12 per `backend/Dockerfile`); frontend: `frontend/package.json` (React 18, Vite 5, Playwright e2e; scripts `dev`/`build`/`preview`/`e2e`).

## Common Edit Targets

- New/changed API behavior: `backend/app/routers/<x>.py` + `backend/app/services/<x>_service.py` + `backend/tests/`.
- Research agent logic: `backend/app/services/research_agent.py`, `backend/app/services/research/`, root `tests/test_research_agent.py`.
- Page/UI changes: `frontend/src/pages/<Page>.jsx` + `frontend/src/api/researchApi.js`.
- Pipeline stages: `scripts/data_collection/<stage>.py` + matching root `tests/test_*.py` + Makefile target.

## Fragile Areas

- Makefile stage ordering in `full-research` (price fetch must precede valuation/build).
- `frontend/src/api/cache.js` rules (never cache auth, `/research/ask`, or errors).
- Leakage/frozen guards in `scripts/data_collection/validate.py` and `manual_ingest.py` — behavior-load-bearing for the project's credibility.
- 2024 manual balance-sheet override (shape-validated, 2024-only) — easy to break silently.
- Docker/Render path env vars (`TRUSTED_*`, `RESEARCH_REPO_ROOT`) — container paths differ from local.

## Do Not Touch Casually

- Anything under `data/trusted/` and `data/trusted_clean/` (generated; regenerate via Makefile).
- `data/trusted_raw/` manual inputs (human-curated corrections).
- `backend/alembic/versions/` (append migrations; never edit shipped ones).
- Weak-signal caveat copy in frontend pages (e.g. `DashboardPage.jsx:445` — "A weak signal, reported *honestly*.").
- `backend/airflow/dags/forecasting_retrain_dag.py` — dormant (airflow is not a declared dependency); leave it alone rather than "fixing" or deleting it without a decision.
- `unnecessary/` quarantine: **does not exist** in the repo and is untracked by git. The former README reference was removed; do not recreate the directory to satisfy that historical link.
