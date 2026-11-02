"""Audit A07: shared financial records are writable by admins only.

Every write endpoint below replaces rows that all users read (statements,
computed ratios, quarterly fundamentals, cohort presets, sector rankings).
Synthetic tickers only; no raw data files are read.
"""
from __future__ import annotations

import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ["RESEARCH_LLM_PROVIDER"] = "none"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models.company import Company  # noqa: E402
from app.models.financial import FinancialStatement  # noqa: E402
from app.models.forecasting import QuarterlyFundamental  # noqa: E402
from app.models.user import User  # noqa: E402

_FUNDAMENTAL_HEADER = (
    "ticker,period,sector,revenue,net_income,total_assets,total_equity,total_liabilities,"
    "current_assets,current_liabilities,cash,operating_cash_flow,operating_income,"
    "gross_profit,inventory\n"
)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _demo_mode_does_not_relax_writes():
    saved = settings.PUBLIC_DEMO_MODE
    settings.PUBLIC_DEMO_MODE = True
    yield
    settings.PUBLIC_DEMO_MODE = saved


def _token_for(role: str, *, active: bool = True) -> dict:
    db = SessionLocal()
    try:
        user = User(email=f"a07-{role}-{uuid.uuid4().hex[:8]}@example.org",
                    password_hash=hash_password("Passw0rd!"), role=role, is_active=active)
        db.add(user)
        db.commit()
        return {"Authorization": f"Bearer {create_access_token({'sub': str(user.id)})}"}
    finally:
        db.close()


@pytest.fixture()
def seeded_statement():
    ticker = f"A7{uuid.uuid4().hex[:6].upper()}"
    db = SessionLocal()
    try:
        company = Company(ticker=ticker, company_name="Synthetic A07", sector="Industrial")
        db.add(company)
        db.flush()
        db.add(FinancialStatement(company_id=company.id, period="2023/12", revenue=100.0,
                                  net_income=10.0, total_assets=200.0, total_equity=80.0))
        db.commit()
        return ticker, company.id
    finally:
        db.close()


def _stored_revenue(company_id: int) -> float | None:
    db = SessionLocal()
    try:
        return (db.query(FinancialStatement)
                .filter(FinancialStatement.company_id == company_id,
                        FinancialStatement.period == "2023/12").one().revenue)
    finally:
        db.close()


def _statement_csv(ticker: str, revenue: str = "1") -> bytes:
    return (f"ticker,period,revenue,net_income,total_assets,total_equity\n"
            f"{ticker},2023/12,{revenue},1,1,1\n").encode()


def _fundamental_csv(ticker: str) -> bytes:
    return (_FUNDAMENTAL_HEADER + f"{ticker},2023Q4,A07Sector,1,1,1,1,1,1,1,1,1,1,1,1\n").encode()


@pytest.mark.parametrize("role", ["investor", "analyst"])
def test_a07_non_admin_cannot_overwrite_financial_statements(client, seeded_statement, role):
    ticker, company_id = seeded_statement
    r = client.post("/financials/import-csv", headers=_token_for(role),
                    files={"file": ("x.csv", _statement_csv(ticker), "text/csv")})
    assert r.status_code == 403
    assert _stored_revenue(company_id) == 100.0


@pytest.mark.parametrize("role", ["investor", "analyst"])
def test_a07_non_admin_cannot_run_ingestion_import(client, seeded_statement, role):
    ticker, company_id = seeded_statement
    r = client.post("/ingestion/import/csv", headers=_token_for(role),
                    files={"file": ("x.csv", _statement_csv(ticker), "text/csv")})
    assert r.status_code == 403
    assert _stored_revenue(company_id) == 100.0


@pytest.mark.parametrize("role", ["investor", "analyst"])
def test_a07_non_admin_cannot_upload_quarterly_fundamentals(client, role):
    ticker = f"A7F{uuid.uuid4().hex[:5].upper()}"
    r = client.post("/fundamentals/upload-csv", headers=_token_for(role),
                    files={"file": ("x.csv", _fundamental_csv(ticker), "text/csv")})
    assert r.status_code == 403
    db = SessionLocal()
    try:
        assert db.query(QuarterlyFundamental).filter(QuarterlyFundamental.stock_code == ticker).count() == 0
    finally:
        db.close()


@pytest.mark.parametrize("role", ["investor", "analyst"])
def test_a07_non_admin_cannot_import_cohort_preset(client, role, tmp_path, monkeypatch):
    (tmp_path / "data").mkdir()  # empty synthetic repo root: no preset files are listed or read
    monkeypatch.setenv("RESEARCH_REPO_ROOT", str(tmp_path))
    r = client.post("/upload-data", headers=_token_for(role), json={"file_name": "2023 synthetic.xlsx"})
    assert r.status_code == 403


@pytest.mark.parametrize("role", ["investor", "analyst"])
def test_a07_non_admin_cannot_replace_sector_rankings(client, role):
    r = client.post("/train-model", headers=_token_for(role),
                    json={"year": 2023, "sector": "A07-NoSuchSector", "top_n_parameters": 3})
    assert r.status_code == 403


@pytest.mark.parametrize("path", ["/financials/import-csv", "/ingestion/import/csv", "/fundamentals/upload-csv"])
def test_a07_anonymous_upload_rejected_even_in_demo_mode(client, path):
    r = client.post(path, files={"file": ("x.csv", b"ticker,period\n", "text/csv")})
    assert r.status_code in (401, 403)


def test_a07_inactive_admin_cannot_write(client, seeded_statement):
    ticker, company_id = seeded_statement
    r = client.post("/financials/import-csv", headers=_token_for("admin", active=False),
                    files={"file": ("x.csv", _statement_csv(ticker), "text/csv")})
    assert r.status_code == 403
    assert _stored_revenue(company_id) == 100.0


def test_a07_admin_can_still_import_statements(client, seeded_statement):
    ticker, company_id = seeded_statement
    r = client.post("/financials/import-csv", headers=_token_for("admin"),
                    files={"file": ("x.csv", _statement_csv(ticker, revenue="150"), "text/csv")})
    assert r.status_code == 200
    assert r.json()["updated"] == 1
    assert _stored_revenue(company_id) == 150.0


def test_a07_admin_can_still_run_ingestion(client, seeded_statement):
    ticker, company_id = seeded_statement
    r = client.post("/ingestion/import/csv", headers=_token_for("admin"),
                    files={"file": ("x.csv", _statement_csv(ticker, revenue="175"), "text/csv")})
    assert r.status_code == 200
    assert _stored_revenue(company_id) == 175.0


def test_a07_admin_can_still_upload_fundamentals(client):
    ticker = f"A7F{uuid.uuid4().hex[:5].upper()}"
    r = client.post("/fundamentals/upload-csv", headers=_token_for("admin"),
                    files={"file": ("x.csv", _fundamental_csv(ticker), "text/csv")})
    assert r.status_code == 200


def test_a07_admin_reaches_train_model_handler(client):
    r = client.post("/train-model", headers=_token_for("admin"),
                    json={"year": 2023, "sector": "A07-NoSuchSector", "top_n_parameters": 3})
    assert r.status_code == 422  # passed the role gate; no data for this sector
