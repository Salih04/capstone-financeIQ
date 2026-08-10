"""R4-ROBUST-01 tail-handling sensitivity laboratory.

This module is deliberately isolated from the canonical experiment harness.
It reads the canonical modeling input, applies the packet's frozen cellwise
operators to fresh in-memory copies, and sends every surface through the
unchanged model and significance machinery.  It never edits canonical inputs
or committed baseline artifacts.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from experiments import run_experiments as canonical  # noqa: E402
from experiments import significance  # noqa: E402


TASK = "R4-ROBUST-01"
OUTPUT_DIR = ROOT / "experiments" / "results_contamination"
CANONICAL_INPUT = ROOT / "data" / "trusted_clean" / "modeling_dataset_training_2020_2025.csv"
QUALITY_REPORT = ROOT / "data" / "trusted_clean" / "data_quality_report.json"
BASELINE_REPORT = ROOT / "experiments" / "results" / "significance_report.json"
BASELINE_MARKDOWN = ROOT / "experiments" / "results" / "significance_report.md"
MODEL_CONFIDENCE_CONTRACT = ROOT / "model_confidence_contract.json"
PACKET_PATH = Path("/tmp/r4-robust-01-canonical-implementation-packet-v3.md")
DISCOVERY_PATH = Path("/tmp/r4-robust-01-discovery-report.md")
EVIDENCE_PATH = Path("/tmp/r4-robust-01-final-prepacket-evidence.md")

EXPECTED_PACKET_SHA256 = "f7f820efec50f84033de0e9567f848e9c8188d5038716fdc878d15387d8639fa"
EXPECTED_DISCOVERY_SHA256 = "71689d6c07605b4241c211998037657e0a286eef877ecd096736a71af2f8fd21"
EXPECTED_EVIDENCE_MARKER = "R4_ROBUST_01_PREPACKET_EVIDENCE: READY"
EXPECTED_HEAD = "dee3618d0ae75b33d852ba91a2d0a2c6492d3c62"
EXPECTED_RUN_EXPERIMENTS_SHA256 = "265f58678d522eea0c48fbccba415ed30b3e20abc6bb7ae0a8e33857c5feb543"
EXPECTED_SIGNIFICANCE_SHA256 = "5fe0e88f9742c32b94425c493a41661ff541b6f1cc21d3c758293a06f09017e6"
EXPECTED_MODELING_SHA256 = "3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78"
EXPECTED_QUALITY_SHA256 = "ec93ab788b453cf7d24850410f10435aab5fe9e17ca776409ec0149f2668f6f1"
EXPECTED_CONTRACT_SHA256 = "59e0fae3be8972e258891e723fd49cf13e36a7d16e918722a5a18b690c55d8f7"

ELIGIBLE_FEATURES = (
    "ebitda_growth_pct",
    "gross_profit_growth_pct",
    "net_income_growth_pct",
    "operating_income_growth_pct",
    "revenue_growth_pct",
)
Q_GRID = (0.025, 0.05, 0.10)
OPERATORS = ("winsorization", "trim_to_null")
PREDICTION_COLUMNS = ["ticker", "year", "model", "y_true", "y_pred"]
STRESS_PREDICTION_COLUMNS = [
    "surface_id",
    "window_condition_id",
    "operator",
    "q",
    "split",
    "ticker",
    "year",
    "model",
    "y_true",
    "y_pred",
]
CELL_COLUMNS = [
    "surface_id",
    "window_condition_id",
    "operator",
    "q",
    "split",
    "test_feature_year",
    "test_target_year",
    "training_target_years_json",
    "training_feature_years_json",
    "feature",
    "threshold_method",
    "lower_threshold",
    "upper_threshold",
    "n_training_nonnull",
    "training_row_count",
    "growth_supported_training_row_count",
    "growth_unsupported_training_row_count",
    "growth_supported_training_row_proportion",
    "growth_unsupported_training_row_proportion",
    "evaluated_row_count",
    "growth_supported_row_count",
    "growth_unsupported_row_count",
    "growth_supported_row_proportion",
    "growth_unsupported_row_proportion",
    "original_growth_null_training_cell_count",
    "original_growth_null_test_cell_count",
    "original_growth_null_cell_count",
    "hard_support_value",
    "hard_support_required",
    "hard_support_pass",
    "stability_support_value",
    "stability_support_required",
    "stability_diagnostic_pass",
    "original_missing_training_count",
    "original_missing_test_count",
    "lower_affected_training_count",
    "upper_affected_training_count",
    "lower_affected_test_count",
    "upper_affected_test_count",
    "lower_affected_training_proportion",
    "upper_affected_training_proportion",
    "lower_affected_test_proportion",
    "upper_affected_test_proportion",
    "affected_cell_count",
    "affected_cell_proportion",
    "perturbation_induced_null_training_count",
    "perturbation_induced_null_test_count",
    "row_count_before",
    "row_count_after",
    "target_immutable",
    "condition_status",
]
METRIC_COLUMNS = [
    "surface_id",
    "operator",
    "q",
    "metric_scope",
    "window_condition_id",
    "split",
    "year",
    "model",
    "kind",
    "n",
    "split_count",
    "observed_ic",
    "bootstrap_ci_95_low",
    "bootstrap_ci_95_high",
    "permutation_p_value_two_sided",
    "observed_null_percentile",
    "bonferroni_adjusted_p_value",
    "significant_fwer_0_05",
    "delta_observed_ic",
    "delta_n",
    "delta_split_count",
    "significance_verdict_changed",
]
REPORT_TOP_LEVEL_KEYS = [
    "schema_version",
    "task",
    "analysis_status",
    "scientific_purpose",
    "scientific_conclusion_boundary",
    "generated_by",
    "frozen_design",
    "determinism_gate",
    "source_artifacts",
    "canonical_baseline",
    "conditions",
    "supplementary",
    "limitations",
    "claim_safety",
]
TARGET_FIELDS = {
    "next_year_return_pct",
    "next_year_excess_return_vs_bist100",
    "next_year_outperform_bist100",
    "next_year_top_20pct_returner",
}
NON_FEATURE_COLUMNS = {
    "ticker",
    "company_name",
    "year",
    "sector",
    "indices",
    "is_bist100",
    "same_year_return_pct",
    "target_year",
    "has_target",
    "is_inference_row",
    "is_public_universe",
    "is_training_universe",
    "universe_source",
}
EXPECTED_OUTPUT_FILES = {
    "artifact_manifest.json",
    "contamination_cells.csv",
    "contamination_metrics.csv",
    "contamination_predictions.csv",
    "contamination_report.json",
    "contamination_report.md",
}
ALLOWED_WORKTREE_PATHS = {
    "experiments/contamination_lab.py",
    "tests/test_contamination_lab.py",
    "Makefile",
    "artifact_registry.json",
    "docs/VERIFICATION_BASELINE.md",
    "experiments/results_contamination/artifact_manifest.json",
    "experiments/results_contamination/contamination_cells.csv",
    "experiments/results_contamination/contamination_metrics.csv",
    "experiments/results_contamination/contamination_predictions.csv",
    "experiments/results_contamination/contamination_report.json",
    "experiments/results_contamination/contamination_report.md",
    "docs/limitations_register.md",
}
LIMITATIONS = [
    "This is a descriptive tail-handling sensitivity laboratory for eligible growth-percentage input cells; it does not detect corrupted data or establish that any cell is bad.",
    "Thresholds are per-feature, per-window quantiles estimated only from permitted training feature years; they are not a data-quality validation rule and do not establish causal validity.",
    "Winsorization and trim-to-null are applied only to fresh isolated copies; canonical/trusted datasets, targets, identifiers, provenance, flags, benchmark/context variables, and committed baseline artifacts are not perturbed.",
    "The frozen q grid is q={0.025,0.05,0.10} per side; hard support (n-1)q>=1 gates eligibility, while nq>=3 is diagnostic only.",
    "Existing within-year permutation/bootstrap and six-model Bonferroni arithmetic are reused descriptively; no new delta-IC significance family, bootstrap, or multiplicity correction is created.",
    "A nominally significant perturbed condition, if any, is a sensitivity finding requiring investigation, not evidence of predictive edge, alpha, profitability, causal validity, or production validity.",
    "Results are numerical-environment-qualified; byte identity is required within the same numerical environment and is not claimed across different environments.",
    "The internal significance scope is 80 evaluated tickers per model and split; public-40 framing is distinct and must not be combined with it.",
    "The canonical evaluation universe remains unchanged; only authoritative non-null cells in the frozen five-feature growth block are perturbable. Rows without growth support remain in canonical evaluation, unperturbed and neither dropped, synthesized, nor relabeled as contaminated. Coverage is reported per window; R4-ROBUST tests tail-handling sensitivity of the growth-supported portion of the canonical analysis, not universal contamination of every evaluated row.",
    "The conclusion remains: no reliable predictive edge. Research support only; not investment advice.",
]


class RobustError(RuntimeError):
    """A fail-closed R4-ROBUST validation error."""


class HardSupportError(RobustError):
    """A frozen threshold-support requirement was not met."""


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True, allow_nan=False)


def _relative_or_absolute(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _copy(value: Any) -> Any:
    return copy.deepcopy(value)


def _proportion(value: int, denominator: int) -> float | None:
    return None if denominator == 0 else float(value / denominator)


def _worktree_paths(status_text: str) -> set[str]:
    paths: set[str] = set()
    for line in status_text.splitlines():
        relative = line[3:].split(" -> ", 1)[-1]
        candidate = ROOT / relative
        if candidate.is_dir():
            paths.update(
                child.relative_to(ROOT).as_posix()
                for child in candidate.rglob("*")
                if child.is_file()
            )
        else:
            paths.add(relative)
    return paths


def _bool_csv(value: Any) -> Any:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, (bool, np.bool_)):
        return "true" if bool(value) else "false"
    return value


def _write_csv(frame: pd.DataFrame, path: Path, columns: list[str]) -> None:
    output = frame.loc[:, columns].copy()
    for column in output.columns:
        if output[column].dtype == bool:
            output[column] = output[column].map(_bool_csv)
    path.write_text(
        output.to_csv(index=False, float_format="%.17g", lineterminator="\n"),
        encoding="utf-8",
        newline="",
    )


def _feature_columns(frame: pd.DataFrame) -> list[str]:
    return [
        column
        for column in frame.columns
        if column not in NON_FEATURE_COLUMNS and not column.startswith("next_year_")
    ]


def validate_raw_frame(frame: pd.DataFrame) -> None:
    """Validate the source contract before any perturbation is constructed."""
    ordered = [column for column in frame.columns if column in ELIGIBLE_FEATURES]
    if ordered != list(ELIGIBLE_FEATURES) or set(ordered) != set(ELIGIBLE_FEATURES):
        raise RobustError(
            "eligible growth columns must be the exact frozen ordered five-column list"
        )
    missing = sorted({"ticker", "year", "next_year_return_pct"} - set(frame.columns))
    if missing:
        raise RobustError(f"source is missing required columns: {missing}")
    if frame.duplicated(["ticker", "year"]).any():
        raise RobustError("source contains duplicate (ticker, year) keys")
    if frame["ticker"].isna().any() or frame["year"].isna().any():
        raise RobustError("source contains null identifiers")
    try:
        years = pd.to_numeric(frame["year"], errors="raise")
        if not np.isfinite(years.to_numpy(dtype=float)).all():
            raise RobustError("source year contains non-finite values")
    except (TypeError, ValueError) as exc:
        raise RobustError(f"source year is not numeric: {exc}") from exc
    numeric_columns = [column for column in frame.columns if column in TARGET_FIELDS or column in ELIGIBLE_FEATURES]
    for column in numeric_columns:
        values = pd.to_numeric(frame[column], errors="coerce")
        non_null = values.dropna().to_numpy(dtype=float)
        if not np.isfinite(non_null).all():
            raise RobustError(f"source column {column} contains non-finite values")
    if int(pd.to_numeric(frame["next_year_return_pct"], errors="coerce").notna().sum()) < 3:
        raise RobustError("source has fewer than three non-null primary target rows")


def validate_repository_inputs() -> None:
    """Check frozen packet, repository, input, and protected-code identities."""
    if not PACKET_PATH.is_file() or sha256_path(PACKET_PATH) != EXPECTED_PACKET_SHA256:
        raise RobustError("packet SHA-256 does not match the approved v3 packet")
    if not DISCOVERY_PATH.is_file() or sha256_path(DISCOVERY_PATH) != EXPECTED_DISCOVERY_SHA256:
        raise RobustError("discovery SHA-256 does not match the approved preflight evidence")
    if not EVIDENCE_PATH.is_file() or EXPECTED_EVIDENCE_MARKER not in EVIDENCE_PATH.read_text(encoding="utf-8"):
        raise RobustError("required pre-packet evidence marker is absent")
    if not (ROOT / "experiments" / "run_experiments.py").is_file():
        raise RobustError("protected canonical harness is missing")
    if sha256_path(ROOT / "experiments" / "run_experiments.py") != EXPECTED_RUN_EXPERIMENTS_SHA256:
        raise RobustError("experiments/run_experiments.py changed from its protected SHA-256")
    if sha256_path(ROOT / "experiments" / "significance.py") != EXPECTED_SIGNIFICANCE_SHA256:
        raise RobustError("experiments/significance.py changed from its protected SHA-256")
    if sha256_path(CANONICAL_INPUT) != EXPECTED_MODELING_SHA256:
        raise RobustError("canonical experiment input changed from its frozen SHA-256")
    if sha256_path(QUALITY_REPORT) != EXPECTED_QUALITY_SHA256:
        raise RobustError("data-quality report changed from its frozen SHA-256")
    if sha256_path(MODEL_CONFIDENCE_CONTRACT) != EXPECTED_CONTRACT_SHA256:
        raise RobustError("model confidence contract changed from its frozen SHA-256")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    if head != EXPECTED_HEAD:
        raise RobustError(f"unexpected starting HEAD: {head}")
    status = subprocess.run(
        ["git", "status", "--porcelain=v1"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.rstrip()
    cached = subprocess.run(
        ["git", "diff", "--cached", "--name-only"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    if cached:
        raise RobustError("repository must have no staged files before generation")
    unexpected = sorted(_worktree_paths(status) - ALLOWED_WORKTREE_PATHS)
    if unexpected:
        raise RobustError(f"worktree contains unapproved paths: {unexpected}")
    raw = pd.read_csv(CANONICAL_INPUT)
    validate_raw_frame(raw)


def load_canonical_source_descriptors() -> list[dict[str, Any]]:
    report = json.loads(BASELINE_REPORT.read_text(encoding="utf-8"))
    sources = _copy(report.get("source_artifacts"))
    expected_paths = [
        "experiments/results/predictions_test_2023.csv",
        "experiments/results/predictions_test_2024.csv",
        "experiments/results/predictions_test_2025.csv",
    ]
    if not isinstance(sources, list) or [item.get("path") for item in sources] != expected_paths:
        raise RobustError("committed significance report has unexpected source-artifact paths")
    for item in sources:
        if set(item) != {"path", "sha256", "rows", "year", "models"}:
            raise RobustError("committed source-artifact descriptor shape changed")
        source_path = ROOT / item["path"]
        if not source_path.is_file() or sha256_path(source_path) != item["sha256"]:
            raise RobustError(f"committed prediction source is stale: {item['path']}")
    return sources


def load_canonical_baseline() -> dict[str, Any]:
    report = json.loads(BASELINE_REPORT.read_text(encoding="utf-8"))
    required = {"analysis", "models", "headline", "source_artifacts"}
    if not required <= set(report):
        raise RobustError("committed significance report is missing mandatory vector fields")
    return report


def build_panel_from_raw(frame: pd.DataFrame) -> pd.DataFrame:
    """Build the canonical rank-normalized panel from an in-memory raw frame."""
    feature_columns = _feature_columns(frame)
    out = frame[["ticker", "year", *feature_columns]].copy()
    out = out.rename(columns={"year": "feature_year"})
    for column in feature_columns:
        out[column] = out.groupby("feature_year")[column].rank(pct=True)
    out["target_return"] = pd.to_numeric(frame["next_year_return_pct"], errors="coerce").to_numpy()
    return out.dropna(subset=["target_return"]).reset_index(drop=True)


def fit_thresholds(values: Iterable[float], q: float) -> tuple[float, float]:
    if q not in Q_GRID:
        raise RobustError(f"q is outside the frozen grid: {q}")
    array = np.asarray(list(values), dtype=float)
    array = array[~np.isnan(array)]
    if not np.isfinite(array).all():
        raise RobustError("threshold input contains non-finite values")
    n = int(len(array))
    if (n - 1) * q < 1:
        raise HardSupportError(f"hard support failed for n={n}, q={q}")
    return (
        float(np.quantile(array, q, method="linear")),
        float(np.quantile(array, 1 - q, method="linear")),
    )


def affected_masks(values: pd.Series, lower: float, upper: float) -> tuple[pd.Series, pd.Series]:
    numeric = pd.to_numeric(values, errors="coerce")
    return numeric < lower, numeric > upper


def apply_operator(
    frame: pd.DataFrame,
    feature_masks: dict[str, tuple[pd.Series, pd.Series]],
    thresholds: dict[str, tuple[float, float]],
    operator: str,
) -> pd.DataFrame:
    if operator not in OPERATORS:
        raise RobustError(f"unsupported operator: {operator}")
    transformed = frame.copy(deep=True)
    for feature, (lower_mask, upper_mask) in feature_masks.items():
        lower, upper = thresholds[feature]
        lower_index = lower_mask.index[lower_mask]
        upper_index = upper_mask.index[upper_mask]
        if operator == "winsorization":
            transformed.loc[lower_index, feature] = lower
            transformed.loc[upper_index, feature] = upper
        else:
            transformed.loc[lower_index, feature] = np.nan
            transformed.loc[upper_index, feature] = np.nan
    return transformed


def _target_rows(frame: pd.DataFrame) -> pd.DataFrame:
    target = pd.to_numeric(frame["next_year_return_pct"], errors="coerce")
    return frame.loc[target.notna()].copy()


def _coverage(frame: pd.DataFrame, years: list[int]) -> dict[str, Any]:
    subset = _target_rows(frame).loc[lambda value: value["year"].isin(years)]
    block = subset.loc[:, list(ELIGIBLE_FEATURES)]
    supported = block.notna().any(axis=1)
    supported_count = int(supported.sum())
    unsupported_count = int((~supported).sum())
    return {
        "row_count": int(len(subset)),
        "growth_supported_row_count": supported_count,
        "growth_unsupported_row_count": unsupported_count,
        "growth_supported_row_proportion": _proportion(supported_count, len(subset)),
        "growth_unsupported_row_proportion": _proportion(unsupported_count, len(subset)),
        "original_growth_null_cell_count": int(block.isna().sum().sum()),
    }


def prepare_window(frame: pd.DataFrame, split: dict[str, Any], operator: str, q: float) -> dict[str, Any]:
    """Make one fresh independent transformed window and its cell audit."""
    raw = frame.copy(deep=True)
    target_rows = _target_rows(raw)
    training_feature_years = [int(year) - 1 for year in split["train_target_years"]]
    test_feature_year = int(split["test_feature_year"])
    training = target_rows.loc[target_rows["year"].isin(training_feature_years)].copy()
    test = target_rows.loc[target_rows["year"] == test_feature_year].copy()
    training_coverage = _coverage(raw, training_feature_years)
    test_coverage = _coverage(raw, [test_feature_year])
    thresholds: dict[str, tuple[float, float]] = {}
    masks: dict[str, tuple[pd.Series, pd.Series]] = {}
    cell_rows: list[dict[str, Any]] = []
    total_affected = 0
    for feature in ELIGIBLE_FEATURES:
        train_values = pd.to_numeric(training[feature], errors="coerce")
        non_null = train_values.dropna().to_numpy(dtype=float)
        lower, upper = fit_thresholds(non_null, q)
        thresholds[feature] = (lower, upper)
        train_lower, train_upper = affected_masks(train_values, lower, upper)
        test_values = pd.to_numeric(test[feature], errors="coerce")
        test_lower, test_upper = affected_masks(test_values, lower, upper)
        # Keep masks indexed to the raw source so the isolated transform cannot
        # accidentally include an unrelated year or an inference-only row.
        combined_lower = pd.Series(False, index=raw.index)
        combined_upper = pd.Series(False, index=raw.index)
        combined_lower.loc[train_lower.index] = train_lower.fillna(False)
        combined_lower.loc[test_lower.index] = test_lower.fillna(False)
        combined_upper.loc[train_upper.index] = train_upper.fillna(False)
        combined_upper.loc[test_upper.index] = test_upper.fillna(False)
        masks[feature] = (combined_lower, combined_upper)
        lower_train_count = int(train_lower.fillna(False).sum())
        upper_train_count = int(train_upper.fillna(False).sum())
        lower_test_count = int(test_lower.fillna(False).sum())
        upper_test_count = int(test_upper.fillna(False).sum())
        affected_count = lower_train_count + upper_train_count + lower_test_count + upper_test_count
        total_affected += affected_count
        train_denominator = int(train_values.notna().sum())
        test_denominator = int(test_values.notna().sum())
        row = {
            "surface_id": f"{operator}__q_{q_code(q)}",
            "window_condition_id": f"{operator}__q_{q_code(q)}__{split['name']}",
            "operator": operator,
            "q": q,
            "split": split["name"],
            "test_feature_year": test_feature_year,
            "test_target_year": test_feature_year + 1,
            "training_target_years_json": _compact_json(split["train_target_years"]),
            "training_feature_years_json": _compact_json(training_feature_years),
            "feature": feature,
            "threshold_method": "linear",
            "lower_threshold": lower,
            "upper_threshold": upper,
            "n_training_nonnull": int(len(non_null)),
            "training_row_count": int(len(training)),
            "growth_supported_training_row_count": training_coverage["growth_supported_row_count"],
            "growth_unsupported_training_row_count": training_coverage["growth_unsupported_row_count"],
            "growth_supported_training_row_proportion": training_coverage["growth_supported_row_proportion"],
            "growth_unsupported_training_row_proportion": training_coverage["growth_unsupported_row_proportion"],
            "evaluated_row_count": int(len(test)),
            "growth_supported_row_count": test_coverage["growth_supported_row_count"],
            "growth_unsupported_row_count": test_coverage["growth_unsupported_row_count"],
            "growth_supported_row_proportion": test_coverage["growth_supported_row_proportion"],
            "growth_unsupported_row_proportion": test_coverage["growth_unsupported_row_proportion"],
            "original_growth_null_training_cell_count": int(training[feature].isna().sum()),
            "original_growth_null_test_cell_count": int(test[feature].isna().sum()),
            "original_growth_null_cell_count": int(training[feature].isna().sum() + test[feature].isna().sum()),
            "hard_support_value": float((len(non_null) - 1) * q),
            "hard_support_required": 1,
            "hard_support_pass": bool((len(non_null) - 1) * q >= 1),
            "stability_support_value": float(len(non_null) * q),
            "stability_support_required": 3,
            "stability_diagnostic_pass": bool(len(non_null) * q >= 3),
            "original_missing_training_count": int(train_values.isna().sum()),
            "original_missing_test_count": int(test_values.isna().sum()),
            "lower_affected_training_count": lower_train_count,
            "upper_affected_training_count": upper_train_count,
            "lower_affected_test_count": lower_test_count,
            "upper_affected_test_count": upper_test_count,
            "lower_affected_training_proportion": _proportion(lower_train_count, train_denominator),
            "upper_affected_training_proportion": _proportion(upper_train_count, train_denominator),
            "lower_affected_test_proportion": _proportion(lower_test_count, test_denominator),
            "upper_affected_test_proportion": _proportion(upper_test_count, test_denominator),
            "affected_cell_count": affected_count,
            "affected_cell_proportion": _proportion(affected_count, train_denominator + test_denominator),
            "perturbation_induced_null_training_count": affected_count if operator == "trim_to_null" else 0,
            "perturbation_induced_null_test_count": 0 if operator == "winsorization" else lower_test_count + upper_test_count,
            "row_count_before": int(len(raw)),
            "row_count_after": int(len(raw)),
            "target_immutable": True,
            "condition_status": "READY" if affected_count else "NO_OP",
        }
        # The training count above is deliberately feature-specific; split it
        # back into train/test components for the exact packet semantics.
        row["perturbation_induced_null_training_count"] = (
            lower_train_count + upper_train_count if operator == "trim_to_null" else 0
        )
        cell_rows.append(row)
    if not all(bool(row["hard_support_pass"]) for row in cell_rows):
        raise HardSupportError(f"hard support failed in {split['name']} at q={q}")
    transformed = apply_operator(raw, masks, thresholds, operator)
    if not transformed["next_year_return_pct"].equals(raw["next_year_return_pct"]):
        raise RobustError("target changed during isolated perturbation")
    window_status = "READY" if total_affected else "NO_OP"
    coverage = {
        "training_row_count": training_coverage["row_count"],
        "growth_supported_training_row_count": training_coverage["growth_supported_row_count"],
        "growth_unsupported_training_row_count": training_coverage["growth_unsupported_row_count"],
        "growth_supported_training_row_proportion": training_coverage["growth_supported_row_proportion"],
        "growth_unsupported_training_row_proportion": training_coverage["growth_unsupported_row_proportion"],
        "evaluated_row_count": test_coverage["row_count"],
        "growth_supported_row_count": test_coverage["growth_supported_row_count"],
        "growth_unsupported_row_count": test_coverage["growth_unsupported_row_count"],
        "growth_supported_row_proportion": test_coverage["growth_supported_row_proportion"],
        "growth_unsupported_row_proportion": test_coverage["growth_unsupported_row_proportion"],
        "original_growth_null_training_cell_count": training_coverage["original_growth_null_cell_count"],
        "original_growth_null_test_cell_count": test_coverage["original_growth_null_cell_count"],
        "original_growth_null_cell_count": training_coverage["original_growth_null_cell_count"]
        + test_coverage["original_growth_null_cell_count"],
    }
    return {
        "split": split["name"],
        "operator": operator,
        "q": q,
        "surface_id": f"{operator}__q_{q_code(q)}",
        "window_condition_id": f"{operator}__q_{q_code(q)}__{split['name']}",
        "test_feature_year": test_feature_year,
        "test_target_year": test_feature_year + 1,
        "training_target_years": _copy(split["train_target_years"]),
        "training_feature_years": training_feature_years,
        "window_status": window_status,
        "coverage": coverage,
        "cell_audit_rows": cell_rows,
        "transformed_frame": transformed,
    }


def q_code(q: float) -> str:
    codes = {0.025: "0p025", 0.05: "0p05", 0.1: "0p10"}
    try:
        return codes[q]
    except KeyError as exc:
        raise RobustError(f"unexpected q code: {q}") from exc


def run_window(frame: pd.DataFrame, split: dict[str, Any]) -> pd.DataFrame:
    """Run one window through the shared ROBUST prediction path."""
    panel = build_panel_from_raw(frame)
    feature_columns = [column for column in panel.columns if column not in {"ticker", "feature_year", "target_return"}]
    train = panel.loc[(panel["feature_year"] + 1).isin(split["train_target_years"])]
    test = panel.loc[panel["feature_year"] == split["test_feature_year"]]
    x_train = train[feature_columns].to_numpy(float)
    y_train = train["target_return"].to_numpy(float)
    x_test = test[feature_columns].to_numpy(float)
    y_test = test["target_return"].to_numpy(float)
    train_mask = ~np.isnan(y_train)
    x_train, y_train = x_train[train_mask], y_train[train_mask]
    rows: list[dict[str, Any]] = []
    for model_name, (_, scorer) in canonical.MODELS.items():
        predictions = np.asarray(scorer(x_train, y_train, x_test), dtype=float)
        evaluated = ~np.isnan(y_test) & ~np.isnan(predictions)
        if not np.isfinite(predictions[evaluated]).all() or not np.isfinite(y_test[evaluated]).all():
            raise RobustError(f"{model_name} produced non-finite predictions")
        rows.extend(
            {
                "ticker": ticker,
                "year": int(split["test_feature_year"] + 1),
                "model": model_name,
                "y_true": float(actual),
                "y_pred": float(prediction),
            }
            for ticker, actual, prediction in zip(
                test.loc[evaluated, "ticker"], y_test[evaluated], predictions[evaluated]
            )
        )
    output = pd.DataFrame(rows, columns=PREDICTION_COLUMNS)
    if output.empty:
        raise RobustError(f"{split['name']} produced no prediction rows")
    return output


def _prediction_bytes(predictions: pd.DataFrame) -> bytes:
    return predictions.loc[:, PREDICTION_COLUMNS].to_csv(
        index=False, float_format="%.17g", lineterminator="\n"
    ).encode("utf-8")


def _mandatory_vector(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "analysis": _copy(report["analysis"]),
        "models": _copy(report["models"]),
        "headline": _copy(report["headline"]),
        "source_artifacts": _copy(report["source_artifacts"]),
    }


def _canonical_vector(report: dict[str, Any]) -> dict[str, Any]:
    vector = _mandatory_vector(report)
    if vector["source_artifacts"] != load_canonical_source_descriptors():
        raise RobustError("canonical baseline vector source artifacts do not match committed sources")
    return vector


def _normalise_significance_report(report: dict[str, Any]) -> dict[str, Any]:
    normalised = _copy(report)
    for source in normalised.get("source_artifacts", []):
        source["path"] = "<canonical-source>"
    return normalised


def _canonical_output_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and "/results/runs/" not in path.as_posix()
    )


def run_canonical_determinism_gate() -> dict[str, Any]:
    """Run the unchanged canonical harness twice and compare bytes/semantics."""
    with tempfile.TemporaryDirectory(prefix="r4-robust-01-ab-") as directory:
        root = Path(directory)
        run_a = root / "run_a"
        run_b = root / "run_b"
        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        for destination in (run_a, run_b):
            subprocess.run(
                [sys.executable, "experiments/run_experiments.py", "--out", str(destination)],
                cwd=ROOT,
                env=env,
                check=True,
                stdout=subprocess.DEVNULL,
            )
            subprocess.run(
                [sys.executable, "experiments/significance.py", "--results-dir", str(destination / "results")],
                cwd=ROOT,
                env=env,
                check=True,
                stdout=subprocess.DEVNULL,
            )
        files_a = _canonical_output_files(run_a)
        files_b = _canonical_output_files(run_b)
        rel_a = {path.relative_to(run_a).as_posix() for path in files_a}
        rel_b = {path.relative_to(run_b).as_posix() for path in files_b}
        if rel_a != rel_b:
            raise RobustError(f"canonical A/B artifact sets differ: {sorted(rel_a ^ rel_b)}")
        run_rel = rel_a - {"results/significance_report.json", "results/significance_report.md"}
        if len(run_rel) != 16:
            raise RobustError(f"canonical harness did not produce the expected 16 artifacts: {sorted(run_rel)}")
        for relative in sorted(rel_a):
            first = run_a / relative
            second = run_b / relative
            if first.read_bytes() != second.read_bytes():
                if relative == "results/significance_report.json":
                    left = _normalise_significance_report(json.loads(first.read_text(encoding="utf-8")))
                    right = _normalise_significance_report(json.loads(second.read_text(encoding="utf-8")))
                    if left != right:
                        raise RobustError(f"canonical A/B semantic mismatch: {relative}")
                else:
                    raise RobustError(f"canonical A/B byte mismatch: {relative}")
            if relative in run_rel:
                committed = ROOT / "experiments" / relative
                if not committed.is_file() or committed.read_bytes() != first.read_bytes():
                    raise RobustError(f"canonical A output differs from committed artifact: {relative}")
        if (run_a / "results/significance_report.md").read_bytes() != BASELINE_MARKDOWN.read_bytes():
            raise RobustError("canonical significance Markdown differs from committed report")
        committed_json = json.loads(BASELINE_REPORT.read_text(encoding="utf-8"))
        generated_json = json.loads((run_a / "results/significance_report.json").read_text(encoding="utf-8"))
        if _normalise_significance_report(generated_json) != _normalise_significance_report(committed_json):
            raise RobustError("canonical significance JSON differs from committed report")
    return {"status": "READY", "artifact_count": 16, "comparison": "byte_identity_with_source_path_exception"}


def run_identity_control(
    raw: pd.DataFrame, sources: list[dict[str, Any]], baseline: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run zero perturbation through the same window/surface path as stress."""
    prediction_parts = []
    for split in canonical.SPLITS:
        predictions = run_window(raw.copy(deep=True), split)
        committed_path = ROOT / "experiments" / "results" / f"predictions_{split['name']}.csv"
        if _prediction_bytes(predictions) != committed_path.read_bytes():
            raise RobustError(f"ROBUST identity prediction mismatch: {split['name']}")
        prediction_parts.append(predictions.assign(split=split["name"]))
    combined = pd.concat(prediction_parts, ignore_index=True)
    report = significance.build_report(
        combined,
        _copy(sources),
        permutations=10_000,
        bootstraps=10_000,
        seed=42,
        power_simulations=5_000,
    )
    if _mandatory_vector(report) != _mandatory_vector(baseline):
        raise RobustError("ROBUST zero-perturbation significance vector differs from canonical baseline")
    if significance.render_markdown(report).encode("utf-8") != BASELINE_MARKDOWN.read_bytes():
        raise RobustError("ROBUST zero-perturbation Markdown differs from canonical baseline")
    return report, {"status": "HARNESS_PARITY_READY", "prediction_files": 3, "source_path_exception": True}


def _precheck_predictions(predictions: pd.DataFrame) -> str:
    clean = predictions.dropna(subset=["y_true", "y_pred"])
    if not np.isfinite(clean[["y_true", "y_pred"]].to_numpy(dtype=float)).all():
        return "FAILED-NONFINITE"
    for _, group in clean.groupby(["model", "split"], sort=True):
        if len(group) < 3:
            return "FAILED-INSUFFICIENT-DATA"
        if group["year"].nunique() != 1:
            return "FAILED-INSUFFICIENT-DATA"
    return "READY"


def _surface_report(
    surface_id: str,
    operator: str,
    q: float,
    windows: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    baseline: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    prediction_parts = []
    for window in windows:
        predictions = run_window(window["transformed_frame"].copy(deep=True), next(
            split for split in canonical.SPLITS if split["name"] == window["split"]
        ))
        status = _precheck_predictions(predictions.assign(split=window["split"]))
        if status != "READY":
            raise RobustError(f"{window['window_condition_id']} failed closed: {status}")
        prediction_parts.append(
            predictions.assign(
                surface_id=surface_id,
                window_condition_id=window["window_condition_id"],
                operator=operator,
                q=q,
                split=window["split"],
            )
        )
    stress_predictions = pd.concat(prediction_parts, ignore_index=True)
    canonical_predictions = stress_predictions.loc[:, PREDICTION_COLUMNS + ["split"]]
    report = significance.build_report(
        canonical_predictions,
        _copy(sources),
        permutations=10_000,
        bootstraps=10_000,
        seed=42,
        power_simulations=5_000,
    )
    baseline_vector = _mandatory_vector(baseline)
    if report["analysis"]["multiplicity"] != baseline_vector["analysis"]["multiplicity"]:
        raise RobustError("stress significance multiplicity differs from frozen canonical family")
    return report, stress_predictions


def _delta_vector(stress: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    base_models = {item["model"]: item for item in baseline["models"]}
    deltas: dict[str, Any] = {}
    for item in stress["models"]:
        base = base_models[item["model"]]
        split_deltas: dict[str, Any] = {}
        base_splits = {part["split"]: part for part in base["exploratory_by_split"]}
        for part in item["exploratory_by_split"]:
            original = base_splits[part["split"]]
            split_deltas[part["split"]] = {
                "delta_observed_ic": float(part["observed_ic"] - original["observed_ic"]),
                "delta_n": int(part["n"] - original["n"]),
                "delta_split_count": None,
                "significance_verdict_changed": None,
            }
        pooled = item["pooled"]
        base_pooled = base["pooled"]
        split_deltas["pooled"] = {
            "delta_observed_ic": float(pooled["observed_ic"] - base_pooled["observed_ic"]),
            "delta_n": int(pooled["n"] - base_pooled["n"]),
            "delta_split_count": int(pooled["split_count"] - base_pooled["split_count"]),
            "significance_verdict_changed": (
                pooled["significant_fwer_0_05"] != base_pooled["significant_fwer_0_05"]
            ),
        }
        deltas[item["model"]] = split_deltas
    return {
        "models": deltas,
        "headline_model_changed": stress["headline"]["model"] != baseline["headline"]["model"],
        "conclusion_category_changed": (
            bool(stress["headline"]["significant_fwer_0_05"])
            != bool(baseline["headline"]["significant_fwer_0_05"])
        ),
    }


def _metric_rows(
    surface_id: str,
    operator: str,
    q: float,
    stress: dict[str, Any],
    baseline: dict[str, Any],
) -> list[dict[str, Any]]:
    base_models = {item["model"]: item for item in baseline["models"]}
    rows = []
    for item in stress["models"]:
        base = base_models[item["model"]]
        base_splits = {part["split"]: part for part in base["exploratory_by_split"]}
        for part in item["exploratory_by_split"]:
            original = base_splits[part["split"]]
            rows.append(_metric_row(surface_id, operator, q, item, part, original, "per_split"))
        rows.append(_metric_row(surface_id, operator, q, item, item["pooled"], base["pooled"], "pooled"))
    return rows


def _metric_row(
    surface_id: str,
    operator: str,
    q: float,
    model: dict[str, Any],
    result: dict[str, Any],
    original: dict[str, Any],
    scope: str,
) -> dict[str, Any]:
    pooled = scope == "pooled"
    return {
        "surface_id": surface_id,
        "operator": operator,
        "q": q,
        "metric_scope": scope,
        "window_condition_id": "pooled" if pooled else f"{surface_id}__{result['split']}",
        "split": "pooled" if pooled else result["split"],
        "year": None if pooled else result["year"],
        "model": model["model"],
        "kind": model["kind"],
        "n": result["n"],
        "split_count": result.get("split_count"),
        "observed_ic": result["observed_ic"],
        "bootstrap_ci_95_low": result["bootstrap_ci_95"][0],
        "bootstrap_ci_95_high": result["bootstrap_ci_95"][1],
        "permutation_p_value_two_sided": result["permutation_p_value_two_sided"],
        "observed_null_percentile": result["observed_null_percentile"],
        "bonferroni_adjusted_p_value": result.get("bonferroni_adjusted_p_value"),
        "significant_fwer_0_05": result.get("significant_fwer_0_05"),
        "delta_observed_ic": float(result["observed_ic"] - original["observed_ic"]),
        "delta_n": int(result["n"] - original["n"]),
        "delta_split_count": (
            None if result.get("split_count") is None else int(result["split_count"] - original["split_count"])
        ),
        "significance_verdict_changed": (
            None
            if result.get("significant_fwer_0_05") is None
            else result["significant_fwer_0_05"] != original.get("significant_fwer_0_05")
        ),
    }


def _claim_safety() -> dict[str, Any]:
    return {
        "corruption_detected": False,
        "bad_cells_detected": False,
        "contamination_removed": False,
        "predictive_edge_established": False,
        "alpha_established": False,
        "profitability_established": False,
        "causal_validity_established": False,
        "production_validity_established": False,
        "investment_value_established": False,
        "research_support_only": True,
    }


def _frozen_design() -> dict[str, Any]:
    return {
        "target": "next_year_return_pct",
        "canonical_input": _relative_or_absolute(CANONICAL_INPUT),
        "eligible_features": list(ELIGIBLE_FEATURES),
        "operators": list(OPERATORS),
        "q_grid": list(Q_GRID),
        "q_is_per_side": True,
        "threshold_method": "linear",
        "affected_comparisons": {"lower": "strict <", "upper": "strict >"},
        "hard_support": {"formula": "(n - 1) * q", "required": 1, "comparison": ">="},
        "stability_diagnostic": {"formula": "n * q", "required": 3, "binding": False},
        "models": list(canonical.MODELS),
        "splits": _copy(canonical.SPLITS),
        "evaluation_universe": "canonical primary-target rows; growth-unsupported rows remain",
    }


def _claim_anchor() -> dict[str, Any]:
    contract = json.loads(MODEL_CONFIDENCE_CONTRACT.read_text(encoding="utf-8"))
    return {
        "path": _relative_or_absolute(MODEL_CONFIDENCE_CONTRACT),
        "sha256": sha256_path(MODEL_CONFIDENCE_CONTRACT),
        "approved_wording": {
            "headline_conclusion": contract["approved_wording"]["headline_conclusion"],
            "evidence_basis": _copy(contract["evidence_basis"]),
        },
    }


def _window_report(window: dict[str, Any]) -> dict[str, Any]:
    coverage = _copy(window["coverage"])
    return {
        "surface_id": window["surface_id"],
        "window_condition_id": window["window_condition_id"],
        "operator": window["operator"],
        "q": window["q"],
        "split": window["split"],
        "test_feature_year": window["test_feature_year"],
        "test_target_year": window["test_target_year"],
        "training_target_years": _copy(window["training_target_years"]),
        "training_feature_years": _copy(window["training_feature_years"]),
        "window_status": window["window_status"],
        **coverage,
        "cell_audit_rows": _copy(window["cell_audit_rows"]),
    }


def _surface_interpretation(stress: dict[str, Any], baseline: dict[str, Any]) -> str:
    if bool(stress["headline"]["significant_fwer_0_05"]) != bool(
        baseline["headline"]["significant_fwer_0_05"]
    ):
        return "A family-wise verdict changed; this is a sensitivity finding requiring investigation, not evidence of predictive edge."
    return "The committed negative finding is unchanged as a conclusion category; every quantitative change remains reported as descriptive sensitivity evidence."


def build_report(
    baseline: dict[str, Any],
    sources: list[dict[str, Any]],
    surfaces: list[dict[str, Any]],
    gate: dict[str, Any],
    seal_hash: str,
) -> dict[str, Any]:
    conditions = []
    for surface in surfaces:
        stress = surface["metric_report"]
        conditions.append(
            {
                "surface_id": surface["surface_id"],
                "operator": surface["operator"],
                "q": surface["q"],
                "surface_status": surface["surface_status"],
                "window_conditions": [_window_report(window) for window in surface["windows"]],
                "mandatory_metric_vector": _mandatory_vector(stress),
                "deltas_from_baseline": _delta_vector(stress, baseline),
                "supplementary": {"power_analysis": _copy(stress["power_analysis"])},
                "interpretation": _surface_interpretation(stress, baseline),
            }
        )
    baseline_vector = _canonical_vector(baseline)
    report = {
        "schema_version": "1.0.0",
        "task": TASK,
        "analysis_status": "READY",
        "scientific_purpose": "Descriptive cellwise extreme-tail and tail-handling sensitivity laboratory for eligible growth input features.",
        "scientific_conclusion_boundary": "No reliable predictive edge has been established. This analysis does not detect corrupted data, establish bad cells, or establish investment value.",
        "generated_by": "make research-contamination -> experiments/contamination_lab.py",
        "frozen_design": _frozen_design(),
        "determinism_gate": {
            **_copy(gate),
            "pre_result_manifest_sha256": seal_hash,
        },
        "source_artifacts": _copy(sources),
        "canonical_baseline": {
            "metric_vector": baseline_vector,
            "claim_anchor": _claim_anchor(),
            "supplementary": {"power_analysis": _copy(baseline["power_analysis"])},
        },
        "conditions": conditions,
        "supplementary": {
            "canonical_scope": "80 evaluated tickers per model and split across test_2023, test_2024, test_2025",
            "metric_deltas": "Only observed_ic, n, and split_count deltas are emitted; no delta inferential family is created.",
        },
        "limitations": _copy(LIMITATIONS),
        "claim_safety": _claim_safety(),
    }
    if list(report) != REPORT_TOP_LEVEL_KEYS:
        raise RobustError("ROBUST report top-level schema drifted")
    return report


def render_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# R4-ROBUST-01 tail-handling sensitivity report",
        "",
        "## Scientific purpose and boundary",
        "",
        report["scientific_purpose"],
        "",
        report["scientific_conclusion_boundary"],
        "",
        "Research support only; not investment advice.",
        "",
        "## Determinism and provenance",
        "",
        f"Analysis status: `{report['analysis_status']}`.",
        f"Canonical A/B gate: `{report['determinism_gate']['canonical_ab']['status']}`.",
        f"ROBUST identity control: `{report['determinism_gate']['robust_identity']['status']}`.",
        "",
        "Canonical prediction sources:",
        "",
    ]
    lines.extend(f"- `{source['path']}` — sha256 `{source['sha256']}`, rows `{source['rows']}`, year `{source['year']}`" for source in report["source_artifacts"])
    lines.extend(["", "## Canonical baseline vector", "", "```json", _json_dump(report["canonical_baseline"]["metric_vector"]).rstrip("\n"), "```", ""])
    lines.extend(["## Window conditions", ""])
    for surface in report["conditions"]:
        lines.extend([
            f"### {surface['surface_id']}",
            "",
            f"Operator `{surface['operator']}`; q per side `{surface['q']}`; surface status `{surface['surface_status']}`.",
            "",
        ])
        for window in surface["window_conditions"]:
            lines.extend([
                f"#### {window['window_condition_id']}",
                "",
                f"Window status `{window['window_status']}`; evaluated rows `{window['evaluated_row_count']}`; growth-supported rows `{window['growth_supported_row_count']}`; growth-unsupported rows `{window['growth_unsupported_row_count']}`.",
                f"Original growth-null cells: training `{window['original_growth_null_training_cell_count']}`, test `{window['original_growth_null_test_cell_count']}`, combined `{window['original_growth_null_cell_count']}`.",
                "",
                "| Feature | Lower | Upper | n | Affected cells | Status |",
                "| --- | ---: | ---: | ---: | ---: | --- |",
            ])
            for row in window["cell_audit_rows"]:
                lines.append(
                    f"| `{row['feature']}` | {row['lower_threshold']:.17g} | {row['upper_threshold']:.17g} | {row['n_training_nonnull']} | {row['affected_cell_count']} | `{row['condition_status']}` |"
                )
            lines.extend(["", "Coverage and cell audit:", "", "```json", _json_dump(window).rstrip("\n"), "```", ""])
    lines.extend(["## Surface metric vectors and deterministic deltas", ""])
    for surface in report["conditions"]:
        lines.extend([
            f"### {surface['surface_id']}",
            "",
            "```json",
            _json_dump({
                "mandatory_metric_vector": surface["mandatory_metric_vector"],
                "deltas_from_baseline": surface["deltas_from_baseline"],
                "interpretation": surface["interpretation"],
            }).rstrip("\n"),
            "```",
            "",
        ])
    lines.extend(["## Limitations", ""])
    lines.extend(f"- {limitation}" for limitation in report["limitations"])
    lines.extend(["", "## Claim safety", "", "```json", _json_dump(report["claim_safety"]).rstrip("\n"), "```", ""])
    lines.extend([
        "## Closing boundary",
        "",
        "The conclusion remains: no reliable predictive edge. Research support only; not investment advice.",
        "",
    ])
    return "\n".join(lines)


def _input_artifacts(seal_hash: str) -> list[dict[str, Any]]:
    paths = [
        (CANONICAL_INPUT, "canonical ROBUST input"),
        (QUALITY_REPORT, "canonical data-quality report"),
        (ROOT / "experiments" / "results" / "predictions_test_2023.csv", "protected baseline prediction source"),
        (ROOT / "experiments" / "results" / "predictions_test_2024.csv", "protected baseline prediction source"),
        (ROOT / "experiments" / "results" / "predictions_test_2025.csv", "protected baseline prediction source"),
        (ROOT / "experiments" / "run_experiments.py", "read-only canonical harness"),
        (ROOT / "experiments" / "significance.py", "read-only significance machinery"),
        (ROOT / "backend" / "app" / "services" / "research" / "feature_registry.py", "canonical feature registry"),
        (ROOT / "Makefile", "generator command source"),
        (MODEL_CONFIDENCE_CONTRACT, "claim boundary contract"),
    ]
    records = [{"path": _relative_or_absolute(path), "sha256": sha256_path(path), "role": role} for path, role in paths]
    records.extend([
        {"path": str(PACKET_PATH), "sha256": sha256_path(PACKET_PATH), "role": "approved implementation packet"},
        {"path": str(DISCOVERY_PATH), "sha256": sha256_path(DISCOVERY_PATH), "role": "discovery evidence"},
        {"path": str(EVIDENCE_PATH), "sha256": sha256_path(EVIDENCE_PATH), "role": "pre-packet evidence"},
        {"path": "<sealed-pre-result-manifest>", "sha256": seal_hash, "role": "sealed pre-result manifest"},
    ])
    return records


def _build_manifest(report: dict[str, Any], output_files: list[Path], seal_hash: str) -> dict[str, Any]:
    artifact_records = [
        {
            "path": f"experiments/results_contamination/{path.name}",
            "sha256": sha256_path(path),
            "size_bytes": path.stat().st_size,
        }
        for path in output_files
    ]
    return {
        "schema_version": "1.0.0",
        "task": TASK,
        "generator_command": "make research-contamination",
        "artifacts": artifact_records,
        "input_artifacts": _input_artifacts(seal_hash),
        "claim_safety": _claim_safety(),
        "determinism": _copy(report["determinism_gate"]),
    }


def _safe_output_path(path: Path) -> Path:
    candidate = path.expanduser()
    temporary_aliases = {Path(tempfile.gettempdir()), Path("/tmp")}
    symlink_checks = [candidate, *candidate.parents]
    symlink_checks = [part for part in symlink_checks if part not in temporary_aliases]
    if any(part.is_symlink() for part in symlink_checks if part.exists()):
        raise RobustError("output path or parent is a symlink")
    resolved = candidate.resolve()
    canonical = OUTPUT_DIR.resolve()
    if resolved == canonical:
        return resolved
    temporary_roots = {Path(tempfile.gettempdir()).resolve(), Path("/tmp").resolve()}
    temporary_root = next((root for root in temporary_roots if resolved.is_relative_to(root)), None)
    if temporary_root is None:
        raise RobustError("temporary output must be below the system temporary directory")
    relative = resolved.relative_to(temporary_root)
    if not relative.parts or not relative.parts[0].startswith("r4-robust-01-"):
        raise RobustError("temporary output must be below an r4-robust-01-* directory")
    return resolved


def _publish(scratch: Path, destination: Path) -> None:
    existing = {path.name for path in destination.iterdir()} if destination.exists() else set()
    if existing - EXPECTED_OUTPUT_FILES:
        raise RobustError(f"output directory contains unapproved files: {sorted(existing - EXPECTED_OUTPUT_FILES)}")
    destination.mkdir(parents=True, exist_ok=True)
    for filename in sorted(EXPECTED_OUTPUT_FILES):
        shutil.copyfile(scratch / filename, destination / filename)


def _seal_manifest(raw: pd.DataFrame, sources: list[dict[str, Any]], baseline: dict[str, Any], gate: dict[str, Any]) -> tuple[Path, str]:
    directory = Path(tempfile.mkdtemp(prefix="r4-robust-01-sealed-"))
    payload = {
        "task": TASK,
        "packet_sha256": sha256_path(PACKET_PATH),
        "discovery_sha256": sha256_path(DISCOVERY_PATH),
        "prepacket_marker": EXPECTED_EVIDENCE_MARKER,
        "head": EXPECTED_HEAD,
        "clean_state": True,
        "canonical_input_hashes": {
            _relative_or_absolute(CANONICAL_INPUT): sha256_path(CANONICAL_INPUT),
            _relative_or_absolute(QUALITY_REPORT): sha256_path(QUALITY_REPORT),
        },
        "code_config_hashes": {
            "experiments/run_experiments.py": sha256_path(ROOT / "experiments" / "run_experiments.py"),
            "experiments/significance.py": sha256_path(ROOT / "experiments" / "significance.py"),
            "model_confidence_contract.json": sha256_path(MODEL_CONFIDENCE_CONTRACT),
        },
        "packages": {
            package: importlib.metadata.version(package)
            for package in ("numpy", "pandas", "scikit-learn")
        },
        "python": platform.python_version(),
        "model_configuration": _copy(canonical.MODEL_CONFIGS),
        "split_configuration": _copy(canonical.SPLITS),
        "seed": 42,
        "q_grid": list(Q_GRID),
        "operators": list(OPERATORS),
        "eligible_columns": list(ELIGIBLE_FEATURES),
        "baseline_vector": _mandatory_vector(baseline),
        "baseline_sources": _copy(sources),
        "gate": _copy(gate),
        "source_rows": int(len(raw)),
    }
    path = directory / "pre_result_manifest.json"
    path.write_text(_json_dump(payload), encoding="utf-8", newline="\n")
    return path, sha256_path(path)


def generate(output_dir: Path = OUTPUT_DIR) -> Path:
    """Generate the complete six-file family after all fail-closed gates."""
    validate_repository_inputs()
    destination = _safe_output_path(output_dir)
    raw = pd.read_csv(CANONICAL_INPUT)
    raw_before = CANONICAL_INPUT.read_bytes()
    sources = load_canonical_source_descriptors()
    baseline = load_canonical_baseline()
    canonical_gate = run_canonical_determinism_gate()
    _, identity_gate = run_identity_control(raw, sources, baseline)
    gate = {"canonical_ab": canonical_gate, "robust_identity": identity_gate}
    _, seal_hash = _seal_manifest(raw, sources, baseline, gate)
    if CANONICAL_INPUT.read_bytes() != raw_before:
        raise RobustError("canonical input changed during pre-result gates")
    windows_by_surface: dict[str, list[dict[str, Any]]] = {}
    for operator in OPERATORS:
        for q in Q_GRID:
            surface_id = f"{operator}__q_{q_code(q)}"
            windows_by_surface[surface_id] = [
                prepare_window(raw, split, operator, q) for split in canonical.SPLITS
            ]
    if not any(window["window_status"] != "NO_OP" for windows in windows_by_surface.values() for window in windows):
        raise RobustError("all frozen conditions are NO_OP; refusing vacuous publication")

    surfaces = []
    all_cell_rows: list[dict[str, Any]] = []
    all_metric_rows: list[dict[str, Any]] = []
    all_prediction_frames = []
    for operator in OPERATORS:
        for q in Q_GRID:
            surface_id = f"{operator}__q_{q_code(q)}"
            windows = windows_by_surface[surface_id]
            metric_report, stress_predictions = _surface_report(surface_id, operator, q, windows, sources, baseline)
            surface_status = "READY" if all(window["window_status"] == "READY" for window in windows) else "FAILED-MIXED"
            surfaces.append({
                "surface_id": surface_id,
                "operator": operator,
                "q": q,
                "surface_status": surface_status,
                "windows": windows,
                "metric_report": metric_report,
            })
            all_cell_rows.extend(row for window in windows for row in window["cell_audit_rows"])
            all_metric_rows.extend(_metric_rows(surface_id, operator, q, metric_report, baseline))
            all_prediction_frames.append(stress_predictions)

    report = build_report(baseline, sources, surfaces, gate, seal_hash)
    scratch_directory = Path(tempfile.mkdtemp(prefix="r4-robust-01-") )
    try:
        cells_path = scratch_directory / "contamination_cells.csv"
        metrics_path = scratch_directory / "contamination_metrics.csv"
        predictions_path = scratch_directory / "contamination_predictions.csv"
        report_path = scratch_directory / "contamination_report.json"
        markdown_path = scratch_directory / "contamination_report.md"
        manifest_path = scratch_directory / "artifact_manifest.json"
        _write_csv(pd.DataFrame(all_cell_rows), cells_path, CELL_COLUMNS)
        _write_csv(pd.DataFrame(all_metric_rows), metrics_path, METRIC_COLUMNS)
        predictions = pd.concat(all_prediction_frames, ignore_index=True)
        _write_csv(predictions, predictions_path, STRESS_PREDICTION_COLUMNS)
        report_path.write_text(_json_dump(report), encoding="utf-8", newline="\n")
        markdown_path.write_text(render_report_markdown(report), encoding="utf-8", newline="\n")
        manifest = _build_manifest(
            report,
            [cells_path, metrics_path, predictions_path, report_path, markdown_path],
            seal_hash,
        )
        manifest_path.write_text(_json_dump(manifest), encoding="utf-8", newline="\n")
        _publish(scratch_directory, destination)
    finally:
        shutil.rmtree(scratch_directory, ignore_errors=True)
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="canonical output directory or a bounded r4-robust-01-* temporary directory",
    )
    args = parser.parse_args(argv)
    try:
        destination = generate(args.output_dir)
    except (RobustError, HardSupportError, OSError, subprocess.CalledProcessError) as exc:
        print(f"R4-ROBUST-01 blocked: {exc}", file=sys.stderr)
        return 1
    print(f"R4-ROBUST-01 wrote exactly six artifacts under {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
