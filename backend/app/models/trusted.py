"""Trusted yearly stock table.

One row per (ticker, year) sourced ONLY from the trusted 2020-2025 XLSX files
(via data/trusted/stocks_2020_2025.csv). This is the single financial table the
app should grow to rely on. Column names mirror app.trusted_data.OUTPUT_COLUMNS.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class YearlyStock(Base):
    __tablename__ = "yearly_stocks"
    __table_args__ = (
        UniqueConstraint("ticker", "year", name="uq_yearly_stocks_ticker_year"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    indices: Mapped[str | None] = mapped_column(Text)
    source_file: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    annual_return_pct: Mapped[float | None] = mapped_column(Float)
    price: Mapped[float | None] = mapped_column(Float)
    daily_change_pct: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[float | None] = mapped_column(Float)
    return_1w_pct: Mapped[float | None] = mapped_column(Float)
    return_1m_pct: Mapped[float | None] = mapped_column(Float)
    return_3m_pct: Mapped[float | None] = mapped_column(Float)
    return_6m_pct: Mapped[float | None] = mapped_column(Float)
    return_ytd_pct: Mapped[float | None] = mapped_column(Float)
    return_1y_pct: Mapped[float | None] = mapped_column(Float)
    return_3y_pct: Mapped[float | None] = mapped_column(Float)
    return_5y_pct: Mapped[float | None] = mapped_column(Float)
    market_cap: Mapped[float | None] = mapped_column(Float)
    enterprise_value: Mapped[float | None] = mapped_column(Float)
    pe: Mapped[float | None] = mapped_column(Float)
    pb: Mapped[float | None] = mapped_column(Float)
    ev_sales: Mapped[float | None] = mapped_column(Float)
    ev_ebitda: Mapped[float | None] = mapped_column(Float)
    peg: Mapped[float | None] = mapped_column(Float)
    gross_margin_pct: Mapped[float | None] = mapped_column(Float)
    ebitda_margin_pct: Mapped[float | None] = mapped_column(Float)
    net_margin_pct: Mapped[float | None] = mapped_column(Float)
    roe_pct: Mapped[float | None] = mapped_column(Float)
    roic_pct: Mapped[float | None] = mapped_column(Float)
    roa_pct: Mapped[float | None] = mapped_column(Float)
    working_capital: Mapped[float | None] = mapped_column(Float)
    net_debt: Mapped[float | None] = mapped_column(Float)
    net_debt_ebitda: Mapped[float | None] = mapped_column(Float)
    net_fin_exp_ebitda: Mapped[float | None] = mapped_column(Float)
    current_ratio: Mapped[float | None] = mapped_column(Float)
    leverage_ratio: Mapped[float | None] = mapped_column(Float)
    financial_debt_ratio: Mapped[float | None] = mapped_column(Float)
    revenue_growth_pct: Mapped[float | None] = mapped_column(Float)
    gross_profit_growth_pct: Mapped[float | None] = mapped_column(Float)
    ebitda_growth_pct: Mapped[float | None] = mapped_column(Float)
    operating_income_growth_pct: Mapped[float | None] = mapped_column(Float)
    net_income_growth_pct: Mapped[float | None] = mapped_column(Float)
    total_assets: Mapped[float | None] = mapped_column(Float)
    current_assets: Mapped[float | None] = mapped_column(Float)
    non_current_assets: Mapped[float | None] = mapped_column(Float)
    short_term_liabilities: Mapped[float | None] = mapped_column(Float)
    long_term_liabilities: Mapped[float | None] = mapped_column(Float)
    equity: Mapped[float | None] = mapped_column(Float)
    revenue: Mapped[float | None] = mapped_column(Float)
    gross_profit: Mapped[float | None] = mapped_column(Float)
    operating_income: Mapped[float | None] = mapped_column(Float)
    ebitda: Mapped[float | None] = mapped_column(Float)
    net_income: Mapped[float | None] = mapped_column(Float)
    free_cash_flow: Mapped[float | None] = mapped_column(Float)
    ocf: Mapped[float | None] = mapped_column(Float)
    icf: Mapped[float | None] = mapped_column(Float)
    fcf_financing: Mapped[float | None] = mapped_column(Float)
