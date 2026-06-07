"""Tests for the manual 2024 balance-sheet correction file."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "2.backend"))

from scripts.data_collection import manual_ingest as M  # noqa: E402
from scripts.data_collection import build_free_valuation_history as V  # noqa: E402

N = np.nan


def test_shifted_2024_cells_rejected_money_ratio_shape():
    """Ratio sitting in a money column and money sitting in a ratio column are nulled."""
    out = pd.DataFrame({
        "ticker": ["AAA", "BBB"], "year": [2024, 2024],
        "equity": [0.45, 5_000_000_000.0],          # AAA equity is a ratio -> reject
        "current_ratio": [1.8, 22_000_000_000.0],   # BBB current_ratio is money -> reject
    })
    rep = M.ManualReport()
    fixed = M._enforce_money_ratio_shape(out.copy(), "corrected_balance_sheet_2024.csv", rep)
    assert pd.isna(fixed.loc[0, "equity"])           # 0.45 nulled (ratio in money slot)
    assert fixed.loc[1, "equity"] == 5_000_000_000.0  # valid money kept
    assert fixed.loc[0, "current_ratio"] == 1.8       # valid ratio kept
    assert pd.isna(fixed.loc[1, "current_ratio"])     # 22e9 nulled (money in ratio slot)
    assert any("money/ratio shape" in i for i in rep.issues)


def test_canon_and_override_include_balance_ratios():
    for c in ("current_ratio", "leverage_ratio", "financial_debt_ratio", "net_debt_to_ebitda"):
        assert M._ALIAS_TO_CANON.get(c) == c
        assert M.OVERRIDE_MAP.get(c) == c
    # corrected balance file has top (high) priority
    assert M._source_priority("corrected_balance_sheet_2024.csv") == 0


def test_load_financials_overrides_only_2024_equity_netdebt(monkeypatch, tmp_path):
    modeling = pd.DataFrame({
        "ticker": ["AAA", "AAA"], "year": [2023, 2024],
        "net_income": [1e6, 1e6], "equity": [5e6, 9.9],     # 2024 equity misaligned (ratio)
        "ebitda": [2e6, 2e6], "net_debt": [1e5, 0.4],       # 2024 net_debt misaligned
    })
    mp = tmp_path / "modeling.csv"; modeling.to_csv(mp, index=False)
    corr = pd.DataFrame({"ticker": ["AAA"], "year": [2024],
                         "equity": [7_000_000.0], "net_debt": [250_000.0]})
    cp = tmp_path / "corrected_balance_sheet_2024.csv"; corr.to_csv(cp, index=False)
    monkeypatch.setattr(V, "MODELING_CSV", mp)
    monkeypatch.setattr(V, "CORRECTED_BS_2024", cp)
    f = V._load_financials().set_index(["ticker", "year"])
    assert f.loc[("AAA", 2024), "equity"] == 7_000_000.0   # overridden
    assert f.loc[("AAA", 2024), "net_debt"] == 250_000.0   # overridden
    assert f.loc[("AAA", 2023), "equity"] == 5e6           # 2023 untouched
    assert f.loc[("AAA", 2024), "net_income"] == 1e6       # income untouched


def test_corrected_set_marks_tickers(monkeypatch, tmp_path):
    corr = pd.DataFrame({"ticker": ["AAA", "BBB"], "year": [2024, 2024],
                         "equity": [7e6, 0.5], "net_debt": [2e5, 1e5]})   # BBB equity is ratio-> excluded
    cp = tmp_path / "corrected_balance_sheet_2024.csv"; corr.to_csv(cp, index=False)
    monkeypatch.setattr(V, "CORRECTED_BS_2024", cp)
    s = V.load_corrected_bs_2024()
    assert "AAA" in s and "BBB" not in s


def test_valuation_recomputes_2024_when_corrected(monkeypatch, tmp_path):
    """With corrected 2024 equity/net_debt, pb/ev for 2024 are computed (not suspect)."""
    tickers = ["AAA"]
    prices = pd.DataFrame({"ticker": ["AAA", "AAA"], "year": [2023, 2024],
                           "year_end_close": [10.0, 12.0], "source": ["t", "t"]})
    shares = pd.DataFrame({"ticker": ["AAA", "AAA"], "year": [2023, 2024],
                           "shares_outstanding": [1e6, 1e6]})
    fin = pd.DataFrame({"ticker": ["AAA", "AAA"], "year": [2023, 2024],
                        "net_income": [1e6, 1e6], "equity": [5e6, 6e6],
                        "ebitda": [2e6, 2e6], "net_debt": [1e5, 1e5]})
    corr = pd.DataFrame({"ticker": ["AAA"], "year": [2024], "equity": [6e6], "net_debt": [1e5]})
    cp = tmp_path / "corrected_balance_sheet_2024.csv"; corr.to_csv(cp, index=False)
    monkeypatch.setattr(V, "_tickers", lambda: tickers)
    monkeypatch.setattr(V, "collect_year_end_prices", lambda t, **k: (prices, {"yahoo_ok": 0}))
    monkeypatch.setattr(V, "ensure_shares_template", lambda t: True)
    monkeypatch.setattr(V, "load_shares", lambda: (shares, "manual"))
    monkeypatch.setattr(V, "_load_financials", lambda: fin)
    monkeypatch.setattr(V, "CORRECTED_BS_2024", cp)
    monkeypatch.setattr(V, "CANDIDATE", tmp_path / "cand.csv")
    monkeypatch.setattr(V, "REPORT_JSON", tmp_path / "r.json")
    monkeypatch.setattr(V, "REPORT_MD", tmp_path / "r.md")
    rep = V.build(log=lambda *a: None)
    # 2024 pb / ev must NOT be rejected as suspect now
    assert rep["rejection_summary"]["pb"].get("suspect_2024_equity", 0) == 0
    assert rep["rejection_summary"]["enterprise_value"].get("suspect_2024_net_debt", 0) == 0
    assert rep["corrected_balance_sheet_2024"]["tickers_corrected"] == 1


def test_no_leakage_after_correction():
    """Raw price/return/volume/shares are not canonical -> never become features."""
    for leak in ("year_end_close", "price", "shares_outstanding", "period_return", "return_1y", "volume"):
        assert M._ALIAS_TO_CANON.get(leak) is None
