"""Tests for grounded intent answers + source-distinction context (PHASE 3-7)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "2.backend"))

from app.services import research_agent as RA  # noqa: E402

pytestmark = pytest.mark.skipif(
    not (REPO / "data" / "trusted_clean" / "modeling_dataset_2020_2025.csv").is_file(),
    reason="modeling dataset not built")


@pytest.fixture(scope="module")
def state():
    # force deterministic path (no LLM) so tests are stable
    import os
    os.environ["RESEARCH_LLM_PROVIDER"] = "none"
    return RA.load_research_state()


def test_intent_classification():
    assert RA.classify_intent("Which stocks beat BIST100?") == "benchmark_outperformers"
    assert RA.classify_intent("Is the benchmark available?") == "benchmark_status"
    assert RA.classify_intent("Which stocks are ranked highest?") == "top_ranked"
    assert RA.classify_intent("Why is the model signal weak?") == "diagnostics"
    assert RA.classify_intent("Which columns were rejected?") == "data_quality"


def test_beat_bist100_returns_actual_tickers(state):
    r = RA.answer_research_question("Which stocks beat BIST100?", state=state)
    assert r["intent"] == "benchmark_outperformers"
    # must reference concrete data, not a generic "based on validated reports" line
    assert "validated reports" not in r["answer"].lower()
    assert r["data_used"]["rows_used"] > 0
    assert "BIST100" in r["answer"]
    # at least one ticker-like token (4-5 uppercase letters)
    import re
    assert re.search(r"\b[A-Z]{4,5}\b", r["answer"])


def test_beat_bist100_not_generic(state):
    r = RA.answer_research_question("Which stocks beat BIST100?", state=state)
    generic = "based only on validated reports" in r["answer"].lower()
    assert not generic


def test_top_ranked_returns_tickers(state):
    r = RA.answer_research_question("Which stocks are ranked highest?", state=state)
    assert r["intent"] == "top_ranked"
    assert r["data_used"]["source"].startswith("research_agent_model_outputs")


def test_two_sequential_questions_independent(state):
    a = RA.answer_research_question("Which stocks beat BIST100?", state=state)
    b = RA.answer_research_question("Why is the model signal weak?", state=state)
    assert a["intent"] != b["intent"]
    assert a["answer"] != b["answer"]


def test_benchmark_outperformers_helper(state):
    o = RA.get_benchmark_outperformers(state=state)
    assert o["available"] is True
    assert o["outperformer_count"] >= 0
    assert "next_year_outperform_bist100" in o["fields_used"]


def test_no_advice_in_answers(state):
    for q in ("Which stocks beat BIST100?", "Which stocks are ranked highest?"):
        ans = RA.answer_research_question(q, state=state)["answer"].lower()
        for bad in (" buy ", " sell ", " hold ", "guaranteed"):
            assert bad not in f" {ans} "


def test_summary_context_has_source_distinction(state):
    s = RA.build_summary_context(state)
    assert s["feature_count_before_corrected_yearly"] == 17
    assert s["feature_count_after_corrected_yearly"] >= 27
    assert "revenue" in s["accepted_corrected_yearly_features"]
    assert "pe" in s["still_missing_valuation_features"]
    assert s["model_signal_after_corrected_yearly"] == "still weak/unstable"


def test_data_quality_context_distinguishes_sources(state):
    d = RA.build_data_quality_context(state)
    cy = d["corrected_yearly"]
    assert cy["available"] is True
    assert "revenue" in cy["accepted_columns"]
    # valuation rejected, not in accepted
    assert "pe" not in cy["accepted_columns"]
    assert "pe" in cy["frozen_valuation_columns"]


def test_no_frozen_valuation_in_model_features(state):
    feats = set((state["quality"] or {}).get("feature_columns", []))
    for c in ("pe", "pb", "ev_ebitda", "market_cap", "market_capitalization", "enterprise_value"):
        assert c not in feats


def test_diagnostics_has_business_interpretation(state):
    diag = RA.build_model_diagnostics_context(state)
    assert "17" in diag["interpretation_business"]
    assert diag["weak_backtest"] is True
