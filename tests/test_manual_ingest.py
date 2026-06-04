"""Tests for manual financial-history ingestion + pipeline integration.

Run: PYTHONPATH=. pytest tests/test_manual_ingest.py
"""

from pathlib import Path

import pandas as pd
import pytest

from scripts.data_collection import manual_ingest as M
from scripts.data_collection import pipeline as P


def _fin_dir(tmp_path: Path) -> Path:
    d = tmp_path / "financials"
    d.mkdir()
    return d


def test_per_ticker_ticker_inferred_from_filename(tmp_path):
    d = _fin_dir(tmp_path)
    (d / "ASELS.csv").write_text("year,revenue,net_income\n2023,100,10\n2024,120,15\n")
    df, rep = M.load_manual(d)
    assert rep.present and set(df["ticker"]) == {"ASELS"}
    assert {"revenue", "net_income"} <= set(df.columns)


def test_all_financials_requires_ticker(tmp_path):
    d = _fin_dir(tmp_path)
    (d / "all_financials.csv").write_text("year,revenue\n2023,100\n")
    df, rep = M.load_manual(d)
    assert df is None
    assert any("missing required 'ticker'" in i for i in rep.issues)


def test_all_financials_with_ticker_ok(tmp_path):
    d = _fin_dir(tmp_path)
    (d / "all_financials.csv").write_text(
        "ticker,year,revenue\nASELS,2023,100\nTHYAO,2023,200\n")
    df, rep = M.load_manual(d)
    assert rep.present and len(df) == 2


def test_duplicate_ticker_year_detected(tmp_path):
    d = _fin_dir(tmp_path)
    (d / "ASELS.csv").write_text("year,revenue\n2023,100\n2023,110\n")
    df, rep = M.load_manual(d)
    assert any("duplicate" in i for i in rep.issues)
    assert len(df) == 1  # de-duplicated, last kept


def test_non_numeric_flagged_as_misalignment(tmp_path):
    d = _fin_dir(tmp_path)
    (d / "ASELS.csv").write_text("year,revenue\n2023,not_a_number\n2024,also_bad\n")
    df, rep = M.load_manual(d)
    assert "revenue" in rep.misaligned_columns


def test_invalid_year_strict_rejected(tmp_path):
    d = _fin_dir(tmp_path)
    (d / "ASELS.csv").write_text("year,revenue\nXX,100\n")
    df, rep = M.load_manual(d, strict=True)
    assert any("invalid/non-numeric year" in i for i in rep.issues)


def test_all_null_column_rejected(tmp_path):
    d = _fin_dir(tmp_path)
    (d / "ASELS.csv").write_text("year,revenue,ebitda\n2023,100,\n2024,120,\n")
    df, rep = M.load_manual(d)
    assert "ebitda" in rep.all_null_columns
    assert "ebitda" not in df.columns


def test_unknown_ticker_reported(tmp_path):
    d = _fin_dir(tmp_path)
    (d / "ZZZZ.csv").write_text("year,revenue\n2023,100\n2024,120\n")
    df, rep = M.load_manual(d, known_tickers={"ASELS"})
    assert any("unknown tickers" in i for i in rep.issues)


def test_alias_mapping(tmp_path):
    d = _fin_dir(tmp_path)
    (d / "ASELS.csv").write_text("year,equity,ebit\n2023,50,8\n2024,60,9\n")
    df, rep = M.load_manual(d)
    assert "total_equity" in df.columns and "operating_income" in df.columns


# ---- pipeline integration ----
def test_merge_accepts_varying_rejects_frozen(monkeypatch, tmp_path):
    d = _fin_dir(tmp_path)
    # revenue varies per year (accepted); flat_col frozen (rejected)
    (d / "ASELS.csv").write_text("year,revenue,pe_ratio\n2023,100,10\n2024,140,10\n")
    cfg = P.PipelineConfig(manual_financials_dir=d)
    base = pd.DataFrame({
        "ticker": ["ASELS", "ASELS"], "year": [2023, 2024],
        "total_assets": [1.0, 2.0], "next_year_return_pct": [5.0, None],
    })
    out = P.merge_manual_financials(cfg, base, base_features={"total_assets"})
    assert "revenue" in out.columns          # varies -> accepted
    assert "pe_ratio" not in out.columns     # frozen (10,10) -> rejected
    assert "revenue" in cfg.manual_feature_columns
    assert cfg.manual_report["rejected_feature_columns"].get("pe_ratio") == "frozen_across_years"


def test_override_of_base_column(tmp_path):
    d = _fin_dir(tmp_path)
    (d / "ASELS.csv").write_text("year,total_assets\n2023,999\n2024,888\n")
    cfg = P.PipelineConfig(manual_financials_dir=d)
    base = pd.DataFrame({
        "ticker": ["ASELS", "ASELS"], "year": [2023, 2024],
        "total_assets": [1.0, 2.0], "next_year_return_pct": [5.0, None],
    })
    out = P.merge_manual_financials(cfg, base, base_features={"total_assets"})
    assert out.loc[out.year == 2023, "total_assets"].iloc[0] == 999
    assert cfg.manual_overrides.get("total_assets") == 2


def test_leakage_columns_never_features():
    df = pd.DataFrame(columns=[
        "ticker", "year", "revenue", "same_year_return_pct",
        "next_year_return_pct", "target_year",
    ])
    feats = P.feature_columns(df)
    assert "revenue" in feats
    for leak in ("same_year_return_pct", "next_year_return_pct", "target_year"):
        assert leak not in feats


def test_no_manual_dir_is_not_fatal(tmp_path):
    cfg = P.PipelineConfig(manual_financials_dir=tmp_path / "nope")
    base = pd.DataFrame({"ticker": ["ASELS"], "year": [2023], "next_year_return_pct": [5.0]})
    out = P.merge_manual_financials(cfg, base, base_features=set())
    assert len(out) == 1
    assert cfg.manual_report.get("present") is False
