"""Deterministic ranking & cohort stability diagnostics from persisted dumps.

R3-STAT-01 consumes only the committed walk-forward prediction artifacts.  It
never retrains a model, alters a production ranking, or compares raw prediction
values across models: their scales are model-local.  It answers three separate
questions and keeps their quantities strictly distinct — it does not collapse
them into a single confidence score:

  (a) Rank-position variability & top-k membership stability.  Per model and
      year, tickers are bootstrapped within that year (with replacement, seeded,
      B >= 2000).  For each ticker we report its top-10 membership frequency
      conditional on being drawn and the 2.5-97.5 percentile interval of its
      within-sample rank.

  (b) Model-performance uncertainty.  Per model, a leave-k-out jackknife of the
      pooled within-year Spearman IC (k=1 exact over every observation; k=8
      sampled, seeded) yields the dispersion of the pooled IC.

  (c) Cohort-composition sensitivity.  Per model, the pooled IC recomputed on
      the public-40 subset of the dump rows, with per-year n reported.  This is
      a sensitivity description, never a "which cohort is better" selection.

The pooled IC reuses ``experiments.significance.spearman_ic`` verbatim, so these
numbers cannot silently diverge from the canonical significance report.  Every
quantity here is resampling variability of a ranking already indistinguishable
from the within-year null; a frequently-top-ranked ticker is not a validated
pick.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from experiments.significance import ML_MODELS, spearman_ic


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "experiments" / "results"
OUTPUT_DIR = ROOT / "experiments" / "results_rank_stability"
PUBLIC_40_CONFIG = ROOT / "data" / "config" / "universe_public_40.csv"
PREDICTION_YEARS = (2023, 2024, 2025)
PREDICTION_PATHS = tuple(
    RESULTS_DIR / f"predictions_test_{year}.csv" for year in PREDICTION_YEARS
)
JSON_OUTPUT = OUTPUT_DIR / "rank_stability_report.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "rank_stability_report.md"
TICKER_OUTPUT = OUTPUT_DIR / "stability_by_ticker.csv"
REQUIRED_COLUMNS = ["ticker", "year", "model", "y_true", "y_pred"]

MIN_ROWS_FOR_IC = 3
MIN_COHORT_N = 30
TOP_K = 10
DEFAULT_SEED = 42
DEFAULT_BOOTSTRAP_DRAWS = 2000
DEFAULT_JACKKNIFE_K8_SAMPLES = 2000
JACKKNIFE_K = 8
ROUND_DIGITS = 10

CLAIM_SAFETY_SENTENCE = (
    "**Stability frequencies describe resampling variability of a ranking already "
    "indistinguishable from the null; a frequently-top-ranked ticker is not a "
    "validated pick.**"
)
MECHANICAL_TOP_K_DISCLOSURE = (
    "Top-k membership frequency is a mechanical consequence of frozen predictions. "
    "A ticker with full-cohort rank <= k gets frequency 1.0 by construction. "
    "Frequencies are near-deterministic transforms of fixed full-cohort rank and n, "
    "not evidence of model/data-driven stability."
)
BASELINE_EQUAL_WEIGHT_IC_QUALIFIER = (
    "reported as descriptive baseline context outside the six-model ML correction "
    "family, not as a validated edge"
)
DELETION_RANGE_DISCLAIMER = (
    "These deletion ranges are not confidence intervals for the IC and should not be "
    "interpreted as uncertainty intervals for predictive performance."
)


def _sha256(path: Path) -> str:
    """Return the SHA-256 checksum of one source artifact."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rounded(value: float | int | None, digits: int = ROUND_DIGITS) -> float | None:
    """Round finite numbers deterministically; non-finite/None become null."""
    if value is None:
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return round(number, digits)


def _rng(base_seed: int, *offsets: int) -> np.random.Generator:
    """Deterministic generator keyed by a base seed and stable positional offsets.

    Offsets come from sorted-iteration positions (model index, year index), never
    from string hashing, so the RNG stream is identical run to run regardless of
    dict ordering or PYTHONHASHSEED.
    """
    seed = base_seed
    for weight, offset in zip((1_000_000, 1_000, 1), offsets[-3:]):
        seed += weight * int(offset)
    return np.random.default_rng(seed)


def validate_claim_safety_text(text: str) -> None:
    """Reject language that would turn a stability diagnostic into a value claim."""
    unsafe_patterns = {
        "frequency_is_confidence": r"\b(?:membership\s+)?frequenc\w*\s+(?:is|are|means?|implies)\s+(?:pick[- ]?)?confidence\b",
        "frequent_top_is_validated": r"\bfrequently[- ]?top[- ]?ranked\s+\w+\s+(?:is|are)\s+(?:a\s+)?(?:validated|reliable)\s+pick\b",
        "stability_is_signal": r"\b(?:stability|stable\s+ranking)\s+(?:is|was|proves|establishes)\s+(?:a\s+)?(?:signal|edge|alpha|predictive)\b",
        "recommendation": r"\b(?:buy|sell|hold)\s+recommendation\b",
        "market_beating": r"\b(?:market[- ]beating|outperform(?:s|ed)\s+the\s+market)\b",
        "profitable_trading": r"\bprofitable\s+trading\b",
        "validated_pick": r"\bvalidated\s+(?:pick|stock|ticker)s?\s+(?:identified|found|selected)\b",
        "better_cohort": r"\bpublic[- ]?40\s+cohort\s+(?:is|performs)\s+better\b",
    }
    violations = [
        name
        for name, pattern in unsafe_patterns.items()
        if re.search(pattern, text, flags=re.IGNORECASE)
    ]
    if violations:
        raise ValueError(f"Unsafe stability claim(s): {', '.join(violations)}")


def load_prediction_dumps(
    paths: Iterable[Path] = PREDICTION_PATHS,
) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    """Load exact persisted dump schemas without filling missing predictions."""
    frames: list[pd.DataFrame] = []
    sources: list[dict[str, object]] = []
    for expected_year, source in zip(PREDICTION_YEARS, paths, strict=True):
        source = Path(source)
        if not source.is_file():
            raise FileNotFoundError(
                f"Persisted prediction dump missing: {source}; run 'make research' first"
            )
        frame = pd.read_csv(source)
        if list(frame.columns) != REQUIRED_COLUMNS:
            raise ValueError(
                f"{source.name} columns must be exactly {REQUIRED_COLUMNS}; got {list(frame.columns)}"
            )
        if frame.empty:
            raise ValueError(f"{source.name} contains no prediction rows")
        frame = frame.copy()
        frame["ticker"] = frame["ticker"].fillna("").astype(str).str.strip().str.upper()
        frame["model"] = frame["model"].fillna("").astype(str).str.strip()
        if frame["ticker"].eq("").any() or frame["model"].eq("").any():
            raise ValueError(f"{source.name} has blank ticker or model identifiers")
        frame["year"] = pd.to_numeric(frame["year"], errors="raise").astype(int)
        years = sorted(frame["year"].unique().tolist())
        if years != [expected_year]:
            raise ValueError(
                f"{source.name} must contain only target year {expected_year}; got {years}"
            )
        if frame.duplicated(["ticker", "year", "model"]).any():
            raise ValueError(f"{source.name} contains duplicate ticker/year/model rows")
        frame["y_true"] = pd.to_numeric(frame["y_true"], errors="coerce")
        frame["y_pred"] = pd.to_numeric(frame["y_pred"], errors="coerce")
        frame.loc[~np.isfinite(frame["y_true"]), "y_true"] = np.nan
        frame.loc[~np.isfinite(frame["y_pred"]), "y_pred"] = np.nan
        frame["source_file"] = (
            source.relative_to(ROOT).as_posix()
            if source.is_relative_to(ROOT)
            else str(source)
        )
        frames.append(frame)
        sources.append(
            {
                "path": frame["source_file"].iloc[0],
                "sha256": _sha256(source),
                "rows": int(len(frame)),
                "year": expected_year,
                "models": sorted(frame["model"].unique().tolist()),
            }
        )
    return (
        pd.concat(frames, ignore_index=True)
        .sort_values(["model", "year", "ticker"], kind="mergesort")
        .reset_index(drop=True),
        sources,
    )


def load_public_40(path: Path = PUBLIC_40_CONFIG) -> tuple[set[str], dict[str, object]]:
    """Load the public-40 cohort tickers and a checksummed provenance record."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"public-40 universe config missing: {path}")
    frame = pd.read_csv(path)
    if "ticker" not in frame.columns:
        raise ValueError(f"{path.name} must contain a 'ticker' column")
    tickers = {
        str(value).strip().upper()
        for value in frame["ticker"].tolist()
        if str(value).strip()
    }
    source = {
        "path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
        "sha256": _sha256(path),
        "rows": int(len(frame)),
        "ticker_count": len(tickers),
    }
    return tickers, source


def _year_ic(usable: pd.DataFrame) -> float | None:
    """Within-year Spearman IC over usable rows, or null when undefined.

    Reuses ``experiments.significance.spearman_ic`` verbatim so the pooled value
    cannot diverge from the canonical significance report.
    """
    if len(usable) < MIN_ROWS_FOR_IC:
        return None
    value = spearman_ic(
        usable["y_true"].to_numpy(dtype=float),
        usable["y_pred"].to_numpy(dtype=float),
    )
    return value if math.isfinite(value) else None


def _pooled_ic(year_ics: list[float | None]) -> float | None:
    """Equal-weighted mean of the within-year Spearman ICs (significance.py rule)."""
    if not year_ics or any(ic is None for ic in year_ics):
        return None
    return float(np.mean([float(ic) for ic in year_ics]))


# --------------------------------------------------------------------------- #
# (a) Rank-position variability & top-k membership stability
# --------------------------------------------------------------------------- #
def bootstrap_year_rank_stability(
    tickers: list[str],
    y_pred: np.ndarray,
    *,
    draws: int,
    rng: np.random.Generator,
    top_k: int = TOP_K,
) -> list[dict[str, object]]:
    """Bootstrap tickers within one year; report rank-interval and top-k frequency.

    Resampling unit is the ticker within this single year: ``draws`` bootstrap
    samples each draw ``n`` tickers with replacement from this year's ``n``
    tickers.  Ranking direction is descending predicted score (rank 1 = highest
    ``y_pred`` = the model's most-favoured name), with deterministic ticker
    tie-breaking; a ticker's within-sample rank is 1 + the number of *distinct*
    drawn tickers with a higher score.  Frequencies are conditional on the ticker
    being drawn.  The year's predictions are never pooled with any other year.
    """
    n = len(tickers)
    if n == 0:
        return []
    # Deterministic descending order (rank 1 = highest y_pred), ties broken by
    # ascending ticker so the ordering is reproducible run to run.
    order = sorted(range(n), key=lambda i: (-float(y_pred[i]), tickers[i]))
    global_rank = [0] * n  # 1-based descending rank per original index
    for position, original_index in enumerate(order):
        global_rank[original_index] = position + 1

    draw_indices = rng.integers(0, n, size=(draws, n))
    present = np.zeros((draws, n), dtype=bool)
    rows = np.repeat(np.arange(draws), n)
    present[rows, draw_indices.ravel()] = True
    # Reorder columns to descending-score order, then a cumulative sum along that
    # order gives each present ticker's within-sample rank (it counts itself).
    present_sorted = present[:, order]
    rank_sorted = np.cumsum(present_sorted, axis=1)

    records: list[dict[str, object]] = []
    for position, original_index in enumerate(order):
        drawn_mask = present_sorted[:, position]
        times_drawn = int(drawn_mask.sum())
        ticker = tickers[original_index]
        base = {
            "ticker": ticker,
            "full_descending_rank": global_rank[original_index],
            "times_drawn": times_drawn,
            "bootstrap_draws": int(draws),
        }
        if times_drawn == 0:
            base.update(
                {
                    "top_k": int(top_k),
                    "top_k_membership_frequency": None,
                    "rank_p2_5": None,
                    "rank_median": None,
                    "rank_p97_5": None,
                    "status": "insufficient_data_never_drawn",
                }
            )
            records.append(base)
            continue
        ranks_when_present = rank_sorted[drawn_mask, position].astype(float)
        in_top_k = int(np.sum(ranks_when_present <= top_k))
        lower, median, upper = (
            float(value)
            for value in np.percentile(ranks_when_present, [2.5, 50.0, 97.5])
        )
        base.update(
            {
                "top_k": int(top_k),
                "top_k_membership_frequency": _rounded(in_top_k / times_drawn),
                "rank_p2_5": _rounded(lower),
                "rank_median": _rounded(median),
                "rank_p97_5": _rounded(upper),
                "status": "complete",
            }
        )
        records.append(base)
    records.sort(key=lambda row: row["ticker"])
    return records


# --------------------------------------------------------------------------- #
# (b) Model-performance uncertainty: leave-k-out jackknife of the pooled IC
# --------------------------------------------------------------------------- #
def _distribution_summary(values: list[float]) -> dict[str, object]:
    """Central summary and dispersion of a pooled-IC jackknife distribution."""
    if not values:
        return {
            "count": 0,
            "mean": None,
            "std": None,
            "min": None,
            "p2_5": None,
            "median": None,
            "p97_5": None,
            "max": None,
            "status": "insufficient_data_no_defined_resamples",
        }
    array = np.asarray(values, dtype=float)
    p2_5, median, p97_5 = (
        float(value) for value in np.percentile(array, [2.5, 50.0, 97.5])
    )
    return {
        "count": int(array.size),
        "mean": _rounded(float(array.mean())),
        "std": _rounded(float(array.std(ddof=1))) if array.size > 1 else _rounded(0.0),
        "min": _rounded(float(array.min())),
        "p2_5": _rounded(p2_5),
        "median": _rounded(median),
        "p97_5": _rounded(p97_5),
        "max": _rounded(float(array.max())),
        "status": "complete",
    }


def jackknife_pooled_ic(
    model_predictions: pd.DataFrame,
    years: list[int],
    *,
    k8_samples: int,
    rng: np.random.Generator,
) -> dict[str, object]:
    """Leave-k-out jackknife dispersion of one model's pooled within-year IC.

    Resampling unit is the ticker-year observation.  ``k=1`` removes every single
    observation exactly once; ``k=8`` removes eight distinct observations per
    seeded draw.  Each affected year's Spearman IC is recomputed on its remaining
    usable rows and the years are re-pooled by equal-weighted mean.  This reports
    the dispersion of a null-consistent estimate, not a confidence interval on
    predictive validity.
    """
    per_year_usable: dict[int, pd.DataFrame] = {}
    per_year_full_ic: dict[int, float | None] = {}
    for year in years:
        usable = model_predictions.loc[model_predictions["year"] == year].dropna(
            subset=["y_true", "y_pred"]
        )
        per_year_usable[year] = usable.reset_index(drop=True)
        per_year_full_ic[year] = _year_ic(usable)

    full_pooled = _pooled_ic([per_year_full_ic[year] for year in years])
    if full_pooled is None:
        return {
            "full_pooled_ic": None,
            "k1_leave_one_out": _distribution_summary([]),
            "k8_leave_eight_out": _distribution_summary([]),
            "status": "insufficient_data_model_pooled_ic_undefined",
        }

    # Flat, deterministically ordered observation index: (year, position-in-year).
    observations: list[tuple[int, int]] = []
    for year in years:
        observations.extend((year, position) for position in range(len(per_year_usable[year])))

    def pooled_after_removal(removed: dict[int, set[int]]) -> float | None:
        year_ics: list[float | None] = []
        for year in years:
            drop = removed.get(year)
            if not drop:
                year_ics.append(per_year_full_ic[year])
                continue
            kept = per_year_usable[year].drop(index=sorted(drop))
            year_ics.append(_year_ic(kept))
        return _pooled_ic(year_ics)

    k1_values: list[float] = []
    for year, position in observations:
        pooled = pooled_after_removal({year: {position}})
        if pooled is not None:
            k1_values.append(pooled)

    k8_values: list[float] = []
    total = len(observations)
    if total >= JACKKNIFE_K:
        for _ in range(k8_samples):
            chosen = rng.choice(total, size=JACKKNIFE_K, replace=False)
            removed: dict[int, set[int]] = {}
            for flat_index in chosen:
                year, position = observations[int(flat_index)]
                removed.setdefault(year, set()).add(position)
            pooled = pooled_after_removal(removed)
            if pooled is not None:
                k8_values.append(pooled)

    k8_summary = _distribution_summary(k8_values)
    if total < JACKKNIFE_K:
        k8_summary["status"] = "insufficient_data_fewer_than_k_observations"

    return {
        "full_pooled_ic": _rounded(full_pooled),
        "observation_count": total,
        "k1_leave_one_out": _distribution_summary(k1_values),
        "k8_leave_eight_out": k8_summary,
        "k8_samples_requested": int(k8_samples),
        "status": "complete",
    }


# --------------------------------------------------------------------------- #
# (c) Cohort-composition sensitivity: public-40 subset pooled IC
# --------------------------------------------------------------------------- #
def cohort_pooled_ic(
    model_predictions: pd.DataFrame,
    years: list[int],
    cohort_tickers: set[str],
) -> dict[str, object]:
    """Pooled IC on the public-40 subset, per-year n reported, no cross-cohort claim.

    A year whose subset falls below ``MIN_COHORT_N`` usable rows is labelled
    ``insufficient_data`` and the pooled value is withheld rather than published
    on a thin cohort.  This is a sensitivity description of cohort composition; it
    is never a statement that one cohort is a better or more tradeable universe.
    """
    per_year: list[dict[str, object]] = []
    year_ics: list[float | None] = []
    any_insufficient = False
    for year in years:
        subset = model_predictions.loc[
            (model_predictions["year"] == year)
            & (model_predictions["ticker"].isin(cohort_tickers))
        ].dropna(subset=["y_true", "y_pred"])
        n = int(len(subset))
        if n < MIN_COHORT_N:
            any_insufficient = True
            year_ics.append(None)
            per_year.append(
                {
                    "year": int(year),
                    "n": n,
                    "year_ic": None,
                    "status": "insufficient_data_below_min_cohort_n",
                }
            )
            continue
        ic = _year_ic(subset)
        year_ics.append(ic)
        per_year.append(
            {
                "year": int(year),
                "n": n,
                "year_ic": _rounded(ic),
                "status": "complete" if ic is not None else "insufficient_data_ic_undefined",
            }
        )

    pooled = None if any_insufficient else _pooled_ic(year_ics)
    return {
        "min_cohort_n": MIN_COHORT_N,
        "public_40_pooled_ic": _rounded(pooled),
        "per_year": per_year,
        "status": "complete" if pooled is not None else "insufficient_data_partial_cohort",
    }


# --------------------------------------------------------------------------- #
# Report assembly
# --------------------------------------------------------------------------- #
def build_report(
    predictions: pd.DataFrame,
    sources: list[dict[str, object]],
    cohort_tickers: set[str],
    cohort_source: dict[str, object],
    *,
    seed: int = DEFAULT_SEED,
    bootstrap_draws: int = DEFAULT_BOOTSTRAP_DRAWS,
    k8_samples: int = DEFAULT_JACKKNIFE_K8_SAMPLES,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Build the isolated rank & cohort stability artifacts from dumps only."""
    if predictions.empty:
        raise ValueError("Prediction dump set is empty")
    if bootstrap_draws < 2000:
        raise ValueError("bootstrap_draws must be at least 2000 (packet design floor)")
    models = sorted(predictions["model"].unique().tolist())
    years = sorted(int(year) for year in predictions["year"].unique().tolist())

    per_model: list[dict[str, object]] = []
    ticker_rows: list[dict[str, object]] = []
    for model_index, model in enumerate(models):
        model_predictions = predictions.loc[predictions["model"] == model]

        rank_stability_by_year: list[dict[str, object]] = []
        for year_index, year in enumerate(years):
            year_rows = model_predictions.loc[model_predictions["year"] == year]
            finite = year_rows.loc[np.isfinite(year_rows["y_pred"])]
            missing = year_rows.loc[~np.isfinite(year_rows["y_pred"])]
            records = bootstrap_year_rank_stability(
                finite["ticker"].tolist(),
                finite["y_pred"].to_numpy(dtype=float),
                draws=bootstrap_draws,
                rng=_rng(seed, model_index, year_index, 1),
            )
            # Missing predictions cannot be ranked; keep them as explicit nulls
            # rather than dropping them, so nothing is silently imputed.
            for ticker in sorted(missing["ticker"].tolist()):
                records.append(
                    {
                        "ticker": ticker,
                        "full_descending_rank": None,
                        "times_drawn": 0,
                        "bootstrap_draws": int(bootstrap_draws),
                        "top_k": int(TOP_K),
                        "top_k_membership_frequency": None,
                        "rank_p2_5": None,
                        "rank_median": None,
                        "rank_p97_5": None,
                        "status": "insufficient_data_missing_prediction",
                    }
                )
            records.sort(key=lambda row: row["ticker"])
            rank_stability_by_year.append({"year": int(year), "tickers": records})
            for record in records:
                ticker_rows.append(
                    {
                        "model": model,
                        "year": int(year),
                        "ticker": record["ticker"],
                        "full_descending_rank": record["full_descending_rank"],
                        "times_drawn": record["times_drawn"],
                        "bootstrap_draws": record["bootstrap_draws"],
                        "top_k": record["top_k"],
                        "top_k_membership_frequency": record["top_k_membership_frequency"],
                        "rank_p2_5": record["rank_p2_5"],
                        "rank_median": record["rank_median"],
                        "rank_p97_5": record["rank_p97_5"],
                        "status": record["status"],
                    }
                )

        jackknife = jackknife_pooled_ic(
            model_predictions,
            years,
            k8_samples=k8_samples,
            rng=_rng(seed, model_index, 0, 2),
        )
        cohort = cohort_pooled_ic(model_predictions, years, cohort_tickers)

        per_model.append(
            {
                "model": model,
                "kind": "ml" if model in ML_MODELS else "baseline",
                "full_universe_pooled_ic": jackknife["full_pooled_ic"],
                "rank_position_and_top_k_stability": rank_stability_by_year,
                "model_performance_uncertainty_jackknife": jackknife,
                "cohort_composition_sensitivity_public_40": cohort,
            }
        )

    ticker_rows.sort(key=lambda row: (row["model"], row["year"], row["ticker"]))

    report = {
        "schema_version": "1.0.0",
        "task": "R3-STAT-01",
        "generated_by": {
            "module": "experiments/rank_stability.py",
            "generator_command": "make research-rank-stability",
            "seed": int(seed),
            "bootstrap_draws_per_model_year": int(bootstrap_draws),
            "jackknife_k8_samples_per_model": int(k8_samples),
            "sampling": "seeded numpy.random.default_rng; positional seed derivation, no string hashing",
            "deterministic_ordering": "model, year, ticker; descending y_pred rank with ascending-ticker tie-break",
            "serialization": "sorted-key JSON, newline-terminated UTF-8 JSON/Markdown/CSV",
            "pooled_ic_source": "experiments.significance.spearman_ic (reused verbatim)",
        },
        "source_artifacts": [*sources, cohort_source],
        "estimands": {
            "rank_position_variability": (
                "For each model, year, and ticker: the 2.5-97.5 percentile interval of the "
                "ticker's within-sample descending rank across within-year ticker bootstraps, "
                "conditional on the ticker being drawn in the bootstrap sample."
            ),
            "top_k_membership_stability": (
                f"For each model, year, and ticker: the frequency, conditional on being drawn, "
                f"that the ticker's within-sample descending rank is <= {TOP_K}."
            ),
            "model_performance_uncertainty": (
                "For each model: the dispersion (mean, std, 2.5/50/97.5 percentiles, range) of "
                "the pooled within-year Spearman IC under leave-1-out (exact) and leave-8-out "
                "(seeded sample) jackknife over ticker-year observations."
            ),
            "cohort_composition_sensitivity": (
                "For each model: the pooled within-year Spearman IC recomputed on the public-40 "
                "subset of the dump rows, with per-year n; a sensitivity description only."
            ),
        },
        "design": {
            "resampling_unit": "ticker within a single test year (never rows pooled across years)",
            "bootstrap": "tickers resampled with replacement independently within each test year",
            "bootstrap_draws_per_model_year": int(bootstrap_draws),
            "jackknife_unit": "ticker-year observation (grouped; not a raw row across the pool)",
            "jackknife_k1": "exact leave-one-out over every observation",
            "jackknife_k8": f"seeded leave-{JACKKNIFE_K}-out; {k8_samples} samples per model",
            "seed": int(seed),
            "rank_direction": "descending predicted score; rank 1 = highest y_pred (the model's top name)",
            "tie_breaking": "deterministic ascending ticker within equal predicted score",
            "pooled_ic_definition": "equal-weighted mean of the within-year Spearman ICs (identical to experiments/significance.py analyze_model)",
            "universe": "81-ticker retrospective training universe; 80 evaluated rows per model-year; public-40 subset where stated",
            "target_years": years,
            "models": models,
            "model_count": len(models),
            "top_k": int(TOP_K),
            "min_cohort_n": int(MIN_COHORT_N),
            "raw_prediction_magnitudes_compared_across_models": False,
            "distinct_quantities_not_collapsed": (
                "Rank-position variability, top-k membership stability, model-performance "
                "uncertainty, and cohort-composition sensitivity are reported separately and are "
                "never combined into a single confidence score. Pairwise ordering stability is a "
                "distinct quantity outside this packet's scope and is not computed here."
            ),
            "significance_test_added": False,
            "p_values_republished": False,
            "core_model_or_ranking_changed": False,
            "missing_prediction_handling": (
                "No values are filled. Tickers never drawn, years/cohorts with an undefined IC, "
                "or public-40 years below the minimum n yield explicit null with an "
                "insufficient-data status."
            ),
        },
        "claim_safety_sentence": CLAIM_SAFETY_SENTENCE,
        "per_model": per_model,
        "artifacts": {
            "json_report": "experiments/results_rank_stability/rank_stability_report.json",
            "markdown_report": "experiments/results_rank_stability/rank_stability_report.md",
            "ticker_csv": "experiments/results_rank_stability/stability_by_ticker.csv",
        },
        "findings": [
            MECHANICAL_TOP_K_DISCLOSURE,
            "Top-k membership frequency and rank intervals describe resampling variability of a ranking already indistinguishable from the within-year null; they are not pick-confidence.",
            "The jackknife dispersion measures how much the pooled IC moves under small cohort perturbations; it is not a confidence interval on any stock outperforming.",
            "The public-40 pooled IC is a cohort-composition sensitivity, reported with per-year n; it is not a claim that one cohort is a better or more tradeable universe.",
            "Raw prediction magnitudes are never compared across models because their scales differ by model; only within-year ranks enter the diagnostics.",
            "Distinct quantities are kept separate and are never collapsed into one confidence score; any absent or thin observation, year, or cohort stays an explicit null with a status.",
        ],
        "claim_safety": {
            "describes_resampling_variability_only": True,
            "top_rank_frequency_is_pick_confidence": False,
            "identifies_validated_picks": False,
            "cohort_comparison_is_selection_signal": False,
            "predictive_validity_established": False,
            "reliable_predictive_edge_established": False,
            "investment_value_established": False,
            "recommendations_emitted": False,
            "new_significance_or_p_values_produced": False,
            "existing_significance_power_disagreement_influence_results_changed": False,
            "existing_real_terms_regime_or_friction_interpretation_changed": False,
            "production_ranking_or_model_changed": False,
        },
        "limitations": [
            "This is the retrospective 81-ticker training universe with 80 evaluated rows per model-year, not verified point-in-time BIST100 membership; survivorship and universe-selection risks remain.",
            "The public-40 subset is a fixed repository cohort, not point-in-time index constituents; sector membership, liquidity, tradeability, and corporate-action history are not inferred here.",
            "Only three target years are represented, all within one unusual nominal-TRY macro regime; stability rankings do not establish regime robustness.",
            "Stability under resampling is not predictive validity: a stable but null-consistent ranking remains indistinguishable from noise, and an unstable ranking does not establish opportunity.",
            "Top-k membership frequency is conditional on being drawn and is a resampling artifact; it is not a probability that a ticker will outperform.",
            "The jackknife dispersion describes the pooled IC estimator's fragility under a tiny three-year sample, not economic value, trading profitability, or out-of-sample skill.",
            "Ticker-year deletion units are treated as exchangeable only for this descriptive sensitivity diagnostic. Repeated tickers across years and within-year cross-sectional dependence prevent interpretation as sampling uncertainty.",
            "No new significance test or p-value is produced; the existing multiplicity correction, low-power limits, and null-consistent conclusion are unchanged.",
            "This report uses nominal-TRY persisted dumps only and does not replace or merge the parallel real-TRY or USD-basis evidence.",
            "Reproduction is numerical-environment-qualified; deterministic byte identity is demonstrated only in the current environment.",
            "Research support only; not investment advice.",
        ],
    }
    return report, ticker_rows


def render_markdown(report: dict[str, object]) -> str:
    """Render a concise, deterministic report without raw prediction magnitudes."""
    design = report["design"]
    lines = [
        "# Ranking & cohort stability diagnostics",
        "",
        "## Scope and estimands",
        "",
        "This R3-STAT-01 artifact measures, from the persisted walk-forward dumps only, "
        "three separate and un-combined quantities: (a) each ticker's within-year "
        "rank-position variability and top-10 membership stability under seeded "
        "within-year ticker bootstraps; (b) each model's pooled within-year Spearman IC "
        "dispersion under leave-1-out and seeded leave-8-out jackknife over ticker-year "
        "observations; and (c) each model's pooled IC recomputed on the public-40 cohort "
        "with per-year n. The pooled IC reuses `experiments/significance.py` verbatim. It "
        "does not retrain models, change any production ranking, compare raw prediction "
        "magnitudes across models, or produce any new significance test or p-value.",
        "",
        str(report["claim_safety_sentence"]),
        "",
        MECHANICAL_TOP_K_DISCLOSURE,
        "",
        "## Provenance and regeneration",
        "",
        f"Generator: `experiments/rank_stability.py` via `make research-rank-stability`. "
        f"Seed {design['seed']}; {design['bootstrap_draws_per_model_year']} within-year "
        f"bootstrap draws per model-year; "
        f"{report['generated_by']['jackknife_k8_samples_per_model']} leave-8-out samples "
        f"per model. Resampling unit: {design['resampling_unit']}.",
        "",
        "| Source artifact | SHA-256 | Rows |",
        "|---|---|---:|",
    ]
    for source in report["source_artifacts"]:
        lines.append(
            f"| {source['path']} | `{source['sha256']}` | {source['rows']} |"
        )
    lines.extend(
        [
            "",
            "The machine-readable report and `stability_by_ticker.csv` carry the complete "
            "per-ticker rank intervals, top-10 frequencies, and explicit insufficient-data "
            "statuses.",
            "",
            "## Per-model pooled-IC uncertainty and cohort sensitivity",
            "",
            "| Model | Kind | Full pooled IC | LOO IC mean (p2.5–p97.5 of deletion estimates) | k=8 IC std | Public-40 pooled IC | Public-40 per-year n |",
            "|---|---|---:|---|---:|---:|---|",
        ]
    )
    for summary in report["per_model"]:
        jack = summary["model_performance_uncertainty_jackknife"]
        k1 = jack["k1_leave_one_out"]
        k8 = jack["k8_leave_eight_out"]
        cohort = summary["cohort_composition_sensitivity_public_40"]
        per_year_n = ", ".join(
            f"{item['year']}:{item['n']}" for item in cohort["per_year"]
        )
        loo = (
            f"{k1['mean']} [{k1['p2_5']}, {k1['p97_5']}]"
            if k1["mean"] is not None
            else "insufficient_data"
        )
        full_pooled_ic = str(summary["full_universe_pooled_ic"])
        if (
            summary["model"] == "baseline_equal_weight"
            and summary["full_universe_pooled_ic"] is not None
        ):
            full_pooled_ic += f" — {BASELINE_EQUAL_WEIGHT_IC_QUALIFIER}"
        lines.append(
            f"| {summary['model']} | {summary['kind']} | {full_pooled_ic} | "
            f"{loo} | {k8['std']} | {cohort['public_40_pooled_ic']} | {per_year_n} |"
        )
    lines.extend(
        [
            "",
            DELETION_RANGE_DISCLAIMER,
            "",
            "The public-40 column is a cohort-composition sensitivity reported with per-year n; "
            "it is not a comparison establishing that either cohort is a better or more "
            "tradeable universe.",
            "",
            "## Interpretation boundaries",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in report["findings"])
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.extend(
        [
            "",
            "The conclusion remains: no reliable predictive edge. Research support only; not investment advice.",
            "",
        ]
    )
    text = "\n".join(lines)
    validate_claim_safety_text(text)
    return text


def write_ticker_csv(path: Path, rows: list[dict[str, object]]) -> None:
    """Serialize the complete per-ticker stability table deterministically."""
    fieldnames = [
        "model",
        "year",
        "ticker",
        "full_descending_rank",
        "times_drawn",
        "bootstrap_draws",
        "top_k",
        "top_k_membership_frequency",
        "rank_p2_5",
        "rank_median",
        "rank_p97_5",
        "status",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)


def run(
    output_dir: Path = OUTPUT_DIR,
    *,
    prediction_paths: Iterable[Path] = PREDICTION_PATHS,
    public_40_config: Path = PUBLIC_40_CONFIG,
    seed: int = DEFAULT_SEED,
    bootstrap_draws: int = DEFAULT_BOOTSTRAP_DRAWS,
    k8_samples: int = DEFAULT_JACKKNIFE_K8_SAMPLES,
) -> tuple[Path, Path, Path]:
    """Generate the isolated rank & cohort stability artifacts from immutable inputs."""
    prediction_paths = tuple(Path(path) for path in prediction_paths)
    predictions, sources = load_prediction_dumps(prediction_paths)
    cohort_tickers, cohort_source = load_public_40(public_40_config)
    report, ticker_rows = build_report(
        predictions,
        sources,
        cohort_tickers,
        cohort_source,
        seed=seed,
        bootstrap_draws=bootstrap_draws,
        k8_samples=k8_samples,
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / JSON_OUTPUT.name
    markdown_path = output_dir / MARKDOWN_OUTPUT.name
    ticker_path = output_dir / TICKER_OUTPUT.name
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    write_ticker_csv(ticker_path, ticker_rows)
    print(
        f"[rank-stability] models={report['design']['model_count']} "
        f"years={len(report['design']['target_years'])} "
        f"bootstrap_draws={bootstrap_draws} ticker_rows={len(ticker_rows)} -> {output_dir}"
    )
    return json_path, markdown_path, ticker_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--bootstrap-draws", type=int, default=DEFAULT_BOOTSTRAP_DRAWS)
    parser.add_argument(
        "--k8-samples", type=int, default=DEFAULT_JACKKNIFE_K8_SAMPLES
    )
    args = parser.parse_args()
    run(
        args.output_dir,
        seed=args.seed,
        bootstrap_draws=args.bootstrap_draws,
        k8_samples=args.k8_samples,
    )


if __name__ == "__main__":
    main()
