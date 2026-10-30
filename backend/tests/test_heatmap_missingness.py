"""Sector heatmap: an all-missing cell is null, never 0.0; a real zero stays 0.0.

Follows the A06 missing-value contract (app/core/numeric.py): null, NaN and
+/-Infinity are missing, so they are neither averaged nor turned into 0.0, and
nothing is imputed. Each cell reports how many finite values it averaged and
how many were missing. SQLite stores NaN as NULL, so NaN reaches the service
through an in-memory stand-in for the query; Infinity goes through SQLite.
Synthetic sectors and tickers only.
"""
from __future__ import annotations

import json
import math
import os
from types import SimpleNamespace
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ["RESEARCH_LLM_PROVIDER"] = "none"

import numpy as np  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from app.core.security import create_access_token, hash_password  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models.forecasting import WinnerCohortRow  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.forecasting import HeatmapCell, SectorHeatmapOut  # noqa: E402
from app.services import forecasting_service  # noqa: E402

YEAR = 2024
FEATURES = ("period_return", "return_1y", "return_6m", "return_3m", "return_1m", "day_return")


def _strict_json(text: str):
    """json.loads that refuses the NaN/Infinity tokens Python would otherwise accept."""
    def reject(token):
        raise ValueError(f"non-JSON constant {token}")
    return json.loads(text, parse_constant=reject)


class _FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *_):
        return self

    def all(self):
        return self.rows


def _fake_db(rows):
    return SimpleNamespace(query=lambda _model: _FakeQuery(rows))


def _row(sector: str, **values):
    return SimpleNamespace(sector=sector, **{f: values.get(f) for f in FEATURES})


def _cells(payload: dict, sector: str) -> dict[str, dict]:
    return {c["feature"]: c for c in payload["heatmap"] if c["sector"] == sector}


# ── service ─────────────────────────────────────────────────────────────────

def test_all_missing_cell_is_null_not_zero():
    out = forecasting_service.get_sector_heatmap_data(_fake_db([_row("S"), _row("S")]), year=YEAR)
    cells = _cells(out, "S")
    assert set(cells) == set(FEATURES)
    for cell in cells.values():
        assert cell["value"] is None
        assert (cell["n_observed"], cell["n_missing"]) == (0, 2)


def test_real_zero_is_preserved_and_distinct_from_missing():
    rows = [_row("S", period_return=0.0, day_return=-0.0), _row("S", period_return=0.0)]
    cells = _cells(forecasting_service.get_sector_heatmap_data(_fake_db(rows), year=YEAR), "S")
    assert cells["period_return"]["value"] == 0.0
    assert (cells["period_return"]["n_observed"], cells["period_return"]["n_missing"]) == (2, 0)
    assert cells["day_return"]["value"] == 0.0
    assert (cells["day_return"]["n_observed"], cells["day_return"]["n_missing"]) == (1, 1)
    assert cells["return_1y"]["value"] is None


@pytest.mark.parametrize("special", [float("nan"), np.float64("nan"), float("inf"), float("-inf"), np.inf])
def test_non_finite_values_are_missing_not_averaged(special):
    rows = [_row("S", return_6m=special, return_1m=special), _row("S", return_6m=2.0, return_1m=special)]
    cells = _cells(forecasting_service.get_sector_heatmap_data(_fake_db(rows), year=YEAR), "S")
    assert cells["return_6m"]["value"] == 2.0
    assert (cells["return_6m"]["n_observed"], cells["return_6m"]["n_missing"]) == (1, 1)
    assert cells["return_1m"]["value"] is None
    assert (cells["return_1m"]["n_observed"], cells["return_1m"]["n_missing"]) == (0, 2)
    for cell in cells.values():
        assert cell["value"] is None or math.isfinite(cell["value"])


def test_observed_means_are_unchanged():
    rows = [_row("S", return_3m=1.0), _row("S", return_3m=2.0), _row("S", return_3m=None)]
    cell = _cells(forecasting_service.get_sector_heatmap_data(_fake_db(rows), year=YEAR), "S")["return_3m"]
    assert cell["value"] == 1.5
    assert (cell["n_observed"], cell["n_missing"]) == (2, 1)


# ── schema ──────────────────────────────────────────────────────────────────

def test_schema_accepts_null_and_zero_values():
    assert HeatmapCell(sector="S", feature="f", value=None, n_observed=0, n_missing=3).value is None
    assert HeatmapCell(sector="S", feature="f", value=0.0, n_observed=3, n_missing=0).value == 0.0


@pytest.mark.parametrize("special", [float("nan"), float("inf"), float("-inf")])
def test_schema_rejects_non_finite_values(special):
    with pytest.raises(ValidationError):
        HeatmapCell(sector="S", feature="f", value=special, n_observed=1, n_missing=0)


def test_schema_rejects_negative_counts():
    with pytest.raises(ValidationError):
        HeatmapCell(sector="S", feature="f", value=None, n_observed=-1, n_missing=0)


def test_response_model_serializes_null_as_json_null():
    out = SectorHeatmapOut(year=YEAR, heatmap=[HeatmapCell(sector="S", feature="f", value=None, n_observed=0, n_missing=1)])
    assert _strict_json(out.model_dump_json())["heatmap"][0]["value"] is None


# ── API, through SQLite ─────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def user_headers():
    db = SessionLocal()
    try:
        user = User(email=f"heatmap-{uuid.uuid4().hex[:8]}@example.org",
                    password_hash=hash_password("Passw0rd!"), role="user", is_active=True)
        db.add(user)
        db.commit()
        return {"Authorization": f"Bearer {create_access_token({'sub': str(user.id)})}"}
    finally:
        db.close()


def _seed(sector: str, rows: list[dict]) -> None:
    db = SessionLocal()
    try:
        for values in rows:
            db.add(WinnerCohortRow(source_file="synthetic", year=YEAR, sector=sector,
                                   stock_code=f"HM{uuid.uuid4().hex[:6].upper()}", **values))
        db.commit()
    finally:
        db.close()


def test_api_returns_null_for_all_missing_and_zero_for_real_zero(client, user_headers):
    sector = f"Synthetic heatmap {uuid.uuid4().hex[:8]}"
    _seed(sector, [
        {"period_return": 0.0, "return_6m": 4.0, "return_3m": float("inf"), "return_1m": float("-inf")},
        {"period_return": 0.0, "return_6m": None, "return_3m": 1.0, "return_1m": None},
    ])
    r = client.get("/predict/heatmap", params={"year": YEAR}, headers=user_headers)
    assert r.status_code == 200, r.text
    cells = _cells(_strict_json(r.text), sector)
    assert cells["period_return"] == {"sector": sector, "feature": "period_return", "value": 0.0,
                                      "n_observed": 2, "n_missing": 0}
    assert cells["return_1y"]["value"] is None and cells["return_1y"]["n_missing"] == 2
    assert cells["day_return"]["value"] is None
    assert cells["return_6m"]["value"] == 4.0
    assert cells["return_3m"]["value"] == 1.0
    assert (cells["return_3m"]["n_observed"], cells["return_3m"]["n_missing"]) == (1, 1)
    assert cells["return_1m"]["value"] is None


@pytest.mark.parametrize(
    "values,expected",
    [
        ([1e308, 1e308], 1e308),
        ([-1e308, -1e308], -1e308),
        ([1e308, -1e308], 0.0),
        ([1e308, 1e308, -1e308, -1e308], 0.0),
    ],
)
def test_large_finite_mean_stays_finite(values, expected):
    rows = [_row("OverflowSynthetic", period_return=v) for v in values]
    result = forecasting_service.get_sector_heatmap_data(
        _fake_db(rows), year=YEAR
    )
    cell = _cells(result, "OverflowSynthetic")["period_return"]
    assert cell["value"] == expected
    assert math.isfinite(cell["value"])
    assert cell["n_observed"] == len(values)
    assert cell["n_missing"] == 0

MAX_FLOAT = float.fromhex("0x1.fffffffffffffp+1023")


@pytest.mark.parametrize(
    "values,expected",
    [
        ([MAX_FLOAT] * 3, MAX_FLOAT),
        ([-MAX_FLOAT] * 3, -MAX_FLOAT),
        ([MAX_FLOAT] * 7, MAX_FLOAT),
        ([MAX_FLOAT] * 3 + [-MAX_FLOAT] * 3, 0.0),
    ],
)
def test_maximum_finite_mean_does_not_overflow(values, expected):
    rows = [_row("MaxFiniteSynthetic", period_return=v) for v in values]
    result = forecasting_service.get_sector_heatmap_data(
        _fake_db(rows), year=YEAR
    )
    cell = _cells(result, "MaxFiniteSynthetic")["period_return"]
    assert cell["value"] == expected
    assert math.isfinite(cell["value"])
    assert (cell["n_observed"], cell["n_missing"]) == (len(values), 0)
