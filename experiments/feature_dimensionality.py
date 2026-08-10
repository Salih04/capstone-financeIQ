"""R4-DIM-01 deterministic descriptive feature-geometry analysis.

The module implements the approved packet literally.  It reads only the
internal training split and immutable feature authorities, seals eligibility
and yearly row intersections before scientific computation, and writes the
bounded five-file result family only after all payloads validate.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import platform
import shutil
import sys
import tempfile
import uuid
from collections import Counter
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
import scipy
from scipy.stats import rankdata


ROOT = Path(__file__).resolve().parents[1]
SOURCE_REL = "data/trusted_clean/modeling_dataset_training_2020_2025.csv"
FEATURE_AUTHORITY_REL = "data/trusted_clean/feature_engineering_report.json"
DATA_DICTIONARY_REL = "data/trusted_clean/data_dictionary.md"
OUTPUT_DIR_REL = "experiments/results_dimensionality"
OUTPUT_FILES = (
    "dimensionality_report.json",
    "dimensionality_report.md",
    "correlation_matrix.csv",
    "pair_overlap.csv",
    "feature_missingness.csv",
)

FEATURES = (
    "benchmark_same_year_return_pct",
    "current_assets",
    "current_ratio",
    "ebitda",
    "ebitda_growth_pct",
    "ebitda_margin",
    "enterprise_value",
    "equity",
    "ev_ebitda",
    "financial_debt_ratio",
    "gross_margin",
    "gross_profit",
    "gross_profit_growth_pct",
    "leverage_ratio",
    "long_term_liabilities",
    "market_cap",
    "net_debt",
    "net_debt_to_ebitda",
    "net_income",
    "net_income_growth_pct",
    "net_margin",
    "non_current_assets",
    "operating_income",
    "operating_income_growth_pct",
    "pb_ratio",
    "pe_ratio",
    "price_adjclose_t",
    "price_data_available",
    "price_drawdown_from_3y_high_pct",
    "price_history_years_available",
    "price_momentum_1y_pct",
    "price_momentum_2y_pct",
    "price_vs_bist100_1y_pct",
    "revenue",
    "revenue_growth_pct",
    "roa",
    "roe",
    "short_term_liabilities",
    "total_assets",
    "working_capital",
)

WINDOWS = (
    {
        "name": "test_2023",
        "feature_years": (2020, 2021),
        "train_target_years": (2021, 2022),
        "held_out_feature_year": 2022,
        "held_out_target_year": 2023,
    },
    {
        "name": "test_2024",
        "feature_years": (2020, 2021, 2022),
        "train_target_years": (2021, 2022, 2023),
        "held_out_feature_year": 2023,
        "held_out_target_year": 2024,
    },
    {
        "name": "test_2025",
        "feature_years": (2020, 2021, 2022, 2023),
        "train_target_years": (2021, 2022, 2023, 2024),
        "held_out_feature_year": 2024,
        "held_out_target_year": 2025,
    },
)
ALL_FEATURE_YEARS = tuple(sorted({year for window in WINDOWS for year in window["feature_years"]}))
THRESHOLDS = ("0.70", "0.80", "0.90")
CLAIM_SENTENCE = "No reliable predictive edge has been established."
VERSION = "R4-DIM-01-v2"

# These are constructionally fixed supported quantities in current-main
# pipeline code.  Missingness never creates a second ordering level.
STRUCTURALLY_FIXED_FEATURES = {
    "benchmark_same_year_return_pct": (
        "benchmark return is merged by year and is constant across supported tickers in a feature year"
    ),
    "price_data_available": (
        "price feature construction emits supported availability as the fixed numeric value 1.0"
    ),
}


class MethodologyError(ValueError):
    """Raised when a frozen input or method guard fails closed."""


@dataclass(frozen=True)
class RankResult:
    completed: np.ndarray
    observed_mask: np.ndarray
    n_obs: int


@dataclass(frozen=True)
class SpectrumResult:
    raw_eigenvalues: np.ndarray
    post_tolerance_eigenvalues: np.ndarray
    lambda_max: float
    zero_tolerance: float
    participation_ratio: float
    spectral_erank: float


@dataclass(frozen=True)
class EligibilityResult:
    primary_features: tuple[str, ...]
    structurally_ineligible: tuple[dict[str, Any], ...]
    support_excluded: tuple[dict[str, Any], ...]
    evidence: tuple[dict[str, Any], ...]
    support_sets: Mapping[str, Mapping[int, frozenset[tuple[str, int]]]]


def _fail(message: str) -> None:
    raise MethodologyError(message)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_float(value: float) -> float:
    value = float(value)
    if not math.isfinite(value):
        _fail(f"non-finite value cannot be serialized: {value!r}")
    return value


def _format_float(value: float) -> str:
    return format(_json_float(value), ".17g")


def _csv_bytes(header: Sequence[str], rows: Iterable[Sequence[Any]]) -> bytes:
    stream = StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _dictionary_features(text: str) -> list[str]:
    result: list[str] = []
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) >= 4 and cells[2] == "feature_allowed":
            result.append(cells[1].strip().strip("`"))
    return result


def validate_feature_authority(
    accepted_features: Sequence[str],
    dictionary_features: Sequence[str],
    source_columns: Sequence[str],
) -> None:
    """Require exact agreement of generated, dictionary, and source authority."""

    if len(accepted_features) != 40 or tuple(accepted_features) != FEATURES:
        _fail("PACKET_CONFLICT: generated accepted_features differ from canonical R4-DIM list")
    if tuple(dictionary_features) != FEATURES:
        _fail("PACKET_CONFLICT: data_dictionary feature_allowed order differs from canonical list")
    if len(source_columns) != len(set(source_columns)):
        _fail("source schema has duplicate column names")
    if source_columns.count("ticker") != 1 or source_columns.count("year") != 1:
        _fail("source schema must contain ticker and year exactly once")
    if source_columns.count("next_year_return_pct") != 1:
        _fail("source schema must contain next_year_return_pct exactly once")
    missing = [feature for feature in FEATURES if source_columns.count(feature) != 1]
    if missing:
        _fail(f"source schema does not contain each canonical feature exactly once: {missing}")
    if len(FEATURES) != 40:
        _fail("PACKET_CONFLICT: canonical feature count is not 40")


def _numeric_column(series: pd.Series, name: str) -> tuple[np.ndarray, np.ndarray]:
    missing = series.isna().to_numpy(dtype=bool)
    converted = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    malformed = ~missing & ~np.isfinite(converted)
    if malformed.any():
        _fail(f"malformed or non-finite numeric value in {name}")
    return converted, missing


def _assert_unique_analytical_keys(
    keys: Iterable[tuple[str, int]], *, scope: str
) -> dict[str, Any]:
    """Return explicit evidence for the frozen ``(ticker, year)`` invariant."""

    ordered_keys = [(str(ticker), int(year)) for ticker, year in keys]
    counts = Counter(ordered_keys)
    duplicates = sorted(key for key, count in counts.items() if count > 1)
    if duplicates:
        _fail(
            f"duplicate (ticker, year) keys in {scope}: "
            f"{duplicates[:5]}"
        )
    return {
        "analytical_key": ["ticker", "year"],
        "checked": True,
        "passed": True,
        "result": "PASS",
        "duplicate_key_count": 0,
        "row_count": len(ordered_keys),
        "unique_key_count": len(counts),
    }


def _read_source(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    source_path = root / SOURCE_REL
    if not source_path.is_file():
        _fail(f"required source split is absent: {SOURCE_REL}")
    try:
        frame = pd.read_csv(source_path, dtype=object, keep_default_na=True)
        authority = json.loads((root / FEATURE_AUTHORITY_REL).read_text(encoding="utf-8"))
        dictionary_text = (root / DATA_DICTIONARY_REL).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        _fail(f"R4-DIM authority cannot be read: {exc}")
    try:
        accepted = authority["accepted_features"]
    except (KeyError, TypeError) as exc:
        _fail(f"feature authority is malformed: {exc}")
    validate_feature_authority(accepted, _dictionary_features(dictionary_text), frame.columns.tolist())
    if frame[["ticker", "year"]].isna().any().any():
        _fail("ticker/year identifiers must not be missing")
    tickers = frame["ticker"].astype(str).str.strip()
    if (tickers == "").any():
        _fail("ticker identifiers must not be empty")
    years_raw, years_missing = _numeric_column(frame["year"], "year")
    if years_missing.any() or (years_raw != np.floor(years_raw)).any():
        _fail("year must contain finite integer values")
    years = years_raw.astype(int)
    _assert_unique_analytical_keys(
        zip(tickers.tolist(), years.tolist()), scope=SOURCE_REL
    )

    values: dict[str, np.ndarray] = {}
    masks: dict[str, np.ndarray] = {}
    for feature in FEATURES:
        values[feature], missing = _numeric_column(frame[feature], feature)
        masks[feature] = ~missing
    target, target_missing = _numeric_column(frame["next_year_return_pct"], "next_year_return_pct")
    numeric = pd.DataFrame(values)
    masks_frame = pd.DataFrame(masks)
    target_eligible = ~target_missing & np.isfinite(target)
    return frame, numeric, masks_frame, years, tickers.to_numpy(dtype=str), target_eligible


def validate_structural_semantics(
    numeric: pd.DataFrame,
    masks: pd.DataFrame,
    years: Sequence[int],
    target_eligible: Sequence[bool],
) -> None:
    """Validate only constructional constants used by structural exclusions."""

    years_array = np.asarray(years, dtype=int)
    eligible = np.asarray(target_eligible, dtype=bool)
    available = eligible & masks["price_data_available"].to_numpy(dtype=bool)
    if available.any() and not np.all(numeric.loc[available, "price_data_available"].to_numpy() == 1.0):
        _fail("PACKET_CONFLICT: price_data_available supported value is not constructionally fixed at 1.0")
    benchmark = numeric["benchmark_same_year_return_pct"].to_numpy(dtype=float)
    benchmark_mask = masks["benchmark_same_year_return_pct"].to_numpy(dtype=bool)
    for year in ALL_FEATURE_YEARS:
        supported = eligible & (years_array == year) & benchmark_mask
        values = benchmark[supported]
        if len(values) > 1 and not np.all(values == values[0]):
            _fail("PACKET_CONFLICT: benchmark_same_year_return_pct is not constant within feature year")


def _support_sets(
    numeric: pd.DataFrame,
    masks: pd.DataFrame,
    years: Sequence[int],
    tickers: Sequence[str],
    target_eligible: Sequence[bool],
) -> dict[str, dict[int, frozenset[tuple[str, int]]]]:
    years_array = np.asarray(years, dtype=int)
    eligible = np.asarray(target_eligible, dtype=bool)
    ticker_array = np.asarray(tickers, dtype=str)
    supports: dict[str, dict[int, frozenset[tuple[str, int]]]] = {}
    for feature in FEATURES:
        supports[feature] = {}
        observed = masks[feature].to_numpy(dtype=bool)
        for year in ALL_FEATURE_YEARS:
            members = {
                (ticker_array[index], int(year))
                for index in np.flatnonzero(eligible & (years_array == year) & observed)
            }
            supports[feature][year] = frozenset(sorted(members))
    return supports


def _member_json(members: Iterable[tuple[str, int]]) -> list[dict[str, Any]]:
    return [{"ticker": ticker, "year": int(year)} for ticker, year in sorted(members, key=lambda item: (item[1], item[0]))]


def build_eligibility(
    numeric: pd.DataFrame,
    masks: pd.DataFrame,
    years: Sequence[int],
    tickers: Sequence[str],
    target_eligible: Sequence[bool],
    *,
    structural_features: Mapping[str, str] | None = None,
) -> EligibilityResult:
    """Seal E, exclusion categories, support evidence, and support sets."""

    fixed = dict(STRUCTURALLY_FIXED_FEATURES if structural_features is None else structural_features)
    supports = _support_sets(numeric, masks, years, tickers, target_eligible)
    evidence: list[dict[str, Any]] = []
    structural: list[dict[str, Any]] = []
    support_excluded: list[dict[str, Any]] = []
    primary: list[str] = []

    for feature in FEATURES:
        order_by_year = {year: feature not in fixed for year in ALL_FEATURE_YEARS}
        window_evidence: list[dict[str, Any]] = []
        for window in WINDOWS:
            per_year = []
            for year in window["feature_years"]:
                support_count = len(supports[feature][year])
                order_capable = bool(order_by_year[year])
                per_year.append(
                    {
                        "year": year,
                        "order_capable": order_capable,
                        "support_count": support_count,
                        "support_members": _member_json(supports[feature][year]),
                        "window_year_eligible": order_capable and support_count >= 2,
                    }
                )
            window_ok = all(item["window_year_eligible"] for item in per_year)
            window_evidence.append(
                {
                    "window_id": window["name"],
                    "order_capable_feature_year_count": sum(item["order_capable"] for item in per_year),
                    "feature_year_count": len(per_year),
                    "total_support_cells": sum(item["support_count"] for item in per_year),
                    "per_year": per_year,
                    "window_order_capable": window_ok,
                }
            )
        all_order_capable = all(order_by_year.values())
        if not all_order_capable:
            structural.append(
                {
                    "feature": feature,
                    "rationale": fixed.get(feature, "constructionally lacks ticker-dependent numeric ordering"),
                    "blocking_feature_years": [year for year in ALL_FEATURE_YEARS if not order_by_year[year]],
                }
            )
        elif not all(item["window_order_capable"] for item in window_evidence):
            support_excluded.append(
                {
                    "feature": feature,
                    "rationale": "exact support rule failed for at least one feature year; no cohort-size judgment applied",
                    "blocking_windows": [
                        item["window_id"] for item in window_evidence if not item["window_order_capable"]
                    ],
                }
            )
        else:
            primary.append(feature)
        evidence.append({"feature": feature, "order_capable_by_year": order_by_year, "windows": window_evidence})

    if not primary:
        _fail("sealed PRIMARY eligible feature list is empty")
    categories = {item["feature"] for item in structural} | {item["feature"] for item in support_excluded}
    if set(primary) | categories != set(FEATURES) or set(primary) & categories:
        _fail("diagnostic features are not exhaustively and exclusively categorized")
    return EligibilityResult(tuple(primary), tuple(structural), tuple(support_excluded), tuple(evidence), supports)


def _row_universes(
    primary_features: Sequence[str],
    supports: Mapping[str, Mapping[int, frozenset[tuple[str, int]]]],
) -> dict[int, frozenset[tuple[str, int]]]:
    if not primary_features:
        _fail("cannot form PRIMARY row universe with empty feature set")
    result: dict[int, frozenset[tuple[str, int]]] = {}
    for year in ALL_FEATURE_YEARS:
        intersection = set(supports[primary_features[0]][year])
        for feature in primary_features[1:]:
            intersection.intersection_update(supports[feature][year])
        result[year] = frozenset(sorted(intersection))
    return result


def rank_feature_values(values: Sequence[float] | np.ndarray) -> RankResult:
    """Apply average/midrank normalization and exact neutral fill.

    The n_obs=0 and n_obs=1 branches never evaluate the normalized-rank
    formula.  No feature-year variance guard exists here by design.
    """

    array = np.asarray(values, dtype=float)
    if array.ndim != 1:
        _fail("rank input must be one-dimensional")
    observed = np.isfinite(array)
    n_obs = int(observed.sum())
    completed = np.full(array.shape, 0.5, dtype=float)
    if n_obs == 0:
        return RankResult(completed, observed, n_obs)
    if n_obs == 1:
        completed[observed] = 0.5
        return RankResult(completed, observed, n_obs)
    ranks = rankdata(array[observed], method="average")
    normalized = (ranks - 1.0) / (n_obs - 1.0)
    completed[observed] = normalized
    if not np.isfinite(completed).all():
        _fail("completed rank vector contains non-finite values")
    return RankResult(completed, observed, n_obs)


def build_completed_rank_matrix(
    numeric: pd.DataFrame,
    years: Sequence[int],
    feature_names: Sequence[str] = FEATURES,
) -> tuple[np.ndarray, pd.DataFrame, dict[str, dict[str, int]]]:
    """Rank every feature-year independently over the supplied row universe."""

    names = tuple(feature_names)
    if not names or len(names) != len(set(names)) or not set(names) <= set(FEATURES):
        _fail("rank feature order is not a canonical feature sub-order")
    absent = [feature for feature in names if feature not in numeric.columns]
    if absent:
        _fail(f"rank input is missing features: {absent}")
    if len(numeric) != len(years):
        _fail("year vector length does not match feature frame")
    years_array = np.asarray(years, dtype=int)
    completed = np.empty((len(numeric), len(names)), dtype=float)
    masks = pd.DataFrame(False, index=range(len(numeric)), columns=names)
    evidence: dict[str, dict[str, int]] = {}
    for year in sorted(set(years_array.tolist())):
        positions = np.flatnonzero(years_array == year)
        evidence[str(year)] = {}
        for feature_index, feature in enumerate(names):
            result = rank_feature_values(numeric.iloc[positions][feature].to_numpy(dtype=float))
            completed[positions, feature_index] = result.completed
            masks.iloc[positions, feature_index] = result.observed_mask
            evidence[str(year)][feature] = result.n_obs
    if not np.isfinite(completed).all():
        _fail("completed rank matrix contains non-finite values")
    return completed, masks, evidence


def pearson_correlation(
    completed: np.ndarray, feature_names: Sequence[str] | None = None
) -> np.ndarray:
    """Compute the sole completed-matrix Pearson correlation matrix."""

    matrix = np.asarray(completed, dtype=float)
    if matrix.ndim != 2 or matrix.shape[1] == 0:
        _fail(f"completed matrix must be a non-empty two-dimensional matrix, got {matrix.shape}")
    names = tuple(FEATURES if feature_names is None else feature_names)
    if len(names) != matrix.shape[1]:
        _fail(f"completed matrix feature count does not match names: {matrix.shape} vs {len(names)}")
    if matrix.shape[0] < 2 or not np.isfinite(matrix).all():
        _fail("completed matrix must have at least two finite rows")
    centered = matrix - matrix.mean(axis=0)
    sumsquares = np.sum(centered * centered, axis=0)
    if not np.isfinite(sumsquares).all() or np.any(sumsquares <= 0.0):
        _fail("invalid Pearson denominator in completed matrix")
    with np.errstate(divide="raise", invalid="raise"):
        correlation = (centered.T @ centered) / np.sqrt(np.outer(sumsquares, sumsquares))
    if correlation.shape != (len(names), len(names)) or not np.isfinite(correlation).all():
        _fail("Pearson correlation matrix is malformed or non-finite")
    correlation = (correlation + correlation.T) / 2.0
    np.fill_diagonal(correlation, 1.0)
    if not np.isfinite(correlation).all():
        _fail("final correlation matrix is non-finite")
    return correlation


def _pair_indices(size: int) -> Iterable[tuple[int, int]]:
    for row in range(size):
        for column in range(size):
            yield row, column


def overlap_matrix(observed_masks: np.ndarray) -> np.ndarray:
    masks = np.asarray(observed_masks, dtype=bool)
    if masks.ndim != 2 or masks.shape[1] != len(FEATURES):
        _fail(f"observed-mask matrix must have shape (n, {len(FEATURES)})")
    overlap = masks.astype(np.int64).T @ masks.astype(np.int64)
    if overlap.shape != (len(FEATURES), len(FEATURES)) or not np.array_equal(overlap, overlap.T):
        _fail("n_AB matrix must be symmetric 40x40")
    return overlap


def _connected_components(
    correlation: np.ndarray, threshold: float
) -> tuple[list[list[int]], list[tuple[int, int]]]:
    matrix = np.asarray(correlation, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or matrix.shape[0] == 0:
        _fail("graph correlation matrix must be square and non-empty")
    if not math.isfinite(threshold) or threshold < 0.0:
        _fail("threshold must be finite and non-negative")
    if not np.isfinite(matrix).all():
        _fail("graph correlation matrix must be finite")
    size = matrix.shape[0]
    edges = [
        (a, b)
        for a in range(size)
        for b in range(a + 1, size)
        if abs(float(matrix[a, b])) >= threshold
    ]
    adjacency = [[] for _ in range(size)]
    for a, b in edges:
        adjacency[a].append(b)
        adjacency[b].append(a)
    seen: set[int] = set()
    components: list[list[int]] = []
    for start in range(size):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        members: list[int] = []
        while stack:
            node = stack.pop()
            members.append(node)
            for neighbor in adjacency[node]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        components.append(sorted(members))
    components.sort(key=lambda members: tuple(members))
    return components, edges


def threshold_components(
    correlation: np.ndarray,
    threshold: float,
    feature_names: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    names = tuple(FEATURES if feature_names is None else feature_names)
    matrix = np.asarray(correlation, dtype=float)
    if matrix.ndim != 2 or matrix.shape != (len(names), len(names)):
        _fail("graph correlation shape does not match feature names")
    components, edges = _connected_components(matrix, threshold)
    edge_set = set(edges)
    output: list[dict[str, Any]] = []
    for members in components:
        pairs = [(a, b) for offset, a in enumerate(members) for b in members[offset + 1 :]]
        abs_values = [abs(float(matrix[a, b])) for a, b in pairs]
        output.append(
            {
                "members": [names[index] for index in members],
                "size": len(members),
                "edge_count": sum((a, b) in edge_set for a, b in pairs),
                "min_abs_corr": None if not abs_values else _json_float(min(abs_values)),
                "median_abs_corr": None if not abs_values else _json_float(float(np.median(abs_values))),
            }
        )
    return output


def _metrics_from_spectrum(values: np.ndarray, lambda_max: float, zero_tolerance: float) -> SpectrumResult:
    if not np.isfinite(values).all():
        _fail("spectrum contains non-finite eigenvalues")
    if not math.isfinite(lambda_max) or lambda_max <= 0.0:
        _fail("spectrum lambda_max must be finite and positive")
    if np.any(values < -zero_tolerance):
        _fail("spectrum contains a materially negative eigenvalue")
    post = np.where(np.abs(values) <= zero_tolerance, 0.0, values)
    if not np.isfinite(post).all() or np.any(post < 0.0):
        _fail("post-tolerance spectrum must be finite and nonnegative")
    total = float(np.sum(post))
    denominator = float(np.sum(post * post))
    if not math.isfinite(total) or total <= 0.0:
        _fail("post-tolerance spectrum sum must be finite and positive")
    if not math.isfinite(denominator) or denominator <= 0.0:
        _fail("participation-ratio denominator must be finite and positive")
    probabilities = post / total
    entropy = -sum(float(p) * math.log(float(p)) for p in probabilities if p > 0.0)
    participation_ratio = total * total / denominator
    spectral_erank = math.exp(entropy)
    if not math.isfinite(participation_ratio) or not math.isfinite(spectral_erank):
        _fail("effective-rank metrics must be finite")
    return SpectrumResult(
        values,
        post,
        lambda_max,
        zero_tolerance,
        participation_ratio,
        spectral_erank,
    )


def spectrum_metrics(correlation: np.ndarray) -> SpectrumResult:
    """Use symmetric eigvalsh and the frozen tolerance/metric policy."""

    matrix = np.asarray(correlation, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or matrix.shape[0] == 0:
        _fail("spectrum input must be a non-empty square matrix")
    if not np.isfinite(matrix).all():
        _fail("spectrum input must be finite")
    matrix = (matrix + matrix.T) / 2.0
    np.fill_diagonal(matrix, 1.0)
    raw = np.linalg.eigvalsh(matrix)
    if raw.shape != (matrix.shape[0],):
        _fail("spectrum has unexpected eigenvalue shape")
    lambda_max = float(np.max(raw))
    zero_tolerance = 1e-8 * lambda_max
    return _metrics_from_spectrum(raw, lambda_max, zero_tolerance)


def spectrum_metrics_from_eigenvalues(raw: Sequence[float]) -> SpectrumResult:
    """Testable spectrum-policy seam for synthetic eigenvalue fixtures."""

    values = np.asarray(raw, dtype=float)
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
        _fail("synthetic spectrum must be finite and one-dimensional; non-finite values are invalid")
    lambda_max = float(np.max(values))
    zero_tolerance = 1e-8 * lambda_max
    return _metrics_from_spectrum(values, lambda_max, zero_tolerance)


def _overlap_summary(overlap: np.ndarray) -> dict[str, Any]:
    values = [int(overlap[a, b]) for a in range(len(FEATURES)) for b in range(a + 1, len(FEATURES))]
    return {
        "off_diagonal_pair_count": len(values),
        "minimum": min(values),
        "maximum": max(values),
        "mean": _json_float(float(np.mean(values))),
        "median": _json_float(float(np.median(values))),
        "population_std": _json_float(float(np.std(values, ddof=0))),
    }


def _missingness_rows(window_name: str, masks: pd.DataFrame, total_rows: int) -> list[dict[str, Any]]:
    if total_rows <= 0:
        _fail("missingness diagnostics require a non-empty window row universe")
    rows: list[dict[str, Any]] = []
    for feature in FEATURES:
        count = int(masks[feature].sum())
        missing = total_rows - count
        rows.append(
            {
                "window": window_name,
                "feature": feature,
                "total_window_row_count": total_rows,
                "original_non_missing_count": count,
                "missing_count": missing,
                "missingness_rate": _json_float(missing / total_rows),
            }
        )
    return rows


def _source_artifacts(root: Path) -> list[dict[str, str]]:
    paths = (SOURCE_REL, FEATURE_AUTHORITY_REL, DATA_DICTIONARY_REL, "experiments/feature_dimensionality.py")
    records = []
    for relative in paths:
        path = root / relative
        if not path.is_file():
            _fail(f"direct source artifact is missing: {relative}")
        records.append({"path": relative, "sha256": sha256_file(path)})
    return records


def _window_json(window: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "window_id": window["name"],
        "feature_years": list(window["feature_years"]),
        "training_target_years": list(window["train_target_years"]),
        "held_out_feature_year": window["held_out_feature_year"],
        "held_out_target_year": window["held_out_target_year"],
    }


def validate_serialized_family(
    directory: Path,
    *,
    expected_outputs: Mapping[str, bytes] | None = None,
) -> None:
    """Validate the complete bounded family before canonical publication."""

    directory = directory.resolve()
    if not directory.is_dir() or directory.is_symlink():
        _fail(f"serialized family directory is not a real directory: {directory}")
    entries = list(directory.iterdir())
    if {entry.name for entry in entries} != set(OUTPUT_FILES) or any(
        not entry.is_file() for entry in entries
    ):
        _fail("serialized family must contain exactly the five R4-DIM artifacts")
    if expected_outputs is not None:
        if set(expected_outputs) != set(OUTPUT_FILES):
            _fail("expected serialized family is not exactly five artifacts")
        for name in OUTPUT_FILES:
            if (directory / name).read_bytes() != expected_outputs[name]:
                _fail(f"serialized artifact bytes differ from the in-memory payload: {name}")

    try:
        payload = json.loads(
            (directory / "dimensionality_report.json").read_text(encoding="utf-8")
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail(f"serialized JSON report is malformed: {exc}")
    if not isinstance(payload, dict):
        _fail("serialized JSON report must be an object")
    for key in (
        "analysis",
        "claim_safety",
        "companion_artifacts",
        "eligibility",
        "environment",
        "feature_authority",
        "limitations",
        "methodology_freeze",
        "methodology_status",
        "primary_row_universe",
        "schema_version",
        "source_artifacts",
        "task_id",
        "windows",
    ):
        if key not in payload:
            _fail(f"serialized JSON report is missing required field: {key}")
    if payload["task_id"] != "R4-DIM-01" or payload["methodology_status"] != "APPROVED_FROZEN":
        _fail("serialized JSON report has an invalid task or methodology status")
    if not isinstance(payload["limitations"], list) or not payload["limitations"] or not all(
        isinstance(item, str) and item.strip() for item in payload["limitations"]
    ):
        _fail("serialized JSON limitations must be a non-empty string list")

    source_artifacts = payload["source_artifacts"]
    if not isinstance(source_artifacts, list) or not source_artifacts:
        _fail("serialized JSON source_artifacts must be a non-empty list")
    for item in source_artifacts:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            _fail("serialized source_artifacts entries are malformed")
        source_path = Path(item["path"])
        if source_path.is_absolute() or "temp" in source_path.parts or OUTPUT_DIR_REL in item["path"]:
            _fail("serialized source_artifacts contains an absolute, temporary, or output path")

    primary = payload["eligibility"].get("primary_features")
    if not isinstance(primary, list) or not primary:
        _fail("serialized eligibility must contain a non-empty primary feature list")
    primary_dimension = payload["eligibility"].get("primary_dimension")
    if primary_dimension != len(primary) or payload["analysis"].get("primary_dimension") != len(primary):
        _fail("serialized PRIMARY dimension is inconsistent")
    windows = payload["windows"]
    expected_windows = [window["name"] for window in WINDOWS]
    if not isinstance(windows, list) or [window.get("window_id") for window in windows] != expected_windows:
        _fail("serialized windows are missing or out of order")
    for window in windows:
        row_universe = window.get("row_universe")
        if not isinstance(row_universe, dict):
            _fail("serialized window row_universe is missing")
        invariant = row_universe.get("row_universe_invariant")
        if invariant != {
            "analytical_key": ["ticker", "year"],
            "checked": True,
            "passed": True,
            "result": "PASS",
            "duplicate_key_count": 0,
            "row_count": len(row_universe.get("eligible_row_members", [])),
            "unique_key_count": len(row_universe.get("eligible_row_members", [])),
        }:
            _fail("serialized row-universe invariant assertion is missing or not an explicit PASS")
        members = row_universe.get("eligible_row_members")
        if not isinstance(members, list) or len({(item.get("ticker"), item.get("year")) for item in members}) != len(members):
            _fail("serialized eligible row members violate the analytical-key invariant")
        if row_universe.get("primary_rank_row_count") != len(row_universe.get("primary_rank_row_members", [])):
            _fail("serialized PRIMARY rank-row count is inconsistent")

    companion = payload["companion_artifacts"]
    expected_companion_paths = {
        f"{OUTPUT_DIR_REL}/correlation_matrix.csv",
        f"{OUTPUT_DIR_REL}/pair_overlap.csv",
        f"{OUTPUT_DIR_REL}/feature_missingness.csv",
    }
    if {item.get("path") for item in companion} != expected_companion_paths:
        _fail("companion artifact references are incomplete or stale")
    for item in companion:
        name = Path(item["path"]).name
        if item["sha256"] != sha256_file(directory / name):
            _fail(f"companion checksum mismatch: {name}")

    def read_csv(name: str, header: tuple[str, ...]) -> list[dict[str, str]]:
        data = (directory / name).read_bytes()
        if not data.endswith(b"\n"):
            _fail(f"CSV artifact lacks a final newline: {name}")
        try:
            reader = csv.DictReader(StringIO(data.decode("utf-8")))
            if tuple(reader.fieldnames or ()) != header:
                _fail(f"CSV header mismatch: {name}")
            return list(reader)
        except (UnicodeDecodeError, csv.Error) as exc:
            _fail(f"CSV artifact is malformed: {name}: {exc}")

    correlation_rows = read_csv(
        "correlation_matrix.csv", ("window", "feature_a", "feature_b", "correlation")
    )
    overlap_rows = read_csv("pair_overlap.csv", ("window", "feature_a", "feature_b", "n_ab"))
    missingness_rows = read_csv(
        "feature_missingness.csv",
        (
            "window",
            "feature",
            "total_window_row_count",
            "original_non_missing_count",
            "missing_count",
            "missingness_rate",
        ),
    )
    if len(correlation_rows) != 3 * len(primary) ** 2:
        _fail("correlation artifact does not have the required 3 x P x P rows")
    if len(overlap_rows) != 3 * len(FEATURES) ** 2 or len(missingness_rows) != 3 * len(FEATURES):
        _fail("diagnostic artifacts do not have the required full-40 row counts")
    expected_corr_order = [
        (window_name, feature_a, feature_b)
        for window_name in expected_windows
        for feature_a in primary
        for feature_b in primary
    ]
    actual_corr_order = [
        (row["window"], row["feature_a"], row["feature_b"]) for row in correlation_rows
    ]
    if actual_corr_order != expected_corr_order:
        _fail("correlation artifact ordering is not deterministic")
    expected_diag_order = [
        (window_name, feature_a, feature_b)
        for window_name in expected_windows
        for feature_a in FEATURES
        for feature_b in FEATURES
    ]
    actual_overlap_order = [
        (row["window"], row["feature_a"], row["feature_b"]) for row in overlap_rows
    ]
    if actual_overlap_order != expected_diag_order:
        _fail("pair-overlap artifact ordering is not deterministic")
    expected_missing_order = [
        (window_name, feature)
        for window_name in expected_windows
        for feature in FEATURES
    ]
    if [(row["window"], row["feature"]) for row in missingness_rows] != expected_missing_order:
        _fail("missingness artifact ordering is not deterministic")
    try:
        for row in overlap_rows:
            value = int(row["n_ab"])
            if value < 0:
                _fail("pair-overlap counts must be non-negative")
        for row in correlation_rows:
            if not math.isfinite(float(row["correlation"])):
                _fail("correlation artifact contains a non-finite value")
    except (TypeError, ValueError) as exc:
        _fail(f"serialized numeric artifact field is malformed: {exc}")
    markdown = (directory / "dimensionality_report.md").read_text(encoding="utf-8")
    if "Row-universe invariant: `PASS`" not in markdown:
        _fail("Markdown report is missing explicit row-universe invariant evidence")


def _eligibility_json(result: EligibilityResult) -> dict[str, Any]:
    return {
        "primary_features": list(result.primary_features),
        "primary_dimension": len(result.primary_features),
        "structurally_ineligible": list(result.structurally_ineligible),
        "support_excluded": list(result.support_excluded),
        "evidence": list(result.evidence),
    }


def _build_payload(root: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    _, numeric, masks, years, tickers, target_eligible = _read_source(root)
    validate_structural_semantics(numeric, masks, years, target_eligible)
    eligibility = build_eligibility(numeric, masks, years, tickers, target_eligible)
    primary_features = eligibility.primary_features
    primary_rows = _row_universes(primary_features, eligibility.support_sets)
    key_to_position = {(tickers[index], int(years[index])): index for index in range(len(years))}
    source_checksum = sha256_file(root / SOURCE_REL)

    row_universe_json = {
        str(year): {
            "count": len(primary_rows[year]),
            "members": _member_json(primary_rows[year]),
            "intersection_features": list(primary_features),
        }
        for year in ALL_FEATURE_YEARS
    }
    all_correlations: list[tuple[str, str, str, str]] = []
    all_overlaps: list[tuple[str, str, str, int]] = []
    all_missingness: list[dict[str, Any]] = []
    windows_payload: list[dict[str, Any]] = []

    for window in WINDOWS:
        feature_year_set = set(window["feature_years"])
        selected_keys = sorted(
            {
                (tickers[index], int(years[index]))
                for index in range(len(years))
                if target_eligible[index] and int(years[index]) in feature_year_set
            },
            key=lambda item: (item[1], item[0]),
        )
        if len(selected_keys) < 2:
            _fail(f"{window['name']} has fewer than two target-eligible rows")
        row_universe_invariant = _assert_unique_analytical_keys(
            selected_keys, scope=f"window {window['name']}"
        )
        selected_positions = [key_to_position[key] for key in selected_keys]
        rank_keys = sorted(
            {
                member
                for year in window["feature_years"]
                for member in primary_rows[year]
            },
            key=lambda item: (item[1], item[0]),
        )
        rank_positions = [key_to_position[key] for key in rank_keys]
        if len(rank_positions) < 2:
            _fail(f"{window['name']} PRIMARY I_y row universe has fewer than two rows")
        rank_numeric = numeric.iloc[rank_positions].reset_index(drop=True)
        rank_years = years[rank_positions]
        completed, _, rank_evidence = build_completed_rank_matrix(
            rank_numeric, rank_years, primary_features
        )
        correlation = pearson_correlation(completed, primary_features)
        overlap = overlap_matrix(masks.iloc[selected_positions].to_numpy(dtype=bool))
        missingness = _missingness_rows(window["name"], masks.iloc[selected_positions], len(selected_positions))
        all_missingness.extend(missingness)
        threshold_payload = []
        for threshold_text in THRESHOLDS:
            threshold_payload.append(
                {
                    "threshold": threshold_text,
                    "inclusive_rule": f"abs(correlation) >= {threshold_text}",
                    "components": threshold_components(correlation, float(threshold_text), primary_features),
                }
            )
        spectrum = spectrum_metrics(correlation)
        for a, b in _pair_indices(len(primary_features)):
            all_correlations.append(
                (
                    window["name"],
                    primary_features[a],
                    primary_features[b],
                    _format_float(correlation[a, b]),
                )
            )
        for a, b in _pair_indices(len(FEATURES)):
            all_overlaps.append((window["name"], FEATURES[a], FEATURES[b], int(overlap[a, b])))
        windows_payload.append(
            {
                **_window_json(window),
                "source_path": SOURCE_REL,
                "source_sha256": source_checksum,
                "total_window_row_count": len(selected_keys),
                "row_universe": {
                    "eligibility_rule": "next_year_return_pct originally non-missing and year in frozen feature_years",
                    "eligible_row_members": _member_json(selected_keys),
                    "primary_rank_row_members": _member_json(rank_keys),
                    "primary_rank_row_count": len(rank_keys),
                    "row_universe_invariant": row_universe_invariant,
                },
                "rank_completion": {"feature_year_n_obs": rank_evidence},
                "thresholds": threshold_payload,
                "spectrum": {
                    "raw_eigenvalues": [_json_float(value) for value in spectrum.raw_eigenvalues],
                    "post_tolerance_eigenvalues": [_json_float(value) for value in spectrum.post_tolerance_eigenvalues],
                    "lambda_max": _json_float(spectrum.lambda_max),
                    "zero_tolerance": _json_float(spectrum.zero_tolerance),
                    "participation_ratio_effective_dimensionality": _json_float(spectrum.participation_ratio),
                    "roy_vetterli_spectral_entropy_effective_rank": _json_float(spectrum.spectral_erank),
                },
                "pair_overlap_summary": _overlap_summary(overlap),
            }
        )

    correlation_bytes = _csv_bytes(
        ("window", "feature_a", "feature_b", "correlation"), all_correlations
    )
    overlap_bytes = _csv_bytes(
        ("window", "feature_a", "feature_b", "n_ab"), all_overlaps
    )
    missingness_bytes = _csv_bytes(
        (
            "window",
            "feature",
            "total_window_row_count",
            "original_non_missing_count",
            "missing_count",
            "missingness_rate",
        ),
        (
            (
                row["window"],
                row["feature"],
                row["total_window_row_count"],
                row["original_non_missing_count"],
                row["missing_count"],
                _format_float(row["missingness_rate"]),
            )
            for row in all_missingness
        ),
    )
    companion = (
        {"path": f"{OUTPUT_DIR_REL}/correlation_matrix.csv", "sha256": _sha256_bytes(correlation_bytes)},
        {"path": f"{OUTPUT_DIR_REL}/pair_overlap.csv", "sha256": _sha256_bytes(overlap_bytes)},
        {"path": f"{OUTPUT_DIR_REL}/feature_missingness.csv", "sha256": _sha256_bytes(missingness_bytes)},
    )
    limitations = [
        "Descriptive feature-geometry analysis only; no model, target, or serving input is changed.",
        "Exact neutral-rank fill is analysis-only and is not model imputation, including for the n_obs = 0 and n_obs = 1 branches.",
        "Under heterogeneous missingness, no direction is guaranteed for spectral or participation-ratio effects.",
        "Windows differ in row universes and missingness, so cross-window metrics are not temporal evolution.",
        "PRIMARY-matrix exclusion does not imply feature uselessness, lack of predictive value, modeling redundancy, lack of temporal information, lack of market-context information, or feature-selection benefit.",
        "Support-based exclusions may remove redundancy-contributing geometry; exclusion is a construction/support limitation, not a finding about the excluded feature.",
        "D_eff is not claimed to be an upper or lower bound of any quantity over a larger or different feature set.",
        "Retrospective cohort, limited historical windows, sparse or mixed-quality source coverage, and environment-qualified reproduction remain limitations.",
        "No reliable predictive edge, alpha, profitability, investment value, tradable strategy, feature-selection benefit, model improvement, causal diagnosis, production validity, or deployment validity is established.",
        "Research support only; not investment advice.",
    ]
    payload: dict[str, Any] = {
        "analysis": {
            "source_path": SOURCE_REL,
            "target_eligibility_rule": "next_year_return_pct originally non-missing; feature year belongs to the window's frozen feature_years",
            "diagnostic_feature_order": list(FEATURES),
            "primary_feature_order": list(primary_features),
            "primary_dimension": len(primary_features),
            "thresholds": list(THRESHOLDS),
            "correlation_method": "Pearson correlation on one completed normalized-rank matrix per window",
            "missing_fill": "analysis-only u = 0.5 for every originally missing or branch-neutral cell",
            "rank_normalization": "u = (rank_average - 1) / (n_obs - 1) when n_obs >= 2",
            "pre_fill_feature_year_variance_guard": "removed by owner amendment; no such guard exists",
        },
        "claim_safety": {
            "analysis_scope": "descriptive feature-geometry analysis only",
            "research_status": "research support only; not investment advice",
            "preserved_boundary_sentence": CLAIM_SENTENCE,
            "firewall_statements": [
                "PRIMARY-matrix exclusion does not imply feature uselessness, lack of predictive value, modeling redundancy, lack of temporal information, lack of market-context information, or feature-selection benefit.",
                "Support-based exclusion may remove geometry that could otherwise contribute redundancy structure.",
                "D_eff is not claimed to be an upper or lower bound over a larger or different feature set.",
                "Cross-window D_eff and erank differences are not evidence of temporal geometry change.",
            ],
            "denied_claims": [
                "predictive edge or alpha",
                "profitability or investment value",
                "tradable strategy validity",
                "feature-selection benefit",
                "performance or model improvement",
                "overfitting diagnosis",
                "causal explanation for weak model performance",
                "production or deployment validity",
            ],
        },
        "environment": {
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "generator_version": VERSION,
        },
        "feature_authority": {
            "accepted_feature_count": len(FEATURES),
            "ordered_features": list(FEATURES),
            "authority_paths": [FEATURE_AUTHORITY_REL, DATA_DICTIONARY_REL],
            "scope": "full 40-feature diagnostic universe; PRIMARY matrix uses sealed eligibility sub-order",
        },
        "methodology_freeze": {
            "status": "APPROVED_FROZEN",
            "owner_decision": "R4-DIM-01 methodology frozen before any result inspection",
            "basis": {
                "C1": "confirmed",
                "C2": "confirmed under stated conditions",
                "C3": "universal conservativeness claim refuted",
                "C4": "confirmed",
            },
            "amendment_rule": "result appearance never permits methodology changes; mechanical corrections preserve the final packet literally",
            "amendment_record": [
                "n_obs = 0 and n_obs = 1 rank-completion branches added; n_obs >= 2 average/midrank normalization retained",
                "mandatory pre-fill feature-year variance guard removed; post-completion Pearson well-definedness is sole numerical guard",
                "fixed PRIMARY 40-feature assumption replaced by deterministic construction/support eligibility and global intersection",
                "structurally_ineligible and support_excluded remain separate with support blocking windows",
                "(ticker, year) uniqueness and sealed per-year I_y are required before scientific computation",
                "full 40-feature diagnostic scope remains unconditional; matrix exclusion does not erase diagnostic evidence",
            ],
        },
        "methodology_status": "APPROVED_FROZEN",
        "schema_version": "1.0.0",
        "source_artifacts": _source_artifacts(root),
        "companion_artifacts": list(companion),
        "task_id": "R4-DIM-01",
        "eligibility": _eligibility_json(eligibility),
        "primary_row_universe": row_universe_json,
        "windows": windows_payload,
        "limitations": limitations,
    }
    markdown = render_markdown(payload)
    json_bytes = (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")
    outputs = {
        "dimensionality_report.json": json_bytes,
        "dimensionality_report.md": markdown.encode("utf-8"),
        "correlation_matrix.csv": correlation_bytes,
        "pair_overlap.csv": overlap_bytes,
        "feature_missingness.csv": missingness_bytes,
    }
    if set(outputs) != set(OUTPUT_FILES):
        _fail("R4-DIM output family is not exactly five files")
    return payload, outputs


def render_markdown(payload: Mapping[str, Any]) -> str:
    """Render Markdown from the already-built payload without source rereads."""

    analysis = payload["analysis"]
    authority = payload["feature_authority"]
    eligibility = payload["eligibility"]
    lines = [
        "# R4-DIM-01 — Feature redundancy & effective dimensionality",
        "",
        "## Research-only boundary",
        "",
        "Descriptive feature-geometry analysis only. Research support only; not investment advice.",
        "",
        CLAIM_SENTENCE,
        "",
        "This report does not establish predictive edge or alpha, profitability or investment value, tradable strategy validity, feature-selection benefit, model improvement, overfitting diagnosis, causal explanation, production validity, or deployment validity.",
        "",
        "## Source and frozen methodology",
        "",
        f"- Task: `{payload['task_id']}`",
        f"- Methodology status: `{payload['methodology_status']}`",
        f"- Source: `{analysis['source_path']}`",
        f"- Target eligibility: {analysis['target_eligibility_rule']}",
        f"- Rank normalization: `{analysis['rank_normalization']}`",
        f"- Missing fill: `{analysis['missing_fill']}`",
        f"- Guard: {analysis['pre_fill_feature_year_variance_guard']}",
        "",
        "### Amendment record",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["methodology_freeze"]["amendment_record"])
    lines.extend(["", "## Exact 40-feature diagnostic order", ""])
    lines.extend(f"{index}. `{feature}`" for index, feature in enumerate(authority["ordered_features"], 1))
    lines.extend(["", "## PRIMARY eligibility and sealed row universe", ""])
    lines.append(f"PRIMARY dimension P = `{eligibility['primary_dimension']}`.")
    lines.append("")
    lines.append("PRIMARY features: " + ", ".join(f"`{name}`" for name in eligibility["primary_features"]) + ".")
    lines.extend(["", "### structurally_ineligible", ""])
    for item in eligibility["structurally_ineligible"]:
        lines.append(f"- `{item['feature']}` — {item['rationale']}; blocking feature years: {item['blocking_feature_years']}.")
    lines.extend(["", "### support_excluded", ""])
    for item in eligibility["support_excluded"]:
        lines.append(f"- `{item['feature']}` — {item['rationale']}; blocking windows: {', '.join(item['blocking_windows'])}.")
    lines.extend(["", "### Eligibility evidence", ""])
    for item in eligibility["evidence"]:
        lines.append(f"#### `{item['feature']}`")
        for window in item["windows"]:
            lines.append(
                f"- `{window['window_id']}`: ORDER_CAPABLE years={window['order_capable_feature_year_count']}/{window['feature_year_count']}; total support cells={window['total_support_cells']}; WINDOW_ORDER_CAPABLE={window['window_order_capable']}."
            )
            for year in window["per_year"]:
                lines.append(
                    f"  - {year['year']}: order_capable={year['order_capable']}; support={year['support_count']}; WINDOW_YEAR_ELIGIBLE={year['window_year_eligible']}."
                )
    lines.extend(["", "### Sealed per-year I_y membership", ""])
    for year, record in payload["primary_row_universe"].items():
        members = ", ".join(f"{item['ticker']}:{item['year']}" for item in record["members"])
        lines.append(f"- `{year}`: count={record['count']}; members={members}.")

    lines.extend(["", "## Independent windows", ""])
    for window in payload["windows"]:
        lines.extend(
            [
                f"### `{window['window_id']}`",
                "",
                f"Feature years: {', '.join(map(str, window['feature_years']))}; training target years: {', '.join(map(str, window['training_target_years']))}; held-out feature year: {window['held_out_feature_year']}; held-out target year: {window['held_out_target_year']}.",
                f"Target-eligible rows: **{window['total_window_row_count']}**; PRIMARY rank rows: **{window['row_universe']['primary_rank_row_count']}**.",
                f"Row members are sealed by unique `(ticker, year)` identity: {json.dumps(window['row_universe']['eligible_row_members'], sort_keys=True)}.",
                f"Row-universe invariant: `{window['row_universe']['row_universe_invariant']['result']}`; analytical key=`(ticker, year)`; duplicate keys={window['row_universe']['row_universe_invariant']['duplicate_key_count']}.",
                "",
                "#### Missingness diagnostics",
                "",
                "See `feature_missingness.csv` for unconditional full-40 pre-imputation counts and rates.",
                "",
                "#### Pair-overlap evidence",
                "",
                "See `pair_overlap.csv` for complete full-40 pre-imputation n_AB evidence.",
                "",
                "Overlap summary: " + json.dumps(window["pair_overlap_summary"], sort_keys=True) + ".",
                "",
                "#### Redundancy thresholds",
                "",
            ]
        )
        for threshold in window["thresholds"]:
            lines.extend([f"##### Inclusive threshold `{threshold['threshold']}`", "", f"Rule: `{threshold['inclusive_rule']}`.", ""])
            for number, component in enumerate(threshold["components"], 1):
                if component["size"] == 1:
                    stats = "singleton pair statistics=null"
                else:
                    stats = f"min_abs_corr={component['min_abs_corr']}, median_abs_corr={component['median_abs_corr']}"
                lines.append(
                    f"{number}. `{', '.join(component['members'])}` — size={component['size']}, edge_count={component['edge_count']}, {stats}."
                )
            lines.append("")
        spectrum = window["spectrum"]
        lines.extend(
            [
                "#### Spectrum and effective ranks",
                "",
                f"Raw eigenvalues: `{json.dumps(spectrum['raw_eigenvalues'], separators=(',', ':'))}`.",
                f"Post-tolerance eigenvalues: `{json.dumps(spectrum['post_tolerance_eigenvalues'], separators=(',', ':'))}`.",
                f"lambda_max={spectrum['lambda_max']}; zero_tolerance={spectrum['zero_tolerance']}.",
                f"Participation-ratio effective dimensionality D_eff={spectrum['participation_ratio_effective_dimensionality']}.",
                f"Roy–Vetterli spectral-entropy effective rank erank={spectrum['roy_vetterli_spectral_entropy_effective_rank']}.",
                "",
            ]
        )

    lines.extend(["## Limitations and non-claims", ""])
    lines.extend(f"- {limitation}" for limitation in payload["limitations"])
    lines.extend(["", "### Interpretation firewall", ""])
    lines.extend(f"- {statement}" for statement in payload["claim_safety"]["firewall_statements"])
    lines.extend(["", "## Reproducibility and source checksums", ""])
    lines.append("Byte identity is claimed only for consecutive runs in a matching Python/platform/numerical-package environment.")
    lines.append("")
    for artifact in payload["source_artifacts"]:
        lines.append(f"- `{artifact['path']}` — `{artifact['sha256']}`")
    lines.append("")
    for artifact in payload["companion_artifacts"]:
        lines.append(f"- `{artifact['path']}` — `{artifact['sha256']}`")
    lines.append("")
    return "\n".join(lines)


def generate(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, bytes]]:
    return _build_payload(root.resolve())


def _write_bytes(path: Path, data: bytes) -> None:
    path.write_bytes(data)


def _remove_private_directory(path: Path) -> None:
    if path.exists() or path.is_symlink():
        if path.is_symlink() or not path.is_dir():
            path.unlink()
        else:
            shutil.rmtree(path)


def _publish_family(
    output_dir: Path,
    outputs: Mapping[str, bytes],
    *,
    write_file: Callable[[Path, bytes], None] = _write_bytes,
) -> list[Path]:
    """Stage, validate, and atomically publish the complete five-file family."""

    # Resolve the parent chain, but keep the governed final component visible so
    # symlink substitution at the canonical name is rejected rather than followed.
    output_dir = output_dir.parent.resolve() / output_dir.name
    parent = output_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    if output_dir.is_symlink() or (output_dir.exists() and not output_dir.is_dir()):
        _fail(f"refusing to publish through a non-directory output path: {output_dir}")
    if set(outputs) != set(OUTPUT_FILES):
        _fail("R4-DIM publication requires exactly five artifacts")
    if output_dir.exists():
        existing_entries = list(output_dir.iterdir())
        existing_names = {entry.name for entry in existing_entries}
        if existing_names and existing_names != set(OUTPUT_FILES):
            _fail("refusing to replace a DIM directory containing an unexpected artifact")

    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=parent))
    backup: Path | None = None
    old_moved = False
    new_installed = False
    committed = False
    try:
        for name in OUTPUT_FILES:
            write_file(staging / name, outputs[name])
        validate_serialized_family(staging, expected_outputs=outputs)

        if output_dir.exists():
            backup = parent / f".{output_dir.name}.backup-{os.getpid()}-{uuid.uuid4().hex}"
            output_dir.rename(backup)
            old_moved = True
        os.replace(staging, output_dir)
        new_installed = True
        validate_serialized_family(output_dir, expected_outputs=outputs)
        committed = True
        return [output_dir / name for name in OUTPUT_FILES]
    except BaseException:
        if new_installed and (output_dir.exists() or output_dir.is_symlink()):
            _remove_private_directory(output_dir)
        if old_moved and backup is not None and backup.exists():
            os.replace(backup, output_dir)
        raise
    finally:
        if staging.exists() or staging.is_symlink():
            _remove_private_directory(staging)
        if committed and backup is not None and (backup.exists() or backup.is_symlink()):
            _remove_private_directory(backup)


def write_outputs(
    root: Path = ROOT,
    *,
    write_file: Callable[[Path, bytes], None] = _write_bytes,
) -> list[Path]:
    """Build and publish the complete family without exposing partial output."""

    root = root.resolve()
    _, outputs = generate(root)
    return _publish_family(root / OUTPUT_DIR_REL, outputs, write_file=write_file)


def main() -> int:
    try:
        for path in write_outputs():
            print(path.relative_to(ROOT).as_posix())
    except MethodologyError as exc:
        print(f"R4-DIM-01 failed closed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
