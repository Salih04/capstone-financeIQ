"""R3-NULL-01 negative-control / placebo laboratory tests.

These pin the placebo machinery's honesty guarantees: the noise-panel builder
preserves structure while replacing every feature, the noise is deterministic per
seed yet independent across seeds/rows/features and free of forged ticker/year
structure, canonical input frames are never mutated, the family-wise rejection
arithmetic and binomial reference are correct, every repetition (including
failures) stays visible, serialization is deterministic, and adversarial
"this is a market signal" wording is rejected.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from experiments import placebo_lab as pl
from experiments import run_experiments as rx
from experiments import significance as sig


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
def _toy_reference() -> tuple[pd.DataFrame, list[str]]:
    """A small structural panel: two tickers across three feature-years, 3 features.

    Feature values are deliberately non-noise sentinels so a failure to replace
    them is detectable, and the split years line up with rx.SPLITS-style filters.
    """
    rows = []
    for ticker in ("AAA", "BBB", "CCC", "DDD"):
        for year in (2021, 2022, 2023, 2024):
            rows.append(
                {
                    "ticker": ticker,
                    "feature_year": year,
                    "f_alpha": 111.0,
                    "f_beta": 222.0,
                    "f_gamma": 333.0,
                    "target_return": 10.0 + hash((ticker, year)) % 7,
                }
            )
    frame = pd.DataFrame(rows)[
        ["ticker", "feature_year", "f_alpha", "f_beta", "f_gamma", "target_return"]
    ]
    return frame, ["f_alpha", "f_beta", "f_gamma"]


def _planted_signal_reference() -> tuple[pd.DataFrame, list[str]]:
    """A compact panel whose feature perfectly and prospectively encodes y_true."""
    rows = []
    for rank in range(1, 21):
        for year in (2020, 2021, 2022, 2023, 2024):
            target = float(rank)
            rows.append(
                {
                    "ticker": f"SIG{rank:02d}",
                    "feature_year": year,
                    "planted_signal": target,
                    "target_return": target,
                }
            )
    return pd.DataFrame(rows), ["planted_signal"]


# --------------------------------------------------------------------------- #
# Noise-panel builder: structure preserved, features replaced
# --------------------------------------------------------------------------- #
def test_noise_panel_preserves_structure_and_replaces_every_feature() -> None:
    ref, feats = _toy_reference()
    original = ref[feats].to_numpy(float).copy()
    noise = pl.build_noise_panel(ref, feats, seed=7)

    # Schema, row count, and column order preserved exactly.
    assert list(noise.columns) == list(ref.columns)
    assert len(noise) == len(ref)
    # Identity, split/year, and target columns preserved byte-for-byte.
    for column in pl.PANEL_ID_COLUMNS:
        pd.testing.assert_series_equal(noise[column], ref[column])
    assert noise["ticker"].tolist() == ref["ticker"].tolist()
    assert noise["feature_year"].tolist() == ref["feature_year"].tolist()
    assert noise["target_return"].tolist() == ref["target_return"].tolist()
    # Every feature value replaced (none of the sentinels survive) and finite.
    replaced = noise[feats].to_numpy(float)
    assert np.isfinite(replaced).all()
    assert not np.any(np.isin(replaced, original))


def test_reference_frame_is_not_mutated() -> None:
    ref, feats = _toy_reference()
    before = ref.copy(deep=True)
    pl.build_noise_panel(ref, feats, seed=1)
    pl.build_noise_panel(ref, feats, seed=2)
    pd.testing.assert_frame_equal(ref, before)


def test_reference_panel_builder_does_not_mutate_canonical_features() -> None:
    """Building the real panel twice yields identical feature blocks (read-only)."""
    first, feats = pl.reference_panel()
    snapshot = first[feats].to_numpy(float).copy()
    _second, _ = pl.reference_panel()
    assert np.array_equal(first[feats].to_numpy(float), snapshot, equal_nan=True)


# --------------------------------------------------------------------------- #
# Determinism and independence
# --------------------------------------------------------------------------- #
def test_noise_is_deterministic_for_a_fixed_seed() -> None:
    ref, feats = _toy_reference()
    a = pl.build_noise_panel(ref, feats, seed=42)
    b = pl.build_noise_panel(ref, feats, seed=42)
    assert np.array_equal(a[feats].to_numpy(float), b[feats].to_numpy(float))


def test_noise_differs_across_repetitions() -> None:
    ref, feats = _toy_reference()
    a = pl.build_noise_panel(ref, feats, seed=100)
    b = pl.build_noise_panel(ref, feats, seed=101)
    assert not np.array_equal(a[feats].to_numpy(float), b[feats].to_numpy(float))


def test_noise_differs_across_rows_and_features() -> None:
    ref, feats = _toy_reference()
    noise = pl.build_noise_panel(ref, feats, seed=5)
    values = noise[feats].to_numpy(float)
    # No two rows are identical across all features.
    assert len({tuple(row) for row in values}) == len(values)
    # No two feature columns are identical across all rows.
    assert len({tuple(col) for col in values.T}) == values.shape[1]


def test_no_ticker_constant_or_year_constant_structure() -> None:
    """Multi-year tickers get independent noise each year; each year varies by row."""
    ref, feats = pl.reference_panel()
    noise = pl.build_noise_panel(ref, feats, seed=9)

    counts = noise.groupby("ticker").size()
    multi_year = counts[counts >= 2].index
    within_ticker_var = (
        noise[noise["ticker"].isin(multi_year)].groupby("ticker")[feats].var(ddof=0)
    )
    # No feature is constant across years for any ticker that spans >=2 years.
    assert bool((within_ticker_var > 0).all().all())

    within_year_var = noise.groupby("feature_year")[feats].var(ddof=0)
    # No feature is constant across tickers within any year.
    assert bool((within_year_var > 0).all().all())


# --------------------------------------------------------------------------- #
# Family-wise rejection arithmetic and binomial reference
# --------------------------------------------------------------------------- #
def test_family_wise_gate_matches_significance_bonferroni(tmp_path: Path) -> None:
    """The placebo gate must equal significance.build_report's Bonferroni result."""
    ref, feats = pl.reference_panel()
    noise = pl.build_noise_panel(ref, feats, seed=2024)
    pl._write_ml_prediction_dumps(noise, feats, tmp_path)

    gate = pl._family_wise_gate(
        tmp_path, permutations=2000, bootstraps=2000, significance_seed=42
    )

    # Recompute independently via significance.analyze_model on the same dumps.
    predictions, _ = sig.load_prediction_dumps(tmp_path)
    raw = {}
    for model in sig.ML_MODELS:
        raw[model] = sig.analyze_model(
            predictions[predictions["model"] == model],
            permutations=2000,
            bootstraps=2000,
            seed=42,
        )["pooled"]["permutation_p_value_two_sided"]
    expected_min_model = min(sig.ML_MODELS, key=lambda m: (raw[m], m))
    expected_min_p = raw[expected_min_model]
    expected_adjusted = min(1.0, expected_min_p * len(sig.ML_MODELS))

    assert gate["min_raw_p_model"] == expected_min_model
    assert gate["min_raw_p_value"] == pytest.approx(expected_min_p, abs=1e-9)
    assert gate["family_wise_rejected"] == (expected_adjusted < 0.05)


def test_real_writer_and_family_wise_gate_reject_planted_signal(
    tmp_path: Path,
) -> None:
    """Positive control: actual dump writer -> significance -> six-model gate."""
    panel, features = _planted_signal_reference()
    pl._write_ml_prediction_dumps(panel, features, tmp_path)

    permutations = 1_000  # canonical analyzer minimum; deterministic and test-sized
    gate = pl._family_wise_gate(
        tmp_path,
        permutations=permutations,
        bootstraps=200,
        significance_seed=42,
    )

    permutation_floor = 1.0 / (permutations + 1)
    assert gate["family_wise_rejected"] is True
    assert gate["min_raw_p_value"] == pytest.approx(permutation_floor, abs=1e-10)
    assert gate["min_raw_p_model"] in gate["raw_p_by_model"]
    assert gate["raw_p_by_model"][gate["min_raw_p_model"]] == pytest.approx(
        gate["min_raw_p_value"]
    )
    assert set(gate["raw_p_by_model"]) == set(sig.ML_MODELS)
    assert len(gate["raw_p_by_model"]) == pl.FAMILY_SIZE == 6
    assert gate["bonferroni_adjusted_min_p"] == pytest.approx(
        permutation_floor * 6
    )


def test_binomial_reference_arithmetic_is_exact() -> None:
    # 0 rejections in 20 at alpha=0.05: P(X<=0) = 0.95**20; P(X>=0)=1.
    ref0 = pl.binomial_reference(0, 20, 0.05)
    assert ref0["expected_rejections"] == pytest.approx(1.0)
    assert ref0["observed_rate"] == pytest.approx(0.0)
    assert ref0["p_value_lower_tail_le_observed"] == pytest.approx(0.95**20, abs=1e-9)
    assert ref0["p_value_upper_tail_ge_observed"] == pytest.approx(1.0, abs=1e-9)

    # 1 rejection in 20: upper tail = 1 - 0.95**20.
    ref1 = pl.binomial_reference(1, 20, 0.05)
    assert ref1["p_value_upper_tail_ge_observed"] == pytest.approx(
        1.0 - 0.95**20, abs=1e-9
    )
    assert ref1["observed_rejections"] == 1

    # 0/25 exact two-sided Clopper-Pearson endpoint:
    # (1 - p_upper)^25 = 0.025, so p_upper = 1 - 0.025^(1/25).
    ref25 = pl.binomial_reference(0, 25, 0.05)
    expected_upper = 1.0 - 0.025 ** (1.0 / 25)
    assert ref25["expected_rejections"] == pytest.approx(1.25)
    assert ref25["p_value_lower_tail_le_observed"] == pytest.approx(0.95**25)
    assert ref25["exact_two_sided_confidence_level"] == pytest.approx(0.95)
    assert ref25["exact_two_sided_clopper_pearson_upper_bound"] == pytest.approx(
        expected_upper, abs=1e-10
    )
    assert expected_upper == pytest.approx(0.1371851715, abs=1e-10)


# --------------------------------------------------------------------------- #
# Every repetition visible; failures explicit, never silently omitted
# --------------------------------------------------------------------------- #
def test_all_repetitions_remain_visible_in_report() -> None:
    ref, feats = _toy_reference()
    records = [
        {
            "rep_index": i,
            "seed": 1000 + i,
            "status": "complete",
            "pooled_ic_by_model": {m: 0.0 for m in pl.ML_FAMILY},
            "raw_p_by_model": {m: 0.5 for m in pl.ML_FAMILY},
            "min_raw_p_value": 0.5,
            "min_raw_p_model": pl.ML_FAMILY[0],
            "bonferroni_adjusted_min_p": 1.0,
            "family_wise_rejected": (i == 2),  # one placebo "hit" must stay visible
            "runtime_seconds": 0.1,
        }
        for i in range(20)
    ]
    report = pl.build_report(
        ref, feats, records, permutations=10, bootstraps=10, significance_seed=42, base_seed=0
    )
    assert len(report["repetitions"]) == 20
    assert report["summary"]["repetitions_total"] == 20
    assert report["summary"]["family_wise_rejection_count"] == 1
    assert report["summary"]["family_wise_rejection_rate"] == pytest.approx(0.05)
    # The rejecting repetition is retained, not pruned.
    assert any(r["family_wise_rejected"] for r in report["repetitions"])


def test_failed_repetition_is_explicit_not_omitted() -> None:
    ref, feats = _toy_reference()
    good = {
        "rep_index": 0,
        "seed": 1,
        "status": "complete",
        "pooled_ic_by_model": {m: 0.0 for m in pl.ML_FAMILY},
        "raw_p_by_model": {m: 0.5 for m in pl.ML_FAMILY},
        "min_raw_p_value": 0.5,
        "min_raw_p_model": pl.ML_FAMILY[0],
        "bonferroni_adjusted_min_p": 1.0,
        "family_wise_rejected": False,
        "runtime_seconds": 0.1,
    }
    bad = {
        "rep_index": 1,
        "seed": 2,
        "status": "failed",
        "error": "ValueError: boom",
        "family_wise_rejected": None,
        "min_raw_p_value": None,
        "runtime_seconds": 0.1,
    }
    report = pl.build_report(
        ref, feats, [good, bad], permutations=10, bootstraps=10, significance_seed=42, base_seed=0
    )
    assert report["analysis_status"] == "partial_with_explicit_failed_repetitions"
    assert report["summary"]["repetitions_failed"] == 1
    assert report["summary"]["failed_rep_indices"] == [1]
    assert len(report["repetitions"]) == 2
    # A failed repetition is not counted as a (non-)rejection.
    assert report["summary"]["family_wise_rejection_count"] == 0


def test_run_repetition_captures_failure_without_raising(monkeypatch) -> None:
    ref, feats = _toy_reference()

    def _boom(*_args, **_kwargs):
        raise RuntimeError("injected failure")

    monkeypatch.setattr(pl, "_write_ml_prediction_dumps", _boom)
    record = pl.run_repetition(
        ref, feats, rep_index=3, seed=77, permutations=10, bootstraps=10, significance_seed=42
    )
    assert record["status"] == "failed"
    assert "injected failure" in record["error"]
    assert record["family_wise_rejected"] is None
    assert record["rep_index"] == 3 and record["seed"] == 77


# --------------------------------------------------------------------------- #
# Claim safety
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "unsafe",
    [
        "The placebo captured alpha.",
        "Alpha captured from noise features.",
        "This placebo run found a market edge.",
        "Profitable trading follows from these placebo hits.",
        "The noise produced a real signal.",
        "A reliable edge was detected in the placebo.",
        "Signal found in the placebo repetitions.",
        "The placebo is a signal about BIST.",
        "These results are market-beating.",
    ],
)
def test_claim_safety_rejects_unsafe_interpretations(unsafe: str) -> None:
    with pytest.raises(ValueError, match="Unsafe placebo claim"):
        pl.validate_claim_safety_text(unsafe)


def test_claim_safety_accepts_the_mandatory_sentence_and_conclusion() -> None:
    # The mandatory sentence and the standard conclusion must NOT be rejected.
    pl.validate_claim_safety_text(pl.CLAIM_SAFETY_SENTENCE)
    pl.validate_claim_safety_text(
        "The conclusion remains: no reliable predictive edge. Research support only."
    )


def test_mandatory_sentence_present_verbatim_in_json_and_markdown() -> None:
    corrected_sentence = (
        "Placebo runs test the evaluation machinery, not the market; the expected "
        "outcome is failure to reject known-null inputs in approximately (1 − α) of "
        "repetitions, and any placebo ‘significance’ is a false positive at rate α or "
        "a numerical artifact — never a signal."
    )
    ref, feats = _toy_reference()
    records = [
        {
            "rep_index": 0,
            "seed": 1,
            "status": "complete",
            "pooled_ic_by_model": {m: 0.0 for m in pl.ML_FAMILY},
            "raw_p_by_model": {m: 0.5 for m in pl.ML_FAMILY},
            "min_raw_p_value": 0.5,
            "min_raw_p_model": pl.ML_FAMILY[0],
            "bonferroni_adjusted_min_p": 1.0,
            "family_wise_rejected": False,
            "runtime_seconds": 0.1,
        }
    ]
    report = pl.build_report(
        ref, feats, records, permutations=10, bootstraps=10, significance_seed=42, base_seed=0
    )
    assert pl.CLAIM_SAFETY_SENTENCE == corrected_sentence
    assert report["claim_safety_sentence"] == corrected_sentence
    markdown = pl.render_markdown(report)
    assert corrected_sentence in markdown
    serialized = json.dumps(report, ensure_ascii=False)
    assert corrected_sentence in serialized
    assert (
        report["claim_safety"][
            "expected_outcome_is_nonrejection_at_rate_one_minus_alpha"
        ]
        is True
    )
    assert "expected_outcome_is_rejection_of_noise" not in serialized
    assert "expected outcome is rejection of noise" not in serialized.lower()
    assert "expected outcome is rejection of noise" not in markdown.lower()


def test_r25_low_resolution_limitation_and_interval_are_disclosed() -> None:
    ref, feats = _toy_reference()
    records = [
        {
            "rep_index": i,
            "seed": 100 + i,
            "status": "complete",
            "pooled_ic_by_model": {m: 0.0 for m in pl.ML_FAMILY},
            "raw_p_by_model": {m: 0.5 for m in pl.ML_FAMILY},
            "min_raw_p_value": 0.5,
            "min_raw_p_model": pl.ML_FAMILY[0],
            "bonferroni_adjusted_min_p": 1.0,
            "family_wise_rejected": False,
            "runtime_seconds": 0.1,
        }
        for i in range(25)
    ]
    report = pl.build_report(
        ref,
        feats,
        records,
        permutations=1_000,
        bootstraps=200,
        significance_seed=42,
        base_seed=100,
    )
    markdown = pl.render_markdown(report)
    limitations = " ".join(report["limitations"])

    assert "R=25 is a low-resolution negative-control smoke test." in limitations
    assert (
        "0/25 does not certify exact family-wise calibration at alpha=0.05."
        in limitations
    )
    assert (
        "It can expose gross anti-conservatism but cannot precisely estimate the Type-I error rate."
        in limitations
    )
    assert "approximately 0.137" in limitations
    assert "0.1371851715" in limitations
    assert "R=25 is a low-resolution negative-control smoke test." in markdown
    assert "does not certify exact family-wise calibration" in markdown


# --------------------------------------------------------------------------- #
# Determinism of serialization and the end-to-end workflow
# --------------------------------------------------------------------------- #
def test_workflow_is_byte_deterministic(tmp_path: Path) -> None:
    first_runtime = tmp_path / "runtime" / "first.json"
    second_runtime = tmp_path / "runtime" / "second.json"
    first_json, first_md = pl.run(
        tmp_path / "first",
        runtime_output=first_runtime,
        repetitions=20,
        permutations=1000,
        bootstraps=1000,
    )
    second_json, second_md = pl.run(
        tmp_path / "second",
        runtime_output=second_runtime,
        repetitions=20,
        permutations=1000,
        bootstraps=1000,
    )
    assert first_json.read_bytes() == second_json.read_bytes()
    assert first_md.read_bytes() == second_md.read_bytes()
    assert first_runtime.is_file() and second_runtime.is_file()
    assert {path.name for path in first_json.parent.iterdir()} == {
        "placebo_report.json",
        "placebo_report.md",
    }
    assert {path.name for path in second_json.parent.iterdir()} == {
        "placebo_report.json",
        "placebo_report.md",
    }

    report = json.loads(first_json.read_text(encoding="utf-8"))
    assert report["task"] == "R3-NULL-01"
    assert report["design"]["repetitions"] == 20
    assert report["design"]["model_family"] == list(sig.ML_MODELS)
    assert report["design"]["features_replaced"] == "all"
    # Deterministic ordering: repetitions ascend by index.
    indices = [r["rep_index"] for r in report["repetitions"]]
    assert indices == sorted(indices) == list(range(20))
    pl.validate_claim_safety_text(first_md.read_text(encoding="utf-8"))


def test_run_rejects_fewer_than_twenty_repetitions(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least 20"):
        pl.run(tmp_path / "x", repetitions=19)


def test_generated_artifacts_have_expected_shape_when_present() -> None:
    if not pl.JSON_OUTPUT.is_file():
        pytest.skip("placebo artifacts not generated; run 'make research-placebo'")
    report = json.loads(pl.JSON_OUTPUT.read_text(encoding="utf-8"))
    markdown = pl.MARKDOWN_OUTPUT.read_text(encoding="utf-8")
    assert report["task"] == "R3-NULL-01"
    assert report["generated_by"]["generator_command"] == "make research-placebo"
    assert report["design"]["repetitions"] >= 20
    assert report["design"]["model_family"] == list(sig.ML_MODELS)
    assert report["claim_safety"]["placebo_significance_is_a_signal"] is False
    assert (
        report["claim_safety"][
            "expected_outcome_is_nonrejection_at_rate_one_minus_alpha"
        ]
        is True
    )
    assert "expected_outcome_is_rejection_of_noise" not in report["claim_safety"]
    assert report["claim_safety"]["canonical_artifacts_modified"] is False
    assert report["claim_safety_sentence"] == pl.CLAIM_SAFETY_SENTENCE
    assert pl.CLAIM_SAFETY_SENTENCE in markdown
    artifact_blob = pl.JSON_OUTPUT.read_text(encoding="utf-8") + markdown
    assert "expected outcome is rejection of noise" not in artifact_blob.lower()
    # Every repetition is present and either complete or explicitly failed.
    assert len(report["repetitions"]) == report["design"]["repetitions"]
    assert all(r["status"] in {"complete", "failed"} for r in report["repetitions"])
    pl.validate_claim_safety_text(markdown)
