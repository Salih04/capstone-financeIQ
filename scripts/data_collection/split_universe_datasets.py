"""Split the modeling dataset into training and public subsets based on universe configs.

Reads:
    data/config/universe_public_40.csv
    data/config/universe_training_bist100.csv
    data/trusted_clean/modeling_dataset_2020_2025.csv

Writes:
    data/trusted_clean/modeling_dataset_training_2020_2025.csv   (is_training_universe=true)
    data/trusted_clean/modeling_dataset_public_2020_2025.csv     (is_public_universe=true)

The original modeling_dataset_2020_2025.csv is NOT modified (backward compatibility).

Validation:
    - Public dataset must ONLY contain public-40 tickers.
    - Training dataset may contain more tickers when financials exist.
    - Non-public tickers NEVER enter the public output.

Run:
    PYTHONPATH=. python -m scripts.data_collection.split_universe_datasets
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
CLEAN_DIR = REPO_ROOT / "data" / "trusted_clean"
CONFIG_DIR = REPO_ROOT / "data" / "config"

PUBLIC_UNIVERSE_CSV = CONFIG_DIR / "universe_public_40.csv"
TRAINING_UNIVERSE_CSV = CONFIG_DIR / "universe_training_bist100.csv"
MODELING_CSV = CLEAN_DIR / "modeling_dataset_2020_2025.csv"
TRAINING_OUT = CLEAN_DIR / "modeling_dataset_training_2020_2025.csv"
PUBLIC_OUT = CLEAN_DIR / "modeling_dataset_public_2020_2025.csv"
REPORT_OUT = CLEAN_DIR / "universe_split_report.json"


def _load_universe(csv_path: Path) -> pd.DataFrame:
    """Load universe CSV, skipping comment lines starting with #."""
    lines = [ln for ln in csv_path.read_text().splitlines() if not ln.startswith("#")]
    from io import StringIO
    df = pd.read_csv(StringIO("\n".join(lines)))
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    for col in ("is_public_universe", "is_training_universe"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().isin({"true", "1", "yes"})
    return df


def main() -> int:
    if not MODELING_CSV.is_file():
        print(f"[split] ERROR: {MODELING_CSV} not found. Run `make data` first.", file=sys.stderr)
        return 1

    if not PUBLIC_UNIVERSE_CSV.is_file() or not TRAINING_UNIVERSE_CSV.is_file():
        print("[split] ERROR: universe config CSVs missing. Expected:", file=sys.stderr)
        print(f"  {PUBLIC_UNIVERSE_CSV}", file=sys.stderr)
        print(f"  {TRAINING_UNIVERSE_CSV}", file=sys.stderr)
        return 1

    public_uni = _load_universe(PUBLIC_UNIVERSE_CSV)
    training_uni = _load_universe(TRAINING_UNIVERSE_CSV)

    public_tickers = set(public_uni[public_uni["is_public_universe"]]["ticker"])
    training_tickers = set(training_uni[training_uni["is_training_universe"]]["ticker"])

    df = pd.read_csv(MODELING_CSV)
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()

    # Add universe membership columns
    df["is_public_universe"] = df["ticker"].isin(public_tickers)
    df["is_training_universe"] = df["ticker"].isin(training_tickers)
    df["universe_source"] = df["ticker"].apply(
        lambda t: "public_40" if t in public_tickers else (
            "training_only" if t in training_tickers else "unknown"
        )
    )

    # Training split: tickers with is_training_universe=true
    df_train = df[df["is_training_universe"]].copy()

    # Public split: tickers with is_public_universe=true
    df_public = df[df["is_public_universe"]].copy()

    # Validation: no non-public tickers in public dataset
    non_public_in_public = set(df_public["ticker"]) - public_tickers
    if non_public_in_public:
        print(f"[split] FATAL: non-public tickers leaked into public dataset: {non_public_in_public}", file=sys.stderr)
        return 1

    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    df_train.to_csv(TRAINING_OUT, index=False)
    df_public.to_csv(PUBLIC_OUT, index=False)

    # Missing training tickers (in config but no data)
    missing_training = training_tickers - set(df["ticker"])
    missing_public = public_tickers - set(df["ticker"])

    report = {
        "public_universe_count": len(public_tickers),
        "training_universe_count": len(training_tickers),
        "training_only_count": len(training_tickers - public_tickers),
        "training_dataset_rows": len(df_train),
        "training_dataset_tickers": int(df_train["ticker"].nunique()),
        "public_dataset_rows": len(df_public),
        "public_dataset_tickers": int(df_public["ticker"].nunique()),
        "missing_from_training_data": sorted(missing_training),
        "missing_from_public_data": sorted(missing_public),
        "non_public_in_public_dataset": sorted(non_public_in_public),
        "validation_passed": len(non_public_in_public) == 0,
        "outputs": {
            "training": str(TRAINING_OUT),
            "public": str(PUBLIC_OUT),
        },
        "note": (
            "Training and public datasets are identical because no extra "
            "BIST100 financial data has been sourced yet. Add tickers to "
            "universe_training_bist100.csv with verified financials to expand."
            if training_tickers == public_tickers else
            f"Training universe has {len(training_tickers - public_tickers)} extra tickers "
            "hidden from frontend endpoints."
        ),
    }
    REPORT_OUT.write_text(json.dumps(report, indent=2))

    print(f"[split] public universe: {len(public_tickers)} tickers")
    print(f"[split] training universe: {len(training_tickers)} tickers "
          f"({len(training_tickers - public_tickers)} training-only)")
    print(f"[split] training dataset: {len(df_train)} rows ({df_train['ticker'].nunique()} tickers)")
    print(f"[split] public dataset:   {len(df_public)} rows ({df_public['ticker'].nunique()} tickers)")
    if missing_training:
        print(f"[split] WARNING: {len(missing_training)} training-universe tickers have no data "
              f"(financials not yet ingested): {sorted(missing_training)}")
    print(f"[split] validation passed: {report['validation_passed']}")
    print(f"[split] wrote: {TRAINING_OUT.name}, {PUBLIC_OUT.name}, universe_split_report.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
