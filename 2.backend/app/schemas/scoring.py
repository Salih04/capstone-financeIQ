from datetime import datetime
from pydantic import BaseModel


class ScoreDetailOut(BaseModel):
    metric_name: str
    metric_value: float | None
    normalized_value: float | None = None
    weight: float | None
    contribution: float | None
    comment: str | None
    # V3 rich fields
    transition_value: float | None = None
    sector_z_score: float | None = None
    l2_explanation: str | None = None
    l3_counterfactual: str | None = None

    model_config = {"from_attributes": True}


class ScoreRunOut(BaseModel):
    id: int
    company_id: int
    user_id: int
    period: str
    model_name: str
    total_score: float | None
    success_probability: float | None
    label_used: str | None = None
    explanation_summary: str | None = None
    # V3 fields
    data_completeness: float | None = None
    confidence_flag: str | None = None
    rich_explanation_json: str | None = None
    created_at: datetime
    details: list[ScoreDetailOut] = []

    model_config = {"from_attributes": True}


class ScoreRunSummary(BaseModel):
    id: int
    company_id: int
    ticker: str | None = None
    company_name: str | None = None
    period: str
    model_name: str
    total_score: float | None
    success_probability: float | None
    label_used: str | None = None
    confidence_flag: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScoreRequest(BaseModel):
    period: str | None = None           # if None uses latest
    year: int | None = None             # if None uses latest year
    mode: str = "rule_based"            # "rule_based" | "logistic"
    scoring_model_id: int | None = None # if set, use custom weights from DB
    custom_weights: dict | None = None  # optional direct weight override


class CompareRequest(BaseModel):
    company_ids: list[int]
    period: str | None = None
    mode: str = "rule_based"


class CompareItem(BaseModel):
    company_id: int
    ticker: str
    company_name: str
    period: str
    total_score: float | None
    success_probability: float | None
    label_used: str | None
    explanation_summary: str | None


class CompareResult(BaseModel):
    items: list[CompareItem]


# ── Admin: scoring models ───────────────────────────────────────────────────

class ScoringModelMetricCreate(BaseModel):
    feature_name: str
    weight: float = 8.33
    threshold_min: float | None = None
    threshold_max: float | None = None
    direction: str = "higher"    # "higher" | "lower"


class ScoringModelCreate(BaseModel):
    model_name: str
    model_type: str = "rule_based"      # "rule_based" | "logistic"
    version: str = "1.0"
    metrics: list[ScoringModelMetricCreate] = []


class ScoringModelMetricOut(BaseModel):
    id: int
    feature_name: str
    weight: float
    threshold_min: float | None
    threshold_max: float | None
    direction: str

    model_config = {"from_attributes": True}


class ScoringModelOut(BaseModel):
    id: int
    model_name: str
    model_type: str
    version: str
    status: str = "draft"
    is_active: bool
    feature_set_version: str | None = None
    label_strategy: str | None = None
    evaluation_horizon: str | None = None
    validation_summary_json: str | None = None
    created_at: datetime
    metrics: list[ScoringModelMetricOut] = []

    model_config = {"from_attributes": True}


# ── Reports ─────────────────────────────────────────────────────────────────

class ReportOut(BaseModel):
    id: int
    user_id: int
    score_run_id: int | None
    report_type: str
    file_path: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
