"""Serving-heuristic missingness sensitivity (R3-MISS-01).

Deterministic OFFLINE replay measuring how the unchanged user-facing serving
heuristic's *ranks* and *confidence* respond to controlled missing inputs.  The
heuristic is never reimplemented: the real backend ``forecasting_csv_service`` is
loaded read-only through the documented ``RESEARCH_REPO_ROOT`` override against an
isolated temporary data root, exactly like the R3-SERV-01 serving-parity harness.
Missing inputs are expressed with the service's own null representation (the cell
becomes NaN); the service then omits the feature and reduces confidence via its
existing ``run_forecast`` path.  No value is fabricated, imputed, zeroed, or
sentinel-filled.

Claim boundary (mandatory, verbatim everywhere it is exposed):

    Serving-heuristic sensitivity only — describes how this deterministic
    ranking recipe responds to missing inputs; it does not measure predictive
    skill, which remains indistinguishable from the null.

This analysis does NOT measure predictive skill, alpha, profitability,
robustness, reliability, or deployment validity.  A small rank delta is not
evidence of a reliable edge; the walk-forward IC remains indistinguishable from
the null (see experiments/results_serving_eval and experiments/results).
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import importlib.util
import inspect
import json
import math
import os
import re
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SERVICE_FILE = ROOT / "backend" / "app" / "services" / "forecasting_csv_service.py"
PUBLIC_DATASET = ROOT / "data" / "trusted_clean" / "modeling_dataset_public_2020_2025.csv"
TRAINING_DATASET = ROOT / "data" / "trusted_clean" / "modeling_dataset_training_2020_2025.csv"
BASE_DATASET = ROOT / "data" / "trusted_clean" / "modeling_dataset_2020_2025.csv"
FEATURE_PASSPORTS = ROOT / "data" / "trusted_clean" / "feature_passports.json"

RESULTS_DIR = ROOT / "experiments" / "results_missingness"
JSON_OUTPUT = RESULTS_DIR / "missingness_report.json"
MARKDOWN_OUTPUT = RESULTS_DIR / "missingness_report.md"
CSV_OUTPUT = RESULTS_DIR / "rank_deltas.csv"

TASK_ID = "R3-MISS-01"
SCHEMA_VERSION = "1.0.0"
TOP_N = 12
REGENERATION_COMMAND = "make research-missingness"

# The exact null/missing-input representation the service already handles.
MISSING_VALUE = np.nan

# Mandatory sensitivity label — must appear verbatim in JSON, Markdown, and CSV.
SENSITIVITY_LABEL = (
    "Serving-heuristic sensitivity only — describes how this deterministic "
    "ranking recipe responds to missing inputs; it does not measure predictive "
    "skill, which remains indistinguishable from the null."
)

PREDICTIVE_SKILL_STATEMENT = (
    "Predictive skill was not measured. This is a deterministic sensitivity "
    "analysis of a fixed ranking recipe's response to omitted inputs. It "
    "establishes no predictive edge, alpha, profitability, robustness, "
    "reliability, tradability, or deployment validity; the walk-forward IC "
    "remains indistinguishable from the null."
)

RANK_DELTA_SIGN_CONVENTION = (
    "signed_rank_delta = masked_rank - baseline_rank. Ranks are 1-based with "
    "rank 1 the highest deterministic score. A POSITIVE signed_rank_delta means "
    "the ticker moved to a worse (higher-numbered) rank under masking; a "
    "NEGATIVE signed_rank_delta means it moved up (toward rank 1). "
    "absolute_rank_delta = abs(signed_rank_delta)."
)

# Neutral, deterministic percentile grid for rank-change summaries.
RANK_CHANGE_PERCENTILE_GRID = (50.0, 75.0, 90.0, 95.0, 99.0, 100.0)
PERCENTILE_METHOD = "linear"

CSV_COLUMNS = [
    "input_year",
    "forecast_year",
    "scenario_family",
    "mask_scope",
    "mask_kind",
    "mask_name",
    "masked_ticker",
    "ticker",
    "baseline_rank",
    "masked_rank",
    "signed_rank_delta",
    "absolute_rank_delta",
    "baseline_confidence",
    "masked_confidence",
    "confidence_delta",
    "baseline_score",
    "masked_score",
    "score_delta",
    "selected_feature_count",
    "usable_feature_count",
    "missing_selected_feature_count",
    "ticker_directly_masked",
    "sensitivity_label",
]

_FAMILY_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3}


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #
class MissingnessError(RuntimeError):
    """Controlled failure for any precondition or fail-closed guard."""


class OutputAuthorityError(MissingnessError):
    """Fail-closed refusal of an unauthorized or unsafe output destination.

    A dedicated subclass keeps a refused destination (missing temporary-root
    authority, an out-of-bounds path, a symlinked component) separable from an
    incidental data or schema fault, while still being caught by callers that
    only know about :class:`MissingnessError`.
    """


# --------------------------------------------------------------------------- #
# Year validation (integral-value only; never truncated)
# --------------------------------------------------------------------------- #
# A canonical integer year string: an optional sign followed by digits only.
# ``2025`` is accepted; ``2025.5``, ``2025x``, ``inf``, ``nan`` and ``""`` are
# not.  The repository's trusted datasets store integer years, so a fractional
# or malformed value is a data fault, not something to silently round.
_CANONICAL_INTEGER_YEAR = re.compile(r"[+-]?[0-9]+")


def _to_integral_year(value: Any, *, position: int) -> int:
    """Return a finite integer year, or fail closed — never floor or truncate.

    Integrality is proven *before* any ``int(...)`` conversion: a float year is
    accepted only when ``float.is_integer()`` holds, and a string year only when
    it is a canonical integer literal.  ``2025.5``, both infinities, NaN, empty
    strings, and mixed text such as ``2025x`` are refused rather than coerced.
    """
    if isinstance(value, bool):  # bool is an int subclass; a year is never a bool
        raise MissingnessError(
            f"row {position}: boolean is not a valid year ({value!r})"
        )
    if value is None:
        raise MissingnessError(f"row {position}: null year value is not permitted")
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if math.isnan(number):
            raise MissingnessError(f"row {position}: NaN year value is not permitted")
        if math.isinf(number):
            raise MissingnessError(
                f"row {position}: non-finite year value is not permitted ({number!r})"
            )
        if not number.is_integer():
            raise MissingnessError(
                f"row {position}: fractional year {number!r} is refused; no floor, "
                "truncation, or rounding is applied"
            )
        return int(number)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise MissingnessError(f"row {position}: empty year value is not permitted")
        if not _CANONICAL_INTEGER_YEAR.fullmatch(text):
            raise MissingnessError(
                f"row {position}: {value!r} is not a canonical integer year; "
                "fractional, non-finite, and mixed text values are refused"
            )
        return int(text)
    try:
        is_null = bool(pd.isna(value))
    except (TypeError, ValueError):
        is_null = False
    if is_null:
        raise MissingnessError(f"row {position}: null year value is not permitted")
    raise MissingnessError(
        f"row {position}: {value!r} ({type(value).__name__}) is not a valid year; "
        "ambiguous coercion is not attempted"
    )


# --------------------------------------------------------------------------- #
# Hashing / provenance helpers
# --------------------------------------------------------------------------- #
def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _source_record(path: Path, *, role: str) -> dict[str, Any]:
    path = path.resolve()
    if not path.is_file():
        raise MissingnessError(f"Required R3-MISS-01 source is missing: {path}")
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": _sha256_file(path),
        "size_bytes": path.stat().st_size,
        "role": role,
    }


def _git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except Exception:  # pragma: no cover - provenance is best-effort, never fatal
        return "unknown"


# --------------------------------------------------------------------------- #
# Service loading (read-only seam)
# --------------------------------------------------------------------------- #
def load_service(repo_root: Path) -> ModuleType:
    """Load the unchanged backend service against ``repo_root`` (RESEARCH_REPO_ROOT).

    The service module is executed fresh so its cached repo-root points at
    ``repo_root``. Function-source identity is asserted so a reimplementation can
    never be substituted.
    """
    backend = str(BACKEND)
    if backend not in sys.path:
        sys.path.insert(0, backend)
    previous = os.environ.get("RESEARCH_REPO_ROOT")
    os.environ["RESEARCH_REPO_ROOT"] = str(repo_root)
    try:
        module_name = f"_financeiq_missingness_{hashlib.sha256(str(repo_root).encode()).hexdigest()[:12]}"
        spec = importlib.util.spec_from_file_location(module_name, SERVICE_FILE)
        if spec is None or spec.loader is None:
            raise MissingnessError(f"Could not load service module from {SERVICE_FILE}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        if previous is None:
            os.environ.pop("RESEARCH_REPO_ROOT", None)
        else:
            os.environ["RESEARCH_REPO_ROOT"] = previous

    for function_name in ("train_parameters", "run_forecast", "get_options"):
        function = getattr(module, function_name, None)
        source = Path(inspect.getsourcefile(function) or "").resolve() if function else None
        if function is None or source != SERVICE_FILE.resolve():
            raise MissingnessError(
                f"R3-MISS-01 must invoke {SERVICE_FILE}::{function_name}; got {source}"
            )
    return module


# --------------------------------------------------------------------------- #
# Input universe and category authority
# --------------------------------------------------------------------------- #
_IDENTIFIER_COLUMNS = {"ticker", "year"}


def load_public_frame(path: Path = PUBLIC_DATASET) -> pd.DataFrame:
    """Load and validate the public serving universe used by ``run_forecast``."""
    if not path.is_file():
        raise MissingnessError(f"Public modeling dataset missing: {path}")
    frame = pd.read_csv(path)
    missing = _IDENTIFIER_COLUMNS - set(frame.columns)
    if missing:
        raise MissingnessError(f"{path} missing required identifier columns: {sorted(missing)}")
    if frame["ticker"].isna().any():
        raise MissingnessError(f"{path} contains a null ticker identifier")
    frame["ticker"] = frame["ticker"].astype(str).str.strip().str.upper()
    if (frame["ticker"] == "").any():
        raise MissingnessError(f"{path} contains an empty ticker identifier")
    # Validate integrality element-by-element *before* any integer conversion, so
    # a fractional value such as 2025.5 is refused rather than silently truncated.
    try:
        validated_years = [
            _to_integral_year(value, position=position)
            for position, value in enumerate(frame["year"].tolist())
        ]
    except MissingnessError as exc:
        raise MissingnessError(f"{path} has malformed year values: {exc}") from exc
    frame["year"] = pd.Series(validated_years, index=frame.index, dtype="int64")
    if frame.duplicated(["ticker", "year"]).any():
        dupes = frame.loc[
            frame.duplicated(["ticker", "year"], keep=False), ["ticker", "year"]
        ].sort_values(["year", "ticker"])
        raise MissingnessError(
            f"{path} contains duplicate ticker/year rows: {dupes.to_dict(orient='records')}"
        )
    return frame.sort_values(["year", "ticker"], kind="mergesort").reset_index(drop=True)


def resolve_input_year(service: ModuleType, public: pd.DataFrame) -> int:
    """Trace the latest public-universe serving input year from repository authority.

    Authority: the service's own ``get_options()['default_prediction_year']`` (the
    forward serving/inference year). It is cross-checked against the maximum year
    actually present in the public modeling dataset — never silently hardcoded.
    """
    options = service.get_options()
    default_year = options.get("default_prediction_year")
    if default_year is None:
        raise MissingnessError("Service get_options() did not expose default_prediction_year")
    default_year = int(default_year)
    max_public_year = int(public["year"].max())
    if default_year != max_public_year:
        raise MissingnessError(
            "Service default_prediction_year "
            f"({default_year}) does not match the latest public-universe year "
            f"({max_public_year}); input-year authority is ambiguous"
        )
    if public[public["year"] == default_year].empty:
        raise MissingnessError(f"No public rows for resolved input year {default_year}")
    return default_year


def load_category_authority(path: Path = FEATURE_PASSPORTS) -> dict[str, Any]:
    """Governed feature-category authority = feature_passports source_class.

    ``feature_passports.json`` is the only governed artifact that classifies every
    serving-universe column and publishes its category definitions. Each feature
    maps to exactly one ``source_class`` (its provenance category), which is used
    here purely as a masking grouping — no financial-sector taxonomy is implied.
    """
    if not path.is_file():
        raise MissingnessError(f"Feature passports (category authority) missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    passports = payload.get("passports")
    definitions = payload.get("source_class_definitions")
    if not isinstance(passports, list) or not passports:
        raise MissingnessError(f"{path} has no passports list")
    if not isinstance(definitions, dict) or not definitions:
        raise MissingnessError(f"{path} has no source_class_definitions")
    feature_to_category: dict[str, str] = {}
    for entry in passports:
        name = entry.get("name")
        category = entry.get("source_class")
        if not name or not category:
            continue
        if name in feature_to_category and feature_to_category[name] != category:
            raise MissingnessError(
                f"Contradictory category authority for {name!r} in {path}"
            )
        feature_to_category[name] = category
    if not feature_to_category:
        raise MissingnessError(f"{path} produced no feature->category mapping")
    return {
        "authority_path": path.relative_to(ROOT).as_posix(),
        "authority_field": "feature_passports.json passports[].source_class",
        "category_definitions": {k: definitions[k] for k in sorted(definitions)},
        "feature_to_category": feature_to_category,
    }


@dataclass
class SelectedSet:
    """The current serving-weight feature set and its category structure."""

    weights: dict[str, float]
    ordered_features: list[str]
    feature_category: dict[str, str]
    category_to_features: dict[str, list[str]]
    parameters: list[dict[str, Any]]

    @property
    def categories(self) -> list[str]:
        return sorted(self.category_to_features)


def selected_weight_set(service: ModuleType, authority: dict[str, Any]) -> SelectedSet:
    """Train the fixed serving weights and attach each feature's governed category.

    Weights come from the finalized serving training window (2020-2024, top_n=12),
    exactly what the forward serving path uses. Weights are held fixed across all
    scenarios; only serving-time inputs are masked.
    """
    trained = service.train_parameters(
        train_year_from=2020,
        train_year_to=2024,
        top_n=TOP_N,
        target_mode=service.TARGET_MODE_FINALIZED,
    )
    parameters = trained.get("top_parameters")
    if not parameters:
        raise MissingnessError("Service returned an empty selected-weight set")
    weights: dict[str, float] = {}
    ordered: list[str] = []
    feature_category: dict[str, str] = {}
    category_to_features: dict[str, list[str]] = {}
    mapping = authority["feature_to_category"]
    for item in parameters:
        name = item["name"]
        weight = float(item["weight"])
        if name in weights:
            raise MissingnessError(f"Duplicate feature {name!r} in selected-weight set")
        if name not in mapping:
            raise MissingnessError(
                f"Selected serving feature {name!r} has no governed category mapping "
                f"in {authority['authority_path']}"
            )
        weights[name] = weight
        ordered.append(name)
        category = mapping[name]
        feature_category[name] = category
        category_to_features.setdefault(category, []).append(name)
    for category in category_to_features:
        category_to_features[category] = sorted(category_to_features[category])
    return SelectedSet(
        weights=weights,
        ordered_features=ordered,
        feature_category=feature_category,
        category_to_features=category_to_features,
        parameters=[
            {
                "name": item["name"],
                "weight": float(item["weight"]),
                "rank": int(item["rank"]),
                "category": feature_category[item["name"]],
            }
            for item in parameters
        ],
    )


# --------------------------------------------------------------------------- #
# Temp seam + scoring
# --------------------------------------------------------------------------- #
def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, float_format="%.17g", lineterminator="\n")


class ScoringSession:
    """Owns an isolated temp data root and a service module bound to it.

    Rewriting the public CSV and re-invoking ``run_forecast`` reproduces the exact
    missing-input behavior of the live service without editing the service.
    """

    def __init__(self, public: pd.DataFrame, training: pd.DataFrame, weights: dict[str, float]):
        self._public = public
        self._weights = weights
        self._tmp = tempfile.TemporaryDirectory(prefix="financeiq-r3-miss-01-")
        clean = Path(self._tmp.name) / "data" / "trusted_clean"
        clean.mkdir(parents=True)
        self._public_path = clean / "modeling_dataset_public_2020_2025.csv"
        _write_csv(training, clean / "modeling_dataset_training_2020_2025.csv")
        _write_csv(public, self._public_path)
        _write_csv(public, clean / "modeling_dataset_2020_2025.csv")
        self._service = load_service(Path(self._tmp.name))

    def close(self) -> None:
        self._tmp.cleanup()

    def __enter__(self) -> "ScoringSession":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def score_raw(self, masked_public: pd.DataFrame, input_year: int) -> dict[str, Any]:
        """Write the (possibly masked) public frame and return the RAW service response.

        The complete, unnormalised response is exposed so the unmasked-baseline
        regression guard can compare every public field — top parameters,
        contributions, warnings, inference flags — not only the reduced per-ticker
        rank/score/confidence view the masking scenarios use.
        """
        _write_csv(masked_public, self._public_path)
        return self._service.run_forecast(year=input_year, trained_weights=self._weights)

    def score(self, masked_public: pd.DataFrame, input_year: int) -> dict[str, dict[str, Any]]:
        """Write the (possibly masked) public frame and return per-ticker service output."""
        return self._normalise(self.score_raw(masked_public, input_year), input_year)

    def _normalise(self, result: dict[str, Any], input_year: int) -> dict[str, dict[str, Any]]:
        items = result.get("items")
        if not isinstance(items, list) or not items:
            raise MissingnessError("Service response has no items list")
        if int(result.get("year", -1)) != input_year:
            raise MissingnessError("Service response year mismatch")
        if int(result.get("stock_count", -1)) != len(items):
            raise MissingnessError("Service stock_count mismatch")
        weight_count = len(self._weights)
        out: dict[str, dict[str, Any]] = {}
        for item in items:
            for key in ("ticker", "score", "confidence", "rank", "missing_parameters"):
                if key not in item:
                    raise MissingnessError(f"Service item missing required key {key!r}")
            ticker = str(item["ticker"]).strip().upper()
            score = float(item["score"])
            confidence = float(item["confidence"])
            rank = int(item["rank"])
            if not (np.isfinite(score) and np.isfinite(confidence)):
                raise MissingnessError(f"Service returned non-finite output for {ticker}")
            missing_params = item["missing_parameters"]
            if not isinstance(missing_params, list):
                raise MissingnessError(f"Service missing_parameters is not a list for {ticker}")
            missing_count = len(missing_params)
            usable = weight_count - missing_count
            if usable < 0:
                raise MissingnessError(f"Service reported more missing than selected for {ticker}")
            # Confidence must equal usable/selected exactly (fail closed otherwise).
            if round(usable / max(1, weight_count), 4) != round(confidence, 4):
                raise MissingnessError(
                    f"Service confidence {confidence} inconsistent with usable {usable}/{weight_count} for {ticker}"
                )
            if ticker in out:
                raise MissingnessError(f"Service returned duplicate ticker {ticker}")
            out[ticker] = {
                "score": score,
                "confidence": confidence,
                "rank": rank,
                "missing_count": missing_count,
                "usable_count": usable,
                "confidence_label": item.get("confidence_label"),
            }
        ranks = sorted(row["rank"] for row in out.values())
        if ranks != list(range(1, len(out) + 1)):
            raise MissingnessError("Service ranks are not a strict 1..N ordinal sequence")
        return out


# --------------------------------------------------------------------------- #
# Masking
# --------------------------------------------------------------------------- #
def _mask_frame(
    public: pd.DataFrame,
    input_year: int,
    features: list[str],
    tickers: list[str] | None,
) -> pd.DataFrame:
    """Return a copy with ``features`` set to the service's null value.

    ``tickers=None`` masks every input-year ticker (dataset-wide); otherwise only
    the named tickers' input-year rows are masked. All other rows are untouched.
    """
    frame = public.copy()
    for feature in features:
        if feature not in frame.columns:
            raise MissingnessError(f"Feature {feature!r} absent from public dataset columns")
    year_mask = frame["year"] == input_year
    if tickers is None:
        row_mask = year_mask
    else:
        row_mask = year_mask & frame["ticker"].isin(tickers)
    for feature in features:
        frame.loc[row_mask, feature] = MISSING_VALUE
    return frame


# --------------------------------------------------------------------------- #
# Scenario enumeration + execution
# --------------------------------------------------------------------------- #
@dataclass
class Scenario:
    family: str
    mask_scope: str  # dataset_wide | per_ticker
    mask_kind: str  # category | feature
    mask_name: str
    masked_ticker: str  # "" for dataset_wide
    features: list[str]


def enumerate_scenarios(selected: SelectedSet, cohort: list[str]) -> list[Scenario]:
    """Deterministic, exhaustive scenarios for the four families (no sampling)."""
    scenarios: list[Scenario] = []
    categories = selected.categories
    features = sorted(selected.ordered_features)

    # A. Dataset-wide category masks
    for category in categories:
        scenarios.append(
            Scenario("A", "dataset_wide", "category", category, "", selected.category_to_features[category])
        )
    # B. Per-ticker category masks
    for ticker in cohort:
        for category in categories:
            scenarios.append(
                Scenario("B", "per_ticker", "category", category, ticker, selected.category_to_features[category])
            )
    # C. Dataset-wide single-feature masks
    for feature in features:
        scenarios.append(Scenario("C", "dataset_wide", "feature", feature, "", [feature]))
    # D. Per-ticker single-feature masks
    for ticker in cohort:
        for feature in features:
            scenarios.append(Scenario("D", "per_ticker", "feature", feature, ticker, [feature]))
    return scenarios


def _scenario_sort_key(row: dict[str, Any]) -> tuple:
    return (
        _FAMILY_ORDER[row["scenario_family"]],
        row["mask_scope"],
        row["mask_kind"],
        row["mask_name"],
        row["masked_ticker"],
        row["ticker"],
    )


def _percentiles(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    return {
        f"p{int(q)}": round(float(np.percentile(array, q, method=PERCENTILE_METHOD)), 6)
        for q in RANK_CHANGE_PERCENTILE_GRID
    }


def _membership_checksum(tickers: list[str]) -> str:
    return _sha256_text("\n".join(sorted(tickers)))


@dataclass
class ScenarioResult:
    definition: Scenario
    rows: list[dict[str, Any]]
    summary: dict[str, Any]


def run_scenario(
    session: ScoringSession,
    scenario: Scenario,
    baseline: dict[str, dict[str, Any]],
    public: pd.DataFrame,
    input_year: int,
    forecast_year: int,
    selected: SelectedSet,
) -> ScenarioResult:
    tickers = None if scenario.mask_scope == "dataset_wide" else [scenario.masked_ticker]
    masked_public = _mask_frame(public, input_year, scenario.features, tickers)
    masked = session.score(masked_public, input_year)

    if set(masked) != set(baseline):
        raise MissingnessError(
            f"Scenario {scenario.family}/{scenario.mask_name}/{scenario.masked_ticker} "
            "changed cohort membership"
        )

    weight_count = len(selected.weights)
    directly_masked = set(baseline) if tickers is None else set(tickers)
    rows: list[dict[str, Any]] = []
    for ticker in sorted(baseline):
        base = baseline[ticker]
        mask = masked[ticker]
        signed = mask["rank"] - base["rank"]
        rows.append(
            {
                "input_year": input_year,
                "forecast_year": forecast_year,
                "scenario_family": scenario.family,
                "mask_scope": scenario.mask_scope,
                "mask_kind": scenario.mask_kind,
                "mask_name": scenario.mask_name,
                "masked_ticker": scenario.masked_ticker,
                "ticker": ticker,
                "baseline_rank": base["rank"],
                "masked_rank": mask["rank"],
                "signed_rank_delta": signed,
                "absolute_rank_delta": abs(signed),
                "baseline_confidence": round(base["confidence"], 4),
                "masked_confidence": round(mask["confidence"], 4),
                "confidence_delta": round(mask["confidence"] - base["confidence"], 6),
                "baseline_score": round(base["score"], 4),
                "masked_score": round(mask["score"], 4),
                "score_delta": round(mask["score"] - base["score"], 6),
                "selected_feature_count": weight_count,
                "usable_feature_count": mask["usable_count"],
                "missing_selected_feature_count": mask["missing_count"],
                "ticker_directly_masked": ticker in directly_masked,
                "sensitivity_label": SENSITIVITY_LABEL,
            }
        )

    summary = _summarise_scenario(scenario, rows, baseline, masked, input_year, forecast_year)
    return ScenarioResult(scenario, rows, summary)


def _summarise_scenario(
    scenario: Scenario,
    rows: list[dict[str, Any]],
    baseline: dict[str, dict[str, Any]],
    masked: dict[str, dict[str, Any]],
    input_year: int,
    forecast_year: int,
) -> dict[str, Any]:
    abs_deltas = [row["absolute_rank_delta"] for row in rows]
    conf_deltas = [abs(row["confidence_delta"]) for row in rows]
    moved = [row for row in rows if row["absolute_rank_delta"] > 0]
    # Largest movements: upward = most negative signed delta (toward rank 1).
    upward = min(rows, key=lambda r: (r["signed_rank_delta"], r["ticker"]))
    downward = max(rows, key=lambda r: (r["signed_rank_delta"], -_ticker_ord(r["ticker"])))
    masked_scores = [round(v["score"], 4) for v in masked.values()]
    score_tie_groups = sum(1 for _, count in _value_counts(masked_scores).items() if count > 1)
    base_members = sorted(baseline)
    masked_members = sorted(masked)
    return {
        "scenario_family": scenario.family,
        "mask_scope": scenario.mask_scope,
        "mask_kind": scenario.mask_kind,
        "mask_name": scenario.mask_name,
        "masked_ticker": scenario.masked_ticker,
        "masked_features": list(scenario.features),
        "input_year": input_year,
        "forecast_year": forecast_year,
        "num_tickers": len(rows),
        "num_directly_masked": sum(1 for row in rows if row["ticker_directly_masked"]),
        "num_with_rank_movement": len(moved),
        "max_absolute_rank_delta": max(abs_deltas),
        "mean_absolute_rank_delta": round(float(np.mean(abs_deltas)), 6),
        "median_absolute_rank_delta": round(float(np.median(abs_deltas)), 6),
        "rank_change_percentiles": _percentiles(abs_deltas),
        "mean_absolute_confidence_change": round(float(np.mean(conf_deltas)), 6),
        "max_absolute_confidence_change": round(float(np.max(conf_deltas)), 6),
        "largest_upward_rank_movement": {
            "ticker": upward["ticker"],
            "signed_rank_delta": upward["signed_rank_delta"],
        },
        "largest_downward_rank_movement": {
            "ticker": downward["ticker"],
            "signed_rank_delta": downward["signed_rank_delta"],
        },
        "strict_ordinal_ranks": True,
        "masked_score_tie_groups": score_tie_groups,
        "baseline_membership_checksum": _membership_checksum(base_members),
        "masked_membership_checksum": _membership_checksum(masked_members),
        "cohort_membership_changed": base_members != masked_members,
        "sensitivity_label": SENSITIVITY_LABEL,
    }


def _ticker_ord(ticker: str) -> int:
    # Deterministic tie-break helper for max() on downward movement.
    return int.from_bytes(hashlib.sha256(ticker.encode()).digest()[:6], "big")


def _value_counts(values: list[float]) -> dict[float, int]:
    counts: dict[float, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


# --------------------------------------------------------------------------- #
# Aggregation across scenarios
# --------------------------------------------------------------------------- #
def _grouped_summary(scenario_summaries: list[dict[str, Any]], key: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for summary in scenario_summaries:
        groups.setdefault(str(summary[key]), []).append(summary)
    out: dict[str, Any] = {}
    for name in sorted(groups):
        members = groups[name]
        out[name] = {
            "scenario_count": len(members),
            "mean_absolute_rank_delta": round(
                float(np.mean([m["mean_absolute_rank_delta"] for m in members])), 6
            ),
            "max_absolute_rank_delta": max(m["max_absolute_rank_delta"] for m in members),
            "mean_absolute_confidence_change": round(
                float(np.mean([m["mean_absolute_confidence_change"] for m in members])), 6
            ),
            "max_absolute_confidence_change": round(
                float(np.max([m["max_absolute_confidence_change"] for m in members])), 6
            ),
        }
    return out


def _feature_grouped_summary(
    scenario_summaries: list[dict[str, Any]], selected: SelectedSet
) -> dict[str, Any]:
    feature_names = set(selected.ordered_features)
    feature_summaries = [s for s in scenario_summaries if s["mask_name"] in feature_names and s["mask_kind"] == "feature"]
    return _grouped_summary(feature_summaries, "mask_name")


def _category_grouped_summary(scenario_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    category_summaries = [s for s in scenario_summaries if s["mask_kind"] == "category"]
    return _grouped_summary(category_summaries, "mask_name")


def _extreme_observation(all_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Neutral maximum-movement diagnostic — not a model-quality claim."""
    extreme = max(
        all_rows,
        key=lambda r: (
            r["absolute_rank_delta"],
            _FAMILY_ORDER[r["scenario_family"]] * -1,
        ),
    )
    # Deterministic tie-break: smallest sort key wins among equal absolute deltas.
    top_delta = extreme["absolute_rank_delta"]
    candidates = [r for r in all_rows if r["absolute_rank_delta"] == top_delta]
    chosen = min(candidates, key=_scenario_sort_key)
    return {
        "note": (
            "Deterministic maximum observed rank movement across all scenarios. "
            "This is an extreme sensitivity observation, not a claim about model "
            "quality, robustness, or reliability."
        ),
        "scenario_family": chosen["scenario_family"],
        "mask_scope": chosen["mask_scope"],
        "mask_kind": chosen["mask_kind"],
        "mask_name": chosen["mask_name"],
        "masked_ticker": chosen["masked_ticker"],
        "ticker": chosen["ticker"],
        "absolute_rank_delta": chosen["absolute_rank_delta"],
        "signed_rank_delta": chosen["signed_rank_delta"],
        "sensitivity_label": SENSITIVITY_LABEL,
    }


# --------------------------------------------------------------------------- #
# Report assembly
# --------------------------------------------------------------------------- #
@dataclass
class Computation:
    input_year: int
    forecast_year: int
    cohort: list[str]
    selected: SelectedSet
    authority: dict[str, Any]
    baseline: dict[str, dict[str, Any]]
    baseline_replay_matches_service: bool
    scenario_results: list[ScenarioResult] = field(default_factory=list)

    @property
    def all_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for result in self.scenario_results:
            rows.extend(result.rows)
        return sorted(rows, key=_scenario_sort_key)

    @property
    def scenario_summaries(self) -> list[dict[str, Any]]:
        summaries = [result.summary for result in self.scenario_results]
        return sorted(summaries, key=lambda s: (_FAMILY_ORDER[s["scenario_family"]], s["mask_scope"], s["mask_kind"], s["mask_name"], s["masked_ticker"]))


# Complete public service-response field inventory that the unmasked baseline
# regression guard now enforces (recorded verbatim in the artifact so the
# provenance claim matches exactly what is compared). The guard compares the WHOLE
# response recursively as canonical serialized bytes, so any field added to a
# future response is included automatically; this list documents the current set.
BASELINE_REPLAY_COMPARED_FIELDS = [
    "year",
    "user_type",
    "risk_level",
    "stock_count",
    "disclaimer",
    "items[].ticker",
    "items[].score",
    "items[].confidence",
    "items[].confidence_label",
    "items[].rank",
    "items[].missing_parameters",
    "items[].is_inference_row",
    "items[].warnings",
    "items[].top_parameters[].name",
    "items[].top_parameters[].weight",
    "items[].top_parameters[].value",
    "items[].top_parameters[].percentile_in_year",
    "items[].top_parameters[].contribution",
]


def _canonicalize_for_comparison(value: Any) -> Any:
    """Deterministic, JSON-safe canonical form of a full service response.

    Dictionaries are ordered by key; sequences keep their order; NaN/infinity,
    ``Decimal``, ``date``/``datetime``, ``Enum``, and numpy scalar types map to
    explicit deterministic tokens.  No public field is dropped: the whole response
    is walked recursively, and an unexpected value *type* raises rather than being
    silently compared by ``repr`` — a future field of an unforeseen type causes a
    controlled fail-closed schema mismatch instead of a false match.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        if math.isnan(value):
            return "__nan__"
        if math.isinf(value):
            return "__+inf__" if value > 0 else "__-inf__"
        return value
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return _canonicalize_for_comparison(float(value))
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, Decimal):
        return f"__decimal__:{value}"
    if isinstance(value, (datetime, date)):
        return f"__datetime__:{value.isoformat()}"
    if isinstance(value, Enum):
        return _canonicalize_for_comparison(value.value)
    if isinstance(value, dict):
        return {
            str(key): _canonicalize_for_comparison(item)
            for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonicalize_for_comparison(item) for item in value]
    raise MissingnessError(
        "unsupported field type in service response for canonical baseline "
        f"comparison: {type(value)!r}; failing closed on a schema mismatch"
    )


def canonical_service_response(result: dict[str, Any]) -> str:
    """Canonical serialized bytes of a complete service response, for exact compare."""
    return json.dumps(
        _canonicalize_for_comparison(result), sort_keys=True, ensure_ascii=False
    )


def compute(
    *,
    public_path: Path = PUBLIC_DATASET,
    training_path: Path = TRAINING_DATASET,
) -> Computation:
    public = load_public_frame(public_path)
    if not training_path.is_file():
        raise MissingnessError(f"Training modeling dataset missing: {training_path}")
    training = pd.read_csv(training_path)
    training["ticker"] = training["ticker"].astype(str).str.strip().str.upper()

    authority = load_category_authority()

    # Ground-truth baseline: invoke the service directly against the real repo.
    real_service = load_service(ROOT)
    input_year = resolve_input_year(real_service, public)
    forecast_year = input_year + 1
    selected = selected_weight_set(real_service, authority)
    baseline_raw = real_service.run_forecast(input_year, selected.weights)

    # Normalise the direct baseline through the same validator used for scenarios.
    baseline = _normalise_direct(baseline_raw, input_year, selected.weights)
    cohort = sorted(baseline)

    with ScoringSession(public, training, selected.weights) as session:
        replay_raw = session.score_raw(public, input_year)
        replay = session._normalise(replay_raw, input_year)
        replay_matches = replay == baseline
        if not replay_matches:
            raise MissingnessError(
                "Unmasked seam replay does not match the direct service output; failing closed"
            )
        # Complete-response regression guard: the unmasked seam replay must equal
        # the direct service response across EVERY public field — top-parameter
        # objects (names, values, weights, percentiles, contributions), warnings,
        # confidence labels, inference flags, and every top-level field — compared
        # as canonical serialized bytes, not merely the reduced per-ticker
        # rank/score/confidence view the masking scenarios rely on.
        if canonical_service_response(baseline_raw) != canonical_service_response(replay_raw):
            raise MissingnessError(
                "Unmasked seam replay does not match the COMPLETE direct service "
                "response (a public field beyond rank/score/confidence differs); "
                "failing closed"
            )
        comp = Computation(
            input_year=input_year,
            forecast_year=forecast_year,
            cohort=cohort,
            selected=selected,
            authority=authority,
            baseline=baseline,
            baseline_replay_matches_service=replay_matches,
        )
        for scenario in enumerate_scenarios(selected, cohort):
            comp.scenario_results.append(
                run_scenario(session, scenario, baseline, public, input_year, forecast_year, selected)
            )
    return comp


def _normalise_direct(result: dict[str, Any], input_year: int, weights: dict[str, float]) -> dict[str, dict[str, Any]]:
    """Validate a direct (non-seam) service response identically to seam scoring."""
    helper = ScoringSession.__new__(ScoringSession)
    helper._weights = weights  # type: ignore[attr-defined]
    return ScoringSession._normalise(helper, result, input_year)


def build_report(comp: Computation) -> dict[str, Any]:
    scenario_summaries = comp.scenario_summaries
    all_rows = comp.all_rows
    counts = {
        "A_dataset_wide_category": sum(1 for s in scenario_summaries if s["scenario_family"] == "A"),
        "B_per_ticker_category": sum(1 for s in scenario_summaries if s["scenario_family"] == "B"),
        "C_dataset_wide_feature": sum(1 for s in scenario_summaries if s["scenario_family"] == "C"),
        "D_per_ticker_feature": sum(1 for s in scenario_summaries if s["scenario_family"] == "D"),
    }
    counts["total_scenarios"] = sum(counts.values())

    csv_text = render_csv(all_rows)
    md_text = ""  # filled by caller after JSON assembled (md embeds json-derived fields)

    report = {
        "schema_version": SCHEMA_VERSION,
        "task": TASK_ID,
        "mandatory_sensitivity_label": SENSITIVITY_LABEL,
        "claim_boundary": SENSITIVITY_LABEL,
        "predictive_skill_measured": False,
        "predictive_skill_statement": PREDICTIVE_SKILL_STATEMENT,
        "rank_delta_sign_convention": RANK_DELTA_SIGN_CONVENTION,
        "generation_provenance": {
            "generator": Path(__file__).resolve().relative_to(ROOT).as_posix(),
            "regeneration_command": REGENERATION_COMMAND,
            "git_commit": _git_commit(),
            "hand_edit_forbidden": True,
            "timestamp_policy": "omitted for byte-deterministic regeneration",
            "determinism": "no random sampling; exhaustive deterministic scenarios",
        },
        "analysis_universe": {
            "input_year": comp.input_year,
            "forecast_year": comp.forecast_year,
            "input_year_authority": "forecasting_csv_service.get_options()['default_prediction_year'], cross-checked against max public year",
            "forecast_year_authority": "forecasting_csv_service.inference_forecast target_year = input_year + 1",
            "ticker_count": len(comp.cohort),
            "cohort": list(comp.cohort),
            "cohort_membership_checksum": _membership_checksum(comp.cohort),
            "selected_feature_count": len(comp.selected.weights),
            "public_dataset": PUBLIC_DATASET.relative_to(ROOT).as_posix(),
            "public_dataset_sha256": _sha256_file(PUBLIC_DATASET),
            "training_dataset": TRAINING_DATASET.relative_to(ROOT).as_posix(),
            "training_dataset_sha256": _sha256_file(TRAINING_DATASET),
            "service_path": SERVICE_FILE.relative_to(ROOT).as_posix(),
            "service_sha256": _sha256_file(SERVICE_FILE),
        },
        "feature_category_authority": {
            "authority_path": comp.authority["authority_path"],
            "authority_field": comp.authority["authority_field"],
            "note": (
                "source_class is a governed provenance classification covering every "
                "serving-universe column; used here only as a masking grouping, not a "
                "financial-sector taxonomy."
            ),
            "category_definitions": comp.authority["category_definitions"],
            "selected_set_categories": comp.selected.categories,
            "category_to_selected_features": {
                category: comp.selected.category_to_features[category]
                for category in comp.selected.categories
            },
        },
        "selected_weight_set": comp.selected.parameters,
        "missingness_semantics": {
            "representation": "null (NaN) written into the service's public input rows",
            "not_used": ["zero", "median", "sentinel value", "new imputation policy"],
            "service_null_path": (
                "run_forecast drops the feature from the within-year percentile pool, "
                "omits its contribution, counts it as missing, and reduces confidence."
            ),
        },
        "baseline_replay_audit": {
            "unmasked_replay_matches_service_output": comp.baseline_replay_matches_service,
            "comparison_method": (
                "complete service response compared as canonical serialized bytes "
                "(recursive key-ordered JSON canonicalization of every public field); "
                "no public field is omitted"
            ),
            "compared_fields": list(BASELINE_REPLAY_COMPARED_FIELDS),
            "invocation_mechanism": (
                "The unchanged backend service is loaded read-only against an isolated "
                "temporary data root via the documented RESEARCH_REPO_ROOT override; "
                "the seam replay of the unmasked cohort is byte-compared to the direct "
                "service output and fails closed on any difference."
            ),
            "functions_invoked": [
                "backend/app/services/forecasting_csv_service.py::train_parameters",
                "backend/app/services/forecasting_csv_service.py::run_forecast",
                "backend/app/services/forecasting_csv_service.py::get_options",
            ],
            "approximation_or_reimplementation_used": False,
        },
        "scenario_definitions": {
            "families": {
                "A": "Dataset-wide category masks: mask all selected features in a category for every ticker.",
                "B": "Per-ticker category masks: mask all selected features in a category for one ticker only.",
                "C": "Dataset-wide single-feature masks: mask one selected feature for every ticker.",
                "D": "Per-ticker single-feature masks: mask one selected feature for one ticker only.",
            },
            "counts": counts,
            "sampling": "none — exhaustive deterministic enumeration",
        },
        "scenario_summaries": scenario_summaries,
        "aggregate_summaries": {
            "by_category": _category_grouped_summary(scenario_summaries),
            "by_feature": _feature_grouped_summary(scenario_summaries, comp.selected),
            "by_mask_scope": _grouped_summary(scenario_summaries, "mask_scope"),
            "by_scenario_family": _grouped_summary(scenario_summaries, "scenario_family"),
            "extreme_observed_sensitivity": _extreme_observation(all_rows),
        },
        "row_level_evidence": {
            "csv_path": CSV_OUTPUT.relative_to(ROOT).as_posix(),
            "row_count": len(all_rows),
            "columns": list(CSV_COLUMNS),
            "csv_sha256": _sha256_text(csv_text),
        },
        "source_artifacts": [
            _source_record(SERVICE_FILE, role="authoritative serving implementation invoked read-only"),
            _source_record(Path(__file__), role="R3-MISS-01 deterministic sensitivity generator"),
            _source_record(PUBLIC_DATASET, role="public serving-universe input scored by run_forecast"),
            _source_record(TRAINING_DATASET, role="training input for the fixed selected serving weights"),
            _source_record(FEATURE_PASSPORTS, role="governed feature-category (source_class) authority"),
        ],
        "artifact_ownership": {
            "owner": REGENERATION_COMMAND,
            "regeneration_command": REGENERATION_COMMAND,
            "hand_edit_forbidden": True,
            "generated_artifacts": [
                JSON_OUTPUT.relative_to(ROOT).as_posix(),
                MARKDOWN_OUTPUT.relative_to(ROOT).as_posix(),
                CSV_OUTPUT.relative_to(ROOT).as_posix(),
            ],
        },
        "limitations": [
            "Serving-heuristic sensitivity only: this measures how one fixed deterministic ranking recipe reacts to omitted inputs, not predictive skill.",
            "A small rank delta is not robustness, reliability, validation, or stability of predictive skill; the walk-forward IC remains indistinguishable from the null.",
            "Only the latest public-universe input year and its retrospective cohort are analysed; results do not generalise across years, universes, or regimes.",
            "Masking uses the service's own null path; no value is fabricated, imputed, zeroed, or sentinel-filled.",
            "Feature categories are the governed source_class provenance grouping, not a financial-sector taxonomy.",
            "The selected-weight feature set is fixed from finalized 2020-2024 training; training-time missingness is out of scope.",
            "Exact byte reproduction is numerical-environment-qualified (Python/platform/package versions).",
            "Research support only; not investment advice.",
        ],
        "claim_boundary_statement": PREDICTIVE_SKILL_STATEMENT,
    }
    report["_markdown_placeholder"] = md_text  # replaced in render; removed before write
    return report


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def render_csv(rows: list[dict[str, Any]]) -> str:
    ordered = sorted(rows, key=_scenario_sort_key)
    frame = pd.DataFrame(ordered, columns=CSV_COLUMNS)
    return frame.to_csv(index=False, lineterminator="\n")


def render_markdown(report: dict[str, Any]) -> str:
    universe = report["analysis_universe"]
    counts = report["scenario_definitions"]["counts"]
    agg = report["aggregate_summaries"]
    lines = [
        f"# Serving-heuristic missingness sensitivity ({TASK_ID})",
        "",
        f"> **{SENSITIVITY_LABEL}**",
        "",
        report["predictive_skill_statement"],
        "",
        "## Analysis universe",
        "",
        f"- Input year: **{universe['input_year']}** (authority: {universe['input_year_authority']})",
        f"- Forecast year: **{universe['forecast_year']}** ({universe['forecast_year_authority']})",
        f"- Cohort tickers: **{universe['ticker_count']}**",
        f"- Selected serving-weight features: **{universe['selected_feature_count']}**",
        f"- Service: `{universe['service_path']}` (sha256 `{universe['service_sha256']}`)",
        f"- Public dataset: `{universe['public_dataset']}` (sha256 `{universe['public_dataset_sha256']}`)",
        "",
        "## Feature-category authority",
        "",
        f"- Authority: `{report['feature_category_authority']['authority_path']}` "
        f"({report['feature_category_authority']['authority_field']})",
        f"- {report['feature_category_authority']['note']}",
        "",
        "| Category | Selected features |",
        "| --- | --- |",
    ]
    for category in report["feature_category_authority"]["selected_set_categories"]:
        feats = ", ".join(report["feature_category_authority"]["category_to_selected_features"][category])
        lines.append(f"| `{category}` | {feats} |")
    lines.extend(
        [
            "",
            "## Baseline replay audit",
            "",
            f"- Unmasked seam replay matches the live service output: "
            f"**{report['baseline_replay_audit']['unmasked_replay_matches_service_output']}**",
            f"- {report['baseline_replay_audit']['invocation_mechanism']}",
            "",
            "## Rank-delta sign convention",
            "",
            report["rank_delta_sign_convention"],
            "",
            "## Missingness semantics",
            "",
            f"- Representation: {report['missingness_semantics']['representation']}",
            f"- Service null path: {report['missingness_semantics']['service_null_path']}",
            "",
            "## Scenario families (exhaustive, deterministic — no sampling)",
            "",
            "| Family | Description | Scenarios |",
            "| --- | --- | ---: |",
            f"| A | {report['scenario_definitions']['families']['A']} | {counts['A_dataset_wide_category']} |",
            f"| B | {report['scenario_definitions']['families']['B']} | {counts['B_per_ticker_category']} |",
            f"| C | {report['scenario_definitions']['families']['C']} | {counts['C_dataset_wide_feature']} |",
            f"| D | {report['scenario_definitions']['families']['D']} | {counts['D_per_ticker_feature']} |",
            f"| — | Total | {counts['total_scenarios']} |",
            "",
            "## Aggregate sensitivity by scenario family",
            "",
            "| Family | Scenarios | Mean abs rank Δ | Max abs rank Δ | Mean abs conf Δ | Max abs conf Δ |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for family in sorted(agg["by_scenario_family"]):
        row = agg["by_scenario_family"][family]
        lines.append(
            f"| {family} | {row['scenario_count']} | {row['mean_absolute_rank_delta']} | "
            f"{row['max_absolute_rank_delta']} | {row['mean_absolute_confidence_change']} | "
            f"{row['max_absolute_confidence_change']} |"
        )
    lines.extend(
        [
            "",
            "## Aggregate sensitivity by governed category",
            "",
            "| Category | Scenarios | Mean abs rank Δ | Max abs rank Δ | Mean abs conf Δ | Max abs conf Δ |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for category in sorted(agg["by_category"]):
        row = agg["by_category"][category]
        lines.append(
            f"| `{category}` | {row['scenario_count']} | {row['mean_absolute_rank_delta']} | "
            f"{row['max_absolute_rank_delta']} | {row['mean_absolute_confidence_change']} | "
            f"{row['max_absolute_confidence_change']} |"
        )
    lines.extend(
        [
            "",
            "## Aggregate sensitivity by selected feature",
            "",
            "| Feature | Scenarios | Mean abs rank Δ | Max abs rank Δ | Mean abs conf Δ | Max abs conf Δ |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for feature in sorted(agg["by_feature"]):
        row = agg["by_feature"][feature]
        lines.append(
            f"| `{feature}` | {row['scenario_count']} | {row['mean_absolute_rank_delta']} | "
            f"{row['max_absolute_rank_delta']} | {row['mean_absolute_confidence_change']} | "
            f"{row['max_absolute_confidence_change']} |"
        )
    extreme = agg["extreme_observed_sensitivity"]
    lines.extend(
        [
            "",
            "## Extreme observed sensitivity (neutral diagnostic)",
            "",
            extreme["note"],
            "",
            f"- Family {extreme['scenario_family']} / {extreme['mask_scope']} / "
            f"`{extreme['mask_name']}`"
            + (f" (masked ticker `{extreme['masked_ticker']}`)" if extreme["masked_ticker"] else "")
            + f": ticker `{extreme['ticker']}` moved {extreme['signed_rank_delta']} rank(s) "
            f"(absolute {extreme['absolute_rank_delta']}).",
            "",
            "## Row-level evidence",
            "",
            f"Complete per-ticker-scenario evidence: `{report['row_level_evidence']['csv_path']}` "
            f"({report['row_level_evidence']['row_count']} rows).",
            "",
            "## Limitations and claim boundary",
            "",
            *[f"- {item}" for item in report["limitations"]],
            "",
            f"> **{SENSITIVITY_LABEL}**",
            "",
            report["claim_boundary_statement"],
            "",
            "## Ownership",
            "",
            f"Owner / regeneration command: `{report['artifact_ownership']['regeneration_command']}`. "
            "Generated files must not be hand-edited.",
            "",
        ]
    )
    markdown = "\n".join(lines)
    _assert_no_forbidden_claims(markdown)
    return markdown


# Affirmative claim phrases that must never appear (the reports deny these terms,
# so bare single words are intentionally excluded — only positive constructions
# are forbidden, following the R3-SERV-01 precedent).
_FORBIDDEN_CLAIM_TERMS = (
    "predictive robustness",
    "predictive reliability",
    "predictive stability",
    "validated missingness tolerance",
    "reliable predictive edge",
    "establishes alpha",
    "generates alpha",
    "is profitable",
    "profitable trading",
    "validated alpha",
    "tradable strategy",
    "tradeable strategy",
    "deployment-ready",
    "production-ready",
    "buy signal",
    "sell signal",
    "market-beating",
    "outperforms the market",
    "most robust",
    "most reliable",
    "winning feature",
    "best feature",
)


def _assert_no_forbidden_claims(text: str) -> None:
    lowered = text.lower()
    hits = [term for term in _FORBIDDEN_CLAIM_TERMS if term in lowered]
    if hits:
        raise MissingnessError(f"Generated output contains forbidden claim wording: {hits}")


# --------------------------------------------------------------------------- #
# Output confinement (canonical namespace, or an explicitly-bounded temp root)
# --------------------------------------------------------------------------- #
# Governed canonical destination.  Normal ``make research-missingness`` execution
# writes here and nowhere else; there is no override on that path.
CANONICAL_RESULTS_DIR = RESULTS_DIR

# Exactly these three basenames may ever be written — nothing else.
GOVERNED_OUTPUT_NAMES = (JSON_OUTPUT.name, MARKDOWN_OUTPUT.name, CSV_OUTPUT.name)

# Canonical publication is anchored beneath the *real* repository: the governed
# output directory (``results_missingness``) is the last component of the
# ``experiments`` directory, itself a component of the repository root.  These
# names drive the descriptor walk that refuses a symlinked ancestor, a symlinked
# canonical directory, or a canonical path that is not a genuine directory.
CANONICAL_PARENT_NAME = CANONICAL_RESULTS_DIR.parent.name  # "experiments"
CANONICAL_CHILD_NAME = CANONICAL_RESULTS_DIR.name  # "results_missingness"

# Descriptor-anchored publication flags.  ``O_NOFOLLOW``/``O_DIRECTORY`` are
# present on Linux and macOS; ``getattr`` keeps the import portable if a platform
# lacks them (in which case the lexical symlink guards still apply).
_O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
_O_DIRECTORY = getattr(os, "O_DIRECTORY", 0)


def _open_dir_path(path: Path) -> int:
    """Open an absolute directory path; its *final* component must not be a symlink.

    ``O_NOFOLLOW`` refuses only a symlinked trailing component (a symlinked
    ancestor in the operating-system path leading to a legitimate root — the
    macOS ``/var`` -> ``/private/var`` link — is followed as usual, exactly as
    the temporary-root scan already tolerates).
    """
    return os.open(str(path), os.O_RDONLY | _O_DIRECTORY | _O_NOFOLLOW)


def _open_dir_component(name: str, *, dir_fd: int) -> int:
    """Open a single directory *component* relative to ``dir_fd``, never following it.

    A symlinked component raises ``OSError`` (``ELOOP``) from ``os.open`` rather
    than being silently traversed — this is what turns a swapped-in symlink into
    a hard failure instead of an escape.
    """
    return os.open(name, os.O_RDONLY | _O_DIRECTORY | _O_NOFOLLOW, dir_fd=dir_fd)


def _open_canonical_parent(repo_root: Path, *, child_name: str = CANONICAL_CHILD_NAME) -> tuple[int, str]:
    """Return ``(experiments_dir_fd, child_name)`` anchored beneath the real repo.

    The chain ``repo_root`` -> ``experiments`` -> ``results_missingness`` is walked
    with per-component ``O_NOFOLLOW`` opens so a symlinked repository root, a
    symlinked ``experiments`` ancestor, or a symlinked/non-directory canonical
    output directory all fail closed.  The returned descriptor is owned by the
    caller, which must close it.  ``repo_root``/``child_name`` are parameters so
    tests can exercise the same authority against isolated fake repositories.
    """
    repo_root = Path(repo_root)
    if repo_root.is_symlink():
        raise OutputAuthorityError(f"repository root must not be a symlink: {repo_root}")
    if not repo_root.is_dir():
        raise OutputAuthorityError(f"repository root is not a directory: {repo_root}")
    try:
        root_fd = _open_dir_path(repo_root)
    except OSError as exc:
        raise OutputAuthorityError(
            f"cannot anchor repository root {repo_root}: {exc}"
        ) from exc
    try:
        exp_fd = _open_dir_component(CANONICAL_PARENT_NAME, dir_fd=root_fd)
    except OSError as exc:
        raise OutputAuthorityError(
            f"cannot anchor canonical '{CANONICAL_PARENT_NAME}' directory under "
            f"{repo_root} (a symlinked or missing ancestor is refused): {exc}"
        ) from exc
    finally:
        os.close(root_fd)
    # The canonical output directory, when it already exists, must be a genuine
    # directory — never a symlink and never another file type.  When it does not
    # yet exist the transactional publisher creates it in place.
    try:
        info = os.stat(child_name, dir_fd=exp_fd, follow_symlinks=False)
    except FileNotFoundError:
        return exp_fd, child_name
    except OSError as exc:
        os.close(exp_fd)
        raise OutputAuthorityError(
            f"cannot inspect canonical output directory {child_name!r}: {exc}"
        ) from exc
    if stat.S_ISLNK(info.st_mode):
        os.close(exp_fd)
        raise OutputAuthorityError(
            f"canonical output directory {child_name!r} is a symlink; refusing"
        )
    if not stat.S_ISDIR(info.st_mode):
        os.close(exp_fd)
        raise OutputAuthorityError(
            f"canonical output path {child_name!r} is not a genuine directory"
        )
    return exp_fd, child_name


def _assert_canonical_chain_safe() -> None:
    """Validate (and immediately release) the canonical publication chain."""
    exp_fd, _child = _open_canonical_parent(ROOT)
    os.close(exp_fd)


def _assert_within(candidate: Path, base: Path) -> Path:
    """Confine a single output *name* to ``base`` (basename-level guard).

    Rejects absolute escapes and ``..`` traversal so a crafted output name can
    never write outside the chosen results directory.  Directory-level authority
    is enforced separately by :func:`resolve_output_authority`.
    """
    base_resolved = base.resolve()
    resolved = (base_resolved / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    if resolved != base_resolved and base_resolved not in resolved.parents:
        raise MissingnessError(f"Refusing to write outside {base_resolved}: {resolved}")
    return resolved


def _is_strictly_within(child: Path, parent: Path) -> bool:
    """True iff ``child`` is a strict descendant of ``parent`` (secure containment).

    Uses ``os.path.commonpath`` rather than a string prefix, so ``/a/bc`` is not
    treated as living under ``/a/b``.
    """
    try:
        common = os.path.commonpath([str(child), str(parent)])
    except ValueError:  # different drives / mixed absolute+relative
        return False
    return common == str(parent) and child != parent


def _normalize_publication_path(path: Path | str) -> Path:
    """Canonicalize a destination *without* resolving its final component.

    The parent chain is fully resolved, so two spellings of the same real parent
    agree and destination identity is stable across the authorization-to-
    publication window.  The governed final component is deliberately kept as a
    *name*: resolving it would follow a symlink planted at that name and silently
    retarget the whole publication at the link's target, which is exactly the
    substitution the publication authorities must refuse.  Keeping the name means
    a substituted symlink cannot change which authority applies — the bound
    device/inode contract decides, and it fails closed.
    """
    candidate = Path(path)
    parent = candidate.parent
    if parent == candidate:  # a filesystem root has no separable final component
        return Path(os.path.realpath(str(candidate)))
    return Path(os.path.realpath(str(parent))) / candidate.name


def _normalize_authority_root(temp_root: Path | str) -> str:
    """Canonical string form of a temporary-root authority (for ledger keys)."""
    return os.path.realpath(str(Path(temp_root)))


def _reject_symlinked_components_below(base: Path, relative_parts: tuple[str, ...], *, label: str) -> None:
    """Reject a symlink in any *existing* component strictly below ``base``.

    Only components between the authorized ``base`` (the temporary root) and the
    destination are inspected; the operating-system path *leading to* ``base`` is
    not (on macOS a legitimate temporary root normally sits under the ``/var`` ->
    ``/private/var`` symlink, which is not an escape).  ``Path.is_symlink`` is an
    lstat that does not follow links.  Traversal stops at the first component that
    does not exist yet — nothing below a missing component can be a live symlink.
    """
    walked = base
    for part in relative_parts:
        walked = walked / part
        if walked.is_symlink():
            raise OutputAuthorityError(
                f"{label}: symlinked path component is not permitted: {walked}"
            )
        if not walked.exists():
            break


def resolve_output_authority(
    results_dir: Path | None, temp_root: Path | None, *, retain: bool = True
) -> Path:
    """Resolve and authorize the output directory; fail closed on anything unsafe.

    Unless ``retain`` is false (used internally by :func:`authorize_publication`
    to avoid re-entrancy), the authorized descriptor/device/inode chain is retained
    in a bounded ledger keyed by the destination, so a later publication that is
    handed only the resolved path revalidates the very chain that was authorized
    rather than re-walking the pathname.

    Retention also records a durable *claim* on the destination.  From then on,
    publication into that destination requires the live retained authority: a
    missing, released, evicted, stale, or mismatched authority fails closed rather
    than silently reverting to path-only validation, which is what previously let a
    symlink substituted at the governed final directory redirect publication into
    the link's target.  The returned path keeps the governed final component as a
    *name* (:func:`_normalize_publication_path`), so a later substitution cannot
    change which authority applies.
    """
    destination = _resolve_output_destination(results_dir, temp_root)
    if retain:
        authority = authorize_publication(results_dir, temp_root)
        _retain_authority(authority, _authority_key(destination, temp_root))
        _record_legacy_claim(destination, temp_root)
    return destination


def _resolve_output_destination(
    results_dir: Path | None, temp_root: Path | None
) -> Path:
    """Validate the requested destination and return the authorized path.

    Two — and only two — kinds of destination are accepted:

    * **Canonical execution** (no temporary-root authority): output goes to
      :data:`CANONICAL_RESULTS_DIR` and nowhere else.  A caller-supplied
      ``results_dir`` is honoured only when it *is* the canonical directory; any
      other directory without an explicit temporary-root authority is refused.
      This is what closes the reviewer's ``--results-dir backend/...`` escape.

    * **Temporary execution** (isolated tests / verification): the caller must
      supply *both* a ``temp_root`` authority *and* a ``results_dir`` destination.
      The destination must resolve strictly beneath the resolved temporary root,
      must not be the repository or any in-repository path, must not traverse via
      ``..`` or an absolute escape, and must not pass through any symlinked
      component.  ``temp_root`` itself must be an existing absolute directory
      outside the repository — an ambiguous or nonexistent authority is refused.
    """
    repo = ROOT.resolve()

    if temp_root is None:
        if results_dir is None:
            _assert_canonical_chain_safe()
            return CANONICAL_RESULTS_DIR
        candidate = Path(results_dir)
        # Compared without resolving the governed final component: a directory that
        # merely *resolves* into the canonical namespace through a substituted
        # symlink is a different destination, not the canonical one.
        try:
            same = _normalize_publication_path(candidate) == _normalize_publication_path(
                CANONICAL_RESULTS_DIR
            )
        except OSError:
            same = False
        if same:
            _assert_canonical_chain_safe()
            return CANONICAL_RESULTS_DIR
        raise OutputAuthorityError(
            "a non-canonical results directory requires an explicit temporary-root "
            f"authority; refusing {candidate} (canonical is "
            f"{CANONICAL_RESULTS_DIR.relative_to(repo).as_posix()})"
        )

    # --- Temporary execution: both a bounded authority and a destination. ---
    if results_dir is None:
        raise OutputAuthorityError(
            "temporary execution requires an explicit destination alongside the "
            "temporary-root authority"
        )

    root = Path(temp_root)
    if not root.is_absolute():
        raise OutputAuthorityError(
            f"temporary-root authority must be an absolute path: {root}"
        )
    if ".." in root.parts:
        raise OutputAuthorityError(
            f"temporary-root authority must not contain '..': {root}"
        )
    if not root.exists():
        raise OutputAuthorityError(
            f"temporary-root authority does not exist: {root}"
        )
    # The authority itself must be a genuine directory, never a symlink: a
    # symlinked temporary root could otherwise redirect the whole bounded tree
    # outside the intended sandbox before any component scan even begins.
    if root.is_symlink():
        raise OutputAuthorityError(
            f"temporary-root authority must not be a symlink: {root}"
        )
    real_root = root.resolve()
    if not real_root.is_dir():
        raise OutputAuthorityError(
            f"temporary-root authority is not a directory: {root}"
        )
    if real_root == repo or _is_strictly_within(real_root, repo):
        raise OutputAuthorityError(
            "temporary-root authority must be outside the repository"
        )

    dest = Path(results_dir)
    if ".." in dest.parts:
        raise OutputAuthorityError(
            f"'..' traversal is not permitted in a temporary destination: {dest}"
        )
    # Locate the destination relative to the authority (never above it), so only
    # components below the temporary root are scanned for symlinks.
    if dest.is_absolute():
        relative_parts: tuple[str, ...] | None = None
        scan_base: Path | None = None
        for candidate_base in (root, real_root):
            try:
                relative_parts = dest.relative_to(candidate_base).parts
            except ValueError:
                continue
            scan_base = candidate_base
            break
        if scan_base is None or relative_parts is None:
            raise OutputAuthorityError(
                f"absolute temporary destination {dest} is not beneath the "
                f"temporary-root authority {root}"
            )
        candidate = dest
    else:
        scan_base = root
        relative_parts = dest.parts
        candidate = root / dest
    if not relative_parts:
        raise OutputAuthorityError(
            "temporary destination must be strictly beneath the temporary root"
        )
    _reject_symlinked_components_below(
        scan_base, relative_parts, label="temporary destination"
    )
    # The component scan above has already refused a symlink at *any* existing
    # component, the governed final one included, so normalizing the parent chain
    # while keeping the final component as a name loses no safety — and it keeps the
    # destination identity stable if a symlink is substituted there afterwards.
    real_dest = _normalize_publication_path(candidate)
    # Post-resolution containment catches a symlink escape that slipped past the
    # component scan (e.g. a component created after the scan).
    if not _is_strictly_within(real_dest, real_root):
        raise OutputAuthorityError(
            f"temporary destination {real_dest} is not strictly within the "
            f"temporary-root authority {real_root}"
        )
    if real_dest == repo or _is_strictly_within(real_dest, repo):
        raise OutputAuthorityError(
            "temporary destination must not be inside the repository "
            "(backend/, frontend/, data/, experiments/results_excess/, or any other "
            "governed or unrelated repository path)"
        )
    return real_dest


def _write_file_anchored(dir_fd: int, name: str, text: str) -> None:
    """Create ``name`` under ``dir_fd`` (must not pre-exist), never following a link.

    ``O_CREAT | O_EXCL`` guarantees a fresh file in the private staging directory,
    and ``O_NOFOLLOW`` refuses a symlink planted at that name.
    """
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | _O_NOFOLLOW
    fd = os.open(name, flags, 0o644, dir_fd=dir_fd)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)


def _read_all_fd(fd: int) -> bytes:
    chunks: list[bytes] = []
    while True:
        block = os.read(fd, 1024 * 1024)
        if not block:
            break
        chunks.append(block)
    return b"".join(chunks)


def _validate_dir_contents(dir_fd: int, contents: dict[str, str], *, label: str) -> None:
    """Prove ``dir_fd`` holds exactly ``contents`` as regular files with matching bytes.

    Rejects a missing member, an unexpected extra member (the forbidden fourth
    file), a non-regular file, a symlinked member, and any checksum drift — read
    through the anchored descriptor, never by reopening a pathname.
    """
    present = set(os.listdir(dir_fd))
    expected = set(contents)
    if present != expected:
        raise OutputAuthorityError(
            f"{label}: published set {sorted(present)} does not equal the exact "
            f"governed set {sorted(expected)}"
        )
    for name, text in contents.items():
        try:
            fd = os.open(name, os.O_RDONLY | _O_NOFOLLOW, dir_fd=dir_fd)
        except OSError as exc:
            raise OutputAuthorityError(
                f"{label}: cannot open published member {name!r} without following a "
                f"symlink: {exc}"
            ) from exc
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                raise OutputAuthorityError(
                    f"{label}: published member {name!r} is not a regular file"
                )
            data = _read_all_fd(fd)
        finally:
            os.close(fd)
        if hashlib.sha256(data).hexdigest() != hashlib.sha256(text.encode("utf-8")).hexdigest():
            raise OutputAuthorityError(
                f"{label}: published member {name!r} checksum does not match the "
                "rendered content"
            )


def _lstat_kind(dir_fd: int, name: str) -> tuple[bool, bool]:
    """``(exists, is_genuine_directory)`` for ``name`` under ``dir_fd`` (no follow)."""
    try:
        info = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False, False
    return True, stat.S_ISDIR(info.st_mode)


def _rmtree_at(dir_fd: int, name: str) -> None:
    """Recursively remove ``name`` under ``dir_fd`` using descriptor-relative ops."""
    try:
        info = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    if not stat.S_ISDIR(info.st_mode):
        os.unlink(name, dir_fd=dir_fd)
        return
    try:
        sub_fd = _open_dir_component(name, dir_fd=dir_fd)
    except OSError:
        # A symlink that raced in: unlink the link itself, never its target.
        os.unlink(name, dir_fd=dir_fd)
        return
    try:
        for entry in os.listdir(sub_fd):
            _rmtree_at(sub_fd, entry)
    finally:
        os.close(sub_fd)
    os.rmdir(name, dir_fd=dir_fd)


def _fd_identity(fd: int) -> tuple[int, int]:
    """``(st_dev, st_ino)`` of an open descriptor — the identity of one inode."""
    info = os.fstat(fd)
    return info.st_dev, info.st_ino


@dataclass(frozen=True)
class _FinalDirectoryIdentity:
    """Bound identity of the *final* authorized output directory.

    The chain walk authorizes the components *above* the destination; this record
    authorizes the destination directory itself.  ``existed`` records whether the
    final directory was already present when the destination was authorized; when
    it was, ``dev``/``ino`` pin the exact inode that was authorized so a directory
    that later took over the same name is refused instead of published into.
    """

    existed: bool
    dev: int | None
    ino: int | None
    label: str


def _snapshot_final_directory(
    parent_fd: int, child: str, *, label: str
) -> _FinalDirectoryIdentity:
    """Bind the identity of the final output directory ``child`` under ``parent_fd``.

    An absent final directory is recorded as absent (the transactional publisher
    creates it).  An existing one must be a genuine, non-symlinked directory, and
    its ``(st_dev, st_ino)`` is captured through an ``O_NOFOLLOW`` descriptor and
    cross-checked against the lstat that selected it, so the binding itself cannot
    be raced onto a different inode.
    """
    try:
        info = os.stat(child, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return _FinalDirectoryIdentity(False, None, None, label)
    except OSError as exc:
        raise OutputAuthorityError(f"cannot inspect {label} {child!r}: {exc}") from exc
    if stat.S_ISLNK(info.st_mode):
        raise OutputAuthorityError(
            f"{label} {child!r} is a symlink; refusing to bind or publish through it"
        )
    if not stat.S_ISDIR(info.st_mode):
        raise OutputAuthorityError(
            f"{label} {child!r} exists but is not a genuine directory; refusing"
        )
    try:
        fd = _open_dir_component(child, dir_fd=parent_fd)
    except OSError as exc:
        raise OutputAuthorityError(
            f"cannot bind {label} {child!r} without following a symlink: {exc}"
        ) from exc
    try:
        identity = _fd_identity(fd)
    finally:
        os.close(fd)
    if identity != (info.st_dev, info.st_ino):
        raise OutputAuthorityError(
            f"{label} {child!r} changed identity while it was being bound; failing closed"
        )
    return _FinalDirectoryIdentity(True, identity[0], identity[1], label)


def _revalidate_final_directory(
    parent_fd: int, child: str, identity: _FinalDirectoryIdentity
) -> None:
    """Prove the current final path still identifies the authorized directory.

    Called from the retained authority root immediately before staging and again
    immediately before the publication swap.  Every way the authorized directory
    can stop being the authorized directory — replaced by another real directory,
    renamed away, deleted, replaced by a symlink, recreated with a different
    identity, or (when it was absent at authorization) an unexpected directory or
    symlink appearing before governed creation — fails closed here, so publication
    never continues through a replacement identity.
    """
    label = identity.label
    try:
        info = os.stat(child, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError as exc:
        if identity.existed:
            raise OutputAuthorityError(
                f"the authorized {label} {child!r} was deleted or renamed away after "
                "authorization; failing closed rather than recreating it or publishing "
                "through a replacement"
            ) from exc
        return
    except OSError as exc:
        raise OutputAuthorityError(
            f"cannot revalidate {label} {child!r}: {exc}"
        ) from exc
    if not identity.existed:
        kind = (
            "symlink"
            if stat.S_ISLNK(info.st_mode)
            else "directory"
            if stat.S_ISDIR(info.st_mode)
            else "entry"
        )
        raise OutputAuthorityError(
            f"the {label} {child!r} did not exist when the destination was authorized "
            f"but an unexpected {kind} exists now; failing closed rather than "
            "publishing through an unauthorized final directory"
        )
    if stat.S_ISLNK(info.st_mode):
        raise OutputAuthorityError(
            f"the authorized {label} {child!r} was replaced by a symlink after "
            "authorization; failing closed"
        )
    if not stat.S_ISDIR(info.st_mode):
        raise OutputAuthorityError(
            f"the authorized {label} {child!r} is no longer a genuine directory; "
            "failing closed"
        )
    try:
        fd = _open_dir_component(child, dir_fd=parent_fd)
    except OSError as exc:
        raise OutputAuthorityError(
            f"the authorized {label} {child!r} is no longer reachable without "
            f"following a symlink: {exc}; failing closed"
        ) from exc
    try:
        current = _fd_identity(fd)
    finally:
        os.close(fd)
    if current != (identity.dev, identity.ino):
        raise OutputAuthorityError(
            f"the authorized {label} {child!r} no longer identifies the authorized "
            "directory (device/inode mismatch — replaced by another real directory, "
            "renamed away and recreated, or otherwise swapped); publication must "
            "never continue through a replacement identity — failing closed"
        )


def _finalize_parent(
    parent_fd: int, child: str, *, label: str
) -> tuple[int, str, Callable[[], None]]:
    """Attach a final-directory identity guard to a freshly anchored parent.

    Used by the publication paths that establish their chain back-to-back with the
    write (canonical without a retained authority, a bounded temporary root, and a
    plain direct caller).  ``parent_fd`` is closed if the binding fails, so a
    refusal never leaks a descriptor.
    """
    try:
        identity = _snapshot_final_directory(parent_fd, child, label=label)
    except BaseException:
        os.close(parent_fd)
        raise
    return (
        parent_fd,
        child,
        functools.partial(_revalidate_final_directory, parent_fd, child, identity),
    )


@dataclass
class _ChainComponent:
    """One authorized path component between the authority root and the child.

    ``existed`` records whether the component was already present when the
    destination was authorized.  For a component that existed, ``dev``/``ino``
    pin the exact directory inode that was authorized and ``fd`` retains an open
    descriptor on it; publication walks *that* descriptor and never a directory
    that later took over the same name.  For a component that did not exist,
    publication creates it through the trusted parent descriptor and then adopts
    the freshly created inode.
    """

    name: str
    existed: bool
    dev: int | None = None
    ino: int | None = None
    fd: int | None = None


class PublicationAuthority:
    """Retained descriptor/device/inode chain authorizing exactly one destination.

    Authorization and publication are separated in time (the whole scenario sweep
    runs in between), so a pathname re-walk at publication time is not evidence
    that the chain is still the chain that was authorized: an intermediate
    directory can be renamed away and replaced by a *different genuine directory*,
    which a plain ``O_NOFOLLOW`` walk accepts because the replacement is not a
    symlink.  This authority therefore retains an open descriptor and the
    ``(st_dev, st_ino)`` identity of the root and of every component that existed
    at authorization time, and revalidates the complete chain immediately before
    publication:

    * the root pathname must still resolve to the authorized root inode (a
      rename-away or replacement of the root fails closed);
    * every authorized component must still be reachable under its own name from
      the retained parent descriptor, must not be a symlink or a non-directory,
      and must still have the authorized ``(st_dev, st_ino)``;
    * a component that was absent at authorization must still be absent, and is
      then created through the retained parent descriptor;
    * the *final* output directory itself is bound the same way: when it exists at
      authorization its ``(st_dev, st_ino)`` is pinned and revalidated from the
      retained authority root before staging and again before the publication
      swap, so a replacement by another real directory, a rename-away, a deletion,
      a symlink substitution, or a recreation with a different identity all fail
      closed; when it was absent at authorization, an unexpected directory or
      symlink appearing before governed creation fails closed too;
    * a deletion, rename-away, symlink replacement, real-directory replacement, or
      any other identity mismatch at any component fails closed *before* anything
      is written.

    Publication proceeds on the retained descriptors, so even a replacement that
    appeared between the identity check and the write is never followed.
    """

    def __init__(
        self,
        *,
        kind: str,
        root_path: Path,
        destination: Path,
        root_fd: int,
        root_identity: tuple[int, int],
        components: list[_ChainComponent],
        child: str,
        final_identity: _FinalDirectoryIdentity,
    ) -> None:
        self.kind = kind
        self.root_path = root_path
        self.destination = _normalize_publication_path(destination)
        self.child = child
        self._root_fd: int | None = root_fd
        self._root_identity = root_identity
        self._components = components
        self._final_identity = final_identity
        self._closed = False

    @property
    def final_identity(self) -> _FinalDirectoryIdentity:
        """The bound identity of the final authorized output directory."""
        return self._final_identity

    def assert_authorizes(self, directory: Path) -> None:
        """Fail closed unless this authority authorizes exactly ``directory``.

        An authority names one destination.  Publishing a different directory
        through it would publish into the authority's destination instead of the
        requested one, so a mismatch is refused rather than silently redirected.
        """
        requested = _normalize_publication_path(directory)
        if requested != self.destination:
            raise OutputAuthorityError(
                f"the supplied {self.kind} publication authority authorizes "
                f"{self.destination} but publication was requested for {requested}; "
                "a mismatched authority is refused — failing closed"
            )

    # -- lifetime ---------------------------------------------------------- #
    def close(self) -> None:
        """Release every retained descriptor (idempotent)."""
        if self._closed:
            return
        self._closed = True
        for component in self._components:
            if component.fd is not None:
                try:
                    os.close(component.fd)
                except OSError:
                    pass
                component.fd = None
        if self._root_fd is not None:
            try:
                os.close(self._root_fd)
            except OSError:
                pass
            self._root_fd = None

    def __enter__(self) -> "PublicationAuthority":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # -- revalidation ------------------------------------------------------ #
    def _revalidate_root(self) -> int:
        if self._closed or self._root_fd is None:
            raise OutputAuthorityError(
                "the retained publication authority was already released; "
                "re-authorize the destination before publishing"
            )
        try:
            info = os.stat(str(self.root_path), follow_symlinks=False)
        except FileNotFoundError as exc:
            raise OutputAuthorityError(
                f"{self.kind} authority root {self.root_path} no longer exists "
                "(deleted or renamed away after authorization); failing closed"
            ) from exc
        except OSError as exc:
            raise OutputAuthorityError(
                f"cannot revalidate {self.kind} authority root {self.root_path}: {exc}"
            ) from exc
        if stat.S_ISLNK(info.st_mode):
            raise OutputAuthorityError(
                f"{self.kind} authority root {self.root_path} is now a symlink; "
                "failing closed"
            )
        if not stat.S_ISDIR(info.st_mode):
            raise OutputAuthorityError(
                f"{self.kind} authority root {self.root_path} is no longer a "
                "genuine directory; failing closed"
            )
        if (info.st_dev, info.st_ino) != self._root_identity:
            raise OutputAuthorityError(
                f"{self.kind} authority root {self.root_path} no longer identifies "
                "the authorized directory (device/inode mismatch — renamed away and "
                "replaced); failing closed"
            )
        return self._root_fd

    def open_publication_parent(self) -> tuple[int, str, Callable[[], None]]:
        """Revalidate the whole chain and return ``(parent_fd, child, revalidate)``.

        The returned descriptor is a *duplicate* owned by the caller (the publisher
        closes it); the authority keeps its own retained descriptors until
        :meth:`close`.  The chain is revalidated from the retained authority root
        all the way down to — and including — the final authorized output
        directory, and the returned ``revalidate`` callable re-proves that final
        identity on the caller's own descriptor immediately before the publication
        swap, so the authorization-to-publication window cannot be used to slip a
        replacement directory under the governed name.
        """
        parent_fd = self._revalidate_root()
        for index, component in enumerate(self._components):
            if component.existed:
                parent_fd = self._revalidate_component(parent_fd, component, index)
            else:
                parent_fd = self._create_component(parent_fd, component, index)
        # The final authorized output directory is revalidated from the retained
        # chain before anything is staged.
        _revalidate_final_directory(parent_fd, self.child, self._final_identity)
        duplicate = os.dup(parent_fd)
        return (
            duplicate,
            self.child,
            functools.partial(
                _revalidate_final_directory,
                duplicate,
                self.child,
                self._final_identity,
            ),
        )

    def _describe(self, index: int) -> str:
        walked = "/".join(c.name for c in self._components[: index + 1])
        return f"{self.root_path}/{walked}"

    def _revalidate_component(
        self, parent_fd: int, component: _ChainComponent, index: int
    ) -> int:
        try:
            fresh_fd = _open_dir_component(component.name, dir_fd=parent_fd)
        except FileNotFoundError as exc:
            raise OutputAuthorityError(
                f"authorized path component {self._describe(index)} was deleted or "
                "renamed away after authorization; failing closed rather than "
                "recreating or following a replacement"
            ) from exc
        except OSError as exc:
            raise OutputAuthorityError(
                f"authorized path component {self._describe(index)} is no longer a "
                f"genuine directory reachable without following a symlink: {exc}; "
                "failing closed"
            ) from exc
        try:
            identity = _fd_identity(fresh_fd)
        finally:
            os.close(fresh_fd)
        if identity != (component.dev, component.ino):
            raise OutputAuthorityError(
                f"authorized path component {self._describe(index)} no longer "
                "identifies the authorized directory (device/inode mismatch — the "
                "component was replaced by a different genuine directory); "
                "publication must not follow the replacement — failing closed"
            )
        assert component.fd is not None  # retained for the authority's lifetime
        return component.fd

    def _create_component(
        self, parent_fd: int, component: _ChainComponent, index: int
    ) -> int:
        # A component that was absent at authorization must still be absent: an
        # entry that appeared in the meantime is foreign to this authority and is
        # refused instead of being adopted.
        try:
            os.stat(component.name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise OutputAuthorityError(
                f"cannot inspect unauthorized path component "
                f"{self._describe(index)}: {exc}"
            ) from exc
        else:
            raise OutputAuthorityError(
                f"path component {self._describe(index)} did not exist when the "
                "destination was authorized but exists now; failing closed rather "
                "than publishing through an unauthorized component"
            )
        try:
            os.mkdir(component.name, 0o755, dir_fd=parent_fd)
            fd = _open_dir_component(component.name, dir_fd=parent_fd)
        except OSError as exc:
            raise OutputAuthorityError(
                f"cannot create the authorized path component "
                f"{self._describe(index)} through its parent descriptor: {exc}"
            ) from exc
        identity = _fd_identity(fd)
        try:
            by_name = os.stat(component.name, dir_fd=parent_fd, follow_symlinks=False)
        except OSError as exc:
            os.close(fd)
            raise OutputAuthorityError(
                f"cannot confirm the freshly created component "
                f"{self._describe(index)}: {exc}"
            ) from exc
        if (by_name.st_dev, by_name.st_ino) != identity:
            os.close(fd)
            raise OutputAuthorityError(
                f"the freshly created component {self._describe(index)} was replaced "
                "before it could be adopted; failing closed"
            )
        component.existed = True
        component.dev, component.ino = identity
        component.fd = fd
        return fd


def _validate_temp_root_authority(temp_root: Path) -> Path:
    """Shared fail-closed validation of a bounded temporary-root authority."""
    root = Path(temp_root)
    if not root.is_absolute():
        raise OutputAuthorityError(f"temporary-root authority must be absolute: {root}")
    if ".." in root.parts:
        raise OutputAuthorityError(
            f"temporary-root authority must not contain '..': {root}"
        )
    if not root.exists():
        raise OutputAuthorityError(f"temporary-root authority does not exist: {root}")
    if root.is_symlink():
        raise OutputAuthorityError(
            f"temporary-root authority must not be a symlink: {root}"
        )
    real_root = root.resolve()
    if not real_root.is_dir():
        raise OutputAuthorityError(
            f"temporary-root authority is not a directory: {root}"
        )
    repo = ROOT.resolve()
    if real_root == repo or _is_strictly_within(real_root, repo):
        raise OutputAuthorityError(
            "temporary-root authority must be outside the repository"
        )
    return real_root


def _relative_parts_under(root: Path, real_root: Path, directory: Path) -> tuple[str, ...]:
    """Destination parts relative to the authority root, or fail closed."""
    for base in (root, real_root):
        try:
            return Path(directory).relative_to(base).parts
        except ValueError:
            continue
    raise OutputAuthorityError(
        f"temporary destination {directory} is not strictly beneath the "
        f"temporary-root authority {root}"
    )


def _authorize_chain(
    *, kind: str, root_path: Path, relative_parts: tuple[str, ...], destination: Path
) -> PublicationAuthority:
    """Walk ``root_path`` -> ``relative_parts`` and retain the authorized chain.

    Every component that already exists is opened with ``O_NOFOLLOW`` and its
    descriptor and ``(st_dev, st_ino)`` identity are retained.  Nothing is created
    here: a component that does not yet exist is recorded as absent (and so is
    everything below it, which cannot exist either) and is created — through the
    retained parent descriptor — only at publication time.

    The *final* output directory is bound the same way rather than being left to a
    pathname check at publication time: when it already exists its device/inode
    identity is pinned here, so a directory that later takes over that name is a
    different, unauthorized directory and fails closed.  When it does not exist it
    is recorded as absent, and any entry that appears under that name before the
    governed creation is refused.
    """
    if not relative_parts:
        raise OutputAuthorityError(
            f"{kind} destination must be strictly beneath its authority root"
        )
    root_path = Path(root_path)
    try:
        root_fd = _open_dir_path(root_path)
    except OSError as exc:
        raise OutputAuthorityError(
            f"cannot anchor the {kind} authority root {root_path}: {exc}"
        ) from exc
    components: list[_ChainComponent] = []
    authority: PublicationAuthority | None = None
    try:
        root_identity = _fd_identity(root_fd)
        parent_fd = root_fd
        missing = False
        for name in relative_parts[:-1]:
            if missing:
                components.append(_ChainComponent(name, False))
                continue
            try:
                fd = _open_dir_component(name, dir_fd=parent_fd)
            except FileNotFoundError:
                missing = True
                components.append(_ChainComponent(name, False))
                continue
            except OSError as exc:
                raise OutputAuthorityError(
                    f"{kind} path component {name!r} beneath {root_path} is not a "
                    f"genuine directory reachable without following a symlink: {exc}"
                ) from exc
            dev, ino = _fd_identity(fd)
            components.append(_ChainComponent(name, True, dev, ino, fd))
            parent_fd = fd
        child_name = relative_parts[-1]
        final_label = f"{kind} final output directory"
        if missing:
            # An absent ancestor means the final directory cannot exist either.
            final_identity = _FinalDirectoryIdentity(False, None, None, final_label)
        else:
            final_identity = _snapshot_final_directory(
                parent_fd, child_name, label=final_label
            )
        authority = PublicationAuthority(
            kind=kind,
            root_path=root_path,
            destination=Path(destination),
            root_fd=root_fd,
            root_identity=root_identity,
            components=components,
            child=child_name,
            final_identity=final_identity,
        )
        return authority
    finally:
        if authority is None:
            for component in components:
                if component.fd is not None:
                    try:
                        os.close(component.fd)
                    except OSError:
                        pass
            try:
                os.close(root_fd)
            except OSError:
                pass


def authorize_publication(
    results_dir: Path | None, temp_root: Path | None
) -> PublicationAuthority:
    """Authorize a destination and retain its descriptor/device/inode chain.

    This is the authority :func:`run` uses: the returned object both names the
    authorized destination and holds the retained chain that publication
    revalidates, so the window between authorization and publication cannot be
    used to swap a component for another directory.  Callers own the object and
    must :meth:`PublicationAuthority.close` it.
    """
    destination = resolve_output_authority(results_dir, temp_root, retain=False)
    if temp_root is None:
        repo_root = ROOT
        relative_parts = destination.relative_to(repo_root).parts
        return _authorize_chain(
            kind="canonical",
            root_path=repo_root,
            relative_parts=relative_parts,
            destination=destination,
        )
    root = Path(temp_root)
    real_root = _validate_temp_root_authority(root)
    relative_parts = _relative_parts_under(root, real_root, destination)
    return _authorize_chain(
        kind="temporary",
        root_path=root,
        relative_parts=relative_parts,
        destination=destination,
    )


# Bounded retention ledger.  ``resolve_output_authority`` retains the chain it
# authorized so that the legacy call pattern — authorize now, publish later while
# passing only the resolved path and the ``temp_root`` authority — is protected by
# the same revalidation as the explicit :func:`authorize_publication` object.  An
# authority is consumed (and closed) by the publication that uses it; an authority
# that is never used is released once ``_RETENTION_LIMIT`` newer destinations have
# been authorized.  Losing the retained authority does *not* downgrade the legacy
# flow to path-only validation: the claim ledger below turns every such case into a
# fail-closed refusal that demands re-authorization.
_RETENTION_LIMIT = 32
_RETAINED_AUTHORITIES: dict[tuple[str, str], PublicationAuthority] = {}

# Durable claims on destinations the *legacy* API has authorized in this process.
# A claim outlives its authority on purpose: once a destination has been authorized
# through :func:`resolve_output_authority`, publication into it requires the live
# retained authority, so a missing, released, evicted, consumed, stale, or
# mismatched authority fails closed instead of falling back to a pathname walk that
# cannot tell the authorized directory from a replacement.  Claims hold key strings
# only — never descriptors — so they cannot leak file handles, and canonical
# publication contributes exactly one claim.
_LEGACY_CLAIMS: set[tuple[str, str]] = set()


def _retain_authority(authority: PublicationAuthority, key: tuple[str, str]) -> None:
    previous = _RETAINED_AUTHORITIES.pop(key, None)
    if previous is not None:
        previous.close()
    _RETAINED_AUTHORITIES[key] = authority
    while len(_RETAINED_AUTHORITIES) > _RETENTION_LIMIT:
        _oldest, released = next(iter(_RETAINED_AUTHORITIES.items()))
        del _RETAINED_AUTHORITIES[_oldest]
        released.close()


def _take_retained_authority(
    destination: Path, temp_root: Path | None
) -> PublicationAuthority | None:
    return _RETAINED_AUTHORITIES.pop(_authority_key(destination, temp_root), None)


def _authority_key(destination: Path, temp_root: Path | None) -> tuple[str, str]:
    return (
        str(_normalize_publication_path(destination)),
        "" if temp_root is None else _normalize_authority_root(temp_root),
    )


def _record_legacy_claim(destination: Path, temp_root: Path | None) -> None:
    """Record that the legacy API authorized ``destination``."""
    _LEGACY_CLAIMS.add(_authority_key(destination, temp_root))


def _legacy_claim_refusal(directory: Path, temp_root: Path | None) -> str | None:
    """Why ``directory`` may not be published without its retained authority.

    Two distinct claims are honoured:

    * an **exact** claim on the destination (under any temporary-root authority):
      the legacy API authorized this destination, so its retained authority — not a
      pathname re-walk — is the only thing allowed to publish into it; and
    * an **alias** claim, where the requested directory is what a claimed
      destination currently *resolves to* while not being that destination.  That is
      the signature of a caller that resolved the governed path through a symlink
      substituted at the final component; the resolution target is refused rather
      than published into.
    """
    requested = _normalize_publication_path(directory)
    requested_key = str(requested)
    for claimed, claimed_root in _LEGACY_CLAIMS:
        if claimed == requested_key:
            return (
                f"{requested} was authorized through resolve_output_authority but its "
                "retained publication authority is missing, released, or already "
                "consumed; the legacy flow must not fall back to path-only validation "
                "(a pathname walk cannot distinguish the authorized directory from a "
                "replacement or a substituted symlink) — re-authorize the destination "
                "before publishing; failing closed"
            )
        if os.path.realpath(claimed) == os.path.realpath(requested_key):
            return (
                f"{requested} is only reachable by resolving the authorized "
                f"destination {claimed} through a substituted final component; "
                "publication must never continue into a resolution target — "
                f"re-authorize {claimed} (authority root {claimed_root or 'canonical'}) "
                "and publish through its retained authority; failing closed"
            )
    return None


def _open_publish_parent(
    directory: Path,
    *,
    temp_root: Path | None = None,
    authority: PublicationAuthority | None = None,
) -> tuple[int, str, Callable[[], None]]:
    """Anchor the parent of ``directory``; return ``(parent_fd, child, revalidate)``.

    An explicit ``authority`` (or one retained by a previous
    :func:`resolve_output_authority` call for the same destination) must authorize
    exactly this destination, and is then revalidated component by component
    against the retained descriptor/device/inode chain, so a symlink replacement, a
    *real-directory* replacement, a rename-away, a deletion, or any other identity
    mismatch fails closed and publication proceeds only on the originally
    authorized inodes.

    Without a live authority the flow never degrades to path-only validation for a
    destination the legacy API authorized: an exact or resolution-alias claim
    (:func:`_legacy_claim_refusal`) fails closed and demands re-authorization, and a
    ``temp_root`` publication — which only ever originates from an authorized
    destination — is refused outright.  What remains are the two windowless cases:
    canonical publication anchored beneath the *real* repository via
    :func:`_open_canonical_parent`, and a plain direct caller (e.g. a unit test
    writing into a pytest temp dir) anchoring the immediate parent with
    ``O_NOFOLLOW`` on its final component.  Both bind the final directory's
    identity at the moment they anchor it, back-to-back with the write.

    Every path returns a ``revalidate`` callable that re-proves the bound identity
    of the final output directory on the returned descriptor; the publisher calls
    it before staging and again immediately before the swap.
    """
    directory = _normalize_publication_path(directory)
    if authority is not None:
        authority.assert_authorizes(directory)
    else:
        authority = _take_retained_authority(directory, temp_root)
    if authority is not None:
        try:
            return authority.open_publication_parent()
        finally:
            authority.close()

    # No live authority: a claimed destination (or the target a claimed destination
    # now resolves to) must be re-authorized rather than re-derived from its path.
    refusal = _legacy_claim_refusal(directory, temp_root)
    if refusal is not None:
        raise OutputAuthorityError(refusal)

    if temp_root is not None:
        raise OutputAuthorityError(
            "a temporary-root publication requires the live retained authority that "
            f"authorized {directory}; re-authorize it through "
            "resolve_output_authority (or pass an explicit authorize_publication "
            "object) rather than revalidating the destination by pathname; "
            "failing closed"
        )

    if directory == _normalize_publication_path(CANONICAL_RESULTS_DIR):
        parent_fd, child = _open_canonical_parent(ROOT)
        return _finalize_parent(
            parent_fd, child, label="canonical final output directory"
        )

    parent = directory.parent
    if parent == directory:
        raise OutputAuthorityError(f"cannot publish at a filesystem root: {directory}")
    if not parent.exists():
        raise OutputAuthorityError(f"publication parent does not exist: {parent}")
    if parent.is_symlink():
        raise OutputAuthorityError(f"publication parent is a symlink: {parent}")
    try:
        parent_fd = _open_dir_path(parent)
    except OSError as exc:
        raise OutputAuthorityError(
            f"cannot anchor publication parent {parent}: {exc}"
        ) from exc
    return _finalize_parent(parent_fd, directory.name, label="final output directory")


def _sweep_stale_residue(parent_fd: int, child: str) -> None:
    """Best-effort removal of leftover ``.<child>.staging.*``/``.<child>.backup.*``.

    A prior invocation whose *post-commit* cleanup failed leaves a clearly named
    backup sibling behind on purpose (the complete new set is never rolled back
    for a cleanup failure).  A later invocation sweeps that residue away before it
    starts; sweeping only removes entries matching this task's own private staging
    and backup prefixes and never touches the governed child.
    """
    staging_prefix = f".{child}.staging."
    backup_prefix = f".{child}.backup."
    try:
        entries = os.listdir(parent_fd)
    except OSError:
        return
    for entry in entries:
        if entry.startswith(staging_prefix) or entry.startswith(backup_prefix):
            try:
                _rmtree_at(parent_fd, entry)
            except OSError:
                pass


def _atomic_write_governed(
    directory: Path,
    contents: dict[str, str],
    *,
    temp_root: Path | None = None,
    authority: PublicationAuthority | None = None,
) -> None:
    """Publish exactly the three governed artifacts as one transaction with commit.

    An explicit state machine with a durable logical commit point governs the
    swap so the visible set is always either the *complete* prior generation or
    the *complete* new generation — never a two-file or mixed-generation set::

        PREPARE -> STAGING_VALIDATED -> OLD_MOVED_TO_BACKUP -> NEW_INSTALLED
                -> NEW_VALIDATED -> COMMITTED -> CLEANUP

    Before ``COMMITTED`` any failure rolls back to the complete prior generation
    (the new directory is moved out of the way and the backup is renamed back onto
    the canonical name) and removes the staging residue; a backup that could not
    be restored is preserved intact rather than deleted, so the prior generation is
    never lost.  ``COMMITTED`` is reached only after the freshly installed new set
    has been re-validated in place.  *After* ``COMMITTED`` the new generation is
    authoritative and is never discarded: backup cleanup is best-effort and its
    failure leaves a clearly named sibling residue (swept by a later invocation)
    without rolling back or making the output incomplete.  Individual backup files
    are never deleted while rollback is still possible.
    """
    directory = _normalize_publication_path(directory)
    for name in contents:
        if name not in GOVERNED_OUTPUT_NAMES:
            raise OutputAuthorityError(
                f"refusing to write a non-governed output filename: {name!r}"
            )
    if set(contents) != set(GOVERNED_OUTPUT_NAMES):
        raise OutputAuthorityError(
            "publication requires exactly the three governed artifacts "
            f"{sorted(GOVERNED_OUTPUT_NAMES)}; got {sorted(contents)}"
        )

    parent_fd, child, revalidate_final = _open_publish_parent(
        directory, temp_root=temp_root, authority=authority
    )
    token = f"{os.getpid()}.{os.urandom(6).hex()}"
    staging = f".{child}.staging.{token}"
    backup = f".{child}.backup.{token}"
    try:
        # Before *anything* is staged, re-prove from the retained authority that
        # the current final path still identifies the authorized directory.
        revalidate_final()
        # A previous invocation's post-commit cleanup residue is swept first so a
        # stale backup sibling is not mistaken for anything and does not accumulate.
        _sweep_stale_residue(parent_fd, child)

        staging_present = False
        child_backed_up = False
        renamed_into_place = False
        committed = False
        try:
            # PREPARE + STAGING_VALIDATED: build and validate the complete new set
            # in a private staging sibling before anything visible is touched.
            os.mkdir(staging, 0o755, dir_fd=parent_fd)
            staging_present = True
            staging_fd = _open_dir_component(staging, dir_fd=parent_fd)
            try:
                for name, text in contents.items():
                    _write_file_anchored(staging_fd, name, text)
                _validate_dir_contents(staging_fd, contents, label="staging")
            finally:
                os.close(staging_fd)

            # Immediately before the visible swap, re-prove the final directory
            # identity once more: a replacement that appeared while the staging set
            # was being built must never be published through.
            revalidate_final()

            child_exists, child_is_dir = _lstat_kind(parent_fd, child)
            if child_exists and not child_is_dir:
                raise OutputAuthorityError(
                    f"refusing to replace a non-directory or symlinked prior output: {child}"
                )
            # OLD_MOVED_TO_BACKUP: the complete prior generation is moved aside
            # atomically; it is never partially disturbed while it is recoverable.
            if child_exists:
                os.rename(child, backup, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
                child_backed_up = True

            # NEW_INSTALLED: the complete new set takes the canonical name.
            os.rename(staging, child, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
            staging_present = False
            renamed_into_place = True

            # NEW_VALIDATED: re-validate the installed set through its own
            # descriptor before declaring the transaction committed.
            child_fd = _open_dir_component(child, dir_fd=parent_fd)
            try:
                _validate_dir_contents(child_fd, contents, label="published")
            finally:
                os.close(child_fd)

            # -------------------- COMMIT POINT --------------------
            committed = True
        except BaseException:
            # Pre-commit rollback only: restore the complete prior generation and
            # remove the staging residue. A backup that cannot be renamed back is
            # left intact (never individually deleted) so the prior set survives.
            if not committed:
                if renamed_into_place:
                    try:
                        os.rename(
                            child, staging, src_dir_fd=parent_fd, dst_dir_fd=parent_fd
                        )
                        renamed_into_place = False
                        staging_present = True
                    except OSError:
                        pass
                if child_backed_up:
                    try:
                        os.rename(
                            backup, child, src_dir_fd=parent_fd, dst_dir_fd=parent_fd
                        )
                        child_backed_up = False
                    except OSError:
                        pass
                if staging_present:
                    try:
                        _rmtree_at(parent_fd, staging)
                    except OSError:
                        pass
            raise

        # CLEANUP (post-commit): the complete new generation is authoritative and
        # is never rolled back. Removing the old backup is best-effort; a failure
        # leaves a clearly named residue for a later sweep and never touches the
        # committed new set.
        if child_backed_up:
            try:
                _rmtree_at(parent_fd, backup)
            except OSError:
                pass
    finally:
        os.close(parent_fd)


def write_outputs(
    report: dict[str, Any],
    results_dir: Path = RESULTS_DIR,
    *,
    temp_root: Path | None = None,
    authority: PublicationAuthority | None = None,
) -> dict[str, str]:
    """Render and safely write the three governed artifacts into ``results_dir``.

    ``results_dir`` is assumed to already be an *authorized* destination (the
    canonical namespace, or a temporary directory vetted by
    :func:`resolve_output_authority`).  Directory-level authority is intentionally
    not re-decided here so that isolated tests can render into their own vetted
    temporary directories, while the safety guards (governed basenames only,
    symlink refusal, no partial set) always apply.  A ``temp_root`` authority, when
    supplied, is forwarded to the publisher so the whole publication chain is
    re-anchored from it with ``O_NOFOLLOW`` — closing any post-authorization
    ancestor-symlink race.  A retained ``authority`` additionally pins the
    device/inode identity of every authorized component, so a component replaced
    by a different genuine directory fails closed instead of being followed.

    ``results_dir`` is canonicalized by :func:`_normalize_publication_path` — its
    parent chain is resolved but the governed final component is kept as a *name*.
    Fully resolving it here used to follow a symlink substituted at that name, which
    silently retargeted publication at the link's target *and* lost the retained
    authority (the resolved path no longer matched the authorized destination), so
    the legacy flow published the three artifacts into the replacement.  Keeping the
    name means the authorized destination still matches its retained authority and
    the bound device/inode contract decides.
    """
    results_dir = _normalize_publication_path(results_dir)
    if authority is None and temp_root is None:
        # Create the parent tree only; the transactional publisher creates (or
        # swaps) the governed directory itself, so a partial directory is never
        # left behind.  Under an authority the missing components are created
        # through the retained descriptors instead — creating them by pathname
        # here would install components the authority never authorized.
        results_dir.parent.mkdir(parents=True, exist_ok=True)

    all_rows = report.pop("_row_cache")
    report.pop("_markdown_placeholder", None)

    csv_text = render_csv(all_rows)
    markdown = render_markdown(report)
    json_text = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"

    _assert_no_forbidden_claims(json_text)

    # Basename-level confinement (a crafted name can never escape the directory).
    _assert_within(Path(CSV_OUTPUT.name), results_dir)
    _assert_within(Path(MARKDOWN_OUTPUT.name), results_dir)
    _assert_within(Path(JSON_OUTPUT.name), results_dir)

    _atomic_write_governed(
        results_dir,
        {
            CSV_OUTPUT.name: csv_text,
            MARKDOWN_OUTPUT.name: markdown,
            JSON_OUTPUT.name: json_text,
        },
        temp_root=temp_root,
        authority=authority,
    )

    return {
        "json": _sha256_text(json_text),
        "markdown": _sha256_text(markdown),
        "csv": _sha256_text(csv_text),
    }


def run(
    *, results_dir: Path | None = None, temp_root: Path | None = None
) -> dict[str, Any]:
    """Resolve the authorized destination, then compute and write the artifacts.

    Canonical execution passes no arguments and writes to
    :data:`CANONICAL_RESULTS_DIR`.  Isolated execution must supply both an
    explicit ``temp_root`` authority and a ``results_dir`` destination beneath it;
    :func:`authorize_publication` refuses anything else *before* any work.

    The authority is held open across the whole computation: publication then
    revalidates the retained descriptor/device/inode chain, so a component that was
    renamed away, deleted, or replaced (by a symlink *or* by another genuine
    directory) between authorization and publication fails closed.
    """
    authority = authorize_publication(results_dir, temp_root)
    try:
        target_dir = authority.destination
        comp = compute()
        report = build_report(comp)
        report["_row_cache"] = comp.all_rows
        checksums = write_outputs(
            report, results_dir=target_dir, temp_root=temp_root, authority=authority
        )
    finally:
        authority.close()
    report.pop("_row_cache", None)
    report.pop("_markdown_placeholder", None)
    return {
        "report": report,
        "checksums": checksums,
        "input_year": comp.input_year,
        "results_dir": target_dir,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=None,
        help=(
            "Optional isolated output directory for tests and deterministic "
            "verification. Defaults to the canonical experiments/results_missingness "
            "namespace. A non-canonical directory is accepted only together with an "
            "explicit --temp-root authority beneath which it must resolve."
        ),
    )
    parser.add_argument(
        "--temp-root",
        type=Path,
        default=None,
        help=(
            "Explicit bounded temporary-root authority. Required for any "
            "non-canonical --results-dir; the destination must resolve strictly "
            "beneath this existing directory, which must lie outside the repository."
        ),
    )
    args = parser.parse_args()
    result = run(results_dir=args.results_dir, temp_root=args.temp_root)
    counts = result["report"]["scenario_definitions"]["counts"]
    print(SENSITIVITY_LABEL)
    print(
        f"input_year={result['input_year']} scenarios={counts['total_scenarios']} "
        f"rows={result['report']['row_level_evidence']['row_count']}"
    )
    print(f"Wrote {result['results_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
