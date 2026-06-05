"""Tests for the BIST100 benchmark collector + pipeline benchmark targets.

Run: PYTHONPATH=. pytest tests/test_benchmark_collector.py
"""

import pandas as pd

from scripts.data_collection import collect_bist100_benchmark as B
from scripts.data_collection import pipeline as P


def test_tr_number_parsing():
    assert B.parse_tr_number("10.628,60") == 10628.60   # TR/EU
    assert B.parse_tr_number("10,628.60") == 10628.60   # US
    assert B.parse_tr_number("10628.60") == 10628.60
    assert B.parse_tr_number("1.234.567,89") == 1234567.89
    assert B.parse_tr_number("12,5") == 12.5
    assert B.parse_tr_number("") is None
    assert B.parse_tr_number("n/a") is None


def test_yearly_return_calculation():
    daily = pd.DataFrame({
        "date": pd.to_datetime(["2021-01-04", "2021-06-01", "2021-12-31",
                                "2022-01-03", "2022-12-30"]),
        "close": [100.0, 150.0, 200.0, 200.0, 400.0],
    })
    out = B.yearly_returns(daily, 2021, 2022).set_index("year")["bist100_return_pct"]
    assert out[2021] == 100.0   # 100 -> 200
    assert out[2022] == 100.0   # 200 -> 400


def test_validate_duplicate_and_missing_years():
    df = pd.DataFrame({"year": [2020, 2020], "bist100_return_pct": [10.0, 11.0]})
    issues = B.validate(df, 2020, 2025)
    assert any("duplicate" in i for i in issues)
    assert any("missing years" in i for i in issues)


def test_manual_daily_parsing_turkish(tmp_path, monkeypatch):
    p = tmp_path / "bist100_daily.csv"
    p.write_text("Tarih,Kapanış\n02.01.2021,\"1.000,00\"\n31.12.2021,\"2.000,00\"\n")
    monkeypatch.setattr(B, "MANUAL_DAILY", [p])
    df = B.load_manual_daily([])
    assert df is not None and len(df) == 2
    out = B.yearly_returns(df, 2021, 2021)
    assert out.iloc[0]["bist100_return_pct"] == 100.0


def test_pipeline_benchmark_targets_created(tmp_path, monkeypatch):
    bench = tmp_path / "bench.csv"
    bench.write_text("year,bist100_return_pct\n2021,25.0\n2022,150.0\n")
    monkeypatch.setattr(P, "BENCHMARK_RAW_CSV", bench)
    monkeypatch.setattr(P, "BENCHMARK_CSV", tmp_path / "none.csv")
    monkeypatch.setattr(P, "BENCHMARK_TEMPLATE", tmp_path / "t1.csv")
    monkeypatch.setattr(P, "BENCHMARK_RAW_TEMPLATE", tmp_path / "t2.csv")
    cfg = P.PipelineConfig()
    b = P.load_benchmark(cfg)
    assert b is not None and set(b["year"]) == {2021, 2022}


def test_benchmark_targets_null_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "BENCHMARK_RAW_CSV", tmp_path / "a.csv")
    monkeypatch.setattr(P, "BENCHMARK_CSV", tmp_path / "b.csv")
    monkeypatch.setattr(P, "BENCHMARK_TEMPLATE", tmp_path / "t1.csv")
    monkeypatch.setattr(P, "BENCHMARK_RAW_TEMPLATE", tmp_path / "t2.csv")
    assert P.load_benchmark(P.PipelineConfig()) is None
