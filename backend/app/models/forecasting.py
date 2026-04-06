from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WinnerCohortRow(Base):
    __tablename__ = "winner_cohort_rows"
    __table_args__ = (
        UniqueConstraint("year", "stock_code", name="uq_winner_year_stock"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    sector: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    stock_code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)

    period_return: Mapped[float | None] = mapped_column(Float)
    day_return: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[float | None] = mapped_column(Float)
    price: Mapped[float | None] = mapped_column(Float)
    return_1w: Mapped[float | None] = mapped_column(Float)
    return_1m: Mapped[float | None] = mapped_column(Float)
    return_3m: Mapped[float | None] = mapped_column(Float)
    return_6m: Mapped[float | None] = mapped_column(Float)
    return_ytd: Mapped[float | None] = mapped_column(Float)
    return_1y: Mapped[float | None] = mapped_column(Float)
    return_3y: Mapped[float | None] = mapped_column(Float)
    return_5y: Mapped[float | None] = mapped_column(Float)

    raw_payload_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SectorParameterRanking(Base):
    __tablename__ = "sector_parameter_rankings"
    __table_args__ = (
        UniqueConstraint("year", "sector", "parameter_name", name="uq_sector_year_parameter"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    sector: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    parameter_name: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    details_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ForecastRun(Base):
    __tablename__ = "forecast_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    sector: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), default="success_dna_mvp_v1")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    predictions: Mapped[list["ForecastPrediction"]] = relationship(
        "ForecastPrediction", back_populates="run", cascade="all, delete-orphan"
    )


class ForecastPrediction(Base):
    __tablename__ = "forecast_predictions"
    __table_args__ = (
        UniqueConstraint("forecast_run_id", "stock_code", name="uq_forecast_run_stock"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    forecast_run_id: Mapped[int] = mapped_column(ForeignKey("forecast_runs.id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    sector: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    stock_code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    run: Mapped["ForecastRun"] = relationship("ForecastRun", back_populates="predictions")


class ForecastEvaluationRun(Base):
    __tablename__ = "forecast_evaluation_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    sector: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False, default="scoring")
    window_size: Mapped[int] = mapped_column(Integer, default=2)
    total_folds: Mapped[int] = mapped_column(Integer, default=0)
    mean_rank_stability: Mapped[float | None] = mapped_column(Float)
    mean_overlap_at_k: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    folds: Mapped[list["ForecastEvaluationFold"]] = relationship(
        "ForecastEvaluationFold", back_populates="evaluation_run", cascade="all, delete-orphan"
    )


class ForecastEvaluationFold(Base):
    __tablename__ = "forecast_evaluation_folds"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    evaluation_run_id: Mapped[int] = mapped_column(ForeignKey("forecast_evaluation_runs.id"), nullable=False)
    fold_index: Mapped[int] = mapped_column(Integer, nullable=False)
    train_year_start: Mapped[int] = mapped_column(Integer, nullable=False)
    train_year_end: Mapped[int] = mapped_column(Integer, nullable=False)
    test_year: Mapped[int] = mapped_column(Integer, nullable=False)
    rank_stability: Mapped[float | None] = mapped_column(Float)
    overlap_at_k: Mapped[float | None] = mapped_column(Float)
    metrics_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    evaluation_run: Mapped["ForecastEvaluationRun"] = relationship(
        "ForecastEvaluationRun", back_populates="folds"
    )


class QuarterlyFundamental(Base):
    __tablename__ = "quarterly_fundamentals"
    __table_args__ = (
        UniqueConstraint("stock_code", "period", name="uq_fundamentals_stock_period"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    stock_code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    sector: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    quarter: Mapped[int] = mapped_column(Integer, nullable=False)
    period: Mapped[str] = mapped_column(String(20), index=True, nullable=False)

    net_income: Mapped[float | None] = mapped_column(Float)
    equity: Mapped[float | None] = mapped_column(Float)
    total_assets: Mapped[float | None] = mapped_column(Float)
    revenue: Mapped[float | None] = mapped_column(Float)
    gross_profit: Mapped[float | None] = mapped_column(Float)
    ebitda: Mapped[float | None] = mapped_column(Float)
    ocf: Mapped[float | None] = mapped_column(Float)
    capex: Mapped[float | None] = mapped_column(Float)
    total_debt: Mapped[float | None] = mapped_column(Float)
    cash: Mapped[float | None] = mapped_column(Float)
    ebit: Mapped[float | None] = mapped_column(Float)
    interest_expense: Mapped[float | None] = mapped_column(Float)
    inventory: Mapped[float | None] = mapped_column(Float)
    receivables: Mapped[float | None] = mapped_column(Float)
    net_working_capital: Mapped[float | None] = mapped_column(Float)
    market_cap: Mapped[float | None] = mapped_column(Float)
    book_value: Mapped[float | None] = mapped_column(Float)
    enterprise_value: Mapped[float | None] = mapped_column(Float)
    eps: Mapped[float | None] = mapped_column(Float)
    growth_rate: Mapped[float | None] = mapped_column(Float)
    current_assets: Mapped[float | None] = mapped_column(Float)
    current_liabilities: Mapped[float | None] = mapped_column(Float)
    dividend_per_share: Mapped[float | None] = mapped_column(Float)
    price: Mapped[float | None] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
