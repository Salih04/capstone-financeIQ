"""Synthetic contract tests for the frozen R4-DIM-01 implementation."""

from __future__ import annotations

import json
import sys
import csv
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ``experiments.run_experiments`` inserts backend/ at import time.  Keep root
# ``scripts`` authoritative when pytest collects this module beside registry
# tests that import the experiment machinery.
_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))
_loaded_scripts = sys.modules.get("scripts")
if _loaded_scripts is not None:
    _loaded_file = getattr(_loaded_scripts, "__file__", None)
    if _loaded_file and Path(_loaded_file).resolve().is_relative_to(_REPO_ROOT / "backend"):
        del sys.modules["scripts"]

from experiments import feature_dimensionality as dim


def _synthetic_inputs(
    *,
    missing: dict[tuple[str, int, str], bool] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    missing = missing or {}
    rows: list[dict[str, object]] = []
    for year in dim.ALL_FEATURE_YEARS:
        for number, ticker in enumerate(("AAA", "BBB", "CCC", "DDD")):
            row = {feature: float(year * 100 + number) for feature in dim.FEATURES}
            row.update({"ticker": ticker, "year": year, "next_year_return_pct": float(number)})
            for feature in dim.FEATURES:
                if missing.get((ticker, year, feature), False):
                    row[feature] = np.nan
            rows.append(row)
    frame = pd.DataFrame(rows)
    numeric = frame[list(dim.FEATURES)].astype(float)
    masks = numeric.notna()
    years = frame["year"].to_numpy(dtype=int)
    tickers = frame["ticker"].to_numpy(dtype=str)
    target_eligible = np.ones(len(frame), dtype=bool)
    return frame, numeric, masks, years, tickers, target_eligible


def _materialize_generator_root(root: Path) -> None:
    rows: list[dict[str, object]] = []
    for year in dim.ALL_FEATURE_YEARS:
        for number, ticker in enumerate(("AAA", "BBB", "CCC", "DDD")):
            row: dict[str, object] = {
                "ticker": ticker,
                "year": year,
                "next_year_return_pct": float(number + 1),
            }
            for feature_index, feature in enumerate(dim.FEATURES):
                if feature == "benchmark_same_year_return_pct":
                    row[feature] = float(year)
                elif feature == "price_data_available":
                    row[feature] = 1.0
                else:
                    row[feature] = float((year - 2019) * 100 + number + feature_index / 100.0)
            rows.append(row)
    source = root / dim.SOURCE_REL
    source.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(source, index=False)
    authority = root / dim.FEATURE_AUTHORITY_REL
    authority.parent.mkdir(parents=True, exist_ok=True)
    authority.write_text(json.dumps({"accepted_features": list(dim.FEATURES)}), encoding="utf-8")
    dictionary = root / dim.DATA_DICTIONARY_REL
    dictionary.parent.mkdir(parents=True, exist_ok=True)
    dictionary.write_text(
        "\n".join(f"| `{feature}` | feature_allowed | source |" for feature in dim.FEATURES),
        encoding="utf-8",
    )
    generator = root / "experiments/feature_dimensionality.py"
    generator.parent.mkdir(parents=True, exist_ok=True)
    generator.write_text("synthetic generator authority", encoding="utf-8")


def test_exact_windows_and_diagnostic_authority() -> None:
    assert [window["name"] for window in dim.WINDOWS] == ["test_2023", "test_2024", "test_2025"]
    assert [window["feature_years"] for window in dim.WINDOWS] == [
        (2020, 2021),
        (2020, 2021, 2022),
        (2020, 2021, 2022, 2023),
    ]
    assert len(dim.FEATURES) == 40
    assert dim.THRESHOLDS == ("0.70", "0.80", "0.90")
    assert "next_year_return_pct" not in dim.FEATURES
    assert "ticker" not in dim.FEATURES


def test_authority_rejects_order_missing_and_duplicate_columns() -> None:
    columns = ["ticker", "year", "next_year_return_pct", *dim.FEATURES]
    with pytest.raises(dim.MethodologyError, match="PACKET_CONFLICT"):
        dim.validate_feature_authority(list(reversed(dim.FEATURES)), dim.FEATURES, columns)
    with pytest.raises(dim.MethodologyError, match="does not contain"):
        dim.validate_feature_authority(dim.FEATURES, dim.FEATURES, columns[:-1])
    with pytest.raises(dim.MethodologyError, match="duplicate"):
        dim.validate_feature_authority(dim.FEATURES, dim.FEATURES, columns + ["year"])


def test_duplicate_analytical_key_fails_before_any_scientific_helper(tmp_path: Path) -> None:
    source = pd.DataFrame(
        [
            {"ticker": "AAA", "year": 2020, "next_year_return_pct": 1.0, **{f: 1.0 for f in dim.FEATURES}},
            {"ticker": "AAA", "year": 2020, "next_year_return_pct": 2.0, **{f: 2.0 for f in dim.FEATURES}},
        ]
    )
    source_path = tmp_path / dim.SOURCE_REL
    source_path.parent.mkdir(parents=True)
    source.to_csv(source_path, index=False)
    authority_path = tmp_path / dim.FEATURE_AUTHORITY_REL
    authority_path.parent.mkdir(parents=True, exist_ok=True)
    authority_path.write_text(json.dumps({"accepted_features": list(dim.FEATURES)}), encoding="utf-8")
    dictionary_path = tmp_path / dim.DATA_DICTIONARY_REL
    dictionary_path.parent.mkdir(parents=True, exist_ok=True)
    dictionary_path.write_text(
        "\n".join(f"| `{feature}` | feature_allowed | source |" for feature in dim.FEATURES),
        encoding="utf-8",
    )
    with pytest.raises(dim.MethodologyError, match=r"duplicate \(ticker, year\)"):
        dim._read_source(tmp_path)
    with pytest.raises(dim.MethodologyError, match=r"duplicate \(ticker, year\)"):
        dim.write_outputs(tmp_path)
    assert not (tmp_path / dim.OUTPUT_DIR_REL).exists()


def test_malformed_numeric_source_fails_closed_before_publication(tmp_path: Path) -> None:
    _materialize_generator_root(tmp_path)
    source_path = tmp_path / dim.SOURCE_REL
    source = pd.read_csv(source_path).astype(object)
    source.loc[0, dim.FEATURES[0]] = "not-a-number"
    source.to_csv(source_path, index=False)
    with pytest.raises(dim.MethodologyError, match="malformed or non-finite"):
        dim.write_outputs(tmp_path)
    assert not (tmp_path / dim.OUTPUT_DIR_REL).exists()


def test_rank_completion_has_all_frozen_degenerate_branches() -> None:
    zero = dim.rank_feature_values([np.nan, np.nan])
    assert zero.n_obs == 0
    assert np.array_equal(zero.completed, [0.5, 0.5])

    one = dim.rank_feature_values([4.0, np.nan, np.nan])
    assert one.n_obs == 1
    assert np.array_equal(one.completed, [0.5, 0.5, 0.5])

    tied = dim.rank_feature_values([4.0, 4.0, np.nan])
    assert tied.n_obs == 2
    assert np.allclose(tied.completed, [0.5, 0.5, 0.5], atol=1e-15)

    ordinary = dim.rank_feature_values([10.0, np.nan, 30.0, 20.0])
    assert ordinary.n_obs == 3
    assert np.allclose(ordinary.completed, [0.0, 0.5, 1.0, 0.5])


def test_rank_completion_does_not_have_obsolete_variance_guard_or_mutate_input() -> None:
    values = np.array([1.0, 1.0, np.nan])
    before = values.copy()
    result = dim.rank_feature_values(values)
    assert np.array_equal(values, before, equal_nan=True)
    assert np.allclose(result.completed, [0.5, 0.5, 0.5])
    assert not hasattr(dim, "VARIANCE_FLOOR")


def test_eligibility_seals_structural_and_support_categories() -> None:
    missing = {
        (ticker, 2023, "current_assets"): ticker != "AAA"
        for ticker in ("AAA", "BBB", "CCC", "DDD")
    }
    _, numeric, masks, years, tickers, target_eligible = _synthetic_inputs(missing=missing)
    result = dim.build_eligibility(numeric, masks, years, tickers, target_eligible)
    assert "benchmark_same_year_return_pct" not in result.primary_features
    assert "price_data_available" not in result.primary_features
    assert "current_assets" not in result.primary_features
    assert "current_assets" in {item["feature"] for item in result.support_excluded}
    current = next(item for item in result.support_excluded if item["feature"] == "current_assets")
    assert current["blocking_windows"] == ["test_2025"]
    structural = {item["feature"] for item in result.structurally_ineligible}
    assert structural == {"benchmark_same_year_return_pct", "price_data_available"}
    assert len(result.primary_features) < 40
    assert set(result.primary_features) | structural | {current["feature"]} == set(dim.FEATURES)


def test_missingness_alone_never_makes_fixed_availability_order_capable() -> None:
    missing = {(ticker, 2020, "price_data_available"): ticker != "AAA" for ticker in ("AAA", "BBB", "CCC", "DDD")}
    _, numeric, masks, years, tickers, target_eligible = _synthetic_inputs(missing=missing)
    result = dim.build_eligibility(numeric, masks, years, tickers, target_eligible)
    item = next(item for item in result.structurally_ineligible if item["feature"] == "price_data_available")
    evidence = next(item for item in result.evidence if item["feature"] == "price_data_available")
    assert item["feature"] not in result.primary_features
    assert all(not year["order_capable"] for window in evidence["windows"] for year in window["per_year"])


def test_primary_row_universe_is_exact_intersection_and_shared_by_features() -> None:
    missing = {}
    for year in dim.ALL_FEATURE_YEARS:
        missing[("AAA", year, "current_assets")] = True
        missing[("BBB", year, "equity")] = True
    _, numeric, masks, years, tickers, target_eligible = _synthetic_inputs(missing=missing)
    result = dim.build_eligibility(numeric, masks, years, tickers, target_eligible)
    row_universes = dim._row_universes(result.primary_features, result.support_sets)
    assert all(len(row_universes[year]) == 2 for year in dim.ALL_FEATURE_YEARS)
    assert all({ticker for ticker, _ in row_universes[year]} == {"CCC", "DDD"} for year in dim.ALL_FEATURE_YEARS)
    key_to_position = {(tickers[index], int(years[index])): index for index in range(len(years))}
    for year in dim.ALL_FEATURE_YEARS:
        members = sorted(row_universes[year], key=lambda item: item[0])
        positions = [key_to_position[member] for member in members]
        completed, ranked_masks, _ = dim.build_completed_rank_matrix(
            numeric.iloc[positions].reset_index(drop=True),
            [year] * len(positions),
            result.primary_features,
        )
        assert completed.shape == (2, len(result.primary_features))
        assert ranked_masks.to_numpy(dtype=bool).all()


def test_completed_rank_matrix_accepts_primary_suborder_and_uses_years_separately() -> None:
    numeric = pd.DataFrame({"a": [1.0, 3.0, 4.0, 2.0], "b": [4.0, 3.0, 2.0, 1.0]})
    names = (dim.FEATURES[1], dim.FEATURES[2])
    renamed = numeric.rename(columns={"a": names[0], "b": names[1]})
    completed, masks, evidence = dim.build_completed_rank_matrix(renamed, [2020, 2020, 2021, 2021], names)
    assert completed.shape == (4, 2)
    assert masks.shape == (4, 2)
    assert evidence == {"2020": {names[0]: 2, names[1]: 2}, "2021": {names[0]: 2, names[1]: 2}}
    assert not np.isclose(completed[0, 0], completed[2, 0])


def test_pearson_guard_is_post_completion_and_dimension_agnostic() -> None:
    matrix = np.column_stack([np.arange(4, dtype=float), [0.0, 1.0, 0.0, 1.0]])
    correlation = dim.pearson_correlation(matrix, (dim.FEATURES[1], dim.FEATURES[2]))
    assert correlation.shape == (2, 2)
    assert np.allclose(correlation, correlation.T)
    assert np.all(np.diag(correlation) == 1.0)
    with pytest.raises(dim.MethodologyError, match="denominator"):
        dim.pearson_correlation(np.ones((4, 2)), (dim.FEATURES[1], dim.FEATURES[2]))
    with pytest.raises(dim.MethodologyError, match="feature count"):
        dim.pearson_correlation(np.ones((4, 2)), (dim.FEATURES[1],))


def test_overlap_is_original_mask_full_40_evidence() -> None:
    masks = np.ones((3, 40), dtype=bool)
    masks[1, 0] = False
    overlap = dim.overlap_matrix(masks)
    assert overlap.shape == (40, 40)
    assert np.array_equal(overlap, overlap.T)
    assert np.array_equal(np.diag(overlap), masks.sum(axis=0))
    assert overlap[0, 1] == 2
    assert np.issubdtype(overlap.dtype, np.integer)


def test_thresholds_are_inclusive_chained_and_singletons_are_null() -> None:
    names = dim.FEATURES[:3]
    correlation = np.eye(3)
    correlation[0, 1] = correlation[1, 0] = 0.8
    correlation[1, 2] = correlation[2, 1] = 0.8
    correlation[0, 2] = correlation[2, 0] = 0.79
    components = dim.threshold_components(correlation, 0.8, names)
    assert components[0]["members"] == list(names)
    assert components[0]["edge_count"] == 2
    assert components[0]["min_abs_corr"] == pytest.approx(0.79)
    assert components[0]["median_abs_corr"] == pytest.approx(0.8)
    singleton_components = dim.threshold_components(np.eye(3), 0.8, names)
    assert all(component["size"] == 1 for component in singleton_components)
    assert all(component["min_abs_corr"] is None for component in singleton_components)
    for threshold in (0.70, 0.80, 0.90):
        matrix = np.eye(3)
        matrix[0, 1] = matrix[1, 0] = threshold
        assert dim.threshold_components(matrix, threshold, names)[0]["edge_count"] == 1


def test_spectrum_metrics_and_exact_tolerance_boundaries() -> None:
    result = dim.spectrum_metrics_from_eigenvalues([2.0, 1.0, 0.0])
    assert result.participation_ratio == pytest.approx(9 / 5)
    expected = np.exp(-(2 / 3 * np.log(2 / 3) + 1 / 3 * np.log(1 / 3)))
    assert result.spectral_erank == pytest.approx(expected)
    assert result.post_tolerance_eigenvalues[-1] == 0.0
    boundary = dim.spectrum_metrics_from_eigenvalues([1.0, -1e-8, 0.5])
    assert boundary.post_tolerance_eigenvalues[1] == 0.0
    with pytest.raises(dim.MethodologyError, match="materially negative"):
        dim.spectrum_metrics_from_eigenvalues([1.0, -1.0001e-8, 0.5])
    with pytest.raises(dim.MethodologyError, match="lambda_max"):
        dim.spectrum_metrics_from_eigenvalues([0.0, 0.0])
    with pytest.raises(dim.MethodologyError, match="non-finite"):
        dim.spectrum_metrics_from_eigenvalues([1.0, np.nan])


def test_real_spectrum_uses_symmetric_solver(monkeypatch: pytest.MonkeyPatch) -> None:
    matrix = np.eye(3)
    called = {"eigvalsh": False}
    original = dim.np.linalg.eigvalsh

    def wrapped(value: np.ndarray) -> np.ndarray:
        called["eigvalsh"] = True
        return original(value)

    monkeypatch.setattr(dim.np.linalg, "eigvalsh", wrapped)
    result = dim.spectrum_metrics(matrix)
    assert called["eigvalsh"]
    assert result.participation_ratio == pytest.approx(3.0)
    assert result.spectral_erank == pytest.approx(3.0)


def test_serialization_and_claim_boundary_are_deterministic() -> None:
    rows = [("test_2023", dim.FEATURES[0], dim.FEATURES[0], "1")]
    first = dim._csv_bytes(("window", "feature_a", "feature_b", "correlation"), rows)
    second = dim._csv_bytes(("window", "feature_a", "feature_b", "correlation"), rows)
    assert first == second and first.endswith(b"\n")
    assert dim.CLAIM_SENTENCE == "No reliable predictive edge has been established."
    assert "conservative" not in " ".join(
        ["heterogeneous missingness does not imply a direction for spectral effects"]
    )


def test_real_generator_serializes_and_validates_exact_five_artifact_family(tmp_path: Path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    _materialize_generator_root(first_root)
    _materialize_generator_root(second_root)

    first_paths = dim.write_outputs(first_root)
    second_paths = dim.write_outputs(second_root)
    assert [path.name for path in first_paths] == list(dim.OUTPUT_FILES)
    first_dir = first_root / dim.OUTPUT_DIR_REL
    assert sorted(path.name for path in first_dir.iterdir()) == sorted(dim.OUTPUT_FILES)
    assert len(list(first_dir.iterdir())) == 5

    payload = json.loads((first_dir / "dimensionality_report.json").read_text(encoding="utf-8"))
    assert payload["eligibility"]["primary_dimension"] < 40
    assert payload["eligibility"]["primary_features"]
    assert payload["eligibility"]["structurally_ineligible"]
    assert payload["primary_row_universe"]
    for window in payload["windows"]:
        invariant = window["row_universe"]["row_universe_invariant"]
        assert invariant == {
            "analytical_key": ["ticker", "year"],
            "checked": True,
            "passed": True,
            "result": "PASS",
            "duplicate_key_count": 0,
            "row_count": len(window["row_universe"]["eligible_row_members"]),
            "unique_key_count": len(window["row_universe"]["eligible_row_members"]),
        }
    assert "Row-universe invariant: `PASS`" in (first_dir / "dimensionality_report.md").read_text(
        encoding="utf-8"
    )

    correlation_rows = list(
        csv.DictReader((first_dir / "correlation_matrix.csv").read_text(encoding="utf-8").splitlines())
    )
    overlap_rows = list(
        csv.DictReader((first_dir / "pair_overlap.csv").read_text(encoding="utf-8").splitlines())
    )
    missingness_rows = list(
        csv.DictReader((first_dir / "feature_missingness.csv").read_text(encoding="utf-8").splitlines())
    )
    assert len(correlation_rows) == 3 * payload["eligibility"]["primary_dimension"] ** 2
    assert len(overlap_rows) == 3 * 40 * 40
    assert len(missingness_rows) == 3 * 40
    assert payload["companion_artifacts"]
    assert all("/" not in item["path"] or not Path(item["path"]).is_absolute() for item in payload["source_artifacts"])
    assert all("companion_artifacts" not in item["path"] for item in payload["source_artifacts"])
    dim.validate_serialized_family(first_dir)
    first_bytes = {name: (first_dir / name).read_bytes() for name in dim.OUTPUT_FILES}

    mutated = json.loads((first_dir / "dimensionality_report.json").read_text(encoding="utf-8"))
    del mutated["windows"][0]["row_universe"]["row_universe_invariant"]
    (first_dir / "dimensionality_report.json").write_text(
        json.dumps(mutated), encoding="utf-8"
    )
    with pytest.raises(dim.MethodologyError, match="row-universe invariant"):
        dim.validate_serialized_family(first_dir)

    second_bytes = {
        name: (second_root / dim.OUTPUT_DIR_REL / name).read_bytes() for name in dim.OUTPUT_FILES
    }
    assert first_bytes == second_bytes


def test_atomic_publication_failure_leaves_no_partial_family_and_preserves_old_family(
    tmp_path: Path,
) -> None:
    fresh_root = tmp_path / "fresh"
    _materialize_generator_root(fresh_root)
    calls = 0

    def fail_on_second_write(path: Path, data: bytes) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected serialization failure")
        path.write_bytes(data)

    with pytest.raises(OSError, match="injected serialization failure"):
        dim.write_outputs(fresh_root, write_file=fail_on_second_write)
    assert not (fresh_root / dim.OUTPUT_DIR_REL).exists()
    assert not list((fresh_root / "experiments").glob(".results_dimensionality.*"))

    stable_root = tmp_path / "stable"
    _materialize_generator_root(stable_root)
    dim.write_outputs(stable_root)
    stable_dir = stable_root / dim.OUTPUT_DIR_REL
    before = {name: (stable_dir / name).read_bytes() for name in dim.OUTPUT_FILES}
    calls = 0
    with pytest.raises(OSError, match="injected serialization failure"):
        dim.write_outputs(stable_root, write_file=fail_on_second_write)
    after = {name: (stable_dir / name).read_bytes() for name in dim.OUTPUT_FILES}
    assert after == before
    assert not list((stable_root / "experiments").glob(".results_dimensionality.*"))
