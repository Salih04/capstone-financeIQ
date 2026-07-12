#!/usr/bin/env python3
"""Read-only pre-demo health check for a running FinanceIQ backend.

Checks the public health endpoint plus the CSV-backed research-runtime and
forecasting-options endpoints. It makes GET requests only and exits nonzero if
any endpoint is unavailable or reports missing/empty runtime data.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


EXPECTED_FORECAST_SOURCE = "modeling_dataset_public_2020_2025.csv"


def _fetch_json(base_url: str, path: str, timeout: float) -> tuple[int, dict[str, Any]]:
    request = Request(
        f"{base_url}{path}",
        headers={"Accept": "application/json", "User-Agent": "financeiq-demo-smoke/1.0"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - URL is explicit CLI input
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
    except (URLError, OSError) as exc:
        raise RuntimeError(str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON response: {exc}") from exc


def _check_health(base_url: str, timeout: float) -> str:
    status, body = _fetch_json(base_url, "/health", timeout)
    if status != 200 or body.get("status") != "ok":
        raise RuntimeError(f"expected HTTP 200 and status=ok, received HTTP {status}: {body}")
    return f"status=ok version={body.get('version', 'unknown')}"


def _check_research_runtime(base_url: str, timeout: float) -> str:
    status, body = _fetch_json(base_url, "/research/runtime-status", timeout)
    missing = body.get("missing_required_files")
    rows = body.get("public_rows", 0)
    tickers = body.get("public_tickers", 0)
    if status != 200:
        raise RuntimeError(f"expected HTTP 200, received HTTP {status}")
    if not body.get("public_dataset_exists") or not isinstance(rows, int) or rows <= 0:
        raise RuntimeError(f"public modeling CSV is unavailable or empty: {body}")
    if not isinstance(tickers, int) or tickers <= 0:
        raise RuntimeError(f"public modeling CSV has no tickers: {body}")
    if missing:
        raise RuntimeError(f"required runtime files are missing: {missing}")
    return f"CSV-backed data (not fallback): public_rows={rows} public_tickers={tickers}"


def _check_forecasting_options(base_url: str, timeout: float) -> str:
    status, body = _fetch_json(base_url, "/forecasting/options", timeout)
    ticker_count = body.get("ticker_count", 0)
    feature_columns = body.get("feature_columns", [])
    if status != 200:
        raise RuntimeError(f"expected HTTP 200, received HTTP {status}")
    if body.get("available") is not True:
        raise RuntimeError(f"forecasting options are not available: {body}")
    if body.get("data_source") != EXPECTED_FORECAST_SOURCE:
        raise RuntimeError(
            f"expected data_source={EXPECTED_FORECAST_SOURCE!r}, got {body.get('data_source')!r}"
        )
    if not isinstance(ticker_count, int) or ticker_count <= 0 or not feature_columns:
        raise RuntimeError(f"forecasting CSV is empty or lacks features: {body}")
    return (
        "CSV-backed data (not fallback): "
        f"source={body['data_source']} tickers={ticker_count} features={len(feature_columns)}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=os.environ.get("FINANCEIQ_API_URL", "http://127.0.0.1:8000"),
        help="running backend base URL (default: FINANCEIQ_API_URL or http://127.0.0.1:8000)",
    )
    parser.add_argument("--timeout", type=float, default=10.0, help="per-request timeout in seconds")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        parser.error("--base-url must start with http:// or https://")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")

    print(f"FinanceIQ demo smoke check: {base_url}")
    checks = (
        ("/health", _check_health),
        ("/research/runtime-status", _check_research_runtime),
        ("/forecasting/options", _check_forecasting_options),
    )
    failures = 0
    for path, check in checks:
        try:
            print(f"PASS {path}: {check(base_url, args.timeout)}")
        except RuntimeError as exc:
            failures += 1
            print(f"FAIL {path}: {exc}")

    if failures:
        print(f"Demo smoke check failed: {failures}/{len(checks)} endpoint(s) need attention.")
        return 1
    print("Demo smoke check passed: all endpoints report real CSV-backed runtime data.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
