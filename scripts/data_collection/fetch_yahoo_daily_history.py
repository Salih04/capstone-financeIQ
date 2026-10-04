"""Fetch daily Yahoo Chart API history for the point-in-time (PIT) evaluation.

Manual, networked collection step (never run by tests). Same free source and
request pattern as ``scripts/fetch_yahoo_chart_prices.py``, but for the full
daily range with split and dividend events, because the PIT protocol
(docs/PIT_PROTOCOL.md) measures returns from the first trading day after a
statement-availability cutoff instead of from 31 December.

Raw responses are PRIVATE_LOCAL_RAW (docs/SOURCE_USE_OWNER_AMENDMENT.md §4):
they are written to ``data/trusted_raw/prices/yahoo_daily_raw/`` (gitignored).
Only a provenance manifest (URL, access time, SHA-256, byte size) is
committed: ``data/pit/yahoo_daily_provenance.csv``.

    python scripts/data_collection/fetch_yahoo_daily_history.py
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "trusted_raw" / "prices" / "yahoo_daily_raw"
PROVENANCE = ROOT / "data" / "pit" / "yahoo_daily_provenance.csv"
TRAINING = ROOT / "data" / "trusted_clean" / "modeling_dataset_training_2020_2025.csv"
BENCHMARK_SYMBOL = "XU100.IS"
URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
PERIOD1 = int(datetime(2017, 1, 1, tzinfo=timezone.utc).timestamp())


def _tickers() -> list[str]:
    with TRAINING.open() as fh:
        return sorted({row["ticker"] for row in csv.DictReader(fh)})


def _get(symbol: str, period2: int, retries: int = 5) -> tuple[bytes, str]:
    params = {"period1": PERIOD1, "period2": period2, "interval": "1d",
              "events": "div,split", "includeAdjustedClose": "true"}
    url = f"{URL.format(symbol=symbol)}?{urlencode(params)}"
    for attempt in range(retries):
        try:
            with urlopen(Request(url, headers=HEADERS), timeout=30) as resp:
                return resp.read(), url
        except HTTPError as exc:
            if exc.code in (400, 401, 403, 404):
                raise
        except (URLError, OSError):
            pass
        time.sleep(2 ** attempt)
    raise RuntimeError(f"{symbol}: retries exhausted")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--end", default=None, help="UTC end date YYYY-MM-DD (default: now)")
    args = ap.parse_args()
    end = (datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
           if args.end else datetime.now(timezone.utc))
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROVENANCE.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for ticker in [*_tickers(), BENCHMARK_SYMBOL]:
        symbol = ticker if ticker.endswith(".IS") else f"{ticker}.IS"
        accessed = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            body, url = _get(symbol, int(end.timestamp()))
        except Exception as exc:  # recorded, never silently skipped
            rows.append({"symbol": symbol, "status": f"error: {exc}", "url": "",
                         "accessed_utc": accessed, "raw_file": "", "sha256": "", "bytes": 0})
            continue
        payload = json.loads(body)
        status = "ok" if payload.get("chart", {}).get("result") else "empty"
        raw = RAW_DIR / f"{symbol}.json"
        raw.write_bytes(body)
        rows.append({"symbol": symbol, "status": status, "url": url, "accessed_utc": accessed,
                     "raw_file": raw.relative_to(ROOT).as_posix(),
                     "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)})
        time.sleep(1.0)  # polite pacing; no rate-limit circumvention
    with PROVENANCE.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    bad = [r["symbol"] for r in rows if r["status"] != "ok"]
    print(f"fetched {len(rows) - len(bad)}/{len(rows)}; not ok: {bad}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
