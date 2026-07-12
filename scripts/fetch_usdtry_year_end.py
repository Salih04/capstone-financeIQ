"""Fetch deterministic year-end USD/TRY closes from Yahoo Chart API.

Yahoo symbol ``TRY=X`` is quoted as Turkish lira per U.S. dollar.  Raw replies
are cached so reruns are offline and byte-stable unless ``--force`` is supplied.
Missing years are emitted with an error status; they are never interpolated.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import pandas as pd

from scripts.fetch_yahoo_chart_prices import HEADERS, fetch_with_backoff, find_year_end_price

ROOT = Path(__file__).resolve().parents[1]
MACRO_DIR = ROOT / "data" / "trusted_raw" / "macro"
RAW_DIR = MACRO_DIR / "yahoo_chart_raw"
OUTPUT = MACRO_DIR / "usdtry_year_end.csv"
SYMBOL = "TRY=X"


def _fetch_year(year: int, force: bool = False) -> dict:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_DIR / f"TRY_X_{year}.json"
    if raw_path.is_file() and not force:
        return json.loads(raw_path.read_text(encoding="utf-8"))

    period1 = int(dt.datetime(year, 12, 20, tzinfo=dt.timezone.utc).timestamp())
    period2 = int(dt.datetime(year + 1, 1, 10, tzinfo=dt.timezone.utc).timestamp())
    payload = fetch_with_backoff(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}",
        {
            "period1": period1,
            "period2": period2,
            "interval": "1d",
            "events": "history",
            "includeAdjustedClose": "true",
        },
        HEADERS,
    )
    raw_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return payload


def extract_row(payload: dict, year: int) -> dict:
    """Extract the last valid close on or before December 31."""
    result = (payload.get("chart", {}).get("result") or [None])[0]
    if result is None:
        error = payload.get("error") or payload.get("chart", {}).get("error") or "empty result"
        return {
            "year": year,
            "target_date": f"{year}-12-31",
            "price_date": None,
            "try_per_usd": None,
            "currency": None,
            "source": "yahoo_chart_api",
            "yahoo_symbol": SYMBOL,
            "status": "error",
            "error": str(error),
        }
    price_date, close, _adjusted, currency = find_year_end_price(result, year)
    return {
        "year": year,
        "target_date": f"{year}-12-31",
        "price_date": price_date,
        "try_per_usd": close,
        "currency": currency,
        "source": "yahoo_chart_api",
        "yahoo_symbol": SYMBOL,
        "status": "success" if close is not None else "error",
        "error": None if close is not None else "no valid close on or before year end",
    }


def run(start_year: int = 2020, end_year: int = 2025, force: bool = False) -> Path:
    if start_year > end_year:
        raise ValueError("start_year must not exceed end_year")
    rows = [extract_row(_fetch_year(year, force=force), year) for year in range(start_year, end_year + 1)]
    MACRO_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUTPUT, index=False, float_format="%.10f", lineterminator="\n")
    print(f"[usdtry] wrote {OUTPUT.relative_to(ROOT)} ({sum(r['status'] == 'success' for r in rows)}/{len(rows)} years)")
    return OUTPUT


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, default=2020)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    run(args.start_year, args.end_year, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
