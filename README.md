# FinanceIQ

An honest, leakage-safe **T→T+1 equity-research system** for 40 public BIST companies
(2020–2025), with an expanded 81-ticker internal training universe: a validated modeling dataset, a BIST100 benchmark, a free-data
valuation reconstruction, an explainable hybrid research agent, and the Fable 5
"Research Terminal" frontend. No paid APIs, no synthetic/fabricated data, no scrapers.

**Maturity:** Completed research project

**Live research interface:** [capstone-finance-iq.vercel.app](https://capstone-finance-iq.vercel.app/)

**Portfolio case study:** [salih04.github.io/projects.html](https://salih04.github.io/projects.html)

> **Capstone status: complete.** The pipeline is rigorous and transparent. The
> honest finding is that the model still shows **no reliable predictive edge** after
> expanding internal training to 81 tickers (walk-forward Spearman remains weak/unstable).
> That is a defensible negative result,
> not a bug. See `TASK_STATE.md`.

**Project resumption:** [Research Consolidation](docs/CONSOLIDATION.md) is the best entry point for the current scientific state, established and unestablished claims, DIM/ROBUST context, open methodological questions, and returning after an interruption.

**Validated features: 40** balance-sheet + growth (reference), real per-year
income/profitability (corrected yearly: revenue, margins, ROE, ROA, …), and
free-derived valuation (market_cap, enterprise_value, pe_ratio, pb_ratio,
ev_ebitda), plus leakage-safe year-T price/benchmark features. Old frozen-snapshot
valuation and price/return leakage are rejected.

## Architecture

```
React (frontend) ──HTTP──▶ FastAPI (backend) ──SQLAlchemy──▶ PostgreSQL
```

Three Docker services: `db`, `backend`, `frontend`. The backend converts the
trusted XLSX files to CSV and loads them into Postgres on startup.

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

Entry route: `/login`.

## Fable 5 frontend

FinanceIQ is no longer a generic capstone dashboard. The frontend is a dark
research-terminal interface for BIST signal analysis: Bloomberg meets Linear,
with the restraint of a scientific instrument. It uses deep ink surfaces, subtle
grain/scanline texture, muted emerald for signal/positive states, oxidized
copper/amber for weak or warning states, monospace data typography, tracked caps
section labels, persistent right-side Signal Readout panels where applicable,
and bottom caveat strips. The core product stance is: **"A weak signal, reported
honestly."** Walk-forward IC ≈ 0 is shown as a core finding, not hidden.

Implemented research surfaces:

| Route | Concept | What it documents in the UI |
|---|---|---|
| `/dashboard` | Weak signal overview | Particle/noise field, BIST100 vs model comparison, feature intake, data quality, visible IC ≈ 0 signal-strength indicator. |
| `/research-agent` | Research query instrument | "Query the signal. Distrust the answer."; intent selectors, restored free-text query, `POST /research/ask` preserved, instrument-style answer blocks, hybrid weights and AI/fallback status. |
| `/research/companies` and `/companies` | Research map | "The universe, laid flat."; research score x-axis, coverage y-axis, sector-colored ticker nodes, search/filter dimming, map/table mode, real API first with demo fallback only. |
| `/experiments` | Seismograph | Walk-forward folds around zero, equal-weight baseline shown honestly where it leads, flat IC trace treated as the finding, `researchApi.experiments()` preserved with demo fallback only. |
| `/research` | Dissection table | Score Explorer route; composite score unfolds into feature/category detail; `/research/years`, `/research/scores`, `/research/company` behavior preserved with demo fallback only. |
| `/data-quality` | Specimen archive | Accepted/rejected feature specimens, `LEAKAGE`/`FROZEN`/`ALL-NULL` stamps, `dataQuality()`, `summary()`, `frozenEvidence()` calls, progressive hydration to avoid false zero states. |
| `/benchmark` | Tide chart | BIST100 vs model top basket as filled water bodies, 2022 +196% event on sign-preserving log scale, small IC markers, `researchApi.benchmark()` preserved. |
| `/forecasting` | Signal tuner | Experimental pipeline using `GET /forecasting/options`, `POST /forecasting/train`, `POST /forecasting/run`, `GET /forecasting/explain/:ticker`; feature weights as a frequency spectrum, ranked results from noise, inference-only rows pulse amber. |

Mock/demo data is fallback only where pages explicitly provide it; real API
behavior is preserved. All copy is research support only and not investment
advice.

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

### Reproducibility quickstart

From the repository root, create a registered run, reproduce its manifest in an
isolated temporary directory, then check the versioned claim guardrails:

```bash
make research
make research-verify-run
make claims-lint
```

To verify an older registered run, set
`RESEARCH_MANIFEST=experiments/results/runs/<run>/manifest.json` on the second
command. See [METHODOLOGY.md — Reproducibility and run provenance](METHODOLOGY.md#reproducibility-and-run-provenance)
for the manifest contents, checksum rules, and environment-sensitive comparison
policy.

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
claims price/return certainty, gives investment advice, or fabricates facts.

Hybrid score (weights configurable via env):
```
final_research_score = 0.65*ml_score + 0.20*confidence_score + 0.15*llm_research_score
```
Components are always returned separately; `ml_score` may be null (partial score).

Endpoints (`/research/summary`, `/research/company/{ticker}`,
`/research/company/{ticker}/score`, `/research/model-diagnostics`,
`/research/data-quality`, `/research/ai-status`, `POST /research/ask`).
Frontend page: `/research-agent`; legacy `/ai-search` redirects there. No
`/ai-research-assistant` route is present in the current route map.

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

The yearly XLSX set in `data/raw/yearly_xlsx/` (reference/bootstrap, see warning above):

```
data/raw/yearly_xlsx/2020stocks.xlsx … 2025stocks.xlsx   (40 BIST companies × 54 columns)
```

These are converted, deterministically and without fabrication, to:

```
data/trusted/2020stocks.csv … 2025stocks.csv   one clean CSV per year
data/trusted/stocks_2020_2025.csv              combined, with a `year` column
```

and loaded into the `yearly_stocks` Postgres table (one row per ticker-year).

The data contract lives in [`backend/app/trusted_data.py`](backend/app/trusted_data.py):
column map, required/optional columns, percent vs. monetary fields, safe numeric
parsing (BOM, thousands separators, negatives), and validation. Missing values
stay null they are never invented.

### Pipeline commands

```bash
cd backend

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
`backend/scripts/start_backend.sh`).

## Run with Docker

```bash
export RESEARCH_LLM_PROVIDER=openrouter
export RESEARCH_LLM_BASE_URL=https://openrouter.ai/api/v1/chat/completions
export RESEARCH_LLM_MODEL=openai/gpt-oss-120b:free
export OPENAI_API_KEY=your-openrouter-key
docker compose up --build
```

The trusted dataset is mounted (`./data/raw/yearly_xlsx`) and loaded on boot. Paths inside
the container are set via `TRUSTED_DATASETS_DIR`, `TRUSTED_OUT_DIR`,
`TRUSTED_COMBINED_CSV` in `docker-compose.yml`.

## Deploy backend on Render

This repo ships a `render.yaml` Blueprint using the **Docker** runtime with the
repo root as build context (the `backend/Dockerfile` copies `data/`,
`experiments/`, and `research_agent_training/` from the repo root). Point Render
at the repo and it reads `render.yaml`, or configure a Docker Web Service manually:

```text
Root Directory:                 (empty / repo root)
Dockerfile Path:                backend/Dockerfile
Docker Build Context Directory: .
Docker Command:                 (blank — Dockerfile CMD honors $PORT)
```

Do **not** set `Root Directory: backend` for the Docker strategy — it produces
`backend/backend/Dockerfile` and a build context that cannot see `data/`. The
Dockerfile already sets in-container data paths (`RESEARCH_REPO_ROOT=/app`,
`TRUSTED_*=/app/data/...`). Set `DATABASE_URL`, `SECRET_KEY`, and optional
`SUPABASE_JWT_SECRET` in Render.

Backend research/forecasting-CSV endpoints are intentionally public for the demo;
verify data shipped with `GET /research/runtime-status`.

See [`docs/RENDER_DEPLOY.md`](docs/RENDER_DEPLOY.md).

## Deploy frontend on Vercel

Vercel deploys the React frontend only. The FastAPI backend must be running on a
public URL (Railway, Render, Fly.io, a VPS, or another host). Authentication is
handled by Supabase Auth in the browser; backend endpoints can also accept
Supabase JWTs when `SUPABASE_JWT_SECRET` is configured.

Recommended Vercel project settings:

```text
Root Directory: frontend
Install Command: npm install
Build Command: npm run build
Output Directory: dist
```

If importing the repository root instead, the root `vercel.json` already points
Vercel at `frontend/` with `npm install --prefix frontend`,
`npm run build --prefix frontend`, and `frontend/dist`.

Set these Vercel environment variables, then redeploy:

```bash
VITE_API_URL=https://your-backend-domain
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-or-publishable-key
VITE_SUPABASE_AUTH_REDIRECT_URL=https://your-frontend-domain/auth/callback
```

Backend environment must include:

```bash
OPENAI_API_KEY=your-openrouter-key
RESEARCH_LLM_PROVIDER=openrouter
RESEARCH_LLM_MODEL=openai/gpt-oss-120b:free
SUPABASE_JWT_SECRET=your-supabase-jwt-secret   # optional but needed for protected API calls
```

Quick check:

```bash
curl https://your-backend-domain/health
```

## Local development

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set DATABASE_URL and SECRET_KEY
alembic upgrade head
python -m scripts.load_trusted_yearly
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local    # set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY
npm run dev
```

### Supabase Auth

Frontend auth uses Supabase session persistence, email/password signup, Google
OAuth, email confirmation redirects, and password recovery. Configure:

- Supabase project URL and anon/publishable key in `frontend/.env.local`.
- Email provider enabled in Authentication → Providers → Email.
- Google provider enabled in Authentication → Providers → Google with Google
  OAuth client ID/secret.
- Redirect URLs in Authentication → URL Configuration:
  `http://localhost:5173/auth/callback`,
  `http://localhost:3000/auth/callback`, and production frontend callback URL.
- Production Site URL must be the deployed frontend URL, for example
  `https://your-frontend-domain`.
- Production Redirect URL must be
  `https://your-frontend-domain/auth/callback`.
- After changing Supabase URL settings, send fresh confirmation/recovery emails;
  old localhost confirmation links should not be reused.
- Optional backend JWT compatibility: set `SUPABASE_JWT_SECRET` from Supabase
  Project Settings → API → JWT Secret. If your project uses asymmetric signing
  keys, keep frontend-only auth or add JWKS verification before protecting APIs.

See [`docs/SUPABASE_AUTH.md`](docs/SUPABASE_AUTH.md).

### Database migrations (Alembic)

```bash
cd backend
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
| `VITE_SUPABASE_URL` | Supabase project URL for frontend auth |
| `VITE_SUPABASE_ANON_KEY` | Supabase browser-safe anon/publishable key |
| `VITE_SUPABASE_AUTH_REDIRECT_URL` | Optional explicit frontend auth callback URL |
| `SUPABASE_JWT_SECRET` | Optional backend verifier secret for Supabase JWTs; never expose in frontend |
| `RESEARCH_LLM_PROVIDER` | `openrouter`, `lmstudio`, `ollama`, or `none` |
| `RESEARCH_LLM_MODEL` | Chat model id (default `openai/gpt-oss-120b:free` for OpenRouter) |
| `TRUSTED_DATASETS_DIR` | Dir of trusted XLSX (default `data/raw/yearly_xlsx/`) |
| `TRUSTED_OUT_DIR` | Output dir for generated CSVs (default `data/trusted/`) |
| `TRUSTED_COMBINED_CSV` | Combined CSV path used by the loader |
| `RUN_DB_MIGRATIONS` | Run Alembic on Docker startup (`1` default, set `0` to skip) |
| `LOAD_TRUSTED_DATA` | Load trusted yearly data on Docker startup (`1` default, set `0` to skip) |
| `PUBLIC_DEMO_MODE` | `true` (default) = open read-only demo; `false` = private (auth required) |
| `REQUIRE_APPROVED_USER` | In private mode, require verified email in `APPROVED_EMAILS` |
| `APPROVED_EMAILS` | Comma-separated allowlist (case-insensitive); empty + require = deny all |
| `ENABLE_PUBLIC_DOCS` | `true` (default) serves `/docs` + `/openapi.json`; `false` disables |
| `RATE_LIMIT_ENABLED` / `RATE_LIMIT_REQUESTS_PER_MINUTE` | In-memory throttle on expensive endpoints (default off / 60) |
| `CORS_ALLOW_ORIGINS` | Comma-separated allowed origins; wildcard auto-disables credentials |
| `VITE_ENABLE_GOOGLE_AUTH` / `VITE_ENABLE_SIGNUP` | Frontend: show Google/signup UI (default off) |
| `VITE_REQUIRE_APPROVED_USER` / `VITE_APPROVED_EMAILS` | Frontend approval gate (UX mirror of backend) |

No real secrets are committed. `.env` is gitignored.

### Private production lockdown

Defaults keep the open demo so nothing breaks on deploy or in dev. To lock the
deployment down to manually-created, approved users:

```bash
# Render (backend)
PUBLIC_DEMO_MODE=false
REQUIRE_APPROVED_USER=true
APPROVED_EMAILS=owner@example.com,teammate@example.com
SUPABASE_URL=https://<project-ref>.supabase.co   # REQUIRED in private mode (JWKS verification of Supabase Signing Keys)
# SUPABASE_JWT_SECRET=<legacy HS256 secret>       # only if your project still issues HS256 tokens
ENABLE_PUBLIC_DOCS=false
RATE_LIMIT_ENABLED=true
CORS_ALLOW_ORIGINS=https://capstone-finance-iq.vercel.app

# Vercel (frontend)
VITE_ENABLE_GOOGLE_AUTH=false
VITE_ENABLE_SIGNUP=false
VITE_REQUIRE_APPROVED_USER=true
VITE_APPROVED_EMAILS=owner@example.com,teammate@example.com
```

Supabase dashboard (owner-managed): OAuth/Google OFF, email signup OFF, users
created manually. The backend is the real boundary; frontend flags are UX only.
See [`SECURITY.md`](SECURITY.md).

## What was removed / quarantined

The quarantined integrations were removed from the repository entirely; do not
reintroduce them:

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
- **Forecasting remains experimental.** The current `/forecasting` page uses the
  CSV-backed options/train/run/explain pipeline and presents inference-only rows
  as research support only. Legacy DB endpoints still exist, but the frontend
  path does not depend on populated DB forecasting tables.
- Dataset is **yearly**; the quarterly Fintables exports are a frozen snapshot and
  are excluded (see `make inspect-quarterly`). No future-year leakage (enforced in
  `validate.py`).
