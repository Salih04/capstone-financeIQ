"""
Ingestion Service – V3
=======================
Centralizes the data ingestion pipeline with job tracking and data quality checks.
Called by routers/ingestion.py.

Pipeline per row:
  1. Validate required fields → DataQualityIssue(missing_field)
  2. Check duplicates
  3. Upsert FinancialStatement
  4. compute_ratios + upsert_computed_metrics
  5. Detect outliers → DataQualityIssue(outlier)
  6. Post-process: transitions | sector benchmarks | sector normalized
  7. Update IngestionJob counters
"""
from __future__ import annotations
import csv
import io
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.financial import FinancialStatement, ComputedMetric
from app.models.ingestion import IngestionJob, DataQualityIssue
from app.services.ratio_service import compute_ratios, upsert_computed_metrics
from app.services.transition_service import compute_transitions_for_company
from app.services.sector_service import recompute_sector_benchmarks, recompute_sector_normalized

_REQUIRED_FIELDS = ["ticker", "period", "revenue", "net_income", "total_assets", "total_equity"]
_FLOAT_FIELDS = [
    "revenue", "net_income", "operating_income", "gross_profit",
    "total_assets", "total_equity", "total_liabilities",
    "current_assets", "current_liabilities", "inventory",
    "cash", "operating_cash_flow",
]
_OUTLIER_THRESHOLDS = {
    "roa": (-2.0, 2.0),
    "roe": (-5.0, 5.0),
    "debt_to_equity": (0, 50.0),
    "current_ratio": (0, 30.0),
}


def process_csv_import(
    db: Session,
    csv_bytes: bytes,
    triggered_by_user_id: int | None = None,
) -> dict[str, Any]:
    """
    Full V3 ingestion pipeline from a CSV upload.
    Creates an IngestionJob row, processes each row, returns summary.
    """
    job = IngestionJob(
        source_name="csv_upload",
        triggered_by=triggered_by_user_id,
        job_status="running",
        started_at=datetime.now(timezone.utc),
        items_total=0,
        items_success=0,
        items_failed=0,
    )
    db.add(job)
    db.flush()

    try:
        text = csv_bytes.decode("utf-8-sig")
        reader = list(csv.DictReader(io.StringIO(text)))
        job.items_total = len(reader)
        db.flush()

        affected_companies: set[int] = set()
        affected_periods: set[str] = set()

        for row in reader:
            ticker = (row.get("ticker") or "").strip().upper()
            period = (row.get("period") or "").strip()

            # 1. Required field validation
            missing = [f for f in _REQUIRED_FIELDS if not row.get(f, "").strip()]
            if missing:
                issue = DataQualityIssue(
                    ingestion_job_id=job.id,
                    period=period or None,
                    issue_type="missing_field",
                    issue_message=f"Ticker={ticker} period={period}: missing {missing}",
                    severity="error",
                )
                db.add(issue)
                job.items_failed += 1
                db.flush()
                continue

            # 2. Resolve company
            company = db.query(Company).filter(Company.ticker == ticker).first()
            if not company:
                issue = DataQualityIssue(
                    ingestion_job_id=job.id,
                    period=period,
                    issue_type="missing_field",
                    issue_message=f"Ticker {ticker} not found in companies table.",
                    severity="warning",
                )
                db.add(issue)
                job.items_failed += 1
                db.flush()
                continue

            # 3. Parse floats
            def _f(key):
                v = row.get(key, "").strip()
                try:
                    return float(v) if v else None
                except ValueError:
                    return None

            # 4. Upsert FinancialStatement
            stmt = db.query(FinancialStatement).filter(
                FinancialStatement.company_id == company.id,
                FinancialStatement.period == period,
            ).first()

            if stmt is None:
                stmt = FinancialStatement(company_id=company.id, period=period)
                db.add(stmt)

            stmt.revenue = _f("revenue")
            stmt.net_income = _f("net_income")
            stmt.operating_income = _f("operating_income")
            stmt.gross_profit = _f("gross_profit")
            stmt.total_assets = _f("total_assets")
            stmt.total_equity = _f("total_equity")
            stmt.total_liabilities = _f("total_liabilities")
            stmt.current_assets = _f("current_assets")
            stmt.current_liabilities = _f("current_liabilities")
            stmt.inventory = _f("inventory")
            stmt.cash = _f("cash")
            stmt.operating_cash_flow = _f("operating_cash_flow")
            stmt.period_type = row.get("period_type", "quarterly").strip() or "quarterly"
            stmt.source_name = row.get("source_name", "csv_upload").strip() or "csv_upload"
            stmt.normalized_at = datetime.now(timezone.utc)
            db.flush()

            # 5. Compute & upsert ratios
            ratios = compute_ratios(stmt)
            upsert_computed_metrics(db, company.id, period, ratios)

            # 6. Outlier check
            for metric, (lo, hi) in _OUTLIER_THRESHOLDS.items():
                val = ratios.get(metric)
                if val is not None and (val < lo or val > hi):
                    db.add(DataQualityIssue(
                        ingestion_job_id=job.id,
                        company_id=company.id,
                        period=period,
                        issue_type="outlier",
                        issue_message=f"{metric}={val:.4f} outside [{lo}, {hi}] for {ticker}/{period}",
                        severity="warning",
                    ))

            affected_companies.add(company.id)
            affected_periods.add(period)
            job.items_success += 1
            db.flush()

        # 7. Post-process analytics
        all_periods = sorted(affected_periods)
        for cid in affected_companies:
            compute_transitions_for_company(db, cid)
        recompute_sector_benchmarks(db, all_periods)
        for cid in affected_companies:
            recompute_sector_normalized(db, cid, all_periods)

        job.job_status = "success" if job.items_failed == 0 else "partial"
        job.finished_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as exc:
        job.job_status = "failed"
        job.error_summary = str(exc)[:1000]
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise

    return {
        "job_id": job.id,
        "status": job.job_status,
        "items_total": job.items_total,
        "items_success": job.items_success,
        "items_failed": job.items_failed,
    }


def get_ingestion_dashboard(db: Session) -> dict[str, Any]:
    """Return data health metrics for the dashboard."""
    from app.models.company import Company as C
    from app.models.financial import FinancialStatement as FS

    jobs = db.query(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(20).all()
    issues = db.query(DataQualityIssue).order_by(DataQualityIssue.detected_at.desc()).limit(50).all()

    last_success = next((j for j in jobs if j.job_status == "success"), None)
    failed_count = sum(1 for j in jobs if j.job_status == "failed")

    # latest period per company
    latest_periods = db.query(FS.company_id, FS.period).order_by(
        FS.company_id.asc(), FS.period.desc()
    ).all()
    # deduplicate
    seen = {}
    for cid, per in latest_periods:
        if cid not in seen:
            seen[cid] = per
    stale_companies = sum(1 for per in seen.values() if per < "2024Q1")

    return {
        "last_ingestion_at": last_success.finished_at.isoformat() if last_success and last_success.finished_at else None,
        "failed_jobs_last20": failed_count,
        "total_jobs": len(jobs),
        "stale_companies": stale_companies,
        "recent_jobs": [
            {
                "id": j.id,
                "source_name": j.source_name,
                "job_status": j.job_status,
                "items_total": j.items_total,
                "items_success": j.items_success,
                "items_failed": j.items_failed,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "finished_at": j.finished_at.isoformat() if j.finished_at else None,
            }
            for j in jobs
        ],
        "recent_issues": [
            {
                "id": i.id,
                "issue_type": i.issue_type,
                "severity": i.severity,
                "issue_message": i.issue_message,
                "period": i.period,
                "detected_at": i.detected_at.isoformat() if i.detected_at else None,
            }
            for i in issues
        ],
    }
