from datetime import datetime
from sqlalchemy import String, Float, Integer, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ScoreRun(Base):
    __tablename__ = "score_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    scoring_model_id: Mapped[int | None] = mapped_column(ForeignKey("scoring_models.id"), nullable=True)
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), default="rule_based_v1")
    total_score: Mapped[float | None] = mapped_column(Float)
    success_probability: Mapped[float | None] = mapped_column(Float)
    label_used: Mapped[str | None] = mapped_column(String(50))  # rule_based | logistic
    explanation_summary: Mapped[str | None] = mapped_column(Text)
    # V3: data quality
    data_completeness: Mapped[float | None] = mapped_column(Float)   # 0-1
    confidence_flag: Mapped[str | None] = mapped_column(String(20))  # high | medium | low
    # V3: rich explanation stored as JSON
    rich_explanation_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="score_runs")
    company: Mapped["Company"] = relationship("Company", back_populates="score_runs")
    scoring_model: Mapped["ScoringModel | None"] = relationship("ScoringModel", back_populates="score_runs")
    details: Mapped[list["ScoreDetail"]] = relationship(
        "ScoreDetail", back_populates="score_run", cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="score_run")


class ScoreDetail(Base):
    __tablename__ = "score_details"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    score_run_id: Mapped[int] = mapped_column(ForeignKey("score_runs.id"), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[float | None] = mapped_column(Float)
    normalized_value: Mapped[float | None] = mapped_column(Float)   # z-score or percentile
    weight: Mapped[float | None] = mapped_column(Float)
    contribution: Mapped[float | None] = mapped_column(Float)
    comment: Mapped[str | None] = mapped_column(String(500))
    # V3 explanation fields
    transition_value: Mapped[float | None] = mapped_column(Float)
    sector_z_score: Mapped[float | None] = mapped_column(Float)
    l2_explanation: Mapped[str | None] = mapped_column(Text)
    l3_counterfactual: Mapped[str | None] = mapped_column(Text)

    score_run: Mapped["ScoreRun"] = relationship("ScoreRun", back_populates="details")

