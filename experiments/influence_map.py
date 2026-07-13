"""Deterministic leave-one-out IC influence diagnostics from persisted dumps.

R3-INF-01 consumes only the committed walk-forward prediction artifacts.  It
never retrains a model, alters a ranking, or compares raw prediction values
across models: their scales are model-local.  For every model and every
ticker-year it measures how much the model's pooled Spearman IC changes when
that single observation is removed and the year is re-scored on n-1 rows.

The pooled IC is the equal-weighted mean of the within-year Spearman ICs and is
computed with ``experiments.significance.spearman_ic`` exactly, so these numbers
cannot silently diverge from the canonical significance report.  Influence is a
sensitivity diagnostic of an estimate already indistinguishable from the null;
it identifies neither mispriced stocks nor opportunities.
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
OUTPUT_DIR = ROOT / "experiments" / "results_influence"
PREDICTION_YEARS = (2023, 2024, 2025)
PREDICTION_PATHS = tuple(
    RESULTS_DIR / f"predictions_test_{year}.csv" for year in PREDICTION_YEARS
)
JSON_OUTPUT = OUTPUT_DIR / "influence_report.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "influence_report.md"
OBSERVATION_OUTPUT = OUTPUT_DIR / "influence_by_observation.csv"
REQUIRED_COLUMNS = ["ticker", "year", "model", "y_true", "y_pred"]
MIN_ROWS_FOR_IC = 3
TOP_INFLUENTIAL_PER_MODEL = 10
CONCENTRATION_TOP_K = 5
ROUND_DIGITS = 10

CLAIM_SAFETY_SENTENCE = (
    "**Influence values describe the sensitivity of a null-consistent estimate to "
    "single observations; they do not identify mispriced stocks or opportunities.**"
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


def validate_claim_safety_text(text: str) -> None:
    """Reject language that would turn a sensitivity diagnostic into a value claim."""
    unsafe_patterns = {
        "influence_identifies_opportunity": r"\binfluenc\w*\s+(?:identif\w+|reveal\w+|find\w+)\s+(?:mispriced|opportun\w+|undervalued|winners?)",
        "sensitivity_is_signal": r"\b(?:sensitivity|influence)\s+(?:is|was|proves|establishes)\s+(?:a\s+)?(?:signal|edge|alpha)\b",
        "reliable_edge": r"\breliable predictive edge\s+(?:is|was)\s+(?:shown|established|found)\b",
        "recommendation": r"\b(?:buy|sell|hold)\s+recommendation\b",
        "market_beating": r"\b(?:market[- ]beating|outperform(?:s|ed)\s+the\s+market)\b",
        "profitable_trading": r"\bprofitable\s+trading\b",
        "mispriced_stock": r"\b(?:mispriced|undervalued|overvalued)\s+(?:stock|ticker|name)s?\s+(?:identified|found|flagged)\b",
    }
    violations = [
        name
        for name, pattern in unsafe_patterns.items()
        if re.search(pattern, text, flags=re.IGNORECASE)
    ]
    if violations:
        raise ValueError(f"Unsafe influence claim(s): {', '.join(violations)}")


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


def build_model_influence(
    model_predictions: pd.DataFrame, model: str, years: list[int]
) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Leave-one-out ΔIC for every ticker-year observation of one model.

    ``delta_pooled_ic = loo_pooled_ic - full_pooled_ic``: a positive value means
    removing the observation raises the pooled IC (it was pulling the estimate
    down); a negative value means removal lowers it.  Row-level (ticker-year),
    year-level (per-year IC), and model-level (concentration) quantities are kept
    strictly separate.
    """
    per_year_usable: dict[int, pd.DataFrame] = {}
    per_year_full_ic: dict[int, float | None] = {}
    for year in years:
        year_rows = model_predictions.loc[model_predictions["year"] == year]
        usable = year_rows.dropna(subset=["y_true", "y_pred"])
        per_year_usable[year] = usable
        per_year_full_ic[year] = _year_ic(usable)

    full_pooled = _pooled_ic([per_year_full_ic[year] for year in years])

    observation_rows: list[dict[str, object]] = []
    for year in years:
        year_rows = model_predictions.loc[model_predictions["year"] == year]
        usable = per_year_usable[year]
        usable_tickers = set(usable["ticker"].tolist())
        for ticker in sorted(year_rows["ticker"].unique().tolist()):
            base = {
                "model": model,
                "ticker": ticker,
                "year": int(year),
                "full_pooled_ic": _rounded(full_pooled),
                "year_full_ic": _rounded(per_year_full_ic[year]),
            }
            if full_pooled is None:
                base.update(
                    {
                        "year_loo_ic": None,
                        "loo_pooled_ic": None,
                        "delta_pooled_ic": None,
                        "abs_delta_pooled_ic": None,
                        "sign": None,
                        "status": "insufficient_data_model_pooled_ic_undefined",
                    }
                )
                observation_rows.append(base)
                continue
            if ticker not in usable_tickers:
                # A missing/non-finite observation was never part of the IC; its
                # removal cannot change anything. Missing stays explicitly null.
                base.update(
                    {
                        "year_loo_ic": None,
                        "loo_pooled_ic": None,
                        "delta_pooled_ic": None,
                        "abs_delta_pooled_ic": None,
                        "sign": None,
                        "status": "insufficient_data_missing_or_nonfinite_value",
                    }
                )
                observation_rows.append(base)
                continue

            loo_usable = usable.loc[usable["ticker"] != ticker]
            year_loo_ic = _year_ic(loo_usable)
            if year_loo_ic is None:
                base.update(
                    {
                        "year_loo_ic": None,
                        "loo_pooled_ic": None,
                        "delta_pooled_ic": None,
                        "abs_delta_pooled_ic": None,
                        "sign": None,
                        "status": "insufficient_data_fewer_than_3_rows_after_removal",
                    }
                )
                observation_rows.append(base)
                continue

            loo_pooled = _pooled_ic(
                [
                    year_loo_ic if other == year else per_year_full_ic[other]
                    for other in years
                ]
            )
            delta = float(loo_pooled) - float(full_pooled)
            base.update(
                {
                    "year_loo_ic": _rounded(year_loo_ic),
                    "loo_pooled_ic": _rounded(loo_pooled),
                    "delta_pooled_ic": _rounded(delta),
                    "abs_delta_pooled_ic": _rounded(abs(delta)),
                    "sign": "positive" if delta > 0 else "negative" if delta < 0 else "zero",
                    "status": "complete",
                }
            )
            observation_rows.append(base)

    complete = [row for row in observation_rows if row["status"] == "complete"]
    abs_deltas = sorted(
        (float(row["abs_delta_pooled_ic"]) for row in complete), reverse=True
    )
    total_abs = float(sum(abs_deltas))
    top_k_abs = float(sum(abs_deltas[:CONCENTRATION_TOP_K]))
    concentration = _rounded(top_k_abs / total_abs) if total_abs > 0 else None

    ranked = sorted(
        complete,
        key=lambda row: (
            -float(row["abs_delta_pooled_ic"]),
            row["year"],
            row["ticker"],
        ),
    )
    top_influential = [
        {
            "ticker": row["ticker"],
            "year": row["year"],
            "delta_pooled_ic": row["delta_pooled_ic"],
            "abs_delta_pooled_ic": row["abs_delta_pooled_ic"],
            "sign": row["sign"],
            "loo_pooled_ic": row["loo_pooled_ic"],
        }
        for row in ranked[:TOP_INFLUENTIAL_PER_MODEL]
    ]

    if full_pooled is None:
        model_status = "insufficient_data_model_pooled_ic_undefined"
    elif all(row["status"] == "complete" for row in observation_rows):
        model_status = "complete"
    else:
        model_status = "partial_with_explicit_insufficient_data"

    summary = {
        "model": model,
        "kind": "ml" if model in ML_MODELS else "baseline",
        "full_pooled_ic": _rounded(full_pooled),
        "per_year_full_ic": {
            str(year): _rounded(per_year_full_ic[year]) for year in years
        },
        "observation_count": len(observation_rows),
        "complete_observation_count": len(complete),
        "influence_concentration_top5_abs_share": concentration,
        "top_influential_observations": top_influential,
        "status": model_status,
    }
    return summary, observation_rows


def build_report(
    predictions: pd.DataFrame, sources: list[dict[str, object]]
) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Build the isolated influence artifacts from persisted predictions only."""
    if predictions.empty:
        raise ValueError("Prediction dump set is empty")
    models = sorted(predictions["model"].unique().tolist())
    years = sorted(int(year) for year in predictions["year"].unique().tolist())

    per_model_summary: list[dict[str, object]] = []
    observation_rows: list[dict[str, object]] = []
    for model in models:
        summary, rows = build_model_influence(
            predictions.loc[predictions["model"] == model], model, years
        )
        per_model_summary.append(summary)
        observation_rows.extend(rows)

    observation_rows.sort(key=lambda row: (row["model"], row["year"], row["ticker"]))

    analysis_status = (
        "complete"
        if all(row["status"] == "complete" for row in observation_rows)
        else "partial_with_explicit_insufficient_data"
    )
    report = {
        "schema_version": "1.0.0",
        "task": "R3-INF-01",
        "analysis_status": analysis_status,
        "generated_by": {
            "module": "experiments/influence_map.py",
            "generator_command": "make research-influence",
            "sampling": "none; seedless leave-one-out arithmetic",
            "deterministic_ordering": "model, year, ticker; top-influential ranked by descending |Δ| with (year, ticker) tie-break",
            "serialization": "sorted-key JSON, newline-terminated UTF-8 JSON/Markdown/CSV",
            "pooled_ic_source": "experiments.significance.spearman_ic (reused verbatim)",
        },
        "source_artifacts": sources,
        "design": {
            "analysis_type": "per-observation leave-one-out sensitivity of the pooled within-year Spearman IC",
            "universe": "81-ticker retrospective training universe; 80 evaluated rows per model-year in the current dumps",
            "target_years": years,
            "models": models,
            "model_count": len(models),
            "pooled_ic_definition": "equal-weighted mean of the within-year Spearman ICs (identical to experiments/significance.py analyze_model)",
            "leave_one_out_definition": "remove one ticker-year observation, re-score that year's Spearman on the remaining usable rows, re-pool across years",
            "delta_sign_convention": "delta_pooled_ic = loo_pooled_ic - full_pooled_ic; positive means removal raises pooled IC, negative means removal lowers it",
            "influence_concentration": "share of total |Δ| held by the top 5 most influential complete observations per model",
            "raw_prediction_magnitudes_compared_across_models": False,
            "missing_prediction_handling": "No values are filled. Observations with a non-finite y_true or y_pred, or years/models whose IC is undefined, yield explicit null Δ with an insufficient-data status.",
            "significance_test_added": False,
            "core_model_or_ranking_changed": False,
        },
        "claim_safety_sentence": CLAIM_SAFETY_SENTENCE,
        "per_model_summary": per_model_summary,
        "influence_by_observation": observation_rows,
        "artifacts": {
            "json_report": "experiments/results_influence/influence_report.json",
            "markdown_report": "experiments/results_influence/influence_report.md",
            "observation_csv": "experiments/results_influence/influence_by_observation.csv",
        },
        "findings": [
            "Δ values are a sensitivity diagnostic of an estimate already indistinguishable from the within-year null; they do not test predictive performance.",
            "Both signs are reported: some single observations prop the pooled IC up and others pull it down, and neither direction is evidence about a ticker.",
            "Raw prediction magnitudes are never compared across models because their scales differ by model; only within-year ranks enter the Spearman IC.",
            "Any absent or insufficient observation, year, or model is retained as an explicit null with a status rather than filled or inferred.",
        ],
        "claim_safety": {
            "describes_estimate_sensitivity_only": True,
            "identifies_mispriced_stocks": False,
            "identifies_opportunities": False,
            "predictive_validity_established": False,
            "reliable_predictive_edge_established": False,
            "investment_value_established": False,
            "recommendations_emitted": False,
            "existing_significance_or_power_results_changed": False,
            "existing_real_terms_regime_or_friction_interpretation_changed": False,
        },
        "limitations": [
            "This is the retrospective 81-ticker training universe with 80 evaluated rows per model-year, not verified point-in-time BIST100 membership; survivorship and universe-selection risks remain.",
            "Only three target years are represented, all within one unusual nominal-TRY macro regime; influence rankings do not establish regime robustness.",
            "High single-observation influence describes estimator fragility under a tiny sample, not opportunity, economic value, trading profitability, or predictive validity.",
            "Influence is a retrospective, in-sample sensitivity diagnostic; it is not a causal, forward-looking, or out-of-sample statement about any ticker.",
            "The analysis adds no significance test and does not change the existing multiplicity correction, low-power limits, or null-consistent conclusion.",
            "The pooled IC and its inputs remain point estimates from three test years; a large |Δ| does not make the underlying pooled IC distinguishable from the null.",
            "This report uses nominal-TRY persisted dumps only and does not replace or merge the parallel real-TRY or USD-basis evidence.",
            "Reproduction is numerical-environment-qualified; deterministic byte identity is demonstrated only in the current environment.",
            "Research support only; not investment advice.",
        ],
    }
    return report, observation_rows


def render_markdown(report: dict[str, object]) -> str:
    """Render a concise, deterministic report without raw prediction magnitudes."""
    lines = [
        "# Leave-one-out IC influence diagnostics",
        "",
        "## Scope and estimand",
        "",
        "This R3-INF-01 artifact measures, for every model and every ticker-year "
        "observation in the persisted walk-forward dumps, the change in that "
        "model's pooled within-year Spearman IC when the single observation is "
        "removed and its year is re-scored on the remaining usable rows "
        "(`delta_pooled_ic = loo_pooled_ic - full_pooled_ic`). The pooled IC is the "
        "equal-weighted mean of the three within-year Spearman ICs, reused verbatim "
        "from `experiments/significance.py`. It does not retrain models, change any "
        "ranking, or compare raw prediction magnitudes across models.",
        "",
        str(report["claim_safety_sentence"]),
        "",
        "## Provenance and regeneration",
        "",
        "Generator: `experiments/influence_map.py` via `make research-influence`. "
        "Seedless leave-one-out arithmetic; no sampling.",
        "",
        "| Source artifact | SHA-256 | Rows |",
        "|---|---|---:|",
    ]
    for source in report["source_artifacts"]:
        lines.append(f"| {source['path']} | `{source['sha256']}` | {source['rows']} |")
    lines.extend(
        [
            "",
            "The machine-readable report and `influence_by_observation.csv` contain the "
            "complete per-observation Δ records with explicit insufficient-data statuses.",
            "",
            "## Per-model influence summary",
            "",
            "| Model | Kind | Full pooled IC | Complete obs | Top-5 \\|Δ\\| share | Most influential (ticker-year, Δ) | Status |",
            "|---|---|---:|---:|---:|---|---|",
        ]
    )
    for summary in report["per_model_summary"]:
        top = summary["top_influential_observations"]
        if top:
            lead = f"{top[0]['ticker']} {top[0]['year']}, {top[0]['delta_pooled_ic']}"
        else:
            lead = "none (insufficient data)"
        lines.append(
            f"| {summary['model']} | {summary['kind']} | {summary['full_pooled_ic']} | "
            f"{summary['complete_observation_count']} | "
            f"{summary['influence_concentration_top5_abs_share']} | {lead} | "
            f"{summary['status']} |"
        )
    lines.extend(["", "## Interpretation boundaries", ""])
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


def write_observation_csv(path: Path, rows: list[dict[str, object]]) -> None:
    """Serialize the complete per-observation influence table deterministically."""
    fieldnames = [
        "model",
        "ticker",
        "year",
        "full_pooled_ic",
        "year_full_ic",
        "year_loo_ic",
        "loo_pooled_ic",
        "delta_pooled_ic",
        "abs_delta_pooled_ic",
        "sign",
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
) -> tuple[Path, Path, Path]:
    """Generate the isolated influence artifacts from immutable dump inputs."""
    prediction_paths = tuple(Path(path) for path in prediction_paths)
    predictions, sources = load_prediction_dumps(prediction_paths)
    report, observation_rows = build_report(predictions, sources)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / JSON_OUTPUT.name
    markdown_path = output_dir / MARKDOWN_OUTPUT.name
    observation_path = output_dir / OBSERVATION_OUTPUT.name
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    write_observation_csv(observation_path, observation_rows)
    print(
        f"[influence] years={len(report['design']['target_years'])} "
        f"models={report['design']['model_count']} "
        f"observations={len(observation_rows)} status={report['analysis_status']} -> {output_dir}"
    )
    return json_path, markdown_path, observation_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    run(args.output_dir)


if __name__ == "__main__":
    main()
