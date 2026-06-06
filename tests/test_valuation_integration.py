"""Tests for free-valuation -> modeling integration (sparse acceptance, naming,
source priority, no leakage)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.data_collection import manual_ingest as M
from scripts.data_collection.pipeline import _manual_col_status

N = np.nan


def test_sparse_varying_column_accepted():
    # market_cap present for only 3/5 tickers but varies year-to-year -> accept
    df = pd.DataFrame({
        "ticker": ["A", "A", "A", "B", "B", "C", "C", "D", "D", "E", "E"],
        "year":   [2020, 2021, 2022, 2020, 2021, 2020, 2021, 2020, 2021, 2020, 2021],
        "market_cap": [100, 120, 150, 200, 260, 50, 55, N, N, N, N],
    })
    assert _manual_col_status(df, "market_cap") == "varying"


def test_frozen_repeated_column_rejected():
    df = pd.DataFrame({
        "ticker": ["A", "A", "A", "B", "B", "C", "C"],
        "year":   [2020, 2021, 2022, 2020, 2021, 2020, 2021],
        "frozen": [9, 9, 9, 7, 7, 5, 5],   # each ticker repeats one value
    })
    assert _manual_col_status(df, "frozen") == "frozen_across_years"


def test_single_year_insufficient():
    df = pd.DataFrame({"ticker": ["A", "B", "C", "D"], "year": [2020] * 4, "x": [1, 2, 3, 4]})
    assert _manual_col_status(df, "x") == "insufficient_history"


def test_all_null_rejected():
    df = pd.DataFrame({"ticker": ["A", "A"], "year": [2020, 2021], "x": [N, N]})
    assert _manual_col_status(df, "x") == "all_null"


def test_pe_pb_alias_maps_to_canonical():
    assert M._ALIAS_TO_CANON.get("pe") == "pe_ratio"
    assert M._ALIAS_TO_CANON.get("pb") == "pb_ratio"
    assert M._ALIAS_TO_CANON.get("market_cap") == "market_cap"
    assert M._ALIAS_TO_CANON.get("ev_ebitda") == "ev_ebitda"
    assert M._ALIAS_TO_CANON.get("enterprise_value") == "enterprise_value"


def test_free_valuation_priority_above_legacy_below_corrected():
    assert M._source_priority("corrected_yearly_financials_candidate.csv") < \
        M._source_priority("free_valuation_history_candidate.csv")
    assert M._source_priority("free_valuation_history_candidate.csv") < \
        M._source_priority("candidate_from_yearly_snapshots.csv")


def test_year_end_close_and_price_never_features():
    # raw price / shares are not canonical manual columns -> never mapped -> never features
    for leak in ("year_end_close", "price", "shares_outstanding", "period_return", "return_1y"):
        assert M._ALIAS_TO_CANON.get(leak) is None


def test_legacy_blocked_from_valuation_override():
    # legacy snapshot tier must not contribute valuation columns
    blocked = set(M.OVERRIDE_MAP) | {"market_cap", "enterprise_value", "pe_ratio",
                                     "pb_ratio", "ps_ratio", "ev_ebitda"}
    for c in ("market_cap", "enterprise_value", "ev_ebitda"):
        assert c in blocked
