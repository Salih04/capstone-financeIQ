"""Expand capital-EVENT rows into per-ticker-year shares outstanding (2020-2025).

Filling 240 ticker-year rows by hand is wasteful. Instead the user records only
capital EVENTS: one row per (ticker, effective_year) when issued/paid-in capital
changes. This script carries the latest event forward to each year.

Input (preferred): data/trusted_raw/shares_outstanding_events.csv
Fallback template:  data/trusted_raw/shares_outstanding_events_template.csv (generated)
Output:             data/trusted_raw/shares_outstanding_manual.csv
Reports:            data/trusted_clean/shares_outstanding_expansion_report.{json,md}

Honesty / correctness rules:
  * No fabrication. Only user-provided event values are carried forward.
  * shares_outstanding MUST be TOTAL issued/paid-in shares, NOT free-float.
    Rows with capital_basis=free_float_only are REJECTED for market_cap
    (rejected_free_float_not_total) — free float understates total shares.
  * A year with no prior event stays null (status=missing_prior_event).

Run: PYTHONPATH=. python -m scripts.data_collection.expand_shares_outstanding_events
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW = REPO_ROOT / "data" / "trusted_raw"
CLEAN = REPO_ROOT / "data" / "trusted_clean"
MODELING_CSV = CLEAN / "modeling_dataset_2020_2025.csv"
EVENTS = RAW / "shares_outstanding_events.csv"
EVENTS_TEMPLATE = RAW / "shares_outstanding_events_template.csv"
MANUAL_OUT = RAW / "shares_outstanding_manual.csv"
REPORT_JSON = CLEAN / "shares_outstanding_expansion_report.json"
REPORT_MD = CLEAN / "shares_outstanding_expansion_report.md"

YEARS = list(range(2020, 2026))
VALID_CONFIDENCE = {"high", "medium", "low"}
VALID_BASIS = {"issued_capital", "paid_in_capital", "share_count", "unknown", "free_float_only"}
EVENT_COLS = ["ticker", "effective_year", "shares_outstanding", "source",
              "notes", "confidence", "capital_basis", "nominal_value"]


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _tickers() -> list[str]:
    if not MODELING_CSV.is_file():
        return []
    return sorted(pd.read_csv(MODELING_CSV, usecols=["ticker"])["ticker"].astype(str).str.upper().unique())


def write_events_template(tickers: list[str]) -> None:
    EVENTS_TEMPLATE.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Capital-EVENT shares outstanding (free valuation). NEVER fabricate.",
        "# One row per capital CHANGE. Stable capital 2020-2025 = a single 2020 row.",
        "# shares_outstanding MUST be TOTAL issued/paid-in shares, NOT free float.",
        "# Do NOT use 'Fiili Dolasimdaki Pay Tutari' (free float) as total shares.",
        "# For BIST, paid-in capital in TL == share count when nominal_value = 1 TL (document it).",
        "# capital_basis: issued_capital | paid_in_capital | share_count | unknown | free_float_only",
        "# confidence: high | medium | low",
        "#",
        "# Example only, do NOT use as real data:",
        "# TICKER,2020,1000000000,KAP company general info,stable issued capital,medium,issued_capital,1",
        "# TICKER,2023,2000000000,KAP capital increase disclosure,post-increase,high,issued_capital,1",
        ",".join(EVENT_COLS),
    ]
    # one blank 2020 event row per ticker (values left empty — user fills real data)
    for t in tickers:
        lines.append(f"{t},2020,,,,,issued_capital,1")
    EVENTS_TEMPLATE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_events() -> tuple[pd.DataFrame | None, str, list[str]]:
    path = EVENTS if EVENTS.is_file() else (EVENTS_TEMPLATE if EVENTS_TEMPLATE.is_file() else None)
    issues: list[str] = []
    if path is None:
        return None, "missing", issues
    try:
        df = pd.read_csv(path, comment="#")
    except Exception as exc:
        return None, f"unreadable ({exc})", issues
    if df.empty:
        return None, "empty", issues
    df.columns = [c.strip().lower() for c in df.columns]
    df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()
    df["effective_year"] = pd.to_numeric(df.get("effective_year"), errors="coerce")
    df["shares_outstanding"] = pd.to_numeric(df.get("shares_outstanding"), errors="coerce")
    if "capital_basis" not in df.columns:
        df["capital_basis"] = "unknown"
    if "confidence" not in df.columns:
        df["confidence"] = ""
    if "nominal_value" not in df.columns:
        df["nominal_value"] = None
    df["capital_basis"] = df["capital_basis"].astype(str).str.strip().str.lower().replace({"": "unknown", "nan": "unknown"})
    df["confidence"] = df["confidence"].astype(str).str.strip().str.lower()
    return df, ("events" if path == EVENTS else "events_template"), issues


def expand(log=print) -> dict:
    tickers = _tickers()
    if not (EVENTS.is_file() or EVENTS_TEMPLATE.is_file()):
        write_events_template(tickers)
    events, src, issues = _load_events()

    rejected_free_float = 0
    valid_events = []
    if events is not None:
        seen = set()
        for _, r in events.iterrows():
            t, ey, sh = r["ticker"], r["effective_year"], r["shares_outstanding"]
            basis = r["capital_basis"]
            conf = r["confidence"]
            if basis == "free_float_only":
                rejected_free_float += 1
                continue  # never usable for total market cap
            if pd.isna(ey) or pd.isna(sh) or sh <= 0:
                continue  # blank/invalid -> skip (template rows / not yet filled)
            if basis not in VALID_BASIS:
                issues.append(f"{t}: invalid capital_basis '{basis}'")
                continue
            if conf and conf not in VALID_CONFIDENCE:
                issues.append(f"{t}: invalid confidence '{conf}'")
            key = (t, int(ey))
            if key in seen:
                issues.append(f"{t}: duplicate event for effective_year {int(ey)} (kept first)")
                continue
            seen.add(key)
            valid_events.append({"ticker": t, "effective_year": int(ey),
                                 "shares_outstanding": float(sh), "source": r.get("source", ""),
                                 "notes": r.get("notes", ""), "confidence": conf or "medium",
                                 "capital_basis": basis, "nominal_value": r.get("nominal_value")})

    ev_df = pd.DataFrame(valid_events, columns=["ticker", "effective_year", "shares_outstanding",
                                                "source", "notes", "confidence", "capital_basis", "nominal_value"])
    rows, filled, missing = [], 0, 0
    stable, multi = [], []
    counts = {t: int(len(g)) for t, g in ev_df.groupby("ticker")} if not ev_df.empty else {}

    for t in tickers:
        tev = ev_df[ev_df["ticker"] == t].sort_values("effective_year")
        for y in YEARS:
            prior = tev[tev["effective_year"] <= y]
            if prior.empty:
                rows.append({"ticker": t, "year": y, "shares_outstanding": None,
                             "source": "", "notes": "", "confidence": "",
                             "capital_basis": "", "nominal_value": None,
                             "status": "missing_prior_event"})
                missing += 1
            else:
                e = prior.iloc[-1]
                rows.append({"ticker": t, "year": y, "shares_outstanding": e["shares_outstanding"],
                             "source": e["source"], "notes": e["notes"], "confidence": e["confidence"],
                             "capital_basis": e["capital_basis"], "nominal_value": e["nominal_value"],
                             "status": "carried_forward"})
                filled += 1
        n = counts.get(t, 0)
        if n == 1:
            stable.append(t)
        elif n > 1:
            multi.append(t)

    out = pd.DataFrame(rows)
    MANUAL_OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(MANUAL_OUT, index=False)

    nominal_warn = []
    if not ev_df.empty:
        for _, e in ev_df.iterrows():
            nv = pd.to_numeric(pd.Series([e["nominal_value"]]), errors="coerce").iloc[0]
            if pd.isna(nv) or nv != 1:
                nominal_warn.append(f"{e['ticker']} ({e['capital_basis']}): nominal_value={e['nominal_value']} "
                                    "— share count from TL capital assumes nominal 1 TL; verify.")

    report = {
        "events_source": src,
        "event_rows_total": int(len(events)) if events is not None else 0,
        "event_rows_used": int(len(ev_df)),
        "ticker_year_rows_filled": filled,
        "ticker_year_rows_missing": missing,
        "tickers_total": len(tickers),
        "tickers_stable_carry_forward": stable,
        "tickers_multiple_events": multi,
        "rejected_free_float_only_rows": rejected_free_float,
        "nominal_value_warnings": nominal_warn,
        "issues": issues,
        "manual_out": _rel(MANUAL_OUT),
        "ready_for_valuation": filled > 0,
        "not_investment_advice": True,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, default=str))
    _write_md(report)
    log(f"[shares] events_used={len(ev_df)} filled={filled} missing={missing} "
        f"free_float_rejected={rejected_free_float} -> {MANUAL_OUT.name}")
    return report


def _write_md(r: dict) -> None:
    lines = [
        "# Shares outstanding expansion report", "",
        "Capital-EVENT workflow: enter only capital CHANGES; they are carried forward "
        "to each year. Research/educational only — NOT investment advice.", "",
        f"- Events source: `{r['events_source']}`  | event rows used: **{r['event_rows_used']}**",
        f"- Ticker-year rows filled: **{r['ticker_year_rows_filled']}** / "
        f"{r['ticker_year_rows_filled'] + r['ticker_year_rows_missing']}",
        f"- Tickers with stable carry-forward: {len(r['tickers_stable_carry_forward'])}",
        f"- Tickers with multiple capital events: {len(r['tickers_multiple_events'])}",
        f"- Free-float-only rows rejected (not total shares): **{r['rejected_free_float_only_rows']}**",
        f"- Ready for valuation: **{r['ready_for_valuation']}**", "",
        "## Why free float is rejected", "",
        "Market cap = year-end price × **total** shares outstanding. 'Fiili Dolasimdaki Pay "
        "Tutari' (free float) is only the publicly-traded portion and understates total shares, "
        "so it is rejected for market cap. Use issued / paid-in capital or total share count.", "",
    ]
    if r["nominal_value_warnings"]:
        lines += ["## Nominal-value warnings", ""] + [f"- {w}" for w in r["nominal_value_warnings"]] + [""]
    if r["issues"]:
        lines += ["## Issues", ""] + [f"- {i}" for i in r["issues"]]
    if not r["ready_for_valuation"]:
        lines += ["", "## ACTION REQUIRED",
                  f"Fill REAL capital events in `data/trusted_raw/shares_outstanding_events.csv` "
                  f"(copy from the generated template), then run `make shares && make valuation`."]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main(argv=None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    rep = expand()
    print(f"[shares] ready_for_valuation={rep['ready_for_valuation']} "
          f"filled={rep['ticker_year_rows_filled']} missing={rep['ticker_year_rows_missing']}")
    print(f"[shares] wrote {MANUAL_OUT.name}, {REPORT_JSON.name}, {REPORT_MD.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
