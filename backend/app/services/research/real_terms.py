"""Read-only passthrough for the committed R2-REAL-01 return-basis evidence.

This service composes a narrow, display-only view over three committed
significance artifacts — the canonical nominal-TRY report and the two
alternative-basis reports (CPI-deflated real TRY and USD) — plus the top-level
comparison report. It never recomputes returns, ICs, permutation p-values, or
family-wise corrections; every number is copied verbatim from its source file.

The response is deliberately shaped so raw and adjusted p-values are structurally
inseparable: each basis entry carries both in the same object, and a basis whose
adjusted p-value is missing raises rather than emitting a raw-p-only view.

The 2022 nominal-versus-real illustration is an inflation-basis illustration
only. Its numbers are the quotable values fixed by METHODOLOGY.md
§"Alternative return-basis evaluation (R2-REAL-01)" (the wording authority for
this task); the nominal 185.94% and 64.27% CPI are additionally committed as
structured fields in ``experiments/results_regime/regime_context_report.json``
(2022 ``bist100_return_pct`` / ``cpi_december_yoy_pct``). This service performs
no arithmetic on them.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.paths import resolve_repo_root


# --- committed source artifacts (relative to repo root) ----------------------
_NOMINAL_REPORT_REL = "experiments/results/significance_report.json"
_COMPARISON_REPORT_REL = "experiments/results_real_terms/comparison_report.json"
_REAL_TRY_REPORT_REL = "experiments/results_real_terms/real_try/significance_report.json"
_USD_REPORT_REL = "experiments/results_real_terms/usd/significance_report.json"
_ALT_TARGETS_REPORT_REL = "data/trusted_clean/alternative_targets_report.json"

# Provenance authorities for the 2022 illustration (no numbers are computed here).
_ILLUSTRATION_AUTHORITY = "METHODOLOGY.md#alternative-return-basis-evaluation-r2-real-01"
_ILLUSTRATION_CROSS_REFERENCE = "experiments/results_regime/regime_context_report.json"

# Quotable illustration values fixed by the METHODOLOGY authority. The nominal
# and CPI figures are byte-identical to the committed regime-context report's
# 2022 fields (pinned in tests); the real figure is the METHODOLOGY-authored
# inflation-basis illustration. These are display constants, not a calculation.
_ILLUSTRATION_2022_NOMINAL_RETURN_PCT = 185.94
_ILLUSTRATION_2022_REAL_RETURN_PCT = 74.07
_ILLUSTRATION_2022_CPI_DECEMBER_YOY_PCT = 64.27

# Verbatim mandatory copy owned by the backend (preserved exactly).
PANEL_CAVEAT = (
    "The no-reliable-edge conclusion was re-evaluated separately on CPI-deflated "
    "TRY and USD bases; neither survives family-wise correction. Basis changes the "
    "unit of measurement, not the conclusion."
)
ILLUSTRATION_QUALIFIER = (
    "an inflation-basis illustration only, not a strategy-performance or "
    "investment-value statement."
)

_REQUIRED_HEADLINE_KEYS = (
    "model",
    "observed_ic",
    "permutation_p_value_two_sided",
    "bonferroni_adjusted_p_value",
    "significant_fwer_0_05",
    "selection",
    "conclusion",
)


class ReturnBasisReportMissing(RuntimeError):
    """Raised when the committed return-basis evidence is unavailable or malformed."""


@lru_cache(maxsize=8)
def _load_cached(path: str, mtime: float) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def _load_report(rel_path: str) -> dict[str, Any]:
    path = resolve_repo_root() / rel_path
    if not path.is_file():
        raise ReturnBasisReportMissing(
            f"Return-basis report not found at {rel_path}. Run `make research-real-terms`."
        )
    try:
        return _load_cached(str(path), path.stat().st_mtime)
    except json.JSONDecodeError as exc:
        raise ReturnBasisReportMissing(f"Return-basis report at {rel_path} is not valid JSON.") from exc


def _headline(report: dict[str, Any], rel_path: str) -> dict[str, Any]:
    headline = report.get("headline")
    if not isinstance(headline, dict):
        raise ReturnBasisReportMissing(f"{rel_path} is missing a headline block.")
    missing = [key for key in _REQUIRED_HEADLINE_KEYS if key not in headline]
    if missing:
        raise ReturnBasisReportMissing(
            f"{rel_path} headline is missing required fields: {', '.join(missing)}."
        )
    # Raw and adjusted p-values are structurally inseparable: refuse to compose a
    # basis entry when either is absent, so the frontend can never render raw-p alone.
    if headline["permutation_p_value_two_sided"] is None:
        raise ReturnBasisReportMissing(f"{rel_path} headline is missing the raw permutation p-value.")
    if headline["bonferroni_adjusted_p_value"] is None:
        raise ReturnBasisReportMissing(
            f"{rel_path} headline is missing the family-wise adjusted p-value; "
            "raw p is never surfaced without it."
        )
    return headline


def _multiplicity(report: dict[str, Any]) -> dict[str, Any]:
    analysis = report.get("analysis")
    multiplicity = analysis.get("multiplicity") if isinstance(analysis, dict) else None
    return multiplicity if isinstance(multiplicity, dict) else {}


def _basis_entry(
    basis_id: str,
    label: str,
    report: dict[str, Any],
    rel_path: str,
) -> dict[str, Any]:
    headline = _headline(report, rel_path)
    multiplicity = _multiplicity(report)
    return {
        "basis_id": basis_id,
        "label": label,
        "selected_model": headline["model"],
        "pooled_ic": headline["observed_ic"],
        # raw and adjusted p sit together in one object — inseparable by design.
        "raw_p_value": headline["permutation_p_value_two_sided"],
        "adjusted_p_value": headline["bonferroni_adjusted_p_value"],
        "correction_method": multiplicity.get("method"),
        "family_size": multiplicity.get("family_size"),
        "family_wise_alpha": multiplicity.get("family_wise_alpha"),
        "significant_fwer_0_05": headline["significant_fwer_0_05"],
        "selection": headline["selection"],
        "significance_statement": headline["conclusion"],
        "source_artifact": rel_path,
    }


def _verify_against_comparison(bases: list[dict[str, Any]], comparison: dict[str, Any]) -> None:
    """Cross-check the alternative-basis numbers against the top-level comparison report.

    The comparison report duplicates each alternative basis's headline; if the
    per-basis report and the comparison report disagree, the artifacts are
    inconsistent and we refuse rather than pick one.
    """
    comparison_bases = comparison.get("bases")
    if not isinstance(comparison_bases, list):
        raise ReturnBasisReportMissing(
            f"{_COMPARISON_REPORT_REL} is missing its bases array."
        )
    by_id = {entry.get("basis_id"): entry for entry in comparison_bases if isinstance(entry, dict)}
    for basis in bases:
        expected = by_id.get(basis["basis_id"])
        if expected is None:
            continue  # nominal has no comparison-report row; only alt bases are cross-checked
        headline = expected.get("headline", {})
        if (
            headline.get("model") != basis["selected_model"]
            or headline.get("observed_ic") != basis["pooled_ic"]
            or headline.get("permutation_p_value_two_sided") != basis["raw_p_value"]
            or headline.get("bonferroni_adjusted_p_value") != basis["adjusted_p_value"]
        ):
            raise ReturnBasisReportMissing(
                f"Basis '{basis['basis_id']}' disagrees between its significance report "
                f"and {_COMPARISON_REPORT_REL}."
            )


def _illustration_2022() -> dict[str, Any]:
    return {
        "year": 2022,
        "nominal_return_pct": _ILLUSTRATION_2022_NOMINAL_RETURN_PCT,
        "real_return_pct": _ILLUSTRATION_2022_REAL_RETURN_PCT,
        "cpi_december_yoy_pct": _ILLUSTRATION_2022_CPI_DECEMBER_YOY_PCT,
        "qualifier": ILLUSTRATION_QUALIFIER,
        "source_artifact": _ILLUSTRATION_AUTHORITY,
        "cross_reference_artifact": _ILLUSTRATION_CROSS_REFERENCE,
    }


def payload() -> dict[str, Any]:
    """Return the composed, display-only return-basis evidence without recalculation."""
    nominal = _load_report(_NOMINAL_REPORT_REL)
    comparison = _load_report(_COMPARISON_REPORT_REL)
    real_try = _load_report(_REAL_TRY_REPORT_REL)
    usd = _load_report(_USD_REPORT_REL)
    alt_targets = _load_report(_ALT_TARGETS_REPORT_REL)

    bases = [
        _basis_entry("nominal", "Nominal TRY return", nominal, _NOMINAL_REPORT_REL),
        _basis_entry("real_try", "CPI-deflated real TRY return", real_try, _REAL_TRY_REPORT_REL),
        _basis_entry("usd", "USD-basis return", usd, _USD_REPORT_REL),
    ]
    _verify_against_comparison(bases, comparison)

    claim_safety = comparison.get("claim_safety")
    if not isinstance(claim_safety, dict) or "conclusion" not in claim_safety:
        raise ReturnBasisReportMissing(
            f"{_COMPARISON_REPORT_REL} is missing its claim_safety conclusion."
        )

    return {
        "task": "R3-UI-02",
        "schema_version": 1,
        "caveat": PANEL_CAVEAT,
        "conclusion": claim_safety["conclusion"],
        "claim_safety": claim_safety,
        "bases": bases,
        "illustration_2022": _illustration_2022(),
        "source_artifacts": {
            "nominal": _NOMINAL_REPORT_REL,
            "comparison": _COMPARISON_REPORT_REL,
            "real_try": _REAL_TRY_REPORT_REL,
            "usd": _USD_REPORT_REL,
            "alternative_targets": _ALT_TARGETS_REPORT_REL,
        },
        "alternative_targets_design": alt_targets.get("design", {}),
    }
