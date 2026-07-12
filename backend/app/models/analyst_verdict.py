"""Append-only analyst dissent records, isolated from every scoring path."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


ANALYST_VERDICTS = ("agree", "disagree", "abstain")
ANALYST_REASON_TYPES = (
    "evidence_quality",
    "data_gap",
    "methodology",
    "model_instability",
    "other",
)


class AnalystVerdict(Base):
    """A human research note that is never consumed by ranking or modeling code."""

    __tablename__ = "analyst_verdicts"
    __table_args__ = (
        Index("ix_analyst_verdicts_ticker_year", "ticker", "year"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    verdict: Mapped[str] = mapped_column(
        Enum(
            *ANALYST_VERDICTS,
            name="analyst_verdict_value",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    reason_type: Mapped[str] = mapped_column(
        Enum(
            *ANALYST_REASON_TYPES,
            name="analyst_verdict_reason_type",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User")
