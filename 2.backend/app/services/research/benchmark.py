"""BIST100 benchmark (PHASE 6).

Benchmark yearly returns come from a MANUAL, user-provided config file:
    data/trusted/bist100_benchmark_returns.csv   (columns: year,bist100_return_pct)

We never fabricate or fetch these values. If the file is absent or a year is
missing, the API/UI reports the benchmark as unavailable rather than inventing
a number. A template (no values) is shipped so the user knows the format.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import pandas as pd

from app.services.research import data

REPO_ROOT = Path(__file__).resolve().parents[4]
BENCH_CSV = Path(
    os.environ.get(
        "BIST100_BENCHMARK_CSV",
        str(REPO_ROOT / "data" / "trusted" / "bist100_benchmark_returns.csv"),
    )
)


@lru_cache(maxsize=2)
def _load(path: str, mtime: float) -> dict[int, float]:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    if "year" not in df.columns or "bist100_return_pct" not in df.columns:
        return {}
    out: dict[int, float] = {}
    for _, r in df.iterrows():
        val = pd.to_numeric(pd.Series([r["bist100_return_pct"]]), errors="coerce").iloc[0]
        if pd.notna(r.get("year")) and pd.notna(val):
            out[int(r["year"])] = float(val)
    return out


def _returns() -> dict[int, float]:
    if not BENCH_CSV.is_file():
        return {}
    return _load(str(BENCH_CSV), BENCH_CSV.stat().st_mtime)


def is_available() -> bool:
    return bool(_returns())


def year_return(year: int) -> float | None:
    return _returns().get(int(year))


def status() -> dict:
    r = _returns()
    return {
        "available": bool(r),
        "path": str(BENCH_CSV),
        "years_present": sorted(r.keys()),
        "missing_years": [y for y in data.SUPPORTED_YEARS if y not in r],
        "message": (
            "BIST100 benchmark loaded."
            if r
            else f"BIST100 benchmark missing. Provide {BENCH_CSV.name} "
            "(columns: year,bist100_return_pct) with real values."
        ),
    }
