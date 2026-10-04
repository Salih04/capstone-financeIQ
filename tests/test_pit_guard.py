"""The point-in-time guard rejects features by timestamp, not by name.

Each test injects a defect the guard must catch: a future-available value, a
feature that only *looks* lagged, an unregistered or excluded feature, a
training label realised after the prediction time, and the published
T -> T+1 design itself.
"""
from __future__ import annotations

import pandas as pd
import pytest

from experiments.pit import config as cfg
from experiments.pit.guard import (
    PointInTimeViolation,
    assert_labels_realized,
    assert_point_in_time,
    assert_registered,
    load_registry,
)
from experiments.pit.panel import build_panel, statement_availability

REGISTRY = load_registry()


def _frame(available_at: list[str], prediction_time: str = "2024-06-03 18:00") -> tuple:
    values = pd.DataFrame({"ticker": [f"T{i}" for i in range(len(available_at))],
                           "prediction_time": pd.Timestamp(prediction_time),
                           "net_income": 1.0})
    avail = pd.DataFrame({"net_income": pd.to_datetime(available_at)})
    return values, avail


def test_registry_covers_every_published_feature():
    published = pd.read_csv(cfg.MODELING_PATH, nrows=1).columns
    non_features = {"ticker", "company_name", "year", "sector", "indices", "is_bist100",
                    "same_year_return_pct", "target_year", "has_target", "is_inference_row",
                    "is_public_universe", "is_training_universe", "universe_source"}
    feats = [c for c in published if c not in non_features and not c.startswith("next_year_")]
    assert sorted(feats) == sorted(REGISTRY), "registry and published feature set diverge"
    for name, entry in REGISTRY.items():
        for key in ("source", "observation_period", "availability", "transformation",
                    "earliest_usable_prediction", "status"):
            assert entry.get(key), f"{name}: registry field {key} is empty"


def test_value_available_before_prediction_passes():
    values, avail = _frame(["2024-05-20 23:59:59"])
    assert_point_in_time(values, avail, ["net_income"])


def test_future_available_value_is_rejected():
    values, avail = _frame(["2024-05-20 23:59:59", "2024-06-04 23:59:59"])
    with pytest.raises(PointInTimeViolation, match="not available at prediction time"):
        assert_point_in_time(values, avail, ["net_income"])


def test_same_day_after_close_is_rejected():
    # A statement filed after the session on the prediction date is not usable that day.
    values, avail = _frame(["2024-06-03 23:59:59"])
    with pytest.raises(PointInTimeViolation):
        assert_point_in_time(values, avail, ["net_income"])


def test_value_without_timestamp_is_rejected():
    values, avail = _frame([None])
    with pytest.raises(PointInTimeViolation):
        assert_point_in_time(values, avail, ["net_income"])


def test_lagged_looking_name_does_not_bypass_the_guard():
    values = pd.DataFrame({"ticker": ["T0"], "prediction_time": pd.Timestamp("2024-06-03 18:00"),
                           "lagged_prior_year_revenue": 1.0})
    with pytest.raises(PointInTimeViolation, match="unknown"):
        assert_registered(["lagged_prior_year_revenue"], REGISTRY)
    with pytest.raises(PointInTimeViolation, match="no availability timestamps"):
        assert_point_in_time(values, pd.DataFrame(index=values.index), ["lagged_prior_year_revenue"])


def test_excluded_feature_is_refused():
    with pytest.raises(PointInTimeViolation, match="excluded"):
        assert_registered(["price_adjclose_t"], REGISTRY)


def test_training_label_realised_after_prediction_is_rejected():
    ends = pd.Series(pd.to_datetime(["2023-05-31 18:00", "2024-06-03 18:00"]))
    starts = pd.Series(pd.to_datetime(["2024-06-03 18:00"]))
    with pytest.raises(PointInTimeViolation):
        assert_labels_realized(ends, starts)
    assert_labels_realized(ends.iloc[:1], starts)


def test_published_design_fails_the_guard():
    """FY-T statements scored on the first trading day of T+1 (the published design)."""
    stmt = statement_availability(cfg.STANDARDIZED_CUTOFF_MODE)
    rows = [(fy, stmt[(None, fy)]) for fy in (2020, 2021, 2022, 2023, 2024)]
    values = pd.DataFrame({"ticker": "X", "net_income": 1.0,
                           "prediction_time": [pd.Timestamp(f"{fy + 1}-01-04 18:00") for fy, _ in rows]})
    avail = pd.DataFrame({"net_income": [at for _, at in rows]})
    with pytest.raises(PointInTimeViolation, match="5 feature values"):
        assert_point_in_time(values, avail, ["net_income"])


def test_actual_mode_never_falls_back_to_standardized_dates():
    panel = build_panel(mode=cfg.ACTUAL_FILING_DATE_MODE, feature_set="statements_only")
    with_values = panel.values.dropna(subset=["net_income"])
    sample = pd.read_csv(cfg.FILING_SAMPLE_PATH)
    allowed = set(zip(sample["ticker"], sample["fiscal_year"]))
    assert set(zip(with_values["ticker"], with_values["fiscal_year"])) <= allowed


def test_deadline_extension_masks_the_affected_row():
    """SASA FY2022 (earthquake-region deadline 10 May 2023) is not public on 3 Apr 2023."""
    panel = build_panel("deadline_month_end", feature_set="statements_only")
    sasa = panel.values[(panel.values["ticker"] == "SASA") & (panel.values["fiscal_year"] == 2022)]
    assert len(sasa) == 1 and sasa["net_income"].isna().all()
    assert panel.report["values_masked_as_unavailable"]["net_income"] == 1
    primary = build_panel("uniform_05_31", feature_set="statements_only")
    assert "net_income" not in primary.report["values_masked_as_unavailable"]


def test_primary_cutoff_is_not_earlier_than_any_statutory_deadline():
    deadlines = pd.read_csv(cfg.DEADLINES_PATH)
    for _, row in deadlines.iterrows():
        latest = max(pd.Timestamp(row["solo_deadline"]), pd.Timestamp(row["consolidated_deadline"]))
        assert pd.Timestamp(cfg.cutoff("uniform_05_31", int(row["fiscal_year"]))) >= latest


def test_sampled_filings_precede_the_primary_cutoff():
    for _, row in pd.read_csv(cfg.FILING_SAMPLE_PATH).iterrows():
        assert pd.Timestamp(row["public_on_or_before"]) <= pd.Timestamp(
            cfg.cutoff("uniform_05_31", int(row["fiscal_year"])))
