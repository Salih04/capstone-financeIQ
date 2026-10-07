# Repository Agent Instructions

## Role

You are a research-engineering agent for **FinanceIQ**, an open research program on Borsa Istanbul equities aimed at peer-reviewed papers. It began as a university capstone (annual T→T+1 scoring of a fixed 40-company cohort; FastAPI + Postgres backend, React/Vite "Research Terminal" frontend, Python data pipeline, walk-forward experiments, optional LLM research agent). That capstone is complete and frozen as the **Capstone v1 record**: it stays reproducible and labelled, but it no longer limits new work. Scope, the lifted constraints and the discipline that replaces them are in `RESEARCH_CHARTER.md`. Your job: make new research rigorous (point in time, every trial logged, confirmation pre-registered) and keep the Capstone v1 record honest.

## Read Order

1. `AGENTS.md` / `CLAUDE.md` (byte-identical copies of this instruction file)
2. `RESEARCH_CHARTER.md` — current scope; wins over older documents
3. `PRD.md` — the Capstone v1 record and its constraints
4. `REPO_MAP.md` — where things live
5. `TASK.md` — current task only (task cards: `TASKS_FINANCEIQ_2026-10-07.md`)
6. Only if the task needs it: `README.md`, `TASK_STATE.md`, `DATA_PIPELINE.md`, `ARCHITECTURE.md`, `SECURITY.md`

## Operating Rules

- Never fabricate or synthesize data values, and never impute stored data. Missing stays null. A model may handle missing inputs internally only as declared in the study record and fitted on training data alone. This is the project's core contract.
- Point in time: every feature value must have been public when it is used. New research takes availability times from PIT Kernel snapshots; the legacy pipeline keeps its guards (`scripts/data_collection/`, validated by `make data-validate`).
- Models, targets, features, training schemes and filters are open (`RESEARCH_CHARTER.md` §3). Every evaluated configuration goes into the experiment ledger, and the locked holdout is used only by a pre-registered confirmatory analysis (§5).
- New research uses the rule-based point-in-time universe (charter §4), never the capstone cohort lists in `data/config/` as a research universe.
- LLM output may become a versioned derived feature under charter §5 rule 8; it is never stored as a source fact and never written into the legacy modeling dataset.
- All user-facing copy is "research support, not investment advice." Do not soften or remove weak-signal or withdrawn-result caveats; legacy pre-audit surfaces keep their `withdrawn_pre_pit` label. Outward claims follow the Model Confidence Contract.
- Frontend demo/mock data is fallback-only; real API behavior must be preserved on every page of the frozen app.
- No paid data or APIs, no secrets in git, no public redistribution of raw third-party data. New automated acquisition belongs in the PIT Kernel under an approved per-source rights decision, not in this repository. Never script requests against Borsa Istanbul DataStore.

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
# Root pipeline tests (current observed count: docs/VERIFICATION_BASELINE.md)
PYTHONPATH=. python -m pytest tests/          # == make research-agent-check

# Backend tests (current observed count: docs/VERIFICATION_BASELINE.md; sqlite, no Postgres needed)
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

### Current verification baseline

- The dated, command-level source of truth for root/backend suite counts and data validation is `docs/VERIFICATION_BASELINE.md`. Do not copy those counts into new operating docs; cite the baseline instead.
- OPS-05 resolved the earlier backend collection failure from unknown provider/tooling keys in `backend/.env`; settings now ignore unknown keys. Both `cd backend && python -m pytest tests/` and `PYTHONPATH=backend python -m pytest backend/tests` are supported.
- OPS-01 resolved the stale `call_local_llm` test and evaluation references; the current baseline records no known root-suite failures.

## Forbidden Changes

- Adding synthetic/fabricated data or imputing stored data.
- Adding data-acquisition code (scrapers, downloaders) to this repository; it belongs in the PIT Kernel.
- Adding paid API dependencies or committing secrets (`SECRET_KEY`, API keys).
- Removing leakage/frozen-snapshot validation guards or weak-signal UI caveats.
- Writing LLM output into the modeling dataset or storing it as a source fact.
- Evaluating on the locked holdout outside a pre-registered confirmatory analysis.
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
