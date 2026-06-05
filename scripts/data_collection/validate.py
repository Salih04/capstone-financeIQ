"""Validation + data-quality report for the modeling dataset (PHASE 7/8)."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from scripts.data_collection import pipeline as P

# Feature registry roles (PHASE 7).
ROLE_IDENTIFIER = "identifier"
ROLE_METADATA = "metadata"
ROLE_FEATURE = "feature_allowed"
ROLE_TARGET = "target"
ROLE_SAME_YEAR = "same_year_analysis_only"
ROLE_BENCHMARK = "benchmark"
ROLE_EXCLUDED = "excluded"


def feature_registry(df: pd.DataFrame) -> list[dict]:
    reg = []
    for col in df.columns:
        if col in ("ticker", "company_name", "year"):
            role, leak = ROLE_IDENTIFIER, "none"
        elif col in ("sector", "indices", "is_bist100", "target_year", "has_target", "is_inference_row"):
            role, leak = ROLE_METADATA, "none"
        elif col == "same_year_return_pct":
            role, leak = ROLE_SAME_YEAR, "is_same_year_outcome"
        elif col == "next_year_return_pct":
            role, leak = ROLE_TARGET, "is_target"
        elif col.startswith("next_year_"):
            role, leak = (ROLE_BENCHMARK if "bist100" in col else ROLE_TARGET), "is_target"
        else:
            role, leak = ROLE_FEATURE, "provisional_reference_fundamental"
        reg.append({"column": col, "role": role, "leakage_risk": leak})
    return reg


def _benchmark_report(df: pd.DataFrame) -> dict:
    """Benchmark coverage for the quality report (source + years + values)."""
    src = "none"
    rep_json = P.CLEAN_DIR / "bist100_benchmark_report.json"
    if rep_json.is_file():
        try:
            src = json.loads(rep_json.read_text()).get("source", "unknown")
        except Exception:
            src = "unknown"
    years, vals = [], {}
    if "next_year_bist100_return_pct" in df.columns:
        b = df.dropna(subset=["next_year_bist100_return_pct"])[["target_year", "next_year_bist100_return_pct"]]
        b = b.drop_duplicates("target_year")
        years = sorted(int(y) for y in b["target_year"])
        vals = {int(y): float(v) for y, v in zip(b["target_year"], b["next_year_bist100_return_pct"])}
    enabled = bool(years)
    return {
        "source": src,
        "target_years_covered": years,
        "bist100_return_values": vals,
        "excess_outperform_targets_enabled": enabled,
    }


def validate(df: pd.DataFrame, cfg: P.PipelineConfig) -> dict:
    issues: list[str] = []
    ref = P.load_reference()
    var = P.classify_variability(ref)

    # required columns
    required = ["ticker", "year", "next_year_return_pct", "has_target", "is_inference_row"]
    for c in required:
        if c not in df.columns:
            issues.append(f"missing required column: {c}")

    # duplicate ticker-year
    dup = df.duplicated(["ticker", "year"]).sum()
    if dup:
        issues.append(f"{dup} duplicate ticker-year rows")

    # leakage: same-year outcome must not be a feature
    feats = P.feature_columns(df)
    if "same_year_return_pct" in feats:
        issues.append("LEAKAGE: same_year_return_pct present in feature set")
    if "next_year_return_pct" in feats:
        issues.append("LEAKAGE: next_year_return_pct present in feature set")

    # frozen-snapshot detection among FEATURES (should be none after exclusion)
    g = df.groupby("ticker")
    frozen_feats = [c for c in feats if c in df.columns
                    and not (g[c].nunique(dropna=False) > 1).any()]

    # missingness per column
    missingness = {c: round(float(df[c].isna().mean()), 3) for c in df.columns}

    # target coverage by year
    cov = (df.groupby("year")["has_target"].mean().round(3)).to_dict()

    # extreme growth (kept, reported)
    extreme = {}
    for c in feats:
        if c.endswith("growth_pct") and c in df.columns:
            extreme[c] = int((df[c].dropna().abs() > 100000).sum())

    report = {
        "rows": int(len(df)),
        "rows_by_year": df.groupby("year").size().to_dict(),
        "tickers_by_year": df.groupby("year")["ticker"].nunique().to_dict(),
        "n_features": len(feats),
        "feature_columns": feats,
        "target_columns": [c for c in P.TARGET_COLS if c in df.columns],
        "frozen_columns_excluded_from_features": [
            c for c in var["frozen"] if c not in ("source_file",)
        ],
        "frozen_feature_columns_remaining": frozen_feats,
        "missingness": missingness,
        "target_coverage_by_year": cov,
        "rows_with_target": int(df["has_target"].sum()),
        "inference_only_rows": int(df["is_inference_row"].sum()),
        "benchmark_available": bool(df["next_year_bist100_return_pct"].notna().any())
        if "next_year_bist100_return_pct" in df.columns else False,
        "benchmark": _benchmark_report(df),
        "extreme_growth_counts": extreme,
        "feature_registry": feature_registry(df),
        "manual_financials": getattr(cfg, "manual_report", {}) or {"present": False},
        "issues": issues,
        "valid_for_T_to_T1_modeling": len(issues) == 0,
    }
    P.QUALITY_JSON.write_text(json.dumps(report, indent=2, default=str))
    _write_md(report)
    status = "VALID" if report["valid_for_T_to_T1_modeling"] else f"ISSUES ({len(issues)})"
    cfg.say(f"[validate] {status}; features={len(feats)} target_rows={report['rows_with_target']} "
            f"benchmark={'yes' if report['benchmark_available'] else 'no'}")
    for i in issues:
        cfg.say(f"   - {i}")
    return report


def _write_md(r: dict) -> None:
    lines = ["# Data quality report\n",
             f"- Rows: **{r['rows']}**  |  Features: **{r['n_features']}**  |  "
             f"Rows with target: **{r['rows_with_target']}**  |  Inference-only: **{r['inference_only_rows']}**",
             f"- Benchmark available: **{r['benchmark_available']}**",
             f"- Valid for T→T+1 modeling: **{r['valid_for_T_to_T1_modeling']}**\n",
             "## Rows by year", "", "| year | rows | tickers | target coverage |", "|---|---|---|---|"]
    for y in sorted(r["rows_by_year"]):
        lines.append(f"| {y} | {r['rows_by_year'][y]} | {r['tickers_by_year'][y]} | {r['target_coverage_by_year'].get(y,'-')} |")
    b = r.get("benchmark", {}) or {}
    lines += ["", "## BIST100 benchmark",
              f"- Source: **{b.get('source', 'none')}**",
              f"- Target years covered: {b.get('target_years_covered', [])}",
              f"- Return values: {b.get('bist100_return_values', {})}",
              f"- Excess/outperform targets enabled: **{b.get('excess_outperform_targets_enabled', False)}**", ""]
    man = r.get("manual_financials", {}) or {}
    lines += ["", "## Manual financial history",
              f"- Present: **{man.get('present', False)}**",
              f"- Files: {man.get('files', [])}",
              f"- Rows ingested: {man.get('rows_ingested', 0)}",
              f"- Accepted as features: {man.get('accepted_feature_columns', [])}",
              f"- Overrides from snapshot: {man.get('overrides_from_snapshot', {})}",
              f"- Rejected: {man.get('rejected_feature_columns', {})}",
              f"- Misaligned columns: {man.get('misaligned_columns_rejected', [])}",
              f"- Issues: {man.get('issues', [])}", ""]
    lines += ["## Frozen reference columns EXCLUDED from features (unreliable snapshot)",
              "", ", ".join(r["frozen_columns_excluded_from_features"]) or "none", "",
              "## Provisional feature columns (year-T, genuinely varying)",
              "", ", ".join(r["feature_columns"]) or "none", ""]
    if r["issues"]:
        lines += ["## Issues", ""] + [f"- {i}" for i in r["issues"]]
    else:
        lines += ["## Issues", "", "None."]
    P.QUALITY_MD.write_text("\n".join(lines))
