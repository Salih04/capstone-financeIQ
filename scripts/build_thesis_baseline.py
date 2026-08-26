"""Freeze the pre-thesis scientific baseline as a machine-readable record.

This script **reads** governed artifacts and **copies** the numbers they already
contain.  It runs no model, fits nothing, and re-derives no statistic: every
scientific value below is transcribed from an artifact that an existing
governed Make target produced.  Its job is provenance, not analysis.

The record exists so that later MSc-thesis work can be compared against a
fixed, hash-verified description of the repository's pre-thesis state.  It
writes to ``docs/thesis/baseline/`` and never touches ``experiments/results*``.

The emitted JSON carries a top-level ``source_artifacts`` list, so
``tests/test_artifact_registry.py::test_embedded_source_artifact_checksums_are_current``
re-hashes every frozen input on each test run.  That makes the freeze
self-verifying: if a governed input drifts, the suite fails and names the file.

The record is descriptive research provenance only.  It certifies no predictive
edge, no investment value, and no methodological validity.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "docs" / "thesis" / "baseline"
JSON_PATH = OUTPUT_DIR / "pre_thesis_baseline.json"
MARKDOWN_PATH = OUTPUT_DIR / "pre_thesis_baseline.md"

MODELING_DATASET = ROOT / "data" / "trusted_clean" / "modeling_dataset_training_2020_2025.csv"
ALTERNATIVE_TARGETS = ROOT / "data" / "trusted_clean" / "modeling_targets_alternative.csv"
SIGNIFICANCE_REPORT = ROOT / "experiments" / "results" / "significance_report.json"
EXCESS_SIGNIFICANCE = ROOT / "experiments" / "results_excess" / "significance_report.json"
LEADERBOARD_BY_TARGET = ROOT / "experiments" / "results" / "leaderboard_by_target.csv"

# Inputs whose bytes define this freeze. Recorded with role + sha256 so the
# registry staleness test re-verifies them on every run of the root suite.
FROZEN_INPUTS: list[tuple[Path, str]] = [
    (MODELING_DATASET, "canonical T->T+1 modeling dataset (features and targets)"),
    (ALTERNATIVE_TARGETS, "derived real-TRY and USD target bases"),
    (SIGNIFICANCE_REPORT, "nominal-TRY walk-forward significance and power report"),
    (EXCESS_SIGNIFICANCE, "excess-return-basis significance report"),
    (LEADERBOARD_BY_TARGET, "per-target walk-forward leaderboard"),
]

UNIVERSE_LIMITATIONS = [
    "The cohort is a retrospectively fixed repository universe, not verified "
    "point-in-time BIST100 membership; survivorship and membership-timing "
    "effects are present and unquantified.",
    "The `sector` column exists in the schema but is empty for every row, so no "
    "sector-neutral or sector-controlled analysis is possible at this baseline.",
    "Three test years at 40-80 evaluated rows per model-year is a small-sample "
    "design; the minimum detectable |IC| is large relative to any effect size "
    "plausibly present in equity cross-sections.",
    "Annual T->T+1 frequency yields at most one observation per ticker-year, "
    "which is the binding constraint on statistical power.",
    "The evaluation window covers one unusual Turkish macro regime (high and "
    "volatile inflation), so a null result is not a general market-efficiency "
    "claim and does not transfer to other regimes or markets.",
    "Reproducibility is numerical-environment-qualified: byte identity requires "
    "the recorded interpreter and package versions.",
]


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def describe_file(path: Path, role: str | None = None) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256_path(path),
        "size_bytes": path.stat().st_size,
    }
    if role is not None:
        entry["role"] = role
    return entry


def dataset_facts() -> dict[str, Any]:
    """Shape, coverage, and target-column facts read from the modeling dataset."""
    from experiments import run_experiments as exp

    frame = pd.read_csv(MODELING_DATASET)
    feature_columns = exp._feature_cols(frame)
    target_columns = [c for c in frame.columns if c.startswith("next_year_")]

    return {
        "path": str(MODELING_DATASET.relative_to(ROOT)),
        "sha256": sha256_path(MODELING_DATASET),
        "size_bytes": MODELING_DATASET.stat().st_size,
        "row_count": int(len(frame)),
        "column_count": int(frame.shape[1]),
        "ticker_count": int(frame["ticker"].nunique()),
        "feature_year_span": [int(frame["year"].min()), int(frame["year"].max())],
        "feature_count": len(feature_columns),
        "feature_columns": feature_columns,
        "target_count": len(target_columns),
        "target_columns": target_columns,
        "modeled_target_count": len(exp.TARGETS),
        "modeled_target_columns": list(exp.TARGETS),
        "rows_with_primary_target": int(frame["next_year_return_pct"].notna().sum()),
        "inference_only_rows": int(frame["is_inference_row"].sum()),
        "target_nonnull_counts": {
            column: int(frame[column].notna().sum()) for column in target_columns
        },
    }


def sector_coverage() -> dict[str, Any]:
    """Sector-field population, stated exactly as observed (no imputation)."""
    frame = pd.read_csv(MODELING_DATASET)
    populated = int(frame["sector"].notna().sum())
    index_membership = int(frame["indices"].notna().sum())
    varying = int(
        (frame.dropna(subset=["indices"]).groupby("ticker")["indices"].nunique() > 1).sum()
    )
    return {
        "sector_column_present": "sector" in frame.columns,
        "sector_populated_rows": populated,
        "sector_total_rows": int(len(frame)),
        "sector_distinct_values": sorted(frame["sector"].dropna().unique().tolist()),
        "usable_for_analysis": populated > 0,
        "indices_column_populated_rows": index_membership,
        "indices_tickers_varying_across_years": varying,
        "note": (
            "The sector column is empty for every row. The indices column carries "
            "BIST index membership strings and is not a sector classification; it "
            "is additionally identical across all years for every ticker, i.e. a "
            "retrospective snapshot rather than point-in-time membership. Neither "
            "field supports sector-controlled analysis at this baseline, and no "
            "sector value is imputed."
        ),
    }


def significance_facts() -> dict[str, Any]:
    """Per-model observed ICs and p-values, transcribed from the report."""
    report = json.loads(SIGNIFICANCE_REPORT.read_text(encoding="utf-8"))

    def summarize(entry: dict[str, Any]) -> dict[str, Any]:
        pooled = entry["pooled"]
        return {
            "model": entry["model"],
            "kind": entry["kind"],
            "pooled_observed_ic": pooled["observed_ic"],
            "pooled_n": pooled["n"],
            "split_count": pooled["split_count"],
            "raw_permutation_p_value_two_sided": pooled["permutation_p_value_two_sided"],
            "bonferroni_adjusted_p_value": pooled["bonferroni_adjusted_p_value"],
            "bootstrap_ci_95": pooled["bootstrap_ci_95"],
            "significant_fwer_0_05": pooled["significant_fwer_0_05"],
        }

    models = [summarize(entry) for entry in report["models"]]
    return {
        "statistic": report["analysis"]["statistic"],
        "permutation_scheme": report["analysis"]["permutation"],
        "bootstrap_scheme": report["analysis"]["bootstrap"],
        "permutations": report["analysis"]["permutations"],
        "bootstraps": report["analysis"]["bootstraps"],
        "seed": report["analysis"]["seed"],
        "evaluated_tickers_per_model_split": report["analysis"][
            "evaluated_tickers_per_model_split"
        ],
        "multiplicity_correction": "Bonferroni across the six ML models",
        "ml_family_size": sum(1 for m in models if m["kind"] == "ml"),
        "baseline_models": [m for m in models if m["kind"] == "baseline"],
        "ml_models": [m for m in models if m["kind"] == "ml"],
        "headline": report["headline"],
        "limitations": report["limitations"],
    }


def power_facts() -> dict[str, Any]:
    """MDE and power values, transcribed from the report's power analysis."""
    power = json.loads(SIGNIFICANCE_REPORT.read_text(encoding="utf-8"))["power_analysis"]
    return {
        "method": power["method"],
        "alpha_two_sided": power["alpha_two_sided"],
        "target_power": power["target_power"],
        "multiplicity_scope": power["multiplicity_scope"],
        "designs": [
            {
                "design_id": design["design_id"],
                "scope": design["scope"],
                "n_per_split": design["n_per_split"],
                "split_count": design["split_count"],
                "total_evaluated_rows": design["total_evaluated_rows"],
                "analytic_minimum_detectable_abs_ic": design[
                    "analytic_minimum_detectable_abs_ic"
                ],
                "simulated_power_at_analytic_mde": design["simulated_power_at_analytic_mde"],
            }
            for design in power["designs"]
        ],
        "projection_40_tickers_per_year": power["projection_40_tickers_per_year"],
        "limitations": power["limitations"],
    }


def target_bases() -> list[dict[str, Any]]:
    """The return bases already evaluated by governed targets."""
    excess = json.loads(EXCESS_SIGNIFICANCE.read_text(encoding="utf-8"))
    return [
        {
            "basis_id": "nominal_try",
            "target_column": "next_year_return_pct",
            "label": "Nominal TRY total return, T->T+1",
            "results_root": "experiments/results",
            "generator_command": "make research",
            "status": "evaluated",
        },
        {
            "basis_id": "excess_vs_bist100",
            "target_column": "next_year_excess_return_vs_bist100",
            "label": "Excess return vs BIST100 (nominal TRY, percentage points)",
            "results_root": "experiments/results_excess",
            "generator_command": "make research-excess",
            "status": "evaluated",
            "headline_conclusion": excess.get("headline", {}).get("conclusion"),
        },
        {
            "basis_id": "real_try",
            "target_column": "next_year_real_return_pct",
            "label": "CPI-deflated real TRY return",
            "results_root": "experiments/results_real_terms/real_try",
            "generator_command": "make research-real-terms",
            "status": "evaluated",
        },
        {
            "basis_id": "usd",
            "target_column": "next_year_usd_return_pct",
            "label": "USD-converted return",
            "results_root": "experiments/results_real_terms/usd",
            "generator_command": "make research-real-terms",
            "status": "evaluated",
        },
    ]


def build_record() -> dict[str, Any]:
    from experiments import run_experiments as exp

    significance = significance_facts()
    return {
        "schema_version": "1.0.0",
        "record_id": "FINANCEIQ_PRE_THESIS_BASELINE",
        "purpose": (
            "Frozen, hash-verified description of the repository's scientific state "
            "immediately before MSc-thesis experiments begin. Every value is "
            "transcribed from a governed artifact; nothing here is recomputed, "
            "reinterpreted, or newly estimated."
        ),
        "claim_safety": {
            "descriptive_research_evidence_only": True,
            "reliable_predictive_edge_established": False,
            "investment_value_established": False,
            "statement": (
                "This record is research provenance. It establishes no predictive "
                "edge and no investment value, and is not investment advice."
            ),
        },
        "git": {
            "sha": git_sha(),
            "note": (
                "The commit observed when this record was generated. The commit that "
                "stores the record is necessarily its child."
            ),
        },
        "dataset": dataset_facts(),
        "design": {
            "frequency": "annual T->T+1",
            "test_years": sorted({split["test_feature_year"] + 1 for split in exp.SPLITS}),
            "splits": [
                {
                    "name": split["name"],
                    "train_target_years": split["train_target_years"],
                    "test_feature_year": split["test_feature_year"],
                    "test_target_year": split["test_feature_year"] + 1,
                }
                for split in exp.SPLITS
            ],
            "ml_models": [name for name, (kind, _) in exp.MODELS.items() if kind == "ml"],
            "baseline_models": [
                name for name, (kind, _) in exp.MODELS.items() if kind == "baseline"
            ],
        },
        "significance": significance,
        "power": power_facts(),
        "target_bases": target_bases(),
        "sector_coverage": sector_coverage(),
        "universe_limitations": UNIVERSE_LIMITATIONS,
        "source_artifacts": [describe_file(path, role) for path, role in FROZEN_INPUTS],
    }


def render_markdown(record: dict[str, Any]) -> str:
    dataset = record["dataset"]
    significance = record["significance"]
    lines = [
        "# Pre-Thesis Scientific Baseline (frozen)",
        "",
        "Generated by `make thesis-baseline`. Do not hand-edit.",
        "",
        record["purpose"],
        "",
        f"**Observed at git SHA:** `{record['git']['sha']}`",
        "",
        "## Dataset",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Modeling dataset | `{dataset['path']}` |",
        f"| SHA256 | `{dataset['sha256']}` |",
        f"| Rows | {dataset['row_count']} |",
        f"| Tickers | {dataset['ticker_count']} |",
        f"| Features | {dataset['feature_count']} |",
        f"| Target columns present | {dataset['target_count']} |",
        f"| Targets modeled | {dataset['modeled_target_count']} |",
        f"| Rows with primary target | {dataset['rows_with_primary_target']} |",
        f"| Inference-only rows | {dataset['inference_only_rows']} |",
        f"| Feature-year span | {dataset['feature_year_span'][0]}–{dataset['feature_year_span'][1]} |",
        f"| Test years | {', '.join(str(y) for y in record['design']['test_years'])} |",
        "",
        "## Pooled walk-forward ICs",
        "",
        "Statistic: " + significance["statistic"] + ".",
        "",
        "| Model | Kind | Pooled IC | Raw p (two-sided) | Bonferroni p | Significant at FWER 0.05 |",
        "|---|---|---|---|---|---|",
    ]
    for entry in significance["baseline_models"] + significance["ml_models"]:
        adjusted = entry["bonferroni_adjusted_p_value"]
        significant = entry["significant_fwer_0_05"]
        lines.append(
            f"| {entry['model']} | {entry['kind']} | {entry['pooled_observed_ic']:.6f} | "
            f"{entry['raw_permutation_p_value_two_sided']:.6f} | "
            f"{'n/a' if adjusted is None else f'{adjusted:.6f}'} | "
            f"{'n/a' if significant is None else significant} |"
        )
    lines += [
        "",
        "Baselines are reported without Bonferroni adjustment because the "
        "correction family is defined over the six ML models only.",
        "",
        "## Headline",
        "",
        f"- Selected model: `{significance['headline']['model']}` "
        f"({significance['headline']['selection']})",
        f"- Observed IC: {significance['headline']['observed_ic']:.6f}",
        f"- Raw permutation p: {significance['headline']['permutation_p_value_two_sided']:.6f}",
        f"- Bonferroni-adjusted p: {significance['headline']['bonferroni_adjusted_p_value']:.6f}",
        f"- Significant at FWER 0.05: {significance['headline']['significant_fwer_0_05']}",
        "",
        f"> {significance['headline']['conclusion']}",
        "",
        "## Power / minimum detectable effect",
        "",
        "| Design | Scope | n/split | Splits | MDE \\|IC\\| at 80% power |",
        "|---|---|---|---|---|",
    ]
    for design in record["power"]["designs"]:
        lines.append(
            f"| {design['design_id']} | {design['scope']} | {design['n_per_split']} | "
            f"{design['split_count']} | {design['analytic_minimum_detectable_abs_ic']:.6f} |"
        )
    lines += [
        "",
        "## Target bases evaluated",
        "",
        "| Basis | Target column | Results root | Generator |",
        "|---|---|---|---|",
    ]
    for basis in record["target_bases"]:
        lines.append(
            f"| {basis['basis_id']} | `{basis['target_column']}` | "
            f"`{basis['results_root']}` | `{basis['generator_command']}` |"
        )
    lines += [
        "",
        "## Sector coverage",
        "",
        f"- `sector` populated rows: {record['sector_coverage']['sector_populated_rows']}"
        f" / {record['sector_coverage']['sector_total_rows']}",
        f"- Usable for analysis: {record['sector_coverage']['usable_for_analysis']}",
        "",
        record["sector_coverage"]["note"],
        "",
        "## Known universe limitations",
        "",
    ]
    lines += [f"- {item}" for item in record["universe_limitations"]]
    lines += [
        "",
        "## Frozen input checksums",
        "",
        "| Path | SHA256 | Bytes |",
        "|---|---|---|",
    ]
    for item in record["source_artifacts"]:
        lines.append(f"| `{item['path']}` | `{item['sha256']}` | {item['size_bytes']} |")
    lines += [
        "",
        record["claim_safety"]["statement"],
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    record = build_record()
    JSON_PATH.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    MARKDOWN_PATH.write_text(render_markdown(record), encoding="utf-8")
    print(f"[thesis-baseline] wrote {JSON_PATH.relative_to(ROOT)}")
    print(f"[thesis-baseline] wrote {MARKDOWN_PATH.relative_to(ROOT)}")
    print(f"[thesis-baseline] git sha: {record['git']['sha']}")
    print(f"[thesis-baseline] dataset sha256: {record['dataset']['sha256']}")


if __name__ == "__main__":
    main()
