"""Tests for the research-agent service + training dataset generator.

Run: PYTHONPATH=. pytest tests/test_research_agent.py
"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "2.backend"))

from app.services import research_agent as RA  # noqa: E402


@pytest.fixture(scope="module")
def state():
    return RA.load_research_state()


# 1 state loading
def test_state_loads(state):
    assert state["modeling_available"] is True
    assert state["modeling"] is not None and len(state["modeling"]) > 0


# 2 summary context
def test_summary_context(state):
    c = RA.build_summary_context(state)
    assert c["feature_count"] and c["rows"] and "rejected_frozen_columns" in c


# 3 company context
def test_company_context(state):
    c = RA.build_company_context("ASELS", state)
    assert c["ticker"] == "ASELS" and c["feature_count"] > 0
    assert isinstance(c["top_positive_features"], dict)


# 4 unknown ticker
def test_unknown_ticker(state):
    with pytest.raises(KeyError):
        RA.build_company_context("ZZZZ", state)


# 5 deterministic summary
def test_deterministic_summary(state):
    ctx = RA.build_company_context("ASELS", state)
    out = RA.deterministic_company_summary(ctx)
    assert out["source"] == "deterministic_fallback" and out["summary"]
    assert out["limitations"]


# 6 deterministic score
def test_deterministic_score(state):
    ctx = RA.build_company_context("ASELS", state)
    ml = RA.ml_score_for_company("ASELS", state)
    conf = RA.confidence_score(state)
    sc = RA.deterministic_research_score({**ctx, **ml, **conf})
    assert 0.0 <= sc["llm_research_score"] <= 1.0


# 7 confidence penalties
def test_confidence_penalties(state):
    c = RA.confidence_score(state)
    assert 0.0 <= c["confidence_score"] <= 1.0
    assert c["confidence_level"] in ("low", "medium", "high")
    assert any("small_sample" in r for r in c["confidence_reasons"])


# 8 + 9 composite formula + bounds
def test_composite_formula_and_bounds():
    comp = RA.composite_score(0.8, 0.4, 0.6,
                              {"weights": {"ml": 0.65, "confidence": 0.20, "llm": 0.15}})
    expected = round(0.65 * 0.8 + 0.20 * 0.4 + 0.15 * 0.6, 3)
    assert comp["final_research_score"] == expected
    assert 0.0 <= comp["final_research_score"] <= 1.0
    assert comp["ml_score"] == 0.8 and comp["confidence_score"] == 0.4


def test_composite_ml_null_redistributes():
    comp = RA.composite_score(None, 0.4, 0.6,
                              {"weights": {"ml": 0.65, "confidence": 0.20, "llm": 0.15}})
    assert comp["partial_score"] is True
    assert comp["ml_score"] is None
    assert 0.0 <= comp["final_research_score"] <= 1.0


# 10 LLM provider failure fallback
def test_llm_provider_none_fails_safe():
    res = RA.call_local_llm([{"role": "user", "content": "hi"}],
                            {"provider": "none", "base_url": "", "model": "x", "timeout": 1,
                             "weights": {"ml": .65, "confidence": .2, "llm": .15}})
    assert res["ok"] is False and res["provider"] == "none"


def test_llm_bad_url_fails_safe():
    res = RA.call_local_llm([{"role": "user", "content": "hi"}],
                            {"provider": "lmstudio", "base_url": "http://127.0.0.1:9/x",
                             "model": "x", "timeout": 1, "weights": {"ml": .65, "confidence": .2, "llm": .15}})
    assert res["ok"] is False  # connection refused -> safe


# 11 + 12 prompt rules
def test_prompt_has_safety_rules():
    p = RA.SYSTEM_PROMPT.lower()
    assert "not investment advice" in p or "not an investment" in p
    assert "do not invent" in p
    assert "buy" in p and "sell" in p  # explicitly forbidden words named


# 13 ask endpoint fallback
def test_ask_fallback(state, monkeypatch):
    monkeypatch.setenv("RESEARCH_LLM_PROVIDER", "none")
    res = RA.answer_research_question("Is the benchmark available?", state=state)
    assert res["fallback_used"] is True and res["provider_used"] == "none"
    assert "investment advice" in res["answer"].lower() or res["answer"]


# 14 generator writes valid JSONL
def test_generator_jsonl(tmp_path):
    from research_agent_training import generate_instruction_dataset as G
    rows = G.generate(30)
    p = tmp_path / "ds.jsonl"
    G.write_jsonl(rows, p)
    lines = p.read_text().strip().splitlines()
    assert len(lines) == len(rows) >= 10
    for ln in lines:
        obj = json.loads(ln)
        assert {"instruction", "input", "output"} <= set(obj)
        s = obj["output"]["llm_research_score"]
        assert s is None or 0.0 <= s <= 1.0


# 15 generated examples include required warnings
def test_generator_warnings_present():
    from research_agent_training import generate_instruction_dataset as G
    rows = G.generate(40)
    assert any("small_sample" in r["output"].get("warnings", []) for r in rows)


# 16 generated outputs avoid buy/sell/hold
def test_generator_no_advice_language():
    from research_agent_training import generate_instruction_dataset as G
    rows = G.generate(60)
    for r in rows:
        blob = f" {json.dumps(r['output']).lower()} "
        for bad in (" buy ", " sell ", " hold ", "price target", " al ", " sat ", " tut "):
            assert bad not in blob
