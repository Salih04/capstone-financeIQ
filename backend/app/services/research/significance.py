"""Read-only access to the committed significance and power report.

This service never recomputes statistics. It filters the generated report for
the user-facing instrument panel, retaining the paired raw/adjusted p-values,
bootstrap intervals, and null histogram for each ML model.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.core.paths import resolve_repo_root


REPORT_PATH = resolve_repo_root() / "experiments" / "results" / "significance_report.json"


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
