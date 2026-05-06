from app.models.financial import FinancialStatement, ComputedMetric


def _safe_div(n, d):
    if n is None or d is None or d == 0:
        return None
    return n / d


def compute_ratios(stmt: FinancialStatement) -> dict:
    """Compute all 12 ratios from a FinancialStatement row."""
    quick_assets = (
        (stmt.current_assets or 0) - (stmt.inventory or 0)
        if stmt.current_assets is not None else None
    )

    return {
        # Profitability
        "roa": _safe_div(stmt.net_income, stmt.total_assets),
        "roe": _safe_div(stmt.net_income, stmt.total_equity),
        "operating_margin": _safe_div(stmt.operating_income, stmt.revenue),
        "net_margin": _safe_div(stmt.net_income, stmt.revenue),
        # Liquidity
        "current_ratio": _safe_div(stmt.current_assets, stmt.current_liabilities),
        "quick_ratio": _safe_div(quick_assets, stmt.current_liabilities),
        "cash_ratio": _safe_div(stmt.cash, stmt.current_liabilities),
        # Leverage
        "debt_to_equity": _safe_div(stmt.total_liabilities, stmt.total_equity),
        "debt_to_assets": _safe_div(stmt.total_liabilities, stmt.total_assets),
        # NOTE: Source dataset may not include operating cash flow for every company/period.
        # Cash flow ratios are excluded from scoring until OCF data is added.
        # Future formulas:
        # ocf_to_debt = operating_cash_flow / total_liabilities
        # ocf_to_assets = operating_cash_flow / total_assets
        # cash_flow_margin = operating_cash_flow / revenue
        "ocf_to_debt": _safe_div(stmt.operating_cash_flow, stmt.total_liabilities),
        "ocf_to_assets": _safe_div(stmt.operating_cash_flow, stmt.total_assets),
        "cash_flow_margin": _safe_div(stmt.operating_cash_flow, stmt.revenue),
    }


def upsert_computed_metrics(db, company_id: int, period: str, ratios: dict) -> ComputedMetric:
    from sqlalchemy import select
    existing = db.execute(
        select(ComputedMetric).where(
            ComputedMetric.company_id == company_id,
            ComputedMetric.period == period,
        )
    ).scalar_one_or_none()

    if existing:
        for k, v in ratios.items():
            if hasattr(existing, k):
                setattr(existing, k, v)
        db.commit()
        db.refresh(existing)
        return existing

    metric = ComputedMetric(company_id=company_id, period=period, **{
        k: v for k, v in ratios.items() if hasattr(ComputedMetric, k)
    })
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric
