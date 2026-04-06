"""add forecast evaluation tables

Revision ID: 20260406_0002
Revises: 20260406_0001
Create Date: 2026-04-06
"""

from alembic import op
import sqlalchemy as sa


revision = "20260406_0002"
down_revision = "20260406_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "forecast_evaluation_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("sector", sa.String(length=200), nullable=False),
        sa.Column("model_type", sa.String(length=50), nullable=False),
        sa.Column("window_size", sa.Integer(), nullable=False),
        sa.Column("total_folds", sa.Integer(), nullable=False),
        sa.Column("mean_rank_stability", sa.Float(), nullable=True),
        sa.Column("mean_overlap_at_k", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_forecast_evaluation_runs_id"), "forecast_evaluation_runs", ["id"], unique=False)
    op.create_index(op.f("ix_forecast_evaluation_runs_sector"), "forecast_evaluation_runs", ["sector"], unique=False)

    op.create_table(
        "forecast_evaluation_folds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("evaluation_run_id", sa.Integer(), nullable=False),
        sa.Column("fold_index", sa.Integer(), nullable=False),
        sa.Column("train_year_start", sa.Integer(), nullable=False),
        sa.Column("train_year_end", sa.Integer(), nullable=False),
        sa.Column("test_year", sa.Integer(), nullable=False),
        sa.Column("rank_stability", sa.Float(), nullable=True),
        sa.Column("overlap_at_k", sa.Float(), nullable=True),
        sa.Column("metrics_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["evaluation_run_id"], ["forecast_evaluation_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_forecast_evaluation_folds_id"), "forecast_evaluation_folds", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_forecast_evaluation_folds_id"), table_name="forecast_evaluation_folds")
    op.drop_table("forecast_evaluation_folds")

    op.drop_index(op.f("ix_forecast_evaluation_runs_sector"), table_name="forecast_evaluation_runs")
    op.drop_index(op.f("ix_forecast_evaluation_runs_id"), table_name="forecast_evaluation_runs")
    op.drop_table("forecast_evaluation_runs")
