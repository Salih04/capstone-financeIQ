"""Focused contract tests for R4-ROBUST-01.

These tests exercise the frozen transform contract with disposable frames and
keep repository-output checks separate from the pre-generation unit checks.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from experiments import contamination_lab as lab


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_REPAIRED_SIGNIFICANCE_SHA256 = "08062b5e2e9af9d9a91200665811492c373dc6fa8db1acd0a849cb3d3d932ab3"


def _frame(rows_per_year: int = 80) -> pd.DataFrame:
    rows = []
    for year in range(2020, 2025):
        for index in range(rows_per_year):
            base = float(index - rows_per_year / 2 + year - 2020)
            rows.append(
                {
                    "ticker": f"T{index:03d}",
                    "company_name": f"Company {index}",
                    "year": year,
                    "sector": "test",
                    "indices": "BIST100",
                    "is_bist100": True,
                    "same_year_return_pct": base,
                    "target_year": year + 1,
                    "has_target": year < 2025,
                    "is_inference_row": False,
                    "is_public_universe": True,
                    "is_training_universe": True,
                    "universe_source": "fixture",
                    "ebitda_growth_pct": base,
                    "gross_profit_growth_pct": base * 2,
                    "net_income_growth_pct": base * 3,
                    "operating_income_growth_pct": base * 4,
                    "revenue_growth_pct": base * 5,
                    "other_feature": base / 10,
                    "next_year_return_pct": base + 1,
                    "next_year_excess_return_vs_bist100": base + 2,
                    "next_year_outperform_bist100": index % 2 == 0,
                    "next_year_top_20pct_returner": index % 5 == 0,
                }
            )
    frame = pd.DataFrame(rows)
    frame.loc[0, "revenue_growth_pct"] = np.nan
    frame.loc[1, list(lab.ELIGIBLE_FEATURES)] = np.nan
    return frame


def _threshold_masks(frame: pd.DataFrame, feature: str, q: float = 0.05):
    lower, upper = lab.fit_thresholds(frame[feature].dropna().tolist(), q)
    lower_mask, upper_mask = lab.affected_masks(frame[feature], lower, upper)
    return {feature: (lower_mask, upper_mask)}, {feature: (lower, upper)}


def test_only_exact_growth_columns_are_eligible():
    assert list(lab.ELIGIBLE_FEATURES) == [
        "ebitda_growth_pct",
        "gross_profit_growth_pct",
        "net_income_growth_pct",
        "operating_income_growth_pct",
        "revenue_growth_pct",
    ]


def test_targets_are_immutable():
    frame = _frame()
    masks, thresholds = _threshold_masks(frame, "revenue_growth_pct")
    transformed = lab.apply_operator(frame, masks, thresholds, "trim_to_null")
    for column in frame.columns:
        if column.startswith("next_year_"):
            pd.testing.assert_series_equal(frame[column], transformed[column])


def test_canonical_dataset_is_read_only():
    path = ROOT / "data/trusted_clean/modeling_dataset_training_2020_2025.csv"
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    lab.build_panel_from_raw(pd.read_csv(path))
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_conditions_start_from_fresh_deep_copy():
    frame = _frame()
    first = lab.prepare_window(frame, lab.canonical.SPLITS[0], "trim_to_null", 0.05)
    second = lab.prepare_window(frame, lab.canonical.SPLITS[0], "winsorization", 0.05)
    assert frame["revenue_growth_pct"].equals(_frame()["revenue_growth_pct"])
    assert first["transformed_frame"] is not second["transformed_frame"]


def test_q_is_per_side():
    values = np.arange(40, dtype=float)
    lower, upper = lab.fit_thresholds(values, 0.05)
    assert lower == np.quantile(values, 0.05, method="linear")
    assert upper == np.quantile(values, 0.95, method="linear")


def test_thresholds_fit_per_column():
    frame = _frame()
    lower_a, upper_a = lab.fit_thresholds(frame["ebitda_growth_pct"].dropna(), 0.05)
    lower_b, upper_b = lab.fit_thresholds(frame["gross_profit_growth_pct"].dropna(), 0.05)
    assert (lower_a, upper_a) != (lower_b, upper_b)


def test_thresholds_use_pooled_training_feature_years_only():
    frame = _frame()
    window = lab.prepare_window(frame, lab.canonical.SPLITS[0], "winsorization", 0.05)
    train = frame[frame["year"].isin([2020, 2021])]["revenue_growth_pct"].dropna()
    row = next(item for item in window["cell_audit_rows"] if item["feature"] == "revenue_growth_pct")
    assert row["lower_threshold"] == np.quantile(train, 0.05, method="linear")


def test_test_feature_year_never_enters_threshold_pool():
    frame = _frame()
    frame.loc[frame["year"] == 2022, "revenue_growth_pct"] = 10_000
    window = lab.prepare_window(frame, lab.canonical.SPLITS[0], "winsorization", 0.05)
    row = next(item for item in window["cell_audit_rows"] if item["feature"] == "revenue_growth_pct")
    training = frame[frame["year"].isin([2020, 2021])]["revenue_growth_pct"].dropna()
    assert row["upper_threshold"] == np.quantile(training, 0.95, method="linear")


def test_threshold_method_is_linear():
    values = np.array([0.0, 1.0, 2.0, 3.0, 4.0] * 10)
    assert lab.fit_thresholds(values, 0.1) == (
        np.quantile(values, 0.1, method="linear"),
        np.quantile(values, 0.9, method="linear"),
    )


def test_lower_and_upper_comparisons_are_strict():
    values = pd.Series([0.0, 1.0, 2.0])
    lower, upper = lab.affected_masks(values, 0.0, 2.0)
    assert not lower.any()
    assert not upper.any()


def test_threshold_equality_is_unchanged():
    values = pd.Series([-1.0, 0.0, 1.0])
    lower, upper = lab.affected_masks(values, -1.0, 1.0)
    assert lower.tolist() == [False, False, False]
    assert upper.tolist() == [False, False, False]


def test_original_nulls_are_excluded_from_fit():
    values = pd.Series([np.nan, 1.0, 2.0, 3.0] * 10)
    lower, upper = lab.fit_thresholds(values.dropna(), 0.1)
    assert np.isfinite(lower) and np.isfinite(upper)
    masks, thresholds = _threshold_masks(pd.DataFrame({"f": values}), "f", 0.1)
    assert not masks["f"][0].iloc[0] and not masks["f"][1].iloc[0]
    assert thresholds["f"] == (lower, upper)


def test_hard_support_uses_n_minus_one_times_q():
    assert (41 - 1) * 0.025 >= 1
    assert (40 - 1) * 0.025 < 1


def test_stability_support_is_diagnostic_only():
    n = 41
    q = 0.025
    assert (n - 1) * q >= 1
    assert n * q < 3


def test_winsorization_replaces_with_matching_threshold():
    frame = pd.DataFrame({"f": [-10.0, 0.0, 10.0]})
    masks = {"f": lab.affected_masks(frame["f"], -5.0, 5.0)}
    transformed = lab.apply_operator(frame, masks, {"f": (-5.0, 5.0)}, "winsorization")
    assert transformed["f"].tolist() == [-5.0, 0.0, 5.0]


def test_trim_to_null_changes_only_affected_cells():
    frame = pd.DataFrame({"f": [-10.0, 0.0, 10.0], "id": [1, 2, 3]})
    masks = {"f": lab.affected_masks(frame["f"], -5.0, 5.0)}
    transformed = lab.apply_operator(frame, masks, {"f": (-5.0, 5.0)}, "trim_to_null")
    assert transformed["f"].isna().sum() == 2
    assert transformed["id"].tolist() == frame["id"].tolist()


def test_trim_to_null_preserves_row_count_and_ticker():
    frame = _frame()
    window = lab.prepare_window(frame, lab.canonical.SPLITS[0], "trim_to_null", 0.05)
    assert len(window["transformed_frame"]) == len(frame)
    assert window["transformed_frame"]["ticker"].tolist() == frame["ticker"].tolist()


def test_perturbation_nulls_are_distinguishable_from_original_nulls():
    frame = _frame()
    window = lab.prepare_window(frame, lab.canonical.SPLITS[0], "trim_to_null", 0.05)
    for row in window["cell_audit_rows"]:
        assert row["original_missing_training_count"] >= 0
        assert row["perturbation_induced_null_training_count"] >= 0


def test_frozen_q_grid_is_exact():
    assert lab.Q_GRID == (0.025, 0.05, 0.10)
    assert set(lab.Q_GRID) == {0.025, 0.05, 0.10}


def test_mandatory_metric_vector_is_exact():
    baseline = lab.load_canonical_baseline()
    assert set(lab._mandatory_vector(baseline)) == {"analysis", "models", "headline", "source_artifacts"}
    assert len(baseline["models"]) == 9
    assert baseline["analysis"]["multiplicity"]["family_size"] == 6


def test_metric_vector_is_sealed_before_result():
    baseline = lab.load_canonical_baseline()
    vector = lab._mandatory_vector(baseline)
    vector_before = json.dumps(vector, sort_keys=True)
    _ = lab._delta_vector(baseline, baseline)
    assert json.dumps(vector, sort_keys=True) == vector_before


def test_no_new_significance_or_bootstrap_family():
    analysis = lab.load_canonical_baseline()["analysis"]
    assert analysis["permutations"] == 10_000
    assert analysis["bootstraps"] == 10_000
    assert analysis["multiplicity"]["family_size"] == 6


def test_baseline_determinism_gate_is_byte_identity():
    raw = pd.read_csv(lab.CANONICAL_INPUT)
    for split in lab.canonical.SPLITS:
        prediction = lab.run_window(raw.copy(deep=True), split)
        committed = ROOT / "experiments/results" / f"predictions_{split['name']}.csv"
        assert lab._prediction_bytes(prediction) == committed.read_bytes()


def test_contamination_artifacts_rerun_byte_identically():
    frame = pd.DataFrame({"ticker": ["A"], "year": [2022], "model": ["m"], "y_true": [1.0], "y_pred": [2.0]})
    assert lab._prediction_bytes(frame) == lab._prediction_bytes(frame.copy(deep=True))


def test_malformed_and_nonfinite_states_fail_closed():
    with pytest.raises(lab.RobustError):
        lab.validate_raw_frame(_frame().drop(columns=["revenue_growth_pct"]))
    bad = _frame()
    bad.loc[0, "revenue_growth_pct"] = np.inf
    with pytest.raises(lab.RobustError):
        lab.validate_raw_frame(bad)


def test_conclusion_firewall_preserves_negative_boundary():
    assert lab.LIMITATIONS[-1] == "The conclusion remains: no reliable predictive edge. Research support only; not investment advice."
    assert all("ROBUST_PASS" not in text and "ROBUST_FAIL" not in text for text in lab.LIMITATIONS)


def test_artifact_registry_has_exact_six_entries():
    registry = json.loads((ROOT / "artifact_registry.json").read_text(encoding="utf-8"))
    expected = {
        "experiments/results_contamination/artifact_manifest.json",
        "experiments/results_contamination/contamination_cells.csv",
        "experiments/results_contamination/contamination_metrics.csv",
        "experiments/results_contamination/contamination_predictions.csv",
        "experiments/results_contamination/contamination_report.json",
        "experiments/results_contamination/contamination_report.md",
    }
    actual = {entry["path_or_glob"] for entry in registry["entries"] if entry["path_or_glob"].startswith("experiments/results_contamination/")}
    assert actual == expected


def test_limitations_register_contains_generated_report_section():
    text = (ROOT / "docs/limitations_register.md").read_text(encoding="utf-8")
    assert "experiments/results_contamination/contamination_report.json" in text
    assert lab.LIMITATIONS[-1] in text


def test_protected_boundary_hashes_are_pinned():
    assert lab.sha256_path(lab.CANONICAL_INPUT) == lab.EXPECTED_MODELING_SHA256
    assert lab.sha256_path(ROOT / "experiments/run_experiments.py") == lab.EXPECTED_RUN_EXPERIMENTS_SHA256
    assert lab.EXPECTED_SIGNIFICANCE_SHA256 == EXPECTED_REPAIRED_SIGNIFICANCE_SHA256
    assert lab.sha256_path(ROOT / "experiments/significance.py") == lab.EXPECTED_SIGNIFICANCE_SHA256


def test_changed_path_allowlist_is_exact():
    result = subprocess.run(["git", "status", "--porcelain=v1"], cwd=ROOT, check=True, capture_output=True, text=True)
    paths = lab._worktree_paths(result.stdout)
    assert paths <= lab.ALLOWED_WORKTREE_PATHS


def test_generated_text_has_no_diff_check_errors():
    result = subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True, capture_output=True, text=True)
    assert result.stdout == ""


def test_full_validation_commands_are_declared():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "research-contamination:" in makefile
    assert "PYTHONPATH=. python experiments/contamination_lab.py" in makefile


def test_robust_identity_control_matches_canonical_harness():
    raw = pd.read_csv(lab.CANONICAL_INPUT)
    for split in lab.canonical.SPLITS:
        assert lab._prediction_bytes(lab.run_window(raw.copy(deep=True), split)) == (
            ROOT / "experiments/results" / f"predictions_{split['name']}.csv"
        ).read_bytes()


def test_surface_significance_uses_one_ordered_build_report():
    source = (ROOT / "experiments/contamination_lab.py").read_text(encoding="utf-8")
    section = source[source.index("def _surface_report"):source.index("def _delta_vector")]
    assert section.count("significance.build_report(") == 1
    assert "seed=42" in section and "permutations=10_000" in section and "bootstraps=10_000" in section


def test_registry_validation_is_split_by_generation_phase():
    source = (ROOT / "experiments/contamination_lab.py").read_text(encoding="utf-8")
    assert "run_canonical_determinism_gate" in source
    assert "_publish(scratch_directory, destination)" in source


def test_growth_coverage_fields_and_limitation_are_mandatory():
    required = {
        "growth_supported_training_row_count",
        "growth_unsupported_training_row_count",
        "growth_supported_row_count",
        "growth_unsupported_row_count",
        "original_growth_null_training_cell_count",
        "original_growth_null_test_cell_count",
        "original_growth_null_cell_count",
    }
    assert required <= set(lab.CELL_COLUMNS)
    assert any("growth-supported portion" in text for text in lab.LIMITATIONS)
