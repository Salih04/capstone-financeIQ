"""Daily-price derivations for the PIT evaluation.

Pure functions operate on one ticker's daily series and are unit-tested with
synthetic data. ``build()`` reads the PRIVATE_LOCAL_RAW Yahoo responses and
writes the committed derived tables under ``data/pit/derived/``:

  listing_and_events.csv   first quote, Yahoo split events, unexplained jumps
  price_panel_<spec>.csv   per ticker x fiscal year: prediction date, target
                           window, PIT price features, PIT market value inputs,
                           quarantine reasons

Conventions (docs/PIT_PROTOCOL.md §3-§5):

* Yahoo ``close`` is split-adjusted to the fetch date; ``adjclose`` is split-
  and dividend-adjusted. Returns and momentum use ``adjclose`` ratios, which
  are invariant to the adjustment basis.
* The price *as quoted at the time* is ``close * F(t)``, where ``F(t)`` is the
  product of Yahoo split ratios dated after ``t``. Undoing a vendor transform
  is not look-ahead: it reconstructs the number an investor saw at ``t``.

Run: PYTHONPATH=. python -m experiments.pit.prices
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from experiments.pit import config as cfg


@dataclass(frozen=True)
class Series:
    """One instrument's daily history, indexed by trading date."""

    symbol: str
    frame: pd.DataFrame          # index: date; columns: close, adjclose
    splits: tuple[tuple[date, float], ...]  # (ex-date, new shares per old share)

    @property
    def first_quote(self) -> date:
        return self.frame.index[0]


def load_raw(path: Path) -> Series:
    payload = json.loads(path.read_bytes())
    result = payload["chart"]["result"][0]
    dates = (pd.to_datetime(result["timestamp"], unit="s", utc=True)
             .tz_convert("Europe/Istanbul").date)
    quote = result["indicators"]["quote"][0]
    frame = pd.DataFrame({"close": quote["close"],
                          "adjclose": result["indicators"]["adjclose"][0]["adjclose"]},
                         index=pd.Index(dates, name="date"))
    frame = frame.dropna()
    frame = frame[~frame.index.duplicated(keep="last")].sort_index()
    splits = []
    for event in ((result.get("events") or {}).get("splits") or {}).values():
        ex = pd.to_datetime(event["date"], unit="s", utc=True).tz_convert("Europe/Istanbul").date()
        splits.append((ex, float(event["numerator"]) / float(event["denominator"])))
    return Series(result["meta"]["symbol"], frame, tuple(sorted(splits)))


def jumps(series: Series, column: str = "adjclose") -> list[tuple[date, float]]:
    """Days whose one-day move exceeds the BIST-impossible threshold."""
    values = series.frame[column].to_numpy(float)
    moves = values[1:] / values[:-1] - 1.0
    idx = np.where(np.abs(moves) > cfg.JUMP_THRESHOLD)[0]
    return [(series.frame.index[i + 1], float(moves[i])) for i in idx]


def last_on_or_before(series: Series, d: date) -> tuple[date, pd.Series] | None:
    sub = series.frame.loc[:d]
    if sub.empty:
        return None
    when = sub.index[-1]
    if (d - when).days > cfg.MAX_STALENESS_DAYS:
        return None
    return when, sub.iloc[-1]


def first_after(series: Series, d: date) -> tuple[date, pd.Series] | None:
    sub = series.frame.loc[d + timedelta(days=1):]
    if sub.empty:
        return None
    when = sub.index[0]
    if (when - d).days > cfg.MAX_STALENESS_DAYS:
        return None
    return when, sub.iloc[0]


def split_factor_after(series: Series, d: date) -> float:
    """F(d): product of split ratios with ex-date strictly after ``d``."""
    return float(np.prod([r for ex, r in series.splits if ex > d])) if series.splits else 1.0


def quoted_close(series: Series, d: date) -> float | None:
    """Close as quoted on ``d`` (undo Yahoo's later split adjustment)."""
    hit = series.frame.loc[d:d]
    if hit.empty:
        return None
    return float(hit["close"].iloc[0]) * split_factor_after(series, d)


def window_jump(series: Series, start: date, end: date) -> bool:
    return any(start < when <= end for when, _ in jumps(series))


def trailing_return(series: Series, asof: date, years: int) -> float | None:
    """adjclose return over ``years`` ending at ``asof``; None if exposed to a jump."""
    end = last_on_or_before(series, asof)
    begin = last_on_or_before(series, asof - timedelta(days=365 * years))
    if end is None or begin is None or window_jump(series, begin[0], end[0]):
        return None
    return float(end[1]["adjclose"] / begin[1]["adjclose"] - 1.0) * 100.0


def drawdown_from_high(series: Series, asof: date, years: int = 3) -> float | None:
    end = last_on_or_before(series, asof)
    if end is None:
        return None
    start = asof - timedelta(days=365 * years)
    if window_jump(series, max(start, series.first_quote), end[0]):
        return None
    window = series.frame.loc[start:end[0], "adjclose"]
    return float(end[1]["adjclose"] / window.max() - 1.0) * 100.0


def target_window(series: Series, cutoff_t: date, cutoff_next: date) -> dict:
    """Entry: first quote after the cutoff. Exit: last quote on/before the next cutoff."""
    out = {"entry_date": None, "exit_date": None, "entry_adjclose": None,
           "exit_adjclose": None, "target_return_pct": None, "target_status": "ok"}
    if series.first_quote > cutoff_t + timedelta(days=cfg.MAX_STALENESS_DAYS):
        out["target_status"] = "not_listed_at_prediction"
        return out
    entry, exit_ = first_after(series, cutoff_t), last_on_or_before(series, cutoff_next)
    if entry is None:
        out["target_status"] = "no_entry_quote"
        return out
    if exit_ is None or series.frame.index[-1] < cutoff_next:
        out["target_status"] = "window_incomplete"
        out.update(entry_date=entry[0], entry_adjclose=float(entry[1]["adjclose"]))
        return out
    out.update(entry_date=entry[0], exit_date=exit_[0],
               entry_adjclose=float(entry[1]["adjclose"]),
               exit_adjclose=float(exit_[1]["adjclose"]))
    out["target_return_pct"] = (out["exit_adjclose"] / out["entry_adjclose"] - 1.0) * 100.0
    if window_jump(series, entry[0], exit_[0]):
        out["target_status"] = "unexplained_jump_in_window"
    return out


def share_count_consistent(shares: pd.Series, series: Series, year: int) -> bool:
    """Year-end share counts around ``year`` agree with Yahoo's dated split ratios.

    ``shares`` is indexed by year (year-end issued capital). A change that is
    not matched by a split (rights issue, buy-back, stale record) or a split
    without a share change both fail: either means the price and share-count
    adjustment bases cannot be shown to agree.
    """
    for y in (year, year + 1):
        if y - 1 not in shares.index or y not in shares.index:
            continue  # nothing to compare against at the edge of the record
        ratio = shares[y] / shares[y - 1]
        split = float(np.prod([r for ex, r in series.splits if ex.year == y])) if series.splits else 1.0
        if abs(ratio / split - 1.0) > cfg.SHARE_SPLIT_TOLERANCE:
            return False
    return True


def pit_market_value(series: Series, shares: pd.Series | None, fiscal_year: int,
                     asof: date) -> tuple[float | None, str]:
    """Market value at ``asof`` on one adjustment basis, or a reason it is excluded.

    mcap(asof) = quoted_close(asof) x shares(asof)
               = close(asof) x F(31 Dec FY) x shares(31 Dec FY)
    which holds when every share-count change between 31 Dec FY and ``asof`` is
    a split or bonus issue recorded by Yahoo. The checks below enforce that.
    """
    if shares is None or fiscal_year not in shares.index or pd.isna(shares[fiscal_year]):
        return None, "no_share_count"
    year_end = date(fiscal_year, 12, 31)
    if not share_count_consistent(shares, series, fiscal_year):
        return None, "share_count_disagrees_with_split_history"
    if any(when > year_end for when, _ in jumps(series, "close")):
        return None, "unexplained_jump_after_year_end"
    end = last_on_or_before(series, asof)
    if end is None:
        return None, "no_quote_at_reference_date"
    value = float(end[1]["close"]) * split_factor_after(series, year_end) * float(shares[fiscal_year])
    return value, "ok"


def _load_all() -> tuple[dict[str, Series], Series]:
    by_ticker = {}
    for path in sorted(cfg.RAW_DAILY_DIR.glob("*.json")):
        s = load_raw(path)
        by_ticker[s.symbol.replace(".IS", "")] = s
    bench = by_ticker.pop(cfg.BENCHMARK_SYMBOL.replace(".IS", ""))
    return by_ticker, bench


def build() -> None:
    if not cfg.RAW_DAILY_DIR.is_dir():
        raise SystemExit(f"{cfg.RAW_DAILY_DIR} missing: run "
                         "scripts/data_collection/fetch_yahoo_daily_history.py first")
    cfg.DERIVED.mkdir(parents=True, exist_ok=True)
    series, bench = _load_all()
    shares_tbl = pd.read_csv(cfg.SHARES_PATH)
    shares = {t: g.set_index("year")["shares_outstanding"] for t, g in shares_tbl.groupby("ticker")}

    meta = []
    for t, s in sorted(series.items()):
        meta.append({"ticker": t, "first_quote": s.first_quote, "last_quote": s.frame.index[-1],
                     "n_quotes": len(s.frame),
                     "splits": ";".join(f"{d}:{r:g}" for d, r in s.splits),
                     "adjclose_jumps": ";".join(f"{d}:{m:+.3f}" for d, m in jumps(s)),
                     "close_jumps": ";".join(f"{d}:{m:+.3f}" for d, m in jumps(s, "close"))})
    pd.DataFrame(meta).to_csv(cfg.DERIVED / "listing_and_events.csv", index=False)

    for spec in cfg.CUTOFF_SPECS:
        rows = []
        for fy in cfg.FISCAL_YEARS:
            c_t = cfg.cutoff(spec, fy)
            try:
                c_next = cfg.cutoff(spec, fy + 1)
            except KeyError:  # no registered deadline yet: window cannot be complete
                c_next = date.max - timedelta(days=cfg.MAX_STALENESS_DAYS + 1)
            bench_1y = trailing_return(bench, c_t, 1)
            for t, s in sorted(series.items()):
                asof = last_on_or_before(s, c_t)
                win = target_window(s, c_t, c_next)
                mom1 = trailing_return(s, c_t, 1)
                mv, mv_status = pit_market_value(s, shares.get(t), fy, c_t)
                rows.append({
                    "ticker": t, "fiscal_year": fy, "cutoff_spec": spec,
                    "cutoff_date": c_t, "feature_asof_date": asof[0] if asof else None,
                    "prediction_date": win["entry_date"],
                    **{k: win[k] for k in ("entry_date", "exit_date", "entry_adjclose",
                                           "exit_adjclose", "target_return_pct", "target_status")},
                    "first_quote": s.first_quote,
                    "price_data_available": 1.0 if asof else 0.0,
                    "price_history_years_available": (round((c_t - s.first_quote).days / 365.25, 3)
                                                      if s.first_quote <= c_t else 0.0),
                    "price_momentum_1y_pct": mom1,
                    "price_momentum_2y_pct": trailing_return(s, c_t, 2),
                    "price_drawdown_from_3y_high_pct": drawdown_from_high(s, c_t, 3),
                    "price_vs_bist100_1y_pct": (mom1 - bench_1y) if mom1 is not None and bench_1y is not None else None,
                    "benchmark_1y_return_pct": bench_1y,
                    "market_value_pit": mv, "market_value_status": mv_status,
                })
        out = pd.DataFrame(rows)
        out.to_csv(cfg.DERIVED / f"price_panel_{spec}.csv", index=False, float_format="%.10g")
        print(f"{spec}: {len(out)} rows; target_status="
              f"{out[out.fiscal_year.isin(cfg.EVALUATED_FISCAL_YEARS)].target_status.value_counts().to_dict()}; "
              f"market_value_status={out.market_value_status.value_counts().to_dict()}")


if __name__ == "__main__":
    build()
