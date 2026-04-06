from datetime import datetime

from pydantic import BaseModel


class UploadPresetRequest(BaseModel):
    file_name: str


class UploadPresetResponse(BaseModel):
    file_name: str
    imported_rows: int
    skipped_rows: int
    years: list[int]


class TrainModelRequest(BaseModel):
    year: int
    sector: str
    top_n_parameters: int = 8


class ParameterRankItem(BaseModel):
    parameter_name: str
    score: float
    rank: int


class TrainModelResponse(BaseModel):
    year: int
    sector: str
    parameter_count: int
    top_parameters: list[ParameterRankItem]


class GetStocksResponseItem(BaseModel):
    stock_code: str
    sector: str
    year: int
    score: float
    rank: int
    confidence: float
    trend: str | None = None


class GetStocksResponse(BaseModel):
    run_id: int
    year: int
    sector: str
    user_type: str | None = None
    risk_level: str | None = None
    investment_scope: float | None = None
    model_type: str | None = None
    items: list[GetStocksResponseItem]


class PredictRequest(BaseModel):
    year: int
    sector: str
    user_type: str = "individual"
    risk_level: str = "medium"
    investment_scope: float | None = None
    model_type: str = "scoring"


class ParametersResponse(BaseModel):
    year: int
    sector: str
    parameters: list[ParameterRankItem]


class ContributionItem(BaseModel):
    parameter_name: str
    contribution: float


class StockDetailResponse(BaseModel):
    stock_code: str
    sector: str
    year: int
    score: float
    rank: int
    confidence: float
    top_contributors: list[ContributionItem]


class ExplanationResponse(BaseModel):
    stock_code: str
    summary: str
    top_contributors: list[ContributionItem]


class PortfolioAnalysisRequest(BaseModel):
    year: int
    sector: str
    stock_codes: list[str]


class PortfolioSuggestionItem(BaseModel):
    stock_code: str
    score: float
    rank: int
    action: str


class PortfolioAnalysisResponse(BaseModel):
    run_id: int
    year: int
    sector: str
    weak_stocks: list[PortfolioSuggestionItem]
    strong_stocks: list[PortfolioSuggestionItem]
    optimization_actions: list[str]


class EvaluationRequest(BaseModel):
    sector: str
    model_type: str = "scoring"
    window_size: int = 2


class EvaluationFoldOut(BaseModel):
    fold_index: int
    train_year_start: int
    train_year_end: int
    test_year: int
    rank_stability: float | None
    overlap_at_k: float | None


class EvaluationOut(BaseModel):
    run_id: int
    sector: str
    model_type: str
    window_size: int
    total_folds: int
    mean_rank_stability: float | None
    mean_overlap_at_k: float | None
    folds: list[EvaluationFoldOut]


class PredictHistoryItem(BaseModel):
    run_id: int
    year: int
    sector: str
    model_version: str
    created_at: datetime | None


class PredictHistoryOut(BaseModel):
    items: list[PredictHistoryItem]


class TrendPoint(BaseModel):
    year: int
    period_return: float | None = None
    return_1y: float | None = None
    return_6m: float | None = None
    return_3m: float | None = None
    return_1m: float | None = None


class TrendSeriesOut(BaseModel):
    stock_code: str
    series: list[TrendPoint]


class HeatmapCell(BaseModel):
    sector: str
    feature: str
    value: float


class SectorHeatmapOut(BaseModel):
    year: int
    heatmap: list[HeatmapCell]


class ParameterCatalogItem(BaseModel):
    category: str
    ratio: str
    formula: str
    purpose: str


class ParameterCatalogOut(BaseModel):
    items: list[ParameterCatalogItem]


class FundamentalsUploadResponse(BaseModel):
    created: int
    updated: int
    skipped: int
    errors: list[str]


class NewsItemOut(BaseModel):
    title: str
    source: str
    published_at: str
    summary: str


class NewsOut(BaseModel):
    sector: str
    updates: list[NewsItemOut]
    ai_insight: str


class AvailableFiltersResponse(BaseModel):
    years: list[int]
    sectors: list[str]


class WinnerCohortRowOut(BaseModel):
    id: int
    source_file: str
    year: int
    sector: str
    stock_code: str
    created_at: datetime

    model_config = {"from_attributes": True}
