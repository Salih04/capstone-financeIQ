"""R3-STAT-01 ranking & cohort stability diagnostics tests.

These pin the resampling unit (ticker within year), fixed-seed reproducibility,
rank direction, deterministic tie-breaking, top-k boundary behaviour, the
duplicate/missing/insufficient null states, schema stability, artifact
provenance, and adversarial claim-safety wording. Small hand-computed fixtures
carry the positive checks; the jackknife pooled IC is pinned to the canonical
``experiments/significance.py`` convention.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from experiments import rank_stability, significance


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
def _one_year_fixture(year: int = 2023, model: str = "model_x") -> pd.DataFrame:
    """Five tickers; y_pred swaps the first two ranks so year Spearman is 0.9."""
    rows = [
        ("A", 1.0, 2.0),
        ("B", 2.0, 1.0),
        ("C", 3.0, 3.0),
        ("D", 4.0, 4.0),
        ("E", 5.0, 5.0),
    ]
    return pd.DataFrame(
        [
            {"ticker": t, "year": year, "model": model, "y_true": yt, "y_pred": yp}
            for t, yt, yp in rows
        ]
    )


def _sources() -> list[dict[str, object]]:
    return [{"path": "fixture.csv", "sha256": "0" * 64, "rows": 5, "year": 2023, "models": ["model_x"]}]


def _cohort_source() -> dict[str, object]:
    return {"path": "public40.csv", "sha256": "0" * 64, "rows": 40, "ticker_count": 40}


def _build(predictions: pd.DataFrame, cohort: set[str] | None = None, **kwargs):
    return rank_stability.build_report(
        predictions,
        _sources(),
        cohort if cohort is not None else set(),
        _cohort_source(),
        bootstrap_draws=kwargs.pop("bootstrap_draws", 2000),
        **kwargs,
    )


def _write_prediction_dumps(directory: Path) -> tuple[Path, ...]:
    paths = []
    for year in rank_stability.PREDICTION_YEARS:
        frame = _one_year_fixture(year)
        path = directory / f"predictions_test_{year}.csv"
        frame.to_csv(path, index=False, lineterminator="\n")
        paths.append(path)
    return tuple(paths)


def _write_public_40(directory: Path, tickers: list[str]) -> Path:
    path = directory / "universe_public_40.csv"
    pd.DataFrame(
        {
            "ticker": tickers,
            "is_public_universe": ["true"] * len(tickers),
            "is_training_universe": ["true"] * len(tickers),
            "notes": ["fixture"] * len(tickers),
        }
    ).to_csv(path, index=False, lineterminator="\n")
    return path


# --------------------------------------------------------------------------- #
# (a) Rank direction, top-k boundary, deterministic tie-breaking
# --------------------------------------------------------------------------- #
def test_rank_direction_and_top_k_boundary_are_exact() -> None:
    """Rank 1 = highest y_pred; ranks <= K are always in top-K when drawn."""
    tickers = ["A", "B", "C", "D"]
    y_pred = np.array([4.0, 3.0, 2.0, 1.0])  # A highest
    records = rank_stability.bootstrap_year_rank_stability(
        tickers, y_pred, draws=2000, rng=np.random.default_rng(42), top_k=2
    )
    by_ticker = {r["ticker"]: r for r in records}
    # Descending direction: A (highest y_pred) is global rank 1, D (lowest) rank 4.
    assert by_ticker["A"]["full_descending_rank"] == 1
    assert by_ticker["D"]["full_descending_rank"] == 4
    # A is always rank 1 when drawn -> interval collapses to [1, 1], freq 1.0.
    assert by_ticker["A"]["rank_p2_5"] == 1.0
    assert by_ticker["A"]["rank_p97_5"] == 1.0
    assert by_ticker["A"]["top_k_membership_frequency"] == 1.0
    # B (rank 2): at most one higher ticker exists, so within-sample rank <= 2 always.
    assert by_ticker["B"]["top_k_membership_frequency"] == 1.0
    # C (rank 3): can be pushed past the top-2 boundary -> strictly below 1.0.
    assert by_ticker["C"]["top_k_membership_frequency"] < 1.0
    assert by_ticker["D"]["top_k_membership_frequency"] < 1.0


def test_generated_output_discloses_mechanical_top_k_property() -> None:
    """Frozen ranks <= k are mechanically 1.0 and the generated report says so."""
    tickers = ["A", "B", "C", "D"]
    y_pred = np.array([4.0, 3.0, 2.0, 1.0])
    records = rank_stability.bootstrap_year_rank_stability(
        tickers, y_pred, draws=2000, rng=np.random.default_rng(42), top_k=2
    )
    mechanically_top_k = [r for r in records if r["full_descending_rank"] <= r["top_k"]]
    assert mechanically_top_k
    assert all(r["top_k_membership_frequency"] == 1.0 for r in mechanically_top_k)

    report, _ = _build(_one_year_fixture())
    markdown = rank_stability.render_markdown(report)
    assert rank_stability.MECHANICAL_TOP_K_DISCLOSURE in markdown
    assert "A ticker with full-cohort rank <= k gets frequency 1.0 by construction." in markdown
    assert "not evidence of model/data-driven stability" in markdown


def test_deterministic_ticker_tie_breaking_on_equal_scores() -> None:
    """Equal predicted scores break ties by ascending ticker, reproducibly."""
    tickers = ["B", "A", "C"]  # A and B share the top score
    y_pred = np.array([5.0, 5.0, 1.0])
    records = rank_stability.bootstrap_year_rank_stability(
        tickers, y_pred, draws=2000, rng=np.random.default_rng(7)
    )
    by_ticker = {r["ticker"]: r for r in records}
    # Ascending-ticker tie-break: A outranks B despite equal y_pred.
    assert by_ticker["A"]["full_descending_rank"] == 1
    assert by_ticker["B"]["full_descending_rank"] == 2
    assert by_ticker["C"]["full_descending_rank"] == 3


def test_resampling_unit_is_ticker_within_year() -> None:
    """Every within-sample rank stays within the single year's ticker count."""
    tickers = [f"T{i:02d}" for i in range(12)]
    y_pred = np.arange(12, dtype=float)
    records = rank_stability.bootstrap_year_rank_stability(
        tickers, y_pred, draws=2000, rng=np.random.default_rng(1)
    )
    for r in records:
        assert 1 <= r["rank_p2_5"] <= len(tickers)
        assert 1 <= r["rank_p97_5"] <= len(tickers)
        assert r["times_drawn"] <= 2000


def test_years_are_never_pooled_in_rank_stability() -> None:
    """A ticker present only in one year gets a record for that year only."""
    year_a = _one_year_fixture(2023)
    year_b = _one_year_fixture(2024)
    year_b.loc[year_b["ticker"] == "E", "ticker"] = "Z"  # Z exists only in 2024
    predictions = pd.concat([year_a, year_b], ignore_index=True)
    report, _ = _build(predictions)
    per_year = report["per_model"][0]["rank_position_and_top_k_stability"]
    y2023 = {r["ticker"] for r in next(y for y in per_year if y["year"] == 2023)["tickers"]}
    y2024 = {r["ticker"] for r in next(y for y in per_year if y["year"] == 2024)["tickers"]}
    assert "Z" in y2024 and "Z" not in y2023
    assert "E" in y2023 and "E" not in y2024


# --------------------------------------------------------------------------- #
# Fixed-seed reproducibility
# --------------------------------------------------------------------------- #
def test_fixed_seed_reproducibility() -> None:
    predictions = _one_year_fixture()
    first, _ = _build(predictions, seed=42)
    second, _ = _build(predictions, seed=42)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_workflow_is_byte_deterministic(tmp_path: Path) -> None:
    paths = _write_prediction_dumps(tmp_path)
    cohort = _write_public_40(tmp_path, ["A", "B", "C", "D", "E"])
    first = rank_stability.run(
        tmp_path / "first", prediction_paths=paths, public_40_config=cohort
    )
    second = rank_stability.run(
        tmp_path / "second", prediction_paths=paths, public_40_config=cohort
    )
    assert [p.name for p in first] == [p.name for p in second]
    assert [p.read_bytes() for p in first] == [p.read_bytes() for p in second]


# --------------------------------------------------------------------------- #
# (b) Jackknife pooled IC matches the significance convention
# --------------------------------------------------------------------------- #
def test_full_pooled_ic_matches_significance_convention() -> None:
    """The failure-mode guard: pooled IC must equal significance.py exactly."""
    if not all(path.is_file() for path in rank_stability.PREDICTION_PATHS):
        pytest.skip("persisted prediction dumps not present")
    predictions, sources = rank_stability.load_prediction_dumps()
    cohort, cohort_source = rank_stability.load_public_40()
    report, _ = rank_stability.build_report(predictions, sources, cohort, cohort_source)
    pooled = {
        m["model"]: m["full_universe_pooled_ic"] for m in report["per_model"]
    }

    sig_predictions, _ = significance.load_prediction_dumps()
    for model in sorted(sig_predictions["model"].unique()):
        expected = significance.analyze_model(
            sig_predictions[sig_predictions["model"] == model]
        )["pooled"]["observed_ic"]
        assert pooled[model] == pytest.approx(
            round(expected, rank_stability.ROUND_DIGITS), abs=1e-12
        )


def test_hand_checked_leave_one_out_jackknife() -> None:
    """Leave-1-out over the 0.9-IC fixture yields the exact perturbed pooled ICs."""
    report, _ = _build(_one_year_fixture())
    jack = report["per_model"][0]["model_performance_uncertainty_jackknife"]
    assert jack["full_pooled_ic"] == pytest.approx(0.9, abs=1e-9)
    # Five single-observation removals of the one 0.9-IC year:
    #   remove A or B -> repairs the inversion -> IC 1.0
    #   remove C, D, or E -> concordant point removed -> IC 0.8
    assert jack["k1_leave_one_out"]["count"] == 5
    assert jack["k1_leave_one_out"]["max"] == pytest.approx(1.0, abs=1e-9)
    assert jack["k1_leave_one_out"]["min"] == pytest.approx(0.8, abs=1e-9)
    # k=8 is undefined with only five observations -> explicit insufficient_data.
    assert jack["k8_leave_eight_out"]["status"] == "insufficient_data_fewer_than_k_observations"


# --------------------------------------------------------------------------- #
# (c) Cohort composition sensitivity and insufficient-data labelling
# --------------------------------------------------------------------------- #
def test_cohort_below_min_n_is_labelled_insufficient_data() -> None:
    """A public-40 year below MIN_COHORT_N is withheld, not published on a thin cohort."""
    predictions = _one_year_fixture()
    cohort = {"A", "B", "C"}  # 3 < MIN_COHORT_N
    report, _ = _build(predictions, cohort=cohort)
    sensitivity = report["per_model"][0]["cohort_composition_sensitivity_public_40"]
    assert sensitivity["public_40_pooled_ic"] is None
    assert sensitivity["status"] == "insufficient_data_partial_cohort"
    year = sensitivity["per_year"][0]
    assert year["n"] == 3
    assert year["year_ic"] is None
    assert year["status"] == "insufficient_data_below_min_cohort_n"


def test_cohort_meeting_min_n_publishes_pooled_ic(monkeypatch) -> None:
    """With enough cohort rows, the per-year IC and pooled IC are reported."""
    # Lower the threshold so the 5-row fixture can exercise the publish path.
    monkeypatch.setattr(rank_stability, "MIN_COHORT_N", 3)
    predictions = _one_year_fixture()
    report, _ = _build(predictions, cohort={"A", "B", "C", "D", "E"})
    sensitivity = report["per_model"][0]["cohort_composition_sensitivity_public_40"]
    assert sensitivity["status"] == "complete"
    assert sensitivity["public_40_pooled_ic"] == pytest.approx(0.9, abs=1e-9)


# --------------------------------------------------------------------------- #
# Missing / duplicate / insufficient null propagation
# --------------------------------------------------------------------------- #
def test_missing_prediction_yields_explicit_null_without_filling() -> None:
    predictions = _one_year_fixture()
    predictions.loc[predictions["ticker"] == "A", "y_pred"] = np.nan
    report, ticker_rows = _build(predictions)
    tickers = report["per_model"][0]["rank_position_and_top_k_stability"][0]["tickers"]
    row_a = next(r for r in tickers if r["ticker"] == "A")
    assert row_a["status"] == "insufficient_data_missing_prediction"
    assert row_a["top_k_membership_frequency"] is None
    assert row_a["full_descending_rank"] is None
    # The remaining four tickers are still ranked among themselves.
    ranked = [r for r in tickers if r["status"] == "complete"]
    assert len(ranked) == 4


def test_duplicate_rows_are_rejected_on_load(tmp_path: Path) -> None:
    paths = _write_prediction_dumps(tmp_path)
    frame = pd.read_csv(paths[0])
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)  # duplicate A
    frame.to_csv(paths[0], index=False)
    with pytest.raises(ValueError, match="duplicate ticker/year/model"):
        rank_stability.load_prediction_dumps(paths)


def test_invalid_schema_fails_instead_of_guessing_columns(tmp_path: Path) -> None:
    paths = _write_prediction_dumps(tmp_path)
    pd.read_csv(paths[0]).drop(columns=["y_pred"]).to_csv(paths[0], index=False)
    with pytest.raises(ValueError, match="columns must be exactly"):
        rank_stability.load_prediction_dumps(paths)


def test_bootstrap_floor_is_enforced() -> None:
    with pytest.raises(ValueError, match="at least 2000"):
        _build(_one_year_fixture(), bootstrap_draws=100)


# --------------------------------------------------------------------------- #
# Adversarial claim safety
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "unsafe",
    [
        "This membership frequency is pick confidence.",
        "The frequently-top-ranked ticker is a validated pick.",
        "This stability is a predictive signal.",
        "That is a buy recommendation.",
        "The result is market-beating.",
        "Profitable trading follows from these frequencies.",
        "The validated picks identified here should be bought.",
        "The public-40 cohort performs better.",
    ],
)
def test_claim_safety_rejects_adversarial_interpretations(unsafe: str) -> None:
    with pytest.raises(ValueError, match="Unsafe stability claim"):
        rank_stability.validate_claim_safety_text(unsafe)


def test_claim_safety_sentence_is_present_in_markdown() -> None:
    report, _ = _build(_one_year_fixture(), cohort={"A", "B", "C", "D", "E"})
    markdown = rank_stability.render_markdown(report)
    assert rank_stability.CLAIM_SAFETY_SENTENCE in markdown


def test_baseline_equal_weight_ic_always_carries_methodology_qualifier() -> None:
    report, _ = _build(_one_year_fixture(model="baseline_equal_weight"))
    markdown = rank_stability.render_markdown(report)
    assert (
        f"| baseline_equal_weight | baseline | 0.9 — "
        f"{rank_stability.BASELINE_EQUAL_WEIGHT_IC_QUALIFIER} |"
    ) in markdown


def test_loo_deletion_ranges_are_not_labelled_as_confidence_intervals() -> None:
    report, _ = _build(_one_year_fixture())
    markdown = rank_stability.render_markdown(report)
    assert "LOO IC mean (p2.5–p97.5 of deletion estimates)" in markdown
    assert rank_stability.DELETION_RANGE_DISCLAIMER in markdown
    assert "LOO IC mean [2.5%, 97.5%]" not in markdown


def test_estimand_and_limitations_pin_conditioning_and_dependence() -> None:
    report, _ = _build(_one_year_fixture())
    assert "conditional on the ticker being drawn in the bootstrap sample" in report[
        "estimands"
    ]["rank_position_variability"]
    limitations = " ".join(report["limitations"])
    assert (
        "Ticker-year deletion units are treated as exchangeable only for this "
        "descriptive sensitivity diagnostic."
    ) in limitations
    assert (
        "Repeated tickers across years and within-year cross-sectional dependence "
        "prevent interpretation as sampling uncertainty."
    ) in limitations


# --------------------------------------------------------------------------- #
# Schema stability and generated-artifact provenance (real committed outputs)
# --------------------------------------------------------------------------- #
def test_report_schema_is_stable() -> None:
    report, _ = _build(_one_year_fixture(), cohort={"A", "B", "C", "D", "E"})
    assert report["task"] == "R3-STAT-01"
    assert report["schema_version"] == "1.0.0"
    assert report["claim_safety_sentence"] == rank_stability.CLAIM_SAFETY_SENTENCE
    assert report["design"]["resampling_unit"].startswith("ticker within a single test year")
    assert report["design"]["raw_prediction_magnitudes_compared_across_models"] is False
    assert report["design"]["significance_test_added"] is False
    assert report["design"]["p_values_republished"] is False
    assert report["design"]["core_model_or_ranking_changed"] is False
    assert report["claim_safety"]["top_rank_frequency_is_pick_confidence"] is False
    assert report["claim_safety"]["identifies_validated_picks"] is False
    assert report["claim_safety"]["cohort_comparison_is_selection_signal"] is False
    assert set(report["estimands"]) == {
        "rank_position_variability",
        "top_k_membership_stability",
        "model_performance_uncertainty",
        "cohort_composition_sensitivity",
    }


def test_generated_artifacts_have_expected_schema_provenance_and_boundaries() -> None:
    if not rank_stability.JSON_OUTPUT.is_file():
        pytest.skip("rank stability artifacts not generated; run 'make research-rank-stability'")
    report = json.loads(rank_stability.JSON_OUTPUT.read_text(encoding="utf-8"))
    markdown = rank_stability.MARKDOWN_OUTPUT.read_text(encoding="utf-8")
    with rank_stability.TICKER_OUTPUT.open(newline="", encoding="utf-8") as handle:
        ticker_rows = list(csv.DictReader(handle))

    assert report["task"] == "R3-STAT-01"
    assert report["generated_by"]["generator_command"] == "make research-rank-stability"
    assert report["claim_safety_sentence"] == rank_stability.CLAIM_SAFETY_SENTENCE
    assert rank_stability.CLAIM_SAFETY_SENTENCE in markdown
    # Prediction dumps + the public-40 cohort config are all provenance-checksummed.
    assert len(report["source_artifacts"]) == 4
    for source in report["source_artifacts"]:
        assert hashlib.sha256(Path(source["path"]).read_bytes()).hexdigest() == source["sha256"]
    # 9 models x 80 tickers x 3 years in the current dumps.
    assert len(ticker_rows) == 9 * 80 * 3
    assert list(ticker_rows[0]) == [
        "model",
        "year",
        "ticker",
        "full_descending_rank",
        "times_drawn",
        "bootstrap_draws",
        "top_k",
        "top_k_membership_frequency",
        "rank_p2_5",
        "rank_median",
        "rank_p97_5",
        "status",
    ]
    rank_stability.validate_claim_safety_text(markdown)
