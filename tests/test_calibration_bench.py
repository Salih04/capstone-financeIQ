from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from experiments import calibration_bench as cal


def _prediction_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"ticker": "A", "year": 2024, "model": "m", "y_true": 30.0, "y_pred": 0.1},
            {"ticker": "B", "year": 2024, "model": "m", "y_true": 20.0, "y_pred": 0.2},
            {"ticker": "C", "year": 2024, "model": "m", "y_true": 10.0, "y_pred": 0.3},
        ]
    )


def test_rank_error_is_within_year_and_model_and_deterministic():
    first = cal.attach_rank_errors(_prediction_fixture(), confidence_score=0.25)
    second = cal.attach_rank_errors(_prediction_fixture(), confidence_score=0.25)

    pd.testing.assert_frame_equal(first, second)
    assert first["predicted_rank"].tolist() == [3.0, 2.0, 1.0]
    assert first["realized_rank"].tolist() == [1.0, 2.0, 3.0]
    assert first["rank_error"].tolist() == [2.0, 0.0, 2.0]
    assert first["hybrid_confidence"].tolist() == [0.25, 0.25, 0.25]


def test_constant_confidence_cannot_be_forced_into_deciles():
    rows = cal.attach_rank_errors(_prediction_fixture(), confidence_score=0.25)
    rows["feature_coverage"] = [1.0, 0.5, 0.0]

    bins = cal.calibration_bins(rows)
    monotonicity = cal.monotonicity_check(rows)

    assert len(bins) == 1
    assert bins.iloc[0]["calibration_status"] == "not_estimable"
    assert monotonicity["status"] == "not_estimable"
    assert monotonicity["higher_confidence_lower_error_spearman"] is None


def test_missing_inputs_reduce_hybrid_confidence_and_are_not_imputed():
    complete_state = {
        "quality": {
            "feature_columns": ["feature_a"],
            "n_features": 1,
            "manual_financials": {"accepted_feature_columns": ["feature_a"]},
            "benchmark": {"excess_outperform_targets_enabled": True},
            "frozen_columns_excluded_from_features": [],
        },
        "leaderboard": pd.DataFrame(
            [
                {"split": "test_2024", "kind": "baseline", "spearman": 0.20},
                {"split": "test_2024", "kind": "ml", "spearman": 0.40},
            ]
        ),
    }
    missing_state = {"quality": {}, "leaderboard": None}

    complete = cal.replay_hybrid_confidence(complete_state)
    missing = cal.replay_hybrid_confidence(missing_state)

    assert complete["confidence_score"] == 0.75
    assert missing["confidence_score"] == 0.20
    assert missing["confidence_score"] < complete["confidence_score"]
    assert "benchmark_missing (-0.15)" in missing["confidence_reasons"]
    assert "no_manual_valuation_profitability_features (-0.20)" in missing["confidence_reasons"]


def test_missing_coverage_row_remains_null_instead_of_being_filled():
    rows = cal.attach_rank_errors(_prediction_fixture(), confidence_score=0.25)
    coverage = pd.DataFrame(
        [{"ticker": "A", "feature_year": 2023, "feature_coverage": 0.5}]
    )

    joined = cal.join_feature_coverage(rows, coverage)

    assert joined.loc[joined["ticker"] == "A", "feature_coverage"].item() == 0.5
    assert joined.loc[joined["ticker"] == "B", "feature_coverage"].isna().all()
    assert joined.loc[joined["ticker"] == "B", "coverage_status"].item() == "missing_input_row"


def test_prediction_loader_rejects_missing_values_instead_of_imputing(tmp_path: Path):
    path = tmp_path / "predictions.csv"
    fixture = _prediction_fixture()
    fixture.loc[0, "y_pred"] = None
    fixture.to_csv(path, index=False)

    with pytest.raises(ValueError, match="refusing to impute"):
        cal.load_prediction_dumps([path])


@pytest.mark.parametrize(
    "unsafe",
    [
        "Confidence is a probability of profit.",
        "Probability of success: 80%.",
        "Recommendation strength: high.",
        "This is calibrated confidence.",
        "The result demonstrates validated predictive reliability.",
    ],
)
def test_negative_claim_safety_rejects_unsafe_interpretations(unsafe: str):
    with pytest.raises(ValueError, match="Unsafe calibration claim"):
        cal.validate_claim_safety_text(unsafe)


def test_generated_calibration_artifacts_pin_diagnostic_claim_boundary():
    report = json.loads(cal.JSON_OUTPUT.read_text(encoding="utf-8"))
    markdown = cal.MARKDOWN_OUTPUT.read_text(encoding="utf-8")
    plot = pd.read_csv(cal.PLOT_OUTPUT)

    assert report["task"] == "R2-CAL-01"
    assert report["calibration"]["status"] == "not_estimable"
    assert report["calibration"]["informative_about_rank_error"] is False
    assert report["claim_safety"]["confidence_is_probability_of_return_profit_or_success"] is False
    assert report["claim_safety"]["confidence_is_recommendation_strength"] is False
    assert report["claim_safety"]["validated_predictive_reliability_established"] is False
    assert "no reliable predictive edge" in markdown.lower()
    assert len(plot) == 1
    cal.validate_claim_safety_text(markdown)
