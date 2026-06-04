import time
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.database import engine
from app.models import *  # noqa: F401,F403 – registers all models with Base
from app.database import Base
from app.routers import auth, companies, financials, scoring
from app.routers import ingestion, admin, reports
from app.routers import validation, labeling
from app.routers import forecasting
from app.routers import users
from app.routers import fundamentals
from app.routers import research
from pathlib import Path

# Wait for DB then create tables
for _i in range(15):
    try:
        with engine.connect() as _c:
            _c.execute(text("SELECT 1"))
        break
    except OperationalError:
        time.sleep(2)

Base.metadata.create_all(bind=engine)


def _ensure_backward_compatible_columns() -> None:
    """
    Hotfix for existing DBs created before new onboarding fields.
    We still keep Alembic as the primary migration path, but this prevents
    login/register from breaking on older schemas.
    """
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS user_type VARCHAR(50) DEFAULT 'individual'"))
            conn.execute(text("ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20) DEFAULT 'medium'"))
            conn.execute(text("ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS investment_scope DOUBLE PRECISION"))
            conn.execute(text("ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS sector_focus VARCHAR(200)"))
    except Exception:
        # Some test/dev DBs (e.g., sqlite) do not support this syntax.
        pass


_ensure_backward_compatible_columns()

app = FastAPI(
    title="Stock Scoring V3 API",
    version="3.0.0",
    description="Capstone – Stock Scoring System V3: Model Governance · Explainability · Validation Lab · Labeling Lab · Data Health",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(financials.router)
app.include_router(scoring.router)
app.include_router(ingestion.router)
app.include_router(admin.router)
app.include_router(reports.router)
app.include_router(validation.router)
app.include_router(labeling.router)
app.include_router(forecasting.router)
app.include_router(users.router)
app.include_router(fundamentals.router)
app.include_router(research.router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "3.0.0"}


@app.get("/fundamentals/template")
def fundamentals_template():
    p = Path(__file__).resolve().parents[1] / "templates" / "quarterly_fundamentals_template.csv"
    return FileResponse(path=str(p), media_type="text/csv", filename="quarterly_fundamentals_template.csv")
