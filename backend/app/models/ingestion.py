"""
Ingestion Observability – V3
============================
Tables: IngestionJob, DataQualityIssue
"""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Float, Integer, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class IngestionJob(Base):
    """Tracks a single batch data-ingestion run."""
    __tablename__ = "ingestion_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source_name: Mapped[str] = mapped_column(String(100), default="csv_upload")
    triggered_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    # status: queued | running | success | failed | partial
    job_status: Mapped[str] = mapped_column(String(20), default="queued")
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    items_total: Mapped[int] = mapped_column(Integer, default=0)
    items_success: Mapped[int] = mapped_column(Integer, default=0)
    items_failed: Mapped[int] = mapped_column(Integer, default=0)
    error_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    issues: Mapped[list["DataQualityIssue"]] = relationship(
        "DataQualityIssue", back_populates="ingestion_job", cascade="all, delete-orphan"
    )


class DataQualityIssue(Base):
    """Records a specific data-quality problem found during ingestion or normalization."""
    __tablename__ = "data_quality_issues"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ingestion_job_id: Mapped[int | None] = mapped_column(ForeignKey("ingestion_jobs.id"), nullable=True, index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True, index=True)
    period: Mapped[str | None] = mapped_column(String(20))
    # issue_type: missing_field | normalization_error | duplicate | stale_data | outlier
    issue_type: Mapped[str] = mapped_column(String(50), default="missing_field")
    issue_message: Mapped[str] = mapped_column(Text)
    # severity: info | warning | error
    severity: Mapped[str] = mapped_column(String(20), default="warning")
    detected_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    ingestion_job: Mapped["IngestionJob | None"] = relationship("IngestionJob", back_populates="issues")
