"""
routers/ingestion.py – V3
=========================
POST /ingestion/import/csv       → full pipeline with job tracking
GET  /ingestion/jobs             → list recent ingestion jobs
GET  /ingestion/jobs/{id}        → single job detail
GET  /ingestion/dashboard        → data health dashboard
GET  /ingestion/issues           → recent data quality issues
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.ingestion import IngestionJob, DataQualityIssue
from app.models.user import User
from app.schemas.v3 import IngestionJobOut, DataQualityIssueOut
from app.services.ingestion_service import process_csv_import, get_ingestion_dashboard

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/import/csv", status_code=status.HTTP_200_OK)
async def import_csv(
    file: UploadFile = File(..., description="CSV with ticker, period, financials"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Full V3 ingestion: validates, upserts financials, computes ratios,
    detects quality issues, re-builds transitions + sector normalization,
    returns IngestionJob summary.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="Only .csv files are accepted.")

    content = await file.read()
    result = process_csv_import(db, content, triggered_by_user_id=current_user.id)
    return result


@router.get("/jobs", response_model=list[IngestionJobOut])
def list_jobs(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(IngestionJob)
        .order_by(IngestionJob.created_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/jobs/{job_id}")
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.get(IngestionJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found.")

    issues = (
        db.query(DataQualityIssue)
        .filter(DataQualityIssue.ingestion_job_id == job_id)
        .order_by(DataQualityIssue.detected_at.asc())
        .all()
    )
    return {
        "id": job.id,
        "source_name": job.source_name,
        "job_status": job.job_status,
        "items_total": job.items_total,
        "items_success": job.items_success,
        "items_failed": job.items_failed,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "error_summary": job.error_summary,
        "issues": [
            {
                "id": i.id,
                "issue_type": i.issue_type,
                "severity": i.severity,
                "issue_message": i.issue_message,
                "period": i.period,
                "company_id": i.company_id,
            }
            for i in issues
        ],
    }


@router.get("/dashboard")
def data_health_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_ingestion_dashboard(db)


@router.get("/issues", response_model=list[DataQualityIssueOut])
def list_issues(
    severity: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(DataQualityIssue)
    if severity:
        q = q.filter(DataQualityIssue.severity == severity)
    return q.order_by(DataQualityIssue.detected_at.desc()).limit(limit).all()

