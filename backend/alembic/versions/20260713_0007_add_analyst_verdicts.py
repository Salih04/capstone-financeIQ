"""add append-only analyst verdict ledger

Revision ID: 20260713_0007
Revises: 20260406_0006
Create Date: 2026-07-13
"""

from alembic import op
import sqlalchemy as sa


revision = "20260713_0007"
down_revision = "20260406_0006"
branch_labels = None
depends_on = None


verdict_enum = sa.Enum(
    "agree",
    "disagree",
    "abstain",
    name="analyst_verdict_value",
    native_enum=False,
    create_constraint=True,
)
reason_type_enum = sa.Enum(
    "evidence_quality",
    "data_gap",
    "methodology",
    "model_instability",
    "other",
    name="analyst_verdict_reason_type",
    native_enum=False,
    create_constraint=True,
)


def upgrade() -> None:
    op.create_table(
        "analyst_verdicts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("verdict", verdict_enum, nullable=False),
        sa.Column("reason_type", reason_type_enum, nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_analyst_verdicts_ticker_year",
        "analyst_verdicts",
        ["ticker", "year"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_analyst_verdicts_ticker_year", table_name="analyst_verdicts")
    op.drop_table("analyst_verdicts")
