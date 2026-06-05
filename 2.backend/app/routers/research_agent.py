"""Research-agent API — constrained, local-LLM-assisted research support.

Reads validated pipeline evidence only. Deterministic fallback always works;
local LLM (LM Studio / Ollama) is optional and fails safe. Never investment advice.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.dependencies import get_current_user
from app.models.user import User
from app.services import research_agent as RA

router = APIRouter(prefix="/research", tags=["research-agent"])


@router.get("/summary")
def summary(_: User = Depends(get_current_user)):
    return RA.generate_summary_insight()


@router.get("/model-diagnostics")
def model_diagnostics(_: User = Depends(get_current_user)):
    state = RA.load_research_state()
    return {"diagnostics": RA.build_model_diagnostics_context(state),
            "confidence": RA.confidence_score(state),
            "disclaimer": RA.NOT_ADVICE}


@router.get("/data-quality")
def data_quality(_: User = Depends(get_current_user)):
    return {"data_quality": RA.build_data_quality_context(), "disclaimer": RA.NOT_ADVICE}


@router.get("/company/{ticker}")
def company(ticker: str, _: User = Depends(get_current_user)):
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
def company_score(ticker: str, _: User = Depends(get_current_user)):
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
def ask(body: AskBody, _: User = Depends(get_current_user)):
    if not body.question.strip():
        raise HTTPException(422, "question is required")
    return RA.answer_research_question(body.question, body.ticker, body.max_context_tokens)
