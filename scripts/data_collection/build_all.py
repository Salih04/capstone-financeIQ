"""One-command pipeline: build the T -> T+1 modeling dataset (PHASE 11).

    python -m scripts.data_collection.build_all [flags]

Flags:
    --start-year N      first feature year (default 2020)
    --end-year N        last feature year (default 2025)
    --tickers A,B,C     restrict universe
    --force-refresh     ignore caches (no network sources wired by default)
    --skip-download     do not hit any network source (default ON)
    --manual-only       use only manually-ingested files in data/trusted_raw/
    --validate-only     re-run validation on the existing modeling CSV

Steps: universe -> fundamentals(year T) -> returns + T->T+1 targets ->
benchmark (manual) -> modeling dataset -> validation -> data dictionary.
No fabrication; frozen-snapshot columns are excluded, missingness is reported.
"""

from __future__ import annotations

import argparse
import sys

import pandas as pd

from scripts.data_collection import pipeline as P
from scripts.data_collection import validate as V


def _data_dictionary(df: pd.DataFrame) -> None:
    reg = V.feature_registry(df)
    lines = ["# Data dictionary — modeling_dataset_2020_2025.csv\n",
             "Research/educational only. NOT investment advice.\n",
             "Each row = one company-year. Features belong to year T; the primary",
             "target is the realized return in year T+1.\n",
             "| column | role | leakage_risk |", "|---|---|---|"]
    for r in reg:
        lines.append(f"| `{r['column']}` | {r['role']} | {r['leakage_risk']} |")
    lines += ["", "## Roles",
              "- **identifier / metadata**: not used as predictive features.",
              "- **feature_allowed**: year-T provisional fundamentals (genuinely vary by year).",
              "- **target**: next-year realized-return outcomes (never a feature).",
              "- **same_year_analysis_only**: `same_year_return_pct` — analysis only, never a feature.",
              "- **benchmark**: BIST100-relative targets (present only if benchmark CSV provided).",
              "- **excluded**: reference columns proven to be a frozen snapshot (see data_quality_report)."]
    (P.CLEAN_DIR / "data_dictionary.md").write_text("\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start-year", type=int, default=2020)
    ap.add_argument("--end-year", type=int, default=2025)
    ap.add_argument("--tickers", type=str, default=None)
    ap.add_argument("--force-refresh", action="store_true")
    ap.add_argument("--skip-download", action="store_true", default=True)
    ap.add_argument("--manual-only", action="store_true")
    ap.add_argument("--validate-only", action="store_true")
    ap.add_argument("--manual-financials-dir", type=str, default=None)
    ap.add_argument("--strict-manual-validation", action="store_true")
    ap.add_argument("--allow-partial-manual-coverage", action="store_true", default=True)
    args = ap.parse_args(argv)

    cfg = P.PipelineConfig(
        start_year=args.start_year, end_year=args.end_year,
        tickers=[t.strip() for t in args.tickers.split(",")] if args.tickers else None,
        force_refresh=args.force_refresh, skip_download=args.skip_download,
        manual_only=args.manual_only, validate_only=args.validate_only,
        strict_manual_validation=args.strict_manual_validation,
        allow_partial_manual_coverage=args.allow_partial_manual_coverage,
    )
    if args.manual_financials_dir:
        from pathlib import Path
        cfg.manual_financials_dir = Path(args.manual_financials_dir)
    if args.manual_only and not cfg.manual_financials_dir.is_dir():
        cfg.say("--manual-only set but no manual financials dir; nothing to ingest.")
        return 1
    P.CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    P.RAW_DIR.mkdir(parents=True, exist_ok=True)

    if args.validate_only:
        if not P.MODELING_CSV.is_file():
            cfg.say("No modeling dataset to validate. Run without --validate-only first.")
            return 1
        df = pd.read_csv(P.MODELING_CSV)
    else:
        cfg.say("=== Building T->T+1 modeling dataset ===")
        df = P.build_modeling_dataset(cfg)
        _data_dictionary(df)

    report = V.validate(df, cfg)

    cfg.say("\n=== SUMMARY ===")
    cfg.say(f"  modeling rows: {report['rows']}  features: {report['n_features']}  "
            f"target rows: {report['rows_with_target']}  inference-only: {report['inference_only_rows']}")
    cfg.say(f"  benchmark: {'available' if report['benchmark_available'] else 'MISSING (manual CSV needed)'}")
    cfg.say(f"  valid for T->T+1 modeling: {report['valid_for_T_to_T1_modeling']}")
    cfg.say(f"  outputs in: {P.CLEAN_DIR}")
    return 0 if report["valid_for_T_to_T1_modeling"] else 2


if __name__ == "__main__":
    sys.exit(main())
