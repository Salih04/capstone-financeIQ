import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.database import engine
from app.models import *  # noqa: F401,F403 – registers all models with Base
from app.database import Base
from app.routers import auth, companies, financials, scoring
from app.routers import ingestion, admin, reports
from app.routers import validation, labeling

# Wait for DB then create tables
for _i in range(15):
    try:
        with engine.connect() as _c:
            _c.execute(text("SELECT 1"))
        break
    except OperationalError:
        time.sleep(2)

Base.metadata.create_all(bind=engine)

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


@app.get("/health")
def health():
    return {"status": "ok", "version": "3.0.0"}


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


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}

