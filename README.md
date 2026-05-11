# FinanceIQ 
Forecasting and comparison platform for BIST stocks using 2020–2025 datasets and multi-model scoring.

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

Default entry route is ` /login `.

## Database Migrations (Alembic)

Apply latest schema:

```bash
cd 2.backend
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

## Data Sources (2020–2025)

Winner/stock input files live under `3.Datasets/`:

```
3.Datasets/
  2020stocks.xlsx
  2021stocks.xlsx
  2022stocks.xlsx
  2023stocks.xlsx
  2024stocks.xlsx
  2025stocks.xlsx
```

Notes:
- Each year can contain a different number of companies.
- UI selection should always be year-aware; a stock list should be sourced from the selected year.
- Missing values are handled with **median imputation**.

## Modeling Strategy (Score + Comparison)

The platform uses five models for forecasting and scoring:

1. ElasticNet
2. Random Forest Regressor
3. XGBoost
4. SARIMAX
5. Temporal Fusion Transformer (TFT)

### Single-Stock Scoring

Users can select one model to generate a score for a single stock. Output is based on trained model predictions and never synthetic or hard-coded values.

### Comparison Mode

When comparing multiple stocks, the system runs **all five models** and produces a combined ranking. If a stock does not have data for the requested year/quarter, it is excluded from comparison and the UI should surface a clear warning.

### Reliability & Generalization

To keep outputs reliable and avoid memorization:
- Use time-based train/validation splits.
- Report evaluation metrics for each model.
- Favor cross-validation or rolling-window evaluation where available.
- Avoid leaking future data into training features.

## Forecasting Flow

1. Login/Register from `/login`
2. Select year + upload winners (2020–2025 `.xlsx`)
3. Upload quarterly fundamentals CSV (per year/quarter)
4. Train model(s)
5. Predict rankings
6. Inspect details and explanations
7. Run rolling time-CV evaluation

## Required Quarterly Fundamentals CSV Columns

`stock_code, sector, period, net_income, equity, total_assets, revenue, gross_profit, ebitda, ocf, capex, total_debt, cash, ebit, interest_expense, inventory, receivables, net_working_capital, market_cap, book_value, enterprise_value, eps, growth_rate, current_assets, current_liabilities, dividend_per_share, price`

- `period` format must be `2020Q4`,`2021Q4`,`2022Q4`,`2023Q4`,`2024Q4`,`2025Q4`
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
- `rebuild_financial_pipeline.py` — full financial data rebuild
- `retrain_forecasting.py` — batch forecasting model retrain
- `incremental_retrain.py` — retrain only on new year data
- `pipeline_runner.py` — incremental retrain + time-CV evaluation

Airflow DAG template:
- `2.backend/airflow/dags/forecasting_retrain_dag.py`

## Infrastructure Scaffolding

Cloud starter configs/docs:
- `infra/aws/`
- `infra/azure/`
- `infra/gcp/`
- `docs/DEPLOYMENT.md`
