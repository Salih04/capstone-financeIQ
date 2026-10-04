"""Corporate actions, pre-listing rows and placeholder returns in the PIT panel."""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from experiments.pit import config as cfg
from experiments.pit import prices
from experiments.pit.panel import build_panel


def _series(closes: list[float], start: date = date(2022, 1, 3), splits=(), adj=None) -> prices.Series:
    days = [start + timedelta(days=i) for i in range(len(closes))]
    frame = pd.DataFrame({"close": closes, "adjclose": adj if adj is not None else closes},
                         index=pd.Index(days, name="date"))
    return prices.Series("SYN.IS", frame, tuple(splits))


def test_bonus_issue_keeps_market_value_on_one_basis():
    """A 1:1 bonus issue halves the quoted price and doubles the shares.

    Yahoo back-adjusts the pre-event close, so the published method
    (adjusted close x historical shares) halves the year-end market value.
    The PIT method restores the as-quoted price and must not.
    """
    ex = date(2023, 6, 1)
    # Yahoo view after the event: pre-event closes divided by 2.
    days = 600
    start = date(2022, 6, 1)
    quoted = [100.0 if start + timedelta(days=i) < ex else 50.0 for i in range(days)]
    yahoo = [q / 2 if start + timedelta(days=i) < ex else q for i, q in enumerate(quoted)]
    s = _series(yahoo, start=start, splits=[(ex, 2.0)])
    shares = pd.Series({2021: 1_000.0, 2022: 1_000.0, 2023: 2_000.0, 2024: 2_000.0})
    published_style = yahoo[(date(2022, 12, 31) - start).days] * shares[2022]
    value, status = prices.pit_market_value(s, shares, 2022, date(2022, 12, 31))
    assert status == "ok"
    assert value == 100.0 * 1_000.0          # as quoted x historical shares
    assert published_style == value / 2       # the defect being fixed
    after, _ = prices.pit_market_value(s, shares, 2023, date(2023, 12, 31))
    assert after == value                      # continuous across the event


def test_share_record_disagreeing_with_split_history_is_excluded():
    ex = date(2023, 6, 1)
    s = _series([10.0] * 800, start=date(2022, 1, 3), splits=[(ex, 8.0)])
    stale_shares = pd.Series({2022: 1_000.0, 2023: 1_000.0, 2024: 1_000.0})  # bonus not recorded
    value, status = prices.pit_market_value(s, stale_shares, 2022, date(2022, 12, 31))
    assert value is None and status == "share_count_disagrees_with_split_history"


def test_unexplained_jump_quarantines_target_and_market_value():
    closes = [10.0] * 200 + [1.0] * 400  # -90 % in one day, no split recorded
    s = _series(closes, start=date(2023, 1, 2))
    win = prices.target_window(s, date(2023, 5, 31), date(2024, 5, 31))
    assert win["target_status"] == "unexplained_jump_in_window"
    value, status = prices.pit_market_value(s, pd.Series({2022: 5.0, 2023: 5.0}), 2022,
                                            date(2023, 5, 31))
    assert value is None and status == "unexplained_jump_after_year_end"


def test_unlisted_security_has_no_target():
    s = _series([10.0] * 300, start=date(2024, 3, 21))  # first quote after the cutoff
    win = prices.target_window(s, date(2023, 5, 31), date(2024, 5, 31))
    assert win["target_status"] == "not_listed_at_prediction"
    assert win["target_return_pct"] is None


def test_window_entry_after_cutoff_and_exit_on_or_before_next_cutoff():
    s = _series(list(np.linspace(10, 20, 800)), start=date(2022, 1, 3))
    win = prices.target_window(s, date(2022, 5, 31), date(2023, 5, 31))
    assert win["entry_date"] > date(2022, 5, 31)
    assert win["exit_date"] <= date(2023, 5, 31)
    assert win["target_status"] == "ok"


def test_pre_listing_rows_and_vendor_placeholders_never_reach_evaluation():
    panel = build_panel()
    events = pd.read_csv(cfg.DERIVED / "listing_and_events.csv", parse_dates=["first_quote"])
    first = events.set_index("ticker")["first_quote"]
    v = panel.values
    assert (v["prediction_time"] >= v["ticker"].map(first)).all()
    # Five unlisted tickers shared this vendor "return" for 2021 in the published data.
    assert not np.isclose(v["target_return"], 56.947991).any()
    assert set(v["target_status"]) == {"ok"}
    assert panel.report["target_status_counts"]["not_listed_at_prediction"] > 0


def test_market_value_features_only_where_pit_valid():
    panel = build_panel()
    pp = pd.read_csv(cfg.DERIVED / "price_panel_uniform_05_31.csv")
    status = pp.set_index(["ticker", "fiscal_year"])["market_value_status"]
    keyed = panel.values.set_index(["ticker", "fiscal_year"])
    has_mv = keyed["market_cap"].notna()
    assert (status.reindex(keyed.index)[has_mv] == "ok").all()
