# FinanceIQ – Success DNA Forecasting Platform

Historically successful stocks (winner-only) based forecasting platform for BIST, with sector/year analysis and explainable rankings.

## Quick Start

### Requirements
- Docker + Docker Compose
- (Local dev) Python 3.12, Node.js 20+

### Run with Docker

```bash
cd Capstone_Code
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

Default entry route is now ` /login `.

## Database Migrations (Alembic)

Apply latest schema (forecasting, evaluations, onboarding fields, quarterly fundamentals):

```bash
cd backend
alembic upgrade head
```

## Local Development

### Backend

```bash
cd 2.backend
source .venv/bin/activate
pip install -r requirements.txt
echo "DATABASE_URL=postgresql://postgres:postgres@localhost:5432/capstone_db" > .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd 1.frontend
npm install
npm run dev
```

## Financial Health Scoring System

### Data Flow (Single Source of Truth)

```
CLEANED_Financial/ (.xlsx per company)
        ↓
QuarterlyFundamental  (imported via scripts/rebuild_financial_pipeline.py)
        ↓
ComputedMetric        (12 ratios: ROA, ROE, margins, liquidity, leverage, OCF)
        ↓
MetricTransition      (period-over-period changes)
        ↓
SectorBenchmark       (mean, std, median, p25, p75 per sector per period)
        ↓
SectorNormalizedFeature  (z-score + percentile rank per company per period)
        ↓
Scoring / Analysis    (rule_based or logistic_real_label mode)
```

### Rebuild the Full Pipeline

After importing or updating `CLEANED_Financial/` data, run:

```bash
cd 2.backend
python -m scripts.rebuild_financial_pipeline
```

This clears and regenerates all computed tables in the correct order, then prints a validation summary (company count, period count, missing field counts, duplicate check).

### Scoring Modes

| Mode | Description |
|---|---|
| `rule_based` | Weighted rule scoring (0–100). Missing metrics are excluded from available weight — never zeroed. |
| `logistic` | Logistic regression trained on real next-period net income growth labels. Uses time-based 80/20 train/test split by period. Prints accuracy, precision, recall, F1, AUC, and confusion matrix to server logs. |

### Explanation Output (`rich_explanation`)

Every score response includes a `rich_explanation` block with:
- `data_completeness_label` — e.g. `"9 / 12 metrics"` (human-readable)
- `excluded_metrics` — list of metric names excluded due to missing data
- `method_note` — `"This score is a rule-based financial health indicator."` or `"This probability is generated using a logistic regression model."`
- `family_performance` — grouped by Kârlılık, Likidite, Kaldıraç, Nakit Akışı
- `strongest_drivers` / `weakest_drivers` — top/bottom 3 metric names
- `counterfactuals` — "if X had been Y, the score would reach Strong band" hints

### Compare Endpoint

`POST /scoring/compare` returns both `items` (ranked results) and `warnings` (companies excluded due to missing data for the requested period), e.g.:

```json
{
  "items": [...],
  "warnings": ["AKSEN has no data for 2022Q2 and was excluded."]
}
```

### Key API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/companies/{id}/score` | Score a company (rule_based or logistic) |
| POST | `/scoring/compare` | Compare multiple companies, returns ranked items + warnings |
| GET | `/score-runs/{run_id}` | Retrieve a stored score run with full detail |
| GET | `/users/me/score-runs` | List my recent score runs |

## Core Forecasting Flow

1. Login/Register from `/login`
2. Import winner files (`2023/2024/2025 HİSSELER.xlsx`) from Forecasting page
3. Upload **quarterly fundamentals CSV** (`2023Q1` to `2025Q4`) from Forecasting page
4. Train model (`/train-model`)
5. Predict rankings (`/predict`)
6. Inspect details (`/get-stock-detail`, `/predict/trends`, `/predict/heatmap`)
7. Run rolling time-CV (`/predict/evaluate`)

## Exact Ratio Mode (No Proxies)

Forecasting now uses uploaded quarterly fundamentals to compute exact ratios (ROE, ROA, margins, leverage, valuation, liquidity, etc.).

If quarterly fundamentals are missing for selected sector/year (Q4), forecasting returns validation errors.
Note: The `@CLEANED_Financial/` directory contains the main and correct data for parameters. Ensure that the uploaded quarterly fundamentals CSV matches the structure and data quality of these files.

## Required Quarterly Fundamentals CSV Columns

`stock_code, sector, period, net_income, equity, total_assets, revenue, gross_profit, ebitda, ocf, capex, total_debt, cash, ebit, interest_expense, inventory, receivables, net_working_capital, market_cap, book_value, enterprise_value, eps, growth_rate, current_assets, current_liabilities, dividend_per_share, price`

- `period` format must be `2023Q1` .. `2025Q4`
- Upload endpoint: `POST /fundamentals/upload-csv`

## Key Pages

| Page | Route | Purpose |
|---|---|---|
| Login | `/login` | Authentication |
| Dashboard | `/dashboard` | Overall platform view |
| Forecasting | `/forecasting` | Upload, train, predict, evaluate |
| Forecast Detail | `/forecasting/detail` | Trend/importance/heatmap charts |
| News | `/news` | Market updates + AI insight |
| Validation Lab | `/validation` | Model validation tooling |
| Data Health | `/data-health` | Ingestion/quality monitoring |

## Forecasting API (Main)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/upload-data` | Import yearly winner Excel preset |
| POST | `/fundamentals/upload-csv` | Upload quarterly fundamentals |
| POST | `/train-model` | Train sector/year parameter ranking |
| POST | `/predict` | Generate stock rankings |
| GET | `/get-parameters` | Ranked solid parameters |
| GET | `/parameters/catalog` | Parameter catalog (category/formula/purpose) |
| GET | `/get-stock-detail` | Per-stock score detail |
| GET | `/get-explanation` | Explainability payload |
| GET | `/predict/history` | Prediction run history |
| POST | `/predict/evaluate` | Rolling window time-CV report |
| GET | `/predict/trends` | Stock yearly trend series |
| GET | `/predict/heatmap` | Sector feature heatmap |
| POST | `/get-portfolio-analysis` | Corporate portfolio suggestions |
| GET | `/news/updates` | News updates + AI insight |

## Continuous Learning Ops

Scripts are under `2.backend/scripts/`:
- `rebuild_financial_pipeline.py` — **full financial data rebuild** (clear → import → metrics → transitions → sector → normalize → validate)
- `retrain_forecasting.py` — batch forecasting model retrain
- `incremental_retrain.py` — retrain only on new year data
- `pipeline_runner.py` — incremental retrain + time-CV evaluation

Airflow DAG template:
- `backend/airflow/dags/forecasting_retrain_dag.py`

## Infrastructure Scaffolding

Cloud starter configs/docs:
- `infra/aws/`
- `infra/azure/`
- `infra/gcp/`
- `docs/DEPLOYMENT.md`