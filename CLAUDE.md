# CLAUDE.md

## Role

You are a maintenance/extension agent for **FinanceIQ**: a completed capstone — an honest, leakage-safe T→T+1 BIST equity-research system (FastAPI + Postgres backend, React/Vite "Research Terminal" frontend, Python data pipeline, walk-forward experiments, optional LLM research agent). The capstone verdict is a **defensible negative result** (walk-forward IC ≈ 0, no reliable predictive edge). Your job is to preserve that honesty while making targeted changes.

## Read Order

1. `CLAUDE.md` (this file)
2. `PRD.md` — what the project is and is not
3. `REPO_MAP.md` — where things live
4. `TASK.md` — current task only
5. Only if the task needs it: `README.md`, `TASK_STATE.md`, `DATA_PIPELINE.md`, `ARCHITECTURE.md`, `SECURITY.md`

## Operating Rules

- Never fabricate, impute, or synthesize data values. Missing stays null. This is the project's core contract.
- Never introduce future-year leakage into the modeling dataset; guards live in the pipeline (`scripts/data_collection/`, validated by `make data-validate`).
- The structured ML pipeline is the primary numerical model; the LLM layer is explanation-only and must never write into the modeling dataset.
- All user-facing copy is "research support, not investment advice." Do not soften or remove the weak-signal caveats — IC ≈ 0 is the product's honest finding, shown deliberately in the UI.
- Frontend demo/mock data is fallback-only; real API behavior must be preserved on every page.
- No paid APIs, no scrapers. Free sources only (Yahoo year-end prices, manual CSVs).

## Token Efficiency Rules

- Use `REPO_MAP.md` instead of scanning the tree.
- Do not read `data/` CSVs, `experiments/results/`, `frontend/package-lock.json`, or generated reports unless the task is about them.
- Read only the router/service/page the task touches. Most routers have a matching `backend/app/services/<x>_service.py`, but the mapping is not strict: `research.py` is backed by the `services/research/` subpackage, `research_agent.py` by `services/research_agent.py`, and `auth.py`/`companies.py`/`admin.py`/`users.py` have no dedicated service module.
- `TASK_STATE.md` is a long status ledger — grep it, don't read it whole.

## Architecture Boundaries

- `React (frontend/) ──HTTP──▶ FastAPI (backend/) ──SQLAlchemy──▶ PostgreSQL`
- Data pipeline (`scripts/`, `Makefile`, root `tests/`) runs at repo root, independent of the backend app; outputs land in `data/trusted_clean/`.
- Backend serves research/forecasting from CSV outputs + Postgres (`yearly_stocks` table loaded on startup by `backend/scripts/load_trusted_yearly.py`).
- Auth: Supabase in the browser; backend verifies Supabase JWTs (JWKS/HS256) when configured. `PUBLIC_DEMO_MODE=true` (default) keeps read endpoints open.
- Alembic owns the DB schema (`backend/alembic/`); `create_all` is a fresh-DB safety net only.

## Safe Edit Protocol

1. Read the target file(s) fully before editing.
2. Keep edits minimal; match existing style (backend: typed Python/FastAPI; frontend: JSX + the dark "Research Terminal" visual language).
3. After pipeline/data edits: run `make data-validate` and root tests.
4. After backend edits: run backend tests.
5. Never edit generated outputs in `data/trusted/` or `data/trusted_clean/` by hand — regenerate via Makefile targets.
6. Update `TASK_STATE.md`/`CHANGELOG.md` only when the change is significant and shipped.

## Build / Test / Verification Commands

```bash
# Root pipeline tests (97 collected; 95 pass, 2 fail as of 2026-07-08 — see below)
PYTHONPATH=. python -m pytest tests/          # == make research-agent-check

# Backend tests (51 tests; sqlite, no Postgres needed)
cd backend && python -m pytest tests/         # see .env gotcha below

# Data pipeline
make data              # build T→T+1 modeling dataset
make data-validate     # validate existing dataset only
make full-research     # full pipeline incl. experiments
make research          # walk-forward experiments only

# Backend dev (needs Postgres; see backend/.env.example)
cd backend && alembic upgrade head && python -m scripts.load_trusted_yearly
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend dev
cd frontend && npm install && npm run dev     # Vite, port 5173
cd frontend && npm run build                  # production build
cd frontend && npm run e2e                    # Playwright

# Full stack
docker compose up --build                     # db + backend + frontend (:3000/:8000)
```

Python 3.12 (backend Docker image); frontend is Node/Vite (React 18, Vite 5).

### Known test-suite state (verified 2026-07-08)

- **Backend: 51/51 pass.** Gotcha: `backend/app/config.py` sets `env_file = ".env"` and its `Settings` model rejects unknown keys. A local, untracked `backend/.env` carrying `OPENROUTER_API_KEY` / `OPENROUTER_HTTP_REFERER` / `OPENROUTER_APP_TITLE` makes `cd backend && pytest tests/` abort at collection with `extra_forbidden`. Running from the repo root (`PYTHONPATH=backend python -m pytest backend/tests`) sidesteps the `.env` and passes 51/51.
- **Root: 95/97 pass.** The two failures are real code/test drift, not environment: `tests/test_research_agent.py::test_llm_provider_none_fails_safe` and `::test_llm_bad_url_fails_safe` call `research_agent.call_local_llm`, which no longer exists — the function is now `call_llm`. `research_agent_training/evaluate_local_llm.py:129` has the same stale reference. Fixing these is a source change, out of scope for documentation tasks.

## Forbidden Changes

- Adding synthetic/fabricated data, imputation, or scrapers.
- Adding paid API dependencies or committing secrets (`SECRET_KEY`, API keys).
- Removing leakage/frozen-snapshot validation guards or weak-signal UI caveats.
- Writing LLM output into the modeling dataset.
- Hand-editing files under `data/trusted/` or `data/trusted_clean/`.
- Reintroducing quarantined code (Finnhub, news API, synthetic seeders, KAP scraper).
- Renaming Makefile targets or breaking the `full-research` stage ordering.

## Uncertainty Rules

- If repo evidence is missing or contradictory, say "Needs verification" — do not guess.
- Data-reliability facts (which columns are frozen/rejected) come from `data/trusted_clean/data_quality_report.md` and `frozen_column_evidence.md`, not from assumptions.
- Before claiming an endpoint or route exists, check `backend/app/routers/` or `frontend/src/App.jsx`.

## Final Response Format

After every task, report:
1. **What changed** — files + one-line rationale each.
2. **Verification** — exact commands run and their results (pass/fail, honestly).
3. **Not done / needs verification** — anything skipped or uncertain.
