from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts.data_collection import derive_alternative_targets as alt
from scripts import fetch_usdtry_year_end as fx_fetch
from experiments import run_experiments


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    modeling = tmp_path / "modeling.csv"
    cpi = tmp_path / "cpi.csv"
    fx = tmp_path / "fx.csv"
    pd.DataFrame(
        [
            {"ticker": "A", "year": 2020, "target_year": 2021, "next_year_return_pct": 50.0},
            {"ticker": "A", "year": 2021, "target_year": 2022, "next_year_return_pct": 100.0},
            {"ticker": "B", "year": 2020, "target_year": 2021, "next_year_return_pct": None},
            {"ticker": "B", "year": 2021, "target_year": 2022, "next_year_return_pct": 25.0},
        ]
    ).to_csv(modeling, index=False)
    pd.DataFrame(
        [
            {"year": 2021, "cpi_december_yoy_pct": 25.0},
            {"year": 2022, "cpi_december_yoy_pct": 50.0},
        ]
    ).to_csv(cpi, index=False)
    pd.DataFrame(
        [
            {"year": 2020, "try_per_usd": 8.0, "status": "success", "source": "fixture", "price_date": "2020-12-31"},
            {"year": 2021, "try_per_usd": 13.0, "status": "success", "source": "fixture", "price_date": "2021-12-31"},
            {"year": 2022, "try_per_usd": 18.2, "status": "success", "source": "fixture", "price_date": "2022-12-31"},
        ]
    ).to_csv(fx, index=False)
    return modeling, cpi, fx


def test_formula_correctness_and_2022_fx_direction() -> None:
    assert alt.real_return_pct(50.0, 25.0) == pytest.approx(20.0)

    # Hand-computed 2022 example with TRY-per-USD quotes:
    # (1 + 100%) * 13.0 / 18.2 - 1 = 42.857142857% in USD terms.
    assert alt.usd_return_pct(100.0, 13.0, 18.2) == pytest.approx(42.8571428571)
    inverted = ((1.0 + 1.0) * 18.2 / 13.0 - 1.0) * 100.0
    assert alt.usd_return_pct(100.0, 13.0, 18.2) != pytest.approx(inverted)


def test_null_propagation_and_no_input_mutation(tmp_path: Path) -> None:
    modeling, cpi, fx = _inputs(tmp_path)
    before = modeling.read_bytes()
    frame = alt.derive(modeling, cpi, fx)

    assert modeling.read_bytes() == before
    missing_nominal = frame[(frame["ticker"] == "B") & (frame["year"] == 2020)].iloc[0]
    assert pd.isna(missing_nominal["next_year_real_return_pct"])
    assert pd.isna(missing_nominal["next_year_usd_return_pct"])
    assert missing_nominal["real_target_status"] == "missing_nominal_target"
    assert missing_nominal["usd_target_status"] == "missing_nominal_target"

    # Removing one CPI and one FX observation must create nulls, never fills.
    pd.read_csv(cpi).query("year != 2022").to_csv(cpi, index=False)
    pd.read_csv(fx).query("year != 2022").to_csv(fx, index=False)
    frame = alt.derive(modeling, cpi, fx)
    row = frame[(frame["ticker"] == "A") & (frame["target_year"] == 2022)].iloc[0]
    assert pd.isna(row["next_year_real_return_pct"])
    assert pd.isna(row["next_year_usd_return_pct"])
    assert row["real_target_status"] == "missing_cpi_target_year"
    assert row["usd_target_status"] == "missing_fx_target_year"


def test_derive_preserves_exact_ticker_year_alignment(tmp_path: Path) -> None:
    modeling, cpi, fx = _inputs(tmp_path)
    source = pd.read_csv(modeling)[["ticker", "year"]]
    derived = alt.derive(modeling, cpi, fx)[["ticker", "year"]]
    pd.testing.assert_frame_equal(derived, source)
    assert not derived.duplicated(["ticker", "year"]).any()


def test_alternative_panel_requires_exact_key_alignment(tmp_path: Path, monkeypatch) -> None:
    base = tmp_path / "training.csv"
    targets = tmp_path / "targets.csv"
    pd.DataFrame(
        [
            {"ticker": "A", "year": 2020, "feature": 1.0, "next_year_return_pct": 5.0},
            {"ticker": "B", "year": 2020, "feature": 2.0, "next_year_return_pct": 6.0},
            {"ticker": "A", "year": 2021, "feature": 3.0, "next_year_return_pct": 7.0},
            {"ticker": "B", "year": 2021, "feature": 4.0, "next_year_return_pct": 8.0},
        ]
    ).to_csv(base, index=False)
    pd.DataFrame(
        [
            {"ticker": "A", "year": 2020, "next_year_real_return_pct": 1.0},
            {"ticker": "B", "year": 2020, "next_year_real_return_pct": 2.0},
            {"ticker": "A", "year": 2021, "next_year_real_return_pct": 3.0},
            {"ticker": "B", "year": 2021, "next_year_real_return_pct": 4.0},
        ]
    ).to_csv(targets, index=False)
    monkeypatch.setattr(run_experiments, "TRAINING_MODELING", base)

    panel, features = run_experiments.build_panel_for_target(
        "next_year_real_return_pct", target_path=targets
    )
    assert features == ["feature"]
    assert panel["target_return"].tolist() == [1.0, 2.0, 3.0, 4.0]

    misaligned = pd.read_csv(targets).iloc[:-1]
    misaligned.to_csv(targets, index=False)
    with pytest.raises(ValueError, match="do not align exactly"):
        run_experiments.build_panel_for_target(
            "next_year_real_return_pct", target_path=targets
        )


def test_fx_extraction_uses_last_valid_close_before_year_end() -> None:
    timestamps = [
        int(pd.Timestamp("2022-12-29", tz="UTC").timestamp()),
        int(pd.Timestamp("2022-12-30", tz="UTC").timestamp()),
        int(pd.Timestamp("2023-01-02", tz="UTC").timestamp()),
    ]
    payload = {
        "chart": {
            "result": [
                {
                    "timestamp": timestamps,
                    "meta": {"currency": "TRY"},
                    "indicators": {
                        "quote": [{"close": [18.60, 18.70, 18.80]}],
                        "adjclose": [{"adjclose": [18.60, 18.70, 18.80]}],
                    },
                }
            ],
            "error": None,
        }
    }
    row = fx_fetch.extract_row(payload, 2022)
    assert row["price_date"] == "2022-12-30"
    assert row["try_per_usd"] == pytest.approx(18.70)
    assert row["status"] == "success"


@pytest.mark.parametrize(
    "unsafe",
    [
        "We found a real-terms signal.",
        "This establishes a reliable predictive edge.",
        "The conversion creates investment value.",
        "A market-beating result.",
        "This predicts future returns.",
    ],
)
def test_claim_safety_rejects_unsafe_alternative_basis_interpretations(unsafe: str) -> None:
    with pytest.raises(ValueError, match="Unsafe alternative-target claim"):
        alt.validate_claim_safety_text(unsafe)


def test_generated_artifacts_preserve_claim_boundary_and_alignment() -> None:
    if not alt.OUTPUT.is_file():
        pytest.skip("generate with make alternative-targets")
    frame = pd.read_csv(alt.OUTPUT)
    source = pd.read_csv(alt.MODELING)[["ticker", "year"]]
    pd.testing.assert_frame_equal(frame[["ticker", "year"]], source)
    assert frame["next_year_real_return_pct"].notna().sum() <= frame["next_year_nominal_try_return_pct"].notna().sum()
    assert frame["next_year_usd_return_pct"].notna().sum() <= frame["next_year_nominal_try_return_pct"].notna().sum()
    alt.validate_claim_safety_text(alt.REPORT_MD.read_text(encoding="utf-8"))
