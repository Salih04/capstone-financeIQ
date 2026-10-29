"""Audit A06: missing stays null through ratio math and persistence.

NaN, +/-Infinity, overflow and absent components are missing values: they
must never be stored, never become 0.0 and never be replaced by an imputed
value. SQLite silently turns NaN into NULL, so NaN persistence is also checked
against PostgreSQL in test_postgres_integrity.py. Synthetic inputs only.
"""
from __future__ import annotations

import math
import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ["RESEARCH_LLM_PROVIDER"] = "none"

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.numeric import finite_or_none  # noqa: E402
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models.company import Company  # noqa: E402
from app.models.financial import ComputedMetric, FinancialStatement  # noqa: E402
from app.models.forecasting import QuarterlyFundamental, WinnerCohortRow  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services import forecasting_service, fundamentals_service  # noqa: E402
from app.services.ratio_service import compute_ratios  # noqa: E402

_SPECIALS = [float("nan"), float("inf"), float("-inf"), np.float64("nan"), np.inf]
_RATIO_INPUTS = ("revenue", "net_income", "operating_income", "total_assets", "total_equity",
                 "total_liabilities", "current_assets", "current_liabilities", "inventory",
                 "cash", "operating_cash_flow")


def _statement(**values) -> FinancialStatement:
    base = dict(revenue=1000.0, net_income=100.0, operating_income=150.0, total_assets=2000.0,
                total_equity=800.0, total_liabilities=1200.0, current_assets=500.0,
                current_liabilities=250.0, inventory=100.0, cash=50.0, operating_cash_flow=120.0)
    base.update(values)
    return FinancialStatement(**base)


def _assert_finite_or_null(mapping: dict) -> None:
    for key, value in mapping.items():
        assert value is None or math.isfinite(value), f"{key}={value!r}"


# ── unit: coercion helper ───────────────────────────────────────────────────

@pytest.mark.parametrize("value", [None, *_SPECIALS, "nan", "inf", "-Infinity", "1e999"])
def test_finite_or_none_maps_missing_and_non_finite_to_none(value):
    assert finite_or_none(value) is None


@pytest.mark.parametrize("value, expected", [(0, 0.0), (-0.0, 0.0), (1.5, 1.5), ("2.25", 2.25), (np.int64(7), 7.0)])
def test_finite_or_none_keeps_finite_values(value, expected):
    assert finite_or_none(value) == expected


# ── unit: ratio_service ─────────────────────────────────────────────────────

def test_a06_missing_inventory_gives_null_quick_ratio_not_current_ratio():
    ratios = compute_ratios(_statement(inventory=None))
    assert ratios["current_ratio"] == 2.0
    assert ratios["quick_ratio"] is None


def test_a06_quick_ratio_unchanged_when_inventory_known():
    assert compute_ratios(_statement())["quick_ratio"] == pytest.approx(1.6)
    assert compute_ratios(_statement(inventory=0.0))["quick_ratio"] == 2.0


def test_a06_infinite_denominator_is_not_a_zero_ratio():
    assert compute_ratios(_statement(total_assets=float("inf")))["roa"] is None


def test_a06_overflowing_ratio_is_null():
    assert compute_ratios(_statement(net_income=1e308, total_assets=1e-10))["roa"] is None


def test_a06_negative_zero_denominator_is_null():
    assert compute_ratios(_statement(total_assets=-0.0))["roa"] is None


@pytest.mark.parametrize("field", _RATIO_INPUTS)
@pytest.mark.parametrize("special", _SPECIALS, ids=["nan", "inf", "-inf", "np.nan", "np.inf"])
def test_a06_no_ratio_is_ever_nan_or_infinite(field, special):
    _assert_finite_or_null(compute_ratios(_statement(**{field: special})))


def test_a06_complete_statement_ratios_unchanged():
    ratios = compute_ratios(_statement())
    assert ratios["roa"] == pytest.approx(0.05)
    assert ratios["roe"] == pytest.approx(0.125)
    assert ratios["debt_to_equity"] == pytest.approx(1.5)
    assert ratios["cash_flow_margin"] == pytest.approx(0.12)


# ── unit: text parsers used before persistence ──────────────────────────────

@pytest.mark.parametrize("parser", [fundamentals_service._to_float, forecasting_service._to_float],
                         ids=["fundamentals", "forecasting"])
@pytest.mark.parametrize("value", [*_SPECIALS, "inf", "NaN", "Infinity", "1e999", "", None])
def test_a06_parsers_return_none_for_missing_or_non_finite(parser, value):
    assert parser(value) is None


@pytest.mark.parametrize("parser", [fundamentals_service._to_float, forecasting_service._to_float],
                         ids=["fundamentals", "forecasting"])
def test_a06_parsers_keep_finite_values(parser):
    assert parser(12.5) == 12.5
    assert parser("1.234,5") == 1234.5
    assert parser("%3,5") == 3.5


def test_a06_pandas_ratio_helper_never_returns_infinity():
    out = forecasting_service._safe_div(pd.Series([1.0, np.inf, 5.0, 1e308]),
                                        pd.Series([2.0, 1.0, 0.0, 1e-10]))
    assert out.iloc[0] == 0.5
    assert out.iloc[1:].isna().all()


def test_a06_zero_base_growth_is_missing_not_infinite():
    fdf = pd.DataFrame({
        "stock_code": ["G", "G"], "period": ["2023Q3", "2023Q4"],
        **{c: [1.0, 1.0] for c in ("equity", "total_assets", "gross_profit", "revenue", "ebit",
                                    "ocf", "total_debt", "cash", "inventory",
                                    "current_assets", "current_liabilities")},
        "net_income": [0.0, 5.0],
    })
    out = forecasting_service._fundamentals_to_exact_ratios(fdf)
    assert pd.isna(out["Net Kar Buyumesi"].iloc[1])


# ── persistence through the HTTP write paths (admin) ────────────────────────

@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def admin_headers():
    db = SessionLocal()
    try:
        user = User(email=f"a06-admin-{uuid.uuid4().hex[:8]}@example.org",
                    password_hash=hash_password("Passw0rd!"), role="admin", is_active=True)
        db.add(user)
        db.commit()
        return {"Authorization": f"Bearer {create_access_token({'sub': str(user.id)})}"}
    finally:
        db.close()


def _company() -> tuple[str, int]:
    ticker = f"A6{uuid.uuid4().hex[:6].upper()}"
    db = SessionLocal()
    try:
        company = Company(ticker=ticker, company_name="Synthetic A06", sector="Industrial")
        db.add(company)
        db.commit()
        return ticker, company.id
    finally:
        db.close()


def _stored(company_id: int) -> tuple[FinancialStatement, ComputedMetric]:
    db = SessionLocal()
    try:
        stmt = db.query(FinancialStatement).filter(FinancialStatement.company_id == company_id).one()
        metric = db.query(ComputedMetric).filter(ComputedMetric.company_id == company_id).one()
        db.expunge_all()
        return stmt, metric
    finally:
        db.close()


_SPECIAL_ROW = "revenue,net_income,total_assets,total_equity,total_liabilities,current_assets,current_liabilities,cash\n"


def test_a06_financials_import_stores_null_for_blank_nan_and_infinity(client, admin_headers):
    ticker, company_id = _company()
    csv = ("ticker,period," + _SPECIAL_ROW + f"{ticker},2023/12,,inf,nan,-inf,1e999,500,250,50\n").encode()
    r = client.post("/financials/import-csv", headers=admin_headers,
                    files={"file": ("x.csv", csv, "text/csv")})
    assert r.status_code == 200, r.text
    stmt, metric = _stored(company_id)
    for field in ("revenue", "net_income", "total_assets", "total_equity", "total_liabilities"):
        assert getattr(stmt, field) is None, field
    assert stmt.current_assets == 500.0
    assert metric.roa is None and metric.roe is None and metric.debt_to_assets is None
    assert metric.current_ratio == 2.0
    assert metric.quick_ratio is None  # inventory column absent → unknown, not zero
    r = client.get(f"/companies/{company_id}/metrics", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()[0]["roa"] is None


def test_a06_ingestion_import_stores_null_for_non_finite_text(client, admin_headers):
    ticker, company_id = _company()
    csv = ("ticker,period,revenue,net_income,total_assets,total_equity,current_assets,current_liabilities\n"
           f"{ticker},2023/12,Infinity,10,-Infinity,NaN,500,250\n").encode()
    r = client.post("/ingestion/import/csv", headers=admin_headers,
                    files={"file": ("x.csv", csv, "text/csv")})
    assert r.status_code == 200, r.text
    stmt, metric = _stored(company_id)
    assert stmt.revenue is None and stmt.total_assets is None and stmt.total_equity is None
    assert stmt.net_income == 10.0
    assert metric.roa is None and metric.net_margin is None
    assert metric.quick_ratio is None


def test_a06_fundamentals_upload_stores_null_for_blank_and_infinity(client, admin_headers):
    ticker = f"A6F{uuid.uuid4().hex[:5].upper()}"
    csv = ("ticker,period,sector,revenue,net_income,total_assets,total_equity,total_liabilities,"
           "current_assets,current_liabilities,cash,operating_cash_flow,operating_income,gross_profit,inventory\n"
           f"{ticker},2023Q4,A06Sector,,inf,100,50,-inf,10,5,1,2,3,4,\n").encode()
    r = client.post("/fundamentals/upload-csv", headers=admin_headers,
                    files={"file": ("x.csv", csv, "text/csv")})
    assert r.status_code == 200, r.text
    db = SessionLocal()
    try:
        row = db.query(QuarterlyFundamental).filter(QuarterlyFundamental.stock_code == ticker).one()
        assert row.revenue is None and row.net_income is None and row.total_debt is None
        assert row.inventory is None
        assert row.total_assets == 100.0
    finally:
        db.close()


def test_a06_cohort_preset_import_does_not_impute_medians(tmp_path, monkeypatch):
    (tmp_path / "data").mkdir()
    codes = [f"A6P{uuid.uuid4().hex[:4].upper()}{i}" for i in range(3)]
    pd.DataFrame({
        "Şirket": codes,
        "Sektör": ["A06 Synthetic"] * 3,
        "Getiri % 2021": [10.0, None, 30.0],
        "Fiyat": [1.0, 2.0, None],
    }).to_excel(tmp_path / "2021 a06 synthetic.xlsx", index=False)
    monkeypatch.setenv("RESEARCH_REPO_ROOT", str(tmp_path))
    db = SessionLocal()
    try:
        admin = User(email=f"preset-admin-{uuid.uuid4().hex}@example.org",
                     password_hash="unused-synthetic", role="admin", is_active=True)
        db.add(admin)
        db.commit()
        result = forecasting_service.import_winner_excel_preset(db, "2021 a06 synthetic.xlsx", current_user=admin)
        assert result["imported_rows"] == 3
        rows = {r.stock_code: r for r in db.query(WinnerCohortRow).filter(WinnerCohortRow.stock_code.in_(codes))}
        assert rows[codes[1]].period_return is None  # was imputed to the 20.0 median
        assert rows[codes[2]].price is None          # was imputed to the 1.5 median
        assert rows[codes[0]].period_return == 10.0 and rows[codes[2]].period_return == 30.0
        assert rows[codes[1]].price == 2.0
    finally:
        db.close()
