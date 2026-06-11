"""Research-agent API - constrained, LLM-assisted research support.

Reads validated pipeline evidence only. Deterministic fallback always works;
OpenRouter/local LLM support is optional and fails safe. Never investment advice.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.dependencies import require_access
from app.core.rate_limit import rate_limit
from app.models.user import User
from app.services import research_agent as RA

router = APIRouter(prefix="/research", tags=["research-agent"])


@router.get("/summary")
def summary(_: User | None = Depends(require_access)):
    return RA.generate_summary_insight()


@router.get("/model-diagnostics")
def model_diagnostics(_: User | None = Depends(require_access)):
    state = RA.load_research_state()
    return {"diagnostics": RA.build_model_diagnostics_context(state),
            "confidence": RA.confidence_score(state),
            "disclaimer": RA.NOT_ADVICE}


@router.get("/data-quality")
def data_quality(_: User | None = Depends(require_access)):
    return {"data_quality": RA.build_data_quality_context(), "disclaimer": RA.NOT_ADVICE}


@router.get("/ai-status")
def ai_status(smoke: bool = False, _: User | None = Depends(require_access)):
    return RA.ai_status(smoke=smoke)


@router.get("/runtime-status")
def runtime_status(_: User | None = Depends(require_access)):
    """Public data + AI runtime diagnostic. No secrets exposed."""
    return RA.runtime_status()


@router.get("/experiments")
def experiments(_: User | None = Depends(require_access)):
    return RA.experiments_payload()


@router.get("/benchmark")
def benchmark(_: User | None = Depends(require_access)):
    return RA.benchmark_payload()


@router.get("/companies")
def companies(_: User | None = Depends(require_access)):
    return RA.companies_payload()


@router.get("/frozen-evidence")
def frozen_evidence(_: User | None = Depends(require_access)):
    return RA.frozen_evidence_payload()


@router.get("/company/{ticker}")
def company(ticker: str, _: User | None = Depends(require_access)):
    state = RA.load_research_state()
    try:
        ctx = RA.build_company_context(ticker, state)
    except KeyError as exc:
        raise HTTPException(404, str(exc))
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    det = RA.deterministic_company_summary(ctx)
    return {"context": ctx, "deterministic_summary": det,
            "ml": RA.ml_score_for_company(ticker, state), "disclaimer": RA.NOT_ADVICE}


@router.get("/company/{ticker}/score")
def company_score(ticker: str, _: User | None = Depends(require_access),
                  __: None = Depends(rate_limit("company-score"))):
    try:
        return RA.generate_company_insight(ticker)
    except KeyError as exc:
        raise HTTPException(404, str(exc))
    except ValueError as exc:
        raise HTTPException(422, str(exc))


class AskBody(BaseModel):
    question: str
    ticker: str | None = None
    max_context_tokens: int | None = None


@router.post("/ask")
def ask(body: AskBody, _: User | None = Depends(require_access),
        __: None = Depends(rate_limit("ask"))):
    if not body.question.strip():
        raise HTTPException(422, "question is required")
    try:
        return RA.answer_research_question(body.question, body.ticker, body.max_context_tokens)
    except Exception as exc:  # noqa - never 500 for a normal research question
        return {
            "answer": ("This question could not be fully processed from the current validated data. "
                       "No values were fabricated. Research support only — not investment advice."),
            "intent": RA.classify_intent(body.question),
            "data_used": {"source": "none", "year": None, "rows_used": 0, "fields_used": []},
            "llm_result": None,
            "warnings": ["request_processing_error"],
            "limitations": [f"internal error: {type(exc).__name__}"],
            "provider_used": RA.get_config()["provider"],
            "fallback_used": True,
            "llm_error": str(exc),
            "disclaimer": "This is research support, not investment advice.",
        }
