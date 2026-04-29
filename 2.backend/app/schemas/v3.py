"""
V3 Governance, Validation, Labeling, Ingestion & Audit Schemas
"""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict


# ── Label Definition ──────────────────────────────────────────────────────────

class LabelDefinitionCreate(BaseModel):
    name: str
    description: str | None = None
    sector_benchmark_type: str = "sector_median"   # sector_median|upper_quartile|absolute|risk_adjusted
    horizon_months: int = 12
    threshold_rule: str = "score >= 55"
    sector_adjustment_mode: str = "z_score"
    success_threshold: float = 0.55


class LabelDefinitionOut(BaseModel):
    id: int
    name: str
    description: str | None
    sector_benchmark_type: str
    horizon_months: int
    threshold_rule: str
    sector_adjustment_mode: str
    success_threshold: float
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LabelPreviewOut(BaseModel):
    total_rows: int
    positive_count: int
    negative_count: int
    positive_rate: float
    imbalance_ratio: float
    imbalance_warning: bool
    median_score_used: float
    p75_score_used: float
    benchmark_type: str
    threshold: float


# ── Model Validation ──────────────────────────────────────────────────────────

class ValidationRunOut(BaseModel):
    id: int
    scoring_model_id: int
    validation_type: str
    train_period_start: str | None
    train_period_end: str | None
    test_period_start: str | None
    test_period_end: str | None
    accuracy: float | None
    precision: float | None
    recall: float | None
    f1: float | None
    roc_auc: float | None
    support_total: int | None
    support_positive: int | None
    confusion_matrix_json: str | None
    calibration_summary: str | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ValidationRequest(BaseModel):
    scoring_model_id: int
    train_ratio: float = 0.7
    label_def_id: int | None = None


# ── Ingestion / Data Health ───────────────────────────────────────────────────

class IngestionJobOut(BaseModel):
    id: int
    source_name: str
    job_status: str
    items_total: int
    items_success: int
    items_failed: int
    started_at: datetime | None
    finished_at: datetime | None
    error_summary: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DataQualityIssueOut(BaseModel):
    id: int
    ingestion_job_id: int | None
    company_id: int | None
    period: str | None
    issue_type: str
    issue_message: str
    severity: str
    detected_at: datetime

    model_config = {"from_attributes": True}


# ── Audit Log ─────────────────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    id: int
    actor_user_id: int | None
    action_type: str
    entity_type: str | None
    entity_id: int | None
    old_value_json: str | None
    new_value_json: str | None
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Model Registry (extended) ─────────────────────────────────────────────────

class ModelRegistryCreate(BaseModel):
    model_name: str
    model_type: str = "rule_based"
    version: str = "1.0"
    description: str | None = None
    feature_set_version: str | None = None
    label_strategy: str | None = None
    evaluation_horizon: str | None = None
    metrics: list[dict] = []   # [{feature_name, weight, direction, threshold_min, threshold_max}]

    model_config = ConfigDict(protected_namespaces=())


class ModelRegistryUpdate(BaseModel):
    model_name: str | None = None
    description: str | None = None
    feature_set_version: str | None = None
    label_strategy: str | None = None
    evaluation_horizon: str | None = None
    status: str | None = None

    model_config = ConfigDict(protected_namespaces=())


class ModelFeatureImportanceOut(BaseModel):
    feature_name: str
    coefficient: float | None
    importance_rank: int | None
    sign_direction: str | None

    model_config = {"from_attributes": True}


class ModelRegistryOut(BaseModel):
    id: int
    model_name: str
    model_type: str
    version: str
    description: str | None
    status: str
    feature_set_version: str | None
    label_strategy: str | None
    evaluation_horizon: str | None
    trained_at: datetime | None
    activated_at: datetime | None
    validation_summary_json: str | None
    is_active: bool
    created_at: datetime
    feature_importances: list[ModelFeatureImportanceOut] = []

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
