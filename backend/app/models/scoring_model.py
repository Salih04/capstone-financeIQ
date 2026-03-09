from datetime import datetime
from sqlalchemy import String, Float, Integer, ForeignKey, DateTime, Text, Boolean, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ScoringModel(Base):
    __tablename__ = "scoring_models"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # model_type: rule_based | logistic | tree_based
    model_type: Mapped[str] = mapped_column(String(50), default="rule_based")
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    description: Mapped[str | None] = mapped_column(String(500))
    config_json: Mapped[str | None] = mapped_column(Text)   # serialized extra config

    # V3 Model Registry fields
    # status: draft | active | archived
    status: Mapped[str] = mapped_column(String(20), default="draft")
    feature_set_version: Mapped[str | None] = mapped_column(String(50))  # e.g. "v2_12metrics"
    label_strategy: Mapped[str | None] = mapped_column(String(100))       # e.g. "sector_median_12m"
    evaluation_horizon: Mapped[str | None] = mapped_column(String(20))    # e.g. "12m"
    trained_at: Mapped[datetime | None] = mapped_column(DateTime)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime)
    validation_summary_json: Mapped[str | None] = mapped_column(Text)     # latest validation metrics as JSON

    # Legacy field kept for compatibility
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    metrics: Mapped[list["ScoringModelMetric"]] = relationship(
        "ScoringModelMetric", back_populates="scoring_model", cascade="all, delete-orphan"
    )
    score_runs: Mapped[list["ScoreRun"]] = relationship("ScoreRun", back_populates="scoring_model")
    validation_runs: Mapped[list["ModelValidationRun"]] = relationship(
        "ModelValidationRun", back_populates="scoring_model", cascade="all, delete-orphan"
    )
    feature_importances: Mapped[list["ModelFeatureImportance"]] = relationship(
        "ModelFeatureImportance", back_populates="scoring_model", cascade="all, delete-orphan"
    )


class ScoringModelMetric(Base):
    __tablename__ = "scoring_model_metrics"
    __table_args__ = (
        UniqueConstraint("scoring_model_id", "feature_name", name="uq_model_feature"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    scoring_model_id: Mapped[int] = mapped_column(ForeignKey("scoring_models.id"), nullable=False)
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    threshold_min: Mapped[float | None] = mapped_column(Float)
    threshold_max: Mapped[float | None] = mapped_column(Float)
    direction: Mapped[str] = mapped_column(String(20), default="higher")  # higher | lower | higher_better | lower_better

    scoring_model: Mapped["ScoringModel"] = relationship("ScoringModel", back_populates="metrics")
