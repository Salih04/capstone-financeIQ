"""Tests for yearly-snapshot extraction + benchmark loading.

Run: PYTHONPATH=. pytest tests/test_yearly_extraction.py
"""

from pathlib import Path

import pandas as pd

from scripts.data_collection import extract_yearly_snapshots_to_manual_financials as X
from scripts.data_collection import pipeline as P


def _cfg(input_dir, out, **kw):
    class C:
        search_dirs = [Path(input_dir)]
        output_file = Path(out)
        validate = True
        strict = False
        dry_run = kw.get("dry_run", False)
        force = False
        selected_tickers = kw.get("selected_tickers")
        start_year = kw.get("start_year")
        end_year = kw.get("end_year")
    return C()


def _write_year_csv(d: Path, year: int, rows, cols, suffix=""):
    df = pd.DataFrame(rows, columns=cols)
    df.to_csv(d / f"{year}stocks{suffix}.csv", index=False)


def test_year_detected_and_mapped(tmp_path):
    d = tmp_path / "in"; d.mkdir(); out = tmp_path / "cand.csv"
    _write_year_csv(d, 2020,
                    [["AEFES", 100, 12.0, 18.0], ["THYAO", 200, 18.0, 5.0]],
                    ["Company", "Revenue", "Return on Equity (ROE)", "P/E"])
    rep = X.extract(_cfg(d, out))
    assert rep["selected_file_per_year"].get(2020, "").endswith("2020stocks.csv")
    cand = pd.read_csv(out)
    assert {"ticker", "year", "revenue", "roe", "pe_ratio"} <= set(cand.columns)
    assert set(cand["ticker"]) == {"AEFES", "THYAO"}


def test_leaky_return_columns_skipped(tmp_path):
    d = tmp_path / "in"; d.mkdir(); out = tmp_path / "cand.csv"
    _write_year_csv(d, 2021,
                    [["AEFES", 100, 5.0, 12.3]],
                    ["Company", "Revenue", "Return % (Last 1 Year)", "Price"])
    rep = X.extract(_cfg(d, out))
    cand = pd.read_csv(out)
    # return/price are never emitted as candidate features
    assert "return_last_1_year" not in cand.columns and "price" not in cand.columns
    skipped = rep["columns_skipped"][2021]
    assert any("leaky" in v for v in skipped.values())


def test_duplicate_year_files_selects_richer(tmp_path):
    d = tmp_path / "in"; d.mkdir(); out = tmp_path / "cand.csv"
    _write_year_csv(d, 2022, [["AEFES", 100]], ["Company", "Revenue"])
    _write_year_csv(d, 2022,
                    [["AEFES", 100, 10.0], ["THYAO", 200, 20.0]],
                    ["Company", "Revenue", "Net Income"], suffix="(1)")
    rep = X.extract(_cfg(d, out))
    assert 2022 in rep["duplicate_years"]
    # richer file (more rows + columns) chosen
    assert rep["selected_file_per_year"][2022].endswith("2022stocks(1).csv")


def test_misalignment_pct_with_currency_magnitude(tmp_path):
    d = tmp_path / "in"; d.mkdir(); out = tmp_path / "cand.csv"
    # ROE column filled with currency-scale values -> misaligned
    _write_year_csv(d, 2023,
                    [["AEFES", 5_000_000_000], ["THYAO", 9_000_000_000]],
                    ["Company", "Return on Equity (ROE)"])
    rep = X.extract(_cfg(d, out))
    reasons = [r["reason"] for r in rep["columns_rejected_misaligned"]]
    assert any("currency_like" in r for r in reasons)


def test_output_grain_one_per_ticker_year(tmp_path):
    d = tmp_path / "in"; d.mkdir(); out = tmp_path / "cand.csv"
    _write_year_csv(d, 2020, [["AEFES", 1], ["AEFES", 2]], ["Company", "Revenue"])
    X.extract(_cfg(d, out))
    cand = pd.read_csv(out)
    assert not cand.duplicated(["ticker", "year"]).any()


def test_dry_run_does_not_write(tmp_path):
    d = tmp_path / "in"; d.mkdir(); out = tmp_path / "cand.csv"
    _write_year_csv(d, 2020, [["AEFES", 1]], ["Company", "Revenue"])
    X.extract(_cfg(d, out, dry_run=True))
    assert not out.exists()


def test_benchmark_missing_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "BENCHMARK_RAW_CSV", tmp_path / "nope_raw.csv")
    monkeypatch.setattr(P, "BENCHMARK_CSV", tmp_path / "nope_clean.csv")
    monkeypatch.setattr(P, "BENCHMARK_TEMPLATE", tmp_path / "t1.csv")
    monkeypatch.setattr(P, "BENCHMARK_RAW_TEMPLATE", tmp_path / "t2.csv")
    assert P.load_benchmark(P.PipelineConfig()) is None


def test_benchmark_loads_and_validates(tmp_path, monkeypatch):
    raw = tmp_path / "bench.csv"
    raw.write_text("year,bist100_return_pct\n2021,25.5\n2022,196.6\n2022,196.6\n")
    monkeypatch.setattr(P, "BENCHMARK_RAW_CSV", raw)
    monkeypatch.setattr(P, "BENCHMARK_CSV", tmp_path / "none.csv")
    monkeypatch.setattr(P, "BENCHMARK_TEMPLATE", tmp_path / "t1.csv")
    monkeypatch.setattr(P, "BENCHMARK_RAW_TEMPLATE", tmp_path / "t2.csv")
    b = P.load_benchmark(P.PipelineConfig())
    assert b is not None and len(b) == 2  # duplicate year collapsed
    assert set(b["year"]) == {2021, 2022}
