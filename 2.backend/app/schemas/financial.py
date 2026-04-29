from pydantic import BaseModel


class FinancialStatementOut(BaseModel):
    id: int
    company_id: int
    period: str
    revenue: float | None
    net_income: float | None
    total_assets: float | None
    total_equity: float | None
    total_liabilities: float | None
    current_assets: float | None
    current_liabilities: float | None
    cash: float | None
    operating_cash_flow: float | None
    operating_income: float | None
    gross_profit: float | None
    inventory: float | None
    period_type: str | None
    source_name: str | None

    model_config = {"from_attributes": True}


class FinancialStatementCreate(BaseModel):
    company_id: int
    period: str
    revenue: float | None = None
    net_income: float | None = None
    total_assets: float | None = None
    total_equity: float | None = None
    total_liabilities: float | None = None
    current_assets: float | None = None
    current_liabilities: float | None = None
    cash: float | None = None
    operating_cash_flow: float | None = None
    operating_income: float | None = None
    gross_profit: float | None = None
    inventory: float | None = None
    period_type: str | None = None
    source_name: str | None = None


class ComputedMetricOut(BaseModel):
    id: int
    company_id: int
    period: str
    roa: float | None
    roe: float | None
    operating_margin: float | None
    net_margin: float | None
    current_ratio: float | None
    quick_ratio: float | None
    cash_ratio: float | None
    debt_to_equity: float | None
    debt_to_assets: float | None
    ocf_to_debt: float | None
    ocf_to_assets: float | None
    cash_flow_margin: float | None

    model_config = {"from_attributes": True}


class MetricTransitionOut(BaseModel):
    id: int
    company_id: int
    from_period: str
    to_period: str
    metric_name: str
    old_value: float | None
    new_value: float | None
    abs_change: float | None
    pct_change: float | None

    model_config = {"from_attributes": True}


class SectorNormalizedOut(BaseModel):
    id: int
    company_id: int
    period: str
    feature_name: str
    raw_value: float | None
    z_score: float | None
    percentile_rank: float | None

    model_config = {"from_attributes": True}
