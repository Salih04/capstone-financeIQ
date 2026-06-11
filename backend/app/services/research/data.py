"""Trusted yearly data access for the research layer.

Source of truth is the converted CSV ``data/trusted/stocks_2020_2025.csv``.
Loading from a file (not the DB) keeps the research/scoring/experiment code
deterministic, DB-free, and testable. The same artifact backs the Postgres
``yearly_stocks`` table, so they never disagree.

No fabrication: missing cells stay NaN.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import pandas as pd

from app.core.paths import resolve_repo_root

REPO_ROOT = resolve_repo_root()
DEFAULT_CSV = Path(
    os.environ.get(
        "TRUSTED_COMBINED_CSV",
        str(REPO_ROOT / "data" / "trusted" / "stocks_2020_2025.csv"),
    )
)

TARGET_COLUMN = "annual_return_pct"  # realized yearly return = ground truth
SUPPORTED_YEARS = (2020, 2021, 2022, 2023, 2024, 2025)

# Clean T->T+1 modeling dataset produced by scripts/data_collection/build_all.
# Legacy stocks_2020_2025.csv is UNRELIABLE for fundamentals (frozen snapshot);
# use this for next-year modelling once present.
MODELING_DATASET = REPO_ROOT / "data" / "trusted_clean" / "modeling_dataset_2020_2025.csv"


def load_modeling_dataset() -> "pd.DataFrame":
    """Clean company-year dataset with next-year return targets, or None-raise."""
    if not MODELING_DATASET.is_file():
        raise TrustedDataMissing(
            f"Modeling dataset not found at {MODELING_DATASET}. Run "
            "`python -m scripts.data_collection.build_all`."
        )
    return pd.read_csv(MODELING_DATASET)


class TrustedDataMissing(RuntimeError):
    """Raised when the trusted CSV is absent. Never silently fabricated."""


def csv_path() -> Path:
    return DEFAULT_CSV


@lru_cache(maxsize=4)
def _load_cached(path: str, mtime: float) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    df["year"] = df["year"].astype(int)
    return df


def load_trusted() -> pd.DataFrame:
    p = DEFAULT_CSV
    if not p.is_file():
        raise TrustedDataMissing(
            f"Trusted dataset not found at {p}. Run "
            "`python -m scripts.convert_trusted_xlsx` first."
        )
    # mtime in cache key => auto-reload if the file is regenerated.
    return _load_cached(str(p), p.stat().st_mtime).copy()


def available_years() -> list[int]:
    df = load_trusted()
    return sorted(int(y) for y in df["year"].unique())


def year_frame(year: int) -> pd.DataFrame:
    df = load_trusted()
    sub = df[df["year"] == int(year)].copy()
    if sub.empty:
        raise ValueError(f"No trusted data for year {year}. Available: {available_years()}")
    return sub.reset_index(drop=True)


_NON_FEATURE = {"ticker", "year", "indices", "source_file"}


def column_variability() -> dict:
    """Classify each numeric column as time-varying or frozen across years.

    DATA INTEGRITY: this dataset is inconsistent. Some columns are genuine
    per-year history; others are a single snapshot repeated in every file. This
    surfaces exactly which, so nothing is silently treated as time-series when
    it is not.
    """
    df = load_trusted()
    g = df.groupby("ticker")
    varying, frozen = [], []
    for col in df.columns:
        if col in _NON_FEATURE:
            continue
        if (g[col].nunique(dropna=False) > 1).any():
            varying.append(col)
        else:
            frozen.append(col)
    return {
        "time_varying": sorted(varying),
        "frozen_snapshot": sorted(frozen),
        "n_varying": len(varying),
        "n_frozen": len(frozen),
    }
