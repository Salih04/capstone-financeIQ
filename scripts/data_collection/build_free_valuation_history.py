"""Free-data valuation builder: reconstruct missing valuation columns WITHOUT
Fintables Pro.

Targets (year T, 2020-2025, current 40 tickers):
    market_cap        = year_end_close * shares_outstanding
    pe                = market_cap / net_income       (reject if net_income <= 0)
    pb                = market_cap / equity           (reject if equity     <= 0)
    enterprise_value  = market_cap + net_debt
    ev_ebitda         = enterprise_value / ebitda     (reject if ebitda     <= 0)

Sources (all free / public, no Fintables, no aggressive scraping):
    year_end_close      Yahoo Finance chart API (TICKER.IS), cached to disk;
                        manual fallback CSV if Yahoo unavailable.
    shares_outstanding  manual file (data/trusted_raw/shares_outstanding_manual.csv);
                        a template is generated when missing. NOT fabricated.
    net_income/equity/  validated modeling dataset (already accepted, leakage-safe).
    ebitda/net_debt

Honesty rules:
    * No fabrication. Missing shares -> market_cap and all derived ratios are NULL
      for that ticker-year (validation_status=rejected, reason recorded).
    * The 2024 corrected export misaligns the balance-sheet block, so equity/net_debt
      for 2024 are treated as suspicious -> pb / enterprise_value / ev_ebitda for 2024
      are rejected, never imputed.
    * Price/return columns never become raw model features; only the derived year-T
      valuation ratios are candidates.

Outputs:
    data/trusted_raw/prices/yahoo_year_end_prices.csv            (cache)
    data/trusted_raw/shares_outstanding_manual_template.csv      (if manual missing)
    data/trusted_raw/financials/free_valuation_history_candidate.csv
    data/trusted_clean/free_valuation_history_report.{json,md}

Run:
    PYTHONPATH=. python -m scripts.data_collection.build_free_valuation_history [--prices-only]
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW = REPO_ROOT / "data" / "trusted_raw"
CLEAN = REPO_ROOT / "data" / "trusted_clean"
MODELING_CSV = CLEAN / "modeling_dataset_2020_2025.csv"
PRICES_CACHE = RAW / "prices" / "yahoo_year_end_prices.csv"
PRICES_MANUAL = RAW / "prices" / "year_end_prices_manual.csv"
SHARES_MANUAL = RAW / "shares_outstanding_manual.csv"
SHARES_TEMPLATE = RAW / "shares_outstanding_manual_template.csv"
CANDIDATE = RAW / "financials" / "free_valuation_history_candidate.csv"
REPORT_JSON = CLEAN / "free_valuation_history_report.json"
REPORT_MD = CLEAN / "free_valuation_history_report.md"

YEARS = list(range(2020, 2026))
PE_ABS_MAX, PB_ABS_MAX, EV_EBITDA_ABS_MAX = 1000.0, 100.0, 500.0
TARGET_COLS = ["market_cap", "enterprise_value", "pe", "pb", "ev_ebitda"]


# --------------------------------------------------------------------------- #
def yahoo_symbol(ticker: str) -> str:
    """BIST ticker -> Yahoo symbol (THYAO -> THYAO.IS)."""
    t = str(ticker).strip().upper()
    return t if t.endswith(".IS") else f"{t}.IS"


def _tickers() -> list[str]:
    if not MODELING_CSV.is_file():
        return []
    df = pd.read_csv(MODELING_CSV, usecols=["ticker"])
    return sorted(df["ticker"].astype(str).str.upper().unique())


def _fetch_yahoo_daily(symbol: str, timeout: float = 8.0) -> pd.DataFrame | None:
    """Daily close 2020-01-01..2025-12-31 from Yahoo chart API. None on failure."""
    p1 = int(pd.Timestamp("2019-12-15").timestamp())
    p2 = int(pd.Timestamp("2026-01-15").timestamp())
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           f"?period1={p1}&period2={p2}&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode())
        res = data["chart"]["result"][0]
        ts = res["timestamp"]
        quote = res["indicators"]["quote"][0]
        closes = quote.get("close", [])
        adj = None
        if "adjclose" in res["indicators"]:
            adj = res["indicators"]["adjclose"][0].get("adjclose")
        out = pd.DataFrame({
            "date": pd.to_datetime(ts, unit="s"),
            "close": closes,
            "adjclose": adj if adj is not None else closes,
        }).dropna(subset=["close"])
        return out
    except Exception:
        return None


def collect_year_end_prices(tickers: list[str], use_cache: bool = True,
                            log=print) -> tuple[pd.DataFrame, dict]:
    """One row per ticker-year: last trading close in the calendar year."""
    meta = {"attempted": 0, "yahoo_ok": 0, "from_cache": 0, "from_manual": 0, "failed": []}
    cache = None
    if use_cache and PRICES_CACHE.is_file():
        try:
            cache = pd.read_csv(PRICES_CACHE)
            cache["ticker"] = cache["ticker"].astype(str).str.upper()
        except Exception:
            cache = None
    manual = None
    if PRICES_MANUAL.is_file():
        try:
            manual = pd.read_csv(PRICES_MANUAL, comment="#")
            manual["ticker"] = manual["ticker"].astype(str).str.upper()
        except Exception:
            manual = None

    rows = []
    for t in tickers:
        # cache first (already-collected, avoids hammering Yahoo / 429s)
        if cache is not None and (cache["ticker"] == t).any():
            for _, r in cache[cache["ticker"] == t].iterrows():
                rows.append({"ticker": t, "year": int(r["year"]),
                             "year_end_close": _num(r.get("year_end_close")),
                             "date": r.get("date"), "source": r.get("source", "cache")})
            meta["from_cache"] += 1
            continue
        meta["attempted"] += 1
        daily = _fetch_yahoo_daily(yahoo_symbol(t))
        time.sleep(0.4)  # polite spacing, never hammer
        if daily is not None and len(daily):
            meta["yahoo_ok"] += 1
            daily["year"] = daily["date"].dt.year
            for y in YEARS:
                yr = daily[daily["year"] == y]
                if yr.empty:
                    continue
                last = yr.sort_values("date").iloc[-1]
                px = last.get("adjclose") if pd.notna(last.get("adjclose")) else last.get("close")
                rows.append({"ticker": t, "year": y, "year_end_close": _num(px),
                             "date": str(last["date"].date()), "source": "yahoo_chart_api"})
        elif manual is not None and (manual["ticker"] == t).any():
            for _, r in manual[manual["ticker"] == t].iterrows():
                rows.append({"ticker": t, "year": int(r["year"]),
                             "year_end_close": _num(r.get("year_end_close")),
                             "date": r.get("date"), "source": "manual"})
            meta["from_manual"] += 1
        else:
            meta["failed"].append(t)

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.drop_duplicates(["ticker", "year"], keep="last")
        df = df[(pd.to_numeric(df["year_end_close"], errors="coerce") > 0)]
        PRICES_CACHE.parent.mkdir(parents=True, exist_ok=True)
        df.sort_values(["ticker", "year"]).to_csv(PRICES_CACHE, index=False)
    log(f"[prices] tickers={len(tickers)} yahoo_ok={meta['yahoo_ok']} cache={meta['from_cache']} "
        f"manual={meta['from_manual']} failed={len(meta['failed'])} rows={len(df)}")
    return df, meta


def _num(v):
    try:
        return None if v is None or (isinstance(v, float) and np.isnan(v)) else round(float(v), 6)
    except (TypeError, ValueError):
        return None


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


# --------------------------------------------------------------------------- #
def ensure_shares_template(tickers: list[str]) -> bool:
    """Write a manual shares template (per ticker-year) if the real manual file is
    absent. The preferred workflow is the capital-EVENT file (fewer rows); this
    full template stays as a fallback. Returns True if a real manual file exists."""
    if SHARES_MANUAL.is_file():
        return True
    SHARES_TEMPLATE.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Manual shares-outstanding fallback (per ticker-year). NEVER fabricate.",
        "# PREFERRED: use the capital-EVENT file instead "
        "(data/trusted_raw/shares_outstanding_events.csv) and run `make shares`.",
        "# shares_outstanding MUST be TOTAL issued/paid-in shares, NOT free float.",
        "# A stable share count may repeat across years — document it in 'notes'.",
        "# capital_basis: issued_capital | paid_in_capital | share_count | unknown | free_float_only",
        "ticker,year,shares_outstanding,source,notes,confidence,capital_basis,nominal_value",
    ]
    for t in tickers:
        for y in YEARS:
            lines.append(f"{t},{y},,,,,issued_capital,1")
    SHARES_TEMPLATE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return False


def load_shares() -> tuple[pd.DataFrame | None, str]:
    """Load TOTAL shares outstanding. free_float_only rows are rejected (free float
    is not total shares and would understate market cap)."""
    if not SHARES_MANUAL.is_file():
        return None, "missing"
    try:
        df = pd.read_csv(SHARES_MANUAL, comment="#")
        df["ticker"] = df["ticker"].astype(str).str.upper()
        df["shares_outstanding"] = pd.to_numeric(df["shares_outstanding"], errors="coerce")
        if "capital_basis" in df.columns:
            df = df[df["capital_basis"].astype(str).str.lower() != "free_float_only"]
        df = df.dropna(subset=["shares_outstanding"])
        df = df[df["shares_outstanding"] > 0]
        if df.empty:
            return None, "empty"
        return df[["ticker", "year", "shares_outstanding"]], "manual"
    except Exception:
        return None, "unreadable"


def _load_financials() -> pd.DataFrame:
    """net_income, equity, ebitda, net_debt from the validated modeling dataset."""
    cols = ["ticker", "year", "net_income", "equity", "ebitda", "net_debt"]
    df = pd.read_csv(MODELING_CSV)
    have = [c for c in cols if c in df.columns]
    f = df[have].copy()
    f["ticker"] = f["ticker"].astype(str).str.upper()
    for c in ("net_income", "equity", "ebitda", "net_debt"):
        if c in f.columns:
            f[c] = pd.to_numeric(f[c], errors="coerce")
        else:
            f[c] = np.nan
    return f


# --------------------------------------------------------------------------- #
def build(log=print) -> dict:
    tickers = _tickers()
    prices, price_meta = collect_year_end_prices(tickers, log=log)
    # If the per-year manual file is missing but a capital-EVENT file exists, expand
    # events -> manual first (the user-friendly path: enter changes, not 240 rows).
    events = RAW / "shares_outstanding_events.csv"
    if not SHARES_MANUAL.is_file() and events.is_file():
        try:
            from scripts.data_collection import expand_shares_outstanding_events as EXP
            EXP.expand(log=log)
        except Exception as exc:  # noqa - never crash valuation on expansion error
            log(f"[valuation] event expansion failed: {exc}")
    have_shares = ensure_shares_template(tickers)
    shares, shares_status = load_shares()
    fin = _load_financials()

    base = pd.DataFrame([(t, y) for t in tickers for y in YEARS], columns=["ticker", "year"])
    base = base.merge(prices[["ticker", "year", "year_end_close", "source"]].rename(columns={"source": "source_price"}),
                      on=["ticker", "year"], how="left") if not prices.empty else base.assign(year_end_close=np.nan, source_price=None)
    if shares is not None:
        base = base.merge(shares, on=["ticker", "year"], how="left")
        base["source_shares"] = np.where(base["shares_outstanding"].notna(), "manual", None)
    else:
        base["shares_outstanding"] = np.nan
        base["source_shares"] = None
    base = base.merge(fin, on=["ticker", "year"], how="left")

    rows, rejections = [], {c: {} for c in TARGET_COLS}

    def rej(col, reason):
        rejections[col][reason] = rejections[col].get(reason, 0) + 1

    for _, r in base.iterrows():
        y = int(r["year"])
        px, sh = _num(r.get("year_end_close")), _num(r.get("shares_outstanding"))
        ni, eq, eb, nd = (_num(r.get("net_income")), _num(r.get("equity")),
                          _num(r.get("ebitda")), _num(r.get("net_debt")))
        notes = []
        mc = pe = pb = ev = ev_ebitda = None

        if px is None:
            rej("market_cap", "missing_price"); notes.append("missing_price")
        if sh is None:
            rej("market_cap", "missing_shares"); notes.append("missing_shares")
        if px is not None and sh is not None:
            mc = round(px * sh, 4)
            if mc <= 0:
                mc = None; rej("market_cap", "non_positive"); notes.append("market_cap_non_positive")

        # 2024 balance-sheet block is misaligned -> distrust equity/net_debt for 2024
        bs_2024_suspect = (y == 2024)

        if mc is not None:
            # P/E
            if ni is None:
                rej("pe", "missing_net_income")
            elif ni <= 0:
                rej("pe", "non_positive_net_income"); notes.append("pe_non_positive_net_income")
            else:
                pe = round(mc / ni, 4)
                if abs(pe) > PE_ABS_MAX:
                    pe = None; rej("pe", "absurd_value"); notes.append("pe_absurd")
            # P/B
            if eq is None:
                rej("pb", "missing_equity")
            elif bs_2024_suspect:
                rej("pb", "suspect_2024_equity"); notes.append("pb_2024_suspect")
            elif eq <= 0:
                rej("pb", "non_positive_equity"); notes.append("pb_non_positive_equity")
            else:
                pb = round(mc / eq, 4)
                if abs(pb) > PB_ABS_MAX:
                    pb = None; rej("pb", "absurd_value"); notes.append("pb_absurd")
            # EV
            if nd is None:
                rej("enterprise_value", "missing_net_debt")
            elif bs_2024_suspect:
                rej("enterprise_value", "suspect_2024_net_debt"); notes.append("ev_2024_suspect")
            else:
                ev = round(mc + nd, 4)
                if ev <= 0:
                    notes.append("enterprise_value_non_positive")
            # EV/EBITDA
            if ev is not None:
                if eb is None:
                    rej("ev_ebitda", "missing_ebitda")
                elif eb <= 0:
                    rej("ev_ebitda", "non_positive_ebitda"); notes.append("ev_ebitda_non_positive_ebitda")
                else:
                    ev_ebitda = round(ev / eb, 4)
                    if abs(ev_ebitda) > EV_EBITDA_ABS_MAX:
                        ev_ebitda = None; rej("ev_ebitda", "absurd_value"); notes.append("ev_ebitda_absurd")
            else:
                rej("ev_ebitda", "missing_enterprise_value")

        status = "accepted" if mc is not None else "rejected"
        rows.append({
            "ticker": r["ticker"], "year": y,
            "market_cap": mc, "enterprise_value": ev, "pe": pe, "pb": pb, "ev_ebitda": ev_ebitda,
            "year_end_close": px, "shares_outstanding": sh,
            "source_price": r.get("source_price"), "source_shares": r.get("source_shares"),
            "source_financials": "modeling_dataset",
            "validation_status": status,
            "validation_notes": ";".join(notes) if notes else "",
        })

    cand = pd.DataFrame(rows)

    # Column-level acceptance: a target column enters the candidate only if it has
    # usable, year-varying values for most tickers (not all-null, not frozen).
    col_status, usable = {}, {}
    for c in TARGET_COLS:
        vals = pd.to_numeric(cand[c], errors="coerce")
        n_usable = int(vals.notna().sum())
        usable[c] = n_usable
        if n_usable == 0:
            col_status[c] = "missing"
            continue
        # frozen check: varies across years for >=50% of tickers that have values
        varying = cand.dropna(subset=[c]).groupby("ticker")[c].nunique()
        frozen_frac = float((varying <= 1).mean()) if len(varying) else 1.0
        col_status[c] = "accepted" if frozen_frac < 0.5 else "rejected_frozen"

    # The candidate CSV only carries target columns that are at least partially usable;
    # fully-missing columns are dropped so manual_ingest won't see empty noise.
    keep_targets = [c for c in TARGET_COLS if col_status[c] in ("accepted",)]
    out_cols = (["ticker", "year"] + keep_targets +
                ["year_end_close", "shares_outstanding", "source_price", "source_shares",
                 "source_financials", "validation_status", "validation_notes"])
    CANDIDATE.parent.mkdir(parents=True, exist_ok=True)
    cand[out_cols].to_csv(CANDIDATE, index=False)

    report = {
        "tickers_covered": len(tickers),
        "years_covered": YEARS,
        "price_coverage": {
            "rows_with_price": int(cand["year_end_close"].notna().sum()),
            "total_rows": int(len(cand)),
            "yahoo_meta": price_meta,
        },
        "shares_status": shares_status,
        "shares_template_path": _rel(SHARES_TEMPLATE) if not have_shares else None,
        "financial_dependency_coverage": {
            c: int(pd.to_numeric(base[c], errors="coerce").notna().sum())
            for c in ("net_income", "equity", "ebitda", "net_debt") if c in base.columns},
        "target_column_status": col_status,
        "usable_values_by_column": usable,
        "columns_entering_candidate": keep_targets,
        "rejection_summary": rejections,
        "coverage_by_year": {int(y): int((cand["year"] == y).sum()) for y in YEARS},
        "feature_count_before": 27,
        "feature_count_after_if_accepted": 27 + len(keep_targets),
        "candidate_csv": _rel(CANDIDATE),
        "limitations": (
            "Shares outstanding is the binding gap: without a real per-ticker-year share count "
            "(KAP/company reports), market_cap cannot be computed and all derived ratios stay null. "
            "Yahoo provides only year-end PRICE freely, not historical shares. 2024 equity/net_debt are "
            "misaligned and were rejected, not imputed."),
        "not_investment_advice": True,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, default=str))
    _write_md(report, have_shares)
    return report


def _write_md(r: dict, have_shares: bool) -> None:
    cs = r["target_column_status"]
    lines = [
        "# Free valuation history report", "",
        "Reconstruct missing valuation columns from FREE sources (no Fintables). "
        "Research/educational only — NOT investment advice.", "",
        f"- Tickers: **{r['tickers_covered']}**  Years: {r['years_covered'][0]}–{r['years_covered'][-1]}",
        f"- Year-end price rows: **{r['price_coverage']['rows_with_price']}/{r['price_coverage']['total_rows']}** "
        f"(Yahoo ok for {r['price_coverage']['yahoo_meta'].get('yahoo_ok', 0)} tickers)",
        f"- Shares outstanding: **{r['shares_status']}**"
        + (f"  → fill template `{r['shares_template_path']}`" if r.get("shares_template_path") else ""),
        "", "## Target valuation columns", "", "| column | formula | status | usable values |",
        "|---|---|---|---|",
        f"| market_cap | year_end_close × shares_outstanding | {cs['market_cap']} | {r['usable_values_by_column']['market_cap']} |",
        f"| pe | market_cap / net_income | {cs['pe']} | {r['usable_values_by_column']['pe']} |",
        f"| pb | market_cap / equity | {cs['pb']} | {r['usable_values_by_column']['pb']} |",
        f"| enterprise_value | market_cap + net_debt | {cs['enterprise_value']} | {r['usable_values_by_column']['enterprise_value']} |",
        f"| ev_ebitda | enterprise_value / ebitda | {cs['ev_ebitda']} | {r['usable_values_by_column']['ev_ebitda']} |",
        "", f"## Columns entering the model candidate", "",
        ", ".join(r["columns_entering_candidate"]) or "**none** (dependency missing)",
        "", "## Rejection summary", "",
    ]
    for col, reasons in r["rejection_summary"].items():
        if reasons:
            lines.append(f"- **{col}**: " + ", ".join(f"{k}={v}" for k, v in reasons.items()))
    lines += ["", "## Limitation", "", r["limitations"]]
    if not have_shares:
        lines += ["", "## ACTION REQUIRED",
                  "Provide real shares-outstanding (KAP/company reports) in "
                  "`data/trusted_raw/shares_outstanding_manual.csv`, then re-run `make valuation`. "
                  "Until then, valuation ratios cannot enter the model."]
    REPORT_MD.write_text("\n".join(lines))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prices-only", action="store_true", help="collect year-end prices + cache, then stop")
    a = ap.parse_args(argv)
    if a.prices_only:
        tickers = _tickers()
        _, meta = collect_year_end_prices(tickers)
        print(f"[prices-only] {json.dumps({k: v for k, v in meta.items() if k != 'failed'})}")
        return 0
    rep = build()
    print(f"[valuation] target_status={rep['target_column_status']}")
    print(f"[valuation] columns_entering_candidate={rep['columns_entering_candidate']}")
    print(f"[valuation] shares_status={rep['shares_status']} "
          f"price_rows={rep['price_coverage']['rows_with_price']}/{rep['price_coverage']['total_rows']}")
    print(f"[valuation] wrote {CANDIDATE.name}, {REPORT_JSON.name}, {REPORT_MD.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
