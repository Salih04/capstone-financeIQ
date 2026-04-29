"""
scripts/rebuild_financial_pipeline.py
======================================
Full pipeline rebuild for the Finance Platform.

Single source of truth flow:
  CLEANED_Financial → QuarterlyFundamental → ComputedMetric → Scoring / Analysis

Steps:
  1. Clear computed_metrics
  2. Import CLEANED_Financial → QuarterlyFundamental
  3. Generate ComputedMetric from QuarterlyFundamental
  4. Generate MetricTransition (per company)
  5. Generate SectorBenchmark (per period)
  6. Generate SectorNormalizedFeature (per company, per period)
  7. Clear sector_parameter_rankings
  8. Print validation summary

Usage:
  cd 2.backend
  python -m scripts.rebuild_financial_pipeline
"""
from __future__ import annotations

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func

from app.database import SessionLocal
from app.models.analytics import MetricTransition, SectorBenchmark, SectorNormalizedFeature
from app.models.company import Company
from app.models.financial import ComputedMetric
from app.models.forecasting import QuarterlyFundamental, SectorParameterRanking
from app.services.sector_service import recompute_sector_benchmarks, recompute_sector_normalized
from app.services.transition_service import compute_transitions_for_company


def _safe_div(n, d):
    if n is None or d is None or d == 0:
        return None
    return n / d


def _compute_ratios_from_qf(row: QuarterlyFundamental) -> dict:
    quick_assets = (
        ((row.current_assets or 0) - (row.inventory or 0))
        if row.current_assets is not None else None
    )
    return {
        "roa": _safe_div(row.net_income, row.total_assets),
        "roe": _safe_div(row.net_income, row.equity),
        "operating_margin": _safe_div(row.ebit, row.revenue),
        "net_margin": _safe_div(row.net_income, row.revenue),
        "current_ratio": _safe_div(row.current_assets, row.current_liabilities),
        "quick_ratio": _safe_div(quick_assets, row.current_liabilities),
        "cash_ratio": _safe_div(row.cash, row.current_liabilities),
        "debt_to_equity": _safe_div(row.total_debt, row.equity),
        "debt_to_assets": _safe_div(row.total_debt, row.total_assets),
        # Returns None when ocf is None — not faked as 0
        "ocf_to_debt": _safe_div(row.ocf, row.total_debt),
        "ocf_to_assets": _safe_div(row.ocf, row.total_assets),
        "cash_flow_margin": _safe_div(row.ocf, row.revenue),
    }


# ── Step 1 ────────────────────────────────────────────────────────────────────

def step_clear_computed_metrics(db) -> None:
    deleted = db.query(ComputedMetric).delete()
    db.commit()
    print(f"  [1] Cleared {deleted} computed_metric rows.")


# ── Step 2 ────────────────────────────────────────────────────────────────────

def step_import_cleaned_financial() -> None:
    print("  [2] Importing CLEANED_Financial → QuarterlyFundamental ...")
    from scripts.import_cleaned_financial import main as import_main
    import_main()


# ── Step 3 ────────────────────────────────────────────────────────────────────

def step_generate_computed_metrics(db) -> None:
    print("  [3] Generating ComputedMetric from QuarterlyFundamental ...")
    qf_rows = (
        db.query(QuarterlyFundamental)
        .order_by(QuarterlyFundamental.stock_code, QuarterlyFundamental.period)
        .all()
    )

    created = updated = skipped = 0
    for row in qf_rows:
        company = db.query(Company).filter(Company.ticker == row.stock_code).first()
        if not company:
            skipped += 1
            continue

        ratios = _compute_ratios_from_qf(row)

        existing = (
            db.query(ComputedMetric)
            .filter(
                ComputedMetric.company_id == company.id,
                ComputedMetric.period == row.period,
            )
            .first()
        )
        if existing:
            for k, v in ratios.items():
                setattr(existing, k, v)
            updated += 1
        else:
            db.add(ComputedMetric(company_id=company.id, period=row.period, **ratios))
            created += 1

    db.commit()
    print(
        f"       created={created}  updated={updated}  "
        f"skipped={skipped} (no matching company in DB)"
    )


# ── Step 4 ────────────────────────────────────────────────────────────────────

def step_generate_transitions(db) -> None:
    print("  [4] Generating MetricTransition ...")
    companies = db.query(Company).filter(Company.is_active.is_(True)).all()
    total = 0
    for company in companies:
        total += compute_transitions_for_company(db, company.id)
    print(f"       {total} transition rows upserted across {len(companies)} companies.")


# ── Step 5 ────────────────────────────────────────────────────────────────────

def step_generate_sector_benchmarks(db) -> None:
    print("  [5] Generating SectorBenchmark ...")
    periods = [r[0] for r in db.query(ComputedMetric.period).distinct().all()]
    total = 0
    for period in sorted(periods):
        total += recompute_sector_benchmarks(db, period)
    print(f"       {total} benchmark rows upserted across {len(periods)} periods.")


# ── Step 6 ────────────────────────────────────────────────────────────────────

def step_generate_sector_normalized(db) -> None:
    print("  [6] Generating SectorNormalizedFeature ...")
    companies = db.query(Company).filter(Company.is_active.is_(True)).all()
    periods = [r[0] for r in db.query(ComputedMetric.period).distinct().all()]
    total = 0
    for company in companies:
        for period in periods:
            total += recompute_sector_normalized(db, company.id, period)
    print(f"       {total} normalized feature rows upserted.")


# ── Step 7 ────────────────────────────────────────────────────────────────────

def step_clear_sector_parameter_rankings(db) -> None:
    deleted = db.query(SectorParameterRanking).delete()
    db.commit()
    print(f"  [7] Cleared {deleted} sector_parameter_ranking rows.")


# ── Step 8 ────────────────────────────────────────────────────────────────────

def step_validation_summary(db) -> None:
    print("\n  [8] Validation Summary")
    print("  " + "-" * 42)

    total_companies = db.query(Company).count()
    total_periods = db.query(ComputedMetric.period).distinct().count()
    total_metrics = db.query(ComputedMetric).count()

    missing_revenue = (
        db.query(QuarterlyFundamental)
        .filter(QuarterlyFundamental.revenue.is_(None))
        .count()
    )
    missing_net_income = (
        db.query(QuarterlyFundamental)
        .filter(QuarterlyFundamental.net_income.is_(None))
        .count()
    )
    missing_equity = (
        db.query(QuarterlyFundamental)
        .filter(QuarterlyFundamental.equity.is_(None))
        .count()
    )
    missing_total_assets = (
        db.query(QuarterlyFundamental)
        .filter(QuarterlyFundamental.total_assets.is_(None))
        .count()
    )
    missing_ocf = (
        db.query(QuarterlyFundamental)
        .filter(QuarterlyFundamental.ocf.is_(None))
        .count()
    )

    dup_rows = (
        db.query(
            QuarterlyFundamental.stock_code,
            QuarterlyFundamental.period,
            func.count().label("cnt"),
        )
        .group_by(QuarterlyFundamental.stock_code, QuarterlyFundamental.period)
        .having(func.count() > 1)
        .all()
    )

    print(f"  Total companies:              {total_companies}")
    print(f"  Total distinct periods:       {total_periods}")
    print(f"  Total ComputedMetric rows:    {total_metrics}")
    print(f"  Missing revenue:              {missing_revenue}")
    print(f"  Missing net_income:           {missing_net_income}")
    print(f"  Missing equity:               {missing_equity}")
    print(f"  Missing total_assets:         {missing_total_assets}")
    print(f"  Missing operating_cash_flow:  {missing_ocf}")
    print(f"  Duplicate stock+period rows:  {len(dup_rows)}")
    if dup_rows:
        for sc, period, cnt in dup_rows[:5]:
            print(f"    ↳ {sc} {period}: {cnt} rows")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 50)
    print("FINANCE PLATFORM – REBUILD PIPELINE")
    print("=" * 50)

    db = SessionLocal()
    try:
        step_clear_computed_metrics(db)
        step_import_cleaned_financial()
        step_generate_computed_metrics(db)
        step_generate_transitions(db)
        step_generate_sector_benchmarks(db)
        step_generate_sector_normalized(db)
        step_clear_sector_parameter_rankings(db)
        step_validation_summary(db)
    finally:
        db.close()

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
