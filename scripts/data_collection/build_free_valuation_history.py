"""Free-data valuation builder: reconstruct missing valuation columns WITHOUT
Fintables Pro.

Targets (year T, 2020-2025, current 40 tickers):
    market_cap        = year_end_close * shares_outstanding
    pe                = market_cap / net_income       (reject if net_income <= 0)
    pb                = market_cap / equity           (reject if equity     <= 0)
    enterprise_value  = market_cap + net_debt
    ev_ebitda         = enterprise_value / ebitda     (reject if ebitda     <= 0)

Sources (all free / public, no Fintables, no aggressive scraping):
    year_end_close      Yahoo Finance chart API (TICKER.IS).  Preferred source:
                        fetch_yahoo_chart_prices.py -> yahoo_year_end_prices.csv
                        (new format with status/close/price_date/yahoo_symbol).
                        Uses close (not adjclose) as the canonical price.
                        Falls back to old-format cache or fresh fetch if new
                        format is absent.
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
    * close is used as the price (not adjclose). adjclose is preserved in the new
      format CSV as reference but never mixed into price-based calculations.

Outputs:
    data/trusted_raw/prices/yahoo_year_end_prices.csv            (new-format cache)
    data/trusted_raw/shares_outstanding_manual_template.csv      (if manual missing)
    data/trusted_raw/financials/free_valuation_history_candidate.csv
    data/trusted_clean/free_valuation_history_report.{json,md}

Run:
    # Step 1 (one-time or refresh): fetch fresh Yahoo prices
    python scripts/fetch_yahoo_chart_prices.py --start-year 2020 --end-year 2025

    # Step 2: build valuation features
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
CORRECTED_BS_2024 = RAW / "financials" / "corrected_balance_sheet_2024.csv"
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


# --------------------------------------------------------------------------- #
# Internal new-format loader — called by collect_year_end_prices only.
# --------------------------------------------------------------------------- #
def _load_yahoo_prices_new_format(path: Path) -> tuple[pd.DataFrame | None, dict]:
    """Load from the new-format CSV (fetch_yahoo_chart_prices.py output).

    New format columns: ticker, yahoo_symbol, year, target_date, price_date,
    close, adjclose, currency, source, status, error.

    Returns (DataFrame with ticker/year/year_end_close/price_date/yahoo_symbol/
    price_source, meta dict) or (None, meta) if absent or old format.
    Uses close as the canonical price — never adjclose.
    """
    meta: dict = {
        "format": "none",
        "rows_loaded": 0,
        "success_rows": 0,
        "error_rows": 0,
        "rows_after_filter": 0,
    }
    if not path.is_file():
        return None, meta
    try:
        df = pd.read_csv(path)
    except Exception:
        return None, meta

    if "status" not in df.columns:
        meta["format"] = "old_format"
        return None, meta

    meta["format"] = "new_format"
    meta["rows_loaded"] = int(len(df))
    meta["success_rows"] = int((df["status"] == "success").sum())
    meta["error_rows"] = int((df["status"] != "success").sum())

    success = df[df["status"] == "success"].copy()
    success["ticker"] = success["ticker"].astype(str).str.upper().str.strip()
    success["year"] = pd.to_numeric(success["year"], errors="coerce")
    success["close"] = pd.to_numeric(success["close"], errors="coerce")
    success = success.dropna(subset=["year", "close"])
    success = success[success["close"] > 0]
    success["year"] = success["year"].astype(int)

    out = pd.DataFrame({
        "ticker": success["ticker"].values,
        "year": success["year"].values,
        "year_end_close": success["close"].round(6).values,
        "price_date": (success["price_date"].values
                       if "price_date" in success.columns else np.full(len(success), np.nan)),
        "yahoo_symbol": (success["yahoo_symbol"].values
                         if "yahoo_symbol" in success.columns
                         else np.full(len(success), np.nan)),
        "price_source": "yahoo_chart_api",
    })
    out = out.drop_duplicates(["ticker", "year"], keep="last")
    meta["rows_after_filter"] = int(len(out))
    return out, meta


# --------------------------------------------------------------------------- #
# Primary price loader — collect_year_end_prices is the single entry point.
# Tests monkeypatch this function directly; always call it from build().
# --------------------------------------------------------------------------- #
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
    """One row per ticker-year: last trading close in the calendar year.

    Priority:
    1. New-format CSV (fetch_yahoo_chart_prices.py) — uses close, not adjclose.
       Returns immediately if it covers the given tickers.
    2. Old-format cache (fallback, uses adjclose for compat).
    3. Fresh Yahoo API fetch.
    4. Manual fallback CSV.

    Returns DataFrame with ticker/year/year_end_close/price_date/yahoo_symbol/
    price_source columns, plus a meta dict.

    NOTE: tests monkeypatch this function directly. The new-format path is
    implemented here (not in build()) so monkeypatching continues to work.
    """
    meta: dict = {
        "format": "legacy",
        "attempted": 0, "yahoo_ok": 0, "from_cache": 0, "from_manual": 0,
        "failed": [],
        "rows_loaded": 0, "success_rows": 0, "error_rows": 0,
    }

    # ---- Try new-format CSV first ----
    if use_cache:
        new_df, new_meta = _load_yahoo_prices_new_format(PRICES_CACHE)
        if new_df is not None and not new_df.empty:
            tickers_upper = {str(t).upper() for t in tickers}
            matched = new_df[new_df["ticker"].isin(tickers_upper)].copy()
            if not matched.empty:
                meta.update({
                    "format": new_meta["format"],
                    "rows_loaded": new_meta["rows_loaded"],
                    "success_rows": new_meta["success_rows"],
                    "error_rows": new_meta["error_rows"],
                    "from_cache": int(matched["ticker"].nunique()),
                })
                log(f"[prices] new-format CSV: loaded={new_meta['rows_loaded']} "
                    f"success={new_meta['success_rows']} error={new_meta['error_rows']} "
                    f"usable_for_tickers={len(matched)}")
                return matched.reset_index(drop=True), meta

    # ---- Old-format cache or fresh fetch fallback ----
    cache = None
    if use_cache and PRICES_CACHE.is_file():
        try:
            c = pd.read_csv(PRICES_CACHE)
            if "status" not in c.columns:   # old format only
                cache = c
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
        t_up = str(t).upper()
        if cache is not None and (cache["ticker"] == t_up).any():
            for _, r in cache[cache["ticker"] == t_up].iterrows():
                rows.append({"ticker": t_up, "year": int(r["year"]),
                             "year_end_close": _num(r.get("year_end_close")),
                             "price_date": r.get("date"),
                             "yahoo_symbol": yahoo_symbol(t_up),
                             "price_source": r.get("source", "cache")})
            meta["from_cache"] += 1
            continue
        meta["attempted"] += 1
        daily = _fetch_yahoo_daily(yahoo_symbol(t_up))
        time.sleep(0.4)
        if daily is not None and len(daily):
            meta["yahoo_ok"] += 1
            daily["year"] = daily["date"].dt.year
            for y in YEARS:
                yr = daily[daily["year"] == y]
                if yr.empty:
                    continue
                last = yr.sort_values("date").iloc[-1]
                # legacy collector uses adjclose for historical compat
                px = last.get("adjclose") if pd.notna(last.get("adjclose")) else last.get("close")
                rows.append({"ticker": t_up, "year": y, "year_end_close": _num(px),
                             "price_date": str(last["date"].date()),
                             "yahoo_symbol": yahoo_symbol(t_up),
                             "price_source": "yahoo_chart_api"})
        elif manual is not None and (manual["ticker"] == t_up).any():
            for _, r in manual[manual["ticker"] == t_up].iterrows():
                rows.append({"ticker": t_up, "year": int(r["year"]),
                             "year_end_close": _num(r.get("year_end_close")),
                             "price_date": r.get("date"),
                             "yahoo_symbol": yahoo_symbol(t_up),
                             "price_source": "manual"})
            meta["from_manual"] += 1
        else:
            meta["failed"].append(t_up)

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.drop_duplicates(["ticker", "year"], keep="last")
        df = df[pd.to_numeric(df["year_end_close"], errors="coerce") > 0]

    log(f"[prices] legacy: tickers={len(tickers)} yahoo_ok={meta['yahoo_ok']} "
        f"cache={meta['from_cache']} manual={meta['from_manual']} "
        f"failed={len(meta['failed'])} rows={len(df)}")
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


def load_corrected_bs_2024() -> set[str]:
    if not CORRECTED_BS_2024.is_file():
        return set()
    try:
        df = pd.read_csv(CORRECTED_BS_2024, comment="#")
    except Exception:
        return set()
    df.columns = [str(c).strip().lower() for c in df.columns]
    if not {"ticker", "year", "equity", "net_debt"}.issubset(df.columns):
        return set()
    df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()
    df = df[pd.to_numeric(df["year"], errors="coerce") == 2024]
    eq = pd.to_numeric(df["equity"], errors="coerce")
    nd = pd.to_numeric(df["net_debt"], errors="coerce")
    ok = eq.notna() & nd.notna() & (eq.abs() >= 1000)
    return set(df.loc[ok, "ticker"])


def _load_financials() -> pd.DataFrame:
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
    if CORRECTED_BS_2024.is_file():
        try:
            c = pd.read_csv(CORRECTED_BS_2024, comment="#")
            c.columns = [str(x).strip().lower() for x in c.columns]
            c["ticker"] = c["ticker"].astype(str).str.upper().str.strip()
            c = c[pd.to_numeric(c["year"], errors="coerce") == 2024]
            for fld in ("equity", "net_debt"):
                if fld in c.columns:
                    m = {t: v for t, v in zip(c["ticker"], pd.to_numeric(c[fld], errors="coerce"))
                         if pd.notna(v) and abs(v) >= 1000}
                    mask = (f["year"] == 2024) & f["ticker"].isin(m)
                    f.loc[mask, fld] = f.loc[mask, "ticker"].map(m)
        except Exception:
            pass
    return f


# --------------------------------------------------------------------------- #
def build(log=print) -> dict:
    tickers = _tickers()
    prices, price_meta = collect_year_end_prices(tickers, log=log)

    # Expand capital events -> shares if needed
    events = RAW / "shares_outstanding_events.csv"
    if not SHARES_MANUAL.is_file() and events.is_file():
        try:
            from scripts.data_collection import expand_shares_outstanding_events as EXP
            EXP.expand(log=log)
        except Exception as exc:
            log(f"[valuation] event expansion failed: {exc}")

    have_shares = ensure_shares_template(tickers)
    shares, shares_status = load_shares()
    fin = _load_financials()
    corrected_bs_2024 = load_corrected_bs_2024()

    # Build base ticker-year grid
    base = pd.DataFrame([(t, y) for t in tickers for y in YEARS], columns=["ticker", "year"])

    # Merge prices
    price_merge_cols = ["ticker", "year", "year_end_close", "price_source", "price_date", "yahoo_symbol"]
    avail_price_cols = [c for c in price_merge_cols if c in prices.columns] if not prices.empty else []
    if avail_price_cols:
        base = base.merge(prices[avail_price_cols], on=["ticker", "year"], how="left")
    else:
        for c in ["year_end_close", "price_source", "price_date", "yahoo_symbol"]:
            base[c] = np.nan

    # Legacy: old prices frame may have 'source' instead of 'price_source'
    if "price_source" not in base.columns and "source" in (prices.columns if not prices.empty else []):
        base = base.merge(prices[["ticker", "year", "source"]].rename(
            columns={"source": "price_source"}), on=["ticker", "year"], how="left")

    # Merge shares
    if shares is not None:
        base = base.merge(shares, on=["ticker", "year"], how="left")
        base["source_shares"] = np.where(base["shares_outstanding"].notna(), "manual", None)
    else:
        base["shares_outstanding"] = np.nan
        base["source_shares"] = None

    # Merge financials
    base = base.merge(fin, on=["ticker", "year"], how="left")

    # Compute valuation
    rows, rejections = [], {c: {} for c in TARGET_COLS}

    def rej(col, reason):
        rejections[col][reason] = rejections[col].get(reason, 0) + 1

    missing_no_price: list[str] = []
    missing_no_shares: list[str] = []

    for _, r in base.iterrows():
        t, y = str(r["ticker"]), int(r["year"])
        px = _num(r.get("year_end_close"))
        sh = _num(r.get("shares_outstanding"))
        ni, eq, eb, nd = (_num(r.get("net_income")), _num(r.get("equity")),
                          _num(r.get("ebitda")), _num(r.get("net_debt")))
        notes = []
        mc = pe = pb = ev = ev_ebitda = None

        if px is None:
            rej("market_cap", "missing_price")
            notes.append("missing_price")
            missing_no_price.append(f"{t}/{y}")
        if sh is None:
            rej("market_cap", "missing_shares")
            notes.append("missing_shares")
            if px is not None:
                missing_no_shares.append(f"{t}/{y}")
        if px is not None and sh is not None:
            mc = round(px * sh, 4)
            if mc <= 0:
                mc = None
                rej("market_cap", "non_positive")
                notes.append("market_cap_non_positive")

        # 2024 balance-sheet block is suspected misaligned unless manually corrected
        bs_2024_suspect = (y == 2024) and (r["ticker"] not in corrected_bs_2024)

        if mc is not None:
            # P/E
            if ni is None:
                rej("pe", "missing_net_income")
            elif ni <= 0:
                rej("pe", "non_positive_net_income")
                notes.append("pe_non_positive_net_income")
            else:
                pe = round(mc / ni, 4)
                if abs(pe) > PE_ABS_MAX:
                    pe = None
                    rej("pe", "absurd_value")
                    notes.append("pe_absurd")
            # P/B
            if eq is None:
                rej("pb", "missing_equity")
            elif bs_2024_suspect:
                rej("pb", "suspect_2024_equity")
                notes.append("pb_2024_suspect")
            elif eq <= 0:
                rej("pb", "non_positive_equity")
                notes.append("pb_non_positive_equity")
            else:
                pb = round(mc / eq, 4)
                if abs(pb) > PB_ABS_MAX:
                    pb = None
                    rej("pb", "absurd_value")
                    notes.append("pb_absurd")
            # EV
            if nd is None:
                rej("enterprise_value", "missing_net_debt")
            elif bs_2024_suspect:
                rej("enterprise_value", "suspect_2024_net_debt")
                notes.append("ev_2024_suspect")
            else:
                ev = round(mc + nd, 4)
                if ev <= 0:
                    notes.append("enterprise_value_non_positive")
            # EV/EBITDA
            if ev is not None:
                if eb is None:
                    rej("ev_ebitda", "missing_ebitda")
                elif eb <= 0:
                    rej("ev_ebitda", "non_positive_ebitda")
                    notes.append("ev_ebitda_non_positive_ebitda")
                else:
                    ev_ebitda = round(ev / eb, 4)
                    if abs(ev_ebitda) > EV_EBITDA_ABS_MAX:
                        ev_ebitda = None
                        rej("ev_ebitda", "absurd_value")
                        notes.append("ev_ebitda_absurd")
            else:
                rej("ev_ebitda", "missing_enterprise_value")

        status = "accepted" if mc is not None else "rejected"
        rows.append({
            "ticker": r["ticker"], "year": y,
            "market_cap": mc, "enterprise_value": ev, "pe": pe, "pb": pb, "ev_ebitda": ev_ebitda,
            "year_end_close": px, "shares_outstanding": sh,
            "price_source": r.get("price_source"),
            "price_date": r.get("price_date"),
            "yahoo_symbol": r.get("yahoo_symbol"),
            "source_shares": r.get("source_shares"),
            "source_financials": "modeling_dataset",
            "validation_status": status,
            "validation_notes": ";".join(notes) if notes else "",
        })

    cand = pd.DataFrame(rows)

    # Column-level acceptance
    col_status, usable = {}, {}
    for c in TARGET_COLS:
        vals = pd.to_numeric(cand[c], errors="coerce")
        n_usable = int(vals.notna().sum())
        usable[c] = n_usable
        if n_usable == 0:
            col_status[c] = "missing"
            continue
        varying = cand.dropna(subset=[c]).groupby("ticker")[c].nunique()
        frozen_frac = float((varying <= 1).mean()) if len(varying) else 1.0
        col_status[c] = "accepted" if frozen_frac < 0.5 else "rejected_frozen"

    keep_targets = [c for c in TARGET_COLS if col_status[c] == "accepted"]
    out_cols = (["ticker", "year"] + keep_targets +
                ["year_end_close", "shares_outstanding",
                 "price_source", "price_date", "yahoo_symbol",
                 "source_shares", "source_financials",
                 "validation_status", "validation_notes"])
    CANDIDATE.parent.mkdir(parents=True, exist_ok=True)
    cand[out_cols].to_csv(CANDIDATE, index=False)

    # Dedup missing lists for report
    missing_no_price_uniq = sorted(set(missing_no_price))
    missing_no_shares_uniq = sorted(set(missing_no_shares))
    mc_ok = int(cand["market_cap"].notna().sum())
    ev_ok = int(cand["enterprise_value"].notna().sum())
    pe_ok = int(cand["pe"].notna().sum())
    pb_ok = int(cand["pb"].notna().sum())
    ev_ebitda_ok = int(cand["ev_ebitda"].notna().sum())

    report = {
        "tickers_covered": len(tickers),
        "years_covered": YEARS,
        "price_coverage": {
            "format": price_meta.get("format", "unknown"),
            "yahoo_price_rows_loaded": price_meta.get("rows_loaded", price_meta.get("yahoo_ok", 0)),
            "yahoo_success_rows": price_meta.get("success_rows", price_meta.get("yahoo_ok", 0)),
            "yahoo_error_rows": price_meta.get("error_rows", len(price_meta.get("failed", []))),
            "rows_with_price": int(cand["year_end_close"].notna().sum()),
            "total_rows": int(len(cand)),
        },
        "valuation_coverage": {
            "successful_market_cap": mc_ok,
            "successful_enterprise_value": ev_ok,
            "successful_pe_ratio": pe_ok,
            "successful_pb_ratio": pb_ok,
            "successful_ev_ebitda": ev_ebitda_ok,
        },
        "missing_ticker_years": {
            "no_yahoo_price": missing_no_price_uniq,
            "no_yahoo_price_count": len(missing_no_price_uniq),
            "no_shares_outstanding": missing_no_shares_uniq,
            "no_shares_outstanding_count": len(missing_no_shares_uniq),
        },
        "shares_status": shares_status,
        "corrected_balance_sheet_2024": {
            "present": CORRECTED_BS_2024.is_file(),
            "tickers_corrected": len(corrected_bs_2024),
            "tickers": sorted(corrected_bs_2024),
        },
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
            "Yahoo provides year-end PRICE (close) freely; adjclose is also captured but not used for "
            "price-based calculations. 2024 equity/net_debt are misaligned and were rejected, not imputed."),
        "not_investment_advice": True,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, default=str))
    _write_md(report, have_shares)
    return report


def _write_md(r: dict, have_shares: bool) -> None:
    cs = r["target_column_status"]
    vc = r["valuation_coverage"]
    pc = r["price_coverage"]
    mt = r["missing_ticker_years"]
    lines = [
        "# Free valuation history report", "",
        "Reconstruct missing valuation columns from FREE sources (no Fintables). "
        "Research/educational only — NOT investment advice.", "",
        f"- Tickers: **{r['tickers_covered']}**  Years: {r['years_covered'][0]}–{r['years_covered'][-1]}",
        f"- Price CSV format: **{pc['format']}**",
        f"- Yahoo price rows loaded: **{pc['yahoo_price_rows_loaded']}**  "
        f"success: **{pc['yahoo_success_rows']}**  error: **{pc['yahoo_error_rows']}**",
        f"- Rows with price in grid: **{pc['rows_with_price']}/{pc['total_rows']}**",
        f"- Shares outstanding: **{r['shares_status']}**"
        + (f"  → fill template `{r['shares_template_path']}`" if r.get("shares_template_path") else ""),
        "", "## Valuation coverage", "",
        f"- successful market_cap: **{vc['successful_market_cap']}**",
        f"- successful enterprise_value: **{vc['successful_enterprise_value']}**",
        f"- successful pe_ratio: **{vc['successful_pe_ratio']}**",
        f"- successful pb_ratio: **{vc['successful_pb_ratio']}**",
        f"- successful ev_ebitda: **{vc['successful_ev_ebitda']}**",
        "",
        f"- missing ticker-years (no Yahoo price): **{mt['no_yahoo_price_count']}**",
        f"- missing ticker-years (no shares outstanding): **{mt['no_shares_outstanding_count']}**",
        "",
        "## Target valuation columns", "", "| column | formula | status | usable values |",
        "|---|---|---|---|",
        f"| market_cap | year_end_close × shares_outstanding | {cs['market_cap']} | {r['usable_values_by_column']['market_cap']} |",
        f"| pe | market_cap / net_income | {cs['pe']} | {r['usable_values_by_column']['pe']} |",
        f"| pb | market_cap / equity | {cs['pb']} | {r['usable_values_by_column']['pb']} |",
        f"| enterprise_value | market_cap + net_debt | {cs['enterprise_value']} | {r['usable_values_by_column']['enterprise_value']} |",
        f"| ev_ebitda | enterprise_value / ebitda | {cs['ev_ebitda']} | {r['usable_values_by_column']['ev_ebitda']} |",
        "", "## Columns entering the model candidate", "",
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
    ap.add_argument("--prices-only", action="store_true",
                    help="report price CSV status, then stop (no valuation build)")
    a = ap.parse_args(argv)
    if a.prices_only:
        tickers = _tickers()
        prices, meta = collect_year_end_prices(tickers, log=lambda *_: None)
        fmt = meta.get("format", "unknown")
        if fmt == "new_format":
            print(f"[prices-only] new-format CSV: loaded={meta['rows_loaded']} "
                  f"success={meta['success_rows']} error={meta['error_rows']} "
                  f"usable={len(prices)}")
        else:
            print(f"[prices-only] legacy format: "
                  f"{json.dumps({k: v for k, v in meta.items() if k != 'failed'})}")
        return 0
    rep = build()
    vc = rep["valuation_coverage"]
    pc = rep["price_coverage"]
    print(f"[valuation] target_status={rep['target_column_status']}")
    print(f"[valuation] columns_entering_candidate={rep['columns_entering_candidate']}")
    print(f"[valuation] price_format={pc['format']} "
          f"yahoo_success={pc['yahoo_success_rows']} yahoo_error={pc['yahoo_error_rows']} "
          f"rows_with_price={pc['rows_with_price']}/{pc['total_rows']}")
    print(f"[valuation] market_cap={vc['successful_market_cap']} "
          f"ev={vc['successful_enterprise_value']} "
          f"pe={vc['successful_pe_ratio']} pb={vc['successful_pb_ratio']} "
          f"ev_ebitda={vc['successful_ev_ebitda']}")
    print(f"[valuation] missing_no_price={rep['missing_ticker_years']['no_yahoo_price_count']} "
          f"missing_no_shares={rep['missing_ticker_years']['no_shares_outstanding_count']}")
    print(f"[valuation] wrote {CANDIDATE.name}, {REPORT_JSON.name}, {REPORT_MD.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
