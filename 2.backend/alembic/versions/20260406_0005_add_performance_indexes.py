"""add performance indexes

Revision ID: 20260406_0005
Revises: 20260406_0004
Create Date: 2026-04-29
"""
from alembic import op

revision = "20260406_0005"
down_revision = "20260406_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_computed_metrics_company_period",
        "computed_metrics",
        ["company_id", "period"],
        unique=False,
    )
    op.create_index(
        "ix_quarterly_fundamentals_stock_period",
        "quarterly_fundamentals",
        ["stock_code", "period"],
        unique=False,
    )
    op.create_index(
        "ix_sector_normalized_company_period",
        "sector_normalized_features",
        ["company_id", "period"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_sector_normalized_company_period", table_name="sector_normalized_features")
    op.drop_index("ix_quarterly_fundamentals_stock_period", table_name="quarterly_fundamentals")
    op.drop_index("ix_computed_metrics_company_period", table_name="computed_metrics")
