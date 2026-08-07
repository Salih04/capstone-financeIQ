"""Read-only access to the committed significance and power report.

This service never recomputes statistics. It filters the generated report for
the user-facing instrument panel, retaining the paired raw/adjusted p-values,
bootstrap intervals, and null histogram for each ML model.
"""

from __future__ import annotations

import csv
import json
import math
from functools import lru_cache
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any

from app.core.paths import resolve_repo_root
from app.services import citations


REPORT_PATH = resolve_repo_root() / "experiments" / "results" / "significance_report.json"
FRICTION_REPORT_PATH = resolve_repo_root() / "experiments" / "results" / "friction_report.json"
_SIGNIFICANCE_REL = "experiments/results/significance_report.json"
_FRICTION_REL = "experiments/results/friction_report.json"
_FRICTION_MARKDOWN_REL = "experiments/results/friction_report.md"
_FRICTION_MARKDOWN_LOCATOR = "# Friction sensitivity report (R2-FRICTION-01)"

_CANONICAL_ML_FAMILY = (
    "linear_regression",
    "ridge",
    "lasso",
    "elasticnet",
    "random_forest",
    "gradient_boosting",
)
_EXPECTED_FRICTION_STAMP = (
    "Hypothetical illustration — not a backtest of a viable strategy; underlying signal IC ≈ 0 "
    "and no model survives significance correction."
)
_EXPECTED_COST_LIMITATION = "Cost bps values are explicit assumptions, not measured BIST costs."
_EXPECTED_FRICTION_CLAIM_SAFETY = {
    "bid_ask_spread_or_market_impact_inferred": False,
    "core_model_or_ranking_computation_changed": False,
    "descriptive_sensitivity_only": True,
    "implementable_returns_established": False,
    "investment_value_established": False,
    "liquidity_or_tradeability_estimated": False,
    "reliable_predictive_edge_established": False,
}
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


# ---------------------------------------------------------------------------
# R3-AGENT-01 grounded ask helpers
# ---------------------------------------------------------------------------
def _strict_relative_source(relative: str) -> None:
    """Reject path tricks before delegating to the shared citation loader."""
    try:
        citations.assert_repo_relative(relative)
        root = citations.REPO_ROOT.resolve()
        current = root
        for part in PurePosixPath(relative).parts:
            current /= part
            if current.is_symlink():
                raise SignificanceReportMissing(
                    f"grounded source is symlinked: {relative}"
                )
    except citations.CitationError as exc:
        raise SignificanceReportMissing(str(exc)) from exc


def _strict_json_source(relative: str) -> dict[str, Any]:
    _strict_relative_source(relative)
    try:
        return citations.load_json_artifact(relative)
    except (OSError, ValueError, citations.CitationError) as exc:
        raise SignificanceReportMissing(
            f"grounded source is unavailable or malformed: {relative}"
        ) from exc


def _strict_text_source(relative: str) -> str:
    _strict_relative_source(relative)
    try:
        return citations.load_text_artifact(relative)
    except (OSError, ValueError, UnicodeError, citations.CitationError) as exc:
        raise SignificanceReportMissing(
            f"grounded source is unavailable or malformed: {relative}"
        ) from exc


def _grounded_mapping(value: Any, label: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise SignificanceReportMissing(f"{label} must be an object")
    return value


def _grounded_string(value: Any, label: str) -> str:
    if type(value) is not str or not value.strip():
        raise SignificanceReportMissing(f"{label} must be a non-empty string")
    return value


def _grounded_number(value: Any, label: str) -> int | float:
    if type(value) not in (int, float) or not math.isfinite(float(value)):
        raise SignificanceReportMissing(f"{label} must be a finite number")
    return value


def _grounded_integer(value: Any, label: str) -> int:
    if type(value) is not int or value < 0:
        raise SignificanceReportMissing(f"{label} must be a non-negative integer")
    return value


def _grounded_string_list(value: Any, label: str) -> list[str]:
    if type(value) is not list or not value or any(type(item) is not str or not item for item in value):
        raise SignificanceReportMissing(f"{label} must be a non-empty string list")
    return list(value)


def significance_headline_payload() -> dict[str, Any]:
    """Return only the strict, six-model significance headline evidence."""
    report = _strict_json_source(_SIGNIFICANCE_REL)
    headline = _grounded_mapping(report.get("headline"), "headline")
    analysis = _grounded_mapping(report.get("analysis"), "analysis")
    multiplicity = _grounded_mapping(analysis.get("multiplicity"), "analysis.multiplicity")

    family = _grounded_string_list(multiplicity.get("family"), "analysis.multiplicity.family")
    if tuple(family) != _CANONICAL_ML_FAMILY:
        raise SignificanceReportMissing("significance family is not the canonical six-model family")
    family_size = _grounded_integer(multiplicity.get("family_size"), "analysis.multiplicity.family_size")
    if family_size != len(_CANONICAL_ML_FAMILY):
        raise SignificanceReportMissing("significance family size is inconsistent")
    family_alpha = _grounded_number(
        multiplicity.get("family_wise_alpha"), "analysis.multiplicity.family_wise_alpha"
    )
    if family_alpha != 0.05:
        raise SignificanceReportMissing("significance family-wise alpha is not 0.05")
    method = _grounded_string(multiplicity.get("method"), "analysis.multiplicity.method")
    if method != "Bonferroni":
        raise SignificanceReportMissing("significance multiplicity method is not Bonferroni")

    model = _grounded_string(headline.get("model"), "headline.model")
    if model not in family:
        raise SignificanceReportMissing("selected significance model is outside the six-model family")
    observed_ic = _grounded_number(headline.get("observed_ic"), "headline.observed_ic")
    raw_p = _grounded_number(
        headline.get("permutation_p_value_two_sided"),
        "headline.permutation_p_value_two_sided",
    )
    adjusted_p = _grounded_number(
        headline.get("bonferroni_adjusted_p_value"),
        "headline.bonferroni_adjusted_p_value",
    )
    if not 0.0 <= float(raw_p) <= 1.0 or not 0.0 <= float(adjusted_p) <= 1.0:
        raise SignificanceReportMissing("significance p-values are outside [0, 1]")
    significant = headline.get("significant_fwer_0_05")
    if type(significant) is not bool:
        raise SignificanceReportMissing("headline.significant_fwer_0_05 must be a boolean")
    conclusion = _grounded_string(headline.get("conclusion"), "headline.conclusion")
    selection = _grounded_string(headline.get("selection"), "headline.selection")

    evaluated = analysis.get("evaluated_tickers_per_model_split")
    if type(evaluated) is not list or not evaluated or any(
        type(item) is not int or item <= 0 for item in evaluated
    ):
        raise SignificanceReportMissing(
            "analysis.evaluated_tickers_per_model_split must be a positive integer list"
        )
    permutation = _grounded_string(analysis.get("permutation"), "analysis.permutation")
    bootstrap = _grounded_string(analysis.get("bootstrap"), "analysis.bootstrap")
    statistic = _grounded_string(analysis.get("statistic"), "analysis.statistic")
    seed = _grounded_integer(analysis.get("seed"), "analysis.seed")

    bounded_headline: dict[str, Any] = {
        "model": model,
        "observed_ic": observed_ic,
        "permutation_p_value_two_sided": raw_p,
        "bonferroni_adjusted_p_value": adjusted_p,
        "significant_fwer_0_05": significant,
        "conclusion": conclusion,
        "selection": selection,
    }
    if "bootstrap_ci_95" in headline:
        ci = headline["bootstrap_ci_95"]
        if type(ci) is not list or len(ci) != 2 or any(
            type(item) not in (int, float) or isinstance(item, bool) or not math.isfinite(float(item))
            for item in ci
        ):
            raise SignificanceReportMissing("headline.bootstrap_ci_95 has an invalid type")
        bounded_headline["bootstrap_ci_95"] = list(ci)
    if "observed_null_percentile" in headline:
        percentile = _grounded_number(
            headline["observed_null_percentile"], "headline.observed_null_percentile"
        )
        if not 0.0 <= float(percentile) <= 1.0:
            raise SignificanceReportMissing("headline.observed_null_percentile is outside [0, 1]")
        bounded_headline["observed_null_percentile"] = percentile

    limitations = report.get("limitations", [])
    if type(limitations) is not list or any(type(item) is not str or not item for item in limitations):
        raise SignificanceReportMissing("limitations must be a string list")

    answer = (
        f"Canonical six-model ML significance headline for {model}: raw two-sided permutation "
        f"p-value {raw_p} and Bonferroni-adjusted p-value {adjusted_p}; the test family "
        f"contains {family_size} ML models (method {method}, family-wise alpha {family_alpha}). "
        f"Family-wise significance at 0.05: {str(significant).lower()}. {conclusion}"
    )
    return {
        "answer": answer,
        "headline": bounded_headline,
        "analysis": {
            "multiplicity": {
                "family": list(family),
                "family_size": family_size,
                "family_wise_alpha": family_alpha,
                "method": method,
            },
            "evaluated_tickers_per_model_split": list(evaluated),
            "permutation": permutation,
            "bootstrap": bootstrap,
            "statistic": statistic,
            "seed": seed,
        },
        "limitations": list(limitations),
    }


def friction_stamp_payload() -> dict[str, Any]:
    """Return the exact committed friction stamp and its claim boundary."""
    report = _strict_json_source(_FRICTION_REL)
    task = _grounded_string(report.get("task"), "friction.task")
    if task != "R2-FRICTION-01":
        raise SignificanceReportMissing("friction report is not R2-FRICTION-01")
    chart_stamp = _grounded_string(report.get("chart_stamp"), "friction.chart_stamp")
    if chart_stamp != _EXPECTED_FRICTION_STAMP:
        raise SignificanceReportMissing("friction chart stamp differs from the governed stamp")
    limitations = _grounded_string_list(report.get("limitations"), "friction.limitations")
    if _EXPECTED_COST_LIMITATION not in limitations:
        raise SignificanceReportMissing("friction cost-assumption limitation is missing")
    claim_safety = _grounded_mapping(report.get("claim_safety"), "friction.claim_safety")
    if set(claim_safety) != set(_EXPECTED_FRICTION_CLAIM_SAFETY):
        raise SignificanceReportMissing("friction claim-safety fields are inconsistent")
    for key, expected in _EXPECTED_FRICTION_CLAIM_SAFETY.items():
        if type(claim_safety.get(key)) is not bool or claim_safety[key] is not expected:
            raise SignificanceReportMissing(f"friction claim-safety flag is inconsistent: {key}")

    _strict_text_source(_FRICTION_MARKDOWN_REL)
    try:
        citations.verify_text_span(
            _FRICTION_MARKDOWN_REL,
            _FRICTION_MARKDOWN_LOCATOR,
            chart_stamp,
        )
    except citations.CitationError as exc:
        raise SignificanceReportMissing("friction chart stamp is not present in the committed Markdown") from exc

    return {
        "answer": chart_stamp,
        "task": task,
        "chart_stamp": chart_stamp,
        "limitations": [_EXPECTED_COST_LIMITATION],
        "claim_safety": dict(claim_safety),
    }


# Descriptive aliases keep the helper names discoverable without changing the
# existing direct significance/autopsy endpoint functions above.
grounded_significance_headline = significance_headline_payload
grounded_friction_stamp = friction_stamp_payload
