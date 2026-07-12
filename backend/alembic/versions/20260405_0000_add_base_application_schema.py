"""add base application schema

Revision ID: 20260405_0000
Revises:
Create Date: 2026-07-12

The original Alembic history started with forecasting tables, even though those
tables referenced the pre-existing application schema.  This baseline records
that schema explicitly so a fresh database can migrate from an empty state.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260405_0000"
down_revision = None
branch_labels = None
depends_on = None


def _created_at() -> sa.Column:
    return sa.Column(
        "created_at",
        sa.DateTime(),
        server_default=sa.text("now()"),
        nullable=False,
    )


def _index(table_name: str, column_name: str, *, unique: bool = False) -> None:
    op.create_index(
        op.f(f"ix_{table_name}_{column_name}"),
        table_name,
        [column_name],
        unique=unique,
    )


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("sector_code", sa.String(length=50), nullable=True),
        sa.Column("sector", sa.String(length=100), nullable=True),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("companies", "id")
    _index("companies", "ticker", unique=True)
    _index("companies", "sector_code")

    op.create_table(
        "sector_benchmarks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sector_code", sa.String(length=50), nullable=False),
        sa.Column("period", sa.String(length=20), nullable=False),
        sa.Column("feature_name", sa.String(length=100), nullable=False),
        sa.Column("mean_value", sa.Float(), nullable=True),
        sa.Column("std_value", sa.Float(), nullable=True),
        sa.Column("median_value", sa.Float(), nullable=True),
        sa.Column("p25", sa.Float(), nullable=True),
        sa.Column("p75", sa.Float(), nullable=True),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "sector_code", "period", "feature_name", name="uq_sector_bench"
        ),
    )
    _index("sector_benchmarks", "id")
    _index("sector_benchmarks", "sector_code")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("failed_login_count", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("users", "id")
    _index("users", "email", unique=True)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action_type", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("old_value_json", sa.Text(), nullable=True),
        sa.Column("new_value_json", sa.Text(), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=True),
        _created_at(),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("audit_logs", "id")
    _index("audit_logs", "actor_user_id")
    _index("audit_logs", "action_type")
    _index("audit_logs", "created_at")

    op.create_table(
        "computed_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("period", sa.String(length=20), nullable=False),
        sa.Column("roa", sa.Float(), nullable=True),
        sa.Column("roe", sa.Float(), nullable=True),
        sa.Column("operating_margin", sa.Float(), nullable=True),
        sa.Column("net_margin", sa.Float(), nullable=True),
        sa.Column("current_ratio", sa.Float(), nullable=True),
        sa.Column("quick_ratio", sa.Float(), nullable=True),
        sa.Column("cash_ratio", sa.Float(), nullable=True),
        sa.Column("debt_to_equity", sa.Float(), nullable=True),
        sa.Column("debt_to_assets", sa.Float(), nullable=True),
        sa.Column("ocf_to_debt", sa.Float(), nullable=True),
        sa.Column("ocf_to_assets", sa.Float(), nullable=True),
        sa.Column("cash_flow_margin", sa.Float(), nullable=True),
        sa.Column("gross_profit_margin", sa.Float(), nullable=True),
        sa.Column("ebitda_margin", sa.Float(), nullable=True),
        sa.Column("roic", sa.Float(), nullable=True),
        sa.Column("revenue_growth", sa.Float(), nullable=True),
        sa.Column("ebitda_growth", sa.Float(), nullable=True),
        sa.Column("net_income_growth", sa.Float(), nullable=True),
        sa.Column("pe_ratio", sa.Float(), nullable=True),
        sa.Column("pb_ratio", sa.Float(), nullable=True),
        sa.Column("ev_ebitda", sa.Float(), nullable=True),
        sa.Column("ev_sales", sa.Float(), nullable=True),
        sa.Column("peg_ratio", sa.Float(), nullable=True),
        sa.Column("working_capital", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "period", name="uq_metric_company_period"),
    )
    _index("computed_metrics", "id")
    _index("computed_metrics", "company_id")

    op.create_table(
        "financial_statements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("period", sa.String(length=20), nullable=False),
        sa.Column("period_type", sa.String(length=20), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("raw_payload_json", sa.Text(), nullable=True),
        sa.Column("normalized_at", sa.DateTime(), nullable=True),
        sa.Column("revenue", sa.Float(), nullable=True),
        sa.Column("net_income", sa.Float(), nullable=True),
        sa.Column("operating_income", sa.Float(), nullable=True),
        sa.Column("gross_profit", sa.Float(), nullable=True),
        sa.Column("total_assets", sa.Float(), nullable=True),
        sa.Column("total_equity", sa.Float(), nullable=True),
        sa.Column("total_liabilities", sa.Float(), nullable=True),
        sa.Column("current_assets", sa.Float(), nullable=True),
        sa.Column("current_liabilities", sa.Float(), nullable=True),
        sa.Column("inventory", sa.Float(), nullable=True),
        sa.Column("cash", sa.Float(), nullable=True),
        sa.Column("operating_cash_flow", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "period", name="uq_fin_company_period"),
    )
    _index("financial_statements", "id")
    _index("financial_statements", "company_id")

    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("triggered_by", sa.Integer(), nullable=True),
        sa.Column("job_status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("items_total", sa.Integer(), nullable=False),
        sa.Column("items_success", sa.Integer(), nullable=False),
        sa.Column("items_failed", sa.Integer(), nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
        _created_at(),
        sa.ForeignKeyConstraint(["triggered_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("ingestion_jobs", "id")

    op.create_table(
        "label_definitions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("sector_benchmark_type", sa.String(length=50), nullable=False),
        sa.Column("horizon_months", sa.Integer(), nullable=False),
        sa.Column("threshold_rule", sa.String(length=200), nullable=False),
        sa.Column("sector_adjustment_mode", sa.String(length=50), nullable=False),
        sa.Column("success_threshold", sa.Float(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        _created_at(),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("label_definitions", "id")

    op.create_table(
        "metric_transitions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("from_period", sa.String(length=20), nullable=False),
        sa.Column("to_period", sa.String(length=20), nullable=False),
        sa.Column("metric_name", sa.String(length=100), nullable=False),
        sa.Column("old_value", sa.Float(), nullable=True),
        sa.Column("new_value", sa.Float(), nullable=True),
        sa.Column("abs_change", sa.Float(), nullable=True),
        sa.Column("pct_change", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id",
            "from_period",
            "to_period",
            "metric_name",
            name="uq_transition",
        ),
    )
    _index("metric_transitions", "id")
    _index("metric_transitions", "company_id")

    op.create_table(
        "scoring_models",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("model_type", sa.String(length=50), nullable=False),
        sa.Column("version", sa.String(length=20), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("config_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("feature_set_version", sa.String(length=50), nullable=True),
        sa.Column("label_strategy", sa.String(length=100), nullable=True),
        sa.Column("evaluation_horizon", sa.String(length=20), nullable=True),
        sa.Column("trained_at", sa.DateTime(), nullable=True),
        sa.Column("activated_at", sa.DateTime(), nullable=True),
        sa.Column("validation_summary_json", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        _created_at(),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("scoring_models", "id")

    op.create_table(
        "sector_normalized_features",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("period", sa.String(length=20), nullable=False),
        sa.Column("feature_name", sa.String(length=100), nullable=False),
        sa.Column("raw_value", sa.Float(), nullable=True),
        sa.Column("z_score", sa.Float(), nullable=True),
        sa.Column("percentile_rank", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "period", "feature_name", name="uq_sector_norm"),
    )
    _index("sector_normalized_features", "id")
    _index("sector_normalized_features", "company_id")

    op.create_table(
        "stock_returns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("period", sa.String(length=20), nullable=False),
        sa.Column("annual_return", sa.Float(), nullable=True),
        sa.Column("return_1w", sa.Float(), nullable=True),
        sa.Column("return_1m", sa.Float(), nullable=True),
        sa.Column("return_3m", sa.Float(), nullable=True),
        sa.Column("return_6m", sa.Float(), nullable=True),
        sa.Column("return_ytd", sa.Float(), nullable=True),
        sa.Column("return_1y", sa.Float(), nullable=True),
        sa.Column("return_3y", sa.Float(), nullable=True),
        sa.Column("return_5y", sa.Float(), nullable=True),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("market_cap", sa.Float(), nullable=True),
        sa.Column("enterprise_value", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "period", name="uq_return_company_period"),
    )
    _index("stock_returns", "id")
    _index("stock_returns", "company_id")

    op.create_table(
        "data_quality_issues",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ingestion_job_id", sa.Integer(), nullable=True),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("period", sa.String(length=20), nullable=True),
        sa.Column("issue_type", sa.String(length=50), nullable=False),
        sa.Column("issue_message", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column(
            "detected_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["ingestion_job_id"], ["ingestion_jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("data_quality_issues", "id")
    _index("data_quality_issues", "company_id")
    _index("data_quality_issues", "ingestion_job_id")

    op.create_table(
        "model_feature_importances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scoring_model_id", sa.Integer(), nullable=False),
        sa.Column("feature_name", sa.String(length=100), nullable=False),
        sa.Column("coefficient", sa.Float(), nullable=True),
        sa.Column("importance_rank", sa.Integer(), nullable=True),
        sa.Column("sign_direction", sa.String(length=10), nullable=True),
        sa.ForeignKeyConstraint(["scoring_model_id"], ["scoring_models.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("model_feature_importances", "id")
    _index("model_feature_importances", "scoring_model_id")

    op.create_table(
        "model_validation_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scoring_model_id", sa.Integer(), nullable=False),
        sa.Column("validation_type", sa.String(length=50), nullable=False),
        sa.Column("train_period_start", sa.String(length=20), nullable=True),
        sa.Column("train_period_end", sa.String(length=20), nullable=True),
        sa.Column("test_period_start", sa.String(length=20), nullable=True),
        sa.Column("test_period_end", sa.String(length=20), nullable=True),
        sa.Column("accuracy", sa.Float(), nullable=True),
        sa.Column("precision", sa.Float(), nullable=True),
        sa.Column("recall", sa.Float(), nullable=True),
        sa.Column("f1", sa.Float(), nullable=True),
        sa.Column("roc_auc", sa.Float(), nullable=True),
        sa.Column("support_total", sa.Integer(), nullable=True),
        sa.Column("support_positive", sa.Integer(), nullable=True),
        sa.Column("confusion_matrix_json", sa.Text(), nullable=True),
        sa.Column("calibration_summary", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        _created_at(),
        sa.ForeignKeyConstraint(["scoring_model_id"], ["scoring_models.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("model_validation_runs", "id")
    _index("model_validation_runs", "scoring_model_id")

    op.create_table(
        "score_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("scoring_model_id", sa.Integer(), nullable=True),
        sa.Column("period", sa.String(length=20), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=True),
        sa.Column("success_probability", sa.Float(), nullable=True),
        sa.Column("label_used", sa.String(length=50), nullable=True),
        sa.Column("explanation_summary", sa.Text(), nullable=True),
        sa.Column("data_completeness", sa.Float(), nullable=True),
        sa.Column("confidence_flag", sa.String(length=20), nullable=True),
        sa.Column("rich_explanation_json", sa.Text(), nullable=True),
        _created_at(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["scoring_model_id"], ["scoring_models.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("score_runs", "id")

    op.create_table(
        "scoring_model_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scoring_model_id", sa.Integer(), nullable=False),
        sa.Column("feature_name", sa.String(length=100), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("threshold_min", sa.Float(), nullable=True),
        sa.Column("threshold_max", sa.Float(), nullable=True),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["scoring_model_id"], ["scoring_models.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scoring_model_id", "feature_name", name="uq_model_feature"),
    )
    _index("scoring_model_metrics", "id")

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("score_run_id", sa.Integer(), nullable=True),
        sa.Column("report_type", sa.String(length=10), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        _created_at(),
        sa.ForeignKeyConstraint(["score_run_id"], ["score_runs.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("reports", "id")

    op.create_table(
        "score_details",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("score_run_id", sa.Integer(), nullable=False),
        sa.Column("metric_name", sa.String(length=100), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=True),
        sa.Column("normalized_value", sa.Float(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("contribution", sa.Float(), nullable=True),
        sa.Column("comment", sa.String(length=500), nullable=True),
        sa.Column("transition_value", sa.Float(), nullable=True),
        sa.Column("sector_z_score", sa.Float(), nullable=True),
        sa.Column("l2_explanation", sa.Text(), nullable=True),
        sa.Column("l3_counterfactual", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["score_run_id"], ["score_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("score_details", "id")


def downgrade() -> None:
    op.drop_table("score_details")
    op.drop_table("reports")
    op.drop_table("scoring_model_metrics")
    op.drop_table("score_runs")
    op.drop_table("model_validation_runs")
    op.drop_table("model_feature_importances")
    op.drop_table("data_quality_issues")
    op.drop_table("stock_returns")
    op.drop_table("sector_normalized_features")
    op.drop_table("scoring_models")
    op.drop_table("metric_transitions")
    op.drop_table("label_definitions")
    op.drop_table("ingestion_jobs")
    op.drop_table("financial_statements")
    op.drop_table("computed_metrics")
    op.drop_table("audit_logs")
    op.drop_table("users")
    op.drop_table("sector_benchmarks")
    op.drop_table("companies")
