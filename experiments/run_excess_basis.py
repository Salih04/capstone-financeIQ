"""Run the existing walk-forward and significance machinery on the excess-return target.

The target column ``next_year_excess_return_vs_bist100`` already lives in the
canonical modeling dataset (leaderboard-level treatment exists in
``experiments/results/leaderboard_by_target.csv``); this runner adds the same
prediction-dump + significance treatment the currency bases received in
R2-REAL-01.  Outputs are isolated under ``experiments/results_excess``.
Canonical nominal prediction dumps, reports, and leaderboards are read-only for
this run.  Benchmark-relative coverage shrinks the evaluated panel; missing
excess targets remain null and are never filled.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd

from scripts.data_collection import derive_alternative_targets as alt
from experiments import run_experiments as exp
from experiments import significance
from experiments.run_alternative_targets import _prediction_rows

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "experiments" / "results_excess"
TARGET_COLUMN = "next_year_excess_return_vs_bist100"
BASIS_ID = "excess_vs_bist100"
BASIS_LABEL = "Excess return vs BIST100 (nominal TRY, percentage points)"
NOMINAL_ROWS_PER_TEST_YEAR = 80

BASIS_LIMITATION = (
    "Excess returns subtract the BIST100 nominal TRY index return within one "
    "unusual macro regime; they are a descriptive benchmark-relative basis and "
    "do not represent an implementable benchmark-hedged position or investment value."
)
COVERAGE_LIMITATION = (
    "BIST100 benchmark-relative coverage exists for only part of the evaluation "
    "panel; rows without a valid excess target remain null and shrink the "
    "evaluated n per year rather than being filled."
)

# Excess-specific overclaims layered on top of the shared alternative-target
# validator: the misquote to pre-kill is any "signal vs the benchmark" reading
# of an uncorrected or per-split excess IC.
_UNSAFE_EXCESS_CLAIMS = (
    re.compile(r"\bsignal (?:vs|versus|against) (?:the )?(?:bist100 )?benchmark\b", re.I),
    re.compile(r"\bbeats? the (?:bist100 )?(?:benchmark|index|market)\b", re.I),
    re.compile(r"\boutperform(?:s|ed)? the bist100\b", re.I),
    re.compile(r"\bbenchmark-beating\b", re.I),
    re.compile(r"\balpha (?:was )?(?:found|generated|captured|delivered)\b", re.I),
)


def validate_excess_claim_safety_text(text: str) -> None:
    """Reject benchmark-relative performance interpretations of the excess basis."""
    alt.validate_claim_safety_text(text)
    for pattern in _UNSAFE_EXCESS_CLAIMS:
        if pattern.search(text):
            raise ValueError(f"Unsafe excess-basis claim: {pattern.pattern}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _evaluated_rows_per_year(predictions: pd.DataFrame) -> dict[int, int]:
    """Evaluated rows per target year, required to be uniform across models."""
    per_year: dict[int, int] = {}
    for year, group in predictions.groupby("year", sort=True):
        counts = sorted(group.groupby("model").size().unique().tolist())
        if len(counts) != 1:
            raise ValueError(
                f"evaluated rows differ across models for year {year}: {counts}"
            )
        per_year[int(year)] = int(counts[0])
    return per_year


def run() -> tuple[Path, Path]:
    panel, feature_cols = exp.build_panel_for_target(TARGET_COLUMN)
    if panel is None:
        raise ValueError(f"no usable rows for {TARGET_COLUMN}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    leaderboard_rows = []
    for split in exp.SPLITS:
        predictions, leaderboard = _prediction_rows(panel, feature_cols, split)
        pd.DataFrame(
            predictions, columns=significance.REQUIRED_COLUMNS
        ).to_csv(
            OUTPUT_DIR / f"predictions_{split['name']}.csv",
            index=False,
            float_format="%.17g",
            lineterminator="\n",
        )
        leaderboard_rows.extend(leaderboard)
    pd.DataFrame(leaderboard_rows).to_csv(
        OUTPUT_DIR / "leaderboard.csv", index=False, lineterminator="\n"
    )

    prediction_frame, sources = significance.load_prediction_dumps(OUTPUT_DIR)
    per_year = _evaluated_rows_per_year(prediction_frame)
    report = significance.build_report(prediction_frame, sources)
    report["task"] = "R3-TGT-01"
    report["target_basis"] = {
        "id": BASIS_ID,
        "label": BASIS_LABEL,
        "target_column": TARGET_COLUMN,
        "modeling_dataset_path": exp._modeling_csv().relative_to(ROOT).as_posix(),
        "modeling_dataset_sha256": _sha256(exp._modeling_csv()),
        "evaluated_rows_per_year": per_year,
        "nominal_basis_rows_per_test_year_context": NOMINAL_ROWS_PER_TEST_YEAR,
        "coverage_note": (
            "Benchmark-relative coverage shrinks the evaluated panel relative to "
            "the nominal basis; missing excess targets remain null and are never filled."
        ),
    }
    report["limitations"] = [
        BASIS_LIMITATION if item.startswith("Nominal TRY returns cover") else item
        for item in report["limitations"]
    ]
    report["limitations"].append(COVERAGE_LIMITATION)
    report["claim_safety"] = {
        "descriptive_research_evidence_only": True,
        "investment_value_established": False,
        "reliable_predictive_edge_established": False,
        "benchmark_relative_signal_established": False,
        "multiplicity_gate": "Bonferroni across the same six-model ML family",
        "statement": (
            "Descriptive historical research result on a benchmark-relative basis; "
            "it does not establish signal, investment value, or a reliable "
            "predictive edge, and the nominal TRY conclusion is unchanged."
        ),
    }

    json_path = OUTPUT_DIR / "significance_report.json"
    markdown_path = OUTPUT_DIR / "significance_report.md"
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    coverage_lines = [
        "| Test year | Evaluated rows (excess basis) | Nominal-basis rows (context) |",
        "| ---: | ---: | ---: |",
        *[
            f"| {year} | {rows} | {NOMINAL_ROWS_PER_TEST_YEAR} |"
            for year, rows in sorted(per_year.items())
        ],
    ]
    prefix = (
        f"# {BASIS_LABEL} evaluation (R3-TGT-01)\n\n"
        "Descriptive historical research evidence only; not investment value or investment advice. "
        "The nominal TRY evaluation remains the canonical headline and is not replaced.\n\n"
        f"Target: `{TARGET_COLUMN}` — the nominal TRY return minus the BIST100 nominal TRY "
        "index return, in percentage points. Benchmark-relative coverage shrinks the "
        "evaluated panel; rows without a valid excess target remain null and are never "
        "filled. Evaluated rows per test year:\n\n" + "\n".join(coverage_lines) + "\n\n"
    )
    closing = (
        "\nThis excess-return-basis evaluation is a descriptive historical research "
        "result; it does not establish signal, investment value, or a reliable "
        "predictive edge. Any isolated split or uncorrected p-value remains "
        "exploratory and must not be promoted as a finding.\n"
    )
    markdown = prefix + significance.render_markdown(report) + closing
    validate_excess_claim_safety_text(markdown)
    markdown_path.write_text(markdown, encoding="utf-8")

    headline = report["headline"]
    print(
        f"[{BASIS_ID}] {headline['model']} pooled IC={headline['observed_ic']:.3f} "
        f"raw p={headline['permutation_p_value_two_sided']:.4f} "
        f"Bonferroni p={headline['bonferroni_adjusted_p_value']:.4f}"
    )
    print(headline["conclusion"])
    print("The canonical nominal TRY artifacts and conclusion are unchanged.")
    return json_path, markdown_path


if __name__ == "__main__":
    run()
