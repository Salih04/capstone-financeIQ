# FinanceIQ

Forecasting and comparison platform for BIST stocks, driven by a single trusted
local dataset: the **2020–2025 yearly stock XLSX files**. No external APIs, no
synthetic data, no scrapers.

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
make data        # or: PYTHONPATH=. python -m scripts.data_collection.build_all
```

Outputs in `data/trusted_clean/` (`modeling_dataset_2020_2025.csv`,
`data_quality_report.json/.md`, `data_dictionary.md`). See **[DATA_PIPELINE.md](DATA_PIPELINE.md)**
and **[DATA_REQUIREMENTS.md](DATA_REQUIREMENTS.md)**. Real income-statement/valuation
history must be ingested manually (see DATA_REQUIREMENTS) for true prediction;
the current targets are real, the year-T fundamentals are provisional.

## Research Assistant (local-LLM-assisted)

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
`/research/data-quality`, `POST /research/ask`). Frontend page: `/research-agent`.

### Run with / without an LLM
```bash
# No LLM (default) — deterministic fallback, always works:
export RESEARCH_LLM_PROVIDER=none

# LM Studio (OpenAI-compatible):
export RESEARCH_LLM_PROVIDER=lmstudio
export RESEARCH_LLM_BASE_URL=http://localhost:1234/v1/chat/completions
export RESEARCH_LLM_MODEL=your-model

# Ollama:
export RESEARCH_LLM_PROVIDER=ollama
export RESEARCH_LLM_BASE_URL=http://localhost:11434/api/chat
export RESEARCH_LLM_MODEL=qwen2.5:3b-instruct
```
Any LLM error falls back to the deterministic path — it cannot break the pipeline.

### Training preparation (no training here)
```bash
make research-agent-dataset     # instruction JSONL from real reports (sample committed)
```
See `research_agent_training/` (`mlx_training_plan.md`, `prompt_policy.md`,
`evaluation_rubric.md`, `schema.json`). LLM output is **never** written back into
the modeling dataset. Research-support only — not investment advice.

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
stay null — they are never invented.

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

On Docker startup the backend runs `python -m scripts.load_trusted_yearly`
automatically (see `2.backend/Dockerfile` CMD).

## Run with Docker

```bash
docker compose up --build
```

The trusted dataset is mounted (`./3.Datasets`) and loaded on boot. Paths inside
the container are set via `TRUSTED_DATASETS_DIR`, `TRUSTED_OUT_DIR`,
`TRUSTED_COMBINED_CSV` in `docker-compose.yml`.

## Local development

### Backend

```bash
cd 2.backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set DATABASE_URL and SECRET_KEY
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

## Environment variables

| Var | Purpose |
|---|---|
| `DATABASE_URL` | Postgres connection string |
| `SECRET_KEY` | JWT signing key. **Not committed.** If unset, a random per-process key is generated (JWTs reset on restart) — set it explicitly in production. |
| `TRUSTED_DATASETS_DIR` | Dir of trusted XLSX (default `3.Datasets/`) |
| `TRUSTED_OUT_DIR` | Output dir for generated CSVs (default `data/trusted/`) |
| `TRUSTED_COMBINED_CSV` | Combined CSV path used by the loader |

No real secrets are committed. `.env` is gitignored.

## What was removed / quarantined

Everything non-trusted is in [`unnecessary/`](unnecessary/README.md):

- **Finnhub** — removed entirely (API key assumed leaked).
- **News API / news page** — removed (not essential, was Finnhub-backed).
- **Synthetic generator, seeders, KAP scraper, xlsx-into-quarterly importer** — quarantined.
- **Old quarterly-CSV workflow** (`quarterly_fundamentals_2025.csv`, `load_trusted_fundamentals.py`) — retired in favor of the yearly XLSX pipeline.
- **Hardcoded secrets** — the `SECRET_KEY` and `NEWS_API_KEY` defaults are gone.

## Known limitations

- **Forecasting engine still reads the legacy `quarterly_fundamentals` /
  `winner_cohort_rows` tables.** The trusted yearly data now lives in
  `yearly_stocks`; wiring the scoring/forecasting engine onto it is the next
  integration step (the data layer is ready; the contract maps 1:1 to the
  features it needs). Until then, forecasting returns clear empty/insufficient
  results rather than fabricated ones.
- **No winner/target labels** ship with the trusted data. Supervised scoring
  must not be presented as trained until real labels are provided. No labels are
  generated or inferred.
- The dataset is **yearly**, not quarterly. Period selection is a year
  (2020–2025); year-over-year and multi-year comparisons use only data up to the
  selected year (no future-year leakage — enforced in `validate_trusted_data`).
```
