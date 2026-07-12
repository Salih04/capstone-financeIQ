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
import json
import sys

import pandas as pd

from scripts.data_collection import pipeline as P
from scripts.data_collection import validate as V


PASSPORT_JSON = P.CLEAN_DIR / "feature_passports.json"
PASSPORT_FIELDS = {
    "name",
    "registry_role",
    "source_class",
    "transform_chain",
    "leakage_risk",
    "acceptance_status",
    "caveats",
    "evidence_files",
}
SOURCE_CLASSES = {
    "vendor_xlsx",
    "corrected_yearly_csv",
    "yahoo_fetch",
    "manual_shares",
    "derived",
    "metadata",
    "unknown",
}

_QUALITY = "data/trusted_clean/data_quality_report.json"
_FROZEN = "data/trusted_clean/frozen_column_evidence.json"
_CORRECTED = "data/trusted_clean/corrected_yearly_ingestion_report.json"
_VALUATION = "data/trusted_clean/free_valuation_history_report.json"
_SHARES = "data/trusted_clean/shares_outstanding_expansion_report.json"
_BENCHMARK = "data/trusted_clean/bist100_benchmark_report.json"
_PILOT = "data/trusted_clean/pilot_integration_report.json"

_GROWTH_VENDOR_COLUMNS = {
    "ebitda_growth_pct",
    "gross_profit_growth_pct",
    "net_income_growth_pct",
    "operating_income_growth_pct",
    "revenue_growth_pct",
}
_MIXED_CORRECTED_COLUMNS = {
    "ebitda",
    "ebitda_margin",
    "gross_margin",
    "gross_profit",
    "net_income",
    "net_margin",
    "operating_income",
    "revenue",
    "roa",
    "roe",
}
_MIXED_BALANCE_COLUMNS = {
    "current_assets",
    "current_ratio",
    "equity",
    "financial_debt_ratio",
    "leverage_ratio",
    "long_term_liabilities",
    "net_debt",
    "net_debt_to_ebitda",
    "non_current_assets",
    "short_term_liabilities",
    "total_assets",
    "working_capital",
}
_VALUATION_COLUMNS = {"market_cap", "enterprise_value", "pe_ratio", "pb_ratio", "ev_ebitda"}
_PRICE_DERIVED_COLUMNS = {
    "price_data_available",
    "price_drawdown_from_3y_high_pct",
    "price_history_years_available",
    "price_momentum_1y_pct",
    "price_momentum_2y_pct",
    "price_vs_bist100_1y_pct",
}


def _acceptance_status(role: str) -> str:
    return {
        V.ROLE_FEATURE: "accepted_feature",
        V.ROLE_TARGET: "target_only",
        V.ROLE_BENCHMARK: "target_only",
        V.ROLE_SAME_YEAR: "analysis_only",
        V.ROLE_IDENTIFIER: "identifier_only",
        V.ROLE_METADATA: "metadata_only",
    }.get(role, "excluded")


def _passport_details(name: str) -> dict:
    """Return code/report-backed lineage facts; ambiguous column sources stay unknown."""
    if name == "ticker":
        return {
            "source_class": "metadata",
            "transform_chain": ["normalize ticker text to uppercase", "use ticker with year as row key"],
            "caveats": ["Ticker identity is normalized text; it is not point-in-time membership evidence."],
            "evidence_files": ["scripts/data_collection/pipeline.py", "scripts/data_collection/integrate_pilot_tickers.py"],
        }
    if name == "company_name":
        return {
            "source_class": "metadata",
            "transform_chain": ["copy ticker into company_name as a display label"],
            "caveats": ["No verified company-name source is attached; the ticker is used as the label."],
            "evidence_files": ["scripts/data_collection/pipeline.py", "scripts/data_collection/integrate_pilot_tickers.py"],
        }
    if name == "year":
        return {
            "source_class": "metadata",
            "transform_chain": ["parse source fiscal year as integer", "retain years 2020 through 2025"],
            "caveats": [],
            "evidence_files": ["scripts/data_collection/pipeline.py", "scripts/data_collection/integrate_pilot_tickers.py"],
        }
    if name == "sector":
        return {
            "source_class": "metadata",
            "transform_chain": ["leave null because no validated sector-label source exists"],
            "caveats": ["Sector is unpopulated in the trusted modeling path and must not be inferred."],
            "evidence_files": ["scripts/data_collection/pipeline.py", "METHODOLOGY.md"],
        }
    if name == "indices":
        return {
            "source_class": "metadata",
            "transform_chain": ["retain public-cohort index text from the reference input", "leave training-only pilot rows null"],
            "caveats": ["Index text does not establish historical constituent membership."],
            "evidence_files": ["scripts/data_collection/pipeline.py", "scripts/data_collection/integrate_pilot_tickers.py", "docs/universe_audit.md"],
        }
    if name == "is_bist100":
        return {
            "source_class": "metadata",
            "transform_chain": ["derive public rows from whether indices contains XU100", "set training-only pilot rows false"],
            "caveats": ["This flag is not verified point-in-time BIST100 membership."],
            "evidence_files": ["scripts/data_collection/pipeline.py", "scripts/data_collection/integrate_pilot_tickers.py", "docs/universe_audit.md"],
        }
    if name in {"is_public_universe", "is_training_universe", "universe_source"}:
        operation = {
            "is_public_universe": "mark membership in the configured public cohort",
            "is_training_universe": "mark membership in the configured training cohort",
            "universe_source": "record public_40 or yfinance_pilot row origin",
        }[name]
        return {
            "source_class": "metadata",
            "transform_chain": [operation, "persist during universe split/integration"],
            "caveats": ["Configured cohort membership is retrospective, not verified point-in-time index membership."],
            "evidence_files": ["scripts/data_collection/integrate_pilot_tickers.py", "scripts/data_collection/split_universe_datasets.py", _PILOT, "docs/universe_audit.md"],
        }
    if name == "target_year":
        return {
            "source_class": "derived",
            "transform_chain": ["target_year = year + 1"],
            "caveats": [],
            "evidence_files": ["scripts/data_collection/pipeline.py", "scripts/data_collection/integrate_pilot_tickers.py"],
        }
    if name in {"has_target", "is_inference_row"}:
        operation = (
            "has_target = next_year_return_pct is non-null"
            if name == "has_target"
            else "is_inference_row = not has_target"
        )
        return {
            "source_class": "derived",
            "transform_chain": [operation],
            "caveats": ["Missing future outcomes remain null and are not imputed."],
            "evidence_files": ["scripts/data_collection/pipeline.py", "scripts/data_collection/integrate_pilot_tickers.py", _QUALITY],
        }

    if name in _GROWTH_VENDOR_COLUMNS:
        return {
            "source_class": "vendor_xlsx",
            "transform_chain": ["load year-varying public-cohort field from the validated legacy yearly export", "leave unavailable training-only values null"],
            "caveats": ["The current training-only pilot rows contain no values for this column."],
            "evidence_files": ["scripts/data_collection/pipeline.py", _QUALITY, _PILOT],
        }
    if name in _MIXED_CORRECTED_COLUMNS:
        return {
            "source_class": "unknown",
            "transform_chain": ["public rows: prefer validated corrected-yearly CSV values", "training-only rows: retain available unofficial yfinance values", "preserve missing values as null"],
            "caveats": ["Column-level provenance is mixed by universe_source, so no single upstream source class is asserted.", "Training-only yfinance values are unofficial and require KAP cross-check."],
            "evidence_files": [_CORRECTED, _PILOT, _QUALITY, "scripts/data_collection/integrate_pilot_tickers.py"],
        }
    if name in _MIXED_BALANCE_COLUMNS:
        return {
            "source_class": "unknown",
            "transform_chain": ["public rows: load accepted year-varying vendor values", "override reviewed 2024 public cells from corrected_balance_sheet_2024.csv", "training-only rows: retain available unofficial yfinance values", "preserve missing values as null"],
            "caveats": ["Column-level provenance is mixed by row and cannot be reduced to one verified source class.", "Rejected or unavailable cells remain null; no values are inferred."],
            "evidence_files": [_QUALITY, _CORRECTED, _PILOT, "scripts/data_collection/manual_ingest.py", "scripts/data_collection/integrate_pilot_tickers.py"],
        }

    if name in _VALUATION_COLUMNS:
        formulas = {
            "market_cap": "market_cap = Yahoo year-end price × manual shares outstanding",
            "enterprise_value": "enterprise_value = market_cap + net_debt",
            "pe_ratio": "pe_ratio = market_cap / net_income where net_income is positive",
            "pb_ratio": "pb_ratio = market_cap / equity where equity is positive and validated",
            "ev_ebitda": "ev_ebitda = enterprise_value / ebitda where ebitda is positive",
        }
        return {
            "source_class": "derived",
            "transform_chain": [formulas[name], "apply input and plausibility guards", "accept only year-varying output; otherwise leave null"],
            "caveats": ["Legacy snapshot values for this field were rejected as frozen; the accepted values are rebuilt from validated dependencies.", "Manual shares and external Yahoo prices are inputs; missing inputs remain null."],
            "evidence_files": [_VALUATION, _SHARES, _FROZEN, "scripts/data_collection/build_free_valuation_history.py"],
        }

    if name == "price_adjclose_t":
        return {
            "source_class": "yahoo_fetch",
            "transform_chain": ["load cached Yahoo adjusted close", "select the final valid price at or before year end T"],
            "caveats": ["Yahoo price coverage is incomplete; missing ticker-years remain null."],
            "evidence_files": ["scripts/data_collection/price_features.py", _PILOT, "docs/universe_audit.md"],
        }
    if name in _PRICE_DERIVED_COLUMNS:
        operations = {
            "price_data_available": "set 1 only when a valid Yahoo year-end price row exists",
            "price_history_years_available": "count valid Yahoo year-end observations available through T",
            "price_momentum_1y_pct": "compute percentage change from T-1 to T adjusted close",
            "price_momentum_2y_pct": "compute percentage change from T-2 to T adjusted close",
            "price_drawdown_from_3y_high_pct": "compare T adjusted close with the maximum adjusted close from T-2 through T",
            "price_vs_bist100_1y_pct": "subtract same-year BIST100 return from one-year price momentum",
        }
        return {
            "source_class": "derived",
            "transform_chain": [operations[name], "use only observations known by end of year T"],
            "caveats": ["Yahoo or benchmark coverage gaps propagate as null; no price values are filled."],
            "evidence_files": ["scripts/data_collection/price_features.py", _BENCHMARK, "docs/universe_audit.md"],
        }
    if name == "benchmark_same_year_return_pct":
        return {
            "source_class": "yahoo_fetch",
            "transform_chain": ["load validated BIST100 yearly return", "join benchmark year to feature year T"],
            "caveats": ["Benchmark coverage gaps remain null."],
            "evidence_files": [_BENCHMARK, "scripts/data_collection/collect_bist100_benchmark.py", "scripts/data_collection/price_features.py"],
        }

    if name == "same_year_return_pct":
        return {
            "source_class": "unknown",
            "transform_chain": ["public rows: retain realized annual return from the legacy yearly export", "training-only rows: derive return from adjacent Yahoo year-end adjusted closes"],
            "caveats": ["Column-level provenance is mixed by universe_source.", "This same-year outcome is analysis-only and never a feature."],
            "evidence_files": ["scripts/data_collection/pipeline.py", "scripts/data_collection/integrate_pilot_tickers.py", _QUALITY],
        }
    if name == "next_year_return_pct":
        return {
            "source_class": "derived",
            "transform_chain": ["shift each ticker's realized return from year T+1 back onto feature year T"],
            "caveats": ["Rows without a validated T+1 outcome remain inference-only."],
            "evidence_files": ["scripts/data_collection/pipeline.py", "scripts/data_collection/integrate_pilot_tickers.py", _QUALITY],
        }
    if name in {"next_year_rank_by_return", "next_year_return_percentile", "next_year_top_10pct_returner", "next_year_top_20pct_returner"}:
        operations = {
            "next_year_rank_by_return": "rank next_year_return_pct descending within target year",
            "next_year_return_percentile": "percentile-rank next_year_return_pct within target year",
            "next_year_top_10pct_returner": "flag target-year return percentile at or above 90",
            "next_year_top_20pct_returner": "flag target-year return percentile at or above 80",
        }
        return {
            "source_class": "derived",
            "transform_chain": [operations[name]],
            "caveats": ["Pilot ranks are computed within the pilot cohort rather than jointly with the public cohort."],
            "evidence_files": ["scripts/data_collection/pipeline.py", "scripts/data_collection/integrate_pilot_tickers.py", _PILOT],
        }
    if name == "next_year_bist100_return_pct":
        return {
            "source_class": "derived",
            "transform_chain": ["join validated BIST100 return on target_year = T+1"],
            "caveats": ["Benchmark targets are unavailable for training-only pilot rows and remain null."],
            "evidence_files": [_BENCHMARK, "scripts/data_collection/pipeline.py", "scripts/data_collection/integrate_pilot_tickers.py"],
        }
    if name == "next_year_excess_return_vs_bist100":
        return {
            "source_class": "derived",
            "transform_chain": ["next_year_return_pct - next_year_bist100_return_pct"],
            "caveats": ["Null company or benchmark targets propagate as null."],
            "evidence_files": [_BENCHMARK, "scripts/data_collection/pipeline.py"],
        }
    if name == "next_year_outperform_bist100":
        return {
            "source_class": "derived",
            "transform_chain": ["flag next_year_excess_return_vs_bist100 greater than zero"],
            "caveats": ["Null excess-return targets remain null."],
            "evidence_files": [_BENCHMARK, "scripts/data_collection/pipeline.py"],
        }

    return {
        "source_class": "unknown",
        "transform_chain": ["retain source value without a verified column-level lineage mapping"],
        "caveats": ["Provenance is unresolved; no source is inferred."],
        "evidence_files": [_QUALITY],
    }


def _feature_passports(registry: list[dict]) -> dict:
    passports = []
    for row in registry:
        details = _passport_details(row["column"])
        passport = {
            "name": row["column"],
            "registry_role": row["role"],
            "source_class": details["source_class"],
            "transform_chain": details["transform_chain"],
            "leakage_risk": row["leakage_risk"],
            "acceptance_status": _acceptance_status(row["role"]),
            "caveats": details["caveats"],
            "evidence_files": sorted(set(details["evidence_files"])),
        }
        if set(passport) != PASSPORT_FIELDS or passport["source_class"] not in SOURCE_CLASSES:
            raise ValueError(f"Invalid feature passport for {row['column']}")
        passports.append(passport)
    return {
        "schema_version": "1.0.0",
        "dataset": P.MODELING_CSV.name,
        "disclaimer": "Research/educational lineage record. Not investment advice or a guarantee of source accuracy.",
        "source_class_definitions": {
            "vendor_xlsx": "Verified column path from the legacy yearly vendor export.",
            "corrected_yearly_csv": "Validated corrected-yearly/manual CSV path.",
            "yahoo_fetch": "External Yahoo/yfinance price or benchmark observation.",
            "manual_shares": "Human-supplied shares-outstanding input; never inferred.",
            "derived": "Deterministic transformation of cited inputs.",
            "metadata": "Identifier, cohort, or row-state metadata.",
            "unknown": "A single verified column-level source cannot be asserted.",
        },
        "passports": passports,
    }


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
    PASSPORT_JSON.write_text(
        json.dumps(_feature_passports(reg), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


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

    report = V.validate(df, cfg)
    _data_dictionary(df)

    cfg.say("\n=== SUMMARY ===")
    cfg.say(f"  modeling rows: {report['rows']}  features: {report['n_features']}  "
            f"target rows: {report['rows_with_target']}  inference-only: {report['inference_only_rows']}")
    cfg.say(f"  benchmark: {'available' if report['benchmark_available'] else 'MISSING (manual CSV needed)'}")
    cfg.say(f"  valid for T->T+1 modeling: {report['valid_for_T_to_T1_modeling']}")
    cfg.say(f"  outputs in: {P.CLEAN_DIR}")
    return 0 if report["valid_for_T_to_T1_modeling"] else 2


if __name__ == "__main__":
    sys.exit(main())
