"""Frozen-column evidence report for the data provider / stakeholders.

Proves, with raw numbers, that valuation/profitability/income-statement columns
in BOTH the yearly XLSX-derived data and the new_data_quarter quarterly files are
a repeated point-in-time snapshot (identical across periods per ticker) — so they
cannot be used as historical T->T+1 features. No fabrication.

Writes data/trusted_clean/frozen_column_evidence.{json,md}.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
YEARLY_CSV = REPO_ROOT / "data" / "trusted" / "stocks_2020_2025.csv"
QDIR = REPO_ROOT / "new_data_quarter"
OUT_JSON = REPO_ROOT / "data" / "trusted_clean" / "frozen_column_evidence.json"
OUT_MD = REPO_ROOT / "data" / "trusted_clean" / "frozen_column_evidence.md"

REPRESENTATIVE = ["AEFES", "ASELS", "BIMAS", "THYAO", "TUPRS"]

# canonical name -> (yearly column, quarterly raw header)
COLMAP = {
    "pe_ratio": ("pe", "P/E"),
    "pb_ratio": ("pb", "P/B"),
    "ev_ebitda": ("ev_ebitda", "EV/EBITDA"),
    "roe": ("roe_pct", "Return on Equity (ROE)"),
    "roa": ("roa_pct", "Return on Assets (ROA)"),
    "gross_margin": ("gross_margin_pct", "Gross Profit Margin"),
    "ebitda_margin": ("ebitda_margin_pct", "EBITDA Margin"),
    "net_margin": ("net_margin_pct", "Net Profit Margin"),
    "market_cap": ("market_cap", "Market Capitalization"),
    "enterprise_value": ("enterprise_value", "Enterprise Value (EV)"),
    "revenue": ("revenue", "Revenue"),
    "ebitda": ("ebitda", "EBITDA"),
    "net_income": ("net_income", "Net Income"),
    "price": ("price", "Price"),
    "total_assets": ("total_assets", "Total Assets"),
}


def _read_quarterly() -> pd.DataFrame | None:
    if not QDIR.is_dir():
        return None
    frames = []
    for f in sorted(QDIR.glob("*.xlsx")):
        m = re.search(r"(20\d{2})q([1-4])", f.name.lower())
        if not m:
            continue
        df = pd.read_excel(f, header=0)
        if not any(str(c).strip().lower() in ("company", "ticker") for c in df.columns):
            df = pd.read_excel(f, header=1)
        df.columns = [str(c).strip() for c in df.columns]
        tcol = next((c for c in df.columns if str(c).strip().lower() in ("company", "ticker")), None)
        if tcol is None:
            continue
        df = df.rename(columns={tcol: "ticker"})
        df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
        df["period"] = m.group(0)
        frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else None


def _analyze(df: pd.DataFrame, col: str, label: str) -> dict | None:
    if col not in df.columns:
        return None
    g = df.groupby("ticker")[col]
    nun = g.nunique(dropna=False)
    total = int(len(nun))
    frozen = int((nun <= 1).sum())
    reps = {}
    for t in REPRESENTATIVE:
        sub = df[df["ticker"] == t]
        if not sub.empty:
            vals = pd.to_numeric(sub[col], errors="coerce").dropna().unique().tolist()
            reps[t] = {"unique_values": len(vals), "values": [round(float(v), 2) for v in vals[:6]]}
    return {"dataset": label, "frozen_ticker_count": frozen, "total_ticker_count": total,
            "frozen_share": round(frozen / total, 3) if total else None,
            "representative": reps}


def main() -> int:
    report = {"columns": {}, "verdict": "", "note": (
        "Columns are valuable in theory but are REJECTED because the current files "
        "appear to contain a repeated point-in-time snapshot: per ticker the value is "
        "identical across all periods, so the column carries no historical T->T+1 signal.")}

    yearly = pd.read_csv(YEARLY_CSV) if YEARLY_CSV.is_file() else None
    if yearly is not None:
        yearly["ticker"] = yearly["ticker"].astype(str).str.upper()
    quarterly = _read_quarterly()

    all_frozen = True
    for canon, (ycol, qcol) in COLMAP.items():
        entry = {}
        if yearly is not None:
            a = _analyze(yearly, ycol, "yearly")
            if a:
                entry["yearly"] = a
                all_frozen &= a["frozen_ticker_count"] == a["total_ticker_count"]
        if quarterly is not None:
            b = _analyze(quarterly, qcol, "quarterly")
            if b:
                entry["quarterly"] = b
                all_frozen &= b["frozen_ticker_count"] == b["total_ticker_count"]
        if entry:
            report["columns"][canon] = entry

    report["verdict"] = (
        "ALL analyzed valuation/profitability/income-statement columns are FROZEN "
        "(one unique value per ticker across every period) in both the yearly and "
        "quarterly files. They cannot be used as historical features until the data "
        "provider supplies genuinely per-period values." if all_frozen else
        "Some columns vary across periods; see per-column detail.")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2))

    lines = ["# Frozen-column evidence (for the data provider)\n", report["note"], "",
             f"**Verdict:** {report['verdict']}\n",
             "| column | yearly frozen | quarterly frozen | ASELS unique vals (yearly) |",
             "|---|---|---|---|"]
    for canon, e in report["columns"].items():
        y = e.get("yearly", {})
        q = e.get("quarterly", {})
        asels = y.get("representative", {}).get("ASELS", {}).get("unique_values", "—")
        lines.append(f"| `{canon}` | {y.get('frozen_ticker_count','—')}/{y.get('total_ticker_count','—')} "
                     f"| {q.get('frozen_ticker_count','—')}/{q.get('total_ticker_count','—')} | {asels} |")
    lines += ["", "## Representative tickers (yearly values across years)", ""]
    for canon, e in report["columns"].items():
        reps = e.get("yearly", {}).get("representative", {})
        for t, info in reps.items():
            if info.get("unique_values") == 1:
                lines.append(f"- `{canon}` {t}: single value {info['values']} repeated every year → frozen")
    OUT_MD.write_text("\n".join(lines))
    print(f"[frozen-evidence] {report['verdict']}")
    print(f"[frozen-evidence] wrote {OUT_JSON.name} + {OUT_MD.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
