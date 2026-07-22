"""R3-TGT-01 excess-target significance, bootstrap-unit, and reporting-policy guards.

These tests are written to fail against the reviewed defective implementation:
they pin the bootstrap resampling unit to complete ticker trajectories, forbid
any post-outcome model selection in the generated artifacts (including a
transient one that is deleted afterwards), bound the temporary-output policy,
require the power report to describe the design that was actually evaluated,
and refuse malformed cluster keys instead of coercing them.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import shutil
import tempfile
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.stats import rankdata

from experiments import run_alternative_targets, run_experiments, significance
from experiments import run_excess_basis as excess


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_committed_dumps() -> pd.DataFrame:
    frames = []
    for path in sorted(excess.OUTPUT_DIR.glob("predictions_test_*.csv")):
        frame = pd.read_csv(path)
        frame["split"] = path.stem.removeprefix("predictions_")
        frames.append(frame)
    if not frames:
        pytest.skip("generate with make research-excess")
    return pd.concat(frames, ignore_index=True)


def _committed_report() -> dict:
    path = excess.OUTPUT_DIR / "significance_report.json"
    if not path.is_file():
        pytest.skip("generate with make research-excess")
    return json.loads(path.read_text(encoding="utf-8"))


def _rowwise_spearman(sampled_true: np.ndarray, sampled_pred: np.ndarray) -> np.ndarray:
    """Rowwise Spearman via scipy average ranks, independent of significance.py."""
    true_rank = rankdata(sampled_true, axis=1)
    pred_rank = rankdata(sampled_pred, axis=1)
    true_centered = true_rank - true_rank.mean(axis=1, keepdims=True)
    pred_centered = pred_rank - pred_rank.mean(axis=1, keepdims=True)
    numerator = np.sum(true_centered * pred_centered, axis=1)
    denominator = np.sqrt(
        np.sum(true_centered**2, axis=1) * np.sum(pred_centered**2, axis=1)
    )
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(denominator > 0, numerator / denominator, np.nan)


def _independent_cluster_interval(
    frame: pd.DataFrame,
    model: str,
    *,
    seed: int = significance.DEFAULT_SEED,
    bootstraps: int = significance.DEFAULT_BOOTSTRAPS,
) -> list[float]:
    """Recompute the ticker-cluster interval without calling the production helper."""
    rows = frame[frame["model"].eq(model)]
    tickers = sorted(rows["ticker"].unique().tolist())
    years = sorted(int(year) for year in rows["year"].unique())
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(tickers), size=(bootstraps, len(tickers)))
    per_year = []
    for year in years:
        group = rows[rows["year"].eq(year)].set_index("ticker").reindex(tickers)
        y_true = group["y_true"].to_numpy(dtype=float)
        y_pred = group["y_pred"].to_numpy(dtype=float)
        per_year.append(_rowwise_spearman(y_true[draws], y_pred[draws]))
    pooled = np.nanmean(np.vstack(per_year), axis=0)
    finite = pooled[np.isfinite(pooled)]
    lower, upper = np.quantile(finite, [0.025, 0.975])
    return [float(lower), float(upper)]


def _independent_year_interval(
    frame: pd.DataFrame,
    model: str,
    *,
    seed: int = significance.DEFAULT_SEED,
    bootstraps: int = 2_000,
) -> list[float]:
    """The reviewed defective procedure: each year resampled on its own."""
    rows = frame[frame["model"].eq(model)]
    tickers = sorted(rows["ticker"].unique().tolist())
    years = sorted(int(year) for year in rows["year"].unique())
    rng = np.random.default_rng(seed)
    per_year = []
    for year in years:
        group = rows[rows["year"].eq(year)].set_index("ticker").reindex(tickers)
        y_true = group["y_true"].to_numpy(dtype=float)
        y_pred = group["y_pred"].to_numpy(dtype=float)
        # A fresh, independent draw per year: trajectories do not move together.
        draws = rng.integers(0, len(tickers), size=(bootstraps, len(tickers)))
        per_year.append(_rowwise_spearman(y_true[draws], y_pred[draws]))
    pooled = np.nanmean(np.vstack(per_year), axis=0)
    finite = pooled[np.isfinite(pooled)]
    lower, upper = np.quantile(finite, [0.025, 0.975])
    return [float(lower), float(upper)]


def _clustered_fixture() -> pd.DataFrame:
    """Persistent per-ticker skill: cluster and independent-year bootstraps diverge.

    Half the tickers are ranked correctly by the prediction in every year and half
    are ranked backwards in every year, so a ticker's trajectory carries the whole
    signal. Resampling tickers as clusters preserves that dependence; resampling
    each year independently averages it away.
    """
    rows = []
    size = 12
    for year in (2023, 2024, 2025):
        for index in range(size):
            aligned = index < size // 2
            truth = float(index)
            rows.append(
                {
                    "ticker": f"T{index:02d}",
                    "year": year,
                    "model": "ridge",
                    "y_true": truth + 0.1 * (year - 2023),
                    "y_pred": truth if aligned else -truth,
                    "split": f"test_{year}",
                }
            )
    return pd.DataFrame(rows)


# Four tickers over three years. The rank orders are deliberately non-monotone
# and differ between years, so (a) dropping a duplicated sampled ticker and
# (b) using a different ticker vector per year both change the result.
_SYNTHETIC_VALUES: dict[int, dict[str, tuple[float, float]]] = {
    2023: {"T0": (1.0, 4.0), "T1": (2.0, 1.0), "T2": (3.0, 3.0), "T3": (4.0, 2.0)},
    2024: {"T0": (2.0, 1.0), "T1": (4.0, 3.0), "T2": (1.0, 2.0), "T3": (3.0, 4.0)},
    2025: {"T0": (3.0, 2.0), "T1": (1.0, 4.0), "T2": (4.0, 1.0), "T3": (2.0, 3.0)},
}


def _synthetic_panel() -> pd.DataFrame:
    rows = [
        {
            "ticker": ticker,
            "year": year,
            "model": "ridge",
            "y_true": values[0],
            "y_pred": values[1],
            "split": f"test_{year}",
        }
        for year, per_ticker in _SYNTHETIC_VALUES.items()
        for ticker, values in per_ticker.items()
    ]
    return pd.DataFrame(rows)


def _manual_equal_year_ic(sampled_names: list[str]) -> float:
    """Equal-year mean IC for an explicit sampled ticker list, computed by hand."""
    per_year = []
    for year in sorted(_SYNTHETIC_VALUES):
        values = _SYNTHETIC_VALUES[year]
        y_true = np.array([values[name][0] for name in sampled_names], dtype=float)
        y_pred = np.array([values[name][1] for name in sampled_names], dtype=float)
        per_year.append(significance.spearman_ic(y_true, y_pred))
    return float(np.nanmean(per_year))


# ---------------------------------------------------------------------------
# module-scoped regeneration into an isolated temporary namespace
# ---------------------------------------------------------------------------

PROTECTED_EXCLUDED_DIRS = {"raw", "trusted_raw"}


def _protected_paths() -> list[Path]:
    """Curated data, every nominal artifact namespace, and the contract.

    Raw inputs and the isolated excess namespace under correction are excluded.
    """
    root = excess.ROOT
    paths: set[Path] = set()
    for name in ("trusted", "trusted_clean", "config", "exports", "interim"):
        directory = root / "data" / name
        if directory.is_dir():
            paths.update(item for item in directory.rglob("*") if item.is_file())
    for directory in (root / "experiments").iterdir():
        if not directory.is_dir():
            continue
        if directory.name == "results_excess":
            continue
        if directory.name == "results" or directory.name.startswith("results_") or directory.name == "reports":
            paths.update(item for item in directory.rglob("*") if item.is_file())
    for extra in (root / "experiments" / "leaderboard.csv", root / "model_confidence_contract.json"):
        if extra.is_file():
            paths.add(extra)
    return sorted(paths)


def _snapshot(paths: list[Path]) -> dict[str, str]:
    return {path.as_posix(): _sha256(path) for path in paths}


def _bounded_temp_dir(suffix: str = "") -> Path:
    """A destination the bounded output policy accepts: prefixed, under gettempdir()."""
    return Path(tempfile.mkdtemp(prefix=excess.TEMP_OUTPUT_PREFIX, suffix=suffix))


def _refusing_build_report(*args: object, **kwargs: object) -> dict:
    raise AssertionError(
        "significance.build_report performs post-outcome model selection and must "
        "never be invoked by the R3-TGT-01 generator"
    )


@pytest.fixture(scope="module")
def isolated_regeneration():
    """Generate twice into one bounded temporary directory, with selection sabotaged.

    ``significance.build_report`` is replaced by a raising stub for the whole
    generation. Every artifact assertion in this module therefore runs against
    output that provably never executed the minimum-raw-p selection, rather than
    against output where the selected field was merely deleted afterwards.
    """
    output_dir = _bounded_temp_dir()
    protected = _protected_paths()
    before = _snapshot(protected)

    original = significance.build_report
    significance.build_report = _refusing_build_report
    try:
        excess.run(output_dir)
        first = {path.name: path.read_bytes() for path in sorted(output_dir.iterdir())}
        excess.run(output_dir)
        second = {path.name: path.read_bytes() for path in sorted(output_dir.iterdir())}
    finally:
        significance.build_report = original

    after = _snapshot(protected)
    try:
        yield {
            "output_dir": output_dir,
            "first": first,
            "second": second,
            "protected_before": before,
            "protected_after": after,
            "protected_count": len(protected),
        }
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# frozen harness reuse
# ---------------------------------------------------------------------------


def test_reuses_frozen_harness_and_significance_conventions() -> None:
    assert excess._prediction_rows is run_alternative_targets._prediction_rows
    assert excess.TARGET_COLUMN == "next_year_excess_return_vs_bist100"
    assert excess.TARGET_COLUMN in run_experiments.TARGETS
    assert tuple(run_experiments.MODELS) == tuple(run_experiments.MODEL_CONFIGS)
    assert tuple(significance.ML_MODELS) == tuple(
        name
        for name, config in run_experiments.MODEL_CONFIGS.items()
        if config["kind"] == "ml"
    )
    assert excess.OUTPUT_DIR == excess.ROOT / "experiments" / "results_excess"
    assert excess.REGENERATION_COMMAND == "make research-excess"
    assert excess.FROZEN_ML_FAMILY == tuple(significance.ML_MODELS)
    assert set(excess.FROZEN_BASELINES).isdisjoint(excess.FROZEN_ML_FAMILY)
    assert len(excess.FROZEN_ML_FAMILY) == 6
    assert len(excess.FROZEN_BASELINES) == 3


def test_panel_drops_null_excess_rows_without_filling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = tmp_path / "training.csv"
    pd.DataFrame(
        [
            {"ticker": "A", "year": 2020, "feature": 1.0, "next_year_return_pct": 5.0, excess.TARGET_COLUMN: 2.0},
            {"ticker": "B", "year": 2020, "feature": 2.0, "next_year_return_pct": 6.0, excess.TARGET_COLUMN: None},
            {"ticker": "A", "year": 2021, "feature": 3.0, "next_year_return_pct": 7.0, excess.TARGET_COLUMN: -1.5},
            {"ticker": "B", "year": 2021, "feature": 4.0, "next_year_return_pct": 8.0, excess.TARGET_COLUMN: None},
        ]
    ).to_csv(base, index=False)
    monkeypatch.setattr(run_experiments, "TRAINING_MODELING", base)

    panel, features = run_experiments.build_panel_for_target(excess.TARGET_COLUMN)

    assert features == ["feature"]
    assert panel[["ticker", "feature_year"]].values.tolist() == [["A", 2020], ["A", 2021]]
    assert panel["target_return"].tolist() == [2.0, -1.5]


def test_reconstructed_leaderboard_uses_persisted_rows() -> None:
    rows = []
    for split_index, split in enumerate(run_experiments.SPLITS):
        year = split["test_feature_year"] + 1
        actual = np.arange(6, dtype=float) + split_index
        for model_index, model in enumerate(run_experiments.MODELS):
            predicted = actual if model_index % 2 == 0 else actual[::-1]
            rows.extend(
                {
                    "ticker": f"T{row_index}",
                    "year": year,
                    "model": model,
                    "y_true": float(value),
                    "y_pred": float(predicted[row_index]),
                    "split": split["name"],
                }
                for row_index, value in enumerate(actual)
            )
    leaderboard = excess.reconstruct_leaderboard(pd.DataFrame(rows))

    assert len(leaderboard) == 27
    assert leaderboard["target"].eq(excess.TARGET_COLUMN).all()
    assert leaderboard.groupby("split").size().eq(9).all()
    assert set(leaderboard["kind"]) == {"baseline", "ml"}
    assert leaderboard.iloc[0]["spearman"] == 1.0
    assert leaderboard.iloc[1]["spearman"] == -1.0


def test_evaluated_rows_per_year_rejects_nonuniform_model_coverage() -> None:
    frame = pd.DataFrame(
        {
            "year": [2023, 2023, 2024, 2024],
            "model": ["ridge", "lasso", "ridge", "lasso"],
            "ticker": ["A", "A", "A", "A"],
        }
    )
    assert excess._evaluated_rows_per_year(frame) == {2023: 1, 2024: 1}

    uneven = pd.concat(
        [frame, pd.DataFrame({"year": [2024], "model": ["ridge"], "ticker": ["B"]})],
        ignore_index=True,
    )
    with pytest.raises(ValueError, match="differ across models"):
        excess._evaluated_rows_per_year(uneven)


def test_aggregate_disagreement_is_reported_not_patched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reconstructed = pd.DataFrame(
        [
            {
                "target": excess.TARGET_COLUMN,
                "split": "test_2023",
                "model": "ridge",
                "kind": "ml",
                "spearman": 0.1,
            }
        ]
    )
    existing = tmp_path / "leaderboard_by_target.csv"
    reconstructed.assign(spearman=0.2).to_csv(existing, index=False)
    before = existing.read_bytes()
    monkeypatch.setattr(excess, "CANONICAL_TARGET_LEADERBOARD", existing)

    comparison = excess.compare_existing_aggregate(reconstructed)

    assert comparison["status"] == "disagreement_reported_not_patched"
    assert comparison["mismatches"]
    assert existing.read_bytes() == before


# ---------------------------------------------------------------------------
# 1. ticker-cluster movement
# ---------------------------------------------------------------------------


def test_forced_draw_carries_complete_ticker_trajectories() -> None:
    """A forced ticker sample must contribute each ticker's whole trajectory."""
    panel = _synthetic_panel()
    tickers = sorted(panel["ticker"].unique().tolist())
    # T0 twice (multiplicity), then T1 and T2; T3 never sampled.
    forced = np.array([[0, 0, 1, 2]])

    result = excess.ticker_cluster_bootstrap(panel, draws=forced, bootstraps=1)

    assert result["tickers"] == tickers
    assert result["years"] == [2023, 2024, 2025]
    sampled_names = [tickers[index] for index in forced[0]]
    assert sampled_names == ["T0", "T0", "T1", "T2"]

    for year in result["years"]:
        rows = panel[panel["year"].eq(year)].set_index("ticker")
        expected_true = np.array([rows.at[name, "y_true"] for name in sampled_names])
        expected_pred = np.array([rows.at[name, "y_pred"] for name in sampled_names])
        expected_ic = significance.spearman_ic(expected_true, expected_pred)
        observed = result["per_year_distributions"][year]
        assert observed.shape == (1,)
        assert observed[0] == pytest.approx(expected_ic, abs=1e-12)

    diagnostics = result["diagnostics"]
    assert diagnostics["unit"] == "ticker_cluster"
    assert diagnostics["cluster_key"] == "ticker"
    assert diagnostics["shared_sample_across_years"] is True
    assert diagnostics["independent_within_year_resampling"] is False
    assert diagnostics["clusters"] == 4
    assert diagnostics["trajectory_years"] == [2023, 2024, 2025]
    assert diagnostics["observations_per_trajectory"] == 3


def test_one_sampled_ticker_vector_is_shared_by_all_years() -> None:
    """A per-year vector would change the pooled statistic; a shared vector does not."""
    panel = _synthetic_panel()
    first = np.array([[0, 0, 1, 2]])
    second = np.array([[0, 0, 0, 2]])
    names = sorted(_SYNTHETIC_VALUES[2023])

    a = excess.ticker_cluster_bootstrap(panel, draws=first, bootstraps=1)
    b = excess.ticker_cluster_bootstrap(panel, draws=second, bootstraps=1)

    a_names = [names[index] for index in first[0]]
    b_names = [names[index] for index in second[0]]
    assert a["pooled_distribution"][0] == pytest.approx(
        _manual_equal_year_ic(a_names), abs=1e-12
    )
    assert b["pooled_distribution"][0] == pytest.approx(
        _manual_equal_year_ic(b_names), abs=1e-12
    )

    # A "mixed" implementation that used `first` for 2023 and `second` for the two
    # later years would land here instead. It must not equal the shared-vector value.
    years = sorted(_SYNTHETIC_VALUES)
    mixed = float(
        np.mean(
            [
                a["per_year_distributions"][years[0]][0],
                b["per_year_distributions"][years[1]][0],
                b["per_year_distributions"][years[2]][0],
            ]
        )
    )
    assert a["pooled_distribution"][0] != pytest.approx(mixed, abs=1e-9)


def test_repeated_trajectories_are_not_deduplicated() -> None:
    """A ticker sampled twice must contribute twice, not collapse to one row."""
    panel = _synthetic_panel()
    names = sorted(_SYNTHETIC_VALUES[2023])
    forced = np.array([[0, 0, 1, 2]])

    result = excess.ticker_cluster_bootstrap(panel, draws=forced, bootstraps=1)

    with_multiplicity = _manual_equal_year_ic(["T0", "T0", "T1", "T2"])
    deduplicated = _manual_equal_year_ic(["T0", "T1", "T2"])
    assert with_multiplicity != pytest.approx(deduplicated, abs=1e-9), (
        "fixture must distinguish multiplicity from deduplication"
    )
    assert result["pooled_distribution"][0] == pytest.approx(
        with_multiplicity, abs=1e-12
    )
    assert result["pooled_distribution"][0] != pytest.approx(deduplicated, abs=1e-9)
    assert [names[index] for index in forced[0]] == ["T0", "T0", "T1", "T2"]


def test_degenerate_all_identical_draw_fails_honestly() -> None:
    """Zero within-year variance must refuse an interval rather than invent one."""
    panel = _synthetic_panel()
    with pytest.raises(excess.ExcessBootstrapError, match="finite equal-year IC"):
        excess.ticker_cluster_bootstrap(
            panel, draws=np.array([[2, 2, 2, 2]]), bootstraps=1
        )


# ---------------------------------------------------------------------------
# 2. independent-year bootstrap rejection
# ---------------------------------------------------------------------------


def test_independent_year_resampling_does_not_reproduce_cluster_interval() -> None:
    """The reviewed per-year procedure gives a materially narrower interval."""
    fixture = _clustered_fixture()

    cluster = excess.ticker_cluster_bootstrap(fixture, bootstraps=2_000)["bootstrap_ci_95"]
    per_year = _independent_year_interval(fixture, "ridge", bootstraps=2_000)

    cluster_width = cluster[1] - cluster[0]
    per_year_width = per_year[1] - per_year[0]
    assert cluster_width > per_year_width * 1.3, (
        f"cluster interval {cluster} should be materially wider than the "
        f"independent-year interval {per_year}"
    )


def test_helper_contract_rejects_per_year_draw_matrices() -> None:
    """The helper accepts one shared ticker vector, not one matrix per year."""
    panel = _synthetic_panel()
    # A caller trying to supply an independent sample per year has the wrong shape.
    with pytest.raises(excess.ExcessBootstrapError, match="shape"):
        excess.ticker_cluster_bootstrap(
            panel, draws=np.zeros((3, 2, 4), dtype=int), bootstraps=3
        )
    with pytest.raises(excess.ExcessBootstrapError, match="shape"):
        excess.ticker_cluster_bootstrap(
            panel, draws=np.zeros((5, 12), dtype=int), bootstraps=5
        )
    with pytest.raises(excess.ExcessBootstrapError, match="outside the cohort"):
        excess.ticker_cluster_bootstrap(
            panel, draws=np.array([[0, 1, 2, 9]]), bootstraps=1
        )


# ---------------------------------------------------------------------------
# 3. committed cluster interval
# ---------------------------------------------------------------------------


def test_committed_intervals_match_independent_cluster_recomputation() -> None:
    frame = _load_committed_dumps()
    report = _committed_report()
    committed = {
        result["model"]: result["pooled"]["bootstrap_ci_95"] for result in report["models"]
    }

    for model in excess.FROZEN_ML_FAMILY:
        expected = _independent_cluster_interval(frame, model)
        assert committed[model] == pytest.approx(expected, rel=0.0, abs=1e-12), model


def test_committed_intervals_differ_from_the_reviewed_per_year_procedure() -> None:
    """Guards against silently relabelling a per-year row bootstrap as clustered."""
    frame = _load_committed_dumps()
    report = _committed_report()
    committed = {
        result["model"]: result["pooled"]["bootstrap_ci_95"] for result in report["models"]
    }

    per_year = _independent_year_interval(frame, "gradient_boosting", bootstraps=10_000)
    assert committed["gradient_boosting"] != pytest.approx(per_year, abs=1e-6)


def test_committed_bootstrap_metadata_declares_the_cluster_unit() -> None:
    report = _committed_report()
    procedure = report["analysis"]["bootstrap_procedure"]
    assert procedure["unit"] == "ticker_cluster"
    assert procedure["cluster_key"] == "ticker"
    assert procedure["clusters"] == 40
    assert procedure["trajectory_years"] == [2023, 2024, 2025]
    assert procedure["requested_resamples"] == significance.DEFAULT_BOOTSTRAPS
    assert procedure["seed"] == significance.DEFAULT_SEED
    assert "independently" not in report["analysis"]["bootstrap"].lower()
    assert "ticker-cluster" in report["analysis"]["bootstrap"].lower()

    for result in report["models"]:
        diagnostics = result["pooled"]["bootstrap"]
        assert diagnostics["unit"] == "ticker_cluster"
        assert diagnostics["clusters"] == 40
        assert diagnostics["valid_resamples"] == significance.DEFAULT_BOOTSTRAPS
        assert diagnostics["invalid_resamples"] == 0
        assert diagnostics["independent_within_year_resampling"] is False


# ---------------------------------------------------------------------------
# 4. no post-outcome selection
# ---------------------------------------------------------------------------


FORBIDDEN_JSON_KEYS = {
    "selected_model",
    "headline_model",
    "best_model",
    "strongest_model",
    "winning_model",
    "most_significant_model",
    "headline",
}


def _collect_keys(payload: object) -> set[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            found.add(str(key).lower())
            found |= _collect_keys(value)
    elif isinstance(payload, list):
        for value in payload:
            found |= _collect_keys(value)
    return found


@pytest.mark.parametrize("filename", ["significance_report.json", "artifact_manifest.json"])
def test_generated_json_contains_no_selection_key(filename: str) -> None:
    path = excess.OUTPUT_DIR / filename
    if not path.is_file():
        pytest.skip("generate with make research-excess")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert not (_collect_keys(payload) & FORBIDDEN_JSON_KEYS)
    excess.assert_no_selection_keys(payload)


def test_selection_key_guard_detects_a_reintroduced_winner() -> None:
    with pytest.raises(ValueError, match="selection key"):
        excess.assert_no_selection_keys({"models": [{"headline_model": "gradient_boosting"}]})
    with pytest.raises(ValueError, match="selection key"):
        excess.assert_no_selection_keys({"headline": {"model": "ridge"}})
    with pytest.raises(ValueError, match="selection key"):
        excess.assert_no_selection_keys({"analysis": {"best_model": "lasso"}})


@pytest.mark.parametrize(
    "wording",
    [
        "The selected model is gradient boosting.",
        "The headline model is gradient boosting.",
        "Gradient boosting is the best model here.",
        "The strongest model is random forest.",
        "The smallest pooled raw p-value belongs to gradient boosting.",
        "The winning model survived nothing.",
    ],
)
def test_selection_language_guard_rejects_post_outcome_framing(wording: str) -> None:
    with pytest.raises(ValueError, match="Post-outcome model selection"):
        excess.validate_no_selection_language(wording)


def test_generated_markdown_contains_no_selection_language() -> None:
    path = excess.OUTPUT_DIR / "significance_report.md"
    if not path.is_file():
        pytest.skip("generate with make research-excess")
    markdown = path.read_text(encoding="utf-8")

    excess.validate_no_selection_language(markdown)
    lowered = markdown.lower()
    for phrase in (
        "smallest pooled raw p-value",
        "smallest raw p-value",
        "selected model",
        "headline model",
        "best model",
        "most significant model",
        "belongs to **",
    ):
        assert phrase not in lowered, phrase

    # Gradient boosting appears only as an ordinary row / ordinary list member,
    # never in a heading or in bold emphasis.
    for line in markdown.splitlines():
        if "gradient_boosting" not in line and "gradient boosting" not in line.lower():
            continue
        assert not line.lstrip().startswith("#"), line
        assert "**gradient" not in line.lower(), line


def test_reporting_order_is_frozen_and_ignores_outcome_statistics() -> None:
    """Permuting outcome statistics in a fixture must not change reporting order."""
    scrambled = list(reversed([*excess.FROZEN_ML_FAMILY, *excess.FROZEN_BASELINES]))
    absurd = {
        name: {
            "model": name,
            "kind": "ml" if name in excess.FROZEN_ML_FAMILY else "baseline",
            "pooled": {
                # deliberately anti-correlated with the frozen order
                "permutation_p_value_two_sided": 0.9 - 0.1 * index,
                "observed_ic": -0.9 + 0.1 * index,
                "bonferroni_adjusted_p_value": 0.5,
                "significant_fwer_0_05": False,
            },
            "exploratory_by_split": [],
        }
        for index, name in enumerate(scrambled)
    }
    report = {"models": [absurd[name] for name in scrambled]}

    ordered = excess.order_models_frozen(report)

    assert [item["model"] for item in ordered["models"]] == [
        *excess.FROZEN_ML_FAMILY,
        *excess.FROZEN_BASELINES,
    ]

    # Reversing the statistics again must not move anything.
    for index, name in enumerate(scrambled):
        absurd[name]["pooled"]["permutation_p_value_two_sided"] = 0.01 * index
    reordered = excess.order_models_frozen({"models": [absurd[name] for name in scrambled]})
    assert [item["model"] for item in reordered["models"]] == [
        item["model"] for item in ordered["models"]
    ]


def test_order_models_frozen_rejects_a_changed_family() -> None:
    with pytest.raises(ValueError, match="frozen family"):
        excess.order_models_frozen(
            {"models": [{"model": "ridge", "kind": "ml", "pooled": {}}]}
        )


def test_family_conclusion_names_no_individual_model() -> None:
    report = _committed_report()
    conclusion = report["family_conclusion"]
    assert conclusion["any_model_survives_family_wise_correction"] is False
    assert conclusion["models_surviving_family_wise_correction"] == []
    assert conclusion["count_surviving_family_wise_correction"] == 0
    assert conclusion["reliable_predictive_edge_established"] is False
    text = conclusion["conclusion"].lower()
    for model in [*excess.FROZEN_ML_FAMILY, *excess.FROZEN_BASELINES]:
        assert model not in text
        assert model.replace("_", " ") not in text
    assert "does not replace" in conclusion["bootstrap_interpretation"].lower()


def test_reporting_policy_is_recorded_in_report_and_manifest() -> None:
    report = _committed_report()
    manifest_path = excess.OUTPUT_DIR / "artifact_manifest.json"
    if not manifest_path.is_file():
        pytest.skip("generate with make research-excess")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for policy in (report["reporting_policy"], manifest["reporting_policy"]):
        assert policy["statement"] == excess.REPORTING_POLICY_STATEMENT
        assert policy["result_driven_selection_performed"] is False
        assert policy["frozen_ml_family_order"] == list(excess.FROZEN_ML_FAMILY)
        assert policy["frozen_baseline_order"] == list(excess.FROZEN_BASELINES)
        assert "symmetric" in policy["model_presentation"]
    assert report["claim_safety"]["result_driven_model_selection_performed"] is False
    # The no-selection claim must match the actual structure: frozen order, no winner.
    assert [item["model"] for item in report["models"]] == [
        *excess.FROZEN_ML_FAMILY,
        *excess.FROZEN_BASELINES,
    ]


# ---------------------------------------------------------------------------
# 5. symmetric family reporting
# ---------------------------------------------------------------------------


def test_all_six_family_members_share_one_schema_with_paired_p_values() -> None:
    report = _committed_report()
    by_name = {result["model"]: result for result in report["models"]}

    schemas = set()
    for model in excess.FROZEN_ML_FAMILY:
        pooled = by_name[model]["pooled"]
        schemas.add(frozenset(pooled))
        assert by_name[model]["kind"] == "ml"
        raw = pooled["permutation_p_value_two_sided"]
        adjusted = pooled["bonferroni_adjusted_p_value"]
        assert raw is not None and adjusted is not None
        assert adjusted == pytest.approx(min(1.0, raw * len(excess.FROZEN_ML_FAMILY)))
        assert pooled["significant_fwer_0_05"] is (adjusted < 0.05)
        assert len(pooled["bootstrap_ci_95"]) == 2
    assert len(schemas) == 1, "family members must share one pooled schema"

    for model in excess.FROZEN_BASELINES:
        pooled = by_name[model]["pooled"]
        assert by_name[model]["kind"] == "baseline"
        assert pooled["bonferroni_adjusted_p_value"] is None
        assert pooled["significant_fwer_0_05"] is None
    assert report["analysis"]["multiplicity"]["family"] == list(excess.FROZEN_ML_FAMILY)
    assert report["analysis"]["multiplicity"]["family_size"] == 6


def test_markdown_reports_the_family_symmetrically() -> None:
    path = excess.OUTPUT_DIR / "significance_report.md"
    if not path.is_file():
        pytest.skip("generate with make research-excess")
    markdown = path.read_text(encoding="utf-8")

    family_rows = [
        line
        for line in markdown.splitlines()
        if line.startswith("| ") and line.split("|")[1].strip() in excess.FROZEN_ML_FAMILY
    ]
    # one row per family member in the family table, plus the per-year rows
    header_index = markdown.index("## Prespecified six-model ML family")
    baseline_index = markdown.index("## Non-family baselines")
    family_table = markdown[header_index:baseline_index]
    ordered = [
        line.split("|")[1].strip()
        for line in family_table.splitlines()
        if line.startswith("| ") and line.split("|")[1].strip() in excess.FROZEN_ML_FAMILY
    ]
    assert ordered == list(excess.FROZEN_ML_FAMILY)
    assert "Bonferroni-adjusted p" in family_table
    assert "Permutation p (raw)" in family_table
    assert family_rows

    baseline_table = markdown[baseline_index:]
    baseline_rows = [
        line.split("|")[1].strip()
        for line in baseline_table.splitlines()
        if line.startswith("| ") and line.split("|")[1].strip() in excess.FROZEN_BASELINES
    ]
    assert baseline_rows[: len(excess.FROZEN_BASELINES)] == list(excess.FROZEN_BASELINES)
    assert "outside the ML family" in baseline_table
    assert "0 of 6 family members survive" in markdown


# ---------------------------------------------------------------------------
# 6. write isolation
# ---------------------------------------------------------------------------


def test_default_output_dir_is_the_excess_namespace() -> None:
    assert excess._resolve_output_dir(None) == excess.OUTPUT_DIR
    # Naming the default explicitly is the same destination, not an override.
    assert excess._resolve_output_dir(excess.OUTPUT_DIR) == excess.OUTPUT_DIR


def test_a_prefixed_directory_under_the_temporary_root_is_accepted() -> None:
    """The one permitted non-default destination: prefixed, under gettempdir()."""
    destination = _bounded_temp_dir()
    try:
        resolved = excess._resolve_output_dir(destination)
        assert resolved == destination
        assert resolved.name.startswith(excess.TEMP_OUTPUT_PREFIX)
        assert resolved.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve())
    finally:
        shutil.rmtree(destination, ignore_errors=True)


@pytest.mark.parametrize(
    "relative",
    [
        "experiments/results",
        "experiments/results/runs",
        "experiments/reports",
        "experiments",
        "experiments/results_real_terms",
        "experiments/results_excess/scratch",
        "data/trusted_clean",
        "data/trusted",
        "backend/app",
        "frontend/src",
        ".",
    ],
)
def test_output_dir_outside_the_excess_namespace_is_refused(relative: str) -> None:
    target = excess.ROOT / relative
    with pytest.raises(excess.ExcessOutputPathError, match="isolated excess namespace"):
        excess._resolve_output_dir(target)


def test_arbitrary_external_and_system_paths_are_refused() -> None:
    """Filesystem root, /etc, the home directory, /tmp, and the temp root itself."""
    candidates = [
        Path("/"),
        Path("/etc"),
        Path.home(),
        Path.home() / "financeiq-r3-tgt-01-elsewhere",
        Path("/tmp"),
        Path("/var"),
        Path("/usr/local/financeiq-r3-tgt-01-out"),
        Path(tempfile.gettempdir()),
        Path(tempfile.gettempdir()).resolve(),
    ]
    for candidate in candidates:
        with pytest.raises(excess.ExcessOutputPathError) as error:
            excess._resolve_output_dir(candidate)
        assert "refusing" in str(error.value), candidate


def test_temporary_destination_must_carry_the_required_prefix() -> None:
    destination = Path(tempfile.mkdtemp(prefix="not-financeiq-"))
    try:
        with pytest.raises(excess.ExcessOutputPathError, match="does not begin with"):
            excess._resolve_output_dir(destination)
    finally:
        shutil.rmtree(destination, ignore_errors=True)


def test_temporary_root_itself_is_refused() -> None:
    with pytest.raises(excess.ExcessOutputPathError, match="temporary root itself"):
        excess._resolve_output_dir(Path(tempfile.gettempdir()))


def test_a_symlinked_destination_is_refused() -> None:
    """The final component may not be a symlink, even with the required prefix."""
    holder = _bounded_temp_dir()
    outside = Path(tempfile.mkdtemp(prefix="financeiq-r3-outside-"))
    link = holder / f"{excess.TEMP_OUTPUT_PREFIX}link"
    try:
        link.symlink_to(outside, target_is_directory=True)
        with pytest.raises(
            excess.ExcessOutputPathError, match="symbolic-link output destination"
        ):
            excess._resolve_output_dir(link)
    finally:
        shutil.rmtree(holder, ignore_errors=True)
        shutil.rmtree(outside, ignore_errors=True)


def test_a_symlink_component_escaping_the_temporary_tree_is_refused() -> None:
    """A symlink *inside* the allowed tree may not be used to escape it."""
    holder = _bounded_temp_dir()
    escape_target = excess.ROOT / "experiments"
    bridge = holder / "escape"
    try:
        bridge.symlink_to(escape_target, target_is_directory=True)
        destination = bridge / f"{excess.TEMP_OUTPUT_PREFIX}dest"
        with pytest.raises(
            excess.ExcessOutputPathError, match="symbolic-link component"
        ):
            excess._resolve_output_dir(destination)
        # The escape really would have left the temporary tree.
        assert not destination.resolve().is_relative_to(
            Path(tempfile.gettempdir()).resolve()
        )
    finally:
        shutil.rmtree(holder, ignore_errors=True)


def test_run_refuses_a_nominal_destination_before_writing() -> None:
    nominal = excess.ROOT / "experiments" / "results"
    before = _snapshot(sorted(item for item in nominal.rglob("*") if item.is_file()))
    with pytest.raises(excess.ExcessOutputPathError):
        excess.run(nominal)
    after = _snapshot(sorted(item for item in nominal.rglob("*") if item.is_file()))
    assert before == after


def test_run_refuses_an_arbitrary_external_destination_before_writing() -> None:
    """Refusal happens before mkdir: no directory and no file may be created."""
    parent = Path(tempfile.mkdtemp(prefix="financeiq-r3-outside-"))
    destination = parent / "arbitrary-output"
    try:
        with pytest.raises(excess.ExcessOutputPathError):
            excess.run(destination)
        assert not destination.exists()
        assert sorted(parent.iterdir()) == []
    finally:
        shutil.rmtree(parent, ignore_errors=True)


def test_output_path_policy_is_recorded_without_a_machine_path() -> None:
    policy = excess.build_output_path_policy()
    assert policy["default_output_directory"] == "experiments/results_excess"
    assert policy["required_destination_name_prefix"] == excess.TEMP_OUTPUT_PREFIX
    assert policy["temporary_root_authority"] == "tempfile.gettempdir()"
    assert policy["temporary_root_hardcoded"] is False
    assert policy["temporary_root_itself_accepted"] is False
    assert policy["symlinked_destination_accepted"] is False
    assert policy["symlinked_path_component_accepted"] is False
    assert policy["arbitrary_external_paths_accepted"] is False
    assert policy["refusal_exception"] == "ExcessOutputPathError"
    assert "before any output file" in policy["refusal_timing"]
    # The concrete temporary root is environment-specific and must not be baked
    # into a deterministic artifact.
    assert tempfile.gettempdir() not in json.dumps(policy)


def test_generated_files_stay_inside_the_requested_namespace(
    isolated_regeneration: dict,
) -> None:
    output_dir = isolated_regeneration["output_dir"]
    produced = sorted(path.name for path in output_dir.iterdir())
    assert produced == [
        "artifact_manifest.json",
        "leaderboard.csv",
        "predictions_test_2023.csv",
        "predictions_test_2024.csv",
        "predictions_test_2025.csv",
        "significance_report.json",
        "significance_report.md",
    ]
    assert all(path.is_file() for path in output_dir.iterdir())


# ---------------------------------------------------------------------------
# 7. dump integrity
# ---------------------------------------------------------------------------


def test_committed_dumps_have_the_declared_schema_and_cohort() -> None:
    paths = sorted(excess.OUTPUT_DIR.glob("predictions_test_*.csv"))
    if not paths:
        pytest.skip("generate with make research-excess")
    assert [path.name for path in paths] == [
        "predictions_test_2023.csv",
        "predictions_test_2024.csv",
        "predictions_test_2025.csv",
    ]
    frame = _load_committed_dumps()
    for path in paths:
        assert list(pd.read_csv(path).columns) == significance.REQUIRED_COLUMNS

    assert not frame.duplicated(["model", "ticker", "year"]).any()
    assert np.isfinite(frame[["y_true", "y_pred"]].to_numpy(dtype=float)).all()
    assert frame[["ticker", "year", "model", "y_true", "y_pred"]].notna().all().all()
    assert sorted(frame["year"].unique().tolist()) == [2023, 2024, 2025]
    assert sorted(frame["model"].unique().tolist()) == sorted(run_experiments.MODELS)

    per_year_tickers = {
        int(year): set(group["ticker"]) for year, group in frame.groupby("year")
    }
    cohorts = list(per_year_tickers.values())
    assert all(len(cohort) == 40 for cohort in cohorts)
    assert all(cohort == cohorts[0] for cohort in cohorts), "cohort must be stable"


def test_cluster_panel_refuses_null_duplicate_and_ragged_input() -> None:
    panel = _synthetic_panel()

    missing = panel.drop(columns=["ticker"])
    with pytest.raises(excess.ExcessBootstrapError, match="requires columns"):
        excess.ticker_cluster_bootstrap(missing)

    nulled = panel.copy()
    nulled.loc[0, "y_true"] = np.nan
    with pytest.raises(excess.ExcessBootstrapError, match="refuses null"):
        excess.ticker_cluster_bootstrap(nulled)

    infinite = panel.copy()
    infinite.loc[0, "y_pred"] = np.inf
    with pytest.raises(excess.ExcessBootstrapError, match="non-finite"):
        excess.ticker_cluster_bootstrap(infinite)

    duplicated = pd.concat([panel, panel.iloc[[0]]], ignore_index=True)
    with pytest.raises(excess.ExcessBootstrapError, match="duplicate ticker/year"):
        excess.ticker_cluster_bootstrap(duplicated)

    ragged = panel.drop(
        index=panel[(panel["ticker"] == "T0") & (panel["year"] == 2024)].index
    )
    with pytest.raises(excess.ExcessBootstrapError, match="inconsistent ticker coverage"):
        excess.ticker_cluster_bootstrap(ragged)

    with pytest.raises(excess.ExcessBootstrapError, match="at least"):
        excess.ticker_cluster_bootstrap(panel[panel["ticker"].isin(["T0", "T1"])])

    with pytest.raises(excess.ExcessBootstrapError, match="no rows"):
        excess.ticker_cluster_bootstrap(panel.iloc[0:0])


# ---------------------------------------------------------------------------
# 7b. strict cluster-key validation
# ---------------------------------------------------------------------------


def _panel_with(column: str, position: int, value: object) -> pd.DataFrame:
    """Synthetic panel with one cluster-key cell replaced, dtype preserved as object."""
    panel = _synthetic_panel()
    panel[column] = panel[column].astype(object)
    panel.loc[position, column] = value
    return panel


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        (2023.5, "fractional year"),
        (2024.75, "fractional year"),
        ("2023", "strings are never coerced"),
        (b"2023", "strings are never coerced"),
        (True, "booleans are not years"),
        (False, "booleans are not years"),
        (np.bool_(True), "booleans are not years"),
        (float("nan"), "NaN year"),
        (np.nan, "NaN year"),
        (float("inf"), "non-finite year"),
        (float("-inf"), "non-finite year"),
        (np.float64("inf"), "non-finite year"),
        (None, "null year"),
        (2022, "outside the expected evaluation years"),
        (2026, "outside the expected evaluation years"),
        (0, "outside the expected evaluation years"),
        (2023.0000001, "fractional year"),
        ([2023], "non-numeric year"),
        (Decimal("2023"), "non-numeric year"),
        (Fraction(2023, 1), "non-numeric year"),
        (complex(2023, 0), "non-numeric year"),
        (pd.NaT, "null year"),
    ],
)
def test_malformed_years_raise_excess_bootstrap_error(value: object, reason: str) -> None:
    """No silent floor, truncation, rounding, or astype(int) before validation."""
    panel = _panel_with("year", 0, value)
    with pytest.raises(excess.ExcessBootstrapError, match=re.escape(reason)) as error:
        excess.ticker_cluster_bootstrap(panel)
    assert type(error.value) is excess.ExcessBootstrapError


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        (None, "null ticker"),
        (np.nan, "null ticker"),
        (123, "non-string ticker"),
        (12.5, "non-string ticker"),
        (np.int64(7), "non-string ticker"),
        (True, "non-string ticker"),
        ("", "empty ticker"),
        ("   ", "whitespace-only ticker"),
        ("\t", "whitespace-only ticker"),
        (" T0", "leading or trailing whitespace"),
        ("T0 ", "leading or trailing whitespace"),
        ("\nT0", "leading or trailing whitespace"),
    ],
)
def test_malformed_tickers_raise_excess_bootstrap_error(
    value: object, reason: str
) -> None:
    panel = _panel_with("ticker", 0, value)
    with pytest.raises(excess.ExcessBootstrapError, match=re.escape(reason)) as error:
        excess.ticker_cluster_bootstrap(panel)
    assert type(error.value) is excess.ExcessBootstrapError


def test_fractional_year_is_never_floored_into_a_valid_year() -> None:
    """2023.5 must be refused outright, not quietly become 2023."""
    panel = _panel_with("year", 0, 2023.5)
    with pytest.raises(excess.ExcessBootstrapError, match="fractional year"):
        excess._cluster_panel(panel)
    # The honest control: the same panel with a genuine integer year works.
    assert excess._cluster_panel(_panel_with("year", 0, 2023))[1] == [2023, 2024, 2025]


def test_integer_valued_floats_are_accepted_only_inside_the_expected_year_set() -> None:
    assert excess.validated_cluster_year(np.float64(2024.0), position=0) == 2024
    assert excess.validated_cluster_year(np.int64(2025), position=0) == 2025
    with pytest.raises(excess.ExcessBootstrapError, match="outside the expected"):
        excess.validated_cluster_year(np.float64(2026.0), position=0)


def test_unexpected_and_missing_evaluation_years_are_refused() -> None:
    panel = _synthetic_panel()

    extra = panel[panel["year"].eq(2025)].assign(year=2026)
    with pytest.raises(
        excess.ExcessBootstrapError, match="outside the expected evaluation years"
    ):
        excess.ticker_cluster_bootstrap(pd.concat([panel, extra], ignore_index=True))

    truncated = panel[panel["year"].ne(2024)]
    with pytest.raises(excess.ExcessBootstrapError, match="expects evaluation years"):
        excess.ticker_cluster_bootstrap(truncated)


def test_duplicate_and_ragged_ticker_coverage_are_refused() -> None:
    panel = _synthetic_panel()

    duplicated = pd.concat([panel, panel.iloc[[3]]], ignore_index=True)
    with pytest.raises(excess.ExcessBootstrapError, match="duplicate ticker/year"):
        excess.ticker_cluster_bootstrap(duplicated)

    # One ticker absent from exactly one year: complete coverage is required.
    ragged = panel.drop(
        index=panel[(panel["ticker"] == "T2") & (panel["year"] == 2025)].index
    )
    with pytest.raises(excess.ExcessBootstrapError, match="inconsistent ticker coverage"):
        excess.ticker_cluster_bootstrap(ragged)


def test_valid_cluster_keys_still_reproduce_the_committed_arithmetic() -> None:
    """Strict validation must not perturb a well-formed panel."""
    frame = _load_committed_dumps()
    for model in ("ridge", "gradient_boosting"):
        tickers, years, per_year = excess._cluster_panel(
            frame[frame["model"].eq(model)]
        )
        assert years == [2023, 2024, 2025]
        assert len(tickers) == 40
        rows = frame[frame["model"].eq(model)]
        for year in years:
            group = rows[rows["year"].eq(year)].set_index("ticker").reindex(tickers)
            assert per_year[year][0] == pytest.approx(
                group["y_true"].to_numpy(dtype=float), abs=0.0
            )
            assert per_year[year][1] == pytest.approx(
                group["y_pred"].to_numpy(dtype=float), abs=0.0
            )


# ---------------------------------------------------------------------------
# 7c. the selecting report helper is never executed
# ---------------------------------------------------------------------------


def test_generation_succeeds_while_build_report_raises() -> None:
    """Adversarial proof: sabotage the selecting helper; generation must still work."""
    destination = _bounded_temp_dir()
    original = significance.build_report
    significance.build_report = _refusing_build_report
    try:
        json_path, markdown_path, manifest_path = excess.run(destination)
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        assert "headline" not in payload
        assert not (_collect_keys(payload) & FORBIDDEN_JSON_KEYS)
        assert [item["model"] for item in payload["models"]] == [
            *excess.FROZEN_ML_FAMILY,
            *excess.FROZEN_BASELINES,
        ]
        assert markdown_path.is_file() and manifest_path.is_file()
    finally:
        significance.build_report = original
        shutil.rmtree(destination, ignore_errors=True)


def test_build_family_report_does_not_call_the_selecting_helper() -> None:
    """The report builder itself must not depend on the minimum-p helper."""
    frame = _synthetic_family_frame(list(_FAMILY_ORDER))
    original_build = significance.build_report
    original_render = significance.render_markdown
    significance.build_report = _refusing_build_report
    significance.render_markdown = _refusing_build_report
    try:
        report = excess.build_family_report(
            frame,
            [],
            {2023: 6, 2024: 6, 2025: 6},
            permutations=1_000,
            bootstraps=200,
            power_simulations=100,
        )
    finally:
        significance.build_report = original_build
        significance.render_markdown = original_render

    assert "headline" not in report
    assert not (_collect_keys(report) & FORBIDDEN_JSON_KEYS)
    assert [item["model"] for item in report["models"]] == list(_FAMILY_ORDER)


def test_no_outcome_selecting_significance_helper_is_called_anywhere() -> None:
    """Source-level: every significance.* call in the generator is non-selecting."""
    source = (excess.ROOT / "experiments" / "run_excess_basis.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    called: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id == "significance":
                called.add(func.attr)

    selecting = {"build_report", "render_markdown", "run", "main"}
    assert not (called & selecting), sorted(called & selecting)
    # Whitelist rather than blacklist: a newly introduced helper has to be
    # reviewed before it can be called from here.
    allowed = {
        "analyze_model",
        "load_prediction_dumps",
        "minimum_detectable_ic",
        "simulate_fisher_power",
        "fisher_power",
        "spearman_ic",
        "_rowwise_correlation",
        "_ci",
        # Reviewed for the post-review trajectory-preserving sensitivity: it
        # locates one observed statistic inside one null distribution and
        # compares nothing across models.
        "_percentile",
    }
    assert called <= allowed, sorted(called - allowed)


# ---------------------------------------------------------------------------
# 7d. frozen family order is invariant to the observed statistics
# ---------------------------------------------------------------------------


_FAMILY_ORDER = (*excess.FROZEN_ML_FAMILY, *excess.FROZEN_BASELINES)


def _synthetic_family_frame(model_order: list[str]) -> pd.DataFrame:
    """Nine models over three years; ``model_order`` decides who gets which signal."""
    size = 6
    truth = np.arange(size, dtype=float)
    rows = []
    for year in (2023, 2024, 2025):
        for rank, model in enumerate(model_order):
            predicted = np.roll(truth[::-1] if rank % 2 else truth, rank)
            for index in range(size):
                rows.append(
                    {
                        "ticker": f"T{index}",
                        "year": year,
                        "model": model,
                        "y_true": float(truth[index] + 0.1 * (year - 2023)),
                        "y_pred": float(predicted[index]),
                        "split": f"test_{year}",
                    }
                )
    return pd.DataFrame(rows)


def _family_report(model_order: list[str]) -> dict:
    return excess.build_family_report(
        _synthetic_family_frame(model_order),
        [],
        {2023: 6, 2024: 6, 2025: 6},
        permutations=1_000,
        bootstraps=200,
        power_simulations=100,
    )


def test_frozen_order_survives_permuted_synthetic_statistics() -> None:
    """Reassigning the signal across models must not move a single reported row."""
    straight = _family_report(list(_FAMILY_ORDER))
    reversed_signal = _family_report(list(reversed(_FAMILY_ORDER)))

    for report in (straight, reversed_signal):
        assert [item["model"] for item in report["models"]] == list(_FAMILY_ORDER)
        assert [item["model"] for item in excess.order_models_frozen(report)["models"]] == list(
            _FAMILY_ORDER
        )

    straight_ic = {item["model"]: item["pooled"]["observed_ic"] for item in straight["models"]}
    reversed_ic = {
        item["model"]: item["pooled"]["observed_ic"] for item in reversed_signal["models"]
    }
    # Non-vacuous: the statistics really did move even though the order did not.
    assert straight_ic != reversed_ic
    assert set(np.round(list(straight_ic.values()), 12)) == set(
        np.round(list(reversed_ic.values()), 12)
    )


def test_family_report_pairs_raw_and_adjusted_p_values_symmetrically() -> None:
    report = _family_report(list(_FAMILY_ORDER))
    schemas = set()
    for item in report["models"]:
        pooled = item["pooled"]
        if item["kind"] == "ml":
            schemas.add(frozenset(pooled))
            assert pooled["bonferroni_adjusted_p_value"] == pytest.approx(
                min(1.0, pooled["permutation_p_value_two_sided"] * 6)
            )
        else:
            assert pooled["bonferroni_adjusted_p_value"] is None
    assert len(schemas) == 1
    assert report["analysis"]["multiplicity"]["family"] == list(excess.FROZEN_ML_FAMILY)
    assert report["analysis"]["multiplicity"]["family_size"] == 6


# ---------------------------------------------------------------------------
# 7e. the power report describes the design that was actually evaluated
# ---------------------------------------------------------------------------


def test_current_power_design_is_forty_rows_per_year_from_the_dumps() -> None:
    report = _committed_report()
    current = report["power_analysis"]["current_design"]

    assert current["rows_per_year"] == 40
    assert current["years"] == [2023, 2024, 2025]
    assert current["test_years"] == 3
    assert current["total_evaluated_rows_per_model"] == 120
    assert current["status"] == "observed"

    frame = _load_committed_dumps()
    per_year = {
        int(year): int(group.groupby("model").size().unique()[0])
        for year, group in frame.groupby("year")
    }
    assert per_year == {2023: 40, 2024: 40, 2025: 40}
    assert sorted(set(per_year.values())) == [current["rows_per_year"]]
    assert sorted(per_year) == current["years"]


def test_exactly_one_current_power_design_exists() -> None:
    report = _committed_report()
    power = report["power_analysis"]
    assert excess._observed_design_count(power) == 1
    # The two analytic rows are views of the one design, not separate designs.
    views = power["current_design"]["views"]
    assert [view["view_of"] for view in views] == ["current_design", "current_design"]
    assert all("status" not in view for view in views)


def test_hypothetical_designs_never_duplicate_the_current_design() -> None:
    report = _committed_report()
    power = report["power_analysis"]
    current = power["current_design"]
    hypothetical = power["hypothetical_planning_sensitivities"]

    assert hypothetical["status"] == "hypothetical"
    assert hypothetical["is_current_evidence"] is False
    assert hypothetical["deduplicated_against_current_design"] is True

    current_key = (current["rows_per_year"], current["test_years"])
    keys = [
        (entry["planning_rows_per_year"], entry["total_test_years"])
        for entry in hypothetical["entries"]
    ]
    assert current_key not in keys
    assert len(keys) == len(set(keys))
    assert all(entry["status"] == "hypothetical" for entry in hypothetical["entries"])
    assert all(
        entry["is_current_evidence"] is False for entry in hypothetical["entries"]
    )
    assert all(entry["total_test_years"] > current["test_years"] for entry in hypothetical["entries"])
    # The removed duplicate is recorded rather than silently dropped.
    excluded = hypothetical["excluded_duplicates_of_current_design"]
    assert [(item["planning_rows_per_year"], item["total_test_years"]) for item in excluded] == [
        current_key
    ]


def test_no_current_eighty_row_prose_survives_anywhere() -> None:
    json_text = (excess.OUTPUT_DIR / "significance_report.json").read_text(
        encoding="utf-8"
    )
    markdown = (excess.OUTPUT_DIR / "significance_report.md").read_text(encoding="utf-8")
    manifest = (excess.OUTPUT_DIR / "artifact_manifest.json").read_text(encoding="utf-8")

    for text in (json_text, markdown, manifest):
        excess.validate_no_current_design_row_contradiction(text)
    assert "80-row prediction-dump design" not in json_text
    assert "not the current 80-row" not in json_text
    assert "80 rows per year" not in markdown.lower()
    # The nominal 80-row figure may still appear, but only as labelled context.
    assert "nominal-basis context" in markdown


@pytest.mark.parametrize(
    "wording",
    [
        "The 40-ticker table is a planning sensitivity, not the current 80-row prediction-dump design.",
        "The current dump design has 80 rows per year.",
        "This evaluation uses 80 rows per evaluation year.",
        "The current design evaluates 80 tickers.",
    ],
)
def test_current_design_contradiction_guard_rejects_the_reviewed_prose(
    wording: str,
) -> None:
    with pytest.raises(ValueError, match="contradicts the observed current design"):
        excess.validate_no_current_design_row_contradiction(wording)


def test_power_report_json_and_markdown_agree() -> None:
    report = _committed_report()
    markdown_path = excess.OUTPUT_DIR / "significance_report.md"
    if not markdown_path.is_file():
        pytest.skip("generate with make research-excess")
    markdown = markdown_path.read_text(encoding="utf-8")

    # The production cross-check, run against the committed pair.
    excess.validate_power_design_consistency(
        report, markdown, {2023: 40, 2024: 40, 2025: 40}
    )

    for view in report["power_analysis"]["current_design"]["views"]:
        assert (
            f"| {view['view_id']} | {view['n_per_split']} | {view['split_count']} |"
            in markdown
        )
    for entry in report["power_analysis"]["hypothetical_planning_sensitivities"][
        "entries"
    ]:
        assert (
            f"| {entry['additional_test_years']} | {entry['total_test_years']} | "
            f"{entry['planning_rows_per_year']} |" in markdown
        )
    for limitation in report["power_analysis"]["limitations"]:
        assert f"- {limitation}" in markdown


def test_power_consistency_check_rejects_a_drifting_design() -> None:
    report = _committed_report()
    markdown = (excess.OUTPUT_DIR / "significance_report.md").read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="does not match the persisted dumps"):
        excess.validate_power_design_consistency(
            report, markdown, {2023: 80, 2024: 80, 2025: 80}
        )


def test_power_report_keeps_the_low_power_non_rejection_boundary() -> None:
    report = _committed_report()
    power = report["power_analysis"]
    interpretation = power["non_rejection_interpretation"].lower()
    assert "low-power non-rejection" in interpretation
    assert "does not establish that the true ic is zero" in interpretation
    assert any(
        "low-power non-rejection" in limitation.lower()
        for limitation in power["limitations"]
    )
    assert any(
        "practical investment relevance" in limitation.lower()
        for limitation in power["limitations"]
    )
    assert "not evaluated by this calculation" in power["definitions"]["practical_relevance"]


# ---------------------------------------------------------------------------
# 8. protected artifacts
# ---------------------------------------------------------------------------


def test_protected_artifacts_are_byte_identical_across_regeneration(
    isolated_regeneration: dict,
) -> None:
    before = isolated_regeneration["protected_before"]
    after = isolated_regeneration["protected_after"]
    assert isolated_regeneration["protected_count"] == 351
    changed = sorted(path for path in before if before[path] != after.get(path))
    assert changed == []
    assert set(before) == set(after)


# ---------------------------------------------------------------------------
# 9. determinism
# ---------------------------------------------------------------------------


def test_same_environment_regeneration_is_byte_identical(
    isolated_regeneration: dict,
) -> None:
    first = isolated_regeneration["first"]
    second = isolated_regeneration["second"]
    assert set(first) == set(second)
    differing = sorted(name for name in first if first[name] != second[name])
    assert differing == []


@pytest.mark.parametrize(
    "filename",
    [
        "predictions_test_2023.csv",
        "predictions_test_2024.csv",
        "predictions_test_2025.csv",
        "leaderboard.csv",
    ],
)
def test_prediction_dumps_and_leaderboard_are_byte_identical_to_the_committed_bytes(
    isolated_regeneration: dict, filename: str
) -> None:
    """The corrections touch report metadata only: prediction values do not move."""
    committed = excess.OUTPUT_DIR / filename
    if not committed.is_file():
        pytest.skip("generate with make research-excess")
    assert isolated_regeneration["first"][filename] == committed.read_bytes()


def test_isolated_run_reproduces_the_committed_statistics(
    isolated_regeneration: dict,
) -> None:
    """The isolated rerun must agree numerically with the committed artifacts."""
    committed_path = excess.OUTPUT_DIR / "significance_report.json"
    if not committed_path.is_file():
        pytest.skip("generate with make research-excess")
    committed = json.loads(committed_path.read_text(encoding="utf-8"))
    rerun = json.loads(
        isolated_regeneration["first"]["significance_report.json"].decode("utf-8")
    )

    committed_models = {item["model"]: item["pooled"] for item in committed["models"]}
    rerun_models = {item["model"]: item["pooled"] for item in rerun["models"]}
    assert set(committed_models) == set(rerun_models)
    for model, pooled in committed_models.items():
        other = rerun_models[model]
        assert other["observed_ic"] == pytest.approx(pooled["observed_ic"], abs=1e-12)
        assert other["bootstrap_ci_95"] == pytest.approx(
            pooled["bootstrap_ci_95"], rel=0.0, abs=1e-12
        )
        assert other["permutation_p_value_two_sided"] == pytest.approx(
            pooled["permutation_p_value_two_sided"], abs=1e-12
        )


# ---------------------------------------------------------------------------
# 10. provenance
# ---------------------------------------------------------------------------


def test_environment_provenance_is_recorded() -> None:
    report = _committed_report()
    manifest_path = excess.OUTPUT_DIR / "artifact_manifest.json"
    if not manifest_path.is_file():
        pytest.skip("generate with make research-excess")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for provenance in (report["provenance"], manifest):
        environment = provenance["environment"]
        assert environment["python_version"].startswith("3.")
        assert environment["system"]
        assert environment["platform"]
        assert environment["machine"]
        packages = environment["packages"]
        for package in ("numpy", "pandas", "scipy", "scikit-learn"):
            assert packages[package], package
        assert "not claimed" in environment["determinism"]
        assert "same" in environment["determinism"].lower()


def test_effective_estimator_parameters_match_the_frozen_constructors() -> None:
    report = _committed_report()
    effective = report["provenance"]["effective_estimator_parameters"]
    live = excess.effective_estimator_parameters()

    expected_classes = {
        "linear_regression": "LinearRegression",
        "ridge": "Ridge",
        "lasso": "Lasso",
        "elasticnet": "ElasticNet",
        "random_forest": "RandomForestRegressor",
        "gradient_boosting": "GradientBoostingRegressor",
    }
    for model in excess.FROZEN_ML_FAMILY:
        record = effective[model]
        assert record["estimator_class"] == expected_classes[model]
        assert record["extraction"] == "estimator.get_params(deep=False)"
        assert record["parameters"] == live[model]["parameters"]
        # Every declared hyperparameter must appear with the declared value.
        for key, value in run_experiments.MODEL_CONFIGS[model]["parameters"].items():
            assert record["parameters"][key] == value, (model, key)
        seed = run_experiments.MODEL_CONFIGS[model]["seed"]
        if seed is not None:
            assert record["parameters"]["random_state"] == seed
        else:
            assert record["parameters"].get("random_state") is None
        # Defaults are read from the estimator, not transcribed: the extracted set
        # is strictly larger than the declared subset.
        assert len(record["parameters"]) > len(
            run_experiments.MODEL_CONFIGS[model]["parameters"]
        )

    for baseline in excess.FROZEN_BASELINES:
        assert effective[baseline]["estimator_class"] is None
        assert effective[baseline]["parameters"] == {}


def test_provenance_records_seeds_splits_features_and_schemas() -> None:
    report = _committed_report()
    provenance = report["provenance"]

    assert provenance["target"] == excess.TARGET_COLUMN
    assert provenance["walk_forward_splits"] == run_experiments.SPLITS
    assert provenance["model_specifications"] == run_experiments.MODEL_CONFIGS
    assert provenance["model_family_membership"]["ml_family"] == list(
        excess.FROZEN_ML_FAMILY
    )
    assert provenance["model_family_membership"]["baselines_outside_family"] == list(
        excess.FROZEN_BASELINES
    )
    seeds = provenance["seeds"]
    assert seeds["significance_seed"] == significance.DEFAULT_SEED
    assert seeds["bootstrap_seed"] == significance.DEFAULT_SEED
    assert seeds["permutation_seed"] == significance.DEFAULT_SEED
    assert seeds["model_seeds"]["random_forest"] == 42
    assert seeds["model_seeds"]["gradient_boosting"] == 42

    resampling = provenance["resampling"]
    assert resampling["permutations"] == significance.DEFAULT_PERMUTATIONS
    assert resampling["bootstraps"] == significance.DEFAULT_BOOTSTRAPS
    assert resampling["bootstrap_unit"] == "ticker_cluster"
    assert resampling["bootstrap_cluster_key"] == "ticker"

    features = provenance["feature_columns"]
    assert features["count"] == len(features["columns"])
    assert features["count"] > 0
    recomputed = hashlib.sha256("\n".join(features["columns"]).encode("utf-8")).hexdigest()
    assert features["sha256"] == recomputed

    schemas = provenance["schema_versions"]
    assert schemas["prediction_csv"]["version"] == excess.PREDICTION_CSV_SCHEMA_VERSION
    assert schemas["prediction_csv"]["columns"] == significance.REQUIRED_COLUMNS
    assert schemas["leaderboard_csv"]["version"] == excess.LEADERBOARD_CSV_SCHEMA_VERSION
    assert schemas["significance_report_json"]["version"] == report["schema_version"]


def test_generated_json_is_strictly_valid_and_deterministically_ordered() -> None:
    for filename in ("significance_report.json", "artifact_manifest.json"):
        path = excess.OUTPUT_DIR / filename
        if not path.is_file():
            pytest.skip("generate with make research-excess")
        text = path.read_text(encoding="utf-8")
        assert "NaN" not in text and "Infinity" not in text
        payload = json.loads(text)
        assert text == json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"


# ---------------------------------------------------------------------------
# claim safety and cohort labelling
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "unsafe",
    [
        "We found a signal vs the benchmark.",
        "There is signal against the BIST100 benchmark.",
        "The model beats the benchmark.",
        "Gradient boosting outperformed the BIST100.",
        "A benchmark-beating result.",
        "Alpha was captured in the excess-return evaluation.",
        "We found a signal.",
        "This establishes a reliable predictive edge.",
        "The conversion creates investment value.",
        "This predicts future returns.",
        "A market-beating result.",
    ],
)
def test_claim_safety_rejects_adversarial_excess_interpretations(unsafe: str) -> None:
    with pytest.raises(ValueError, match="Unsafe"):
        excess.validate_excess_claim_safety_text(unsafe)


def test_claim_safety_allows_required_boundary() -> None:
    excess.validate_excess_claim_safety_text(
        "This excess-return-basis evaluation is a descriptive historical research "
        "result; it does not establish signal, investment value, or a reliable "
        "predictive edge."
    )


def test_cohort_is_labelled_as_the_benchmark_covered_public_40() -> None:
    report = _committed_report()
    basis = report["target_basis"]
    assert basis["cohort"] == "benchmark-covered public 40"
    assert "public" in basis["cohort_note"].lower()
    assert basis["evaluated_rows_per_year"] == {"2023": 40, "2024": 40, "2025": 40}

    markdown_path = excess.OUTPUT_DIR / "significance_report.md"
    if not markdown_path.is_file():
        pytest.skip("generate with make research-excess")
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "benchmark-covered public 40" in markdown
    assert not re.search(
        r"per model and split from the internal training universe", markdown
    )
    assert any(
        limitation.startswith("The evaluated cohort is the benchmark-covered public 40")
        for limitation in report["limitations"]
    )


def test_generated_artifacts_are_isolated_complete_and_claim_safe() -> None:
    report_path = excess.OUTPUT_DIR / "significance_report.json"
    manifest_path = excess.OUTPUT_DIR / "artifact_manifest.json"
    if not report_path.is_file() or not manifest_path.is_file():
        pytest.skip("generate with make research-excess")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert report["task"] == manifest["task"] == "R3-TGT-01"
    assert report["target_basis"]["target_column"] == excess.TARGET_COLUMN
    assert manifest["target"] == excess.TARGET_COLUMN
    assert manifest["generator"] == excess.GENERATOR
    assert manifest["regeneration_command"] == excess.REGENERATION_COMMAND
    assert manifest["seeds"]["significance_seed"] == significance.DEFAULT_SEED
    assert manifest["model_specifications"] == run_experiments.MODEL_CONFIGS
    assert manifest["walk_forward_splits"] == run_experiments.SPLITS

    expected_outputs = {
        "experiments/results_excess/artifact_manifest.json",
        "experiments/results_excess/leaderboard.csv",
        "experiments/results_excess/predictions_test_2023.csv",
        "experiments/results_excess/predictions_test_2024.csv",
        "experiments/results_excess/predictions_test_2025.csv",
        "experiments/results_excess/significance_report.json",
        "experiments/results_excess/significance_report.md",
    }
    recorded_outputs = {item["path"] for item in manifest["artifacts"]}
    recorded_outputs.add(manifest["manifest_self_record"]["path"])
    assert recorded_outputs == expected_outputs
    for artifact in manifest["artifacts"]:
        path = excess.ROOT / artifact["path"]
        assert path.is_file()
        assert artifact["sha256"] == _sha256(path)

    for source in report["source_artifacts"]:
        assert (excess.ROOT / source["path"]).is_file()
        assert source["sha256"] == _sha256(excess.ROOT / source["path"])

    comparison = report["analysis"]["aggregate_leaderboard_reconstruction"]
    assert comparison["status"] == "match"
    assert comparison["mismatches"] == []
    assert comparison["reconstructed_rows"] == comparison["existing_rows"] == 27

    assert report["analysis"]["evaluated_tickers_per_model_split"] == [40]
    for model in report["models"]:
        assert "permutation_p_value_two_sided" in model["pooled"]
        assert "bonferroni_adjusted_p_value" in model["pooled"]
        if model["kind"] == "ml":
            assert model["pooled"]["bonferroni_adjusted_p_value"] is not None
            assert model["pooled"]["significant_fwer_0_05"] is not None

    claim_safety = report["claim_safety"]
    assert claim_safety["descriptive_research_evidence_only"] is True
    assert claim_safety["investment_value_established"] is False
    assert claim_safety["reliable_predictive_edge_established"] is False
    assert claim_safety["benchmark_relative_signal_established"] is False

    markdown = (excess.OUTPUT_DIR / "significance_report.md").read_text(encoding="utf-8")
    excess.validate_excess_claim_safety_text(markdown)
    assert "not investment value or investment advice" in markdown
    assert (
        "does not establish signal, investment value, or a reliable predictive edge"
        in markdown
    )
    assert "The nominal TRY evaluation remains the canonical headline" in markdown


# ---------------------------------------------------------------------------
# 12. human-review corrections: estimand, dual permutation, disclosures
#
# These tests validate the underlying evidence rather than the prose that
# reports it: each disclosure is checked against an independent recomputation
# from the trusted dataset or the persisted dumps.
# ---------------------------------------------------------------------------


def _trusted_targets() -> pd.DataFrame:
    """Trusted nominal, benchmark, and excess targets keyed by ticker and target year."""
    modeling = pd.read_csv(run_experiments._modeling_csv())
    columns = [
        "ticker",
        "target_year",
        "next_year_return_pct",
        "next_year_bist100_return_pct",
        excess.TARGET_COLUMN,
    ]
    return modeling[columns].copy()


def _shared_mapping_null(
    frame: pd.DataFrame,
    model: str,
    mappings_by_year: dict[int, np.ndarray],
) -> np.ndarray:
    """Equal-year pooled null ICs for explicit per-year mappings, computed here.

    Passing the same array for every year reproduces the trajectory-preserving
    contract; passing different arrays reproduces the per-year procedure that the
    contract forbids.
    """
    rows = frame[frame["model"].eq(model)]
    tickers = sorted(rows["ticker"].unique().tolist())
    per_year = []
    for year in sorted(mappings_by_year):
        group = rows[rows["year"].eq(year)].set_index("ticker").reindex(tickers)
        y_true = group["y_true"].to_numpy(dtype=float)
        y_pred = group["y_pred"].to_numpy(dtype=float)
        mapping = mappings_by_year[year]
        permuted_true = y_true[mapping]
        repeated_pred = np.broadcast_to(y_pred, permuted_true.shape)
        per_year.append(_rowwise_spearman(permuted_true, repeated_pred))
    return np.nanmean(np.vstack(per_year), axis=0)


def _independent_sensitivity_p_value(
    frame: pd.DataFrame,
    model: str,
    *,
    seed: int = excess.TRAJECTORY_SENSITIVITY_SEED,
    draws: int = excess.TRAJECTORY_SENSITIVITY_DRAWS,
) -> tuple[float, int, float]:
    """Recompute the sensitivity p-value without calling the production helper."""
    rows = frame[frame["model"].eq(model)]
    tickers = sorted(rows["ticker"].unique().tolist())
    years = sorted(int(year) for year in rows["year"].unique())
    rng = np.random.default_rng(seed)
    mapping = np.argsort(rng.random((draws, len(tickers))), axis=1)

    observed_parts = []
    per_year = []
    for year in years:
        group = rows[rows["year"].eq(year)].set_index("ticker").reindex(tickers)
        y_true = group["y_true"].to_numpy(dtype=float)
        y_pred = group["y_pred"].to_numpy(dtype=float)
        observed_parts.append(
            float(_rowwise_spearman(y_true[np.newaxis, :], y_pred[np.newaxis, :])[0])
        )
        permuted_true = y_true[mapping]
        repeated_pred = np.broadcast_to(y_pred, permuted_true.shape)
        per_year.append(_rowwise_spearman(permuted_true, repeated_pred))

    observed = float(np.mean(observed_parts))
    pooled = np.nanmean(np.vstack(per_year), axis=0)
    finite = pooled[np.isfinite(pooled)]
    extreme = int(np.sum(np.abs(finite) >= abs(observed)))
    return float((extreme + 1) / (len(finite) + 1)), extreme, observed


# --- 1. per-year nominal and excess ranks are identical ---------------------


def test_per_year_nominal_and_excess_target_ranks_are_identical() -> None:
    """Recomputed from the trusted dataset, not read back from the audit."""
    frame = _load_committed_dumps()
    trusted = _trusted_targets()

    total_mismatches = 0
    checked_years = []
    for year, group in frame[frame["model"].eq("ridge")].groupby("year", sort=True):
        merged = group[["ticker", "year", "y_true"]].merge(
            trusted, left_on=["ticker", "year"], right_on=["ticker", "target_year"]
        )
        assert len(merged) == len(group)
        nominal = merged["next_year_return_pct"].to_numpy(dtype=float)
        excess_target = merged["y_true"].to_numpy(dtype=float)
        # The subtrahend really is one common value inside the year.
        implied = nominal - excess_target
        assert float(np.max(implied) - np.min(implied)) <= 1e-9
        assert implied.mean() == pytest.approx(
            float(merged["next_year_bist100_return_pct"].mean()), abs=1e-9
        )
        mismatches = int(
            np.sum(rankdata(nominal) != rankdata(excess_target))
        )
        total_mismatches += mismatches
        checked_years.append(int(year))
        assert mismatches == 0

    assert checked_years == list(excess.EXPECTED_EVALUATION_YEARS)
    assert total_mismatches == 0

    audit = _committed_report()["estimand_invariance_audit"]
    assert audit["evaluated_years"] == checked_years
    assert audit["total_rank_mismatch_count"] == total_mismatches
    assert [entry["rank_mismatch_count"] for entry in audit["per_year"]] == [0, 0, 0]
    # The nominal column is traced, not assumed.
    assert audit["nominal_target_column"] == run_experiments.TARGETS[0]
    assert audit["excess_target_column"] == excess.TARGET_COLUMN
    assert audit["derivation_traced_not_assumed"] is True


def test_estimand_audit_fails_when_rank_invariance_is_broken() -> None:
    """A non-common subtrahend must fail the run rather than be reported."""
    frame = _load_committed_dumps()
    broken = frame.copy()
    # Perturb one realized outcome so nominal - excess is no longer constant.
    target = broken.index[broken["year"].eq(2024)][0]
    broken.loc[target, "y_true"] = float(broken.loc[target, "y_true"]) + 25.0
    with pytest.raises(excess.ExcessEstimandError):
        excess.build_estimand_invariance_audit(broken)


def test_nominal_target_column_is_resolved_from_repository_authority() -> None:
    authority = excess.resolve_nominal_target_column()
    assert authority["nominal_target_column"] == run_experiments.TARGETS[0]
    assert authority["benchmark_column"] == "next_year_bist100_return_pct"
    source = (excess.ROOT / excess.EXCESS_DERIVATION_AUTHORITY).read_text(encoding="utf-8")
    minuend = authority["nominal_target_column"]
    subtrahend = authority["benchmark_column"]
    assert f'df["{minuend}"] - df["{subtrahend}"]' in source


# --- 2 and 3. estimand is ordinal; alpha/magnitude/value are rejected -------


def test_report_describes_the_estimand_as_ordinal_ranking() -> None:
    report = _committed_report()
    audit = report["estimand_invariance_audit"]
    assert audit["estimand"] == "within-year ordinal cross-sectional ranking"
    assert audit["evaluates_ordinal_cross_sectional_ranking"] is True
    assert audit["benchmark_subtraction_may_affect_fitting"] is True
    assert audit["benchmark_subtraction_alters_within_year_evaluation_ranks"] is False
    assert report["claim_safety"]["estimand"] == "within-year ordinal cross-sectional ranking"

    markdown = (excess.OUTPUT_DIR / "significance_report.md").read_text(encoding="utf-8")
    assert "## Estimand: within-year ordinal ranking" in markdown
    assert audit["fitting_effect_note"] in markdown


def test_alpha_magnitude_and_investment_value_interpretations_are_rejected() -> None:
    report = _committed_report()
    audit = report["estimand_invariance_audit"]
    assert audit["evaluates_benchmark_relative_magnitude_accuracy"] is False
    assert audit["estimates_alpha"] is False
    assert audit["estimates_economic_outperformance"] is False
    assert audit["establishes_investment_value"] is False
    assert audit["represents_a_tradable_strategy"] is False
    claim_safety = report["claim_safety"]
    assert claim_safety["alpha_estimated"] is False
    assert claim_safety["benchmark_relative_magnitude_accuracy_evaluated"] is False
    assert claim_safety["tradable_strategy_established"] is False

    # The guard is behavioural: these upgrades are refused, and the published
    # text passes the same guard.
    for unsafe in (
        "This IC estimates alpha on the excess basis.",
        "The model measures benchmark-relative magnitude accuracy.",
        "A tradable strategy was established on this basis.",
        "This establishes an inverse alpha for the tree models.",
    ):
        with pytest.raises(ValueError, match="Unsafe"):
            excess.validate_excess_claim_safety_text(unsafe)
    markdown = (excess.OUTPUT_DIR / "significance_report.md").read_text(encoding="utf-8")
    excess.validate_excess_claim_safety_text(markdown)


# --- 4. the original permutation is preserved unchanged --------------------


def test_original_within_year_permutation_values_are_unchanged() -> None:
    """Recompute the prespecified analysis and match the persisted values exactly."""
    frame = _load_committed_dumps()
    report = _committed_report()
    by_name = {result["model"]: result["pooled"] for result in report["models"]}

    for model in excess.FROZEN_ML_FAMILY:
        recomputed = significance.analyze_model(
            frame[frame["model"].eq(model)],
            permutations=significance.DEFAULT_PERMUTATIONS,
            bootstraps=significance.DEFAULT_BOOTSTRAPS,
            seed=significance.DEFAULT_SEED,
        )["pooled"]
        pooled = by_name[model]
        assert pooled["observed_ic"] == recomputed["observed_ic"]
        assert (
            pooled["permutation_p_value_two_sided"]
            == recomputed["permutation_p_value_two_sided"]
        )
        assert pooled["observed_null_percentile"] == recomputed["observed_null_percentile"]
        # The sensitivity is a separate block; it never overwrites these fields.
        assert (
            pooled["trajectory_preserving_sensitivity"]["permutation_p_value_two_sided"]
            != pooled["permutation_p_value_two_sided"]
        )

    primary = report["analysis"]["primary_permutation"]
    assert primary["analysis_id"] == excess.PRIMARY_PERMUTATION_ID
    assert primary["prespecified"] is True
    assert primary["unchanged_by_human_review"] is True
    assert primary["independent_per_year_permutation"] is True
    assert primary["renamed_or_replaced_by_the_sensitivity"] is False
    assert primary["draws"] == 10_000
    assert primary["seed"] == significance.DEFAULT_SEED
    assert primary["two_sided"] is True
    assert primary["monte_carlo_correction"] == "(extreme_count + 1) / (draw_count + 1)"
    assert primary["family_size"] == 6
    assert primary["null_hypothesis"] == excess.PRIMARY_PERMUTATION_NULL
    assert "each year permuted independently" in primary["null_hypothesis"]
    # The prespecified analysis keeps its own identity in the report body.
    assert report["analysis"]["permutation"].startswith("two-sided")


# --- 5, 6, 7. the trajectory-preserving contract ---------------------------


def test_sensitivity_uses_one_identical_mapping_across_every_year() -> None:
    frame = _clustered_fixture()
    tickers = sorted(frame["ticker"].unique().tolist())
    mapping = excess.trajectory_permutation_matrix(len(tickers), 64, seed=7)

    result = excess.trajectory_preserving_permutation(frame, permutation_matrix=mapping)
    shared = _shared_mapping_null(frame, "ridge", {year: mapping for year in (2023, 2024, 2025)})
    assert np.allclose(result["pooled_null_distribution"], shared, equal_nan=True)

    # A different mapping in even one year is a different analysis.
    other = excess.trajectory_permutation_matrix(len(tickers), 64, seed=11)
    per_year = {2023: mapping, 2024: other, 2025: mapping}
    assert not np.allclose(
        result["pooled_null_distribution"],
        _shared_mapping_null(frame, "ridge", per_year),
        equal_nan=True,
    )


def test_complete_outcome_trajectories_move_together() -> None:
    """Each destination slot draws from the same source ticker in every year."""
    frame = _clustered_fixture()
    tickers = sorted(frame["ticker"].unique().tolist())
    mapping = excess.trajectory_permutation_matrix(len(tickers), 8, seed=3)

    original = {}
    permuted = {}
    for year in (2023, 2024, 2025):
        group = (
            frame[frame["year"].eq(year)].set_index("ticker").reindex(tickers)
        )
        values = group["y_true"].to_numpy(dtype=float)
        original[year] = values
        permuted[year] = excess.apply_trajectory_permutation(values, mapping)

    for draw in range(mapping.shape[0]):
        for slot, source in enumerate(mapping[draw]):
            # The whole trajectory of one source ticker lands in one slot.
            moved = [permuted[year][draw][slot] for year in (2023, 2024, 2025)]
            expected = [original[year][source] for year in (2023, 2024, 2025)]
            assert moved == expected
        # Nothing is dropped or duplicated: it is a permutation, not a bootstrap.
        assert sorted(mapping[draw].tolist()) == list(range(len(tickers)))


def test_independent_per_year_mappings_cannot_satisfy_the_sensitivity_contract() -> None:
    frame = _clustered_fixture()
    tickers = sorted(frame["ticker"].unique().tolist())
    draws = 256

    # A per-year mapping array is refused outright.
    per_year_matrix = np.stack(
        [excess.trajectory_permutation_matrix(len(tickers), draws, seed=seed) for seed in (1, 2, 3)],
        axis=1,
    )
    assert per_year_matrix.ndim == 3
    with pytest.raises(excess.ExcessPermutationError, match="per-year permutation mapping"):
        excess.trajectory_preserving_permutation(frame, permutation_matrix=per_year_matrix)

    # And independently generated per-year mappings produce different behaviour,
    # so they could not silently stand in for the shared mapping either.
    shared = excess.trajectory_permutation_matrix(len(tickers), draws, seed=5)
    result = excess.trajectory_preserving_permutation(frame, permutation_matrix=shared)
    independent = {
        year: excess.trajectory_permutation_matrix(len(tickers), draws, seed=seed)
        for year, seed in zip((2023, 2024, 2025), (5, 6, 7))
    }
    independent_null = _shared_mapping_null(frame, "ridge", independent)
    shared_null = result["pooled_null_distribution"]
    assert float(np.nanstd(shared_null)) > float(np.nanstd(independent_null))
    assert not np.allclose(shared_null, independent_null, equal_nan=True)


def test_sensitivity_refuses_a_mapping_with_duplicates() -> None:
    frame = _clustered_fixture()
    tickers = sorted(frame["ticker"].unique().tolist())
    duplicated = np.zeros((4, len(tickers)), dtype=int)
    with pytest.raises(excess.ExcessPermutationError, match="duplicate-free"):
        excess.trajectory_preserving_permutation(frame, permutation_matrix=duplicated)


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda f: f[f["year"].ne(2024)], "expects evaluation years"),
        (lambda f: pd.concat([f, f.iloc[[0]]], ignore_index=True), "duplicate ticker/year"),
        (lambda f: f.iloc[1:], "inconsistent ticker coverage"),
        (lambda f: f.head(6), "expects evaluation years"),
    ],
)
def test_sensitivity_refuses_malformed_panels(mutate, reason: str) -> None:
    """Panel refusals raise the permutation exception, not a bare ValueError."""
    with pytest.raises(excess.ExcessPermutationError, match=reason) as error:
        excess.trajectory_preserving_permutation(mutate(_clustered_fixture()))
    assert isinstance(error.value, excess.ExcessPanelError)
    assert not isinstance(error.value, excess.ExcessBootstrapError)


def test_sensitivity_refuses_non_finite_and_malformed_keys() -> None:
    frame = _clustered_fixture()
    broken = frame.copy()
    broken.loc[0, "y_true"] = np.inf
    with pytest.raises(excess.ExcessPermutationError, match="non-finite"):
        excess.trajectory_preserving_permutation(broken)

    bad_year = frame.copy()
    bad_year["year"] = bad_year["year"].astype(object)
    bad_year.loc[0, "year"] = 2023.5
    with pytest.raises(excess.ExcessPermutationError, match="fractional year"):
        excess.trajectory_preserving_permutation(bad_year)

    bad_ticker = frame.copy()
    bad_ticker["ticker"] = bad_ticker["ticker"].astype(object)
    bad_ticker.loc[0, "ticker"] = " T00"
    with pytest.raises(excess.ExcessPermutationError, match="whitespace"):
        excess.trajectory_preserving_permutation(bad_ticker)


def test_sensitivity_refuses_insufficient_tickers() -> None:
    frame = _clustered_fixture()
    kept = frame[frame["ticker"].isin(["T00", "T01"])]
    with pytest.raises(excess.ExcessPermutationError, match="at least"):
        excess.trajectory_preserving_permutation(kept)


# --- 8 and 9. Monte Carlo formula and independent Bonferroni ---------------


def test_sensitivity_p_value_uses_the_monte_carlo_formula() -> None:
    frame = _load_committed_dumps()
    report = _committed_report()
    by_name = {result["model"]: result["pooled"] for result in report["models"]}

    for model in excess.FROZEN_ML_FAMILY:
        expected_p, extreme, observed = _independent_sensitivity_p_value(frame, model)
        block = by_name[model]["trajectory_preserving_sensitivity"]
        assert block["permutation_p_value_two_sided"] == pytest.approx(expected_p, abs=1e-15)
        assert block["extreme_count"] == extreme
        assert block["observed_ic"] == pytest.approx(observed, abs=1e-12)
        # The persisted numbers satisfy the stated formula on their own terms.
        assert block["p_value_formula"] == "(extreme_count + 1) / (draw_count + 1)"
        assert block["valid_draws"] == 10_000
        assert block["p_value_denominator"] == block["valid_draws"] + 1
        assert block["permutation_p_value_two_sided"] == (
            (block["extreme_count"] + 1) / block["p_value_denominator"]
        )
        assert block["is_bootstrap"] is False
        assert block["duplicate_free_one_to_one_mapping"] is True


def test_six_model_bonferroni_is_applied_independently_to_both_analyses() -> None:
    report = _committed_report()
    by_name = {result["model"]: result["pooled"] for result in report["models"]}
    family_size = len(excess.FROZEN_ML_FAMILY)
    assert family_size == 6

    for model in excess.FROZEN_ML_FAMILY:
        pooled = by_name[model]
        block = pooled["trajectory_preserving_sensitivity"]
        assert pooled["bonferroni_adjusted_p_value"] == pytest.approx(
            min(1.0, pooled["permutation_p_value_two_sided"] * family_size)
        )
        assert block["bonferroni_adjusted_p_value"] == pytest.approx(
            min(1.0, block["permutation_p_value_two_sided"] * family_size)
        )
        # Two adjustments, each from its own raw p-value.
        assert block["significant_fwer_0_05"] is (
            block["bonferroni_adjusted_p_value"] < 0.05
        )
        assert pooled["significant_fwer_0_05"] is (
            pooled["bonferroni_adjusted_p_value"] < 0.05
        )

    for model in excess.FROZEN_BASELINES:
        block = by_name[model]["trajectory_preserving_sensitivity"]
        assert block["bonferroni_adjusted_p_value"] is None
        assert block["significant_fwer_0_05"] is None

    conclusion = report["family_conclusion"]
    comparison = report["significance_comparison"]
    # The conclusion is computed from the adjusted p-values, not assumed.
    expected_primary = sorted(
        model
        for model in excess.FROZEN_ML_FAMILY
        if by_name[model]["bonferroni_adjusted_p_value"] < 0.05
    )
    expected_sensitivity = sorted(
        model
        for model in excess.FROZEN_ML_FAMILY
        if by_name[model]["trajectory_preserving_sensitivity"]["bonferroni_adjusted_p_value"]
        < 0.05
    )
    assert conclusion["models_surviving_family_wise_correction"] == expected_primary
    assert (
        conclusion["models_surviving_sensitivity_family_wise_correction"]
        == expected_sensitivity
    )
    assert comparison["models_rejecting_under_either_after_correction"] == sorted(
        set(expected_primary) | set(expected_sensitivity)
    )


# --- 4 (reporting) and 10. symmetric side-by-side, labelled post-review -----


def test_every_family_member_is_reported_symmetrically_for_both_analyses() -> None:
    report = _committed_report()
    comparison = report["significance_comparison"]
    rows = comparison["family"]
    assert [row["model"] for row in rows] == list(excess.FROZEN_ML_FAMILY)

    required = set(comparison["fields_reported_for_every_member"])
    assert required == {
        "pooled_equal_year_ic",
        "primary_raw_permutation_p",
        "primary_bonferroni_p",
        "sensitivity_raw_permutation_p",
        "sensitivity_bonferroni_p",
        "ticker_cluster_bootstrap_ci_95",
        "either_family_corrected_analysis_rejects_fwer_0_05",
    }
    schemas = {frozenset(row) for row in rows}
    assert len(schemas) == 1
    for row in rows:
        assert required <= set(row)
        for field in required:
            assert row[field] is not None
        assert row["either_family_corrected_analysis_rejects_fwer_0_05"] is (
            row["primary_rejects_fwer_0_05"] or row["sensitivity_rejects_fwer_0_05"]
        )

    # Baselines stay separate and outside the corrected family.
    baselines = comparison["baselines_outside_the_corrected_family"]["rows"]
    assert [row["model"] for row in baselines] == list(excess.FROZEN_BASELINES)
    for row in baselines:
        assert row["inside_corrected_family"] is False
        assert row["bonferroni_adjusted"] is False
        assert "sensitivity_bonferroni_p" not in row

    markdown = (excess.OUTPUT_DIR / "significance_report.md").read_text(encoding="utf-8")
    family_table = markdown[
        markdown.index("## Prespecified six-model ML family") : markdown.index(
            "## Non-family baselines"
        )
    ]
    assert "Sensitivity permutation p (raw)" in family_table
    assert "Sensitivity Bonferroni-adjusted p" in family_table
    assert "Either corrected analysis rejects at FWER 0.05" in family_table
    ordered = [
        line.split("|")[1].strip()
        for line in family_table.splitlines()
        if line.startswith("| ") and line.split("|")[1].strip() in excess.FROZEN_ML_FAMILY
    ]
    assert ordered == list(excess.FROZEN_ML_FAMILY)


def test_sensitivity_is_labelled_post_review_and_non_prespecified() -> None:
    report = _committed_report()
    section = report["analysis"]["trajectory_preserving_sensitivity"]
    assert section["analysis_id"] == excess.TRAJECTORY_SENSITIVITY_ID
    assert section["status"] == "post_review_sensitivity"
    assert section["prespecified"] is False
    assert section["added_after_human_review"] is True
    assert section["replaces_primary_analysis"] is False
    assert section["shared_mapping_across_years"] is True
    assert section["independent_per_year_mapping"] is False
    assert section["prediction_rows_fixed"] is True
    assert section["seed_frozen_and_documented"] is True
    assert section["seed"] == excess.TRAJECTORY_SENSITIVITY_SEED
    assert section["requested_draws"] == 10_000
    assert len(section["algorithm"]) == 11
    for refused in (
        "ragged ticker coverage",
        "missing years",
        "duplicate ticker/year rows",
        "malformed ticker or year values",
        "unequal ticker sets across years",
        "non-finite targets or predictions",
        "insufficient tickers",
        "insufficient valid permutation draws",
    ):
        assert refused in section["refused_inputs"]

    comparison = report["significance_comparison"]
    assert comparison["sensitivity_is_prespecified"] is False
    assert comparison["sensitivity_replaces_primary"] is False
    assert report["family_conclusion"]["sensitivity_is_prespecified"] is False

    markdown = (excess.OUTPUT_DIR / "significance_report.md").read_text(encoding="utf-8")
    assert excess.TRAJECTORY_SENSITIVITY_PROVENANCE in markdown
    assert "not a prespecified analysis" in markdown


# --- 11. no model selection field or semantic alias ------------------------


_SELECTION_ALIASES = {
    "selected_model",
    "headline_model",
    "best_model",
    "strongest_model",
    "winning_model",
    "winner",
    "most_significant_model",
    "headline",
    "top_model",
    "chosen_model",
    "preferred_model",
    "champion_model",
    "leading_model",
    "min_p_model",
    "minimum_p_model",
    "smallest_p_model",
    "model_rank",
    "model_ranking",
    "recommended_model",
}


@pytest.mark.parametrize(
    "filename", ["significance_report.json", "artifact_manifest.json"]
)
def test_no_model_selection_field_or_semantic_alias_exists(filename: str) -> None:
    path = excess.OUTPUT_DIR / filename
    if not path.is_file():
        pytest.skip("generate with make research-excess")
    payload = json.loads(path.read_text(encoding="utf-8"))
    keys = {key.lower() for key in _collect_keys(payload)}
    assert keys & _SELECTION_ALIASES == set()
    excess.assert_no_selection_keys(payload)

    # No scalar field names a single family member. Model names may appear as
    # dictionary *keys* of per-model maps and as list entries of the frozen
    # order; what is forbidden is a scalar that elects one member.
    allowed_scalar_keys = {"model"}

    def _assert_no_scalar_elects_a_model(payload: object, path: str = "$") -> None:
        if isinstance(payload, dict):
            for key, value in payload.items():
                if (
                    isinstance(value, str)
                    and value in set(excess.FROZEN_ML_FAMILY)
                    and str(key) not in allowed_scalar_keys
                ):
                    raise AssertionError(f"{path}.{key} elects a single model: {value}")
                _assert_no_scalar_elects_a_model(value, f"{path}.{key}")
        elif isinstance(payload, list):
            for index, value in enumerate(payload):
                _assert_no_scalar_elects_a_model(value, f"{path}[{index}]")

    _assert_no_scalar_elects_a_model(payload)

    # The guard is real: a reintroduced winner field is caught.
    with pytest.raises(AssertionError, match="elects a single model"):
        _assert_no_scalar_elects_a_model({"leader": excess.FROZEN_ML_FAMILY[0]})

    if filename == "significance_report.json":
        comparison = payload["significance_comparison"]
        assert comparison["selection_performed"] is False
        # Frozen order, not an order induced by any observed statistic.
        assert [row["model"] for row in comparison["family"]] == list(
            excess.FROZEN_ML_FAMILY
        )
        by_p = sorted(
            comparison["family"], key=lambda row: row["sensitivity_raw_permutation_p"]
        )
        assert [row["model"] for row in by_p] != list(excess.FROZEN_ML_FAMILY)


def test_markdown_carries_no_selection_language_after_the_corrections() -> None:
    markdown = (excess.OUTPUT_DIR / "significance_report.md").read_text(encoding="utf-8")
    excess.validate_no_selection_language(markdown)
    for wording in ("strongest model", "best model", "headline model", "winning model"):
        assert wording not in markdown.lower()


# --- 12. cross-basis multiplicity ------------------------------------------


def test_cross_basis_exploratory_confirmatory_disclosure_is_present() -> None:
    report = _committed_report()
    disclosure = report["cross_basis_multiplicity"]
    assert disclosure["confirmatory_family"]["basis_id"] == "nominal_try_return"
    assert disclosure["confirmatory_family"]["target_column"] == "next_year_return_pct"
    assert disclosure["confirmatory_family"]["target_column"] == run_experiments.TARGETS[0]

    exploratory = {basis["basis_id"] for basis in disclosure["exploratory_bases"]}
    assert {"real_try_return", "usd_return", excess.BASIS_ID} <= exploratory
    assert "nominal_try_return" not in exploratory
    assert disclosure["this_basis_role"] == "exploratory robustness evaluation"
    assert disclosure["controls_multiplicity_across_target_bases"] is False
    assert disclosure["cross_basis_correction_prespecified"] is False
    assert disclosure["nominal_artifacts_altered"] is False
    assert "must not be described as confirmatory" in disclosure["future_result_policy"]
    assert report["claim_safety"]["cross_basis_multiplicity_controlled"] is False

    # The within-basis correction is exactly the frozen six-model family.
    within = disclosure["within_basis_correction"]
    assert within["family"] == list(excess.FROZEN_ML_FAMILY)
    assert within["family_size"] == 6

    markdown = (excess.OUTPUT_DIR / "significance_report.md").read_text(encoding="utf-8")
    assert "## Cross-basis multiplicity" in markdown
    assert disclosure["statement"] in markdown
    assert disclosure["future_result_policy"] in markdown
    assert excess.CROSS_BASIS_LIMITATION in report["limitations"]


# --- 13. coincident baselines ---------------------------------------------


def test_duplicate_baseline_wording_matches_the_persisted_equality_level() -> None:
    """Independently establish how far the two baselines coincide, then check wording."""
    frame = _load_committed_dumps()
    left_name, right_name = excess.COINCIDENT_BASELINE_CANDIDATES
    left = frame[frame["model"].eq(left_name)].sort_values(["year", "ticker"])
    right = frame[frame["model"].eq(right_name)].sort_values(["year", "ticker"])
    assert left["ticker"].tolist() == right["ticker"].tolist()

    left_pred = left["y_pred"].to_numpy(dtype=float)
    right_pred = right["y_pred"].to_numpy(dtype=float)
    values_identical = bool(np.array_equal(left_pred, right_pred))
    ranks_identical = all(
        np.array_equal(
            rankdata(left[left["year"].eq(year)]["y_pred"].to_numpy(dtype=float)),
            rankdata(right[right["year"].eq(year)]["y_pred"].to_numpy(dtype=float)),
        )
        for year in sorted(left["year"].unique())
    )
    if values_identical:
        expected_level = "identical_prediction_values"
    elif ranks_identical:
        expected_level = "identical_prediction_ranks_only"
    else:
        expected_level = "identical_ic_values_only"

    evidence = _committed_report()["coincident_baselines"]
    assert evidence["equality_level"] == expected_level
    assert evidence["identical_prediction_values"] is values_identical
    assert evidence["max_absolute_prediction_difference"] == pytest.approx(
        float(np.max(np.abs(left_pred - right_pred)))
    )
    assert evidence["independent_baseline_diversity"] is False
    assert evidence["specifications_retained"] is True
    assert evidence["removal_permitted_by_repository_authority"] is False
    # Both frozen specifications are still present in the dumps and the report.
    assert set(excess.COINCIDENT_BASELINE_CANDIDATES) <= set(frame["model"].unique())

    statement = evidence["strongest_supported_statement"]
    if values_identical:
        assert "bitwise-identical prediction values" in statement
        # It must not understate the evidence.
        assert "ranks" not in statement.split("which necessarily")[0]
    else:
        assert "bitwise-identical prediction values" not in statement

    markdown = (excess.OUTPUT_DIR / "significance_report.md").read_text(encoding="utf-8")
    assert "## Coincident baseline specifications" in markdown
    assert statement in markdown
    assert evidence["interpretation"] in markdown
    assert "must not be interpreted as independent baseline diversity" in markdown


def test_coincident_baseline_evidence_downgrades_when_values_differ() -> None:
    """The wording follows the evidence: perturbed values drop to the rank claim."""
    frame = _load_committed_dumps()
    left_name, right_name = excess.COINCIDENT_BASELINE_CANDIDATES
    perturbed = frame.copy()
    mask = perturbed["model"].eq(right_name)
    # A strictly positive affine shift preserves ranks but breaks value equality.
    perturbed.loc[mask, "y_pred"] = perturbed.loc[mask, "y_pred"] * 2.0 + 1.0
    evidence = excess.build_coincident_baseline_evidence(perturbed)
    assert evidence["equality_level"] == "identical_prediction_ranks_only"
    assert evidence["identical_prediction_values"] is False
    assert evidence["identical_prediction_ranks"] is True
    assert "bitwise-identical prediction values" not in evidence["strongest_supported_statement"]
    assert left_name in evidence["strongest_supported_statement"]


# --- 14. negative IC signs -------------------------------------------------


def test_negative_ic_wording_rejects_inverse_alpha_and_contrarian_readings() -> None:
    report = _committed_report()
    note = report["ic_sign_note"]
    by_name = {result["model"]: result["pooled"] for result in report["models"]}
    expected_negative = sorted(
        model
        for model in excess.FROZEN_ML_FAMILY
        if by_name[model]["observed_ic"] < 0
    )
    assert note["models_with_negative_pooled_ic"] == expected_negative
    assert note["negative_pooled_ic_count"] == len(expected_negative)
    assert note["predominantly_negative"] is (len(expected_negative) > 3)

    assert note["interpreted_as_inverse_alpha"] is False
    assert note["interpreted_as_contrarian_strategy"] is False
    assert note["interpreted_as_actionable_signal"] is False
    assert note["interpreted_as_validated_predictive_evidence"] is False
    assert note["tree_models_selected_or_privileged"] is False
    assert set(note["possible_explanations"]) == {
        "sampling variation",
        "feature-orientation effects",
        "systematic construction effects",
    }
    assert report["claim_safety"]["inverse_alpha_or_contrarian_interpretation"] is False

    # The note is family-level: no tree model is singled out.
    assert note["scope"] == "prespecified six-model ML family"
    for tree in ("random_forest", "gradient_boosting"):
        assert tree not in note["note"]
        assert tree not in note["selection_note"]

    markdown = (excess.OUTPUT_DIR / "significance_report.md").read_text(encoding="utf-8")
    assert "## Interpretation of predominantly negative IC signs" in markdown
    assert note["note"] in markdown
    assert excess.NEGATIVE_IC_LIMITATION in report["limitations"]


# --- 15. human-review package scope ---------------------------------------


def test_review_package_scope_disclosure_is_present() -> None:
    report = _committed_report()
    scope = report["review_package_scope"]
    assert scope["standalone_feature_construction_reproduction"] is False
    assert scope["standalone_model_fitting_reproduction"] is False
    assert scope["complete_independent_fitting_stage_replication_claimed"] is False
    assert set(scope["repository_technical_review_covers"]) == {
        "governed source paths",
        "protected hashes",
        "split tracing",
        "implementation behavior",
    }
    assert "prediction-to-significance layer" in scope["supports"]
    assert len(scope["statements"]) == 4

    markdown = (excess.OUTPUT_DIR / "significance_report.md").read_text(encoding="utf-8")
    assert "## Scope of the compact human-review package" in markdown
    for statement in scope["statements"]:
        assert statement in markdown
    assert excess.REVIEW_PACKAGE_LIMITATION in report["limitations"]

    manifest = json.loads(
        (excess.OUTPUT_DIR / "artifact_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["review_package_scope"] == scope
    assert manifest["estimand_invariance_audit"] == report["estimand_invariance_audit"]
    assert manifest["cross_basis_multiplicity"] == report["cross_basis_multiplicity"]


# --- 16, 17, 18. preserved bytes, protected boundary, determinism ----------


def test_leaderboard_keeps_twenty_seven_canonical_rows(
    isolated_regeneration: dict,
) -> None:
    """All 27 rows still match the canonical target rows at rtol=0, atol=1e-12."""
    regenerated = pd.read_csv(isolated_regeneration["output_dir"] / "leaderboard.csv")
    assert len(regenerated) == 27
    assert sorted(regenerated["model"].unique()) == sorted(run_experiments.MODELS)
    assert sorted(regenerated["split"].unique()) == [
        split["name"] for split in run_experiments.SPLITS
    ]

    canonical = pd.read_csv(excess.CANONICAL_TARGET_LEADERBOARD)
    canonical = canonical[canonical["target"].eq(excess.TARGET_COLUMN)]
    assert len(canonical) == 27

    keys = ["target", "split", "model", "kind"]
    left = regenerated.sort_values(keys).reset_index(drop=True)
    right = canonical[regenerated.columns.tolist()].sort_values(keys).reset_index(drop=True)
    for column in regenerated.columns:
        if pd.api.types.is_numeric_dtype(left[column]):
            assert left[column].to_numpy() == pytest.approx(
                right[column].to_numpy(), rel=0.0, abs=1e-12
            )
        else:
            assert left[column].tolist() == right[column].tolist()

    committed = pd.read_csv(excess.OUTPUT_DIR / "leaderboard.csv")
    assert len(committed) == 27
    assert (
        (excess.OUTPUT_DIR / "leaderboard.csv").read_bytes()
        == isolated_regeneration["first"]["leaderboard.csv"]
    )


def test_corrections_changed_only_report_and_manifest_bytes(
    isolated_regeneration: dict,
) -> None:
    """Prediction dumps and the leaderboard survive the corrections unchanged."""
    for name in (
        "predictions_test_2023.csv",
        "predictions_test_2024.csv",
        "predictions_test_2025.csv",
        "leaderboard.csv",
    ):
        committed = excess.OUTPUT_DIR / name
        if not committed.is_file():
            pytest.skip("generate with make research-excess")
        assert isolated_regeneration["first"][name] == committed.read_bytes()
    assert set(isolated_regeneration["first"]) == {
        "artifact_manifest.json",
        "leaderboard.csv",
        "predictions_test_2023.csv",
        "predictions_test_2024.csv",
        "predictions_test_2025.csv",
        "significance_report.json",
        "significance_report.md",
    }


def test_protected_boundary_and_determinism_survive_the_corrections(
    isolated_regeneration: dict,
) -> None:
    assert isolated_regeneration["protected_count"] == 351
    assert isolated_regeneration["protected_before"] == isolated_regeneration["protected_after"]
    assert isolated_regeneration["first"] == isolated_regeneration["second"]
    # The corrected report parses and carries every new section.
    report = json.loads(
        isolated_regeneration["first"]["significance_report.json"].decode("utf-8")
    )
    for section in (
        "estimand_invariance_audit",
        "significance_comparison",
        "cross_basis_multiplicity",
        "coincident_baselines",
        "ic_sign_note",
        "review_package_scope",
    ):
        assert section in report
