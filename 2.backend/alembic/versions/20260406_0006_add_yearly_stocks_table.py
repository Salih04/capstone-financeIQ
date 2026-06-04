"""add yearly_stocks table (trusted 2020-2025 dataset)

Revision ID: 20260406_0006
Revises: 20260406_0005
Create Date: 2026-06-04
"""

from alembic import op

from app.models.trusted import YearlyStock

revision = "20260406_0006"
down_revision = "20260406_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create directly from the single source-of-truth model definition so the
    # migration can never drift from app.models.trusted.YearlyStock.
    YearlyStock.__table__.create(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    YearlyStock.__table__.drop(bind=op.get_bind(), checkfirst=True)
