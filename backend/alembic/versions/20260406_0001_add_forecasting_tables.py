"""add forecasting tables

Revision ID: 20260406_0001
Revises: 20260405_0000
Create Date: 2026-04-06
"""

from alembic import op
import sqlalchemy as sa


revision = "20260406_0001"
down_revision = "20260405_0000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "winner_cohort_rows",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_file", sa.String(length=255), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("sector", sa.String(length=200), nullable=False),
        sa.Column("stock_code", sa.String(length=50), nullable=False),
        sa.Column("period_return", sa.Float(), nullable=True),
        sa.Column("day_return", sa.Float(), nullable=True),
        sa.Column("volume", sa.Float(), nullable=True),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("return_1w", sa.Float(), nullable=True),
        sa.Column("return_1m", sa.Float(), nullable=True),
        sa.Column("return_3m", sa.Float(), nullable=True),
        sa.Column("return_6m", sa.Float(), nullable=True),
        sa.Column("return_ytd", sa.Float(), nullable=True),
        sa.Column("return_1y", sa.Float(), nullable=True),
        sa.Column("return_3y", sa.Float(), nullable=True),
        sa.Column("return_5y", sa.Float(), nullable=True),
        sa.Column("raw_payload_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("year", "stock_code", name="uq_winner_year_stock"),
    )
    op.create_index(op.f("ix_winner_cohort_rows_id"), "winner_cohort_rows", ["id"], unique=False)
    op.create_index(op.f("ix_winner_cohort_rows_year"), "winner_cohort_rows", ["year"], unique=False)
    op.create_index(op.f("ix_winner_cohort_rows_sector"), "winner_cohort_rows", ["sector"], unique=False)
    op.create_index(op.f("ix_winner_cohort_rows_stock_code"), "winner_cohort_rows", ["stock_code"], unique=False)

    op.create_table(
        "sector_parameter_rankings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("sector", sa.String(length=200), nullable=False),
        sa.Column("parameter_name", sa.String(length=100), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("year", "sector", "parameter_name", name="uq_sector_year_parameter"),
    )
    op.create_index(op.f("ix_sector_parameter_rankings_id"), "sector_parameter_rankings", ["id"], unique=False)
    op.create_index(op.f("ix_sector_parameter_rankings_year"), "sector_parameter_rankings", ["year"], unique=False)
    op.create_index(op.f("ix_sector_parameter_rankings_sector"), "sector_parameter_rankings", ["sector"], unique=False)

    op.create_table(
        "forecast_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("sector", sa.String(length=200), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_forecast_runs_id"), "forecast_runs", ["id"], unique=False)
    op.create_index(op.f("ix_forecast_runs_year"), "forecast_runs", ["year"], unique=False)
    op.create_index(op.f("ix_forecast_runs_sector"), "forecast_runs", ["sector"], unique=False)

    op.create_table(
        "forecast_predictions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("forecast_run_id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("sector", sa.String(length=200), nullable=False),
        sa.Column("stock_code", sa.String(length=50), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("explanation_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["forecast_run_id"], ["forecast_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("forecast_run_id", "stock_code", name="uq_forecast_run_stock"),
    )
    op.create_index(op.f("ix_forecast_predictions_id"), "forecast_predictions", ["id"], unique=False)
    op.create_index(op.f("ix_forecast_predictions_year"), "forecast_predictions", ["year"], unique=False)
    op.create_index(op.f("ix_forecast_predictions_sector"), "forecast_predictions", ["sector"], unique=False)
    op.create_index(op.f("ix_forecast_predictions_stock_code"), "forecast_predictions", ["stock_code"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_forecast_predictions_stock_code"), table_name="forecast_predictions")
    op.drop_index(op.f("ix_forecast_predictions_sector"), table_name="forecast_predictions")
    op.drop_index(op.f("ix_forecast_predictions_year"), table_name="forecast_predictions")
    op.drop_index(op.f("ix_forecast_predictions_id"), table_name="forecast_predictions")
    op.drop_table("forecast_predictions")

    op.drop_index(op.f("ix_forecast_runs_sector"), table_name="forecast_runs")
    op.drop_index(op.f("ix_forecast_runs_year"), table_name="forecast_runs")
    op.drop_index(op.f("ix_forecast_runs_id"), table_name="forecast_runs")
    op.drop_table("forecast_runs")

    op.drop_index(op.f("ix_sector_parameter_rankings_sector"), table_name="sector_parameter_rankings")
    op.drop_index(op.f("ix_sector_parameter_rankings_year"), table_name="sector_parameter_rankings")
    op.drop_index(op.f("ix_sector_parameter_rankings_id"), table_name="sector_parameter_rankings")
    op.drop_table("sector_parameter_rankings")

    op.drop_index(op.f("ix_winner_cohort_rows_stock_code"), table_name="winner_cohort_rows")
    op.drop_index(op.f("ix_winner_cohort_rows_sector"), table_name="winner_cohort_rows")
    op.drop_index(op.f("ix_winner_cohort_rows_year"), table_name="winner_cohort_rows")
    op.drop_index(op.f("ix_winner_cohort_rows_id"), table_name="winner_cohort_rows")
    op.drop_table("winner_cohort_rows")
