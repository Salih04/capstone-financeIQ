# FinanceIQ

An honest, leakage-safe **T→T+1 equity-research system** for 40 public BIST companies
(2020–2025), with an expanded 81-ticker internal training universe: a validated modeling dataset, a BIST100 benchmark, a free-data
valuation reconstruction, an explainable hybrid research agent, and a "Research
Terminal" frontend. No paid APIs, no synthetic/fabricated data, no scrapers.

> **Capstone status: complete.** The pipeline is rigorous and transparent. The
> honest finding is that the model still shows **no reliable predictive edge** after
> expanding internal training to 81 tickers (walk-forward Spearman remains weak/unstable).
> That is a defensible negative result,
> not a bug see `TASK_STATE.md`.

**Validated features: 40** balance-sheet + growth (reference), real per-year
income/profitability (corrected yearly: revenue, margins, ROE, ROA, …), and
free-derived valuation (market_cap, enterprise_value, pe_ratio, pb_ratio,
ev_ebitda), plus leakage-safe year-T price/benchmark features. Old frozen-snapshot
valuation and price/return leakage are rejected.

## Architecture

```
React (1.frontend) ──HTTP──▶ FastAPI (2.backend) ──SQLAlchemy──▶ PostgreSQL
```

Three Docker services: `db`, `backend`, `frontend`. The backend converts the
trusted XLSX files to CSV and loads them into Postgres on startup.

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

Entry route: `/login`.

## ⚠️ Data reliability & the modeling pipeline

The yearly XLSX / `data/trusted/stocks_2020_2025.csv` files are **unreliable for
fundamentals**: income-statement, profitability, valuation and momentum fields
are a frozen 2025 snapshot repeated across years (only balance-sheet, growth and
realized return vary). They are kept as **reference / target bootstrap only**.

The correct **T → T+1** modeling dataset (year-T features → year-(T+1) realized
return) is built by a separate, validated pipeline:

```bash
make full-research        # full pipeline: extract → benchmark → corrected yearly
                          #   → fetch prices → free valuation → build
                          #   → integrate training-only tickers → validate → experiments
make full-research-agent  # full pipeline + frozen evidence + split + contexts + audit + tests
# or individual stages:
make fetch-training-prices # Yahoo year-end prices for public + training-only universe
make shares               # expand capital-event shares → per-year (carry-forward)
make valuation            # free valuation: Yahoo price × shares × financials → ratios
make data                 # build + validate the T→T+1 modeling dataset
make data-audit           # write CSV inventory/count/missingness report
```

Outputs in `data/trusted_clean/` (`modeling_dataset_2020_2025.csv`,
`modeling_dataset_public_2020_2025.csv`, `modeling_dataset_training_2020_2025.csv`,
`data_quality_report.json/.md`, `pipeline_audit_report.*`,
`feature_engineering_report.*`, `free_valuation_history_report.*`,
`corrected_yearly_ingestion_report.*`, `data_dictionary.md`). See
**[DATA_PIPELINE.md](DATA_PIPELINE.md)** and **[DATA_REQUIREMENTS.md](DATA_REQUIREMENTS.md)**.

Real per-year income/profitability is now ingested (corrected yearly files) and
valuation is reconstructed for free from Yahoo year-end price × manual shares
outstanding. Supply shares via the capital-event file
(`data/trusted_raw/shares_outstanding_events.csv`) and 2024 fixes via
`data/trusted_raw/financials/corrected_balance_sheet_2024.csv`. Targets are real;
no value is fabricated or imputed.

## Research Assistant (OpenRouter/local-LLM-assisted)

A constrained research-support layer. The **structured ML pipeline stays the
primary numerical model**; the LLM only reads validated structured evidence and
produces cautious explanation + a bounded `llm_research_score` in [0,1]. It never
predicts prices/returns, never gives buy/sell/hold, never fabricates facts.

Hybrid score (weights configurable via env):
```
final_research_score = 0.65*ml_score + 0.20*confidence_score + 0.15*llm_research_score
```
Components are always returned separately; `ml_score` may be null (partial score).

Endpoints (`/research/summary`, `/research/company/{ticker}`,
`/research/company/{ticker}/score`, `/research/model-diagnostics`,
`/research/data-quality`, `/research/ai-status`, `POST /research/ask`).
Frontend page: `/research-agent`.

### Run with / without an LLM
```bash
# No LLM deterministic fallback, always works:
export RESEARCH_LLM_PROVIDER=none

# OpenRouter (OpenAI-compatible):
export RESEARCH_LLM_PROVIDER=openrouter
export RESEARCH_LLM_BASE_URL=https://openrouter.ai/api/v1/chat/completions
export RESEARCH_LLM_MODEL=openai/gpt-oss-120b:free
export OPENAI_API_KEY=your-openrouter-key

# LM Studio (legacy local option):
export RESEARCH_LLM_PROVIDER=lmstudio
export RESEARCH_LLM_BASE_URL=http://localhost:1234/v1/chat/completions
export RESEARCH_LLM_MODEL=your-local-model

# Ollama:
export RESEARCH_LLM_PROVIDER=ollama
export RESEARCH_LLM_BASE_URL=http://localhost:11434/api/chat
export RESEARCH_LLM_MODEL=qwen2.5:3b-instruct
```
Any LLM error falls back to the deterministic path; it cannot break the pipeline.
Check configuration with `GET /research/ai-status` or `/research/ai-status?smoke=true`.

### Training preparation (no training here)
```bash
make research-agent-dataset     # instruction JSONL from real reports (sample committed)
```
See `research_agent_training/` (`mlx_training_plan.md`, `prompt_policy.md`,
`evaluation_rubric.md`, `schema.json`). LLM output is **never** written back into
the modeling dataset. Research-support only not investment advice.

## Trusted data source (legacy reference)

The yearly XLSX set in `3.Datasets/` (reference/bootstrap, see warning above):

```
3.Datasets/2020stocks.xlsx … 2025stocks.xlsx   (40 BIST companies × 54 columns)
```

These are converted, deterministically and without fabrication, to:

```
data/trusted/2020stocks.csv … 2025stocks.csv   one clean CSV per year
data/trusted/stocks_2020_2025.csv              combined, with a `year` column
```

and loaded into the `yearly_stocks` Postgres table (one row per ticker-year).

The data contract lives in [`2.backend/app/trusted_data.py`](2.backend/app/trusted_data.py):
column map, required/optional columns, percent vs. monetary fields, safe numeric
parsing (BOM, thousands separators, negatives), and validation. Missing values
stay null they are never invented.

### Pipeline commands

```bash
cd 2.backend

# 1. Convert XLSX -> clean CSVs (writes data/trusted/)
python -m scripts.convert_trusted_xlsx

# 2. Load combined CSV -> Postgres (idempotent; aborts on invalid data).
#    Auto-converts first if the combined CSV is missing.
python -m scripts.load_trusted_yearly
python -m scripts.load_trusted_yearly --reconvert   # force re-convert first
python -m scripts.load_trusted_yearly --summary      # DB summary, no write

# 3. Validate everything (data + schema + no banned refs + compile)
python -m scripts.validate_trusted_data
```

On Docker startup the backend runs Alembic migrations first, then
`python -m scripts.load_trusted_yearly` automatically (see
`2.backend/scripts/start_backend.sh`).

## Run with Docker

```bash
export RESEARCH_LLM_PROVIDER=openrouter
export RESEARCH_LLM_BASE_URL=https://openrouter.ai/api/v1/chat/completions
export RESEARCH_LLM_MODEL=openai/gpt-oss-120b:free
export OPENAI_API_KEY=your-openrouter-key
docker compose up --build
```

The trusted dataset is mounted (`./3.Datasets`) and loaded on boot. Paths inside
the container are set via `TRUSTED_DATASETS_DIR`, `TRUSTED_OUT_DIR`,
`TRUSTED_COMBINED_CSV` in `docker-compose.yml`.

## Deploy frontend on Vercel

Vercel deploys the React frontend only. The FastAPI backend must be running on a
public URL (Railway, Render, Fly.io, a VPS, or another host). If `VITE_API_URL`
is missing, the browser posts login requests to the Vercel static site at
`/api/auth/login`, which returns `405 Method Not Allowed`.

Set these Vercel environment variables, then redeploy:

```bash
VITE_API_URL=https://your-backend-domain
```

Backend environment must include:

```bash
OPENAI_API_KEY=your-openrouter-key
RESEARCH_LLM_PROVIDER=openrouter
RESEARCH_LLM_MODEL=openai/gpt-oss-120b:free
```

Quick check:

```bash
curl https://your-backend-domain/health
```

## Local development

### Backend

```bash
cd 2.backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set DATABASE_URL and SECRET_KEY
alembic upgrade head
python -m scripts.load_trusted_yearly
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd 1.frontend
npm install
npm run dev
```

### Database migrations (Alembic)

```bash
cd 2.backend
alembic upgrade head        # head includes 20260406_0006 (yearly_stocks)
```

`create_all` on startup is a safety net for fresh DBs; Alembic owns the schema.
Docker startup runs Alembic automatically before trusted data loading. Existing
Docker volumes created before Alembic are stamped once, then upgraded normally.

## Environment variables

| Var | Purpose |
|---|---|
| `DATABASE_URL` | Postgres connection string |
| `SECRET_KEY` | JWT signing key. **Not committed.** If unset, a random per-process key is generated (JWTs reset on restart) set it explicitly in production. |
| `OPENROUTER_API_KEY` / `OPENAI_API_KEY` | OpenRouter API key for AI research support |
| `RESEARCH_LLM_PROVIDER` | `openrouter`, `lmstudio`, `ollama`, or `none` |
| `RESEARCH_LLM_MODEL` | Chat model id (default `openai/gpt-oss-120b:free` for OpenRouter) |
| `TRUSTED_DATASETS_DIR` | Dir of trusted XLSX (default `3.Datasets/`) |
| `TRUSTED_OUT_DIR` | Output dir for generated CSVs (default `data/trusted/`) |
| `TRUSTED_COMBINED_CSV` | Combined CSV path used by the loader |
| `RUN_DB_MIGRATIONS` | Run Alembic on Docker startup (`1` default, set `0` to skip) |
| `LOAD_TRUSTED_DATA` | Load trusted yearly data on Docker startup (`1` default, set `0` to skip) |

No real secrets are committed. `.env` is gitignored.

## What was removed / quarantined

Everything non-trusted is in [`unnecessary/`](unnecessary/README.md):

- **Finnhub** removed entirely (API key assumed leaked).
- **News API / news page** removed (not essential, was Finnhub-backed).
- **Synthetic generator, seeders, KAP scraper, xlsx-into-quarterly importer** quarantined.
- **Old quarterly-CSV workflow** (`quarterly_fundamentals_2025.csv`, `load_trusted_fundamentals.py`) retired in favor of the yearly XLSX pipeline.
- **Hardcoded secrets** the `SECRET_KEY` and `NEWS_API_KEY` defaults are gone.

## Known limitations (accepted)

- **No reliable predictive edge.** Even after expanding the internal training
  universe to 81 tickers, the walk-forward signal is weak/unstable and ML does not
  consistently beat simple baselines. This is the honest result; treat scores as
  research support, not investment advice.
- **Shares outstanding is manual.** No free historical source exists, so market_cap
  (and the valuation ratios derived from it) require the capital-event file. Until
  supplied for a ticker, those values stay null never fabricated.
- **2024 vendor export was column-misaligned.** Handled via the manual
  `corrected_balance_sheet_2024.csv` (shape-validated, 2024-only override); an
  upstream-clean export would still be preferable.
- **Forecasting (legacy `/forecasting`)** is functional: `/forecasting/filters`
  unions cohort + uploaded fundamentals, actions return friendly errors (never raw
  500) and stay re-clickable. It remains a separate legacy tool from the Research
  Terminal.
- Dataset is **yearly**; the quarterly Fintables exports are a frozen snapshot and
  are excluded (see `make inspect-quarterly`). No future-year leakage (enforced in
  `validate.py`).
```
