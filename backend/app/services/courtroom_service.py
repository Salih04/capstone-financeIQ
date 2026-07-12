"""Deterministic, citation-complete Research Courtroom evidence lenses.

The Courtroom is deliberately not an adjudicator. It reads generated company
contexts and committed quality/statistical artifacts, never changes a score,
and never creates an argument when required evidence is absent or malformed.
"""

from __future__ import annotations

import json
import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.paths import resolve_repo_root
from app.services import skeptic_service


REPO_ROOT = resolve_repo_root()
CLEAN_DIR = REPO_ROOT / "data" / "trusted_clean"
COMPANY_CONTEXTS_DIR = CLEAN_DIR / "company_contexts"
FEATURE_PASSPORTS = CLEAN_DIR / "feature_passports.json"
SIGNIFICANCE_REPORT = REPO_ROOT / "experiments" / "results" / "significance_report.json"

PASSPORT_SOURCE = "data/trusted_clean/feature_passports.json"
SIGNIFICANCE_SOURCE = "experiments/results/significance_report.json"

EVIDENCE_BUDGET = 4
PERSONA_ORDER = ("bull", "bear", "skeptic", "risk")
CLOSING = (
    "A structured debate over historical, validated evidence. No persona forecasts "
    "returns; no verdict is issued; nothing here is investment advice."
)

_SKEPTIC_CHECK_IDS = (
    "staleness_frozen_probe",
    "missingness_attack",
    "cohort_integrity_challenge",
    "backtest_reminder",
)
_TICKER = re.compile(r"[A-Z0-9.]{1,16}")


def _citation(field: str, value: Any, source_file: str) -> dict[str, Any]:
    return {"field": field, "value": value, "source_file": source_file}


def _item(
    statement: str,
    field: str,
    value: Any,
    source_file: str,
    limitation: str,
) -> dict[str, Any]:
    return {
        "statement": statement,
        "citation": _citation(field, value, source_file),
        "limitation": limitation,
    }


def _persona(persona_id: str, lens: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    if len(items) != EVIDENCE_BUDGET:
        raise ValueError(f"{persona_id} requires exactly {EVIDENCE_BUDGET} evidence items")
    return {
        "persona_id": persona_id,
        "name": persona_id.title(),
        "lens": lens,
        "items": items,
    }


def _insufficient(
    ticker: str,
    year: int | None,
    missing_evidence: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "insufficient_data",
        "ticker": ticker,
        "year": year,
        "mode": "deterministic",
        "evidence_budget_per_persona": EVIDENCE_BUDGET,
        "personas": [],
        "missing_evidence": missing_evidence,
        "closing": CLOSING,
    }


@lru_cache(maxsize=8)
def _load_json_cached(path: str, mtime: float) -> dict[str, Any]:
    del mtime
    with Path(path).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("expected a JSON object")
    return value


def _load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, "artifact is missing"
    try:
        return _load_json_cached(str(path), path.stat().st_mtime), None
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return None, f"artifact is malformed ({type(exc).__name__})"


def _context_path(ticker: str, year: int | None) -> Path | None:
    if not COMPANY_CONTEXTS_DIR.is_dir():
        return None
    if year is not None:
        path = COMPANY_CONTEXTS_DIR / f"{ticker}_{year}.json"
        return path if path.is_file() else None
    candidates: list[tuple[int, Path]] = []
    for path in COMPANY_CONTEXTS_DIR.glob(f"{ticker}_*.json"):
        match = re.fullmatch(rf"{re.escape(ticker)}_(\d{{4}})\.json", path.name)
        if match:
            candidates.append((int(match.group(1)), path))
    return max(candidates, default=(0, None), key=lambda item: item[0])[1]


def _source(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.name


def _passport_index(artifact: dict[str, Any]) -> dict[str, dict[str, Any]] | None:
    passports = artifact.get("passports")
    if not isinstance(passports, list) or not passports:
        return None
    index = {
        item.get("name"): item
        for item in passports
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    return index if len(index) == len(passports) else None


def _metric_values(context: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for section in ("financials", "valuation"):
        section_values = context.get(section)
        if isinstance(section_values, dict):
            values.update(section_values)
    return values


def _validated_percentiles(
    context: dict[str, Any],
    passports: dict[str, dict[str, Any]],
) -> list[tuple[str, float]]:
    benchmarks = context.get("benchmarks")
    percentiles = (
        benchmarks.get("training_universe_percentiles")
        if isinstance(benchmarks, dict)
        else None
    )
    if not isinstance(percentiles, dict):
        return []
    values = _metric_values(context)
    output: list[tuple[str, float]] = []
    for field, raw_percentile in percentiles.items():
        passport = passports.get(field)
        raw_value = values.get(field)
        if not passport or passport.get("acceptance_status") != "accepted_feature":
            continue
        if raw_value is None or isinstance(raw_value, bool):
            continue
        try:
            percentile = float(raw_percentile)
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(percentile) and math.isfinite(value) and 0.0 <= percentile <= 100.0:
            output.append((field, percentile))
    return output


def _metric_label(field: str) -> str:
    return field.replace("_", " ").title()


def build_bull(
    context: dict[str, Any],
    context_source: str,
    passports: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    """Return the four highest accepted-feature percentiles."""
    metrics = sorted(
        _validated_percentiles(context, passports),
        key=lambda item: (-item[1], item[0]),
    )
    if len(metrics) < EVIDENCE_BUDGET * 2:
        return None
    year = int(context["year"])
    items = [
        _item(
            f"{_metric_label(field)} is at training-universe percentile {percentile:.1f} "
            f"in the validated {year} company context.",
            f"benchmarks.training_universe_percentiles.{field}",
            percentile,
            context_source,
            "Historical cross-sectional percentile; it does not establish a future outcome.",
        )
        for field, percentile in metrics[:EVIDENCE_BUDGET]
    ]
    return _persona("bull", "Highest accepted-feature percentiles", items)


def build_bear(
    context: dict[str, Any],
    context_source: str,
    passports: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    """Return the four lowest accepted-feature percentiles."""
    metrics = sorted(
        _validated_percentiles(context, passports),
        key=lambda item: (item[1], item[0]),
    )
    if len(metrics) < EVIDENCE_BUDGET * 2:
        return None
    year = int(context["year"])
    items = [
        _item(
            f"{_metric_label(field)} is at training-universe percentile {percentile:.1f} "
            f"in the validated {year} company context.",
            f"benchmarks.training_universe_percentiles.{field}",
            percentile,
            context_source,
            "Historical cross-sectional percentile; it does not establish a future outcome.",
        )
        for field, percentile in metrics[:EVIDENCE_BUDGET]
    ]
    return _persona("bear", "Lowest accepted-feature percentiles", items)


def build_skeptic(ticker: str, report: dict[str, Any]) -> dict[str, Any] | None:
    """Embed four fixed Skeptic evidence facts exactly as produced by R2-SKEPTIC-01."""
    checks = report.get("checks")
    if report.get("ticker") != ticker or not isinstance(checks, list):
        return None
    indexed = {
        item.get("check_id"): item
        for item in checks
        if isinstance(item, dict) and item.get("check_id")
    }
    items: list[dict[str, Any]] = []
    for check_id in _SKEPTIC_CHECK_IDS:
        check = indexed.get(check_id)
        evidence = check.get("evidence") if isinstance(check, dict) else None
        first = evidence[0] if isinstance(evidence, list) and evidence else None
        if not isinstance(first, dict):
            return None
        fact = first.get("fact")
        source_file = first.get("source_file")
        if not isinstance(fact, str) or not fact or not isinstance(source_file, str):
            return None
        items.append(
            _item(
                fact,
                f"checks.{check_id}.evidence[0].fact",
                fact,
                source_file,
                "Skeptic evidence reproduced without added interpretation; it does not alter any score.",
            )
        )
    return _persona("skeptic", "Artifact-backed challenge report", items)


def build_risk(
    context: dict[str, Any],
    context_source: str,
    significance: dict[str, Any],
) -> dict[str, Any] | None:
    """Keep ticker missingness, small-n, return basis, and significance visible."""
    quality = context.get("data_quality")
    analysis = significance.get("analysis")
    headline = significance.get("headline")
    limitations = significance.get("limitations")
    if (
        not isinstance(quality, dict)
        or not isinstance(quality.get("missing_fields"), list)
        or not isinstance(analysis, dict)
        or not isinstance(headline, dict)
        or not isinstance(limitations, list)
    ):
        return None
    evaluated = analysis.get("evaluated_tickers_per_model_split")
    conclusion = headline.get("conclusion")
    small_n = next(
        (item for item in limitations if isinstance(item, str) and "Only three test years" in item),
        None,
    )
    nominal_try = next(
        (item for item in limitations if isinstance(item, str) and "Nominal TRY" in item),
        None,
    )
    if not isinstance(evaluated, list) or not evaluated or not all(
        isinstance(value, int) for value in evaluated
    ):
        return None
    if not isinstance(conclusion, str) or not small_n or not nominal_try:
        return None

    missing_fields = quality["missing_fields"]
    missing_statement = (
        f"The validated company context lists {len(missing_fields)} missing fields"
        + (f": {', '.join(str(field) for field in missing_fields)}." if missing_fields else ".")
    )
    items = [
        _item(
            missing_statement,
            "data_quality.missing_fields",
            missing_fields,
            context_source,
            "Context-level completeness only; absence of listed gaps does not validate the signal.",
        ),
        _item(
            small_n,
            "limitations.small_sample",
            small_n,
            SIGNIFICANCE_SOURCE,
            "Small-sample design limitation; estimates remain noisy and do not support ticker-level inference.",
        ),
        _item(
            nominal_try,
            "limitations.nominal_try_basis",
            nominal_try,
            SIGNIFICANCE_SOURCE,
            "Return-basis scope is historical context, not a forecast or causal explanation.",
        ),
        _item(
            conclusion,
            "headline.conclusion",
            conclusion,
            SIGNIFICANCE_SOURCE,
            "Family-wise corrected model-family evidence; no ticker-level inference follows.",
        ),
    ]
    return _persona("risk", "Data and inference limitations", items)


def courtroom_report(ticker: str, year: int | None = None) -> dict[str, Any]:
    """Build four deterministic evidence lenses or an honest insufficient-data state."""
    ticker = str(ticker).strip().upper()
    if not ticker or not _TICKER.fullmatch(ticker):
        raise ValueError("ticker must contain 1-16 uppercase letters, digits, or dots")
    if year is not None and not 1900 <= int(year) <= 2100:
        raise ValueError("year must be between 1900 and 2100")

    context_path = _context_path(ticker, year)
    if context_path is None:
        requested = f"{ticker}_{year}.json" if year is not None else f"{ticker}_<latest>.json"
        return _insufficient(
            ticker,
            year,
            [{"source_file": f"data/trusted_clean/company_contexts/{requested}", "reason": "company context is missing"}],
        )

    context, context_error = _load_json(context_path)
    passports_artifact, passports_error = _load_json(FEATURE_PASSPORTS)
    significance, significance_error = _load_json(SIGNIFICANCE_REPORT)
    missing: list[dict[str, str]] = []
    for source_file, reason in (
        (_source(context_path), context_error),
        (PASSPORT_SOURCE, passports_error),
        (SIGNIFICANCE_SOURCE, significance_error),
    ):
        if reason:
            missing.append({"source_file": source_file, "reason": reason})
    if missing:
        return _insufficient(ticker, year, missing)

    assert context is not None and passports_artifact is not None and significance is not None
    if context.get("ticker") != ticker or not isinstance(context.get("year"), int):
        return _insufficient(
            ticker,
            year,
            [{"source_file": _source(context_path), "reason": "company context identity is malformed"}],
        )
    resolved_year = int(context["year"])
    if year is not None and resolved_year != year:
        return _insufficient(
            ticker,
            year,
            [{"source_file": _source(context_path), "reason": "company context year does not match the request"}],
        )

    passports = _passport_index(passports_artifact)
    if passports is None:
        return _insufficient(
            ticker,
            resolved_year,
            [{"source_file": PASSPORT_SOURCE, "reason": "feature passports are malformed"}],
        )

    try:
        skeptic_report = skeptic_service.skeptic_report(ticker)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return _insufficient(
            ticker,
            resolved_year,
            [{"source_file": "backend/app/services/skeptic_service.py", "reason": f"Skeptic evidence unavailable ({type(exc).__name__})"}],
        )

    context_source = _source(context_path)
    builders = [
        (build_bull, (context, context_source, passports), PASSPORT_SOURCE),
        (build_bear, (context, context_source, passports), PASSPORT_SOURCE),
        (build_skeptic, (ticker, skeptic_report), "backend/app/services/skeptic_service.py"),
        (build_risk, (context, context_source, significance), SIGNIFICANCE_SOURCE),
    ]
    personas: list[dict[str, Any]] = []
    for builder, args, source_file in builders:
        persona = builder(*args)
        if persona is None:
            return _insufficient(
                ticker,
                resolved_year,
                [{"source_file": source_file, "reason": f"{builder.__name__} evidence is incomplete or malformed"}],
            )
        personas.append(persona)

    return {
        "schema_version": 1,
        "status": "complete",
        "ticker": ticker,
        "year": resolved_year,
        "mode": "deterministic",
        "evidence_budget_per_persona": EVIDENCE_BUDGET,
        "personas": personas,
        "missing_evidence": [],
        "closing": CLOSING,
    }
