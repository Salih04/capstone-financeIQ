from sqlalchemy import String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MetricTransition(Base):
    __tablename__ = "metric_transitions"
    __table_args__ = (
        UniqueConstraint("company_id", "from_period", "to_period", "metric_name",
                         name="uq_transition"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    from_period: Mapped[str] = mapped_column(String(20), nullable=False)
    to_period: Mapped[str] = mapped_column(String(20), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[float | None] = mapped_column(Float)
    new_value: Mapped[float | None] = mapped_column(Float)
    abs_change: Mapped[float | None] = mapped_column(Float)
    pct_change: Mapped[float | None] = mapped_column(Float)

    company: Mapped["Company"] = relationship("Company", back_populates="metric_transitions")


class SectorBenchmark(Base):
    """Stores sector-wide distribution statistics per metric per period."""
    __tablename__ = "sector_benchmarks"
    __table_args__ = (
        UniqueConstraint("sector_code", "period", "feature_name", name="uq_sector_bench"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sector_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False)
    mean_value: Mapped[float | None] = mapped_column(Float)
    std_value: Mapped[float | None] = mapped_column(Float)
    median_value: Mapped[float | None] = mapped_column(Float)
    p25: Mapped[float | None] = mapped_column(Float)
    p75: Mapped[float | None] = mapped_column(Float)
    sample_count: Mapped[int] = mapped_column(default=0)


class SectorNormalizedFeature(Base):
    """Per-company, per-period z-score and percentile for each feature."""
    __tablename__ = "sector_normalized_features"
    __table_args__ = (
        UniqueConstraint("company_id", "period", "feature_name", name="uq_sector_norm"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_value: Mapped[float | None] = mapped_column(Float)
    z_score: Mapped[float | None] = mapped_column(Float)
    percentile_rank: Mapped[float | None] = mapped_column(Float)

    company: Mapped["Company"] = relationship("Company", back_populates="sector_normalized")
