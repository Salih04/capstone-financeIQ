# FINANCEIQ_SMALL_MODEL_RULES.md

Binding rules for small/cheap coding models working in this repository. These are repo-specific; they supplement, never override, `CLAUDE.md`.

## 1. Required read order

1. `CLAUDE.md` 2. `PRD.md` 3. `REPO_MAP.md` 4. your assigned task in `FINANCEIQ_AGENT_TASK_QUEUE.md` (or `TASK.md`) 5. this file 6. **only** the files your task lists under "Read first". Do not scan the tree; `REPO_MAP.md` is the map. Do not read `data/` CSVs (the `.md`/`.json` reports in `data/trusted_clean/` are allowed and are the source of truth for data-reliability facts). Grep `TASK_STATE.md`; never read it whole.

## 2. Maximum edit scope

- ≤ 5 files per task, and only files your task names or their directly-matching test files.
- No new dependencies (`backend/requirements.txt`, `frontend/package.json` are frozen for you).
- No new directories except files explicitly assigned.
- If a fix seems to require touching a 6th file or an unlisted file: STOP and report instead.

## 3. Safe task types (for you)

- Documentation and prose corrections in root `.md` files.
- Frontend copy/wording changes (disclaimers, caveats, scope lines) in `frontend/src/pages/*.jsx`.
- Renaming a stale reference in a test to match existing source (e.g. OPS-01: `call_local_llm` → `call_llm`).
- Adding tests that pin *existing* behavior without changing source.
- Running documented verification commands and recording results.

## 4. Unsafe task types (never yours, even if asked casually)

- Anything in `scripts/data_collection/` (leakage/frozen guards live here — project credibility depends on them).
- `experiments/run_experiments.py` (metrics/report generation).
- `backend/app/services/forecasting_csv_service.py`, `scoring_service.py`, `adaptive_weights_service.py`, `research_agent.py` score math (the `0.65/0.20/0.15` hybrid weights and penalty terms).
- Alembic migrations (`backend/alembic/versions/` — append-only, and not by you).
- Regenerating datasets (`make data`, `make full-research`, `make research`) — these rewrite committed outputs.
- Auth/JWT verification code (`test_supabase_jwks.py` territory).

## 5. Avoid unless explicitly assigned

`data/` (everything), `experiments/results|reports/`, `backend/alembic/`, `backend/airflow/` (one dormant DAG; airflow isn't even installed — do not "fix" or delete it), `research_agent_training/`, `frontend/package-lock.json`, `docker-compose.yml`, `render.yaml`, `vercel.json` (note: there are TWO vercel.json files; the root one carries build config), `Makefile` (adding a target may be assigned; renaming targets is forbidden for everyone).

## 6. Requires strong-model review regardless of who edits

Any diff touching: leakage guards (`scripts/data_collection/validate.py`, `manual_ingest.py`), the DEGENERATE caveat block (`experiments/run_experiments.py:425-430`), dataset build order in `Makefile` (`fetch-training-prices` → `valuation` → `data` → `integrate-pilot-tickers` → `data-validate`), the 2024 manual balance-sheet override, or `frontend/src/api/cache.js` rules (never cache auth, `/research/ask`, or errors).

## 7. Common failure modes in this repo (observed, not hypothetical)

- **`cd backend && pytest tests/` aborts at collection** when an untracked `backend/.env` holds `OPENROUTER_*` keys (`Settings` forbids extras). Run `PYTHONPATH=backend python -m pytest backend/tests` from the repo root instead.
- **Assuming router prefixes**: forecasting and scoring routers have **no prefix** — routes sit at API root (`/get-stocks`, `/predict`, …), while `research.py` *and* `research_agent.py` both mount under `/research`. Always check `backend/app/routers/<x>.py` before naming an endpoint.
- **Assuming router→service symmetry**: `auth`/`companies`/`admin`/`users` routers have no service module; `research.py` is backed by the `services/research/` subpackage.
- **Trusting generated reports' prose**: `experiments/reports/summary.md` contains a hardcoded stale caveat. Metrics tables are committed evidence; embedded prose may lag.
- **"Fixing" the dead `unnecessary/README.md` link by creating the directory** — the directory was deliberately removed; fix the link, never recreate the target.
- **Editing files under `data/trusted/` or `data/trusted_clean/` by hand** — they are generated; hand edits are forbidden and will be overwritten.

## 8. Frontend wording changes, safely

Read the whole target page first. Match the dark "Research Terminal" visual language and existing copy tone. Never remove or soften weak-signal caveats (e.g. `DashboardPage.jsx` "A weak signal, reported honestly."). Demo/mock data is fallback-only — do not touch the real-API code path or the fallback trigger. New numbers in copy must come from `data/trusted_clean/data_quality_report.md` or `experiments/leaderboard.csv`, cited in your report. Verify with `cd frontend && npm run build` (requires `npm install` first if `node_modules` is absent).

## 9. Backend changes, safely

Only with an assigned task naming the router/service. Read router + matching service + matching test file fully. Never change response shapes without a test proving the old contract (the contract tests in `backend/tests/test_forecasting_api_contract.py` exist for exactly this). Verify: `PYTHONPATH=backend python -m pytest backend/tests` → expect 51 pass (or more if you added tests); any failure you didn't introduce must be reported, not "fixed".

## 10. Data pipeline changes, safely

For a small model: you don't make them. If assigned anything under `scripts/` anyway, treat it as mis-assignment — report back citing this file. The one exception: adding a *test* that pins existing pipeline behavior, verified by `PYTHONPATH=. python -m pytest tests/` and `make data-validate` (which must still report 403 rows / 40 features / 321 target rows unless your task says otherwise).

## 11. ML/scoring changes, safely

You don't make these either. The hybrid score weights, forecasting heuristic, and adaptive weights are strong-model territory (§4, §6). Copy *describing* scores is yours only under §8 rules, and must never upgrade a claim (no "predicts", no accuracy numbers not present in committed results).

## 12. Required verification behavior

Run the verification commands your task lists — actually run them, do not simulate output. Expected baselines: backend 51/51; root 97 collected (95 pass + 2 known `call_local_llm` failures until OPS-01 lands, then 97/97); `make data-validate` → "valid for T→T+1 modeling: True". If a command cannot run (missing Postgres, missing node_modules), say so explicitly — never report a pass you didn't observe.

## 13. Final response checklist (all required)

1. **What changed** — each file + one-line rationale.
2. **Verification** — exact commands and honest pass/fail output.
3. **Not done / needs verification** — anything skipped, assumed, or unrunnable.
4. Confirm no forbidden area (§4–§6) was touched — state it explicitly.

## 14. Stop conditions (halt and report; do not improvise)

- Task requires touching a §4/§5 area or a 6th file.
- A test that was green at baseline turns red for reasons outside your diff.
- You need data-reliability facts not present in `data_quality_report.md`/`frozen_column_evidence.md`.
- The task asks you to weaken a caveat, add data values, impute, scrape, or add a paid API — refuse; these are project-level forbidden changes.
- Repo evidence contradicts your task description — report the contradiction rather than picking a side.
