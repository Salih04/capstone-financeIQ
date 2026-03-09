"""
SectorAdjustmentService – computes sector-level distribution statistics
and per-company z-score / percentile for each metric and transition feature.
"""
from __future__ import annotations

import math
from typing import Any

from sqlalchemy.orm import Session

from app.models.analytics import SectorBenchmark, SectorNormalizedFeature
from app.models.company import Company
from app.models.financial import ComputedMetric

ALL_METRICS = [
    "roa", "roe", "operating_margin", "net_margin",
    "current_ratio", "quick_ratio", "cash_ratio",
    "debt_to_equity", "debt_to_assets",
    "ocf_to_debt", "ocf_to_assets", "cash_flow_margin",
]

MIN_PEERS = 2  # minimum companies in a sector to compute z-score


def _percentile_rank(values: list[float], target: float) -> float:
    """Fraction of values strictly below target (0–100)."""
    below = sum(1 for v in values if v < target)
    return round(100 * below / len(values), 2)


def _stats(values: list[float]) -> dict:
    n = len(values)
    if n == 0:
        return dict(mean_value=None, std_value=None, median_value=None, p25=None, p75=None)
    sorted_v = sorted(values)
    mean = sum(values) / n
    std = math.sqrt(sum((v - mean) ** 2 for v in values) / n) if n > 1 else 0.0
    median = sorted_v[n // 2] if n % 2 == 1 else (sorted_v[n // 2 - 1] + sorted_v[n // 2]) / 2
    p25 = sorted_v[max(0, int(0.25 * n))]
    p75 = sorted_v[min(n - 1, int(0.75 * n))]
    return dict(mean_value=mean, std_value=std, median_value=median, p25=p25, p75=p75)


def recompute_sector_benchmarks(db: Session, period: str) -> int:
    """
    For a given period, group all companies by sector_code and compute
    distribution stats for each metric. Upserts SectorBenchmark rows.
    Returns number of benchmark rows written.
    """
    # Build: sector_code -> {metric -> [values]}
    metrics_rows = (
        db.query(ComputedMetric, Company.sector_code)
        .join(Company, Company.id == ComputedMetric.company_id)
        .filter(ComputedMetric.period == period, Company.sector_code.isnot(None))
        .all()
    )

    sector_data: dict[str, dict[str, list[float]]] = {}
    for m, sc in metrics_rows:
        if sc not in sector_data:
            sector_data[sc] = {k: [] for k in ALL_METRICS}
        for metric in ALL_METRICS:
            v = getattr(m, metric, None)
            if v is not None:
                sector_data[sc][metric].append(v)

    count = 0
    for sector_code, metric_map in sector_data.items():
        for feature_name, values in metric_map.items():
            st = _stats(values)
            existing = (
                db.query(SectorBenchmark)
                .filter(
                    SectorBenchmark.sector_code == sector_code,
                    SectorBenchmark.period == period,
                    SectorBenchmark.feature_name == feature_name,
                )
                .first()
            )
            data = {**st, "sample_count": len(values)}
            if existing:
                for k, v in data.items():
                    setattr(existing, k, v)
            else:
                db.add(SectorBenchmark(
                    sector_code=sector_code,
                    period=period,
                    feature_name=feature_name,
                    **data,
                ))
                count += 1
    db.commit()
    return count


def recompute_sector_normalized(db: Session, company_id: int, period: str) -> int:
    """
    Compute z-score and percentile rank for each metric for one company
    relative to its sector peers in the given period.
    """
    company = db.get(Company, company_id)
    if not company or not company.sector_code:
        return 0

    # Get this company's metrics
    metric = (
        db.query(ComputedMetric)
        .filter(ComputedMetric.company_id == company_id, ComputedMetric.period == period)
        .first()
    )
    if not metric:
        return 0

    # Get all peer metrics in same sector + period
    peer_rows = (
        db.query(ComputedMetric)
        .join(Company, Company.id == ComputedMetric.company_id)
        .filter(
            ComputedMetric.period == period,
            Company.sector_code == company.sector_code,
        )
        .all()
    )
    peer_values: dict[str, list[float]] = {k: [] for k in ALL_METRICS}
    for p in peer_rows:
        for m in ALL_METRICS:
            v = getattr(p, m, None)
            if v is not None:
                peer_values[m].append(v)

    count = 0
    for feature_name in ALL_METRICS:
        raw = getattr(metric, feature_name, None)
        peers = peer_values[feature_name]

        z_score = None
        percentile = None

        if raw is not None and len(peers) >= MIN_PEERS:
            st = _stats(peers)
            if st["std_value"] and st["std_value"] > 0:
                z_score = round((raw - st["mean_value"]) / st["std_value"], 4)
            percentile = _percentile_rank(peers, raw)

        existing = (
            db.query(SectorNormalizedFeature)
            .filter(
                SectorNormalizedFeature.company_id == company_id,
                SectorNormalizedFeature.period == period,
                SectorNormalizedFeature.feature_name == feature_name,
            )
            .first()
        )
        if existing:
            existing.raw_value = raw
            existing.z_score = z_score
            existing.percentile_rank = percentile
        else:
            db.add(SectorNormalizedFeature(
                company_id=company_id,
                period=period,
                feature_name=feature_name,
                raw_value=raw,
                z_score=z_score,
                percentile_rank=percentile,
            ))
            count += 1
    db.commit()
    return count
