# PRD.md

## Project Definition

**FinanceIQ** is a completed university capstone: an honest, leakage-safe **T→T+1 equity-research system** for 40 public BIST (Borsa Istanbul) companies, 2020–2025, with an 81-ticker internal training universe. It combines:

- a validated no-fabrication data pipeline (yearly XLSX + free Yahoo prices + manual shares/corrections → T→T+1 modeling dataset),
- walk-forward ML experiments against a BIST100 benchmark,
- an explainable hybrid research agent (deterministic + optional OpenRouter/local LLM),
- a dark "Research Terminal" React frontend (FastAPI + Postgres behind it).

No paid APIs, no scrapers, no synthetic data.

## Current Reality

- **Capstone status: complete** (see `TASK_STATE.md`). Test state re-verified 2026-07-08: **backend 51/51 pass**; **root 95/97 pass**, with 2 failures from a stale `call_local_llm` reference in `tests/test_research_agent.py` (the function is now `call_llm`). The ledger's "97 + 51 all passing" line reflects 2026-06-11 and is now out of date.
- **The headline finding is negative and intentional:** walk-forward Spearman IC ≈ 0; the model shows no reliable predictive edge and does not consistently beat simple baselines. The UI displays this prominently ("A weak signal, reported honestly.").
- Modeling dataset: 403 rows / 81 tickers / 321 target rows (`data/trusted_clean/modeling_dataset_2020_2025.csv`); public subset stays 40 tickers.
- Vendor XLSX fundamentals are partly a **frozen 2025 snapshot** — rejected for modeling; real per-year income/profitability ingested via corrected yearly files; valuation reconstructed from Yahoo price × manual shares.
- Deployment paths exist: Docker Compose (local), Render blueprint (backend, `render.yaml`), Vercel (frontend, `vercel.json`), Supabase Auth. Live-deployment state: needs verification.
- LLM layer is optional; `RESEARCH_LLM_PROVIDER=none` gives a deterministic fallback that always works.

## Target Users / Consumers

- Capstone evaluators/instructors reviewing methodology and honesty.
- The project author maintaining/demoing it.
- Researchers using the scores as **research support only — never investment advice** (stated throughout code and UI).

## Core Problem

Can free, validated, leakage-safe fundamentals predict next-year BIST stock returns? The rigorous answer produced here: **not reliably** — and the system is built to demonstrate that transparently rather than hide it.

## Core Workflows

1. **Data pipeline** (repo root): `make full-research` — extract → benchmark → corrected yearly ingest → fetch Yahoo prices → free valuation → build T→T+1 dataset → integrate training-only tickers → validate → experiments. Outputs + audit reports in `data/trusted_clean/`.
2. **Serving**: backend loads trusted yearly data into Postgres on startup. `research.py` and `research_agent.py` both mount under the `/research` prefix (scores, diagnostics, data-quality evidence). The forecasting router declares **no prefix** — its routes sit at the API root (`/get-stocks`, `/predict`, `/predict/evaluate`, `/train-model`, `/get-parameters`, …), not under `/forecasting/*`.
3. **Research agent**: `POST /research/ask` — grounded intents over validated evidence; hybrid score `0.65*ml + 0.20*confidence + 0.15*llm`, LLM optional and sandboxed.
4. **Frontend**: routes `/dashboard`, `/research-agent`, `/companies`, `/experiments`, `/research`, `/data-quality`, `/benchmark`, `/forecasting` — each a research surface that keeps caveats and IC ≈ 0 visible; demo data as fallback only.
5. **Training prep (no training performed)**: `research_agent_training/` generates/validates instruction JSONL from real reports.

## Intended Direction

Beyond-capstone options only (from `TASK_STATE.md`, all optional): expand the training universe via the ready yfinance workflow, obtain genuine quarterly fundamentals, optionally fine-tune a local model per `research_agent_training/mlx_training_plan.md`. No committed roadmap; a **candidate** roadmap (assessment, staged ideas, execution queue) was documented 2026-07-12 in `FINANCEIQ_MOONSHOT_ROADMAP.md` + `FINANCEIQ_AGENT_TASK_QUEUE.md` Phase 2 — its theme is "instrument the negative result" (significance testing, reproducibility manifests, claim-gating, adversarial self-checks), never manufacturing predictive-edge claims.

## Non-Goals

- Producing investment advice or claiming predictive edge.
- Real-time/intraday data, paid data vendors, web scraping.
- Fabricating or imputing missing values.
- Making the LLM a numerical model or letting it write into the dataset.

## Constraints

- Free data sources only; shares outstanding is manual (capital-event CSV) — derived valuation stays null until supplied.
- Yearly granularity; quarterly exports are frozen and excluded.
- 2024 vendor export was column-misaligned; fixed via a manual, shape-validated 2024-only override.
- Secrets via env only; nothing committed. Default deployment is open read-only demo; private lockdown is env-gated.

## Success Criteria

- Pipeline reproducible end-to-end via Makefile with all validation gates passing.
- All tests green (root + backend).
- Every score surfaced with its components, caveats, and data-quality evidence.
- No fabricated value anywhere; negative result reported plainly.

## Resolved (verified 2026-07-08)

- **`unnecessary/` quarantine: does not exist.** Absent from the working tree, untracked by git (`git ls-files unnecessary` → empty), and not gitignored. The `README.md:396` link to `unnecessary/README.md` is therefore **dead**. The quarantine rule in `CLAUDE.md` ("do not reintroduce Finnhub, news API, synthetic seeders, KAP scraper") still stands on its own; only the directory link is stale. Fixing README is outside the four-file scope.
- **`backend/airflow/`: one orphaned DAG.** Contains exactly `dags/forecasting_retrain_dag.py`, a tracked `BashOperator` DAG (`forecasting_retrain_daily`, `0 3 * * *`) shelling out to `backend/scripts/retrain_forecasting.py`. `airflow` appears in **no** dependency or deploy file (`backend/requirements.txt`, `docker-compose.yml`, `render.yaml`, `Makefile`). Nothing schedules or imports it — treat as dormant/aspirational, not live infrastructure.
- **Test counts.** Re-run above: backend 51/51 green; root 97 collected, 95 green, 2 red.
- **Dataset shape.** Independently recounted from `data/trusted_clean/modeling_dataset_2020_2025.csv`: 403 rows, 81 unique tickers, `has_target=True` on 321 rows. Matches the documented 403/81/321.
- **Quarterly fundamentals template (verified 2026-07-12): live download endpoint, not a pipeline input.** `grep -rn "quarterly_fundamentals_template" backend/ scripts/` returns `backend/app/main.py:101` (the template path) and `backend/app/main.py:102` (the `FileResponse`); `GET /fundamentals/template` therefore serves the CSV to callers. The grep has no `scripts/` result, so the template is not consumed by the root modeling pipeline. Its availability does not change the rule that frozen quarterly exports are excluded from modeling.
- **`backend/experiments/` (verified 2026-07-12): no repo-defined role.** The directory is empty; `git ls-tree -r --name-only HEAD -- backend/experiments` and `git log --all --oneline -- backend/experiments` both return no entries, and there are no source references to the path. It is an untracked local directory with no recoverable repository purpose; preserving or deleting it remains an owner decision.

## Needs Verification

- Whether Render/Vercel/Supabase deployments are currently live and at which URLs. Deploy *definitions* are present and internally consistent (`render.yaml` → `financeiq-backend` + `financeiq-db`; root `vercel.json`), but liveness was not probed — confirming it requires an outbound request, not a repo read.
