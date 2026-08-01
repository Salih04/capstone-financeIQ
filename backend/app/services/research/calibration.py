"""Read-only passthrough for the committed R2-CAL-01 confidence calibration audit.

This service filters the committed calibration report for the Validation Lab
panel. It never recomputes calibration, monotonicity, bootstrap intervals, or
any confidence value: every field is copied verbatim from
``experiments/results/calibration_report.json``.

The panel copy is fixed by the R3-UI-03 task packet and is owned here so the
frontend cannot paraphrase it. Because that copy states specific audited facts
(constant confidence 0.25, calibration and monotonicity not estimable, 240
ticker-year outcomes, replay of git ``a95e1e1c``), the loader validates the
artifact *fail-closed* before serving it: structure and types are checked
before any field is read, and every fact the copy asserts must still be true
in the artifact. An artifact that is missing, malformed, from another task, or
scientifically contradictory raises :class:`CalibrationReportMissing`, which the route
translates into ``503``. It must fail loudly rather than be described by copy
that no longer applies.

Validation is explicit rather than defensive: there is deliberately no broad
``except Exception`` here, so genuine application or programming errors surface
as errors instead of being disguised as a missing artifact.
"""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.paths import resolve_repo_root


_REPORT_REL = "experiments/results/calibration_report.json"

_EXPECTED_TASK = "R2-CAL-01"

# Facts asserted by the fixed panel copy below; verified against the artifact.
_EXPECTED_CONSTANT_CONFIDENCE = 0.25
_EXPECTED_UNIQUE_CONFIDENCE_VALUES = 1
_EXPECTED_AUDITED_OUTCOMES = 240
_EXPECTED_REPLAY_SHA_PREFIX = "a95e1e1c"
_EXPECTED_NOT_ESTIMABLE = "not_estimable"
_EXPECTED_CONFIDENCE_QUANTITY = "research_agent_hybrid_confidence"
_EXPECTED_VERDICT = (
    "Hybrid confidence is not informative about rank error at this scale: the "
    "replayed value is constant across all evaluated rows, so calibration and "
    "monotonicity are not estimable."
)
_EXPECTED_MONOTONICITY_REASON = "Replayed hybrid confidence has fewer than two distinct values."
_EXPECTED_CONTRACT_CONCLUSION = "no reliable predictive edge"
_EXPECTED_CLAIM_SAFETY_STATEMENT = (
    "Diagnostic only: confidence is not a probability of return, profit, or "
    "success; it is not recommendation strength and does not establish "
    "validated predictive reliability."
)

# Sanity bounds for calendar years appearing in `sample.target_years` (matches
# the range already used elsewhere in the backend, e.g. courtroom_service.py).
_MIN_VALID_YEAR = 1900
_MAX_VALID_YEAR = 2100

# `hybrid_weight` is a blend weight in the [0, 1] simplex (see
# research_agent.py::confidence_score); a value outside that range cannot be a
# genuine blend weight and indicates a malformed or contradictory artifact.
_MIN_HYBRID_WEIGHT = 0.0
_MAX_HYBRID_WEIGHT = 1.0

# Exact allowed-key contracts for every object served verbatim (or field-by-field
# reconstructed) by `payload()`. Unknown keys are rejected fail-closed rather than
# silently forwarded, so an injected key can never reach a `200` response.
_ALLOWED_CALIBRATION_KEYS = frozenset(
    {
        "status",
        "verdict",
        "informative_about_rank_error",
        "confidence_unique_values",
        "confidence_values",
        "requested_bins",
        "realized_bins",
        "monotonicity",
    }
)
_ALLOWED_MONOTONICITY_KEYS = frozenset(
    {
        "status",
        "reason",
        "higher_confidence_lower_error_spearman",
        "bootstrap_95pct",
        "bootstrap_samples_requested",
        "bootstrap_samples_usable",
        "seed",
    }
)
_ALLOWED_CONFIDENCE_QUANTITY_KEYS = frozenset(
    {
        "quantity",
        "scope",
        "confidence_level",
        "confidence_reasons",
        "confidence_score",
        "hybrid_weight",
        "service_function",
        "consumer_function",
    }
)
_ALLOWED_REPLAY_PROVENANCE_KEYS = frozenset(
    {"git_sha", "git_worktree_dirty", "replay_date", "random_seed", "code_version"}
)
_ALLOWED_CODE_VERSION_FILES = frozenset(
    {
        "backend/app/services/forecasting_csv_service.py",
        "backend/app/services/research_agent.py",
    }
)
_ALLOWED_SAMPLE_KEYS = frozenset(
    {
        "independent_ticker_year_outcomes",
        "models",
        "prediction_model_rows",
        "rows_per_model_year",
        "target_years",
        "universe",
    }
)
_ALLOWED_CLAIM_SAFETY_KEYS = frozenset(
    {
        "confidence_is_probability_of_return_profit_or_success",
        "confidence_is_recommendation_strength",
        "contract_conclusion",
        "contract_version",
        "core_ranking_or_model_computation_changed",
        "statement",
        "validated_predictive_reliability_established",
    }
)

# Verbatim panel copy owned by the backend (R3-UI-03; changes require the packet).
PANEL_COPY = (
    "Confidence audited (R2-CAL-01, replay of git `a95e1e1c`): the hybrid "
    "confidence component was constant at 0.25 across all 240 audited "
    "ticker-year outcomes, so calibration against rank error is not estimable "
    "at this scale. Confidence is not a probability of return or recommendation "
    "strength."
)

# Claim-safety flags the closing sentence of the fixed copy depends on, plus the
# "nothing was recomputed" invariant this whole read-only service relies on.
_REQUIRED_FALSE_CLAIM_SAFETY = (
    "confidence_is_probability_of_return_profit_or_success",
    "confidence_is_recommendation_strength",
    "validated_predictive_reliability_established",
    "core_ranking_or_model_computation_changed",
)


class CalibrationReportMissing(RuntimeError):
    """Raised when the committed calibration audit is unavailable or malformed."""


class _NonFiniteJSONConstant(ValueError):
    """Raised when the on-disk artifact spells a bare NaN/Infinity/-Infinity token."""


# --------------------------------------------------------------------------
# Explicit, fail-closed type checks. Every accessor raises
# CalibrationReportMissing rather than letting a TypeError/AttributeError from a
# malformed artifact escape the service as a 500.
# --------------------------------------------------------------------------


def _fail(detail: str) -> "CalibrationReportMissing":
    return CalibrationReportMissing(f"{_REPORT_REL} {detail}")


def _mapping(container: dict[str, Any], key: str, label: str) -> dict[str, Any]:
    if key not in container:
        raise _fail(f"is missing the required `{label}` object.")
    value = container[key]
    if not isinstance(value, dict):
        raise _fail(f"has a non-object `{label}` block ({type(value).__name__}).")
    return value


def _reject_unknown_keys(container: dict[str, Any], allowed: frozenset[str], label: str) -> None:
    """Fail closed on any key outside the exact allowed-key contract for `label`.

    This is what stops an injected key (e.g. an unsupported predictive-skill
    assertion smuggled into `claim_safety` or `sample`) from ever reaching a
    `200` response: unknown keys are rejected before any field is read, rather
    than being silently forwarded by whole-object passthrough.
    """
    unknown = sorted(set(container) - allowed)
    if unknown:
        raise _fail(f"has unexpected key(s) in `{label}`: {unknown}.")


def _field(container: dict[str, Any], key: str, label: str) -> Any:
    if key not in container:
        raise _fail(f"is missing the required field `{label}`.")
    return container[key]


def _str(container: dict[str, Any], key: str, label: str) -> str:
    value = _field(container, key, label)
    if not isinstance(value, str):
        raise _fail(f"has a non-string `{label}` ({type(value).__name__}).")
    return value


def _bool(container: dict[str, Any], key: str, label: str) -> bool:
    value = _field(container, key, label)
    if not isinstance(value, bool):
        raise _fail(f"has a non-boolean `{label}` ({type(value).__name__}).")
    return value


def _int(container: dict[str, Any], key: str, label: str) -> int:
    value = _field(container, key, label)
    if isinstance(value, bool) or not isinstance(value, int):
        raise _fail(f"has a non-integer `{label}` ({type(value).__name__}).")
    return value


def _number(container: dict[str, Any], key: str, label: str) -> float:
    value = _field(container, key, label)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _fail(f"has a non-numeric `{label}` ({type(value).__name__}).")
    value = float(value)
    if not math.isfinite(value):
        raise _fail(f"has a non-finite `{label}` ({value}).")
    return value


def _list(container: dict[str, Any], key: str, label: str) -> list[Any]:
    value = _field(container, key, label)
    if not isinstance(value, list):
        raise _fail(f"has a non-list `{label}` ({type(value).__name__}).")
    return value


def _optional_number(container: dict[str, Any], key: str, label: str) -> float | None:
    value = _field(container, key, label)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _fail(f"has a `{label}` that is neither null nor numeric ({type(value).__name__}).")
    value = float(value)
    if not math.isfinite(value):
        raise _fail(f"has a non-finite `{label}` ({value}).")
    return value


def _optional_list(container: dict[str, Any], key: str, label: str) -> list[Any] | None:
    value = _field(container, key, label)
    if value is None:
        return None
    if not isinstance(value, list):
        raise _fail(f"has a `{label}` that is neither null nor a list ({type(value).__name__}).")
    return value


def _str_list(container: dict[str, Any], key: str, label: str) -> list[str]:
    """A list every one of whose elements must be a string."""
    value = _list(container, key, label)
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise _fail(f"has a non-string `{label}[{index}]` ({type(item).__name__}).")
    return value


def _int_list(container: dict[str, Any], key: str, label: str) -> list[int]:
    """A list every one of whose elements must be an integer (bool excluded)."""
    value = _list(container, key, label)
    for index, item in enumerate(value):
        if isinstance(item, bool) or not isinstance(item, int):
            raise _fail(f"has a non-integer `{label}[{index}]` ({type(item).__name__}).")
    return value


def _positive_int(container: dict[str, Any], key: str, label: str) -> int:
    value = _int(container, key, label)
    if value < 1:
        raise _fail(f"has a non-positive `{label}` ({value}).")
    return value


def _non_negative_int(container: dict[str, Any], key: str, label: str) -> int:
    value = _int(container, key, label)
    if value < 0:
        raise _fail(f"has a negative `{label}` ({value}).")
    return value


def _positive_int_list(container: dict[str, Any], key: str, label: str) -> list[int]:
    value = _int_list(container, key, label)
    if not value:
        raise _fail(f"reports an empty `{label}` list.")
    for index, item in enumerate(value):
        if item < 1:
            raise _fail(f"has a non-positive `{label}[{index}]` ({item}).")
    return value


def _non_empty_str(container: dict[str, Any], key: str, label: str) -> str:
    value = _str(container, key, label)
    if not value:
        raise _fail(f"has an empty `{label}`.")
    return value


def _validate_target_years(sample: dict[str, Any]) -> list[int]:
    years = _int_list(sample, "target_years", "sample.target_years")
    if not years:
        raise _fail("reports an empty `sample.target_years` list.")
    if len(set(years)) != len(years):
        raise _fail("reports duplicate years in `sample.target_years`.")
    if years != sorted(years):
        raise _fail("reports `sample.target_years` out of ascending order.")
    for year in years:
        if not (_MIN_VALID_YEAR <= year <= _MAX_VALID_YEAR):
            raise _fail(f"reports an out-of-range year {year} in `sample.target_years`.")
    return years


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------


def _reject_json_constant(constant: str) -> Any:
    """`json.load`'s hook for the non-standard `NaN`/`Infinity`/`-Infinity` tokens.

    The stdlib decoder accepts these bare tokens by default even though they are
    not valid JSON; without this hook they would parse straight into Python
    `float('nan')`/`float('inf')` values that later slip past a type-only
    numeric check.
    """
    raise _NonFiniteJSONConstant(f"contains the non-standard JSON constant `{constant}`.")


@lru_cache(maxsize=2)
def _load_cached(path: str, mtime: float) -> Any:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle, parse_constant=_reject_json_constant)


def _load_report() -> dict[str, Any]:
    path = resolve_repo_root() / _REPORT_REL
    if not path.is_file():
        raise CalibrationReportMissing(
            f"Calibration report not found at {_REPORT_REL}. Run `make research-calibration`."
        )
    try:
        report = _load_cached(str(path), path.stat().st_mtime)
    except _NonFiniteJSONConstant as exc:
        raise _fail(str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise _fail("is not valid JSON.") from exc
    except UnicodeDecodeError as exc:
        raise _fail("is not valid UTF-8 text.") from exc
    except OSError as exc:
        raise _fail("could not be read from disk.") from exc
    if not isinstance(report, dict):
        raise _fail(f"is not a JSON object ({type(report).__name__}).")
    return report


# --------------------------------------------------------------------------
# Validation of every fact the fixed panel copy asserts
# --------------------------------------------------------------------------


def _validated_blocks(report: dict[str, Any]) -> dict[str, Any]:
    """Validate structure, types, and copy-supporting facts; return newly
    constructed, whitelisted blocks ready for direct response serialization.

    Raises ``CalibrationReportMissing`` for anything the fixed panel copy would
    misdescribe. Nothing is indexed before its container type is checked. Every
    object below is reconstructed key-by-key from an exact allowed-key
    contract rather than returned as the original cached artifact object: an
    injected/unknown key anywhere in these objects raises here, and a mutable
    list or dict is never handed back by reference into the ``lru_cache``d
    parse result.
    """
    task = _str(report, "task", "task")
    if task != _EXPECTED_TASK:
        raise _fail(f"is task `{task}`, not the {_EXPECTED_TASK} calibration audit.")
    _non_empty_str(report, "schema_version", "schema_version")

    calibration = _mapping(report, "calibration", "calibration")
    claim_safety = _mapping(report, "claim_safety", "claim_safety")
    confidence_quantity = _mapping(report, "confidence_quantity", "confidence_quantity")
    provenance = _mapping(report, "replay_provenance", "replay_provenance")
    sample = _mapping(report, "sample", "sample")
    monotonicity = _mapping(calibration, "monotonicity", "calibration.monotonicity")

    _reject_unknown_keys(calibration, _ALLOWED_CALIBRATION_KEYS, "calibration")
    _reject_unknown_keys(monotonicity, _ALLOWED_MONOTONICITY_KEYS, "calibration.monotonicity")
    _reject_unknown_keys(
        confidence_quantity, _ALLOWED_CONFIDENCE_QUANTITY_KEYS, "confidence_quantity"
    )
    _reject_unknown_keys(provenance, _ALLOWED_REPLAY_PROVENANCE_KEYS, "replay_provenance")
    _reject_unknown_keys(sample, _ALLOWED_SAMPLE_KEYS, "sample")
    _reject_unknown_keys(claim_safety, _ALLOWED_CLAIM_SAFETY_KEYS, "claim_safety")

    limitations = _str_list(report, "limitations", "limitations")
    if not limitations:
        raise _fail("reports an empty `limitations` list.")
    for index, item in enumerate(limitations):
        if not item:
            raise _fail(f"has an empty `limitations[{index}]`.")
    if len(set(limitations)) != len(limitations):
        raise _fail("reports duplicate `limitations` entries.")

    # --- calibration block -------------------------------------------------
    status = _str(calibration, "status", "calibration.status")
    verdict = _str(calibration, "verdict", "calibration.verdict")
    informative = _bool(
        calibration, "informative_about_rank_error", "calibration.informative_about_rank_error"
    )
    unique_values = _int(
        calibration, "confidence_unique_values", "calibration.confidence_unique_values"
    )
    confidence_values = _list(calibration, "confidence_values", "calibration.confidence_values")
    requested_bins = _positive_int(calibration, "requested_bins", "calibration.requested_bins")
    realized_bins = _positive_int(calibration, "realized_bins", "calibration.realized_bins")
    if realized_bins > requested_bins:
        raise _fail(
            f"reports `calibration.realized_bins` ({realized_bins}) greater than "
            f"`calibration.requested_bins` ({requested_bins}); internally inconsistent."
        )

    if status != _EXPECTED_NOT_ESTIMABLE:
        raise _fail(
            f"reports calibration status `{status}`, not `{_EXPECTED_NOT_ESTIMABLE}`; "
            "the fixed panel copy would misdescribe it."
        )
    if informative is not False:
        raise _fail(
            "reports confidence as informative about rank error; "
            "the fixed panel copy would misdescribe it."
        )
    if unique_values != _EXPECTED_UNIQUE_CONFIDENCE_VALUES:
        raise _fail(
            f"reports {unique_values} unique confidence values, not "
            f"{_EXPECTED_UNIQUE_CONFIDENCE_VALUES}; the fixed panel copy would misdescribe it."
        )
    if confidence_values != [_EXPECTED_CONSTANT_CONFIDENCE]:
        raise _fail(
            "no longer reports a single constant confidence value of "
            f"{_EXPECTED_CONSTANT_CONFIDENCE}; the fixed panel copy would misdescribe it."
        )
    if verdict != _EXPECTED_VERDICT:
        raise _fail(
            "reports a `calibration.verdict` that does not match the committed, "
            "supported verdict text; the fixed panel copy would misdescribe it."
        )

    # --- monotonicity block ------------------------------------------------
    monotonicity_status = _str(monotonicity, "status", "calibration.monotonicity.status")
    monotonicity_reason = _str(monotonicity, "reason", "calibration.monotonicity.reason")
    spearman = _optional_number(
        monotonicity,
        "higher_confidence_lower_error_spearman",
        "calibration.monotonicity.higher_confidence_lower_error_spearman",
    )
    bootstrap = _optional_list(
        monotonicity, "bootstrap_95pct", "calibration.monotonicity.bootstrap_95pct"
    )
    requested_samples = _positive_int(
        monotonicity,
        "bootstrap_samples_requested",
        "calibration.monotonicity.bootstrap_samples_requested",
    )
    usable = _non_negative_int(
        monotonicity,
        "bootstrap_samples_usable",
        "calibration.monotonicity.bootstrap_samples_usable",
    )
    if usable > requested_samples:
        raise _fail(
            f"reports `calibration.monotonicity.bootstrap_samples_usable` ({usable}) greater "
            f"than `bootstrap_samples_requested` ({requested_samples}); internally inconsistent."
        )
    seed = _non_negative_int(monotonicity, "seed", "calibration.monotonicity.seed")

    if monotonicity_status != _EXPECTED_NOT_ESTIMABLE:
        raise _fail(
            f"reports monotonicity status `{monotonicity_status}`, not "
            f"`{_EXPECTED_NOT_ESTIMABLE}`; the fixed panel copy would misdescribe it."
        )
    if spearman is not None or bootstrap is not None or usable != 0:
        raise _fail(
            "reports a monotonicity coefficient, bootstrap interval, or usable bootstrap "
            f"sample inconsistent with `{_EXPECTED_NOT_ESTIMABLE}`; "
            "the fixed panel copy would misdescribe it."
        )
    if monotonicity_reason != _EXPECTED_MONOTONICITY_REASON:
        raise _fail(
            "reports a `calibration.monotonicity.reason` that does not match the "
            "committed, supported reason text; the fixed panel copy would misdescribe it."
        )

    # --- confidence quantity ----------------------------------------------
    quantity = _str(confidence_quantity, "quantity", "confidence_quantity.quantity")
    scope = _non_empty_str(confidence_quantity, "scope", "confidence_quantity.scope")
    confidence_level = _non_empty_str(
        confidence_quantity, "confidence_level", "confidence_quantity.confidence_level"
    )
    service_function = _non_empty_str(
        confidence_quantity, "service_function", "confidence_quantity.service_function"
    )
    consumer_function = _non_empty_str(
        confidence_quantity, "consumer_function", "confidence_quantity.consumer_function"
    )
    confidence_reasons = _str_list(
        confidence_quantity, "confidence_reasons", "confidence_quantity.confidence_reasons"
    )
    if not confidence_reasons:
        raise _fail("reports an empty `confidence_quantity.confidence_reasons` list.")
    for index, item in enumerate(confidence_reasons):
        if not item:
            raise _fail(f"has an empty `confidence_quantity.confidence_reasons[{index}]`.")
    if len(set(confidence_reasons)) != len(confidence_reasons):
        raise _fail("reports duplicate `confidence_quantity.confidence_reasons` entries.")
    hybrid_weight = _number(
        confidence_quantity, "hybrid_weight", "confidence_quantity.hybrid_weight"
    )
    if not (_MIN_HYBRID_WEIGHT <= hybrid_weight <= _MAX_HYBRID_WEIGHT):
        raise _fail(
            f"reports `confidence_quantity.hybrid_weight` ({hybrid_weight}) outside the "
            f"valid [{_MIN_HYBRID_WEIGHT}, {_MAX_HYBRID_WEIGHT}] blend-weight range."
        )
    score = _number(confidence_quantity, "confidence_score", "confidence_quantity.confidence_score")

    if quantity != _EXPECTED_CONFIDENCE_QUANTITY:
        raise _fail(
            f"audits `{quantity}`, not `{_EXPECTED_CONFIDENCE_QUANTITY}`; "
            "the fixed panel copy would misdescribe it."
        )
    if score != _EXPECTED_CONSTANT_CONFIDENCE:
        raise _fail(
            f"reports a hybrid confidence score of {score}, not "
            f"{_EXPECTED_CONSTANT_CONFIDENCE}; the fixed panel copy would misdescribe it."
        )

    # --- sample ------------------------------------------------------------
    outcomes = _int(sample, "independent_ticker_year_outcomes", "sample.independent_ticker_year_outcomes")
    if outcomes != _EXPECTED_AUDITED_OUTCOMES:
        raise _fail(
            f"reports {outcomes} audited ticker-year outcomes, not "
            f"{_EXPECTED_AUDITED_OUTCOMES}; the fixed panel copy would misdescribe it."
        )
    models = _positive_int(sample, "models", "sample.models")
    prediction_model_rows = _positive_int(
        sample, "prediction_model_rows", "sample.prediction_model_rows"
    )
    rows_per_model_year = _positive_int_list(
        sample, "rows_per_model_year", "sample.rows_per_model_year"
    )
    target_years = _validate_target_years(sample)
    universe = _non_empty_str(sample, "universe", "sample.universe")

    # --- replay provenance -------------------------------------------------
    git_sha = _str(provenance, "git_sha", "replay_provenance.git_sha")
    git_worktree_dirty = _bool(
        provenance, "git_worktree_dirty", "replay_provenance.git_worktree_dirty"
    )
    replay_date = _non_empty_str(provenance, "replay_date", "replay_provenance.replay_date")
    random_seed = _non_negative_int(
        provenance, "random_seed", "replay_provenance.random_seed"
    )
    code_version_raw = _mapping(provenance, "code_version", "replay_provenance.code_version")
    _reject_unknown_keys(
        code_version_raw, _ALLOWED_CODE_VERSION_FILES, "replay_provenance.code_version"
    )
    missing_code_versions = sorted(_ALLOWED_CODE_VERSION_FILES - set(code_version_raw))
    if missing_code_versions:
        raise _fail(
            f"is missing required `replay_provenance.code_version` entries: "
            f"{missing_code_versions}."
        )
    code_version: dict[str, str] = {}
    for file_path in sorted(_ALLOWED_CODE_VERSION_FILES):
        digest = code_version_raw[file_path]
        if not isinstance(digest, str) or not digest:
            raise _fail(
                f"has a non-string or empty `replay_provenance.code_version[{file_path}]`."
            )
        code_version[file_path] = digest

    if not git_sha.startswith(_EXPECTED_REPLAY_SHA_PREFIX):
        raise _fail(
            f"was not replayed at git {_EXPECTED_REPLAY_SHA_PREFIX}; "
            "the fixed panel copy would misdescribe it."
        )

    # --- claim safety ------------------------------------------------------
    claim_safety_flags: dict[str, bool] = {}
    for key in _REQUIRED_FALSE_CLAIM_SAFETY:
        if _bool(claim_safety, key, f"claim_safety.{key}") is not False:
            raise _fail(
                f"asserts `claim_safety.{key}`; the fixed panel copy would misdescribe it."
            )
        claim_safety_flags[key] = False
    contract_conclusion = _str(claim_safety, "contract_conclusion", "claim_safety.contract_conclusion")
    if contract_conclusion != _EXPECTED_CONTRACT_CONCLUSION:
        raise _fail(
            f"reports `claim_safety.contract_conclusion` `{contract_conclusion}`, not "
            f"`{_EXPECTED_CONTRACT_CONCLUSION}`; the fixed panel copy would misdescribe it."
        )
    contract_version = _non_empty_str(
        claim_safety, "contract_version", "claim_safety.contract_version"
    )
    statement = _str(claim_safety, "statement", "claim_safety.statement")
    if statement != _EXPECTED_CLAIM_SAFETY_STATEMENT:
        raise _fail(
            "reports a `claim_safety.statement` that does not match the committed "
            "claim-safety statement; the fixed panel copy would misdescribe it."
        )

    return {
        "calibration": {
            "status": status,
            "verdict": verdict,
            "informative_about_rank_error": informative,
            "confidence_unique_values": unique_values,
            "confidence_values": list(confidence_values),
            "requested_bins": requested_bins,
            "realized_bins": realized_bins,
            "monotonicity": {
                "status": monotonicity_status,
                "reason": monotonicity_reason,
                "higher_confidence_lower_error_spearman": spearman,
                "bootstrap_95pct": list(bootstrap) if bootstrap is not None else None,
                "bootstrap_samples_requested": requested_samples,
                "bootstrap_samples_usable": usable,
                "seed": seed,
            },
        },
        "confidence_quantity": {
            "quantity": quantity,
            "scope": scope,
            "confidence_score": score,
            "confidence_level": confidence_level,
            "confidence_reasons": list(confidence_reasons),
            "hybrid_weight": hybrid_weight,
            "service_function": service_function,
            "consumer_function": consumer_function,
        },
        "claim_safety": {
            "confidence_is_probability_of_return_profit_or_success": claim_safety_flags[
                "confidence_is_probability_of_return_profit_or_success"
            ],
            "confidence_is_recommendation_strength": claim_safety_flags[
                "confidence_is_recommendation_strength"
            ],
            "contract_conclusion": contract_conclusion,
            "contract_version": contract_version,
            "core_ranking_or_model_computation_changed": claim_safety_flags[
                "core_ranking_or_model_computation_changed"
            ],
            "statement": statement,
            "validated_predictive_reliability_established": claim_safety_flags[
                "validated_predictive_reliability_established"
            ],
        },
        "sample": {
            "independent_ticker_year_outcomes": outcomes,
            "models": models,
            "prediction_model_rows": prediction_model_rows,
            "rows_per_model_year": list(rows_per_model_year),
            "target_years": list(target_years),
            "universe": universe,
        },
        "replay_provenance": {
            "git_sha": git_sha,
            "git_worktree_dirty": git_worktree_dirty,
            "replay_date": replay_date,
            "random_seed": random_seed,
            "code_version": code_version,
        },
        "limitations": list(limitations),
    }


def payload() -> dict[str, Any]:
    """Return the filtered, committed calibration audit without recalculation."""
    report = _load_report()
    blocks = _validated_blocks(report)

    return {
        "task": "R3-UI-03",
        "schema_version": 1,
        "source_task": report["task"],
        "report_schema_version": report["schema_version"],
        "panel_copy": PANEL_COPY,
        "calibration": blocks["calibration"],
        "confidence_quantity": blocks["confidence_quantity"],
        "claim_safety": blocks["claim_safety"],
        "sample": blocks["sample"],
        "replay_provenance": blocks["replay_provenance"],
        "limitations": blocks["limitations"],
        "source_artifact": _REPORT_REL,
    }
