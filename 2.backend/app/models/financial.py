from datetime import datetime
from sqlalchemy import String, Float, Integer, ForeignKey, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FinancialStatement(Base):
    __tablename__ = "financial_statements"
    __table_args__ = (UniqueConstraint("company_id", "period", name="uq_fin_company_period"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. "2023Q4"
    period_type: Mapped[str] = mapped_column(String(20), default="quarterly")  # quarterly | annual
    source_name: Mapped[str] = mapped_column(String(100), default="manual")
    raw_payload_json: Mapped[str | None] = mapped_column(Text)
    normalized_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Income statement
    revenue: Mapped[float | None] = mapped_column(Float)
    net_income: Mapped[float | None] = mapped_column(Float)
    operating_income: Mapped[float | None] = mapped_column(Float)
    gross_profit: Mapped[float | None] = mapped_column(Float)

    # Balance sheet
    total_assets: Mapped[float | None] = mapped_column(Float)
    total_equity: Mapped[float | None] = mapped_column(Float)
    total_liabilities: Mapped[float | None] = mapped_column(Float)
    current_assets: Mapped[float | None] = mapped_column(Float)
    current_liabilities: Mapped[float | None] = mapped_column(Float)
    inventory: Mapped[float | None] = mapped_column(Float)
    cash: Mapped[float | None] = mapped_column(Float)

    # Cash flow
    operating_cash_flow: Mapped[float | None] = mapped_column(Float)

    company: Mapped["Company"] = relationship("Company", back_populates="financial_statements")


class ComputedMetric(Base):
    __tablename__ = "computed_metrics"
    __table_args__ = (UniqueConstraint("company_id", "period", name="uq_metric_company_period"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(20), nullable=False)

    # Profitability
    roa: Mapped[float | None] = mapped_column(Float)
    roe: Mapped[float | None] = mapped_column(Float)
    operating_margin: Mapped[float | None] = mapped_column(Float)
    net_margin: Mapped[float | None] = mapped_column(Float)

    # Liquidity
    current_ratio: Mapped[float | None] = mapped_column(Float)
    quick_ratio: Mapped[float | None] = mapped_column(Float)
    cash_ratio: Mapped[float | None] = mapped_column(Float)

    # Leverage
    debt_to_equity: Mapped[float | None] = mapped_column(Float)
    debt_to_assets: Mapped[float | None] = mapped_column(Float)

    # Cash-flow strength
    ocf_to_debt: Mapped[float | None] = mapped_column(Float)
    ocf_to_assets: Mapped[float | None] = mapped_column(Float)
    cash_flow_margin: Mapped[float | None] = mapped_column(Float)

    company: Mapped["Company"] = relationship("Company", back_populates="computed_metrics")
