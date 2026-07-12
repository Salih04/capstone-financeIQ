"""Deterministic audit of the user-facing hybrid confidence component.

R2-CAL-01 evaluates the 0.20 ``confidence_score`` component used by
``research_agent.generate_company_insight`` against realized rank error in the
persisted walk-forward prediction dumps.  It does not tune or modify either
scoring service.

Important distinctions:

* ``y_pred`` is model-native score magnitude and is never pooled across models.
* predicted and realized ranks are computed within target year and model.
* uncertainty is the observed distribution of absolute rank error.
* calibration asks whether higher replayed confidence accompanies lower error.
* feature coverage is measured separately and is not substituted for confidence.
* realized ``y_true`` is an evaluation outcome, never a scoring input.

The audited hybrid confidence is a dataset-state diagnostic.  The forecasting
service's per-row selected-feature coverage is a different quantity and is not
silently substituted here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "experiments" / "results"
PREDICTION_PATHS = tuple(
    RESULTS_DIR / f"predictions_test_{year}.csv" for year in (2023, 2024, 2025)
)
TRAINING_DATASET = ROOT / "data" / "trusted_clean" / "modeling_dataset_training_2020_2025.csv"
QUALITY_REPORT = ROOT / "data" / "trusted_clean" / "data_quality_report.json"
CONTRACT_PATH = ROOT / "model_confidence_contract.json"
JSON_OUTPUT = RESULTS_DIR / "calibration_report.json"
MARKDOWN_OUTPUT = RESULTS_DIR / "calibration_report.md"
PLOT_OUTPUT = RESULTS_DIR / "calibration_plot.csv"
RANDOM_SEED = 42
BOOTSTRAP_SAMPLES = 2_000
REQUIRED_PREDICTION_COLUMNS = {"ticker", "year", "model", "y_true", "y_pred"}
CLAIM_SAFETY_TEXT = (
    "Diagnostic only: confidence is not a probability of return, profit, or success; "
    "it is not recommendation strength and does not establish validated predictive reliability."
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_output(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def load_prediction_dumps(paths: Iterable[Path] = PREDICTION_PATHS) -> pd.DataFrame:
    """Load and strictly validate persisted predictions; never fill missing values."""
    frames: list[pd.DataFrame] = []
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"Persisted prediction dump missing: {path}")
        frame = pd.read_csv(path)
        missing_columns = REQUIRED_PREDICTION_COLUMNS - set(frame.columns)
        if missing_columns:
            raise ValueError(f"{path} missing required columns: {sorted(missing_columns)}")
        if frame[list(REQUIRED_PREDICTION_COLUMNS)].isna().any().any():
            raise ValueError(f"{path} contains missing required prediction values; refusing to impute")
        if frame.duplicated(["ticker", "year", "model"]).any():
            raise ValueError(f"{path} contains duplicate ticker/year/model rows")
        frame = frame[list(sorted(REQUIRED_PREDICTION_COLUMNS))].copy()
        frame["source_file"] = str(path.relative_to(ROOT))
        frames.append(frame)

    predictions = pd.concat(frames, ignore_index=True)
    predictions["ticker"] = predictions["ticker"].astype(str).str.strip().str.upper()
    predictions["year"] = pd.to_numeric(predictions["year"], errors="raise").astype(int)
    predictions["y_true"] = pd.to_numeric(predictions["y_true"], errors="raise")
    predictions["y_pred"] = pd.to_numeric(predictions["y_pred"], errors="raise")
    return predictions.sort_values(["year", "model", "ticker"], kind="mergesort").reset_index(drop=True)


def attach_rank_errors(predictions: pd.DataFrame, confidence_score: float) -> pd.DataFrame:
    """Compute within-year/model ranks, retaining raw magnitudes only as diagnostics."""
    out = predictions.copy()
    group = out.groupby(["year", "model"], sort=True)
    out["predicted_rank"] = group["y_pred"].rank(method="average", ascending=False)
    out["realized_rank"] = group["y_true"].rank(method="average", ascending=False)
    out["rank_error"] = (out["predicted_rank"] - out["realized_rank"]).abs()
    out["hybrid_confidence"] = float(confidence_score)
    out["feature_year"] = out["year"] - 1
    return out


def compute_feature_coverage(
    dataset_path: Path = TRAINING_DATASET,
    quality_path: Path = QUALITY_REPORT,
) -> pd.DataFrame:
    """Measure observed feature completeness; missing cells stay missing.

    This is deliberately separate from the audited hybrid confidence.  A row
    absent from the modeling dataset has unknown coverage (null), not zero or an
    imputed average.
    """
    if not dataset_path.is_file():
        raise FileNotFoundError(f"Training dataset missing: {dataset_path}")
    if not quality_path.is_file():
        raise FileNotFoundError(f"Data-quality report missing: {quality_path}")
    quality = json.loads(quality_path.read_text(encoding="utf-8"))
    features = quality.get("feature_columns")
    if not isinstance(features, list) or not features:
        raise ValueError("Data-quality report has no feature_columns; refusing to infer coverage inputs")
    frame = pd.read_csv(dataset_path)
    missing_columns = set(features) - set(frame.columns)
    if missing_columns:
        raise ValueError(f"Training dataset missing declared feature columns: {sorted(missing_columns)}")
    coverage = frame[["ticker", "year", *features]].copy()
    coverage["ticker"] = coverage["ticker"].astype(str).str.strip().str.upper()
    coverage["feature_coverage"] = coverage[features].notna().mean(axis=1)
    return coverage[["ticker", "year", "feature_coverage"]].rename(columns={"year": "feature_year"})


def join_feature_coverage(rows: pd.DataFrame, coverage: pd.DataFrame) -> pd.DataFrame:
    out = rows.merge(coverage, on=["ticker", "feature_year"], how="left", validate="many_to_one")
    out["coverage_status"] = np.where(out["feature_coverage"].isna(), "missing_input_row", "observed")
    return out


def replay_hybrid_confidence(state: dict[str, Any] | None = None) -> dict[str, Any]:
    """Call the production research-agent confidence function without modifying it."""
    backend = str(ROOT / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    from app.services import research_agent  # noqa: PLC0415

    replay_state = state if state is not None else research_agent.load_research_state()
    result = research_agent.confidence_score(replay_state)
    return {
        **result,
        "quantity": "research_agent_hybrid_confidence",
        "scope": "dataset_artifact_state_not_per_ticker",
        "service_function": "backend/app/services/research_agent.py::confidence_score",
        "consumer_function": "backend/app/services/research_agent.py::generate_company_insight",
        "hybrid_weight": 0.20,
    }


def _safe_spearman(x: pd.Series, y: pd.Series) -> float | None:
    if x.nunique(dropna=True) < 2 or y.nunique(dropna=True) < 2:
        return None
    value = x.corr(y, method="spearman")
    return None if pd.isna(value) else round(float(value), 6)


def monotonicity_check(
    rows: pd.DataFrame,
    seed: int = RANDOM_SEED,
    bootstrap_samples: int = BOOTSTRAP_SAMPLES,
) -> dict[str, Any]:
    """Seeded association check: higher confidence should mean lower rank error."""
    observed = _safe_spearman(rows["hybrid_confidence"], -rows["rank_error"])
    if observed is None:
        return {
            "status": "not_estimable",
            "higher_confidence_lower_error_spearman": None,
            "bootstrap_95pct": None,
            "seed": seed,
            "bootstrap_samples_requested": bootstrap_samples,
            "bootstrap_samples_usable": 0,
            "reason": "Replayed hybrid confidence has fewer than two distinct values.",
        }

    rng = np.random.default_rng(seed)
    values: list[float] = []
    n_rows = len(rows)
    for _ in range(bootstrap_samples):
        sample = rows.iloc[rng.integers(0, n_rows, n_rows)]
        value = _safe_spearman(sample["hybrid_confidence"], -sample["rank_error"])
        if value is not None:
            values.append(value)
    interval = None
    if values:
        interval = [round(float(v), 6) for v in np.quantile(values, [0.025, 0.975])]
    return {
        "status": "estimated" if interval is not None else "not_estimable",
        "higher_confidence_lower_error_spearman": observed,
        "bootstrap_95pct": interval,
        "seed": seed,
        "bootstrap_samples_requested": bootstrap_samples,
        "bootstrap_samples_usable": len(values),
    }


def calibration_bins(rows: pd.DataFrame) -> pd.DataFrame:
    """Create up to ten confidence bins without splitting tied confidence values."""
    out = rows.copy()
    distinct = int(out["hybrid_confidence"].nunique(dropna=True))
    if distinct < 1:
        raise ValueError("No replayed confidence values available")
    if distinct == 1:
        out["confidence_bin"] = 1
    else:
        out["confidence_bin"] = (
            pd.qcut(out["hybrid_confidence"], q=min(10, distinct), labels=False, duplicates="drop") + 1
        ).astype(int)

    bins = (
        out.groupby("confidence_bin", sort=True)
        .agg(
            confidence_min=("hybrid_confidence", "min"),
            confidence_max=("hybrid_confidence", "max"),
            mean_confidence=("hybrid_confidence", "mean"),
            n_model_rows=("rank_error", "size"),
            n_ticker_years=("ticker", lambda s: int(out.loc[s.index, ["ticker", "year"]].drop_duplicates().shape[0])),
            mean_rank_error=("rank_error", "mean"),
            median_rank_error=("rank_error", "median"),
            mean_feature_coverage=("feature_coverage", "mean"),
        )
        .reset_index()
    )
    bins.insert(0, "calibration_status", "not_estimable" if distinct == 1 else "estimated")
    for column in (
        "confidence_min", "confidence_max", "mean_confidence", "mean_rank_error",
        "median_rank_error", "mean_feature_coverage",
    ):
        bins[column] = bins[column].round(6)
    return bins


def validate_claim_safety_text(text: str) -> None:
    """Reject affirmative probability, recommendation, or reliability claims."""
    forbidden = {
        "confidence_as_probability": r"\bconfidence\s+(?:is|means|represents)\s+(?:a\s+)?probability\b",
        "numeric_profit_probability": r"\bprobability of (?:profit|success|return)\s*[:=]\s*\d",
        "recommendation_strength": r"\brecommendation strength\s*[:=]\s*(?:high|medium|low|\d)",
        "calibrated_confidence_claim": r"\bcalibrated confidence\b",
        "validated_reliability_claim": r"\b(?:shows|establishes|demonstrates) validated predictive reliability\b",
    }
    violations = [name for name, pattern in forbidden.items() if re.search(pattern, text, flags=re.IGNORECASE)]
    if violations:
        raise ValueError(f"Unsafe calibration claim(s): {', '.join(violations)}")


def _model_summaries(rows: pd.DataFrame) -> list[dict[str, Any]]:
    summaries = []
    for model, group in rows.groupby("model", sort=True):
        summaries.append({
            "model": model,
            "model_rows": int(len(group)),
            "target_years": sorted(int(year) for year in group["year"].unique()),
            "score_magnitude_model_native_min": round(float(group["y_pred"].min()), 6),
            "score_magnitude_model_native_max": round(float(group["y_pred"].max()), 6),
            "mean_absolute_rank_error": round(float(group["rank_error"].mean()), 6),
            "median_absolute_rank_error": round(float(group["rank_error"].median()), 6),
        })
    return summaries


def build_report(
    rows: pd.DataFrame,
    replay: dict[str, Any],
    bins: pd.DataFrame,
    replay_date: str,
    prediction_paths: Iterable[Path] = PREDICTION_PATHS,
) -> dict[str, Any]:
    unique_units = rows[["ticker", "year"]].drop_duplicates()
    monotonicity = monotonicity_check(rows)
    confidence_values = sorted(float(value) for value in rows["hybrid_confidence"].unique())
    not_estimable = monotonicity["status"] != "estimated"
    verdict = (
        "Hybrid confidence is not informative about rank error at this scale: the replayed value "
        "is constant across all evaluated rows, so calibration and monotonicity are not estimable."
        if not_estimable else
        "Hybrid confidence is informative about rank error at this scale under this diagnostic audit."
    )
    coverage = rows[["ticker", "year", "feature_coverage", "coverage_status"]].drop_duplicates()
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    service_paths = (
        ROOT / "backend" / "app" / "services" / "research_agent.py",
        ROOT / "backend" / "app" / "services" / "forecasting_csv_service.py",
    )
    prediction_paths = tuple(prediction_paths)
    report = {
        "schema_version": "1.0.0",
        "task": "R2-CAL-01",
        "replay_provenance": {
            "replay_date": replay_date,
            "git_sha": _git_output("rev-parse", "HEAD"),
            "git_worktree_dirty": bool(_git_output("status", "--porcelain")),
            "random_seed": RANDOM_SEED,
            "code_version": {
                str(path.relative_to(ROOT)): _sha256(path) for path in service_paths
            },
        },
        "inputs": [
            {"path": str(path.relative_to(ROOT)), "sha256": _sha256(path)}
            for path in (*prediction_paths, TRAINING_DATASET, QUALITY_REPORT, CONTRACT_PATH)
        ],
        "confidence_quantity": replay,
        "excluded_confidence_quantity": {
            "name": "forecasting_selected_feature_coverage_confidence",
            "service_function": "backend/app/services/forecasting_csv_service.py::run_forecast",
            "reason": "Separate per-row coverage diagnostic; it is not the hybrid score's 0.20 component.",
        },
        "definitions": {
            "score_magnitude": "Raw y_pred in each model's native scale; never compared or pooled across models.",
            "predicted_rank": "Descending y_pred rank within target year and model; average rank for ties.",
            "realized_outcome": "Persisted y_true nominal TRY T+1 return used only after scoring for evaluation.",
            "realized_rank": "Descending y_true rank within target year and model.",
            "rank_error": "Absolute difference between predicted_rank and realized_rank.",
            "uncertainty": "Observed rank-error distribution and seeded bootstrap association; not a return interval.",
            "calibration": "Whether higher replayed confidence accompanies lower realized rank error.",
            "coverage": "Observed fraction of declared feature columns populated for the feature-year row; not confidence.",
        },
        "sample": {
            "prediction_model_rows": int(len(rows)),
            "independent_ticker_year_outcomes": int(len(unique_units)),
            "models": int(rows["model"].nunique()),
            "target_years": sorted(int(year) for year in rows["year"].unique()),
            "rows_per_model_year": sorted(int(value) for value in rows.groupby(["model", "year"]).size().unique()),
            "universe": "81-ticker training universe; 80 evaluated rows per split; nominal TRY realized returns",
        },
        "coverage_audit": {
            "observed_ticker_years": int((coverage["coverage_status"] == "observed").sum()),
            "missing_input_ticker_years": int((coverage["coverage_status"] == "missing_input_row").sum()),
            "minimum": round(float(coverage["feature_coverage"].min()), 6) if coverage["feature_coverage"].notna().any() else None,
            "median": round(float(coverage["feature_coverage"].median()), 6) if coverage["feature_coverage"].notna().any() else None,
            "maximum": round(float(coverage["feature_coverage"].max()), 6) if coverage["feature_coverage"].notna().any() else None,
            "relationship_to_hybrid_confidence": "Measured separately; missing values are not imputed into either quantity.",
        },
        "calibration": {
            "requested_bins": 10,
            "realized_bins": int(len(bins)),
            "confidence_unique_values": len(confidence_values),
            "confidence_values": confidence_values,
            "status": monotonicity["status"],
            "informative_about_rank_error": False if not_estimable else monotonicity["higher_confidence_lower_error_spearman"] > 0,
            "monotonicity": monotonicity,
            "verdict": verdict,
        },
        "model_summaries": _model_summaries(rows),
        "claim_safety": {
            "contract_version": contract["version"],
            "contract_conclusion": contract["evidence_state"]["conclusion"],
            "confidence_is_probability_of_return_profit_or_success": False,
            "confidence_is_recommendation_strength": False,
            "validated_predictive_reliability_established": False,
            "core_ranking_or_model_computation_changed": False,
            "statement": CLAIM_SAFETY_TEXT,
        },
        "limitations": [
            "The replay describes the current checked-out confidence code applied to persisted historical outcomes; it is not historically persisted confidence.",
            "The hybrid confidence component is dataset-state scoped and constant across tickers, so decile calibration cannot be estimated.",
            "The 2,160 model rows repeat 240 ticker-year realized outcomes across nine models and are not 2,160 independent observations.",
            "Only three test years and one macro regime are observed; no reliable predictive edge is established.",
            "No confidence tuning or recalibration was performed on these rows.",
        ],
    }
    validate_claim_safety_text(json.dumps(report, ensure_ascii=False))
    return report


def render_markdown(report: dict[str, Any], bins: pd.DataFrame) -> str:
    replay = report["confidence_quantity"]
    calibration = report["calibration"]
    sample = report["sample"]
    coverage = report["coverage_audit"]
    models = pd.DataFrame(report["model_summaries"])
    lines = [
        "# Confidence calibration report (R2-CAL-01)",
        "",
        f"**Verdict:** {calibration['verdict']}",
        "",
        CLAIM_SAFETY_TEXT,
        "",
        "## Audited quantity",
        "",
        "The audited value is the hybrid research score's 0.20 `confidence_score` component from "
        "`research_agent.confidence_score`, consumed by `generate_company_insight`. It is a dataset-artifact-state "
        "diagnostic, not a ticker-specific coverage estimate. The separate forecasting-service confidence is selected-feature "
        "coverage and was not substituted for the hybrid component.",
        "",
        f"Replayed value: **{replay['confidence_score']:.3f} ({replay['confidence_level']})** for every evaluated row. "
        f"Reasons: {', '.join(replay['confidence_reasons']) or 'none'}.",
        "",
        "## Design and sample",
        "",
        f"The bench read the three persisted prediction dumps without retraining: {sample['prediction_model_rows']} "
        f"model rows, {sample['independent_ticker_year_outcomes']} distinct ticker-year outcomes, "
        f"{sample['models']} models, target years {', '.join(map(str, sample['target_years']))}. "
        f"Scope: {sample['universe']}.",
        "",
        "For every model and target year, descending model-native `y_pred` becomes predicted rank and descending persisted "
        "`y_true` becomes realized rank. Absolute rank error is their distance. Raw score magnitudes stay model-local because "
        "their scales differ. Realized returns are evaluation outcomes only. Feature coverage is computed separately on the "
        "corresponding feature-year row and is never filled when an input row is absent.",
        "",
        "## Calibration finding",
        "",
        f"Ten bins were requested; **{calibration['realized_bins']}** was realizable because confidence had "
        f"**{calibration['confidence_unique_values']}** distinct value. The higher-confidence/lower-error association and its "
        "seeded bootstrap interval are therefore not estimable. This is evidence about the current confidence semantics, not "
        "evidence that rank errors are small.",
        "",
        f"Coverage remained a separate observed diagnostic across {coverage['observed_ticker_years']} ticker-years "
        f"(min/median/max {coverage['minimum']:.3f}/{coverage['median']:.3f}/{coverage['maximum']:.3f}); "
        f"{coverage['missing_input_ticker_years']} input rows were missing. Coverage variation must not be relabeled as hybrid "
        "confidence after the fact.",
        "",
        "## Plot-ready bin",
        "",
        bins.to_markdown(index=False),
        "",
        "## Model-native score scales and rank error",
        "",
        models.to_markdown(index=False),
        "",
        "## Provenance and limitations",
        "",
        f"Audited as of replay {report['replay_provenance']['replay_date']} at git SHA "
        f"`{report['replay_provenance']['git_sha']}`. The report records service-code and input checksums in the JSON artifact. "
        "Replayed confidence describes that code on past rows; it is not a historically persisted observation.",
        "",
        *[f"- {item}" for item in report["limitations"]],
        "",
        "The conclusion remains: no reliable predictive edge. Research support only; not investment advice.",
        "",
    ]
    text = "\n".join(lines)
    validate_claim_safety_text(text)
    return text


def run(replay_date: str | None = None) -> dict[str, Any]:
    predictions = load_prediction_dumps()
    replay = replay_hybrid_confidence()
    rows = attach_rank_errors(predictions, replay["confidence_score"])
    rows = join_feature_coverage(rows, compute_feature_coverage())
    bins = calibration_bins(rows)
    report = build_report(rows, replay, bins, replay_date or date.today().isoformat())
    markdown = render_markdown(report, bins)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    MARKDOWN_OUTPUT.write_text(markdown, encoding="utf-8")
    bins.to_csv(PLOT_OUTPUT, index=False, lineterminator="\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--replay-date",
        default=None,
        help="ISO date recorded in provenance (default: current local date).",
    )
    args = parser.parse_args()
    report = run(replay_date=args.replay_date)
    print(report["calibration"]["verdict"])
    print(f"Wrote {JSON_OUTPUT.relative_to(ROOT)}, {MARKDOWN_OUTPUT.relative_to(ROOT)}, and {PLOT_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
