"""Clean the raw yfinance candidate CSV and produce a validated output.

Reads:
    data/trusted_raw/financials/bist100_yfinance_candidate.csv  (raw, may have nulls)

Writes:
    data/trusted_raw/financials/bist100_yfinance_candidate_clean.csv
    data/trusted_clean/bist100_yfinance_pilot_report.md

Cleaning rules (a row is KEPT if ALL of the following hold):
    - revenue is not null
    - net_income is not null
    - total_assets is not null
    - equity is not null
    - at least one of (roe, roa) is not null

Rows failing any rule are dropped and reported.

Run:
    PYTHONPATH=. python scripts/data_collection/clean_yfinance_candidate.py

    # Preview only (no writes):
    PYTHONPATH=. python scripts/data_collection/clean_yfinance_candidate.py --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_CSV = REPO_ROOT / "data" / "trusted_raw" / "financials" / "bist100_yfinance_candidate.csv"
CLEAN_CSV = REPO_ROOT / "data" / "trusted_raw" / "financials" / "bist100_yfinance_candidate_clean.csv"
REPORT_MD = REPO_ROOT / "data" / "trusted_clean" / "bist100_yfinance_pilot_report.md"

REQUIRED_COLS = ["revenue", "net_income", "total_assets", "equity"]
ROE_ROA_COLS = ["roe", "roa"]

DISCLAIMER = (
    "yfinance (unofficial Yahoo Finance) — NOT official KAP/IFRS data. "
    "KAP cross-check recommended (kap.borsaistanbul.com). "
    "Training use only. Not investment advice."
)


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (kept_df, dropped_df)."""
    core_ok = df[REQUIRED_COLS].notna().all(axis=1)
    ratios_ok = df[ROE_ROA_COLS].notna().any(axis=1)
    mask = core_ok & ratios_ok
    return df[mask].copy(), df[~mask].copy()


def build_report(raw: pd.DataFrame, kept: pd.DataFrame, dropped: pd.DataFrame) -> str:
    lines = [
        "# yfinance BIST100 Pilot — Data Quality Report",
        "",
        f"> {DISCLAIMER}",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Raw rows | {len(raw)} |",
        f"| Rows retained (clean) | {len(kept)} |",
        f"| Rows dropped | {len(dropped)} |",
        f"| Tickers in raw | {raw['ticker'].nunique()} |",
        f"| Tickers in clean | {kept['ticker'].nunique()} |",
        "",
    ]

    if not kept.empty:
        lines += [
            "## Retained tickers",
            "",
            "| Ticker | Years | revenue | net_income | total_assets | equity | roe | roa |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for ticker, grp in kept.groupby("ticker"):
            years = sorted(grp["year"].tolist())
            rev_ok = int(grp["revenue"].notna().sum())
            ni_ok = int(grp["net_income"].notna().sum())
            ta_ok = int(grp["total_assets"].notna().sum())
            eq_ok = int(grp["equity"].notna().sum())
            roe_ok = int(grp["roe"].notna().sum()) if "roe" in grp else 0
            roa_ok = int(grp["roa"].notna().sum()) if "roa" in grp else 0
            n = len(grp)
            lines.append(
                f"| {ticker} | {years} | {rev_ok}/{n} | {ni_ok}/{n} | {ta_ok}/{n} | {eq_ok}/{n} | {roe_ok}/{n} | {roa_ok}/{n} |"
            )
        lines.append("")

    if not dropped.empty:
        drop_reasons = []
        for _, row in dropped.iterrows():
            missing = [c for c in REQUIRED_COLS if pd.isna(row.get(c))]
            ratio_miss = all(pd.isna(row.get(c)) for c in ROE_ROA_COLS)
            reason_parts = []
            if missing:
                reason_parts.append(f"missing: {missing}")
            if ratio_miss:
                reason_parts.append("no roe/roa")
            drop_reasons.append(f"| {row['ticker']} | {row['year']} | {', '.join(reason_parts)} |")

        lines += [
            "## Dropped rows",
            "",
            "| Ticker | Year | Reason |",
            "|---|---|---|",
        ] + drop_reasons + [""]

    lines += [
        "## Field coverage (clean rows)",
        "",
    ]
    if not kept.empty:
        lines += ["| Column | Non-null rows | Total rows | Coverage |", "|---|---|---|---|"]
        numeric_cols = [c for c in kept.columns if c not in ("ticker", "year", "source", "retrieved_at", "_bank_warning")]
        for col in numeric_cols:
            if col in kept:
                nn = int(kept[col].notna().sum())
                total = len(kept)
                pct = f"{nn/total*100:.0f}%" if total else "—"
                lines.append(f"| {col} | {nn} | {total} | {pct} |")
        lines.append("")

    if not kept.empty:
        lines += [
            "## Year coverage per ticker (clean)",
            "",
        ]
        for ticker, grp in kept.groupby("ticker"):
            years = sorted(grp["year"].tolist())
            lines.append(f"- **{ticker}**: {years}")
        lines.append("")

    lines += [
        "## Caveats",
        "",
        "- yfinance is an unofficial scraper. Values may differ from KAP IFRS filings.",
        "- EBITDA is approximated as operating_income + depreciation where available.",
        "- FY2020 and FY2021 are typically unavailable for most BIST stocks via yfinance.",
        "- Bank tickers (is_bank=true in bist100_candidates.csv): revenue = net interest income;",
        "  gross_profit and EBITDA are undefined. Ratios not comparable with non-banks.",
        "- These rows are training-only. They never appear in frontend (public_40) endpoints.",
    ]

    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Print stats but do not write output.")
    ap.add_argument(
        "--raw-csv", type=Path, default=RAW_CSV,
        help=f"Input raw CSV (default: {RAW_CSV.relative_to(REPO_ROOT)})",
    )
    args = ap.parse_args(argv)

    raw_path = Path(args.raw_csv)
    if not raw_path.is_file():
        print(f"[clean] ERROR: {raw_path} not found. Run: make collect-yfinance-bist100", file=sys.stderr)
        return 1

    raw = pd.read_csv(raw_path)
    raw["ticker"] = raw["ticker"].astype(str).str.strip().str.upper()

    for col in REQUIRED_COLS + ROE_ROA_COLS:
        if col not in raw.columns:
            raw[col] = float("nan")

    print(f"[clean] Raw rows: {len(raw)} | Tickers: {raw['ticker'].nunique()}")

    kept, dropped = clean(raw)

    print(f"[clean] Retained: {len(kept)} rows | {kept['ticker'].nunique()} tickers")
    print(f"[clean] Dropped : {len(dropped)} rows")
    if not kept.empty:
        print(f"[clean] Tickers retained: {sorted(kept['ticker'].unique())}")
    if not dropped.empty:
        print(f"[clean] Dropped tickers (partial): {sorted(dropped['ticker'].unique())}")

    if kept.empty:
        print("[clean] ERROR: No rows passed quality filter. Check raw CSV for data.", file=sys.stderr)
        return 1

    if args.dry_run:
        print("[clean] --dry-run: no files written.")
        return 0

    CLEAN_CSV.parent.mkdir(parents=True, exist_ok=True)
    kept.to_csv(CLEAN_CSV, index=False)
    print(f"[clean] Wrote {len(kept)} clean rows → {CLEAN_CSV.relative_to(REPO_ROOT)}")

    report_md = build_report(raw, kept, dropped)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(report_md)
    print(f"[clean] Report → {REPORT_MD.relative_to(REPO_ROOT)}")

    print(f"\n{DISCLAIMER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
