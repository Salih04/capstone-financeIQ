from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.forecasting import (
    AvailableFiltersResponse,
    EvaluationOut,
    EvaluationRequest,
    ExplanationResponse,
    GetStocksResponse,
    ParametersResponse,
    ParameterCatalogOut,
    PortfolioAnalysisRequest,
    PortfolioAnalysisResponse,
    PredictRequest,
    PredictHistoryOut,
    SectorHeatmapOut,
    StockDetailResponse,
    TrendSeriesOut,
    TrainModelRequest,
    TrainModelResponse,
    UploadPresetRequest,
    UploadPresetResponse,
)
from app.services.forecasting_service import (
    analyze_portfolio,
    get_available_filters,
    get_parameters_for_sector,
    get_parameter_catalog,
    get_predict_history,
    get_sector_heatmap_data,
    get_stock_detail,
    get_stock_explanation,
    get_yearly_trend_series,
    import_winner_excel_preset,
    run_time_cv_evaluation,
    run_forecast_for_sector,
    train_sector_success_model,
)

router = APIRouter(tags=["forecasting"])


@router.post("/upload-data", response_model=UploadPresetResponse)
def upload_data(
    body: UploadPresetRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        return import_winner_excel_preset(db, body.file_name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/train-model", response_model=TrainModelResponse)
def train_model(
    body: TrainModelRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        return train_sector_success_model(
            db,
            year=body.year,
            sector=body.sector,
            top_n_parameters=body.top_n_parameters,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/get-stocks", response_model=GetStocksResponse)
def get_stocks(
    year: int,
    sector: str,
    user_type: str = "individual",
    risk_level: str = "medium",
    investment_scope: float | None = None,
    model_type: str = "scoring",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return run_forecast_for_sector(
            db,
            year=year,
            sector=sector,
            created_by_user_id=current_user.id,
            user_type=user_type,
            risk_level=risk_level,
            investment_scope=investment_scope,
            model_type=model_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/predict", response_model=GetStocksResponse)
def predict(
    body: PredictRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return run_forecast_for_sector(
            db,
            year=body.year,
            sector=body.sector,
            created_by_user_id=current_user.id,
            user_type=body.user_type,
            risk_level=body.risk_level,
            investment_scope=body.investment_scope,
            model_type=body.model_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/predict/evaluate", response_model=EvaluationOut)
def evaluate_predict_family(
    body: EvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return run_time_cv_evaluation(
            db,
            sector=body.sector,
            model_type=body.model_type,
            window_size=body.window_size,
            created_by_user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/predict/history", response_model=PredictHistoryOut)
def predict_history(
    limit: int = 30,
    sector: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_predict_history(db, limit=limit, sector=sector)


@router.get("/predict/trends", response_model=TrendSeriesOut)
def predict_trends(
    stock_code: str,
    sector: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_yearly_trend_series(db, stock_code=stock_code, sector=sector)


@router.get("/predict/heatmap", response_model=SectorHeatmapOut)
def predict_heatmap(
    year: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_sector_heatmap_data(db, year=year)


@router.get("/get-parameters", response_model=ParametersResponse)
def get_parameters(
    year: int,
    sector: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        return get_parameters_for_sector(db, year=year, sector=sector)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/parameters/catalog", response_model=ParameterCatalogOut)
def parameters_catalog(
    _: User = Depends(get_current_user),
):
    return get_parameter_catalog()


@router.post("/get-portfolio-analysis", response_model=PortfolioAnalysisResponse)
def get_portfolio_analysis(
    body: PortfolioAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return analyze_portfolio(
            db,
            year=body.year,
            sector=body.sector,
            stock_codes=body.stock_codes,
            created_by_user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/get-stock-detail", response_model=StockDetailResponse)
def get_stock_detail_endpoint(
    run_id: int,
    stock_code: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = get_stock_detail(db, run_id=run_id, stock_code=stock_code)
    if not item:
        raise HTTPException(status_code=404, detail="Stock detail not found for run.")
    return item


@router.get("/get-explanation", response_model=ExplanationResponse)
def get_explanation(
    run_id: int,
    stock_code: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = get_stock_explanation(db, run_id=run_id, stock_code=stock_code)
    if not item:
        raise HTTPException(status_code=404, detail="Explanation not found for run.")
    return item


@router.get("/forecasting/filters", response_model=AvailableFiltersResponse)
def get_filters(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_available_filters(db)
