"""Audit A06/A07/A08 against a real PostgreSQL schema.

SQLite stores NaN as NULL, so it cannot show NaN persistence; PostgreSQL keeps
'NaN' and '+/-Infinity' in double precision columns. These tests run only when
FIQ_TEST_POSTGRES_URL points at a disposable database already migrated with
``alembic upgrade head``; otherwise they are skipped (and must be reported as
not run). Synthetic rows only.
"""
from __future__ import annotations

import math
import os
import time
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ["RESEARCH_LLM_PROVIDER"] = "none"

import pytest  # noqa: E402

_PG_URL = os.environ.get("FIQ_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not _PG_URL, reason="FIQ_TEST_POSTGRES_URL not set; PostgreSQL checks not run")

from fastapi.testclient import TestClient  # noqa: E402
import jwt  # noqa: E402
from sqlalchemy import create_engine, inspect, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.config import settings  # noqa: E402
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.company import Company  # noqa: E402
from app.models.financial import FinancialStatement  # noqa: E402
from app.models.user import User  # noqa: E402

_SUPABASE_SECRET = "postgres-integrity-test-secret"


@pytest.fixture(scope="module")
def pg_session_factory():
    engine = create_engine(_PG_URL)
    if not engine.url.get_backend_name().startswith("postgresql"):
        pytest.fail("FIQ_TEST_POSTGRES_URL must be a PostgreSQL URL")
    tables = set(inspect(engine).get_table_names())
    if not {"users", "financial_statements", "computed_metrics", "quarterly_fundamentals"} <= tables:
        pytest.fail("PostgreSQL schema missing: run `alembic upgrade head` against FIQ_TEST_POSTGRES_URL")
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield factory
    engine.dispose()


@pytest.fixture(scope="module")
def client(pg_session_factory):
    def _pg_db():
        db = pg_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _pg_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(autouse=True)
def _supabase_secret():
    saved = settings.SUPABASE_JWT_SECRET
    settings.SUPABASE_JWT_SECRET = _SUPABASE_SECRET
    yield
    settings.SUPABASE_JWT_SECRET = saved


def _user(factory, role: str, *, active: bool = True) -> tuple[int, str]:
    db = factory()
    try:
        email = f"pg-{role}-{uuid.uuid4().hex[:8]}@example.org"
        user = User(email=email, password_hash=hash_password("Passw0rd!"), role=role, is_active=active)
        db.add(user)
        db.commit()
        return user.id, email
    finally:
        db.close()


def _headers(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token({'sub': str(user_id)})}"}


def _company(factory, *, revenue: float | None = None) -> tuple[str, int]:
    db = factory()
    try:
        ticker = f"PG{uuid.uuid4().hex[:6].upper()}"
        company = Company(ticker=ticker, company_name="Synthetic PG", sector="Industrial", sector_code="PGSYN")
        db.add(company)
        db.flush()
        if revenue is not None:
            db.add(FinancialStatement(company_id=company.id, period="2023/12", revenue=revenue))
        db.commit()
        return ticker, company.id
    finally:
        db.close()


def _non_finite_cells(factory, table: str, key: str, value) -> int:
    """Count NaN/+-Infinity cells in every double precision column of matching rows."""
    db = factory()
    try:
        cols = [c["name"] for c in inspect(db.get_bind()).get_columns(table)
                if c["type"].__class__.__name__ in ("DOUBLE_PRECISION", "FLOAT", "Float")]
        assert cols, table
        checks = " + ".join(
            f"(CASE WHEN {c} IN ('NaN'::float8, 'Infinity'::float8, '-Infinity'::float8) THEN 1 ELSE 0 END)"
            for c in cols)
        return db.execute(text(f"SELECT COALESCE(SUM({checks}), 0) FROM {table} WHERE {key} = :v"),
                          {"v": value}).scalar_one()
    finally:
        db.close()


def test_pg_control_postgres_really_keeps_nan_and_infinity(pg_session_factory):
    """Negative control: without coercion PostgreSQL stores NaN/Infinity verbatim."""
    _, company_id = _company(pg_session_factory)
    db = pg_session_factory()
    try:
        db.add(FinancialStatement(company_id=company_id, period="ctrl", revenue=float("nan"),
                                  net_income=float("inf")))
        db.commit()
        row = db.execute(text("SELECT revenue, net_income FROM financial_statements "
                              "WHERE company_id = :c AND period = 'ctrl'"), {"c": company_id}).one()
        assert math.isnan(row.revenue) and math.isinf(row.net_income)
    finally:
        db.close()
    assert _non_finite_cells(pg_session_factory, "financial_statements", "company_id", company_id) == 2


def test_pg_financials_import_persists_null_not_nan(client, pg_session_factory):
    admin_id, _ = _user(pg_session_factory, "admin")
    ticker, company_id = _company(pg_session_factory)
    csv = ("ticker,period,revenue,net_income,total_assets,total_equity,total_liabilities,"
           "current_assets,current_liabilities,cash\n"
           f"{ticker},2023/12,,inf,nan,-inf,1e999,500,250,50\n").encode()
    r = client.post("/financials/import-csv", headers=_headers(admin_id),
                    files={"file": ("x.csv", csv, "text/csv")})
    assert r.status_code == 200, r.text
    db = pg_session_factory()
    try:
        row = db.execute(text("SELECT revenue, net_income, total_assets, total_equity, total_liabilities, "
                              "current_assets FROM financial_statements WHERE company_id = :c"),
                         {"c": company_id}).one()
        assert row[:5] == (None, None, None, None, None)
        assert row.current_assets == 500.0
        metric = db.execute(text("SELECT roa, current_ratio, quick_ratio FROM computed_metrics "
                                 "WHERE company_id = :c"), {"c": company_id}).one()
        assert metric.roa is None and metric.quick_ratio is None and metric.current_ratio == 2.0
    finally:
        db.close()
    assert _non_finite_cells(pg_session_factory, "financial_statements", "company_id", company_id) == 0
    assert _non_finite_cells(pg_session_factory, "computed_metrics", "company_id", company_id) == 0


def test_pg_ingestion_import_persists_null_and_completes(client, pg_session_factory):
    admin_id, _ = _user(pg_session_factory, "admin")
    ticker, company_id = _company(pg_session_factory)
    csv = ("ticker,period,revenue,net_income,total_assets,total_equity,current_assets,current_liabilities\n"
           f"{ticker},2023/12,Infinity,10,-Infinity,NaN,500,250\n").encode()
    r = client.post("/ingestion/import/csv", headers=_headers(admin_id),
                    files={"file": ("x.csv", csv, "text/csv")})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "success"
    assert _non_finite_cells(pg_session_factory, "financial_statements", "company_id", company_id) == 0
    assert _non_finite_cells(pg_session_factory, "computed_metrics", "company_id", company_id) == 0


def test_pg_fundamentals_upload_persists_null_for_blank_cells(client, pg_session_factory):
    admin_id, _ = _user(pg_session_factory, "admin")
    ticker = f"PGF{uuid.uuid4().hex[:5].upper()}"
    csv = ("ticker,period,sector,revenue,net_income,total_assets,total_equity,total_liabilities,"
           "current_assets,current_liabilities,cash,operating_cash_flow,operating_income,gross_profit,inventory\n"
           f"{ticker},2023Q4,PGSector,,inf,100,50,-inf,10,5,1,2,3,4,\n").encode()
    r = client.post("/fundamentals/upload-csv", headers=_headers(admin_id),
                    files={"file": ("x.csv", csv, "text/csv")})
    assert r.status_code == 200, r.text
    db = pg_session_factory()
    try:
        row = db.execute(text("SELECT revenue, net_income, total_debt, inventory, total_assets "
                              "FROM quarterly_fundamentals WHERE stock_code = :s"), {"s": ticker}).one()
        assert row[:4] == (None, None, None, None)
        assert row.total_assets == 100.0
    finally:
        db.close()
    assert _non_finite_cells(pg_session_factory, "quarterly_fundamentals", "stock_code", ticker) == 0


def test_pg_investor_cannot_modify_shared_statement(client, pg_session_factory):
    investor_id, _ = _user(pg_session_factory, "investor")
    ticker, company_id = _company(pg_session_factory, revenue=100.0)
    csv = f"ticker,period,revenue\n{ticker},2023/12,1\n".encode()
    r = client.post("/financials/import-csv", headers=_headers(investor_id),
                    files={"file": ("x.csv", csv, "text/csv")})
    assert r.status_code == 403
    db = pg_session_factory()
    try:
        assert db.execute(text("SELECT revenue FROM financial_statements WHERE company_id = :c"),
                          {"c": company_id}).scalar_one() == 100.0
    finally:
        db.close()


def test_pg_inactive_account_rejected(client, pg_session_factory):
    user_id, _ = _user(pg_session_factory, "admin", active=False)
    assert client.get("/auth/me", headers=_headers(user_id)).status_code == 403


def test_pg_stale_supabase_admin_claim_does_not_restore_role(client, pg_session_factory):
    user_id, email = _user(pg_session_factory, "investor")  # admin already revoked
    now = int(time.time())
    stale = jwt.encode({"sub": "uid-pg", "email": email, "aud": "authenticated", "iat": now,
                        "exp": now + 3600, "app_metadata": {"role": "admin"}},
                       _SUPABASE_SECRET, algorithm="HS256")
    assert client.get("/admin/users", headers={"Authorization": f"Bearer {stale}"}).status_code == 403
    db = pg_session_factory()
    try:
        assert db.execute(text("SELECT role FROM users WHERE id = :i"), {"i": user_id}).scalar_one() == "investor"
    finally:
        db.close()
