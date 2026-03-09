from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector_code: Mapped[str | None] = mapped_column(String(50), index=True)
    sector: Mapped[str | None] = mapped_column(String(100))  # human-readable label
    description: Mapped[str | None] = mapped_column(String(1000))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    financial_statements: Mapped[list["FinancialStatement"]] = relationship(
        "FinancialStatement", back_populates="company", cascade="all, delete-orphan"
    )
    computed_metrics: Mapped[list["ComputedMetric"]] = relationship(
        "ComputedMetric", back_populates="company", cascade="all, delete-orphan"
    )
    metric_transitions: Mapped[list["MetricTransition"]] = relationship(
        "MetricTransition", back_populates="company", cascade="all, delete-orphan"
    )
    sector_normalized: Mapped[list["SectorNormalizedFeature"]] = relationship(
        "SectorNormalizedFeature", back_populates="company", cascade="all, delete-orphan"
    )
    score_runs: Mapped[list["ScoreRun"]] = relationship(
        "ScoreRun", back_populates="company", cascade="all, delete-orphan"
    )
