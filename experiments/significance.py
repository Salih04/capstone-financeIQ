"""Permutation tests and bootstrap intervals from persisted prediction dumps.

This module never trains a model. It consumes predictions_<split>.csv artifacts
written by run_experiments.py and preserves the year structure in every resample.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

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
        "schema_version": 1,
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
) -> tuple[Path, Path]:
    predictions, sources = load_prediction_dumps(results_dir)
    report = build_report(
        predictions,
        sources,
        permutations=permutations,
        bootstraps=bootstraps,
        seed=seed,
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
    args = parser.parse_args()
    run(
        args.results_dir,
        permutations=args.permutations,
        bootstraps=args.bootstraps,
        seed=args.seed,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
