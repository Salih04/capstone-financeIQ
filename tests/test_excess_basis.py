"""Excess-return-basis significance treatment guards (R3-TGT-01).

The runner must reuse the canonical model family, splits, and seeded
significance machinery; report benchmark-coverage-reduced n explicitly with
nulls staying null; ship every quoted IC with raw AND Bonferroni-adjusted p;
and never emit benchmark-relative performance claims.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from experiments import run_alternative_targets, run_experiments, significance
from experiments import run_excess_basis as excess


def test_reuses_canonical_harness_and_significance_conventions() -> None:
    # Identity, not equality: the runner may not fork the scoring path.
    assert excess._prediction_rows is run_alternative_targets._prediction_rows
    assert excess.TARGET_COLUMN == "next_year_excess_return_vs_bist100"
    assert excess.TARGET_COLUMN in run_experiments.TARGETS
    assert excess.OUTPUT_DIR.name == "results_excess"
    assert excess.OUTPUT_DIR.parent.name == "experiments"


def test_panel_drops_null_excess_rows_without_filling(tmp_path: Path, monkeypatch) -> None:
    base = tmp_path / "training.csv"
    pd.DataFrame(
        [
            {"ticker": "A", "year": 2020, "feature": 1.0,
             "next_year_return_pct": 5.0, excess.TARGET_COLUMN: 2.0},
            {"ticker": "B", "year": 2020, "feature": 2.0,
             "next_year_return_pct": 6.0, excess.TARGET_COLUMN: None},
            {"ticker": "A", "year": 2021, "feature": 3.0,
             "next_year_return_pct": 7.0, excess.TARGET_COLUMN: -1.5},
            {"ticker": "B", "year": 2021, "feature": 4.0,
             "next_year_return_pct": 8.0, excess.TARGET_COLUMN: None},
        ]
    ).to_csv(base, index=False)
    monkeypatch.setattr(run_experiments, "TRAINING_MODELING", base)

    panel, features = run_experiments.build_panel_for_target(excess.TARGET_COLUMN)
    assert features == ["feature"]
    # Null excess rows shrink n; values are never imputed or borrowed.
    assert len(panel) == 2
    assert panel["ticker"].tolist() == ["A", "A"]
    assert panel["target_return"].tolist() == [2.0, -1.5]


def test_evaluated_rows_per_year_requires_uniform_model_coverage() -> None:
    frame = pd.DataFrame(
        {
            "year": [2023, 2023, 2024, 2024],
            "model": ["ridge", "lasso", "ridge", "lasso"],
            "ticker": ["A", "A", "A", "A"],
        }
    )
    # n is evaluated rows per model within each year (one per model here).
    assert excess._evaluated_rows_per_year(frame) == {2023: 1, 2024: 1}
    uneven = pd.concat(
        [frame, pd.DataFrame({"year": [2024], "model": ["ridge"], "ticker": ["B"]})],
        ignore_index=True,
    )
    with pytest.raises(ValueError, match="differ across models"):
        excess._evaluated_rows_per_year(uneven)


@pytest.mark.parametrize(
    "unsafe",
    [
        # Excess-specific misquotes the packet pre-kills.
        "We found a signal vs the benchmark.",
        "There is signal against the BIST100 benchmark.",
        "The model beats the benchmark.",
        "gradient_boosting outperforms the BIST100 after correction.",
        "A benchmark-beating result.",
        "Alpha was captured in the excess-return evaluation.",
        # Inherited alternative-target overclaims must stay rejected too.
        "We found a signal.",
        "This establishes a reliable predictive edge.",
        "The conversion creates investment value.",
        "This predicts future returns.",
    ],
)
def test_claim_safety_rejects_unsafe_excess_interpretations(unsafe: str) -> None:
    with pytest.raises(ValueError, match="Unsafe"):
        excess.validate_excess_claim_safety_text(unsafe)


def test_claim_safety_allows_the_required_qualifier() -> None:
    excess.validate_excess_claim_safety_text(
        "This excess-return-basis evaluation is a descriptive historical research "
        "result; it does not establish signal, investment value, or a reliable "
        "predictive edge."
    )


def test_generated_artifacts_preserve_claim_boundary_and_isolation() -> None:
    report_path = excess.OUTPUT_DIR / "significance_report.json"
    if not report_path.is_file():
        pytest.skip("generate with make research-excess")
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["task"] == "R3-TGT-01"
    assert report["target_basis"]["target_column"] == excess.TARGET_COLUMN

    # Isolation: every source artifact lives inside the excess results directory.
    for source in report["source_artifacts"]:
        assert source["path"].startswith("experiments/results_excess/"), source["path"]

    # Every quoted IC ships with raw AND Bonferroni-adjusted p inside the family.
    headline = report["headline"]
    assert headline["permutation_p_value_two_sided"] is not None
    assert headline["bonferroni_adjusted_p_value"] is not None
    for model in report["models"]:
        if model["kind"] == "ml":
            assert model["pooled"]["bonferroni_adjusted_p_value"] is not None
            assert model["pooled"]["significant_fwer_0_05"] is not None

    # Benchmark coverage shrinks n; the reduced per-year n is reported explicitly.
    per_year = report["target_basis"]["evaluated_rows_per_year"]
    assert sorted(per_year) == ["2023", "2024", "2025"]
    assert all(
        rows <= report["target_basis"]["nominal_basis_rows_per_test_year_context"]
        for rows in per_year.values()
    )

    claim_safety = report["claim_safety"]
    assert claim_safety["descriptive_research_evidence_only"] is True
    assert claim_safety["investment_value_established"] is False
    assert claim_safety["reliable_predictive_edge_established"] is False
    assert claim_safety["benchmark_relative_signal_established"] is False

    markdown = (excess.OUTPUT_DIR / "significance_report.md").read_text(encoding="utf-8")
    excess.validate_excess_claim_safety_text(markdown)
    assert "not investment value or investment advice" in markdown
    assert (
        "does not establish signal, investment value, or a reliable predictive edge"
        in markdown
    )
    assert "The nominal TRY evaluation remains the canonical headline" in markdown
