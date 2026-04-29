"""
Model Governance – V3
=====================
Tables: ModelValidationRun, ModelFeatureImportance, LabelDefinition
"""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Float, Integer, ForeignKey, DateTime, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ModelValidationRun(Base):
    """Records a time-split validation experiment against a ScoringModel."""
    __tablename__ = "model_validation_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    scoring_model_id: Mapped[int] = mapped_column(ForeignKey("scoring_models.id"), nullable=False, index=True)
    validation_type: Mapped[str] = mapped_column(String(50), default="time_split")
    train_period_start: Mapped[str | None] = mapped_column(String(20))
    train_period_end: Mapped[str | None] = mapped_column(String(20))
    test_period_start: Mapped[str | None] = mapped_column(String(20))
    test_period_end: Mapped[str | None] = mapped_column(String(20))
    accuracy: Mapped[float | None] = mapped_column(Float)
    precision: Mapped[float | None] = mapped_column(Float)
    recall: Mapped[float | None] = mapped_column(Float)
    f1: Mapped[float | None] = mapped_column(Float)
    roc_auc: Mapped[float | None] = mapped_column(Float)
    support_total: Mapped[int | None] = mapped_column(Integer)
    support_positive: Mapped[int | None] = mapped_column(Integer)
    confusion_matrix_json: Mapped[str | None] = mapped_column(Text)  # [[tn,fp],[fn,tp]]
    calibration_summary: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    scoring_model: Mapped["ScoringModel"] = relationship("ScoringModel", back_populates="validation_runs")


class ModelFeatureImportance(Base):
    """Per-feature coefficient or importance for a trained model."""
    __tablename__ = "model_feature_importances"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    scoring_model_id: Mapped[int] = mapped_column(ForeignKey("scoring_models.id"), nullable=False, index=True)
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False)
    coefficient: Mapped[float | None] = mapped_column(Float)
    importance_rank: Mapped[int | None] = mapped_column(Integer)
    sign_direction: Mapped[str | None] = mapped_column(String(10))  # positive | negative

    scoring_model: Mapped["ScoringModel"] = relationship("ScoringModel", back_populates="feature_importances")


class LabelDefinition(Base):
    """Configures how 'success' is defined for labeling and training."""
    __tablename__ = "label_definitions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    # benchmark_type: sector_median | upper_quartile | absolute | risk_adjusted
    sector_benchmark_type: Mapped[str] = mapped_column(String(50), default="sector_median")
    horizon_months: Mapped[int] = mapped_column(Integer, default=12)
    # threshold_rule: score >= X, roa >= X, etc.
    threshold_rule: Mapped[str] = mapped_column(String(200), default="score >= 55")
    sector_adjustment_mode: Mapped[str] = mapped_column(String(50), default="z_score")
    success_threshold: Mapped[float] = mapped_column(Float, default=0.55)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
