"""Fetch year-end daily close prices from Yahoo Finance Chart API.

Outputs:
    data/trusted_raw/prices/yahoo_year_end_prices.csv
    data/trusted_raw/prices/yahoo_year_end_prices_report.md
    data/trusted_raw/prices/yahoo_chart_raw/<SYMBOL>_<YEAR>.json  (raw cache)

Run:
    python scripts/fetch_yahoo_chart_prices.py --start-year 2020 --end-year 2025

The raw JSON cache is idempotent: existing files are reused (skip API call).
Use --force to refetch everything.

Retry policy:
    Transient errors (429, 500, 502, 503, 504): exponential backoff, up to 5 retries.
    Permanent errors (400, 401, 403, 404): no retry; write status=error immediately.
"""

import argparse
import datetime
import json
import logging
import time
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

DEFAULT_TICKERS = [
    "AEFES", "ARCLK", "ASTOR", "BRSAN", "BTCIM", "CANTE", "CCOLA", "CIMSA",
    "DOAS", "DSTKF", "ENKAI", "GUBRF", "HEKTS", "KONTR", "KRDMD", "KUYAS",
    "MAVI", "MGROS", "MIATK", "OYAKC", "PASEU", "PETKM", "PGSUS", "SASA",
    "TAVHL", "TRALT", "TRMET", "TSKB", "TURSG", "ULKER", "THYAO", "ASELS",
    "BIMAS", "EREGL", "FROTO", "TUPRS", "SISE", "TCELL", "TTKOM", "TOASO",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    )
}

# Transient status codes that warrant a retry with backoff.
_TRANSIENT = {429, 500, 502, 503, 504}
# Permanent status codes: do not retry.
_PERMANENT = {400, 401, 403, 404}


def fetch_with_backoff(url, params, headers, max_retries=5):
    """Fetch URL with exponential backoff for transient errors only.

    Returns parsed JSON dict, or a dict with an "error" key on permanent
    failure.  Never retries 400/401/403/404 (permanent).
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)

            if response.status_code == 200:
                return response.json()

            if response.status_code in _PERMANENT:
                # Extract Yahoo error message if available
                try:
                    body = response.json()
                    msg = (body.get("chart", {}).get("error", {}) or {}).get(
                        "description", ""
                    )
                except Exception:
                    msg = ""
                err = f"HTTP {response.status_code}" + (f": {msg}" if msg else "")
                return {"error": err}

            if response.status_code in _TRANSIENT:
                logging.warning(
                    f"Transient error {response.status_code}. "
                    f"Retry {attempt + 1}/{max_retries}..."
                )
            else:
                logging.warning(
                    f"Unexpected status {response.status_code}. "
                    f"Retry {attempt + 1}/{max_retries}..."
                )

        except requests.exceptions.RequestException as e:
            logging.warning(f"Request exception: {e}. Retry {attempt + 1}/{max_retries}...")

        time.sleep(2 ** attempt)  # 1s, 2s, 4s, 8s, 16s

    return {"error": "Max retries reached (transient failures)"}


def find_year_end_price(result, target_year):
    """Return (price_date, close, adjclose, currency) for the last trading day
    in target_year on or before Dec 31.  All None on failure."""
    timestamps = result.get("timestamp", [])
    if not timestamps:
        return None, None, None, None

    quote = result.get("indicators", {}).get("quote", [{}])[0]
    closes = quote.get("close", [])
    adjclose_dict = result.get("indicators", {}).get("adjclose", [{}])[0]
    adjcloses = adjclose_dict.get("adjclose", [])
    currency = result.get("meta", {}).get("currency")

    target_date = datetime.date(target_year, 12, 31)
    best_idx, best_date = -1, None

    for i, ts in enumerate(timestamps):
        dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).date()
        if dt <= target_date and i < len(closes) and closes[i] is not None:
            if best_date is None or dt > best_date:
                best_date = dt
                best_idx = i

    if best_idx == -1:
        return None, None, None, currency

    c = closes[best_idx]
    ac = adjcloses[best_idx] if best_idx < len(adjcloses) else c
    return best_date.strftime("%Y-%m-%d"), c, ac, currency


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, required=True)
    parser.add_argument("--end-year", type=int, required=True)
    parser.add_argument("--tickers", type=str, nargs="+", default=DEFAULT_TICKERS)
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing raw JSON cache files")
    args = parser.parse_args()

    raw_dir = Path("data/trusted_raw/prices/yahoo_chart_raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_dir = Path("data/trusted_raw/prices")
    csv_path = output_dir / "yahoo_year_end_prices.csv"
    report_path = output_dir / "yahoo_year_end_prices_report.md"

    results = []
    success_count = fail_count = skipped_count = 0

    for year in range(args.start_year, args.end_year + 1):
        for ticker in args.tickers:
            symbol = f"{ticker}.IS"
            json_file = raw_dir / f"{symbol}_{year}.json"

            raw_data = None
            if json_file.exists() and not args.force:
                try:
                    raw_data = json.loads(json_file.read_text(encoding="utf-8"))
                    skipped_count += 1
                except Exception:
                    pass

            if raw_data is None:
                p1 = int(datetime.datetime(year, 12, 20, tzinfo=datetime.timezone.utc).timestamp())
                p2 = int(datetime.datetime(year + 1, 1, 10, tzinfo=datetime.timezone.utc).timestamp())
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                params = {
                    "period1": p1,
                    "period2": p2,
                    "interval": "1d",
                    "events": "history",
                    "includeAdjustedClose": "true",
                }
                logging.info(f"Fetching {symbol} for {year}...")
                raw_data = fetch_with_backoff(url, params, HEADERS)
                time.sleep(0.5)
                json_file.write_text(json.dumps(raw_data, indent=2), encoding="utf-8")

            # Parse result
            status = "success"
            error_msg = None
            price_date = close_price = adj_close_price = currency = None

            top_error = raw_data.get("error")
            if top_error:
                error_msg = str(top_error)
                status = "error"
            elif (
                "chart" in raw_data
                and isinstance(raw_data["chart"].get("result"), list)
                and raw_data["chart"]["result"]
            ):
                chart_error = raw_data["chart"].get("error")
                if chart_error:
                    desc = (chart_error or {}).get("description", "Unknown API error")
                    error_msg = f"API Error: {desc}"
                    status = "error"
                else:
                    result = raw_data["chart"]["result"][0]
                    price_date, close_price, adj_close_price, currency = find_year_end_price(
                        result, year
                    )
                    if close_price is None:
                        status = "error"
                        error_msg = "No valid close price found on or before Dec 31"
            else:
                status = "error"
                error_msg = "Invalid response format or empty result"

            if status == "success":
                success_count += 1
            else:
                fail_count += 1

            results.append({
                "ticker": ticker,
                "yahoo_symbol": symbol,
                "year": year,
                "target_date": f"{year}-12-31",
                "price_date": price_date,
                "close": close_price,
                "adjclose": adj_close_price,
                "currency": currency,
                "source": "yahoo_chart_api",
                "status": status,
                "error": error_msg,
            })

    # Write CSV
    import csv
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "ticker", "yahoo_symbol", "year", "target_date", "price_date",
            "close", "adjclose", "currency", "source", "status", "error",
        ])
        writer.writeheader()
        writer.writerows(results)
    logging.info(f"Saved {len(results)} rows to {csv_path}")

    # Write report
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# Yahoo Finance Year-End Prices Report",
        f"",
        f"**Generated:** {now}",
        f"**Parameters:** start={args.start_year} end={args.end_year} tickers={len(args.tickers)}",
        f"",
        f"## Summary",
        f"- **Total records:** {len(results)}",
        f"- **Successful:** {success_count}",
        f"- **Failed/Missing:** {fail_count}",
        f"- **Skipped (read from JSON cache):** {skipped_count}",
        f"",
    ]
    if fail_count > 0:
        lines += [
            "## Errors & Missing Data",
            "| Ticker | Year | Error |",
            "|---|---|---|",
        ]
        for r in results:
            if r["status"] == "error":
                lines.append(f"| {r['ticker']} | {r['year']} | {r['error']} |")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    logging.info(f"Saved report to {report_path}")


if __name__ == "__main__":
    main()
