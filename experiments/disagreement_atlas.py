"""Deterministic model-rank disagreement atlas from persisted prediction dumps.

R3-STAT-02 consumes the committed walk-forward prediction artifacts only.  It
does not retrain models, alter any ranking, or compare raw prediction values
across models: their scales are model-local.  It describes cross-model rank
agreement as an instability diagnostic, not as evidence of predictive value.
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


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "experiments" / "results"
OUTPUT_DIR = ROOT / "experiments" / "results_disagreement"
PREDICTION_YEARS = (2023, 2024, 2025)
PREDICTION_PATHS = tuple(
    RESULTS_DIR / f"predictions_test_{year}.csv" for year in PREDICTION_YEARS
)
JSON_OUTPUT = OUTPUT_DIR / "disagreement_report.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "disagreement_report.md"
MATRIX_OUTPUT = OUTPUT_DIR / "disagreement_matrix.csv"
REQUIRED_COLUMNS = ["ticker", "year", "model", "y_true", "y_pred"]
CLAIM_SAFETY_SENTENCE = (
    "**Model disagreement measures instability of a signal already indistinguishable "
    "from the null; high agreement between models is not evidence of predictive validity.**"
)


def _sha256(path: Path) -> str:
    """Return the SHA-256 checksum of one source artifact."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rounded(value: float | int | None, digits: int = 10) -> float | None:
    if value is None or not math.isfinite(float(value)):
        return None
    return round(float(value), digits)


def validate_claim_safety_text(text: str) -> None:
    """Reject language that would turn a descriptive atlas into a value claim."""
    unsafe_patterns = {
        "agreement_validates_prediction": r"\b(?:agreement|consensus)\s+(?:validates|proves|establishes)\s+(?:predictive|prediction)",
        "signal_is_real": r"\b(?:signal|model)\s+(?:is|was)\s+real\b",
        "reliable_edge": r"\breliable predictive edge\s+(?:is|was)\s+(?:shown|established|found)\b",
        "recommendation": r"\b(?:buy|sell|hold)\s+recommendation\b",
        "market_beating": r"\b(?:market[- ]beating|outperform(?:s|ed)\s+the\s+market)\b",
        "profitable_trading": r"\bprofitable\s+trading\b",
    }
    violations = [
        name
        for name, pattern in unsafe_patterns.items()
        if re.search(pattern, text, flags=re.IGNORECASE)
    ]
    if violations:
        raise ValueError(f"Unsafe disagreement claim(s): {', '.join(violations)}")


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
        frame["y_pred"] = pd.to_numeric(frame["y_pred"], errors="coerce")
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
        .sort_values(["year", "model", "ticker"], kind="mergesort")
        .reset_index(drop=True),
        sources,
    )


def rank_within_model_year(predictions: pd.DataFrame) -> pd.DataFrame:
    """Append average-tie ranks inside each model/year, leaving missing values null."""
    ranked = predictions[["ticker", "year", "model", "y_pred"]].copy()
    ranked["prediction_rank"] = ranked.groupby(
        ["year", "model"], sort=True
    )["y_pred"].rank(method="average", ascending=True)
    return ranked.sort_values(["year", "model", "ticker"], kind="mergesort").reset_index(
        drop=True
    )


def pairwise_rank_correlations(
    ranked: pd.DataFrame, models: list[str], years: list[int]
) -> list[dict[str, object]]:
    """Return a deterministic year/model matrix with nulls for insufficient pairs."""
    rows: list[dict[str, object]] = []
    for year in years:
        year_rows = ranked.loc[ranked["year"] == year]
        for row_model in models:
            left = year_rows.loc[
                year_rows["model"] == row_model, ["ticker", "prediction_rank"]
            ].rename(columns={"prediction_rank": "left_rank"})
            for column_model in models:
                right = year_rows.loc[
                    year_rows["model"] == column_model,
                    ["ticker", "prediction_rank"],
                ].rename(columns={"prediction_rank": "right_rank"})
                common = left.merge(right, on="ticker", how="inner", sort=True).dropna()
                shared = int(len(common))
                if shared < 3:
                    correlation = None
                    status = "insufficient_data_fewer_than_3_shared_ranked_tickers"
                else:
                    correlation_value = common["left_rank"].corr(
                        common["right_rank"], method="pearson"
                    )
                    correlation = _rounded(correlation_value)
                    status = (
                        "complete"
                        if correlation is not None
                        else "insufficient_data_constant_or_nonfinite_rank"
                    )
                rows.append(
                    {
                        "year": int(year),
                        "row_model": row_model,
                        "column_model": column_model,
                        "shared_ranked_ticker_count": shared,
                        "rank_spearman": correlation,
                        "status": status,
                    }
                )
    return rows


def ticker_rank_spreads(
    ranked: pd.DataFrame, models: list[str], years: list[int]
) -> list[dict[str, object]]:
    """Measure each ticker-year's range and IQR across the complete model set."""
    rows: list[dict[str, object]] = []
    expected_model_count = len(models)
    for year in years:
        year_rows = ranked.loc[ranked["year"] == year]
        for ticker in sorted(year_rows["ticker"].unique().tolist()):
            values = (
                year_rows.loc[year_rows["ticker"] == ticker]
                .set_index("model")["prediction_rank"]
                .reindex(models)
            )
            valid = values.dropna().to_numpy(dtype=float)
            valid_count = int(len(valid))
            if expected_model_count >= 2 and valid_count == expected_model_count:
                lower, upper = np.quantile(valid, [0.25, 0.75], method="linear")
                spread = _rounded(float(np.max(valid) - np.min(valid)))
                iqr = _rounded(float(upper - lower))
                status = "complete"
            else:
                spread = None
                iqr = None
                status = "insufficient_data_missing_model_rank"
            rows.append(
                {
                    "ticker": ticker,
                    "year": int(year),
                    "expected_model_count": expected_model_count,
                    "ranked_model_count": valid_count,
                    "rank_spread_max_minus_min": spread,
                    "rank_iqr": iqr,
                    "status": status,
                }
            )
    return rows


def _summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "minimum": None, "median": None, "maximum": None}
    array = np.asarray(values, dtype=float)
    return {
        "count": int(len(array)),
        "minimum": _rounded(float(np.min(array))),
        "median": _rounded(float(np.median(array))),
        "maximum": _rounded(float(np.max(array))),
    }


def build_report(
    predictions: pd.DataFrame, sources: list[dict[str, object]]
) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Build only descriptive rank-agreement artifacts from persisted predictions."""
    if predictions.empty:
        raise ValueError("Prediction dump set is empty")
    models = sorted(predictions["model"].unique().tolist())
    years = sorted(int(year) for year in predictions["year"].unique().tolist())
    ranked = rank_within_model_year(predictions)
    matrix_rows = pairwise_rank_correlations(ranked, models, years)
    spread_rows = ticker_rank_spreads(ranked, models, years)

    per_year: list[dict[str, object]] = []
    for year in years:
        correlations = [
            float(row["rank_spearman"])
            for row in matrix_rows
            if row["year"] == year
            and row["row_model"] != row["column_model"]
            and row["rank_spearman"] is not None
        ]
        complete_spreads = [
            float(row["rank_spread_max_minus_min"])
            for row in spread_rows
            if row["year"] == year and row["rank_spread_max_minus_min"] is not None
        ]
        complete_iqrs = [
            float(row["rank_iqr"])
            for row in spread_rows
            if row["year"] == year and row["rank_iqr"] is not None
        ]
        per_year.append(
            {
                "year": year,
                "pairwise_off_diagonal_rank_spearman": _summary(correlations),
                "ticker_rank_spread_max_minus_min": _summary(complete_spreads),
                "ticker_rank_iqr": _summary(complete_iqrs),
                "pairwise_insufficient_data_cells": sum(
                    row["year"] == year and row["status"] != "complete"
                    for row in matrix_rows
                ),
                "ticker_insufficient_data_rows": sum(
                    row["year"] == year and row["status"] != "complete"
                    for row in spread_rows
                ),
            }
        )

    analysis_status = (
        "complete"
        if all(row["status"] == "complete" for row in matrix_rows + spread_rows)
        else "partial_with_explicit_insufficient_data"
    )
    report = {
        "schema_version": "1.0.0",
        "task": "R3-STAT-02",
        "analysis_status": analysis_status,
        "generated_by": {
            "module": "experiments/disagreement_atlas.py",
            "generator_command": "make research-disagreement",
            "sampling": "none; seedless arithmetic",
            "deterministic_ordering": "year, model, ticker; CSV rows use year, row_model, column_model",
            "serialization": "sorted-key JSON, newline-terminated UTF-8 JSON/Markdown/CSV",
        },
        "source_artifacts": sources,
        "design": {
            "analysis_type": "cross-model within-year prediction-rank disagreement",
            "universe": "81-ticker retrospective training universe; 80 evaluated rows per model-year in the current dumps",
            "target_years": years,
            "models": models,
            "model_count": len(models),
            "rank_definition": "average-tie ascending rank of y_pred within one target year and one model",
            "pairwise_statistic": "Pearson correlation of the two models' within-model ranks (Spearman rank correlation)",
            "ticker_statistic": "max minus min and linear-interpolation IQR across all model ranks for a ticker-year",
            "raw_prediction_magnitudes_compared_across_models": False,
            "missing_prediction_handling": "No values are filled. Pairwise cells with fewer than three shared ranks are null; ticker-year spread/IQR are null unless every model has a rank.",
            "significance_test_added": False,
            "core_model_or_ranking_changed": False,
        },
        "claim_safety_sentence": CLAIM_SAFETY_SENTENCE,
        "per_year_summary": per_year,
        "pairwise_rank_correlation_matrix": matrix_rows,
        "ticker_year_rank_spread": spread_rows,
        "artifacts": {
            "json_report": "experiments/results_disagreement/disagreement_report.json",
            "markdown_report": "experiments/results_disagreement/disagreement_report.md",
            "matrix_csv": "experiments/results_disagreement/disagreement_matrix.csv",
        },
        "findings": [
            "The matrix and spread rows are descriptive rank-agreement diagnostics only; they do not test predictive performance.",
            "Raw prediction magnitudes are never compared across models because their scales differ by model.",
            "Any absent or insufficient rank evidence is retained as an explicit null/status rather than filled or inferred.",
        ],
        "claim_safety": {
            "describes_model_instability_only": True,
            "predictive_validity_established": False,
            "reliable_predictive_edge_established": False,
            "investment_value_established": False,
            "recommendations_emitted": False,
            "existing_significance_or_power_results_changed": False,
            "existing_real_terms_regime_or_friction_interpretation_changed": False,
        },
        "limitations": [
            "This is the retrospective 81-ticker training universe with 80 evaluated rows per model-year, not verified point-in-time BIST100 membership; survivorship and universe-selection risks remain.",
            "Only three target years are represented, all within one unusual macro regime; this atlas does not establish regime robustness.",
            "Rank agreement or disagreement describes model instability, not opportunity, economic value, trading profitability, or predictive validity.",
            "The analysis adds no significance test and does not change the existing multiplicity correction, low-power limits, or null-consistent conclusion.",
            "Raw y_pred scales differ by model and are deliberately never compared across models; ties receive average ranks.",
            "Missing or non-finite predictions are never imputed. Insufficient pairwise or ticker-year evidence is reported as null with an explicit status.",
            "This report uses nominal-TRY persisted dumps only and does not replace or merge the parallel real-TRY or USD-basis evidence.",
            "Reproduction is numerical-environment-qualified; deterministic byte identity is demonstrated only in the current environment.",
            "Research support only; not investment advice.",
        ],
    }
    return report, matrix_rows


def render_markdown(report: dict[str, object]) -> str:
    """Render a concise, deterministic report without raw prediction magnitudes."""
    design = report["design"]
    lines = [
        "# Model disagreement atlas",
        "",
        "## Scope and estimand",
        "",
        "This R3-STAT-02 artifact compares each model's within-year, within-model "
        "prediction ranks. For every target year it reports the 9×9 pairwise Spearman "
        "matrix; for every ticker-year it reports the max−min rank spread and IQR across "
        "the nine model ranks. It does not compare raw prediction magnitudes across models.",
        "",
        str(report["claim_safety_sentence"]),
        "",
        "## Provenance and regeneration",
        "",
        "Generator: `experiments/disagreement_atlas.py` via `make research-disagreement`.",
        "",
        "| Source artifact | SHA-256 | Rows |",
        "|---|---|---:|",
    ]
    for source in report["source_artifacts"]:
        lines.append(f"| {source['path']} | `{source['sha256']}` | {source['rows']} |")
    lines.extend(
        [
            "",
            "The machine-readable report contains the complete ticker-year spread records. "
            "`disagreement_matrix.csv` contains the complete, deterministic pairwise matrix "
            "with explicit insufficient-data statuses.",
            "",
            "## Descriptive summaries",
            "",
            "| Target year | Off-diagonal Spearman median | Rank-spread median | Rank-IQR median | Pairwise insufficient cells | Ticker insufficient rows |",
            "|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in report["per_year_summary"]:
        lines.append(
            f"| {row['year']} | {row['pairwise_off_diagonal_rank_spearman']['median']} | "
            f"{row['ticker_rank_spread_max_minus_min']['median']} | "
            f"{row['ticker_rank_iqr']['median']} | {row['pairwise_insufficient_data_cells']} | "
            f"{row['ticker_insufficient_data_rows']} |"
        )
    lines.extend(["", "## Interpretation boundaries", ""])
    lines.extend(f"- {item}" for item in report["findings"])
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.extend(["", "The conclusion remains: no reliable predictive edge. Research support only; not investment advice.", ""])
    text = "\n".join(lines)
    validate_claim_safety_text(text)
    return text


def write_matrix_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "year",
        "row_model",
        "column_model",
        "shared_ranked_ticker_count",
        "rank_spearman",
        "status",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(
    output_dir: Path = OUTPUT_DIR,
    *,
    prediction_paths: Iterable[Path] = PREDICTION_PATHS,
) -> tuple[Path, Path, Path]:
    """Generate the isolated disagreement artifacts from immutable dump inputs."""
    prediction_paths = tuple(Path(path) for path in prediction_paths)
    predictions, sources = load_prediction_dumps(prediction_paths)
    report, matrix_rows = build_report(predictions, sources)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / JSON_OUTPUT.name
    markdown_path = output_dir / MARKDOWN_OUTPUT.name
    matrix_path = output_dir / MATRIX_OUTPUT.name
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    write_matrix_csv(matrix_path, matrix_rows)
    print(
        f"[disagreement] years={len(report['design']['target_years'])} "
        f"models={report['design']['model_count']} status={report['analysis_status']} -> {output_dir}"
    )
    return json_path, markdown_path, matrix_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    run(args.output_dir)


if __name__ == "__main__":
    main()
