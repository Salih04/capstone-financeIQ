from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

_DATASET_YEARS: list[int] = [2020, 2021, 2022, 2023, 2024, 2025]
_DATASET_DIR = Path(__file__).resolve().parents[3] / "3.Datasets"

_CACHED_TICKERS: list[str] | None = None
_CACHED_MTIMES: dict[Path, float] = {}


def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if "Company" not in df.columns and not df.empty:
        first_row = df.iloc[0].astype(str).str.strip()
        if (first_row == "Company").any():
            df = df.copy()
            df.columns = first_row.tolist()
            df = df.iloc[1:].reset_index(drop=True)
    return df


def _ticker_column(df: pd.DataFrame) -> str:
    if "Company" in df.columns:
        return "Company"
    return df.columns[0]


def _tickers_from_file(path: Path) -> set[str]:
    df = pd.read_excel(path)
    df = _normalize_dataframe(df)
    col = _ticker_column(df)
    tickers = [str(v).strip().upper() for v in df[col].dropna().tolist() if str(v).strip()]
    return set(tickers)


def _dataset_files() -> list[Path]:
    return [(_DATASET_DIR / f"{year}stocks.xlsx") for year in _DATASET_YEARS]


def get_dataset_tickers() -> list[str]:
    global _CACHED_TICKERS
    files = [p for p in _dataset_files() if p.exists()]
    if not files:
        return []

    mtimes = {p: p.stat().st_mtime for p in files}
    if _CACHED_TICKERS is not None and mtimes == _CACHED_MTIMES:
        return _CACHED_TICKERS

    sets = []
    for path in files:
        sets.append(_tickers_from_file(path))

    common = set.intersection(*sets) if sets else set()
    _CACHED_TICKERS = sorted(common)
    _CACHED_MTIMES.clear()
    _CACHED_MTIMES.update(mtimes)
    return _CACHED_TICKERS


def get_allowed_periods() -> list[str]:
    return [f"{year}Q4" for year in _DATASET_YEARS]
