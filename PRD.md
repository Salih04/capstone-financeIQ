# PRD.md

## Project Definition

**FinanceIQ** is a completed university capstone: an honest, leakage-safe **T→T+1 equity-research system** for 40 public BIST (Borsa Istanbul) companies, 2020–2025, with an 81-ticker internal training universe. It combines:

- a validated no-fabrication data pipeline (yearly XLSX + free Yahoo prices + manual shares/corrections → T→T+1 modeling dataset),
- walk-forward ML experiments against a BIST100 benchmark,
- an explainable hybrid research agent (deterministic + optional OpenRouter/local LLM),
- a dark "Research Terminal" React frontend (FastAPI + Postgres behind it).

No paid APIs, no scrapers, no synthetic data.

## Current Reality

- **Capstone status: complete** (see `TASK_STATE.md`). Root 97 + backend 51 tests passing as of last ledger update (2026-06-11).
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
2. **Serving**: backend loads trusted yearly data into Postgres on startup; `/research/*` and `/forecasting/*` endpoints serve scores, diagnostics, data-quality evidence, and CSV-backed forecasting.
3. **Research agent**: `POST /research/ask` — grounded intents over validated evidence; hybrid score `0.65*ml + 0.20*confidence + 0.15*llm`, LLM optional and sandboxed.
4. **Frontend**: routes `/dashboard`, `/research-agent`, `/companies`, `/experiments`, `/research`, `/data-quality`, `/benchmark`, `/forecasting` — each a research surface that keeps caveats and IC ≈ 0 visible; demo data as fallback only.
5. **Training prep (no training performed)**: `research_agent_training/` generates/validates instruction JSONL from real reports.

## Intended Direction

Beyond-capstone options only (from `TASK_STATE.md`, all optional): expand the training universe via the ready yfinance workflow, obtain genuine quarterly fundamentals, optionally fine-tune a local model per `research_agent_training/mlx_training_plan.md`. No committed roadmap.

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

## Needs Verification

- Whether Render/Vercel/Supabase deployments are currently live and at which URLs.
- `unnecessary/` quarantine directory is referenced by `README.md` but absent from this worktree.
- Test counts (97/51) reflect the 2026-06-11 ledger; re-run to confirm current state.
- `backend/airflow/` exists but its role/liveness is undocumented.
