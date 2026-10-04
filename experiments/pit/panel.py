"""Build the availability-aware modeling panel (docs/PIT_PROTOCOL.md §4-§6).

Every feature value carries an ``available_at`` timestamp computed from the
registry rule for that feature. Values that are not available at the row's
prediction time are masked to null and counted (never repaired or imputed);
the guard then re-checks the finished panel and refuses if anything slipped.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date

import numpy as np
import pandas as pd

from experiments.pit import config as cfg
from experiments.pit.guard import assert_point_in_time, assert_registered, load_registry

PE_ABS_MAX, PB_ABS_MAX, EV_EBITDA_ABS_MAX = 1000.0, 100.0, 500.0  # build_free_valuation_history.py

FEATURE_SETS = {
    "all_admitted": None,
    "no_market_value": {"financial_statement_level", "financial_statement_ratio",
                        "financial_statement_growth", "price"},
    "price_only": {"price"},
    "statements_only": {"financial_statement_level", "financial_statement_ratio",
                        "financial_statement_growth"},
}


@dataclass
class Panel:
    values: pd.DataFrame          # identifiers, prediction_time, label_end, target, features
    availability: pd.DataFrame    # same index; available_at per feature
    features: list[str]
    mode: str
    cutoff_spec: str
    report: dict = field(default_factory=dict)


def _stamp(d, hh: int, mm: int, ss: int = 0) -> pd.Timestamp:
    if d is None or (isinstance(d, float) and np.isnan(d)) or pd.isna(d):
        return pd.NaT
    return pd.Timestamp(pd.Timestamp(d).date()) + pd.Timedelta(hours=hh, minutes=mm, seconds=ss)


def statement_availability(mode: str) -> dict[tuple[str | None, int], pd.Timestamp]:
    """(ticker or None, fiscal_year) -> statement available_at for the mode."""
    out: dict[tuple[str | None, int], pd.Timestamp] = {}
    if mode == cfg.STANDARDIZED_CUTOFF_MODE:
        with cfg.DEADLINES_PATH.open() as fh:
            for row in csv.DictReader(fh):
                key = (row["ticker"] or None, int(row["fiscal_year"]))
                d = max(date.fromisoformat(row["solo_deadline"]),
                        date.fromisoformat(row["consolidated_deadline"]))
                out[key] = _stamp(d, 23, 59, 59)
    elif mode == cfg.ACTUAL_FILING_DATE_MODE:
        with cfg.FILING_SAMPLE_PATH.open() as fh:
            for row in csv.DictReader(fh):
                out[(row["ticker"], int(row["fiscal_year"]))] = _stamp(
                    date.fromisoformat(row["public_on_or_before"]), 23, 59, 59)
    else:
        raise ValueError(f"unknown mode {mode!r}")
    return out


def _statement_at(table: dict, mode: str, ticker: str, fy: int) -> pd.Timestamp:
    if (ticker, fy) in table:
        return table[(ticker, fy)]
    if mode == cfg.STANDARDIZED_CUTOFF_MODE:
        return table.get((None, fy), pd.NaT)
    return pd.NaT  # ACTUAL mode never falls back to a standardized date


def _valuation(frame: pd.DataFrame) -> pd.DataFrame:
    """PIT market value and the four ratios built on it (published rules inherited)."""
    mv = frame["market_value_pit"].where(frame["market_value_status"] == "ok")
    out = pd.DataFrame(index=frame.index)
    out["market_cap"] = mv.where(mv > 0)
    ni, eq = frame["net_income"], frame["equity"]
    pe = out["market_cap"] / ni
    out["pe_ratio"] = pe.where(frame["pe_ratio_published"].notna() & (ni > 0) & (pe.abs() <= PE_ABS_MAX))
    pb = out["market_cap"] / eq
    out["pb_ratio"] = pb.where(frame["pb_ratio_published"].notna() & (eq > 0) & (pb.abs() <= PB_ABS_MAX))
    ev = out["market_cap"] + frame["net_debt"]
    out["enterprise_value"] = ev.where(frame["enterprise_value_published"].notna())
    evx = out["enterprise_value"] / frame["ebitda"]
    out["ev_ebitda"] = evx.where(frame["ev_ebitda_published"].notna() & (frame["ebitda"] > 0)
                                 & (evx.abs() <= EV_EBITDA_ABS_MAX))
    return out


def build_panel(cutoff_spec: str = "uniform_05_31", mode: str = cfg.STANDARDIZED_CUTOFF_MODE,
                feature_set: str = "all_admitted", exclude_quarantined: bool = True,
                registry: dict | None = None) -> Panel:
    registry = registry or load_registry()
    admitted = [n for n, f in registry.items() if f["status"] == "admitted"]
    allowed = FEATURE_SETS[feature_set]
    features = [n for n in admitted if allowed is None or registry[n]["feature_class"] in allowed]
    assert_registered(features, registry)

    m = pd.read_csv(cfg.MODELING_PATH).rename(columns={"year": "fiscal_year"})
    published = ["market_cap", "pe_ratio", "pb_ratio", "enterprise_value", "ev_ebitda"]
    m = m.rename(columns={c: f"{c}_published" for c in published})
    m = m.drop(columns=[c for c in m.columns if c.startswith(("price_", "benchmark_"))])
    prices = pd.read_csv(cfg.DERIVED / f"price_panel_{cutoff_spec}.csv")
    frame = m.merge(prices, on=["ticker", "fiscal_year"], how="left", validate="one_to_one")
    frame = pd.concat([frame, _valuation(frame)], axis=1)

    frame["prediction_time"] = frame["prediction_date"].map(lambda d: _stamp(d, 18, 0))
    frame["label_end"] = frame["exit_date"].map(lambda d: _stamp(d, 18, 0))
    stmt = statement_availability(mode)
    stmt_at = pd.Series([_statement_at(stmt, mode, t, int(y))
                         for t, y in zip(frame["ticker"], frame["fiscal_year"])], index=frame.index)
    price_at = frame["feature_asof_date"].map(lambda d: _stamp(d, 18, 10))

    availability = pd.DataFrame(index=frame.index)

    def resolve(name: str) -> pd.Series:
        if name in availability:
            return availability[name]
        if name == "market_value_pit":
            return price_at
        rule = registry[name]["availability"]
        if rule["rule"] == "statement_publication":
            col = stmt_at
        elif rule["rule"] == "price_close":
            col = price_at
        elif rule["rule"] == "max_of":
            deps = [resolve(d) for d in rule["depends_on"]]
            col = pd.concat(deps, axis=1).max(axis=1, skipna=False)
        else:
            raise ValueError(f"{name}: rule {rule['rule']!r} cannot be evaluated")
        availability[name] = col
        return col

    masked = {}
    for name in features:
        when = resolve(name)
        unavailable = frame[name].notna() & (when.isna() | (when > frame["prediction_time"]))
        masked[name] = int(unavailable.sum())
        frame.loc[unavailable, name] = np.nan

    frame = frame[frame["fiscal_year"].isin(cfg.FISCAL_YEARS)]
    evaluable = frame["fiscal_year"].isin(cfg.EVALUATED_FISCAL_YEARS)
    status_counts = frame.loc[evaluable, "target_status"].value_counts().to_dict()
    keep = evaluable & frame["target_return_pct"].notna()
    if exclude_quarantined:
        keep &= frame["target_status"].eq("ok")
    values = frame.loc[keep, ["ticker", "fiscal_year", "prediction_time", "label_end",
                              "target_return_pct", "target_status", *features]].copy()
    values = values.rename(columns={"target_return_pct": "target_return"})
    avail = availability.loc[values.index, features]
    assert_point_in_time(values, avail, features)

    return Panel(values.reset_index(drop=True), avail.reset_index(drop=True), features, mode,
                 cutoff_spec, report={
                     "rows_in_published_dataset_evaluable_years": int(evaluable.sum()),
                     "target_status_counts": {str(k): int(v) for k, v in status_counts.items()},
                     "rows_evaluated": int(len(values)),
                     "values_masked_as_unavailable": {k: v for k, v in masked.items() if v},
                     "market_value_status_counts": frame.loc[evaluable, "market_value_status"]
                     .value_counts().to_dict(),
                 })


def ranked(panel: Panel) -> pd.DataFrame:
    """Within-cross-section percentile ranks (same transform as the published harness)."""
    out = panel.values.copy()
    for c in panel.features:
        out[c] = out.groupby("fiscal_year")[c].rank(pct=True)
    return out
