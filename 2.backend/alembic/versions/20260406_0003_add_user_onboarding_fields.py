"""add user onboarding fields

Revision ID: 20260406_0003
Revises: 20260406_0002
Create Date: 2026-04-06
"""

from alembic import op
import sqlalchemy as sa


revision = "20260406_0003"
down_revision = "20260406_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("user_type", sa.String(length=50), nullable=False, server_default="individual"))
    op.add_column("users", sa.Column("risk_level", sa.String(length=20), nullable=False, server_default="medium"))
    op.add_column("users", sa.Column("investment_scope", sa.Float(), nullable=True))
    op.add_column("users", sa.Column("sector_focus", sa.String(length=200), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "sector_focus")
    op.drop_column("users", "investment_scope")
    op.drop_column("users", "risk_level")
    op.drop_column("users", "user_type")
