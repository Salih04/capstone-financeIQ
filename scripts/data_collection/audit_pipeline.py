"""Audit FinanceIQ CSV data pipeline without mutating datasets.

Writes:
    data/trusted_clean/pipeline_audit_report.json
    data/trusted_clean/pipeline_audit_report.md
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
CLEAN_DIR = DATA_DIR / "trusted_clean"
OUT_JSON = CLEAN_DIR / "pipeline_audit_report.json"
OUT_MD = CLEAN_DIR / "pipeline_audit_report.md"


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, comment="#")


def _classify(path: Path) -> str:
    s = str(path.relative_to(REPO_ROOT))
    name = path.name
    if "/trusted_raw/" in s:
        return "raw"
    if "/trusted/" in s:
        return "trusted_reference"
    if "/config/" in s:
        return "config"
    if name.startswith("modeling_dataset_public"):
        return "public_modeling_ready"
    if name.startswith("modeling_dataset_training"):
        return "training_modeling_ready"
    if name.startswith("modeling_dataset_"):
        return "modeling_ready"
    if "/trusted_clean/" in s:
        return "clean_generated"
    return "other"


def _target_summary(df: pd.DataFrame) -> dict:
    out: dict[str, int] = {}
    for col in ("has_target", "is_inference_row"):
        if col in df.columns:
            out[col] = int(df[col].astype(str).str.lower().isin({"true", "1"}).sum())
    for col in df.columns:
        if col.startswith("next_year_"):
            out[f"{col}_nonnull"] = int(pd.to_numeric(df[col], errors="coerce").notna().sum())
    return out


def _profile(path: Path) -> dict:
    rel = str(path.relative_to(REPO_ROOT))
    try:
        df = _read_csv(path)
    except Exception as exc:  # noqa: BLE001
        return {"path": rel, "class": _classify(path), "read_error": f"{type(exc).__name__}: {exc}"}

    ticker_col = "ticker" if "ticker" in df.columns else None
    year_col = "year" if "year" in df.columns else None
    years: list[int] = []
    if year_col:
        y = pd.to_numeric(df[year_col], errors="coerce").dropna()
        years = sorted(int(v) for v in y.unique())

    duplicate_keys = None
    if ticker_col and year_col:
        duplicate_keys = int(df.duplicated([ticker_col, year_col]).sum())

    missing = {
        c: round(float(df[c].isna().mean()), 4)
        for c in df.columns
        if len(df) and float(df[c].isna().mean()) > 0
    }
    return {
        "path": rel,
        "class": _classify(path),
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "ticker_count": int(df[ticker_col].astype(str).str.upper().nunique()) if ticker_col else None,
        "year_min": min(years) if years else None,
        "year_max": max(years) if years else None,
        "years": years,
        "duplicate_ticker_year_keys": duplicate_keys,
        "avg_missingness": round(float(df.isna().mean().mean()), 4) if len(df) else 0.0,
        "missingness_nonzero": missing,
        "target_availability": _target_summary(df),
    }


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text()) if path.is_file() else {}
    except Exception:
        return {}


def build_report() -> dict:
    csvs = sorted(DATA_DIR.rglob("*.csv"))
    profiles = [_profile(p) for p in csvs]
    by_class: dict[str, int] = {}
    for p in profiles:
        by_class[p["class"]] = by_class.get(p["class"], 0) + 1

    quality = _load_json(CLEAN_DIR / "data_quality_report.json")
    split = _load_json(CLEAN_DIR / "universe_split_report.json")
    experiments = REPO_ROOT / "experiments" / "results" / "leaderboard.csv"
    leaderboard_rows = 0
    if experiments.is_file():
        leaderboard_rows = int(len(_read_csv(experiments)))

    return {
        "report": "FinanceIQ pipeline audit",
        "csv_file_count": len(profiles),
        "files_by_class": by_class,
        "files": profiles,
        "current_quality_summary": {
            "rows": quality.get("rows"),
            "n_features": quality.get("n_features"),
            "rows_with_target": quality.get("rows_with_target"),
            "inference_only_rows": quality.get("inference_only_rows"),
            "benchmark_available": quality.get("benchmark_available"),
            "valid_for_T_to_T1_modeling": quality.get("valid_for_T_to_T1_modeling"),
            "issues": quality.get("issues"),
        },
        "universe_split": split,
        "experiment_leaderboard_rows": leaderboard_rows,
        "guardrails": {
            "public_ui_universe": "data/config/universe_public_40.csv",
            "expanded_training_universe": "data/config/universe_training_bist100.csv",
            "inference_only_year_rule": "rows without validated T+1 target stay is_inference_row=true",
            "no_investment_advice": True,
        },
    }


def write_markdown(report: dict) -> None:
    lines = [
        "# FinanceIQ Pipeline Audit",
        "",
        f"- CSV files: **{report['csv_file_count']}**",
        f"- Files by class: `{report['files_by_class']}`",
        f"- Public universe: **{report.get('universe_split', {}).get('public_universe_count')}** tickers",
        f"- Training universe: **{report.get('universe_split', {}).get('training_universe_count')}** tickers",
        f"- Training-only: **{report.get('universe_split', {}).get('training_only_count')}** tickers",
        "",
        "## Current Quality Summary",
        "",
    ]
    for k, v in report["current_quality_summary"].items():
        lines.append(f"- {k}: `{v}`")
    lines += [
        "",
        "## CSV Inventory",
        "",
        "| class | path | rows | tickers | years | duplicate ticker-year | avg missing | target fields |",
        "|---|---|---:|---:|---|---:|---:|---|",
    ]
    for item in report["files"]:
        if item.get("read_error"):
            lines.append(f"| {item['class']} | `{item['path']}` | error |  |  |  |  | {item['read_error']} |")
            continue
        years = ""
        if item.get("year_min") is not None:
            years = f"{item['year_min']}-{item['year_max']}"
        targets = {k: v for k, v in item.get("target_availability", {}).items() if v}
        lines.append(
            f"| {item['class']} | `{item['path']}` | {item['rows']} | "
            f"{item.get('ticker_count') or ''} | {years} | "
            f"{item.get('duplicate_ticker_year_keys') if item.get('duplicate_ticker_year_keys') is not None else ''} | "
            f"{item['avg_missingness']} | `{targets}` |"
        )
    OUT_MD.write_text("\n".join(lines))


def main() -> int:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    report = build_report()
    OUT_JSON.write_text(json.dumps(report, indent=2, default=str))
    write_markdown(report)
    print(f"[audit] wrote {OUT_JSON.relative_to(REPO_ROOT)}")
    print(f"[audit] wrote {OUT_MD.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
