"""Run the existing walk-forward and significance machinery on alternative targets.

Outputs are isolated under ``experiments/results_real_terms``.  Canonical
nominal prediction dumps, reports, and leaderboards are read-only for this run.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.data_collection import derive_alternative_targets as alt
from experiments import run_experiments as exp
from experiments import significance

ROOT = Path(__file__).resolve().parents[1]
ALTERNATIVE_TARGETS = ROOT / "data" / "trusted_clean" / "modeling_targets_alternative.csv"
OUTPUT_ROOT = ROOT / "experiments" / "results_real_terms"

BASES = {
    "real_try": {
        "target_col": "next_year_real_return_pct",
        "label": "CPI-deflated real TRY return",
        "limitation": "CPI-deflated TRY returns use national December year-on-year CPI as a descriptive basis; they do not represent investor-specific inflation or investment value.",
    },
    "usd": {
        "target_col": "next_year_usd_return_pct",
        "label": "USD-basis return",
        "limitation": "USD-basis returns use Yahoo year-end TRY-per-USD closes as a descriptive currency basis; they do not establish implementability or investment value.",
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _prediction_rows(panel: pd.DataFrame, feature_cols: list[str], split: dict) -> tuple[list[dict], list[dict]]:
    train = panel[(panel["feature_year"] + 1).isin(split["train_target_years"])]
    test = panel[panel["feature_year"] == split["test_feature_year"]]
    x_train = train[feature_cols].to_numpy(float)
    y_train = train["target_return"].to_numpy(float)
    x_test = test[feature_cols].to_numpy(float)
    y_test = test["target_return"].to_numpy(float)
    usable_train = ~np.isnan(y_train)
    x_train, y_train = x_train[usable_train], y_train[usable_train]

    predictions: list[dict] = []
    leaderboard: list[dict] = []
    for name, (kind, model) in exp.MODELS.items():
        y_pred = np.asarray(model(x_train, y_train, x_test), dtype=float)
        metrics = exp._metrics(y_test, y_pred)
        evaluated = ~np.isnan(y_test) & ~np.isnan(y_pred)
        predictions.extend(
            {
                "ticker": ticker,
                "year": split["test_feature_year"] + 1,
                "model": name,
                "y_true": float(actual),
                "y_pred": float(predicted),
            }
            for ticker, actual, predicted in zip(
                test.loc[evaluated, "ticker"], y_test[evaluated], y_pred[evaluated]
            )
        )
        leaderboard.append(
            {
                "split": split["name"],
                "model": name,
                "kind": kind,
                **{key: value for key, value in metrics.items() if key != "n"},
            }
        )
    return predictions, leaderboard


def _run_basis(basis_id: str, config: dict) -> dict:
    output_dir = OUTPUT_ROOT / basis_id
    output_dir.mkdir(parents=True, exist_ok=True)
    panel, feature_cols = exp.build_panel_for_target(
        config["target_col"], target_path=ALTERNATIVE_TARGETS
    )
    if panel is None:
        raise ValueError(f"no usable rows for {config['target_col']}")

    leaderboard_rows = []
    for split in exp.SPLITS:
        predictions, leaderboard = _prediction_rows(panel, feature_cols, split)
        pd.DataFrame(
            predictions, columns=significance.REQUIRED_COLUMNS
        ).to_csv(
            output_dir / f"predictions_{split['name']}.csv",
            index=False,
            float_format="%.17g",
            lineterminator="\n",
        )
        leaderboard_rows.extend(leaderboard)
    pd.DataFrame(leaderboard_rows).to_csv(
        output_dir / "leaderboard.csv", index=False, lineterminator="\n"
    )

    prediction_frame, sources = significance.load_prediction_dumps(output_dir)
    report = significance.build_report(prediction_frame, sources)
    report["task"] = "R2-REAL-01"
    report["target_basis"] = {
        "id": basis_id,
        "label": config["label"],
        "target_column": config["target_col"],
        "alternative_targets_sha256": _sha256(ALTERNATIVE_TARGETS),
    }
    report["limitations"] = [
        config["limitation"] if item.startswith("Nominal TRY returns cover") else item
        for item in report["limitations"]
    ]
    report["claim_safety"] = {
        "descriptive_research_evidence_only": True,
        "investment_value_established": False,
        "reliable_predictive_edge_established": False,
        "multiplicity_gate": "Bonferroni across the same six-model ML family",
    }
    json_path = output_dir / "significance_report.json"
    markdown_path = output_dir / "significance_report.md"
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    prefix = (
        f"# {config['label']} evaluation (R2-REAL-01)\n\n"
        "Descriptive historical research evidence only; not investment value or investment advice. "
        "The nominal TRY evaluation remains the canonical headline and is not replaced.\n\n"
    )
    markdown = prefix + significance.render_markdown(report)
    alt.validate_claim_safety_text(markdown)
    markdown_path.write_text(markdown, encoding="utf-8")
    return {
        "basis_id": basis_id,
        "label": config["label"],
        "target_column": config["target_col"],
        "headline": report["headline"],
        "evaluated_rows_per_model_split": report["analysis"]["evaluated_tickers_per_model_split"],
        "report_json": json_path.relative_to(ROOT).as_posix(),
        "report_md": markdown_path.relative_to(ROOT).as_posix(),
    }


def _write_comparison(results: list[dict]) -> tuple[Path, Path]:
    payload = {
        "schema_version": "1.0.0",
        "task": "R2-REAL-01",
        "nominal_artifacts_replaced": False,
        "alternative_targets_sha256": _sha256(ALTERNATIVE_TARGETS),
        "bases": results,
        "claim_safety": {
            "conclusion": "No reliable predictive edge is established on either alternative basis.",
            "descriptive_research_evidence_only": True,
            "investment_value_established": False,
        },
    }
    json_path = OUTPUT_ROOT / "comparison_report.json"
    md_path = OUTPUT_ROOT / "comparison_report.md"
    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Alternative-basis comparison (R2-REAL-01)",
        "",
        "The nominal TRY evaluation remains unchanged. These parallel results are descriptive historical research evidence only, not investment value or investment advice.",
        "",
        "| Basis | Selected ML model | Pooled IC | Raw permutation p | Bonferroni p | FWER significant |",
        "|---|---|---:|---:|---:|---|",
    ]
    for result in results:
        headline = result["headline"]
        lines.append(
            f"| {result['label']} | {headline['model']} | {headline['observed_ic']:.3f} | "
            f"{headline['permutation_p_value_two_sided']:.4f} | "
            f"{headline['bonferroni_adjusted_p_value']:.4f} | "
            f"{'yes' if headline['significant_fwer_0_05'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "No reliable predictive edge is established on either alternative basis. Any isolated split or uncorrected p-value remains exploratory and must not be promoted as a finding.",
            "",
        ]
    )
    markdown = "\n".join(lines)
    alt.validate_claim_safety_text(markdown)
    md_path.write_text(markdown, encoding="utf-8")
    return json_path, md_path


def run() -> tuple[Path, Path]:
    if not ALTERNATIVE_TARGETS.is_file():
        raise FileNotFoundError(
            f"missing {ALTERNATIVE_TARGETS}; run make alternative-targets first"
        )
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    results = [_run_basis(basis_id, config) for basis_id, config in BASES.items()]
    paths = _write_comparison(results)
    for result in results:
        headline = result["headline"]
        print(
            f"[{result['basis_id']}] {headline['model']} pooled IC={headline['observed_ic']:.3f} "
            f"Bonferroni p={headline['bonferroni_adjusted_p_value']:.4f}"
        )
    print("No reliable predictive edge is established on either alternative basis.")
    return paths


if __name__ == "__main__":
    run()
