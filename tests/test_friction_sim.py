from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from experiments import friction_sim


def _group(year: int = 2024) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"ticker": "A", "year": year, "model": "m", "y_true": 30.0, "y_pred": 0.1},
            {"ticker": "B", "year": year, "model": "m", "y_true": 20.0, "y_pred": 0.9},
            {"ticker": "C", "year": year, "model": "m", "y_true": 10.0, "y_pred": 0.5},
            {"ticker": "D", "year": year, "model": "m", "y_true": -5.0, "y_pred": 0.2},
        ]
    )


def test_basket_formation_uses_descending_within_model_rank_and_is_scale_invariant() -> None:
    original = friction_sim.form_top_k_basket(_group(), top_k=2)
    transformed = _group()
    transformed["y_pred"] = transformed["y_pred"] * 1_000 + 17
    shifted = friction_sim.form_top_k_basket(transformed, top_k=2)

    assert original["selected_tickers_ranked"] == ["B", "C"]
    assert shifted["selected_tickers_ranked"] == ["B", "C"]
    assert original["gross_basket_mean_return_pct"] == 15.0
    assert "within target year and model" in original["ranking_rule"]


def test_rank_ties_use_ticker_as_a_deterministic_tie_break() -> None:
    group = _group()
    group.loc[group["ticker"].isin(["A", "B"]), "y_pred"] = 1.0

    basket = friction_sim.form_top_k_basket(group.sample(frac=1, random_state=7), top_k=2)

    assert basket["selected_tickers_ranked"] == ["A", "B"]


def test_turnover_is_half_l1_weight_change() -> None:
    assert friction_sim.basket_turnover(["A", "B", "C", "D"], ["A", "B", "E", "F"]) == 0.5
    assert friction_sim.basket_turnover(["A", "B"], ["A", "B"]) == 0.0
    assert friction_sim.basket_turnover(["A", "B"], ["C", "D"]) == 1.0


def test_zero_and_adverse_cost_controls_pin_cost_arithmetic() -> None:
    zero_drag, zero_net = friction_sim.apply_cost(5.0, 0.75, 0.0)
    adverse_drag, adverse_net = friction_sim.apply_cost(5.0, 0.75, 10_000.0)

    assert (zero_drag, zero_net) == (0.0, 5.0)
    assert (adverse_drag, adverse_net) == (75.0, -70.0)
    assert adverse_net < zero_net


def test_missing_values_are_excluded_or_propagated_never_filled() -> None:
    group = _group()
    group.loc[group["ticker"] == "B", "y_pred"] = None
    group.loc[group["ticker"] == "C", "y_true"] = None

    basket = friction_sim.form_top_k_basket(group, top_k=2)

    assert basket["selected_tickers_ranked"] == ["C", "D"]
    assert basket["excluded_missing_prediction_rows"] == 1
    assert basket["selected_missing_realized_rows"] == 1
    assert basket["gross_basket_mean_return_pct"] is None
    assert friction_sim.apply_cost(None, 0.5, 100.0) == (None, None)
    assert friction_sim.apply_cost(5.0, None, 100.0) == (None, None)


@pytest.mark.parametrize(
    "unsafe",
    [
        "These are implementable returns.",
        "Achievable performance is shown.",
        "Investment value is established.",
        "A reliable predictive edge was found.",
        "Verified historical BIST100 membership.",
        "Market impact is 25 bps.",
    ],
)
def test_claim_safety_rejects_unsafe_friction_interpretations(unsafe: str) -> None:
    with pytest.raises(ValueError, match="Unsafe friction claim"):
        friction_sim.validate_claim_safety_text(unsafe)


def test_generated_report_pins_cohort_basis_controls_and_claim_boundaries() -> None:
    report = json.loads(friction_sim.JSON_OUTPUT.read_text(encoding="utf-8"))
    markdown = friction_sim.MARKDOWN_OUTPUT.read_text(encoding="utf-8")
    plot = pd.read_csv(friction_sim.PLOT_OUTPUT)

    assert report["task"] == "R2-FRICTION-01"
    assert report["design"]["universe"] == friction_sim.UNIVERSE_LABEL
    assert report["design"]["raw_prediction_magnitudes_emitted"] is False
    assert report["claim_safety"]["implementable_returns_established"] is False
    assert report["claim_safety"]["reliable_predictive_edge_established"] is False
    assert {0.0, 10_000.0}.issubset(set(plot["cost_bps_assumption"]))
    assert plot["chart_stamp"].eq(friction_sim.CHART_STAMP).all()
    assert plot["gross_basket_mean_return_pct"].notna().all()
    assert friction_sim.CHART_STAMP in markdown
    assert "not verified point-in-time BIST100 membership" in markdown
    friction_sim.validate_claim_safety_text(markdown)


def test_workflow_is_byte_deterministic(tmp_path: Path) -> None:
    first = friction_sim.run(tmp_path / "first")
    second = friction_sim.run(tmp_path / "second")

    assert [path.name for path in first] == [path.name for path in second]
    assert [path.read_bytes() for path in first] == [path.read_bytes() for path in second]
