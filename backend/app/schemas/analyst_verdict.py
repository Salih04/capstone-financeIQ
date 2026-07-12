"""Request and response contracts for the analyst dissent ledger."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


VerdictValue = Literal["agree", "disagree", "abstain"]
ReasonType = Literal[
    "evidence_quality",
    "data_gap",
    "methodology",
    "model_instability",
    "other",
]


class AnalystVerdictCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=20, pattern=r"^[A-Za-z0-9.]+$")
    year: int = Field(ge=2000, le=2100)
    verdict: VerdictValue
    reason_type: ReasonType
    note: str | None = Field(default=None, max_length=2000)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class AnalystVerdictOut(BaseModel):
    id: int
    ticker: str
    year: int
    verdict: VerdictValue
    reason_type: ReasonType
    note: str | None
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class VerdictCounts(BaseModel):
    agree: int
    disagree: int
    abstain: int
    total: int


class AnalystVerdictAggregateRow(BaseModel):
    ticker: str
    year: int
    verdict_counts: VerdictCounts
    reason_counts: dict[str, int]


class AnalystVerdictAggregateOut(BaseModel):
    purpose: str
    interpretation: str
    rows: list[AnalystVerdictAggregateRow]
