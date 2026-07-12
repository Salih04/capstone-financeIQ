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


# Raw / old-snapshot / leakage columns that must NEVER be model features.
# NOTE: free-DERIVED valuation (market_cap, enterprise_value, pe_ratio, pb_ratio,
# ev_ebitda) IS allowed once the free valuation builder produces it — it is NOT
# listed here. Only the old snapshot names (pe, pb, market_capitalization) and raw
# price/return/volume/shares are forbidden.
RAW_OR_LEAKAGE_FORBIDDEN = (
    "pe", "pb", "market_capitalization",                       # old frozen snapshot names
    "price", "day_return", "period_return", "volume",          # leakage: price/volume
    "return_1w", "return_1m", "return_3m", "return_6m",
    "return_ytd", "return_1y", "return_3y", "return_5y",       # leakage: returns
    "shares_outstanding", "year_end_close",                    # raw inputs, not features
)


def test_modeling_features_grew_only_with_validated_fields():
    """Income features present; no raw/old-snapshot/leakage column is a feature.
    Free-derived valuation (pe_ratio/pb_ratio/market_cap/...) is allowed."""
    quality = REPO / "data" / "trusted_clean" / "data_quality_report.json"
    if not quality.is_file():
        pytest.skip("modeling dataset not built")
    q = json.loads(quality.read_text())
    feats = set(q.get("feature_columns", []))
    # validated income/profitability features entered the model
    assert {"revenue", "ebitda", "net_income", "roe", "roa"} & feats, \
        "expected corrected income/profitability features in the model"
    # raw / old-snapshot / leakage columns must never be features
    for c in RAW_OR_LEAKAGE_FORBIDDEN:
        assert c not in feats, f"forbidden raw/leakage column {c} must not be a feature"


def _valid_source_frame(rows: int = ING.EXPECTED_TICKERS) -> pd.DataFrame:
    data = {
        "stock_code": [f"T{i:02d}" for i in range(rows)],
        **{column: list(range(rows)) for column in ING.INCOME_FIELDS},
        **{column: list(range(rows)) for column in ING.MARGIN_FIELDS},
    }
    return pd.DataFrame(data)


def test_corrected_source_wrong_header_fails_with_required_columns():
    df = _valid_source_frame().rename(columns={"stock_code": "stock_cod"})
    with pytest.raises(ValueError, match=r"malformed header; missing required column.*stock_code"):
        ING._validate_source_frame(df, "2023stocks.xlsx")


def test_corrected_source_wrong_shape_fails_with_expected_counts():
    df = _valid_source_frame(rows=ING.EXPECTED_TICKERS - 1)
    with pytest.raises(ValueError, match=r"malformed shape; expected exactly 40 rows.*found 39 rows"):
        ING._validate_source_frame(df, "2023stocks.xlsx")
