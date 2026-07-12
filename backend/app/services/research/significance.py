"""Read-only access to the committed significance and power report.

This service never recomputes statistics. It filters the generated report for
the user-facing instrument panel, retaining the paired raw/adjusted p-values,
bootstrap intervals, and null histogram for each ML model.
"""

from __future__ import annotations

import csv
import json
from functools import lru_cache
from pathlib import Path

from app.core.paths import resolve_repo_root


REPORT_PATH = resolve_repo_root() / "experiments" / "results" / "significance_report.json"
FRICTION_REPORT_PATH = resolve_repo_root() / "experiments" / "results" / "friction_report.json"
AUTOPSY_ARTIFACTS = {
    "feature_stability_by_split": resolve_repo_root()
    / "experiments"
    / "results"
    / "feature_stability_by_split.csv",
    "feature_stability_summary": resolve_repo_root()
    / "experiments"
    / "results"
    / "feature_stability_summary.csv",
    "coverage_impact": resolve_repo_root()
    / "experiments"
    / "results"
    / "coverage_impact.csv",
    "leaderboard": resolve_repo_root() / "experiments" / "leaderboard.csv",
}


class SignificanceReportMissing(RuntimeError):
    """Raised when the generated significance evidence is unavailable."""


@lru_cache(maxsize=2)
def _load_cached(path: str, mtime: float) -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def _load_report() -> dict:
    if not REPORT_PATH.is_file():
        raise SignificanceReportMissing(
            f"Significance report not found at {REPORT_PATH}. Run `make research-significance`."
        )
    return _load_cached(str(REPORT_PATH), REPORT_PATH.stat().st_mtime)


def _typed_csv_value(value: str):
    if value == "":
        return None
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


@lru_cache(maxsize=8)
def _load_csv_cached(path: str, mtime: float) -> tuple[dict, ...]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return tuple(
            {key: _typed_csv_value(value) for key, value in row.items()}
            for row in csv.DictReader(handle)
        )


def _artifact_payload(path: Path) -> dict:
    if not path.is_file():
        raise SignificanceReportMissing(f"Autopsy evidence not found at {path}.")
    rows = _load_csv_cached(str(path), path.stat().st_mtime)
    return {
        "source_file": str(path.relative_to(resolve_repo_root())),
        "rows": list(rows),
    }


def payload() -> dict:
    """Return report-backed ML significance and power evidence without recalculation."""
    report = _load_report()
    required = {"schema_version", "headline", "limitations", "models", "power_analysis"}
    if not required.issubset(report) or not isinstance(report["models"], list):
        raise SignificanceReportMissing("Significance report has an unsupported schema.")

    models = [model for model in report["models"] if model.get("kind") == "ml"]
    if not models:
        raise SignificanceReportMissing("Significance report contains no ML model evidence.")

    for model in models:
        pooled = model.get("pooled", {})
        if not all(key in pooled for key in (
            "observed_ic",
            "bootstrap_ci_95",
            "permutation_p_value_two_sided",
            "bonferroni_adjusted_p_value",
            "null_histogram",
        )):
            raise SignificanceReportMissing("Significance report is missing required ML evidence fields.")

    return {
        "schema_version": report["schema_version"],
        "headline": report["headline"],
        "models": models,
        "power_analysis": report["power_analysis"],
        "limitations": report["limitations"],
    }


def autopsy_payload() -> dict:
    """Return the existing significance evidence plus parsed autopsy exhibits."""
    friction = None
    if FRICTION_REPORT_PATH.is_file():
        friction = _load_cached(str(FRICTION_REPORT_PATH), FRICTION_REPORT_PATH.stat().st_mtime)
        required = {"task", "chart_stamp", "design", "plot_rows", "claim_safety", "limitations"}
        if not required.issubset(friction) or friction.get("task") != "R2-FRICTION-01":
            raise SignificanceReportMissing("Friction report has an unsupported schema.")
    return {
        "schema_version": 1,
        "significance": payload(),
        "evidence": {
            name: _artifact_payload(path)
            for name, path in AUTOPSY_ARTIFACTS.items()
        },
        "friction": friction,
    }
