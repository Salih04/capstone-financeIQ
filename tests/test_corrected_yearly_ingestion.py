"""Tests for corrected-yearly financial ingestion + its effect on the model.

Validates that real per-year income/profitability columns are accepted, frozen
valuation columns are rejected, the 2024 misalignment is caught, leakage columns
never enter the candidate, and the modeling feature set grows only with validated
fields (no raw frozen valuation leaks in).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.data_collection import ingest_corrected_yearly_financials as ING

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "data" / "trusted_raw" / "financials_corrected_yearly"

pytestmark = pytest.mark.skipif(not SRC.is_dir() or not any(SRC.glob("*.xlsx")),
                                reason="corrected yearly XLSX source not present")


@pytest.fixture(scope="module")
def report():
    return ING.ingest()


def test_candidate_written_with_income_columns(report):
    assert ING.OUT_CSV.is_file()
    df = pd.read_csv(ING.OUT_CSV)
    assert {"ticker", "year"}.issubset(df.columns)
    for c in ("revenue", "gross_profit", "operating_income", "ebitda", "net_income"):
        assert c in df.columns, f"income column {c} missing from candidate"


def test_income_profitability_accepted(report):
    acc = set(report["accepted_columns"])
    for c in ("revenue", "ebitda", "net_income", "roe", "roa",
              "gross_profit_margin", "ebitda_margin", "net_profit_margin"):
        assert c in acc, f"{c} should be accepted (varies per year)"


def test_frozen_valuation_rejected(report):
    froz = set(report["frozen_valuation_columns"])
    acc = set(report["accepted_columns"])
    for c in ("pe", "pb", "ev_ebitda", "market_capitalization", "enterprise_value"):
        assert c in froz, f"{c} should be reported frozen_snapshot"
        assert c not in acc, f"{c} must never be accepted as a feature"


def test_2024_misalignment_detected(report):
    ev = report["misalignment_2024_evidence"]
    # the shifted balance-sheet / ratio block must be flagged
    assert ev, "expected 2024 misalignment evidence"
    for c in ("current_assets", "equity", "leverage_ratio"):
        assert c in ev and ev[c] > 0, f"{c} 2024 misalignment not detected"


def test_leakage_columns_never_in_candidate(report):
    df = pd.read_csv(ING.OUT_CSV)
    for c in ("price", "period_return", "day_return", "volume",
              "return_1m", "return_1y", "return_3m"):
        assert c not in df.columns, f"leakage column {c} leaked into candidate"


def test_candidate_columns_numeric(report):
    df = pd.read_csv(ING.OUT_CSV)
    for c in [x for x in df.columns if x not in ("ticker", "year")]:
        assert pd.api.types.is_numeric_dtype(df[c]), f"{c} is not numeric"


def test_modeling_features_grew_only_with_validated_fields():
    """If the modeling dataset was rebuilt, income features are present and no raw
    frozen valuation column is a feature."""
    quality = REPO / "data" / "trusted_clean" / "data_quality_report.json"
    if not quality.is_file():
        pytest.skip("modeling dataset not built")
    q = json.loads(quality.read_text())
    feats = set(q.get("feature_columns", []))
    # validated income/profitability features entered the model
    assert {"revenue", "ebitda", "net_income", "roe", "roa"} & feats, \
        "expected corrected income/profitability features in the model"
    # raw frozen valuation must never be a feature
    for c in ("pe", "pb", "ev_ebitda", "market_cap", "market_capitalization", "enterprise_value"):
        assert c not in feats, f"frozen valuation {c} must not be a feature"
