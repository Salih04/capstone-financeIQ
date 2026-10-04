"""Frozen configuration of the availability-aware point-in-time (PIT) evaluation.

Defined in docs/PIT_PROTOCOL.md and registered by
docs/PREREGISTRATION_AMENDMENT_2026-10-04.md before any PIT outcome was
computed. Changing a value here after results exist is a protocol deviation and
must be recorded as a further dated amendment.
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIT_DATA = ROOT / "data" / "pit"
DERIVED = PIT_DATA / "derived"
REGISTRY_PATH = PIT_DATA / "feature_availability_registry.json"
DEADLINES_PATH = PIT_DATA / "reporting_deadlines.csv"
FILING_SAMPLE_PATH = PIT_DATA / "filing_dates_sample.csv"
MODELING_PATH = ROOT / "data" / "trusted_clean" / "modeling_dataset_training_2020_2025.csv"
RAW_DAILY_DIR = ROOT / "data" / "trusted_raw" / "prices" / "yahoo_daily_raw"
SHARES_PATH = ROOT / "data" / "trusted_raw" / "shares_outstanding_manual.csv"
RESULTS_DIR = ROOT / "experiments" / "results_pit_v2"

BENCHMARK_SYMBOL = "XU100.IS"
FISCAL_YEARS = range(2020, 2026)          # feature (fiscal) years in the modeling dataset
EVALUATED_FISCAL_YEARS = range(2020, 2025)  # FY2025 window is not complete

# Mode names. They are never mixed inside one run.
ACTUAL_FILING_DATE_MODE = "ACTUAL_FILING_DATE"
STANDARDIZED_CUTOFF_MODE = "STANDARDIZED_CONSERVATIVE_CUTOFF"

# BIST daily price limits are +/-10 %, so a one-day move beyond 25 % in a
# split- and dividend-adjusted series is a corporate-action or data defect,
# not a market return. Rows exposed to one are quarantined, not repaired.
JUMP_THRESHOLD = 0.25
# Tolerance when comparing a share-count change with Yahoo's split ratio.
SHARE_SPLIT_TOLERANCE = 0.02
# A quote older than this many calendar days at a reference date is stale.
MAX_STALENESS_DAYS = 7

SEED = 20261004
N_PERMUTATIONS = 10_000
N_BOOTSTRAPS = 10_000
ML_MODELS = ("linear_regression", "ridge", "lasso", "elasticnet",
             "random_forest", "gradient_boosting")
PRIMARY_MODEL = "baseline_equal_weight"


def _deadlines() -> dict[int, date]:
    """Latest listed-company consolidated deadline per fiscal year."""
    out: dict[int, date] = {}
    with DEADLINES_PATH.open() as fh:
        for row in csv.DictReader(fh):
            if row["scope"] != "listed_companies":
                continue
            out[int(row["fiscal_year"])] = date.fromisoformat(row["consolidated_deadline"])
    return out


def _month_end(d: date) -> date:
    nxt = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    return date.fromordinal(nxt.toordinal() - 1)


def cutoff(spec: str, fiscal_year: int) -> date:
    """Calendar date after whose close fiscal-year statements count as public."""
    if spec == "uniform_05_31":
        return date(fiscal_year + 1, 5, 31)
    if spec == "deadline_month_end":
        return _month_end(_deadlines()[fiscal_year])
    raise ValueError(f"unknown cutoff spec {spec!r}")


# Primary specification and the sensitivities registered with it.
PRIMARY = {"cutoff": "uniform_05_31", "exclude_quarantined": True, "features": "all_admitted"}
SENSITIVITIES = {
    "S1_deadline_month_end": {"cutoff": "deadline_month_end", "exclude_quarantined": True,
                              "features": "all_admitted"},
    "S2_without_valuation": {"cutoff": "uniform_05_31", "exclude_quarantined": True,
                             "features": "no_market_value"},
    "S3_price_only": {"cutoff": "uniform_05_31", "exclude_quarantined": True,
                      "features": "price_only"},
    "S4_statements_only": {"cutoff": "uniform_05_31", "exclude_quarantined": True,
                           "features": "statements_only"},
}
CUTOFF_SPECS = ("uniform_05_31", "deadline_month_end")
