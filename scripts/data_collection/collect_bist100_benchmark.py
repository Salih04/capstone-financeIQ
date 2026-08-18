"""Collect BIST100 (XU100.IS) yearly benchmark returns.

Source priority (no paid APIs, no leaked keys, never fabricated):
  1. Yahoo Finance daily history for XU100.IS (yfinance if installed, else the
     public chart JSON endpoint via stdlib urllib).
  2. Manual daily/monthly CSV at data/trusted_raw/bist100_daily.csv or
     bist100_historical.csv (flexible headers + Turkish number formats).
  3. Keep the template and report the benchmark as missing.

Yearly return for year Y = (last_close(Y) / first_close(Y) - 1) * 100, using
adjusted close when available. Output: data/trusted_raw/bist100_benchmark_returns.csv
(year,bist100_return_pct). Report: data/trusted_clean/bist100_benchmark_report.{json,md}

CLI: python -m scripts.data_collection.collect_bist100_benchmark [--start-year 2020]
     [--end-year 2025] [--manual-only] [--force]
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "trusted_raw"
CLEAN_DIR = REPO_ROOT / "data" / "trusted_clean"
OUT_CSV = RAW_DIR / "bist100_benchmark_returns.csv"
TEMPLATE_CSV = RAW_DIR / "bist100_benchmark_returns.template.csv"
MANUAL_DAILY = [RAW_DIR / "bist100_daily.csv", RAW_DIR / "bist100_historical.csv"]
REPORT_JSON = CLEAN_DIR / "bist100_benchmark_report.json"
REPORT_MD = CLEAN_DIR / "bist100_benchmark_report.md"
SYMBOL = "XU100.IS"

_DATE_ALIASES = ("date", "tarih", "datetime", "time")
_CLOSE_ALIASES = ("adj_close", "adjclose", "close", "şimdi", "simdi", "kapanış", "kapanis", "price", "fiyat")


def parse_tr_number(v) -> float | None:
    """Parse 10.628,60 / 10,628.60 / 10628.60 -> 10628.60. None if unparseable."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("₺", "").replace("%", "").replace(" ", "")
    if not s or s.lower() in ("na", "n/a", "nan", "-"):
        return None
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")   # 10.628,60 -> 10628.60
        else:
            s = s.replace(",", "")                      # 10,628.60 -> 10628.60
    elif "," in s:
        s = s.replace(",", ".") if len(s.split(",")[-1]) != 3 else s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def _relative_or_absolute(path: Path) -> str:
    """Serialize a path for the benchmark report.

    Repo-local paths become repo-relative POSIX text so the committed report
    stays relocatable and never embeds the absolute checkout location of
    whichever machine last ran the generator. A path that legitimately lives
    outside the repository keeps a usable absolute representation instead of
    raising, which a bare ``relative_to(REPO_ROOT)`` would do. Mirrors the
    convention in ``experiments/contamination_lab.py::_relative_or_absolute``.
    """
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _norm(c) -> str:
    return str(c).strip().lower().replace(" ", "_")


def fetch_yahoo(start_year: int, end_year: int, log: list) -> pd.DataFrame | None:
    p1 = int(datetime(start_year, 1, 1, tzinfo=timezone.utc).timestamp())
    p2 = int(datetime(end_year, 12, 31, 23, 59, tzinfo=timezone.utc).timestamp())

    try:
        import yfinance as yf  # noqa
        df = yf.download(SYMBOL, start=f"{start_year}-01-01", end=f"{end_year}-12-31",
                         progress=False, auto_adjust=False)
        if df is not None and len(df):
            col = "Adj Close" if "Adj Close" in df.columns else "Close"
            out = df[[col]].reset_index()
            out.columns = ["date", "close"]
            log.append("source=yfinance")
            return out
    except Exception as exc:  # noqa
        log.append(f"yfinance unavailable/failed: {exc}")

    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}"
           f"?period1={p1}&period2={p2}&interval=1d")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
        res = data["chart"]["result"][0]
        ts = res["timestamp"]
        ind = res["indicators"]
        closes = ind["quote"][0].get("close")
        adj = ind.get("adjclose", [{}])[0].get("adjclose") if ind.get("adjclose") else None
        df = pd.DataFrame({"date": pd.to_datetime(ts, unit="s"), "close": (adj or closes)}).dropna()
        if len(df):
            log.append("source=yahoo_chart_api")
            return df
    except Exception as exc:  # noqa
        log.append(f"yahoo chart API failed: {exc}")
    return None


def load_manual_daily(log: list) -> pd.DataFrame | None:
    for path in MANUAL_DAILY:
        if not path.is_file():
            continue
        try:
            df = pd.read_csv(path)
        except Exception as exc:  # noqa
            log.append(f"{path.name}: malformed ({exc})")
            continue
        cols = {_norm(c): c for c in df.columns}
        dcol = next((cols[a] for a in _DATE_ALIASES if a in cols), None)
        ccol = next((cols[a] for a in _CLOSE_ALIASES if a in cols), None)
        if not dcol or not ccol:
            log.append(f"{path.name}: need date+close columns; found {list(cols)}")
            continue
        out = pd.DataFrame({
            "date": pd.to_datetime(df[dcol], errors="coerce", dayfirst=True),
            "close": df[ccol].map(parse_tr_number),
        }).dropna()
        if len(out):
            log.append(f"source=manual:{path.name}")
            return out
    return None


def yearly_returns(daily: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    d = daily.copy()
    d["date"] = pd.to_datetime(d["date"])
    d["year"] = d["date"].dt.year
    d = d.sort_values("date")
    rows = []
    for y in range(start_year, end_year + 1):
        g = d[d["year"] == y]
        if len(g) < 2:
            continue
        first, last = float(g.iloc[0]["close"]), float(g.iloc[-1]["close"])
        if first > 0:
            rows.append({"year": y, "bist100_return_pct": round((last / first - 1) * 100, 2)})
    return pd.DataFrame(rows)


def validate(df: pd.DataFrame, start_year: int, end_year: int) -> list[str]:
    issues = []
    if df.empty:
        return ["no benchmark rows produced"]
    if df["year"].duplicated().any():
        issues.append("duplicate year rows")
    if df["bist100_return_pct"].isna().any():
        issues.append("null return values")
    missing = [y for y in range(start_year, end_year + 1) if y not in set(df["year"])]
    if missing:
        issues.append(f"missing years: {missing}")
    return issues


def ensure_template() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if not TEMPLATE_CSV.exists():
        TEMPLATE_CSV.write_text(
            "year,bist100_return_pct\n"
            "# Real BIST100 yearly total-return %, one row per year. Do not fabricate.\n"
        )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start-year", type=int, default=2020)
    ap.add_argument("--end-year", type=int, default=2025)
    ap.add_argument("--manual-only", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)

    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    ensure_template()
    log: list[str] = []

    daily = None if a.manual_only else fetch_yahoo(a.start_year, a.end_year, log)
    if daily is None:
        daily = load_manual_daily(log)

    if daily is None:
        msg = (
            "Yahoo unreachable and no manual file found. Provide ONE of:\n"
            f"   - {MANUAL_DAILY[0].name} or bist100_historical.csv under {RAW_DIR}\n"
            "     columns: date,close  (also Tarih/Şimdi, Tarih/Kapanış, Price/Close;\n"
            "     Turkish numbers like 10.628,60 handled)\n"
            f"   - {OUT_CSV.name} directly (year,bist100_return_pct)\n"
        )
        REPORT_JSON.write_text(json.dumps(
            {"source": "none", "years_covered": [], "returns": {}, "missing_years":
             list(range(a.start_year, a.end_year + 1)), "excess_targets_enabled": False,
             "issues": ["benchmark missing"], "log": log}, indent=2))
        REPORT_MD.write_text("# BIST100 benchmark\n\nMISSING.\n\n" + msg)
        print("[benchmark] MISSING. " + msg)
        return 1

    df = yearly_returns(daily, a.start_year, a.end_year).sort_values("year")
    issues = validate(df, a.start_year, a.end_year)
    if not df.empty:
        df.to_csv(OUT_CSV, index=False)

    source = next((l.split("source=")[1] for l in log if l.startswith("source=")), "unknown")
    report = {
        "source": source, "years_covered": df["year"].astype(int).tolist(),
        "returns": {int(y): float(r) for y, r in zip(df["year"], df["bist100_return_pct"])},
        "missing_years": [y for y in range(a.start_year, a.end_year + 1) if y not in set(df["year"])],
        "excess_targets_enabled": not df.empty, "issues": issues, "log": log, "output": _relative_or_absolute(OUT_CSV),
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, default=str))
    REPORT_MD.write_text(
        f"# BIST100 benchmark\n\n- Source: **{source}**\n- Years: {report['years_covered']}\n"
        f"- Returns: {report['returns']}\n- Missing: {report['missing_years']}\n"
        f"- Excess/outperform targets enabled: **{report['excess_targets_enabled']}**\n"
        f"- Issues: {issues or 'none'}\n")
    print(f"[benchmark] source={source} years={report['years_covered']} returns={report['returns']}")
    for i in issues:
        print(f"[benchmark] issue: {i}")
    print(f"[benchmark] wrote {OUT_CSV}")
    return 0 if not issues else 0


if __name__ == "__main__":
    sys.exit(main())
