# PROJECT_CONTEXT.md — FinanceIQ

## What it is

FinanceIQ is a capstone project: an honest, leakage-safe **T→T+1 equity-research
system** for 40 BIST (Borsa Istanbul) companies, 2020–2025. It builds a validated
modeling dataset (year-T features → year-(T+1) realized return), a BIST100 benchmark,
a free-data valuation reconstruction, walk-forward experiments, an explainable hybrid
research agent (OpenRouter by default, local providers optional), and a "Research Terminal" frontend. A legacy
sector-forecasting tool remains available at `/forecasting`.

**Status: complete.** Honest finding: no reliable predictive edge on ~40 stocks/year
— a rigorous pipeline + transparent negative result, not alpha. See `TASK_STATE.md`.

## Goals

- Build a leakage-safe T→T+1 dataset from real data only (no synthetic, no fabrication)
- Reconstruct missing valuation (market_cap, P/E, P/B, EV, EV/EBITDA) from FREE sources
  (Yahoo year-end price × manual shares × validated financials) instead of paid APIs
- Evaluate honestly via walk-forward CV vs a simple baseline (report weak signal as-is)
- Provide explainable, bounded research support — never investment advice
- Keep every accepted/rejected column traceable to its source and reason

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
