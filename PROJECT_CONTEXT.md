# PROJECT_CONTEXT.md — FinanceIQ

## What it is

FinanceIQ is a capstone project: a web-based forecasting and stock-scoring platform for BIST (Borsa Istanbul) equities. Users upload yearly winner cohort Excel files (2020–2025), upload quarterly fundamental CSVs, train sector-specific scoring models, generate stock rankings, and evaluate model stability via rolling time-based cross-validation.

## Goals

- Rank BIST stocks within a sector/year using real financial fundamentals (no synthetic data)
- Surface explainable scores — each stock's score traces back to weighted financial parameters
- Support multiple scoring "model types" (scoring, xgboost, arima, prophet, dbscan, gmm) on top of one unified parameter-scoring pipeline
- Provide rolling time-CV evaluation (rank stability + overlap@K) to validate model generalization
- Show news/AI insights, portfolio optimization suggestions, and data health monitoring

## Users

Investors (individual, corporate) and admins. Role stored on `User.role` (investor | admin). User profile includes `user_type`, `risk_level`, `investment_scope`, `sector_focus` — these modulate scoring output.

## Data scope

| File | Content |
|---|---|
| `3.Datasets/2020stocks.xlsx` … `2025stocks.xlsx` | Yearly BIST winner cohorts — price returns, sector, stock code |
| Quarterly fundamentals CSV | 28-column fundamentals per stock/period (uploaded by user) |

Missing values handled with median imputation at import time.

## Tech stack

| Layer | Tech |
|---|---|
| Frontend | React 18 + Vite, React Router v6, nginx in Docker |
| Backend | FastAPI 0.111, Python 3.12, Uvicorn |
| ORM / DB | SQLAlchemy 2.0, PostgreSQL 16-alpine, Alembic |
| ML / Data | scikit-learn, pandas, numpy, SHAP, openpyxl |
| Auth | JWT (python-jose), bcrypt/passlib, 1440-min tokens |
| Containerization | Docker Compose (3 services: db, backend, frontend) |

## Environments

| Service | Local port | Docker |
|---|---|---|
| Frontend | 5173 (dev) | 3000 → nginx:80 |
| Backend | 8000 | 8000 |
| DB | 5432 | 5432 (internal) |

## Key directories

```
1.frontend/src/pages/     — one file per page/route
1.frontend/src/components/ — shared UI (AppShell, ProtectedRoute, …)
2.backend/app/routers/    — one router per domain
2.backend/app/services/   — business logic
2.backend/app/models/     — SQLAlchemy ORM models
2.backend/app/schemas/    — Pydantic request/response schemas
2.backend/scripts/        — batch retrain + pipeline ops scripts
3.Datasets/               — xlsx winner cohort files (2020–2025)
```

## Auth flow

POST `/auth/login` → JWT → stored in localStorage → `ProtectedRoute` checks token before rendering any page. Account lockout after failed attempts (`failed_login_count`, `locked_until` columns).
