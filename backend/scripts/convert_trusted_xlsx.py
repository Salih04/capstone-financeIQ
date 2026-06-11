"""Convert the trusted 2020-2025 XLSX files into clean CSVs.

Deterministic, no fabrication. Source XLSX files are never modified.

Outputs (default under <repo>/data/trusted/):
    2020stocks.csv ... 2025stocks.csv      one per year
    stocks_2020_2025.csv                    combined, with a `year` column

Usage:
    python -m scripts.convert_trusted_xlsx
    python -m scripts.convert_trusted_xlsx --datasets ../data/raw/yearly_xlsx --out ../data/trusted
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

from app.trusted_data import (
    read_trusted_xlsx,
    summarize_frame,
    validate_frame,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
# Env overrides make this work both in the repo (parents[2] == repo root) and
# in Docker, where /app == backend and the heuristic would be wrong.
DEFAULT_DATASETS = os.environ.get("TRUSTED_DATASETS_DIR", str(REPO_ROOT / "data/raw/yearly_xlsx"))
DEFAULT_OUT = os.environ.get("TRUSTED_OUT_DIR", str(REPO_ROOT / "data" / "trusted"))
COMBINED_NAME = "stocks_2020_2025.csv"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--datasets", default=DEFAULT_DATASETS)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    datasets = Path(args.datasets)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    files = sorted(datasets.glob("20*stocks.xlsx"))
    if not files:
        raise SystemExit(f"No trusted *stocks.xlsx files found in {datasets}")

    all_errors: list[str] = []
    frames: list[pd.DataFrame] = []

    print(f"Converting {len(files)} trusted XLSX file(s) from {datasets}")
    for f in files:
        df = read_trusted_xlsx(f)
        errors = validate_frame(df, f.name)
        all_errors.extend(errors)

        csv_path = out / f"{f.stem}.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8")
        s = summarize_frame(df)
        print(
            f"  {f.name:18s} -> {csv_path.name:18s} "
            f"rows={s['rows']:3d} tickers={s['tickers']:3d} "
            f"cols={s['columns']:2d} missing_critical={s['missing_critical']}"
        )
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    all_errors.extend(validate_frame(combined, COMBINED_NAME))
    combined_path = out / COMBINED_NAME
    combined.to_csv(combined_path, index=False, encoding="utf-8")

    cs = summarize_frame(combined)
    print(
        f"\nCombined -> {combined_path.name}: rows={cs['rows']} "
        f"years={cs['years']} tickers={cs['tickers']} cols={cs['columns']}"
    )

    if all_errors:
        print("\nVALIDATION ERRORS:", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("OK: all trusted files converted and validated cleanly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
