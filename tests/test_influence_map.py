"""R3-INF-01 leave-one-out IC influence diagnostics tests.

These pin the leave-one-out arithmetic against a hand computation, prove the
pooled IC is byte-for-byte the same convention as ``experiments/significance.py``,
exercise the missing-data and boundary null states, confirm byte determinism,
and reject adversarial value-claim wording.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from experiments import influence_map, significance


def _one_year_fixture(year: int = 2023) -> pd.DataFrame:
    """Five tickers; y_pred swaps the first two ranks so full-year Spearman is 0.9."""
    rows = []
    for ticker, y_true, y_pred in (
        ("A", 1.0, 2.0),
        ("B", 2.0, 1.0),
        ("C", 3.0, 3.0),
        ("D", 4.0, 4.0),
        ("E", 5.0, 5.0),
    ):
        rows.append(
            {
                "ticker": ticker,
                "year": year,
                "model": "model_x",
                "y_true": y_true,
                "y_pred": y_pred,
            }
        )
    return pd.DataFrame(rows)


def _sources() -> list[dict[str, object]]:
    return [{"path": "fixture.csv", "sha256": "0" * 64, "rows": 5, "year": 2023, "models": ["model_x"]}]


def _write_prediction_dumps(directory: Path) -> tuple[Path, Path, Path]:
    paths = []
    for year in influence_map.PREDICTION_YEARS:
        frame = _one_year_fixture(year)
        path = directory / f"predictions_test_{year}.csv"
        frame.to_csv(path, index=False, lineterminator="\n")
        paths.append(path)
    return tuple(paths)  # type: ignore[return-value]


# --------------------------------------------------------------------------- #
# Positive: hand-computed leave-one-out arithmetic
# --------------------------------------------------------------------------- #
def test_hand_checked_single_year_leave_one_out_deltas() -> None:
    report, observations = influence_map.build_report(_one_year_fixture(), _sources())
    summary = report["per_model_summary"][0]

    # Full-year Spearman with one adjacent rank swap is exactly 0.9; one year so
    # the pooled IC equals the year IC.
    assert summary["full_pooled_ic"] == pytest.approx(0.9, abs=1e-9)

    by_ticker = {row["ticker"]: row for row in observations}
    # Removing A or B repairs the single inversion -> year IC 1.0 -> delta +0.1.
    assert by_ticker["A"]["delta_pooled_ic"] == pytest.approx(0.1, abs=1e-9)
    assert by_ticker["A"]["sign"] == "positive"
    assert by_ticker["B"]["delta_pooled_ic"] == pytest.approx(0.1, abs=1e-9)
    # Removing C (a concordant middle point) drops the year IC to 0.8 -> delta -0.1.
    assert by_ticker["C"]["delta_pooled_ic"] == pytest.approx(-0.1, abs=1e-9)
    assert by_ticker["C"]["sign"] == "negative"
    assert all(row["status"] == "complete" for row in observations)


def test_hand_checked_two_year_repooling() -> None:
    year_a = _one_year_fixture(2023)  # year IC 0.9
    year_b = _one_year_fixture(2024)
    year_b["y_pred"] = year_b["y_true"]  # perfect -> year IC 1.0
    predictions = pd.concat([year_a, year_b], ignore_index=True)

    report, observations = influence_map.build_report(predictions, _sources())
    summary = report["per_model_summary"][0]
    # Pooled IC is the equal-weighted mean of the two year ICs: (0.9 + 1.0) / 2.
    assert summary["full_pooled_ic"] == pytest.approx(0.95, abs=1e-9)

    a_2023 = next(
        row for row in observations if row["ticker"] == "A" and row["year"] == 2023
    )
    # Removing A in 2023 lifts that year to 1.0; 2024 unchanged -> pooled 1.0.
    assert a_2023["loo_pooled_ic"] == pytest.approx(1.0, abs=1e-9)
    assert a_2023["delta_pooled_ic"] == pytest.approx(0.05, abs=1e-9)


def test_full_pooled_ic_matches_significance_convention() -> None:
    """The failure-mode guard: pooled IC must equal significance.py exactly."""
    if not all(path.is_file() for path in influence_map.PREDICTION_PATHS):
        pytest.skip("persisted prediction dumps not present")
    predictions, sources = influence_map.load_prediction_dumps()
    report, _ = influence_map.build_report(predictions, sources)
    influence_pooled = {
        summary["model"]: summary["full_pooled_ic"]
        for summary in report["per_model_summary"]
    }

    sig_predictions, _ = significance.load_prediction_dumps()
    for model in sorted(sig_predictions["model"].unique()):
        expected = significance.analyze_model(
            sig_predictions[sig_predictions["model"] == model]
        )["pooled"]["observed_ic"]
        # The report rounds to influence_map.ROUND_DIGITS; pin to that precision.
        assert influence_pooled[model] == pytest.approx(
            round(expected, influence_map.ROUND_DIGITS), abs=1e-12
        )


# --------------------------------------------------------------------------- #
# Missing data and boundary null states
# --------------------------------------------------------------------------- #
def test_missing_prediction_yields_explicit_null_without_filling() -> None:
    predictions = _one_year_fixture()
    predictions.loc[predictions["ticker"] == "A", "y_pred"] = np.nan
    report, observations = influence_map.build_report(predictions, _sources())

    row_a = next(row for row in observations if row["ticker"] == "A")
    assert row_a["delta_pooled_ic"] is None
    assert row_a["loo_pooled_ic"] is None
    assert row_a["sign"] is None
    assert row_a["status"] == "insufficient_data_missing_or_nonfinite_value"
    # The remaining four rows still yield a defined pooled IC (year now has 4 usable rows).
    assert report["per_model_summary"][0]["full_pooled_ic"] is not None
    assert report["analysis_status"] == "partial_with_explicit_insufficient_data"


def test_removal_below_three_rows_is_insufficient_data() -> None:
    predictions = _one_year_fixture().iloc[:3].copy()  # exactly 3 usable rows
    report, observations = influence_map.build_report(predictions, _sources())
    assert report["per_model_summary"][0]["full_pooled_ic"] is not None
    for row in observations:
        assert row["delta_pooled_ic"] is None
        assert row["status"] == "insufficient_data_fewer_than_3_rows_after_removal"
    assert report["per_model_summary"][0]["influence_concentration_top5_abs_share"] is None
    assert report["analysis_status"] == "partial_with_explicit_insufficient_data"


def test_invalid_schema_fails_instead_of_guessing_columns(tmp_path: Path) -> None:
    paths = _write_prediction_dumps(tmp_path)
    pd.read_csv(paths[0]).drop(columns=["y_pred"]).to_csv(paths[0], index=False)

    with pytest.raises(ValueError, match="columns must be exactly"):
        influence_map.load_prediction_dumps(paths)


# --------------------------------------------------------------------------- #
# Adversarial claim safety
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "unsafe",
    [
        "Influence reveals mispriced stocks.",
        "This sensitivity is a signal.",
        "A reliable predictive edge was found.",
        "This is a buy recommendation.",
        "The result is market-beating.",
        "Profitable trading follows from these deltas.",
        "The mispriced tickers identified here should be bought.",
    ],
)
def test_claim_safety_rejects_adversarial_interpretations(unsafe: str) -> None:
    with pytest.raises(ValueError, match="Unsafe influence claim"):
        influence_map.validate_claim_safety_text(unsafe)


def test_claim_safety_sentence_is_present_in_markdown() -> None:
    report, _ = influence_map.build_report(_one_year_fixture(), _sources())
    markdown = influence_map.render_markdown(report)
    assert influence_map.CLAIM_SAFETY_SENTENCE in markdown


# --------------------------------------------------------------------------- #
# Generated-artifact provenance and boundaries (real committed outputs)
# --------------------------------------------------------------------------- #
def test_generated_artifacts_have_expected_schema_provenance_and_boundaries() -> None:
    if not influence_map.JSON_OUTPUT.is_file():
        pytest.skip("influence artifacts not generated; run 'make research-influence'")
    report = json.loads(influence_map.JSON_OUTPUT.read_text(encoding="utf-8"))
    markdown = influence_map.MARKDOWN_OUTPUT.read_text(encoding="utf-8")
    with influence_map.OBSERVATION_OUTPUT.open(newline="", encoding="utf-8") as handle:
        observation_rows = list(csv.DictReader(handle))

    assert report["task"] == "R3-INF-01"
    assert report["generated_by"]["generator_command"] == "make research-influence"
    assert report["design"]["raw_prediction_magnitudes_compared_across_models"] is False
    assert report["design"]["significance_test_added"] is False
    assert report["design"]["core_model_or_ranking_changed"] is False
    assert report["claim_safety"]["identifies_mispriced_stocks"] is False
    assert report["claim_safety"]["predictive_validity_established"] is False
    assert report["claim_safety"]["reliable_predictive_edge_established"] is False
    assert report["claim_safety_sentence"] == influence_map.CLAIM_SAFETY_SENTENCE
    assert influence_map.CLAIM_SAFETY_SENTENCE in markdown
    assert len(report["source_artifacts"]) == 3
    for source in report["source_artifacts"]:
        assert hashlib.sha256(Path(source["path"]).read_bytes()).hexdigest() == source["sha256"]
    # 9 models x 80 tickers x 3 years in the current dumps.
    assert len(observation_rows) == 9 * 80 * 3
    assert list(observation_rows[0]) == [
        "model",
        "ticker",
        "year",
        "full_pooled_ic",
        "year_full_ic",
        "year_loo_ic",
        "loo_pooled_ic",
        "delta_pooled_ic",
        "abs_delta_pooled_ic",
        "sign",
        "status",
    ]
    influence_map.validate_claim_safety_text(markdown)


def test_workflow_is_byte_deterministic(tmp_path: Path) -> None:
    paths = _write_prediction_dumps(tmp_path)
    first = influence_map.run(tmp_path / "first", prediction_paths=paths)
    second = influence_map.run(tmp_path / "second", prediction_paths=paths)

    assert [path.name for path in first] == [path.name for path in second]
    assert [path.read_bytes() for path in first] == [path.read_bytes() for path in second]
