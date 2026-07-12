"""Deterministic rank-basket friction sensitivity for persisted predictions.

R2-FRICTION-01 is an inverted backtesting exercise: it uses the already
persisted walk-forward rows to show how gross, occasionally lucky baskets
change under explicit turnover and cost assumptions.  It never retrains a
model, changes a ranking, or treats the output as implementable performance.

Basket membership is determined only by descending ``y_pred`` rank within one
target year and one model.  Raw score magnitudes never cross model boundaries
and are not emitted.  Realized ``y_true`` values are evaluation outcomes only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "experiments" / "results"
PREDICTION_PATHS = tuple(
    RESULTS_DIR / f"predictions_test_{year}.csv" for year in (2023, 2024, 2025)
)
SIGNIFICANCE_REPORT = RESULTS_DIR / "significance_report.json"
REAL_TERMS_REPORT = ROOT / "experiments" / "results_real_terms" / "comparison_report.json"
REGIME_REPORT = ROOT / "experiments" / "results_regime" / "regime_context_report.json"
JSON_OUTPUT = RESULTS_DIR / "friction_report.json"
MARKDOWN_OUTPUT = RESULTS_DIR / "friction_report.md"
PLOT_OUTPUT = RESULTS_DIR / "friction_plot.csv"
REQUIRED_COLUMNS = {"ticker", "year", "model", "y_true", "y_pred"}
TOP_K = 10
UNIVERSE_LABEL = "81-ticker training universe, nominal TRY."
CHART_STAMP = (
    "Hypothetical illustration — not a backtest of a viable strategy; underlying signal "
    "IC ≈ 0 and no model survives significance correction."
)

# Scenario values are assumptions, not measured BIST costs.  The last value is
# intentionally extreme so it functions only as an adverse arithmetic control.
DEFAULT_COST_SCENARIOS = (
    {"scenario_id": "zero_cost_control", "cost_bps": 0.0, "role": "zero-cost arithmetic control"},
    {"scenario_id": "illustrative_25bps_assumption", "cost_bps": 25.0, "role": "illustrative assumption"},
    {"scenario_id": "illustrative_100bps_assumption", "cost_bps": 100.0, "role": "illustrative assumption"},
    {
        "scenario_id": "deliberately_adverse_10000bps_control",
        "cost_bps": 10_000.0,
        "role": "deliberately adverse arithmetic stress control",
    },
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rounded(value: float | int | None, digits: int = 10) -> float | None:
    if value is None or not math.isfinite(float(value)):
        return None
    return round(float(value), digits)


def validate_claim_safety_text(text: str) -> None:
    """Reject positive implementability, investment-value, or inferred-friction claims."""
    unsafe_patterns = {
        "achievable_or_implementable_performance": r"\b(?:achievable|implementable)\s+(?:performance|returns?)\b",
        "investment_value_claim": r"\binvestment value (?:is|was) (?:shown|established|demonstrated)\b",
        "reliable_edge_claim": r"\breliable predictive edge (?:is|was) (?:shown|established|found)\b",
        "historical_membership_claim": r"\bverified historical BIST100 membership\b",
        "measured_market_friction": (
            r"\b(?:bid[- ]ask spread|market impact|liquidity|tradeability)\s*"
            r"(?:is|was|=|of)\s*\d"
        ),
    }
    violations = [
        name for name, pattern in unsafe_patterns.items()
        if re.search(pattern, text, flags=re.IGNORECASE)
    ]
    if violations:
        raise ValueError(f"Unsafe friction claim(s): {', '.join(violations)}")


def load_prediction_dumps(paths: Iterable[Path] = PREDICTION_PATHS) -> pd.DataFrame:
    """Load persisted rows while preserving missing predictions/outcomes as missing."""
    frames: list[pd.DataFrame] = []
    for source in paths:
        source = Path(source)
        if not source.is_file():
            raise FileNotFoundError(f"Persisted prediction dump missing: {source}")
        frame = pd.read_csv(source)
        missing = REQUIRED_COLUMNS - set(frame.columns)
        if missing:
            raise ValueError(f"{source} missing required columns: {sorted(missing)}")
        frame = frame[["ticker", "year", "model", "y_true", "y_pred"]].copy()
        frame["source_file"] = (
            source.relative_to(ROOT).as_posix() if source.is_relative_to(ROOT) else str(source)
        )
        frames.append(frame)

    rows = pd.concat(frames, ignore_index=True)
    if rows["year"].isna().any() or rows["model"].isna().any():
        raise ValueError("Prediction rows require non-missing year and model identifiers")
    rows["ticker"] = rows["ticker"].fillna("").astype(str).str.strip().str.upper()
    rows["model"] = rows["model"].astype(str).str.strip()
    if rows["model"].eq("").any():
        raise ValueError("Prediction rows require non-blank model identifiers")
    rows["year"] = pd.to_numeric(rows["year"], errors="raise").astype(int)
    rows["y_true"] = pd.to_numeric(rows["y_true"], errors="coerce")
    rows["y_pred"] = pd.to_numeric(rows["y_pred"], errors="coerce")
    if rows.duplicated(["ticker", "year", "model"]).any():
        raise ValueError("Prediction dumps contain duplicate ticker/year/model rows")
    return rows.sort_values(["model", "year", "ticker"], kind="mergesort").reset_index(drop=True)


def form_top_k_basket(group: pd.DataFrame, top_k: int = TOP_K) -> dict[str, object]:
    """Form one equal-weight basket from descending within-group prediction rank."""
    if top_k < 1:
        raise ValueError("top_k must be positive")
    years = group["year"].dropna().unique()
    models = group["model"].dropna().unique()
    if len(years) != 1 or len(models) != 1:
        raise ValueError("Basket input must contain exactly one target year and one model")

    finite_prediction = np.isfinite(group["y_pred"].astype(float))
    eligible = group.loc[group["ticker"].ne("") & finite_prediction].copy()
    excluded_missing_prediction = int(len(group) - len(eligible))
    if len(eligible) < top_k:
        raise ValueError(
            f"Not enough finite within-model predictions for top-{top_k}: {len(eligible)} eligible"
        )

    # Magnitudes establish order only inside this model/year.  The ticker key is
    # a deterministic tie-break; no magnitude is emitted into the report.
    selected = eligible.sort_values(
        ["y_pred", "ticker"], ascending=[False, True], kind="mergesort"
    ).head(top_k)
    realized = selected["y_true"].astype(float)
    missing_realized = int((~np.isfinite(realized)).sum())
    gross_return = None if missing_realized else _rounded(float(realized.mean()))
    tickers = selected["ticker"].tolist()
    return {
        "model": str(models[0]),
        "year": int(years[0]),
        "basket_size": top_k,
        "selected_tickers_ranked": tickers,
        "gross_basket_mean_return_pct": gross_return,
        "excluded_missing_prediction_rows": excluded_missing_prediction,
        "selected_missing_realized_rows": missing_realized,
        "ranking_rule": "descending y_pred rank within target year and model; ticker ascending breaks ties",
    }


def basket_turnover(previous: Sequence[str], current: Sequence[str]) -> float:
    """Return half-L1 turnover between two equal-weight baskets."""
    if not previous or not current:
        raise ValueError("Turnover requires two non-empty baskets")
    if len(set(previous)) != len(previous) or len(set(current)) != len(current):
        raise ValueError("Basket tickers must be unique")
    previous_weight = 1.0 / len(previous)
    current_weight = 1.0 / len(current)
    names = set(previous) | set(current)
    turnover = 0.5 * sum(
        abs(
            (current_weight if ticker in current else 0.0)
            - (previous_weight if ticker in previous else 0.0)
        )
        for ticker in names
    )
    return _rounded(turnover)


def apply_cost(
    gross_return_pct: float | None,
    turnover: float | None,
    cost_bps: float,
) -> tuple[float | None, float | None]:
    """Apply an assumed bps charge once to the replaced basket fraction."""
    if cost_bps < 0 or not math.isfinite(float(cost_bps)):
        raise ValueError("cost_bps must be finite and non-negative")
    if gross_return_pct is None:
        return None, None
    if cost_bps == 0:
        return 0.0, _rounded(gross_return_pct)
    if turnover is None:
        return None, None
    drag_pct_points = float(turnover) * float(cost_bps) / 100.0
    return _rounded(drag_pct_points), _rounded(float(gross_return_pct) - drag_pct_points)


def _validated_scenarios(scenarios: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    seen: set[str] = set()
    for scenario in scenarios:
        scenario_id = str(scenario["scenario_id"])
        cost_bps = float(scenario["cost_bps"])
        if scenario_id in seen or not scenario_id:
            raise ValueError("Cost scenario IDs must be non-blank and unique")
        if cost_bps < 0 or not math.isfinite(cost_bps):
            raise ValueError("Cost scenario bps values must be finite and non-negative")
        seen.add(scenario_id)
        normalized.append(
            {"scenario_id": scenario_id, "cost_bps": cost_bps, "role": str(scenario["role"])}
        )
    if not any(item["cost_bps"] == 0 for item in normalized):
        raise ValueError("A zero-cost control is required")
    return normalized


def build_report(
    predictions: pd.DataFrame,
    *,
    top_k: int = TOP_K,
    cost_scenarios: Sequence[dict[str, object]] = DEFAULT_COST_SCENARIOS,
    prediction_paths: Iterable[Path] = PREDICTION_PATHS,
) -> dict[str, object]:
    """Construct rank baskets and descriptive friction rows without resampling."""
    scenarios = _validated_scenarios(cost_scenarios)
    significance = json.loads(SIGNIFICANCE_REPORT.read_text(encoding="utf-8"))
    real_terms = json.loads(REAL_TERMS_REPORT.read_text(encoding="utf-8"))
    regime = json.loads(REGIME_REPORT.read_text(encoding="utf-8"))
    model_kind = {item["model"]: item["kind"] for item in significance["models"]}

    baskets: list[dict[str, object]] = []
    for model, model_rows in predictions.groupby("model", sort=True):
        previous: list[str] | None = None
        for year, group in model_rows.groupby("year", sort=True):
            basket = form_top_k_basket(group, top_k=top_k)
            current = list(basket["selected_tickers_ranked"])
            basket["model_kind"] = model_kind.get(str(model), "unknown")
            basket["turnover_from_prior_year"] = (
                None if previous is None else basket_turnover(previous, current)
            )
            basket["turnover_status"] = (
                "not_applicable_first_observed_basket" if previous is None else "observed_from_rank_baskets"
            )
            baskets.append(basket)
            previous = current

    plot_rows: list[dict[str, object]] = []
    for basket in baskets:
        for scenario in scenarios:
            drag, net = apply_cost(
                basket["gross_basket_mean_return_pct"],
                basket["turnover_from_prior_year"],
                float(scenario["cost_bps"]),
            )
            plot_rows.append(
                {
                    "model": basket["model"],
                    "model_kind": basket["model_kind"],
                    "year": basket["year"],
                    "scenario_id": scenario["scenario_id"],
                    "scenario_role": scenario["role"],
                    "cost_bps_assumption": scenario["cost_bps"],
                    "basket_size": basket["basket_size"],
                    "selected_tickers_ranked": "|".join(basket["selected_tickers_ranked"]),
                    "gross_basket_mean_return_pct": basket["gross_basket_mean_return_pct"],
                    "turnover_from_prior_year": basket["turnover_from_prior_year"],
                    "cost_drag_pct_points": drag,
                    "net_basket_mean_return_pct": net,
                    "chart_stamp": CHART_STAMP,
                }
            )

    transition_rows = [row for row in plot_rows if row["turnover_from_prior_year"] is not None]
    adverse_id = max(scenarios, key=lambda item: float(item["cost_bps"]))["scenario_id"]
    adverse_rows = [row for row in transition_rows if row["scenario_id"] == adverse_id]
    adverse_negative = sum(
        row["net_basket_mean_return_pct"] is not None and row["net_basket_mean_return_pct"] < 0
        for row in adverse_rows
    )
    source_paths = (
        *tuple(Path(path) for path in prediction_paths),
        SIGNIFICANCE_REPORT,
        REAL_TERMS_REPORT,
        REGIME_REPORT,
    )
    three_year_design = next(
        item for item in significance["power_analysis"]["designs"]
        if item["design_id"] == "current_three_year_pooled"
    )
    single_year_design = next(
        item for item in significance["power_analysis"]["designs"]
        if item["design_id"] == "current_one_split"
    )
    report = {
        "schema_version": "1.0.0",
        "task": "R2-FRICTION-01",
        "chart_stamp": CHART_STAMP,
        "design": {
            "analysis_type": "descriptive rank-basket turnover and cost sensitivity",
            "universe": UNIVERSE_LABEL,
            "target_years": sorted(int(value) for value in predictions["year"].unique()),
            "models": sorted(str(value) for value in predictions["model"].unique()),
            "rows_per_model_year": sorted(
                int(value) for value in predictions.groupby(["model", "year"]).size().unique()
            ),
            "top_k": top_k,
            "top_k_share_of_evaluated_rows": _rounded(top_k / 80),
            "basket_weighting": "equal weight",
            "rank_direction": "descending y_pred within target year and model",
            "tie_break": "ticker ascending",
            "raw_prediction_magnitudes_emitted": False,
            "turnover": "half-L1 distance between consecutive equal-weight rank baskets",
            "cost_formula": "net return pct = gross return pct - turnover * cost_bps / 100",
            "first_year_treatment": (
                "No predecessor basket is observed. Nonzero-cost drag and net are null; "
                "the zero-cost control equals gross."
            ),
            "sampling": "none; seedless arithmetic",
        },
        "cost_scenarios": scenarios,
        "baskets": baskets,
        "plot_rows": plot_rows,
        "evidence_context": {
            "nominal_try": {
                "evaluated_here": True,
                "significance_source": "experiments/results/significance_report.json",
                "ml_family_wise_significant": bool(significance["headline"]["significant_fwer_0_05"]),
                "conclusion": significance["headline"]["conclusion"],
            },
            "cpi_deflated_try": {
                "evaluated_here": False,
                "source": "experiments/results_real_terms/comparison_report.json",
                "reliable_predictive_edge_established": False,
            },
            "usd_basis": {
                "evaluated_here": False,
                "source": "experiments/results_real_terms/comparison_report.json",
                "reliable_predictive_edge_established": False,
            },
            "multiplicity": significance["analysis"]["multiplicity"],
            "power": {
                "three_year_detectable_abs_ic": three_year_design["analytic_minimum_detectable_abs_ic"],
                "single_year_detectable_abs_ic": single_year_design["analytic_minimum_detectable_abs_ic"],
                "interpretation": "Design limits remain unchanged; this sensitivity adds no significance test.",
            },
            "regime_status": regime["conditional_diagnostics"]["status"],
        },
        "findings": [
            "The zero-cost control reproduces each observed gross basket mean exactly.",
            (
                f"The deliberately adverse arithmetic control produces negative net values in "
                f"{adverse_negative} of {len(adverse_rows)} model-year transitions; this is a stress-control "
                "property, not a market-cost estimate."
            ),
            "No cost scenario changes the existing significance, power, calibration, or model evidence.",
        ],
        "claim_safety": {
            "descriptive_sensitivity_only": True,
            "implementable_returns_established": False,
            "investment_value_established": False,
            "liquidity_or_tradeability_estimated": False,
            "bid_ask_spread_or_market_impact_inferred": False,
            "core_model_or_ranking_computation_changed": False,
            "reliable_predictive_edge_established": False,
        },
        "limitations": [
            "Cost bps values are explicit assumptions, not measured BIST costs.",
            "No bid–ask spread, market impact, liquidity, capacity, execution, suspension, or tradeability input is available or inferred.",
            "The evaluated cohort is the retrospectively fixed 81-ticker training universe with 80 rows per split, not verified point-in-time BIST100 membership; survivorship and universe-selection look-ahead risks remain unresolved.",
            "Only three test years are observed in one task-defined macro period; the numerical environment qualification remains applicable.",
            "The analysis uses nominal TRY outcomes only. CPI-deflated TRY and USD-basis evidence remain separate and are not recomputed here.",
            "Multiplicity and low-power limits remain unchanged; isolated basket outcomes do not establish signal or practical value.",
            "Missing selected realized outcomes propagate to null gross and net values; missing predictions are excluded from rank eligibility and never filled.",
            "Research support only; not investment advice.",
        ],
        "source_artifacts": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": _sha256(path),
            }
            for path in source_paths
        ],
    }
    validate_claim_safety_text(json.dumps(report, ensure_ascii=False))
    return report


def _shown(value: object, digits: int = 3) -> str:
    if value is None:
        return "null"
    return f"{float(value):.{digits}f}"


def render_markdown(report: dict[str, object]) -> str:
    design = report["design"]
    lines = [
        "# Friction sensitivity report (R2-FRICTION-01)",
        "",
        f"> **{report['chart_stamp']}**",
        "",
        f"**Evaluated cohort:** {design['universe']}",
        "",
        "This is descriptive sensitivity analysis over persisted historical evaluation rows. It does not establish execution quality, realizable performance, investment value, or advice.",
        "",
        "## Design and assumptions",
        "",
        f"Each model and target year forms an equal-weight top-{design['top_k']} basket from descending within-model, within-year `y_pred` ranks. Raw prediction magnitudes are neither compared across models nor emitted. Ties are resolved by ticker ascending. Realized `y_true` is used only after basket formation to calculate the basket's nominal TRY mean.",
        "",
        "Turnover is half the L1 distance between consecutive annual equal-weight baskets. Assumed cost drag in percentage points is `turnover × cost_bps / 100`; net is gross minus that drag. There is no predecessor for 2023, so nonzero-cost drag and net remain null there. The zero-cost control equals gross.",
        "",
        "| Scenario | Assumed bps | Role |",
        "|---|---:|---|",
    ]
    for scenario in report["cost_scenarios"]:
        lines.append(
            f"| {scenario['scenario_id']} | {_shown(scenario['cost_bps'], 1)} | {scenario['role']} |"
        )
    lines.extend(
        [
            "",
            "The two middle values are illustrative assumptions. The 10,000 bps value is deliberately extreme and exists only to negative-control the arithmetic. None is a measured BIST spread, impact, liquidity, or tradeability estimate.",
            "",
            "## Per-year gross and assumed-cost net basket means",
            "",
            "Every gross figure stays paired with its net counterpart under the report stamp above.",
            "",
            "| Model | Year | Scenario | Gross nominal TRY % | Turnover | Cost drag pp | Net nominal TRY % |",
            "|---|---:|---|---:|---:|---:|---:|",
        ]
    )
    for row in report["plot_rows"]:
        lines.append(
            f"| {row['model']} | {row['year']} | {row['scenario_id']} | "
            f"{_shown(row['gross_basket_mean_return_pct'])} | "
            f"{_shown(row['turnover_from_prior_year'])} | "
            f"{_shown(row['cost_drag_pct_points'])} | "
            f"{_shown(row['net_basket_mean_return_pct'])} |"
        )
    lines.extend(["", "## Findings", ""])
    lines.extend(f"- {finding}" for finding in report["findings"])
    lines.extend(["", "## Claim-safety boundaries and limitations", ""])
    lines.extend(f"- {limitation}" for limitation in report["limitations"])
    lines.extend(
        [
            "",
            "Nominal TRY is the only basis evaluated in this report. The CPI-deflated TRY and USD-basis significance reports remain parallel evidence and are not substituted or merged. Existing multiplicity, power, survivorship, retrospective-cohort, single-regime, and environment limitations remain in force.",
            "",
            "The conclusion remains: no reliable predictive edge. Research support only; not investment advice.",
            "",
        ]
    )
    text = "\n".join(lines)
    validate_claim_safety_text(text)
    return text


def _write_plot_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "model",
        "model_kind",
        "year",
        "scenario_id",
        "scenario_role",
        "cost_bps_assumption",
        "basket_size",
        "selected_tickers_ranked",
        "gross_basket_mean_return_pct",
        "turnover_from_prior_year",
        "cost_drag_pct_points",
        "net_basket_mean_return_pct",
        "chart_stamp",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(
    output_dir: Path = RESULTS_DIR,
    *,
    prediction_paths: Iterable[Path] = PREDICTION_PATHS,
    top_k: int = TOP_K,
    cost_scenarios: Sequence[dict[str, object]] = DEFAULT_COST_SCENARIOS,
) -> tuple[Path, Path, Path]:
    prediction_paths = tuple(Path(path) for path in prediction_paths)
    predictions = load_prediction_dumps(prediction_paths)
    report = build_report(
        predictions,
        top_k=top_k,
        cost_scenarios=cost_scenarios,
        prediction_paths=prediction_paths,
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / JSON_OUTPUT.name
    markdown_path = output_dir / MARKDOWN_OUTPUT.name
    plot_path = output_dir / PLOT_OUTPUT.name
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    _write_plot_csv(plot_path, report["plot_rows"])
    print(
        f"[friction] models={len(report['design']['models'])} top_k={top_k} "
        f"scenarios={len(report['cost_scenarios'])} -> {output_dir}"
    )
    return json_path, markdown_path, plot_path


def _scenarios_from_bps(values: Sequence[float]) -> tuple[dict[str, object], ...]:
    scenarios = []
    for value in values:
        shown = str(int(value)) if float(value).is_integer() else str(value).replace(".", "p")
        scenarios.append(
            {
                "scenario_id": f"assumed_{shown}bps",
                "cost_bps": float(value),
                "role": "user-supplied descriptive assumption",
            }
        )
    return tuple(scenarios)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--top-k", type=int, default=TOP_K)
    parser.add_argument(
        "--cost-bps",
        type=float,
        nargs="+",
        default=None,
        help="Optional assumed bps scenarios. Include 0 for the required control.",
    )
    args = parser.parse_args()
    scenarios = DEFAULT_COST_SCENARIOS if args.cost_bps is None else _scenarios_from_bps(args.cost_bps)
    run(args.output_dir, top_k=args.top_k, cost_scenarios=scenarios)


if __name__ == "__main__":
    main()
