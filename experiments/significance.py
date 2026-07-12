"""Permutation tests and bootstrap intervals from persisted prediction dumps.

This module never trains a model. It consumes predictions_<split>.csv artifacts
written by run_experiments.py and preserves the year structure in every resample.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "experiments" / "results"
REQUIRED_COLUMNS = ["ticker", "year", "model", "y_true", "y_pred"]
ML_MODELS = (
    "linear_regression",
    "ridge",
    "lasso",
    "elasticnet",
    "random_forest",
    "gradient_boosting",
)
DEFAULT_SEED = 42
DEFAULT_PERMUTATIONS = 10_000
DEFAULT_BOOTSTRAPS = 10_000
DEFAULT_POWER_SIMULATIONS = 5_000
POWER_ALPHA = 0.05
POWER_TARGET = 0.80
POWER_AGREEMENT_TOLERANCE = 0.05
PUBLIC_UNIVERSE_PLANNING_N = 40
PROJECTION_EXTRA_YEARS = (0, 1, 2, 3, 5, 7)
_STANDARD_NORMAL = NormalDist()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rank(values: np.ndarray) -> np.ndarray:
    return pd.Series(values).rank(method="average").to_numpy(dtype=float)


def _rowwise_correlation(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    left_centered = left - left.mean(axis=1, keepdims=True)
    right_centered = right - right.mean(axis=1, keepdims=True)
    denominator = np.sqrt(
        np.sum(left_centered**2, axis=1) * np.sum(right_centered**2, axis=1)
    )
    numerator = np.sum(left_centered * right_centered, axis=1)
    return np.divide(
        numerator,
        denominator,
        out=np.full(len(left), np.nan, dtype=float),
        where=denominator > 0,
    )


def spearman_ic(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Spearman rank correlation with average ranks for ties."""
    true_rank = _rank(np.asarray(y_true, dtype=float))
    pred_rank = _rank(np.asarray(y_pred, dtype=float))
    value = _rowwise_correlation(true_rank[None, :], pred_rank[None, :])[0]
    return float(value)


def fisher_power(
    true_ic: float,
    *,
    n_per_split: int,
    split_count: int = 1,
    alpha: float = POWER_ALPHA,
) -> float:
    """Approximate two-sided power for an equal-year Spearman IC design.

    The approximation treats Fisher-transformed within-year Spearman
    correlations as independent with variance ``1 / (n - 3)``. It is a design
    calculation, not an estimate of the true IC and not a practical-return test.
    """
    if not -1.0 < true_ic < 1.0:
        raise ValueError("true_ic must be strictly between -1 and 1")
    if n_per_split < 4:
        raise ValueError("n_per_split must be at least 4")
    if split_count < 1:
        raise ValueError("split_count must be positive")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be strictly between 0 and 1")

    information = split_count * (n_per_split - 3)
    mean_shift = math.atanh(abs(true_ic)) * math.sqrt(information)
    critical_value = _STANDARD_NORMAL.inv_cdf(1.0 - alpha / 2.0)
    upper_tail = 1.0 - _STANDARD_NORMAL.cdf(critical_value - mean_shift)
    lower_tail = _STANDARD_NORMAL.cdf(-critical_value - mean_shift)
    return float(upper_tail + lower_tail)


def minimum_detectable_ic(
    *,
    n_per_split: int,
    split_count: int = 1,
    alpha: float = POWER_ALPHA,
    target_power: float = POWER_TARGET,
) -> float:
    """Return the minimum absolute IC reaching the requested analytic power."""
    if not 0.0 < target_power < 1.0:
        raise ValueError("target_power must be strictly between 0 and 1")
    if target_power <= alpha:
        return 0.0

    lower = 0.0
    upper = 1.0 - 1e-12
    for _ in range(80):
        midpoint = (lower + upper) / 2.0
        if fisher_power(
            midpoint,
            n_per_split=n_per_split,
            split_count=split_count,
            alpha=alpha,
        ) >= target_power:
            upper = midpoint
        else:
            lower = midpoint
    return float(upper)


def _ordinal_row_ranks(values: np.ndarray) -> np.ndarray:
    """Fast row ranks for continuous simulation draws, where ties occur with probability zero."""
    order = np.argsort(values, axis=1)
    ranks = np.empty_like(order, dtype=float)
    rows = np.arange(len(values))[:, None]
    ranks[rows, order] = np.arange(values.shape[1], dtype=float)
    return ranks


def simulate_fisher_power(
    true_ic: float,
    *,
    n_per_split: int,
    split_count: int = 1,
    simulations: int = DEFAULT_POWER_SIMULATIONS,
    seed: int = DEFAULT_SEED,
    alpha: float = POWER_ALPHA,
) -> float:
    """Seeded Gaussian-copula cross-check of the Fisher-z power approximation."""
    if not -1.0 < true_ic < 1.0:
        raise ValueError("true_ic must be strictly between -1 and 1")
    if n_per_split < 4:
        raise ValueError("n_per_split must be at least 4")
    if split_count < 1:
        raise ValueError("split_count must be positive")
    if simulations < 1:
        raise ValueError("simulations must be positive")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be strictly between 0 and 1")

    # For a bivariate Gaussian copula, rho_s = 6/pi * asin(rho_p/2).
    latent_correlation = 2.0 * math.sin(math.pi * true_ic / 6.0)
    residual_scale = math.sqrt(1.0 - latent_correlation**2)
    critical_value = _STANDARD_NORMAL.inv_cdf(1.0 - alpha / 2.0)
    rng = np.random.default_rng(seed)
    rejected = 0
    completed = 0
    chunk_size = min(1_000, simulations)
    while completed < simulations:
        batch_size = min(chunk_size, simulations - completed)
        fisher_parts = []
        for _ in range(split_count):
            left = rng.normal(size=(batch_size, n_per_split))
            noise = rng.normal(size=(batch_size, n_per_split))
            right = latent_correlation * left + residual_scale * noise
            correlations = _rowwise_correlation(
                _ordinal_row_ranks(left), _ordinal_row_ranks(right)
            )
            fisher_parts.append(np.arctanh(np.clip(correlations, -0.999999, 0.999999)))
        combined_z = np.mean(np.vstack(fisher_parts), axis=0) * math.sqrt(
            split_count * (n_per_split - 3)
        )
        rejected += int(np.sum(np.abs(combined_z) > critical_value))
        completed += batch_size
    return float(rejected / simulations)


def build_power_analysis(
    evaluated_per_split: list[int],
    *,
    simulations: int = DEFAULT_POWER_SIMULATIONS,
    seed: int = DEFAULT_SEED,
) -> dict:
    """Build actual-design and public-40 planning-sensitivity power results."""
    if len(evaluated_per_split) != 1:
        raise ValueError(
            "power analysis requires one common evaluated-row count across split/model groups"
        )
    current_n = int(evaluated_per_split[0])
    designs = [
        ("current_one_split", current_n, 1, "actual prediction-dump design"),
        ("current_three_year_pooled", current_n, 3, "actual prediction-dump design"),
        (
            "public_40_one_split_sensitivity",
            PUBLIC_UNIVERSE_PLANNING_N,
            1,
            "planning sensitivity; not the current dump design",
        ),
        (
            "public_40_three_year_sensitivity",
            PUBLIC_UNIVERSE_PLANNING_N,
            3,
            "planning sensitivity; not the current dump design",
        ),
    ]
    design_results = []
    for design_index, (design_id, n_per_split, split_count, scope) in enumerate(designs):
        detectable = minimum_detectable_ic(
            n_per_split=n_per_split,
            split_count=split_count,
        )
        simulated_at_mde = simulate_fisher_power(
            detectable,
            n_per_split=n_per_split,
            split_count=split_count,
            simulations=simulations,
            seed=seed + design_index * 100,
        )
        curve = []
        for point_index, multiplier in enumerate((0.0, 0.5, 1.0, 1.25)):
            true_ic = min(0.95, detectable * multiplier)
            simulated = simulate_fisher_power(
                true_ic,
                n_per_split=n_per_split,
                split_count=split_count,
                simulations=simulations,
                seed=seed + design_index * 100 + point_index + 1,
            )
            curve.append(
                {
                    "assumed_true_ic": float(true_ic),
                    "analytic_power": fisher_power(
                        true_ic,
                        n_per_split=n_per_split,
                        split_count=split_count,
                    ),
                    "simulated_rejection_rate": simulated,
                }
            )
        difference = abs(simulated_at_mde - POWER_TARGET)
        design_results.append(
            {
                "design_id": design_id,
                "scope": scope,
                "n_per_split": n_per_split,
                "split_count": split_count,
                "total_evaluated_rows": n_per_split * split_count,
                "analytic_minimum_detectable_abs_ic": detectable,
                "simulated_power_at_analytic_mde": simulated_at_mde,
                "absolute_power_difference": difference,
                "agreement_within_tolerance": difference <= POWER_AGREEMENT_TOLERANCE,
                "simulation_curve": curve,
            }
        )

    projections = []
    for extra_years in PROJECTION_EXTRA_YEARS:
        total_years = 3 + extra_years
        projections.append(
            {
                "additional_years": extra_years,
                "total_test_years": total_years,
                "n_per_year": PUBLIC_UNIVERSE_PLANNING_N,
                "analytic_minimum_detectable_abs_ic": minimum_detectable_ic(
                    n_per_split=PUBLIC_UNIVERSE_PLANNING_N,
                    split_count=total_years,
                ),
            }
        )

    return {
        "method": (
            "two-sided Fisher z approximation for independent within-year Spearman ICs; "
            "equal year weights and variance 1/(n-3)"
        ),
        "alpha_two_sided": POWER_ALPHA,
        "target_power": POWER_TARGET,
        "multiplicity_scope": (
            "single prespecified IC test at alpha=0.05; this power calculation does not "
            "represent Bonferroni-adjusted family-wise power across six ML models"
        ),
        "simulation": {
            "method": (
                "seeded Gaussian-copula draws calibrated to assumed Spearman IC, converted "
                "to ranks, and rejected with the same Fisher-z approximation"
            ),
            "simulations_per_curve_point": simulations,
            "seed": seed,
            "agreement_tolerance_absolute_power": POWER_AGREEMENT_TOLERANCE,
        },
        "definitions": {
            "observed_ic": "sample estimate computed from persisted prediction dumps",
            "detectable_ic": (
                "assumed true absolute IC yielding 80% long-run rejection probability under "
                "the stated approximation; not a hard significance cutoff"
            ),
            "statistical_power": (
                "long-run probability of rejecting a zero-IC null when the stated true IC "
                "and design assumptions hold"
            ),
            "practical_relevance": (
                "not evaluated by this calculation; detectability does not establish economic "
                "value, robustness, implementability, or investment relevance"
            ),
        },
        "designs": design_results,
        "projection_framing": (
            "The pipeline is ready for more data; this is pipeline capability, not a promise "
            "that more data will produce predictive skill or practical returns."
        ),
        "projection_40_tickers_per_year": projections,
        "limitations": [
            "Only three test years are observed; treating within-year IC estimates as independent is an approximation.",
            "The calculation assumes equal per-year sample sizes and a stable true IC across years, neither of which establishes regime generality.",
            "The 40-ticker table is a planning sensitivity for the public-universe scale, not the current 80-row prediction-dump design.",
            "The cohort is retrospective rather than verified point-in-time membership, and reproducibility remains numerical-environment-qualified.",
            "Power bounds detection under assumptions; it neither estimates the true IC nor establishes practical investment relevance.",
        ],
    }


def _permutation_distribution(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    iterations: int,
    rng: np.random.Generator,
) -> np.ndarray:
    true_rank = _rank(y_true)
    pred_rank = _rank(y_pred)
    indices = np.argsort(rng.random((iterations, len(y_true))), axis=1)
    shuffled_true = true_rank[indices]
    repeated_pred = np.broadcast_to(pred_rank, shuffled_true.shape)
    return _rowwise_correlation(shuffled_true, repeated_pred)


def _bootstrap_distribution(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    iterations: int,
    rng: np.random.Generator,
) -> np.ndarray:
    indices = rng.integers(0, len(y_true), size=(iterations, len(y_true)))
    sampled_true = y_true[indices]
    sampled_pred = y_pred[indices]
    true_rank = pd.DataFrame(sampled_true).rank(axis=1, method="average").to_numpy()
    pred_rank = pd.DataFrame(sampled_pred).rank(axis=1, method="average").to_numpy()
    return _rowwise_correlation(true_rank, pred_rank)


def _two_sided_p_value(observed: float, null: np.ndarray) -> float:
    valid = null[np.isfinite(null)]
    return float((np.sum(np.abs(valid) >= abs(observed)) + 1) / (len(valid) + 1))


def _percentile(observed: float, null: np.ndarray) -> float:
    valid = null[np.isfinite(null)]
    return float(100.0 * (np.sum(valid < observed) + 0.5 * np.sum(valid == observed)) / len(valid))


def _ci(distribution: np.ndarray) -> list[float]:
    valid = distribution[np.isfinite(distribution)]
    lower, upper = np.quantile(valid, [0.025, 0.975])
    return [float(lower), float(upper)]


def _histogram(distribution: np.ndarray) -> dict:
    valid = distribution[np.isfinite(distribution)]
    counts, edges = np.histogram(valid, bins=np.linspace(-1.0, 1.0, 41))
    return {
        "bin_edges": [round(float(value), 6) for value in edges],
        "counts": [int(value) for value in counts],
    }


def _statistic(observed: float, null: np.ndarray, bootstrap: np.ndarray, n: int) -> dict:
    return {
        "n": int(n),
        "observed_ic": float(observed),
        "permutation_p_value_two_sided": _two_sided_p_value(observed, null),
        "observed_null_percentile": _percentile(observed, null),
        "bootstrap_ci_95": _ci(bootstrap),
    }


def analyze_model(
    predictions: pd.DataFrame,
    *,
    permutations: int = DEFAULT_PERMUTATIONS,
    bootstraps: int = DEFAULT_BOOTSTRAPS,
    seed: int = DEFAULT_SEED,
) -> dict:
    """Analyze one model using within-split resampling and equal split weights."""
    if permutations < 1_000:
        raise ValueError("permutations must be at least 1,000")
    if bootstraps < 1:
        raise ValueError("bootstraps must be positive")

    clean = predictions.dropna(subset=["y_true", "y_pred"]).copy()
    if not np.isfinite(clean[["y_true", "y_pred"]].to_numpy(dtype=float)).all():
        raise ValueError("predictions contain non-finite values")

    rng = np.random.default_rng(seed)
    split_results = []
    permutation_parts = []
    bootstrap_parts = []
    observed_parts = []
    total_n = 0
    for split, group in clean.groupby("split", sort=True):
        if group["year"].nunique() != 1:
            raise ValueError(f"{split} contains more than one target year")
        if len(group) < 3:
            raise ValueError(f"{split} has fewer than three evaluated rows")
        y_true = group["y_true"].to_numpy(dtype=float)
        y_pred = group["y_pred"].to_numpy(dtype=float)
        observed = spearman_ic(y_true, y_pred)
        null = _permutation_distribution(y_true, y_pred, permutations, rng)
        bootstrap = _bootstrap_distribution(y_true, y_pred, bootstraps, rng)
        stats = _statistic(observed, null, bootstrap, len(group))
        stats.update({"split": str(split), "year": int(group["year"].iloc[0])})
        split_results.append(stats)
        permutation_parts.append(null)
        bootstrap_parts.append(bootstrap)
        observed_parts.append(observed)
        total_n += len(group)

    pooled_observed = float(np.mean(observed_parts))
    pooled_null = np.mean(np.vstack(permutation_parts), axis=0)
    pooled_bootstrap = np.nanmean(np.vstack(bootstrap_parts), axis=0)
    pooled = _statistic(pooled_observed, pooled_null, pooled_bootstrap, total_n)
    pooled.update(
        {
            "split_count": len(split_results),
            "null_distribution_quantiles": {
                str(q): float(np.quantile(pooled_null, q))
                for q in (0.01, 0.05, 0.5, 0.95, 0.99)
            },
            "null_histogram": _histogram(pooled_null),
        }
    )
    return {"pooled": pooled, "exploratory_by_split": split_results}


def load_prediction_dumps(results_dir: Path = RESULTS) -> tuple[pd.DataFrame, list[dict]]:
    paths = sorted(results_dir.glob("predictions_test_*.csv"))
    if not paths:
        raise FileNotFoundError(
            f"no predictions_test_*.csv files found in {results_dir}; run 'make research' first"
        )

    frames = []
    sources = []
    for path in paths:
        frame = pd.read_csv(path)
        if list(frame.columns) != REQUIRED_COLUMNS:
            raise ValueError(
                f"{path.name} columns must be exactly {REQUIRED_COLUMNS}; got {list(frame.columns)}"
            )
        split = path.stem.removeprefix("predictions_")
        frame["split"] = split
        if frame.duplicated(["ticker", "year", "model"]).any():
            raise ValueError(f"{path.name} contains duplicate ticker/year/model rows")
        frames.append(frame)
        sources.append(
            {
                "path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
                "sha256": _sha256(path),
                "rows": int(len(frame)),
                "year": int(frame["year"].iloc[0]),
                "models": sorted(frame["model"].unique().tolist()),
            }
        )
    return pd.concat(frames, ignore_index=True), sources


def build_report(
    predictions: pd.DataFrame,
    sources: list[dict],
    *,
    permutations: int = DEFAULT_PERMUTATIONS,
    bootstraps: int = DEFAULT_BOOTSTRAPS,
    seed: int = DEFAULT_SEED,
    power_simulations: int = DEFAULT_POWER_SIMULATIONS,
) -> dict:
    models = sorted(predictions["model"].unique())
    missing_ml = sorted(set(ML_MODELS) - set(models))
    if missing_ml:
        raise ValueError(f"prediction dumps are missing ML models: {missing_ml}")

    results = []
    for model in models:
        result = analyze_model(
            predictions[predictions["model"] == model],
            permutations=permutations,
            bootstraps=bootstraps,
            seed=seed,
        )
        result.update({"model": model, "kind": "ml" if model in ML_MODELS else "baseline"})
        results.append(result)

    family_size = len(ML_MODELS)
    for result in results:
        pooled = result["pooled"]
        if result["kind"] == "ml":
            adjusted = min(1.0, pooled["permutation_p_value_two_sided"] * family_size)
            pooled["bonferroni_adjusted_p_value"] = adjusted
            pooled["significant_fwer_0_05"] = bool(adjusted < 0.05)
        else:
            pooled["bonferroni_adjusted_p_value"] = None
            pooled["significant_fwer_0_05"] = None

    ml_results = [result for result in results if result["kind"] == "ml"]
    headline_model = min(
        ml_results,
        key=lambda item: (item["pooled"]["permutation_p_value_two_sided"], item["model"]),
    )
    headline = {
        "selection": "smallest pooled raw permutation p-value among the six ML models",
        "model": headline_model["model"],
        **{
            key: headline_model["pooled"][key]
            for key in (
                "observed_ic",
                "permutation_p_value_two_sided",
                "observed_null_percentile",
                "bootstrap_ci_95",
                "bonferroni_adjusted_p_value",
                "significant_fwer_0_05",
            )
        },
    }
    headline["conclusion"] = (
        "At least one ML model is statistically distinguishable from the within-year null "
        "after Bonferroni correction, but this alone does not establish a reliable edge."
        if headline["significant_fwer_0_05"]
        else "No ML model is statistically distinguishable from the within-year null after "
        "Bonferroni correction; the data do not support a reliable predictive edge."
    )

    evaluated_per_split = sorted(
        int(value)
        for value in predictions.groupby(["split", "model"], sort=True).size().unique()
    )
    evaluated_label = ", ".join(str(value) for value in evaluated_per_split)
    return {
        "schema_version": 2,
        "analysis": {
            "statistic": "equal-weighted mean of within-split Spearman ICs",
            "permutation": "two-sided; realized returns shuffled independently within each test year",
            "bootstrap": "tickers resampled with replacement independently within each test year",
            "permutations": permutations,
            "bootstraps": bootstraps,
            "seed": seed,
            "evaluated_tickers_per_model_split": evaluated_per_split,
            "multiplicity": {
                "method": "Bonferroni",
                "family": list(ML_MODELS),
                "family_size": family_size,
                "family_wise_alpha": 0.05,
            },
        },
        "source_artifacts": sources,
        "headline": headline,
        "power_analysis": build_power_analysis(
            evaluated_per_split,
            simulations=power_simulations,
            seed=seed,
        ),
        "models": results,
        "limitations": [
            f"Only three test years with {evaluated_label} evaluated tickers per model and split; estimates remain noisy.",
            "The cohort is a retrospectively fixed repository universe, not verified point-in-time BIST100 membership.",
            "Prediction artifact byte reproducibility is environment-qualified; manifests separate same-environment byte identity from cross-environment semantic checks.",
            "Nominal TRY returns cover one unusual macro regime, so absence of detected signal is not a general market-efficiency claim.",
            "Research support only; not investment advice.",
        ],
    }


def _fmt(value: float | None, digits: int = 3) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"


def render_markdown(report: dict) -> str:
    headline = report["headline"]
    ci = headline["bootstrap_ci_95"]
    conclusion = headline["conclusion"]
    evaluated = report["analysis"]["evaluated_tickers_per_model_split"]
    evaluated_label = ", ".join(str(value) for value in evaluated)
    lines = [
        "# Headline IC significance report",
        "",
        "## Pooled, multiplicity-corrected result",
        "",
        f"The smallest pooled raw p-value among the six ML models belongs to "
        f"**{headline['model']}**: pooled IC {_fmt(headline['observed_ic'])}, "
        f"two-sided within-year permutation p={_fmt(headline['permutation_p_value_two_sided'], 4)}, "
        f"Bonferroni-adjusted p={_fmt(headline['bonferroni_adjusted_p_value'], 4)}, and "
        f"bootstrap 95% CI [{_fmt(ci[0])}, {_fmt(ci[1])}].",
        "",
        conclusion,
        "",
        "The pooled statistic is the equal-weighted mean of within-year Spearman ICs. "
        "Realized returns are shuffled within each test year, and bootstrap samples resample "
        "tickers within each year; years are never pooled before resampling.",
        "",
        "## Pooled model results",
        "",
        "| Model | Kind | Pooled IC | Permutation p | Null percentile | Bootstrap 95% CI | Bonferroni p | FWER significant |",
        "| --- | --- | ---: | ---: | ---: | --- | ---: | --- |",
    ]
    for result in report["models"]:
        pooled = result["pooled"]
        pooled_ci = pooled["bootstrap_ci_95"]
        adjusted = pooled["bonferroni_adjusted_p_value"]
        significant = pooled["significant_fwer_0_05"]
        lines.append(
            f"| {result['model']} | {result['kind']} | {_fmt(pooled['observed_ic'])} | "
            f"{_fmt(pooled['permutation_p_value_two_sided'], 4)} | "
            f"{_fmt(pooled['observed_null_percentile'], 1)}% | "
            f"[{_fmt(pooled_ci[0])}, {_fmt(pooled_ci[1])}] | "
            f"{_fmt(adjusted, 4)} | "
            f"{'yes' if significant else 'no' if significant is not None else 'not in ML family'} |"
        )

    power = report["power_analysis"]
    lines.extend(
        [
            "",
            "## Statistical power and minimum detectable IC",
            "",
            "Observed IC, detectable IC, and statistical power answer different questions. "
            "Observed IC is the sample estimate from the persisted dumps. Detectable IC is "
            "the assumed true |IC| that reaches 80% long-run rejection probability here; it "
            "is not a hard significance cutoff. Statistical power is that long-run probability, "
            "not the probability that a reported model is true. Practical investment relevance "
            "is not evaluated by this calculation.",
            "",
            f"The analytic calculation uses a two-sided Fisher-z approximation for Spearman "
            f"IC at alpha={power['alpha_two_sided']:.2f} and target power "
            f"{power['target_power']:.0%}. It covers one prespecified IC test; it is not the "
            "Bonferroni-adjusted family-wise power of the six-model search.",
            "",
            "| Design | Scope | Rows/year | Test years | Total rows | Detectable \\|IC\\| (analytic) | Simulated power at analytic MDE | Agreement |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for design in power["designs"]:
        lines.append(
            f"| {design['design_id']} | {design['scope']} | {design['n_per_split']} | "
            f"{design['split_count']} | {design['total_evaluated_rows']} | "
            f"{_fmt(design['analytic_minimum_detectable_abs_ic'])} | "
            f"{_fmt(design['simulated_power_at_analytic_mde'], 3)} | "
            f"{'within ±0.05' if design['agreement_within_tolerance'] else 'outside ±0.05'} |"
        )

    lines.extend(
        [
            "",
            "The seeded Gaussian-copula rank simulation checks several assumed true ICs for "
            "each design; full curves are in `significance_report.json`. Agreement means the "
            "simulated rejection rate at the analytic MDE is within 0.05 of 80%, not that the "
            "approximation or underlying design assumptions are proven correct.",
            "",
            "### Forty-ticker-per-year planning projection",
            "",
            power["projection_framing"],
            "",
            "| Additional test years | Total test years | Tickers/year | Detectable \\|IC\\| (analytic) |",
            "| ---: | ---: | ---: | ---: |",
        ]
    )
    for projection in power["projection_40_tickers_per_year"]:
        lines.append(
            f"| {projection['additional_years']} | {projection['total_test_years']} | "
            f"{projection['n_per_year']} | "
            f"{_fmt(projection['analytic_minimum_detectable_abs_ic'])} |"
        )
    lines.extend(
        [
            "",
            "Power-analysis limits:",
            "",
            *[f"- {limitation}" for limitation in power["limitations"]],
        ]
    )

    lines.extend(
        [
            "",
            "Bonferroni correction covers the six ML models only; baselines are shown as "
            "context and are not part of that model-selection family. Their p-values are "
            "unadjusted and descriptive; they do not establish a reliable edge in only three "
            "test years from a retrospectively fixed cohort.",
            "",
            "## Exploratory per-split results",
            "",
            "Per-split ICs at n≈40 have SE ≈ 0.16 in the public-40 framing cited by the task "
            f"queue. The current harness prediction dumps evaluate n={evaluated_label} per "
            "model and split from the internal training universe; with only three test years, "
            "these rows remain exploratory and must not be promoted as discoveries.",
            "",
            "| Model | Split | Year | n | IC | Permutation p | Bootstrap 95% CI |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for result in report["models"]:
        for split in result["exploratory_by_split"]:
            split_ci = split["bootstrap_ci_95"]
            lines.append(
                f"| {result['model']} | {split['split']} (exploratory) | {split['year']} | "
                f"{split['n']} | {_fmt(split['observed_ic'])} | "
                f"{_fmt(split['permutation_p_value_two_sided'], 4)} | "
                f"[{_fmt(split_ci[0])}, {_fmt(split_ci[1])}] |"
            )

    lines.extend(
        [
            "",
            "## Required limitations",
            "",
            *[f"- {limitation}" for limitation in report["limitations"]],
            "",
            "The absence of a detectable signal in this small, fixed cohort and single regime "
            "does not establish that other markets or better point-in-time datasets are unpredictable.",
            "",
        ]
    )
    markdown = "\n".join(lines)
    forbidden = ("proves", "confirms market efficiency")
    if any(term in markdown.lower() for term in forbidden):
        raise ValueError("generated report contains forbidden overclaim wording")
    return markdown


def run(
    results_dir: Path = RESULTS,
    *,
    permutations: int = DEFAULT_PERMUTATIONS,
    bootstraps: int = DEFAULT_BOOTSTRAPS,
    seed: int = DEFAULT_SEED,
    power_simulations: int = DEFAULT_POWER_SIMULATIONS,
) -> tuple[Path, Path]:
    predictions, sources = load_prediction_dumps(results_dir)
    report = build_report(
        predictions,
        sources,
        permutations=permutations,
        bootstraps=bootstraps,
        seed=seed,
        power_simulations=power_simulations,
    )
    json_path = results_dir / "significance_report.json"
    markdown_path = results_dir / "significance_report.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    markdown_path.write_text(render_markdown(report))
    print(f"Wrote {json_path}")
    print(f"Wrote {markdown_path}")
    print(report["headline"]["conclusion"])
    return json_path, markdown_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=RESULTS)
    parser.add_argument("--permutations", type=int, default=DEFAULT_PERMUTATIONS)
    parser.add_argument("--bootstraps", type=int, default=DEFAULT_BOOTSTRAPS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--power-simulations", type=int, default=DEFAULT_POWER_SIMULATIONS
    )
    args = parser.parse_args()
    run(
        args.results_dir,
        permutations=args.permutations,
        bootstraps=args.bootstraps,
        seed=args.seed,
        power_simulations=args.power_simulations,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
