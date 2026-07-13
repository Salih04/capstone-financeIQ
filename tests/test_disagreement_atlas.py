from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from experiments import disagreement_atlas


def _fixture_predictions() -> pd.DataFrame:
    rows = []
    for model, values in (
        ("model_a", [1.0, 2.0, 3.0, 4.0, 5.0]),
        ("model_b", [5.0, 4.0, 3.0, 2.0, 1.0]),
    ):
        for ticker, value in zip(["A", "B", "C", "D", "E"], values, strict=True):
            rows.append(
                {
                    "ticker": ticker,
                    "year": 2023,
                    "model": model,
                    "y_true": 0.0,
                    "y_pred": value,
                }
            )
    return pd.DataFrame(rows)


def _sources() -> list[dict[str, object]]:
    return [{"path": "fixture.csv", "sha256": "0" * 64, "rows": 10, "year": 2023, "models": ["model_a", "model_b"]}]


def _write_prediction_dumps(directory: Path) -> tuple[Path, Path, Path]:
    paths = []
    for year in disagreement_atlas.PREDICTION_YEARS:
        frame = _fixture_predictions().assign(year=year)
        path = directory / f"predictions_test_{year}.csv"
        frame.to_csv(path, index=False, lineterminator="\n")
        paths.append(path)
    return tuple(paths)  # type: ignore[return-value]


def test_hand_checked_pairwise_spearman_and_ticker_spread() -> None:
    report, matrix = disagreement_atlas.build_report(_fixture_predictions(), _sources())
    pair = next(
        row
        for row in matrix
        if row["row_model"] == "model_a" and row["column_model"] == "model_b"
    )
    ticker_a = next(row for row in report["ticker_year_rank_spread"] if row["ticker"] == "A")
    ticker_c = next(row for row in report["ticker_year_rank_spread"] if row["ticker"] == "C")

    assert pair == {
        "year": 2023,
        "row_model": "model_a",
        "column_model": "model_b",
        "shared_ranked_ticker_count": 5,
        "rank_spearman": -1.0,
        "status": "complete",
    }
    assert ticker_a["rank_spread_max_minus_min"] == 4.0
    assert ticker_a["rank_iqr"] == 2.0
    assert ticker_c["rank_spread_max_minus_min"] == 0.0
    assert ticker_c["rank_iqr"] == 0.0


def test_ranks_are_scale_invariant_and_ties_use_average_rank() -> None:
    original = disagreement_atlas.rank_within_model_year(_fixture_predictions())
    transformed = _fixture_predictions()
    transformed.loc[transformed["model"] == "model_b", "y_pred"] = (
        transformed.loc[transformed["model"] == "model_b", "y_pred"] * 1_000 + 17
    )
    transformed.loc[
        (transformed["model"] == "model_a") & transformed["ticker"].isin(["A", "B"]),
        "y_pred",
    ] = 9.0
    transformed_ranked = disagreement_atlas.rank_within_model_year(transformed)

    assert original.loc[original["model"] == "model_b", "prediction_rank"].tolist() == transformed_ranked.loc[
        transformed_ranked["model"] == "model_b", "prediction_rank"
    ].tolist()
    tied = transformed_ranked.loc[
        (transformed_ranked["model"] == "model_a")
        & transformed_ranked["ticker"].isin(["A", "B"]),
        "prediction_rank",
    ].tolist()
    assert tied == [4.5, 4.5]


def test_missing_predictions_remain_explicit_insufficient_data() -> None:
    predictions = _fixture_predictions()
    predictions.loc[
        (predictions["model"] == "model_b") & predictions["ticker"].isin(["C", "D", "E"]),
        "y_pred",
    ] = np.nan
    report, matrix = disagreement_atlas.build_report(predictions, _sources())
    pair = next(
        row
        for row in matrix
        if row["row_model"] == "model_a" and row["column_model"] == "model_b"
    )
    ticker_c = next(row for row in report["ticker_year_rank_spread"] if row["ticker"] == "C")

    assert pair["shared_ranked_ticker_count"] == 2
    assert pair["rank_spearman"] is None
    assert pair["status"] == "insufficient_data_fewer_than_3_shared_ranked_tickers"
    assert ticker_c["rank_spread_max_minus_min"] is None
    assert ticker_c["rank_iqr"] is None
    assert ticker_c["status"] == "insufficient_data_missing_model_rank"
    assert report["analysis_status"] == "partial_with_explicit_insufficient_data"


def test_invalid_schema_fails_instead_of_guessing_columns(tmp_path: Path) -> None:
    paths = _write_prediction_dumps(tmp_path)
    pd.read_csv(paths[0]).drop(columns=["y_pred"]).to_csv(paths[0], index=False)

    with pytest.raises(ValueError, match="columns must be exactly"):
        disagreement_atlas.load_prediction_dumps(paths)


@pytest.mark.parametrize(
    "unsafe",
    [
        "Agreement validates prediction.",
        "The signal is real.",
        "A reliable predictive edge was found.",
        "This is a buy recommendation.",
        "Profitable trading follows from consensus.",
    ],
)
def test_claim_safety_rejects_adversarial_interpretations(unsafe: str) -> None:
    with pytest.raises(ValueError, match="Unsafe disagreement claim"):
        disagreement_atlas.validate_claim_safety_text(unsafe)


def test_generated_artifacts_have_expected_schema_provenance_and_boundaries() -> None:
    report = json.loads(disagreement_atlas.JSON_OUTPUT.read_text(encoding="utf-8"))
    markdown = disagreement_atlas.MARKDOWN_OUTPUT.read_text(encoding="utf-8")
    with disagreement_atlas.MATRIX_OUTPUT.open(newline="", encoding="utf-8") as handle:
        matrix_rows = list(csv.DictReader(handle))

    assert report["task"] == "R3-STAT-02"
    assert report["analysis_status"] == "complete"
    assert report["generated_by"]["generator_command"] == "make research-disagreement"
    assert report["design"]["raw_prediction_magnitudes_compared_across_models"] is False
    assert report["claim_safety"]["predictive_validity_established"] is False
    assert report["claim_safety"]["reliable_predictive_edge_established"] is False
    assert report["claim_safety_sentence"] == disagreement_atlas.CLAIM_SAFETY_SENTENCE
    assert disagreement_atlas.CLAIM_SAFETY_SENTENCE in markdown
    assert len(report["source_artifacts"]) == 3
    for source in report["source_artifacts"]:
        assert hashlib.sha256(Path(source["path"]).read_bytes()).hexdigest() == source["sha256"]
    assert len(matrix_rows) == 3 * 9 * 9
    assert list(matrix_rows[0]) == [
        "year",
        "row_model",
        "column_model",
        "shared_ranked_ticker_count",
        "rank_spearman",
        "status",
    ]
    assert {row["status"] for row in matrix_rows} == {"complete"}
    disagreement_atlas.validate_claim_safety_text(markdown)


def test_workflow_is_byte_deterministic(tmp_path: Path) -> None:
    paths = _write_prediction_dumps(tmp_path)
    first = disagreement_atlas.run(tmp_path / "first", prediction_paths=paths)
    second = disagreement_atlas.run(tmp_path / "second", prediction_paths=paths)

    assert [path.name for path in first] == [path.name for path in second]
    assert [path.read_bytes() for path in first] == [path.read_bytes() for path in second]
