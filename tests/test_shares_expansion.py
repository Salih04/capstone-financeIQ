"""Tests for the capital-event shares-outstanding workflow + RA free-float answer."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "2.backend"))

from scripts.data_collection import expand_shares_outstanding_events as E  # noqa: E402


def _setup(monkeypatch, tmp_path, events_df, tickers):
    p = tmp_path / "events.csv"
    events_df.to_csv(p, index=False)
    monkeypatch.setattr(E, "EVENTS", p)
    monkeypatch.setattr(E, "EVENTS_TEMPLATE", tmp_path / "ev_tmpl.csv")
    monkeypatch.setattr(E, "MANUAL_OUT", tmp_path / "manual.csv")
    monkeypatch.setattr(E, "REPORT_JSON", tmp_path / "r.json")
    monkeypatch.setattr(E, "REPORT_MD", tmp_path / "r.md")
    monkeypatch.setattr(E, "_tickers", lambda: tickers)


def test_carry_forward(monkeypatch, tmp_path):
    ev = pd.DataFrame([["ASELS", 2020, 1000, "KAP", "pre", "medium", "issued_capital", 1],
                       ["ASELS", 2023, 2000, "KAP", "post", "high", "issued_capital", 1]],
                      columns=E.EVENT_COLS)
    _setup(monkeypatch, tmp_path, ev, ["ASELS"])
    rep = E.expand(log=lambda *a: None)
    m = pd.read_csv(E.MANUAL_OUT).set_index("year")["shares_outstanding"].to_dict()
    assert m[2020] == 1000 and m[2022] == 1000     # pre-increase carried forward
    assert m[2023] == 2000 and m[2025] == 2000     # post-increase carried forward
    assert "ASELS" in rep["tickers_multiple_events"]


def test_missing_prior_event(monkeypatch, tmp_path):
    ev = pd.DataFrame([["ASELS", 2023, 2000, "KAP", "late", "high", "issued_capital", 1]],
                      columns=E.EVENT_COLS)
    _setup(monkeypatch, tmp_path, ev, ["ASELS"])
    E.expand(log=lambda *a: None)
    m = pd.read_csv(E.MANUAL_OUT).set_index("year")
    assert pd.isna(m.loc[2020, "shares_outstanding"])           # no prior event
    assert m.loc[2020, "status"] == "missing_prior_event"
    assert m.loc[2023, "shares_outstanding"] == 2000


def test_duplicate_event_flagged(monkeypatch, tmp_path):
    ev = pd.DataFrame([["ASELS", 2020, 1000, "KAP", "a", "medium", "issued_capital", 1],
                       ["ASELS", 2020, 9999, "KAP", "dup", "low", "issued_capital", 1]],
                      columns=E.EVENT_COLS)
    _setup(monkeypatch, tmp_path, ev, ["ASELS"])
    rep = E.expand(log=lambda *a: None)
    assert any("duplicate" in i for i in rep["issues"])
    m = pd.read_csv(E.MANUAL_OUT).set_index("year")["shares_outstanding"].to_dict()
    assert m[2020] == 1000     # first kept, dup ignored


def test_free_float_rejected(monkeypatch, tmp_path):
    ev = pd.DataFrame([["THYAO", 2020, 5000, "KAP", "ff", "low", "free_float_only", 1]],
                      columns=E.EVENT_COLS)
    _setup(monkeypatch, tmp_path, ev, ["THYAO"])
    rep = E.expand(log=lambda *a: None)
    assert rep["rejected_free_float_only_rows"] == 1
    m = pd.read_csv(E.MANUAL_OUT)
    assert not m["shares_outstanding"].notna().any()   # free float never used


def test_template_generation(monkeypatch, tmp_path):
    tmpl = tmp_path / "ev_tmpl.csv"
    monkeypatch.setattr(E, "EVENTS", tmp_path / "nope.csv")
    monkeypatch.setattr(E, "EVENTS_TEMPLATE", tmpl)
    monkeypatch.setattr(E, "MANUAL_OUT", tmp_path / "manual.csv")
    monkeypatch.setattr(E, "REPORT_JSON", tmp_path / "r.json")
    monkeypatch.setattr(E, "REPORT_MD", tmp_path / "r.md")
    monkeypatch.setattr(E, "_tickers", lambda: ["ASELS", "THYAO"])
    E.expand(log=lambda *a: None)
    assert tmpl.is_file()
    body = tmpl.read_text()
    assert "effective_year" in body and "free_float_only" in body
    assert "ASELS,2020" in body and "THYAO,2020" in body


def test_valuation_reads_expanded_shares(monkeypatch, tmp_path):
    """Builder picks up expanded manual shares -> market_cap computed."""
    from scripts.data_collection import build_free_valuation_history as V
    manual = pd.DataFrame({"ticker": ["AAA", "AAA"], "year": [2022, 2023],
                           "shares_outstanding": [1e6, 1e6], "capital_basis": ["issued_capital"] * 2})
    mpath = tmp_path / "manual.csv"
    manual.to_csv(mpath, index=False)
    monkeypatch.setattr(V, "SHARES_MANUAL", mpath)
    df, status = V.load_shares()
    assert status == "manual"
    assert set(df["ticker"]) == {"AAA"}
    assert (df["shares_outstanding"] > 0).all()


def test_valuation_rejects_free_float_in_manual(monkeypatch, tmp_path):
    from scripts.data_collection import build_free_valuation_history as V
    manual = pd.DataFrame({"ticker": ["AAA"], "year": [2022],
                           "shares_outstanding": [1e6], "capital_basis": ["free_float_only"]})
    mpath = tmp_path / "manual.csv"
    manual.to_csv(mpath, index=False)
    monkeypatch.setattr(V, "SHARES_MANUAL", mpath)
    df, status = V.load_shares()
    assert df is None and status == "empty"   # free float filtered out -> nothing usable


def test_research_agent_free_float_answer():
    import os
    os.environ["RESEARCH_LLM_PROVIDER"] = "none"
    from app.services import research_agent as RA
    st = RA.load_research_state()
    r = RA.answer_research_question("Can I use Fiili Dolasimdaki Pay Tutari as shares?", state=st)
    assert r["intent"] == "valuation"
    a = r["answer"].lower()
    assert "free float" in a and ("not" in a or "must not" in a or "understates" in a)
    for bad in (" buy ", " sell ", " hold ", "guaranteed"):
        assert bad not in f" {a} "


def test_research_agent_how_to_fill_shares():
    import os
    os.environ["RESEARCH_LLM_PROVIDER"] = "none"
    from app.services import research_agent as RA
    st = RA.load_research_state()
    r = RA.answer_research_question("How do I fill shares outstanding?", state=st)
    assert r["intent"] == "valuation"
    assert "events" in r["answer"].lower() and "make shares" in r["answer"].lower()
