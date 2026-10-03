# OPERATING_LAYER_VALIDATION.md

Validation pass of the four-file operating layer (`CLAUDE.md`, `PRD.md`, `REPO_MAP.md`, `TASK.md`) against the live repository. Performed 2026-07-08 on branch `local/capstone-strategy-readiness-ab0527` (clean tree, HEAD `47e1510a`).

## 1. Files inspected

- Operating layer: `CLAUDE.md`, `PRD.md`, `REPO_MAP.md`, `TASK.md` (read in full).
- Structure: repo root listing; `backend/app/routers/` (15 routers), `backend/app/services/` (17 modules + `research/` subpackage), `frontend/src/pages/` (21 pages), `scripts/` + `scripts/data_collection/` (22 stage modules), `experiments/` (`run_experiments.py`, `leaderboard.csv`, `reports/`, `results/`), `tests/` (11 files), `backend/tests/` (7 test files + conftest), `data/trusted_clean/` (34 outputs/reports).
- Code spot-checks: `backend/app/main.py` (router registration), `backend/app/routers/{research,research_agent,forecasting,scoring}.py` (prefixes), `backend/app/services/research_agent.py` (hybrid weights), `backend/app/services/forecasting_csv_service.py` (serving model), `backend/app/services/adaptive_weights_service.py`, `frontend/src/App.jsx` (routes), `frontend/package.json` (scripts), `Makefile` (all targets), `experiments/run_experiments.py:405-440`.
- Evidence reports: `data/trusted_clean/data_quality_report.md`, `frozen_column_evidence.md`, `experiments/reports/summary.md`, `TASK_STATE.md` (grepped, not read whole).

## 2. Commands discovered

From `CLAUDE.md`/`Makefile`/`package.json`: root pytest, backend pytest, `make data`, `make data-validate`, `make full-research`, `make research`, `make research-agent-check`, `make benchmark`, `make build-company-contexts` (plus ~25 other Makefile targets, all present), backend uvicorn/alembic, `npm run dev|build|preview|e2e`, `docker compose up --build`.

## 3. Commands verified / not verified

| Command | Result |
|---|---|
| `PYTHONPATH=. python -m pytest tests/` | **Run: 95 passed, 2 failed** — exactly the two documented stale `call_local_llm` failures. Matches CLAUDE.md. |
| `PYTHONPATH=backend python -m pytest backend/tests` | **Run: 51 passed.** Matches CLAUDE.md, including the `backend/.env` gotcha workaround. |
| `make data-validate` | **Run: passes** — 403 rows / 40 features / 321 target rows / 82 inference-only, "valid for T→T+1 modeling: True". Matches PRD numbers. |
| `git status --short` | **Run: clean.** |
| `npm run build` / `npm run e2e` | **Not run** — `frontend/node_modules` is absent in this worktree; would require `npm install` (dependency download), out of proportion for a docs-only pass. |
| `make data` / `make full-research` / `make research` | **Not run** — they regenerate datasets/experiment outputs; running them mutates generated files, forbidden for this task. Target definitions verified to exist in `Makefile`. |
| `alembic upgrade head` | **Not run** — requires a Postgres instance. |
| `docker compose up --build` | **Not run** — heavyweight; definitions verified to exist. |

## 4. Incorrect paths found

None. Every path named in the four files exists (spot-checked per TASK.md's own verification list). Two path claims are *about* absence and were re-confirmed: `unnecessary/` does not exist (README.md:396 link is dead, as PRD.md already records) and `.agent/` did not exist before this pass.

## 5. Stale or misleading architecture claims

None in the four operating-layer files — the previous validation pass (commit `47e1510a`) already corrected them, and my re-checks agree:

- Router prefixes verified: `research.py` and `research_agent.py` both declare `prefix="/research"`; `forecasting.py` and `scoring.py` declare **no prefix** (`backend/app/routers/*.py`, `backend/app/main.py:78-91`). PRD.md describes this correctly.
- Frontend routes in PRD.md all exist in `frontend/src/App.jsx:36-60`.
- Service↔router mapping caveats in CLAUDE.md/REPO_MAP.md match `backend/app/services/` contents.

One stale claim exists **outside** the operating layer and is worth recording: `experiments/reports/summary.md` embeds a hardcoded "DEGENERATE data" caveat (written unconditionally by `experiments/run_experiments.py:425-430`) claiming predictor features are identical every year. Git history shows the last experiment run (2026-06-10, commit `fed0c165`) postdates the corrected-yearly ingest (2026-06-06, `7aa1d834`), and `data_quality_report.md` confirms corrected columns genuinely vary by year. The caveat overstates the current degeneracy; fixing it is a source change (see task queue DATA-04).

## 6. Missing high-leverage repo areas

The operating layer did not previously point to these; now covered by the new documents rather than by editing REPO_MAP.md (which TASK.md scoped to the four files):

- `backend/app/services/forecasting_csv_service.py` — the actual serving-side "model" (deterministic winner-discrimination weights). Highest-leverage file for any forecasting claim.
- `backend/app/services/adaptive_weights_service.py` + `scoring_service.py` — the legacy DB-backed scoring/weighting path, distinct from the CSV path.
- `experiments/results/` — contains a second summary (`experiment_summary.md`) and feature-stability/coverage CSVs not mentioned in REPO_MAP.md.
- Six routers beyond those REPO_MAP.md names explicitly (`financials`, `fundamentals`, `ingestion`, `labeling`, `reports`, `validation`) — covered by its "…", but small models should know they exist.

## 7. Risky or ambiguous operating-layer instructions

1. **TASK.md was stale**: it described the operating-layer validation task already completed in commit `47e1510a`, and its "Forbidden Changes" bans creating documentation files beyond the four — which conflicts with this explicitly-assigned strategy pass. Resolved by appending a status note to TASK.md (see §8). Future agents reading TASK.md before this note could have re-done finished work.
2. **`cd backend && python -m pytest tests/` in CLAUDE.md** is listed as a primary command but fails when an untracked `backend/.env` holds `OPENROUTER_*` keys. CLAUDE.md documents the gotcha immediately below; left as-is since the warning is adjacent and accurate.
3. **"Do not read `data/` CSVs"** (CLAUDE.md token rules) is safe but ambiguous for the `.md` reports in `data/trusted_clean/`, which CLAUDE.md's Uncertainty Rules *require* reading for data-reliability facts. Interpretation: the rule targets CSVs, not the `.md`/`.json` reports. Not edited; recorded here.

## 8. Corrections made

- `TASK.md`: appended a **Status** section stating the validation objective was completed (commit `47e1510a`, re-verified this pass) and pointing the next agent to `FINANCEIQ_AGENT_TASK_QUEUE.md` for current work. No other operating-layer edits were needed — all checked claims held.

## 9. Remaining uncertainties

- Render/Vercel/Supabase deployment liveness (PRD.md already flags this; confirming needs an outbound probe, not a repo read).
- `backend/templates/quarterly_fundamentals_template.csv` — live input vs leftover (PRD.md flags it; queued as OPS-06).
- `backend/experiments/` empty local directory — purpose unknown (PRD.md flags it).
- Frontend production build and Playwright e2e status — not run (no `node_modules`); queued as VER-02.
- Whether the frozen-column caveat in `experiments/reports/summary.md` materially changes the headline IC ≈ 0 conclusion after correction — requires re-running `make research` (queued as DATA-04/DATA-05; do not re-run casually, it rewrites generated outputs).

## 10. Final judgment

**SAFE_FOR_SMALL_MODELS** — *for the task types defined in `FINANCEIQ_SMALL_MODEL_RULES.md`* (docs, UI wording, isolated test fixes, single-endpoint changes with existing test coverage). The four-file layer is accurate, internally consistent, command-verified, and explicitly marks its own uncertainties. Anything touching `scripts/data_collection/`, `experiments/run_experiments.py`, dataset regeneration, or scoring/weight math remains **strong-model territory** regardless of this judgment; that boundary is enforced by the rules file, not by the operating layer alone.
