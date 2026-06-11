"""Inspect the data/raw/quarterly_fintables/ Fintables quarterly exports for usability.

Answers one question honestly: do the quarterly files contain genuinely
per-quarter (or per-year) varying fundamentals, or are they a single frozen
snapshot replicated across periods?

Writes data/trusted_clean/quarterly_snapshot_inspection.{json,md}.
No modeling, no fabrication — diagnostic only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
QDIR = REPO_ROOT / "data/raw/quarterly_fintables"
OUT_JSON = REPO_ROOT / "data" / "trusted_clean" / "quarterly_snapshot_inspection.json"
OUT_MD = REPO_ROOT / "data" / "trusted_clean" / "quarterly_snapshot_inspection.md"

_CHECK_COLS = ["Revenue", "Net Income", "Return on Equity (ROE)", "Total Assets",
               "Price", "P/E", "Market Capitalization"]


def _read(f: Path) -> pd.DataFrame:
    df = pd.read_excel(f, header=0)
    if not any(str(c).strip().lower() in ("company", "ticker") for c in df.columns):
        df = pd.read_excel(f, header=1)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _period(f: Path) -> str | None:
    m = re.search(r"(20\d{2})q([1-4])", f.name.lower())
    return m.group(0) if m else None


def inspect() -> dict:
    files = sorted(p for p in QDIR.glob("*.xlsx")) if QDIR.is_dir() else []
    rep = {"dir": str(QDIR), "files": [p.name for p in files], "periods": [],
           "rows_per_period": {}, "frozen_columns": [], "varying_columns": [],
           "verdict": "", "issues": []}
    if not files:
        rep["issues"].append("no quarterly files found")
        return rep

    frames = []
    for f in files:
        p = _period(f)
        if not p:
            rep["issues"].append(f"{f.name}: no period in filename")
            continue
        df = _read(f)
        tcol = next((c for c in df.columns if str(c).strip().lower() in ("company", "ticker")), None)
        if tcol is None:
            rep["issues"].append(f"{f.name}: no ticker column")
            continue
        df = df.rename(columns={tcol: "ticker"})
        df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
        df["period"] = p
        df = df[df["ticker"].str.match(r"^[A-Z]{3,6}$")]
        rep["periods"].append(p)
        rep["rows_per_period"][p] = int(len(df))
        frames.append(df)

    if not frames:
        rep["issues"].append("no usable frames")
        return rep
    big = pd.concat(frames, ignore_index=True)
    rep["periods"] = sorted(set(rep["periods"]))

    # for each ticker, does the column ever change across periods?
    g = big.groupby("ticker")
    for col in _CHECK_COLS:
        if col not in big.columns:
            continue
        share_varying = float((g[col].nunique(dropna=False) > 1).mean())
        (rep["varying_columns"] if share_varying >= 0.5 else rep["frozen_columns"]).append(
            {"column": col, "share_tickers_varying": round(share_varying, 3)})

    n_frozen = len(rep["frozen_columns"])
    n_var = len(rep["varying_columns"])
    if n_var == 0:
        rep["verdict"] = ("FROZEN SNAPSHOT: every checked fundamental is identical across all "
                          "periods for ~all tickers. Same defect as the yearly files — NOT usable "
                          "as time-varying fundamentals for T->T+1.")
    elif n_frozen == 0:
        rep["verdict"] = "USABLE: fundamentals genuinely vary across periods."
    else:
        rep["verdict"] = (f"PARTIAL: {n_var} varying, {n_frozen} frozen columns. "
                          "Only varying columns would be usable.")
    return rep


def main() -> int:
    rep = inspect()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(rep, indent=2))
    OUT_MD.write_text(
        f"# Quarterly snapshot inspection\n\n- Files: {len(rep['files'])} | periods: {rep['periods']}\n"
        f"- Frozen columns: {[c['column'] for c in rep['frozen_columns']]}\n"
        f"- Varying columns: {[c['column'] for c in rep['varying_columns']]}\n\n"
        f"**Verdict:** {rep['verdict']}\n")
    print(f"[quarterly] periods={rep['periods']} frozen={[c['column'] for c in rep['frozen_columns']]} "
          f"varying={[c['column'] for c in rep['varying_columns']]}")
    print(f"[quarterly] {rep['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
