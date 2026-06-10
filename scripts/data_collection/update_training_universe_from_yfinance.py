"""Add yfinance-verified tickers to the training universe config.

Reads:
    data/trusted_raw/financials/bist100_yfinance_candidate_clean.csv
    data/config/universe_training_bist100.csv

Writes:
    data/config/universe_training_bist100.csv  (in-place, appends new tickers only)

Rules:
    - Only tickers with ≥1 valid row in the clean CSV are eligible.
    - Never modifies rows for tickers already present (public_40 or existing pilots).
    - Never sets is_public_universe=true.
    - Adds new tickers with: is_public_universe=false, is_training_universe=true,
      notes=yfinance_unofficial_expansion

Run:
    PYTHONPATH=. python scripts/data_collection/update_training_universe_from_yfinance.py

    # Preview without writing:
    PYTHONPATH=. python scripts/data_collection/update_training_universe_from_yfinance.py --dry-run

    # Force update notes for already-present yfinance tickers:
    PYTHONPATH=. python scripts/data_collection/update_training_universe_from_yfinance.py --update-notes
"""

from __future__ import annotations

import argparse
import sys
from io import StringIO
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
CLEAN_CSV = REPO_ROOT / "data" / "trusted_raw" / "financials" / "bist100_yfinance_candidate_clean.csv"
UNIVERSE_CSV = REPO_ROOT / "data" / "config" / "universe_training_bist100.csv"

TRAINING_NOTES = "yfinance_unofficial_expansion"


def _load_universe_preserving_comments(path: Path) -> tuple[list[str], pd.DataFrame]:
    """Load universe CSV, preserving comment lines separately."""
    raw_lines = path.read_text().splitlines()
    comment_lines = [ln for ln in raw_lines if ln.strip().startswith("#")]
    data_lines = [ln for ln in raw_lines if not ln.strip().startswith("#") and ln.strip()]
    df = pd.read_csv(StringIO("\n".join(data_lines)))
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    for col in ("is_public_universe", "is_training_universe"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().isin({"true", "1", "yes"})
    return comment_lines, df


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Print plan but do not write.")
    ap.add_argument("--update-notes", action="store_true",
                    help="Update notes field for already-present yfinance tickers.")
    ap.add_argument(
        "--clean-csv", type=Path, default=CLEAN_CSV,
        help=f"Clean candidate CSV (default: {CLEAN_CSV.relative_to(REPO_ROOT)})",
    )
    args = ap.parse_args(argv)

    clean_path = Path(args.clean_csv)
    if not clean_path.is_file():
        print(
            f"[update-universe] ERROR: {clean_path} not found.\n"
            "  Run: make collect-yfinance-bist100 && make clean-yfinance-bist100",
            file=sys.stderr,
        )
        return 1

    if not UNIVERSE_CSV.is_file():
        print(f"[update-universe] ERROR: {UNIVERSE_CSV} not found.", file=sys.stderr)
        return 1

    clean = pd.read_csv(clean_path)
    clean["ticker"] = clean["ticker"].astype(str).str.strip().str.upper()

    # Tickers in clean CSV with ≥1 valid row
    eligible = set(clean["ticker"].unique())
    print(f"[update-universe] Eligible tickers from clean CSV ({len(eligible)}): {sorted(eligible)}")

    comment_lines, universe = _load_universe_preserving_comments(UNIVERSE_CSV)
    existing_tickers = set(universe["ticker"].unique())
    public_tickers = set(universe[universe["is_public_universe"]]["ticker"].unique())

    already_present = eligible & existing_tickers
    truly_new = eligible - existing_tickers
    would_overwrite_public = truly_new & public_tickers

    if would_overwrite_public:
        print(f"[update-universe] WARNING: Skipping tickers already in public_40: {sorted(would_overwrite_public)}")
        truly_new -= would_overwrite_public

    print(f"[update-universe] Already in universe (skip): {sorted(already_present)}")
    print(f"[update-universe] New tickers to add ({len(truly_new)}): {sorted(truly_new)}")

    if not truly_new:
        print("[update-universe] Nothing to add. Universe is up-to-date.")
        return 0

    if args.dry_run:
        print("[update-universe] --dry-run: no changes written.")
        for t in sorted(truly_new):
            print(f"  Would add: {t},false,true,{TRAINING_NOTES}")
        return 0

    # Build new rows
    new_rows = pd.DataFrame([
        {
            "ticker": t,
            "is_public_universe": False,
            "is_training_universe": True,
            "notes": TRAINING_NOTES,
        }
        for t in sorted(truly_new)
    ])

    updated = pd.concat([universe, new_rows], ignore_index=True)
    updated = updated.sort_values(
        ["is_public_universe", "ticker"],
        ascending=[False, True],
    ).reset_index(drop=True)

    # Rebuild file preserving original comment header + appending new-ticker comment
    new_comment_section = "\n# --- yfinance expansion tickers (added by update_training_universe_from_yfinance.py) ---"
    header_comments = "\n".join(comment_lines)

    # Write: header comments + data + new section marker for newly added tickers
    public_part = updated[updated["is_public_universe"]].copy()
    training_only_part = updated[~updated["is_public_universe"]].copy()

    with UNIVERSE_CSV.open("w") as f:
        f.write(header_comments + "\n")
        f.write("ticker,is_public_universe,is_training_universe,notes\n")
        for _, row in public_part.iterrows():
            f.write(f"{row['ticker']},{str(row['is_public_universe']).lower()},{str(row['is_training_universe']).lower()},{row.get('notes', '')}\n")
        if not training_only_part.empty:
            f.write("# yfinance training-only tickers — is_public_universe=false\n")
            f.write("# Source: yfinance (unofficial Yahoo Finance). KAP cross-check recommended.\n")
            for _, row in training_only_part.iterrows():
                f.write(f"{row['ticker']},{str(row['is_public_universe']).lower()},{str(row['is_training_universe']).lower()},{row.get('notes', '')}\n")

    print(f"[update-universe] Wrote {len(updated)} total tickers to {UNIVERSE_CSV.relative_to(REPO_ROOT)}")
    print(f"  Public tickers: {len(public_part)}")
    print(f"  Training-only: {len(training_only_part)}")
    print(f"  Added: {sorted(truly_new)}")
    print(
        "\nNext steps:\n"
        "  make fetch-training-prices\n"
        "  make full-research-agent"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
