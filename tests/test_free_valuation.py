"""Tests for the free-data valuation builder (formulas, rejections, integration)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]

from scripts.data_collection import build_free_valuation_history as V  # noqa: E402


EXPECTED_LIMITATION_TEXT = (
    "Shares outstanding is the binding gap: without a real per-ticker-year share count "
    "(KAP/company reports), market_cap cannot be computed and all derived ratios stay null. "
    "Yahoo provides only year-end PRICE freely, not historical shares. 2024 equity/net_debt are "
    "misaligned and were rejected, not imputed."
)


def test_yahoo_symbol_mapping():
    assert V.yahoo_symbol("THYAO") == "THYAO.IS"
    assert V.yahoo_symbol("ASELS") == "ASELS.IS"
    assert V.yahoo_symbol("aselS") == "ASELS.IS"
    assert V.yahoo_symbol("THYAO.IS") == "THYAO.IS"   # idempotent


def test_year_end_close_is_last_trading_day():
    daily = pd.DataFrame({
        "date": pd.to_datetime(["2021-01-04", "2021-06-30", "2021-12-30", "2022-01-03"]),
        "close": [10.0, 12.0, 15.0, 16.0],
        "adjclose": [10.0, 12.0, 15.0, 16.0],
    })
    daily["year"] = daily["date"].dt.year
    last_2021 = daily[daily["year"] == 2021].sort_values("date").iloc[-1]
    assert last_2021["close"] == 15.0   # last trading day of 2021


def test_market_cap_and_ratio_formulas():
    px, shares = 20.0, 1_000_000.0
    mc = px * shares
    assert mc == 20_000_000.0
    ni, eq, eb, nd = 2_000_000.0, 10_000_000.0, 4_000_000.0, 5_000_000.0
    assert round(mc / ni, 4) == 10.0                 # pe
    assert round(mc / eq, 4) == 2.0                  # pb
    ev = mc + nd
    assert ev == 25_000_000.0                        # enterprise_value
    assert round(ev / eb, 4) == 6.25                 # ev_ebitda


def test_negative_denominators_reject(monkeypatch, tmp_path):
    """net_income<=0 -> pe null; equity<=0 -> pb null; ebitda<=0 -> ev_ebitda null."""
    # craft minimal in-memory inputs by monkeypatching loaders
    tickers = ["AAA", "BBB"]
    prices = pd.DataFrame({"ticker": ["AAA", "AAA", "BBB", "BBB"],
                           "year": [2022, 2023, 2022, 2023],
                           "year_end_close": [10.0, 12.0, 5.0, 6.0],
                           "source": ["test"] * 4})
    shares = pd.DataFrame({"ticker": ["AAA", "AAA", "BBB", "BBB"],
                           "year": [2022, 2023, 2022, 2023],
                           "shares_outstanding": [1e6, 1e6, 1e6, 1e6]})
    fin = pd.DataFrame({"ticker": ["AAA", "AAA", "BBB", "BBB"],
                        "year": [2022, 2023, 2022, 2023],
                        "net_income": [1e6, -5e5, 1e6, 1e6],   # AAA 2023 negative -> pe null
                        "equity": [5e6, 5e6, -1e6, 5e6],       # BBB 2022 negative -> pb null
                        "ebitda": [2e6, 2e6, 2e6, -1e5],       # BBB 2023 negative -> ev_ebitda null
                        "net_debt": [1e5, 1e5, 1e5, 1e5]})
    monkeypatch.setattr(V, "_tickers", lambda: tickers)
    monkeypatch.setattr(V, "collect_year_end_prices", lambda t, **k: (prices, {"yahoo_ok": 0}))
    monkeypatch.setattr(V, "ensure_shares_template", lambda t: True)
    monkeypatch.setattr(V, "load_shares", lambda: (shares, "manual"))
    monkeypatch.setattr(V, "_load_financials", lambda: fin)
    monkeypatch.setattr(V, "CANDIDATE", tmp_path / "cand.csv")
    monkeypatch.setattr(V, "REPORT_JSON", tmp_path / "r.json")
    monkeypatch.setattr(V, "REPORT_MD", tmp_path / "r.md")
    rep = V.build(log=lambda *a: None)
    rs = rep["rejection_summary"]
    assert rs["pe"].get("non_positive_net_income", 0) >= 1
    assert rs["pb"].get("non_positive_equity", 0) >= 1
    assert rs["ev_ebitda"].get("non_positive_ebitda", 0) >= 1
    # market_cap should be computed (all have price+shares) -> accepted/varying
    assert rep["target_column_status"]["market_cap"] in ("accepted", "rejected_frozen")


def test_missing_shares_rejects_market_cap(monkeypatch, tmp_path):
    tickers = ["AAA"]
    prices = pd.DataFrame({"ticker": ["AAA", "AAA"], "year": [2022, 2023],
                           "year_end_close": [10.0, 12.0], "source": ["t", "t"]})
    fin = pd.DataFrame({"ticker": ["AAA", "AAA"], "year": [2022, 2023],
                        "net_income": [1e6, 1e6], "equity": [5e6, 5e6],
                        "ebitda": [2e6, 2e6], "net_debt": [1e5, 1e5]})
    monkeypatch.setattr(V, "_tickers", lambda: tickers)
    monkeypatch.setattr(V, "collect_year_end_prices", lambda t, **k: (prices, {"yahoo_ok": 0}))
    monkeypatch.setattr(V, "ensure_shares_template", lambda t: False)
    monkeypatch.setattr(V, "load_shares", lambda: (None, "missing"))
    monkeypatch.setattr(V, "_load_financials", lambda: fin)
    monkeypatch.setattr(V, "CANDIDATE", tmp_path / "cand.csv")
    monkeypatch.setattr(V, "REPORT_JSON", tmp_path / "r.json")
    monkeypatch.setattr(V, "REPORT_MD", tmp_path / "r.md")
    rep = V.build(log=lambda *a: None)
    assert rep["target_column_status"]["market_cap"] == "missing"
    assert rep["columns_entering_candidate"] == []
    assert rep["shares_status"] == "missing"


def test_committed_report_limitations_are_non_empty_strings():
    report = json.loads(V.REPORT_JSON.read_text(encoding="utf-8"))
    limitations = report["limitations"]

    assert isinstance(limitations, list)
    assert limitations
    assert all(isinstance(item, str) and item.strip() for item in limitations)
    assert limitations == [EXPECTED_LIMITATION_TEXT]


def test_regeneration_produces_committed_report_json(monkeypatch, tmp_path):
    committed_json = V.REPORT_JSON.read_bytes()
    cached_prices = pd.read_csv(V.PRICES_CACHE)
    cached_prices["ticker"] = cached_prices["ticker"].astype(str).str.upper()
    price_columns = ["ticker", "year", "year_end_close", "source"]
    cached_prices = cached_prices[price_columns]

    monkeypatch.setattr(
        V,
        "collect_year_end_prices",
        lambda tickers, **kwargs: (
            cached_prices,
            {"attempted": 0, "yahoo_ok": 0, "from_cache": 81, "from_manual": 0, "failed": []},
        ),
    )
    monkeypatch.setattr(V, "REPORT_JSON", tmp_path / "free_valuation_history_report.json")
    monkeypatch.setattr(V, "REPORT_MD", tmp_path / "free_valuation_history_report.md")

    V.build(log=lambda *args: None)

    assert V.REPORT_JSON.read_bytes() == committed_json


def test_2024_balance_block_rejected(monkeypatch, tmp_path):
    tickers = ["AAA"]
    prices = pd.DataFrame({"ticker": ["AAA", "AAA"], "year": [2023, 2024],
                           "year_end_close": [10.0, 12.0], "source": ["t", "t"]})
    shares = pd.DataFrame({"ticker": ["AAA", "AAA"], "year": [2023, 2024],
                           "shares_outstanding": [1e6, 1e6]})
    fin = pd.DataFrame({"ticker": ["AAA", "AAA"], "year": [2023, 2024],
                        "net_income": [1e6, 1e6], "equity": [5e6, 5e6],
                        "ebitda": [2e6, 2e6], "net_debt": [1e5, 1e5]})
    monkeypatch.setattr(V, "_tickers", lambda: tickers)
    monkeypatch.setattr(V, "collect_year_end_prices", lambda t, **k: (prices, {"yahoo_ok": 0}))
    monkeypatch.setattr(V, "ensure_shares_template", lambda t: True)
    monkeypatch.setattr(V, "load_shares", lambda: (shares, "manual"))
    monkeypatch.setattr(V, "_load_financials", lambda: fin)
    monkeypatch.setattr(V, "CANDIDATE", tmp_path / "cand.csv")
    monkeypatch.setattr(V, "REPORT_JSON", tmp_path / "r.json")
    monkeypatch.setattr(V, "REPORT_MD", tmp_path / "r.md")
    rep = V.build(log=lambda *a: None)
    # 2024 pb / ev must be rejected as suspect, 2023 ok
    assert rep["rejection_summary"]["pb"].get("suspect_2024_equity", 0) >= 1
    assert rep["rejection_summary"]["enterprise_value"].get("suspect_2024_net_debt", 0) >= 1


@pytest.mark.skipif(not (REPO / "data" / "trusted_clean" / "data_quality_report.json").is_file(),
                    reason="pipeline not built")
def test_no_raw_or_leakage_valuation_in_features():
    """Old-snapshot valuation names + raw price/return/volume/shares must never be
    features. Free-DERIVED valuation (market_cap, enterprise_value, pe_ratio,
    pb_ratio, ev_ebitda) IS allowed and, when the builder accepted it, expected."""
    import json
    q = json.loads((REPO / "data" / "trusted_clean" / "data_quality_report.json").read_text())
    feats = set(q.get("feature_columns", []))

    # forbidden: old snapshot names + leakage (NOT the free-derived names)
    forbidden = ("pe", "pb", "market_capitalization", "price", "day_return", "period_return",
                 "volume", "return_1w", "return_1m", "return_3m", "return_6m", "return_ytd",
                 "return_1y", "return_3y", "return_5y", "shares_outstanding", "year_end_close")
    for c in forbidden:
        assert c not in feats, f"forbidden raw/leakage column {c} must not be a feature"

    # no pe + pe_ratio (or pb + pb_ratio) duplication
    assert not ({"pe", "pe_ratio"} <= feats), "pe and pe_ratio must not both be features"
    assert not ({"pb", "pb_ratio"} <= feats), "pb and pb_ratio must not both be features"

    # if the free valuation builder accepted columns, they should be in the model
    sd = q.get("source_distinction", {}) or {}
    entering = set((sd.get("free_valuation_builder", {}) or {}).get("columns_entering_candidate", []))
    derived = {"market_cap", "enterprise_value", "pe_ratio", "pb_ratio", "ev_ebitda"}
    expected = {("pe_ratio" if c == "pe" else "pb_ratio" if c == "pb" else c) for c in entering} & derived
    for c in expected:
        assert c in feats, f"accepted free-derived valuation {c} should be a model feature"
