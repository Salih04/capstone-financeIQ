"""add quarterly fundamentals table

Revision ID: 20260406_0004
Revises: 20260406_0003
Create Date: 2026-04-06
"""

from alembic import op
import sqlalchemy as sa


revision = "20260406_0004"
down_revision = "20260406_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "quarterly_fundamentals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stock_code", sa.String(length=50), nullable=False),
        sa.Column("sector", sa.String(length=200), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("quarter", sa.Integer(), nullable=False),
        sa.Column("period", sa.String(length=20), nullable=False),
        sa.Column("net_income", sa.Float(), nullable=True),
        sa.Column("equity", sa.Float(), nullable=True),
        sa.Column("total_assets", sa.Float(), nullable=True),
        sa.Column("revenue", sa.Float(), nullable=True),
        sa.Column("gross_profit", sa.Float(), nullable=True),
        sa.Column("ebitda", sa.Float(), nullable=True),
        sa.Column("ocf", sa.Float(), nullable=True),
        sa.Column("capex", sa.Float(), nullable=True),
        sa.Column("total_debt", sa.Float(), nullable=True),
        sa.Column("cash", sa.Float(), nullable=True),
        sa.Column("ebit", sa.Float(), nullable=True),
        sa.Column("interest_expense", sa.Float(), nullable=True),
        sa.Column("inventory", sa.Float(), nullable=True),
        sa.Column("receivables", sa.Float(), nullable=True),
        sa.Column("net_working_capital", sa.Float(), nullable=True),
        sa.Column("market_cap", sa.Float(), nullable=True),
        sa.Column("book_value", sa.Float(), nullable=True),
        sa.Column("enterprise_value", sa.Float(), nullable=True),
        sa.Column("eps", sa.Float(), nullable=True),
        sa.Column("growth_rate", sa.Float(), nullable=True),
        sa.Column("current_assets", sa.Float(), nullable=True),
        sa.Column("current_liabilities", sa.Float(), nullable=True),
        sa.Column("dividend_per_share", sa.Float(), nullable=True),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stock_code", "period", name="uq_fundamentals_stock_period"),
    )

    op.create_index(op.f("ix_quarterly_fundamentals_id"), "quarterly_fundamentals", ["id"], unique=False)
    op.create_index(op.f("ix_quarterly_fundamentals_stock_code"), "quarterly_fundamentals", ["stock_code"], unique=False)
    op.create_index(op.f("ix_quarterly_fundamentals_sector"), "quarterly_fundamentals", ["sector"], unique=False)
    op.create_index(op.f("ix_quarterly_fundamentals_year"), "quarterly_fundamentals", ["year"], unique=False)
    op.create_index(op.f("ix_quarterly_fundamentals_period"), "quarterly_fundamentals", ["period"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_quarterly_fundamentals_period"), table_name="quarterly_fundamentals")
    op.drop_index(op.f("ix_quarterly_fundamentals_year"), table_name="quarterly_fundamentals")
    op.drop_index(op.f("ix_quarterly_fundamentals_sector"), table_name="quarterly_fundamentals")
    op.drop_index(op.f("ix_quarterly_fundamentals_stock_code"), table_name="quarterly_fundamentals")
    op.drop_index(op.f("ix_quarterly_fundamentals_id"), table_name="quarterly_fundamentals")
    op.drop_table("quarterly_fundamentals")
