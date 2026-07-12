"""Persistence and deterministic aggregation for analyst dissent records.

This module is deliberately separate from scoring, forecasting, experiment, and
trusted-data services. It records human disagreement but exposes no mechanism
that could feed those records back into model evidence or ranking behavior.
"""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.analyst_verdict import (
    ANALYST_REASON_TYPES,
    ANALYST_VERDICTS,
    AnalystVerdict,
)
from app.schemas.analyst_verdict import AnalystVerdictCreate


LEDGER_BOUNDARY = "Records disagreement for research; never a score input."
LEDGER_INTERPRETATION = (
    "Counts are descriptive ledger records, not consensus, a recommendation, "
    "or a crowd signal."
)


def create_verdict(
    db: Session,
    body: AnalystVerdictCreate,
    user_id: int,
) -> AnalystVerdict:
    """Append one authenticated verdict without updating any prior record."""
    verdict = AnalystVerdict(**body.model_dump(), user_id=user_id)
    db.add(verdict)
    db.flush()
    return verdict


def aggregate_verdicts(
    db: Session,
    ticker: str | None = None,
    year: int | None = None,
) -> dict:
    """Return stable ticker/year counts; never expose notes as a signal."""
    query = db.query(
        AnalystVerdict.ticker,
        AnalystVerdict.year,
        AnalystVerdict.verdict,
        AnalystVerdict.reason_type,
        func.count(AnalystVerdict.id),
    )
    if ticker is not None:
        query = query.filter(AnalystVerdict.ticker == ticker.strip().upper())
    if year is not None:
        query = query.filter(AnalystVerdict.year == year)

    grouped = query.group_by(
        AnalystVerdict.ticker,
        AnalystVerdict.year,
        AnalystVerdict.verdict,
        AnalystVerdict.reason_type,
    ).all()

    by_key: dict[tuple[str, int], dict] = {}
    for row_ticker, row_year, verdict, reason_type, count in grouped:
        key = (str(row_ticker), int(row_year))
        item = by_key.setdefault(
            key,
            {
                "ticker": key[0],
                "year": key[1],
                "verdict_counts": {value: 0 for value in ANALYST_VERDICTS},
                "reason_counts": {value: 0 for value in ANALYST_REASON_TYPES},
            },
        )
        item["verdict_counts"][str(verdict)] += int(count)
        item["reason_counts"][str(reason_type)] += int(count)

    rows = []
    for key in sorted(by_key, key=lambda value: (value[0], -value[1])):
        item = by_key[key]
        item["verdict_counts"]["total"] = sum(
            item["verdict_counts"][value] for value in ANALYST_VERDICTS
        )
        rows.append(item)

    return {
        "purpose": LEDGER_BOUNDARY,
        "interpretation": LEDGER_INTERPRETATION,
        "rows": rows,
    }
