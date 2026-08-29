"""Guards for Stage 1 — raw-layer positive control (``experiments/thesis/positive_control.py``).

The stage deliberately manufactures a relationship between a raw feature and the
future-return ranking. That makes it exactly the kind of code that must not be
able to leak into anything else, so these tests police three separate things:

1. **The injection is honest** — it fabricates no value, preserves the carrier's
   own marginal and missingness, leaves every other column bit-identical, and
   forces no correlation at ``theta = 0``.
2. **The injection is contained** — the real modeling dataset is never written,
   the production pipeline is unchanged the moment a repetition ends, and no
   governed historical results root can be written into.
3. **The measurements mean what the report says** — attenuation arithmetic, the
   copula identity, the Bonferroni rule, determinism, and the no-interpolation
   rule for the detection threshold.

Nothing here asserts a scientific outcome. A positive control that "passes" is
evidence about the instrument, not about BIST.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import Ridge

from experiments import run_experiments as rx
from experiments import significance as sig
from experiments.thesis import positive_control as pc
from experiments.thesis import provenance as prov


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "experiments" / "results_thesis" / "positive_control"


@pytest.fixture(scope="module")
def raw_table() -> pd.DataFrame:
    return pd.read_csv(rx.TRAINING_MODELING)


@pytest.fixture(scope="module")
def carriers(raw_table: pd.DataFrame) -> dict[str, str]:
    return pc.select_carriers(raw_table)


def _synthetic_raw(rows_per_year: int = 60, years: tuple[int, ...] = (2022, 2023, 2024),
                   seed: int = 11) -> pd.DataFrame:
    """A controlled fixture with the raw table's shape but no real data.

    Used where a test needs to reason about a *known* structure rather than
    inherit whatever the real panel happens to contain.
    """
    rng = np.random.default_rng(seed)
    frames = []
    for year in years:
        frame = pd.DataFrame(
            {
                "ticker": [f"T{index:03d}" for index in range(rows_per_year)],
                "year": year,
                "carrier": rng.normal(size=rows_per_year),
                "other": rng.normal(size=rows_per_year),
                pc.TARGET_COLUMN: rng.normal(size=rows_per_year),
            }
        )
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def _realized_ic(injected: pd.DataFrame, carrier: str = "carrier") -> float:
    pooled, _, _ = pc.pooled_spearman_by_year(
        injected[carrier], injected[pc.TARGET_COLUMN], injected[pc.YEAR_COLUMN]
    )
    return float(pooled)


# --------------------------------------------------------------------------- #
# 1. Zero injection forces no correlation
# --------------------------------------------------------------------------- #
def test_zero_injection_uses_zero_latent_correlation():
    """theta = 0 must reduce the mechanism to an independent permutation, exactly."""
    assert pc.latent_correlation_for_ic(0.0) == 0.0


def test_zero_injection_produces_no_forced_correlation():
    """Averaged over seeds, theta = 0 recovers a carrier/target IC centred on zero.

    A single draw of a random permutation has non-zero sample correlation; the
    claim being tested is that the *mechanism* introduces no systematic
    relationship, so the test looks at the mean across many independent seeds
    and at a tolerance derived from the design rather than from the observation.
    """
    fixture = _synthetic_raw()
    realized = [
        _realized_ic(pc.inject_carrier(fixture, "carrier", 0.0, seed=seed))
        for seed in range(60)
    ]
    mean = float(np.mean(realized))
    # Standard error of a pooled 3-year Spearman at n=60 is about 1/sqrt(3*57);
    # 60 seeds shrink it by another sqrt(60). Three of those is a wide margin.
    tolerance = 3.0 / math.sqrt(3 * (60 - 3) * 60)
    assert abs(mean) < tolerance, f"theta=0 mean realized IC {mean} exceeds {tolerance}"


def test_zero_injection_is_a_pure_permutation_of_the_column(raw_table, carriers):
    """At theta = 0 the output is a rearrangement of the input's own values."""
    carrier = carriers["primary"]
    injected = pc.inject_carrier(raw_table, carrier, 0.0, seed=5)
    for year, group in raw_table.groupby(pc.YEAR_COLUMN):
        before = np.sort(group[carrier].dropna().to_numpy(dtype=float))
        after = np.sort(
            injected.loc[injected[pc.YEAR_COLUMN] == year, carrier].dropna().to_numpy(dtype=float)
        )
        assert np.array_equal(before, after), f"year {year} marginal changed"


# --------------------------------------------------------------------------- #
# 2. Stronger injection increases the realized relationship, monotonically
# --------------------------------------------------------------------------- #
def test_stronger_injection_monotonically_increases_realized_ic():
    """On a controlled fixture, mean realized IC is strictly increasing in theta."""
    fixture = _synthetic_raw()
    means = []
    for level_index, theta in enumerate(pc.IC_GRID):
        realized = [
            _realized_ic(pc.inject_carrier(fixture, "carrier", theta, seed=1000 * level_index + seed))
            for seed in range(40)
        ]
        means.append(float(np.mean(realized)))
    assert all(b > a for a, b in zip(means, means[1:])), f"not monotone: {means}"


def test_realized_ic_tracks_the_intended_level():
    """Mean realized IC lands on the intended level, not merely above the previous one.

    This is the property that makes "injected IC" a meaningful label rather than
    an ordinal rank, so it is checked against theta itself.
    """
    fixture = _synthetic_raw(rows_per_year=80)
    for theta in (0.10, 0.20, 0.30, 0.40):
        realized = [
            _realized_ic(pc.inject_carrier(fixture, "carrier", theta, seed=seed))
            for seed in range(60)
        ]
        mean = float(np.mean(realized))
        assert abs(mean - theta) < 0.03, f"theta={theta} realized mean {mean}"


def test_copula_identity_matches_the_governed_power_simulator():
    """The injection and significance.simulate_fisher_power must share one identity.

    If these ever diverge, the empirical detection curve and the analytic power
    curve stop being expressed on the same scale and the comparison in the
    report becomes meaningless. The fixed seeded outputs below exercise the
    governed simulator itself; this is not a test of positive_control.py's
    formula against a duplicate of that formula.
    """
    governed_power = [
        sig.simulate_fisher_power(
            theta,
            n_per_split=80,
            split_count=3,
            simulations=2_000,
            seed=1729,
            alpha=pc.ALPHA / pc.CONFIRMATORY_FAMILY_SIZE,
        )
        for theta in (0.05, 0.1, 0.25, 0.4, 0.9)
    ]
    assert governed_power == pytest.approx([0.0345, 0.155, 0.908, 1.0, 1.0])
    for theta in (0.05, 0.1, 0.25, 0.4, 0.9):
        assert pc.latent_correlation_for_ic(theta) == pytest.approx(
            2.0 * math.sin(math.pi * theta / 6.0), rel=1e-12
        )
    # LOW residual (independent review, optional): the line above still checks
    # pc.latent_correlation_for_ic against a re-typed copy of the same formula.
    # Coupling it behaviourally to the governed implementation would mean
    # exposing the copula map from significance.py, which is out of scope for
    # this bounded task. As a minimal stand-in, pin the governed source: if
    # simulate_fisher_power's Gaussian-copula identity drifts from the one the
    # injection uses, this fails.
    governed_source = inspect.getsource(sig.simulate_fisher_power)
    assert "2.0 * math.sin(math.pi * true_ic / 6.0)" in governed_source


# --------------------------------------------------------------------------- #
# 3. Determinism
# --------------------------------------------------------------------------- #
def test_injection_is_deterministic_for_a_fixed_seed(raw_table, carriers):
    left = pc.inject_carrier(raw_table, carriers["primary"], 0.30, seed=99)
    right = pc.inject_carrier(raw_table, carriers["primary"], 0.30, seed=99)
    pd.testing.assert_frame_equal(left, right)


def test_different_seeds_give_different_injections(raw_table, carriers):
    left = pc.inject_carrier(raw_table, carriers["primary"], 0.30, seed=1)
    right = pc.inject_carrier(raw_table, carriers["primary"], 0.30, seed=2)
    assert not left[carriers["primary"]].equals(right[carriers["primary"]])


def test_repetition_replays_identically(raw_table, carriers):
    """A whole repetition — injection, pipeline, significance — must replay byte-equal."""
    kwargs = dict(injection_seed=4242, permutation_seed=42, permutations=1_000, bootstraps=1_000)
    first = pc.run_repetition(raw_table, carriers["primary"], 0.30, **kwargs)
    second = pc.run_repetition(raw_table, carriers["primary"], 0.30, **kwargs)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_seed_formulas_are_declared_and_collision_free():
    seeds = {
        pc.derive_injection_seed(42, level, rep)
        for level in range(len(pc.IC_GRID))
        for rep in range(pc.DESCRIPTIVE_REPETITIONS)
    }
    assert len(seeds) == len(pc.IC_GRID) * pc.DESCRIPTIVE_REPETITIONS
    # Repetition 0 must run on the governed default so the confirmatory arm is
    # not using a seed invented by this stage.
    assert pc.derive_permutation_seed(42, 0) == sig.DEFAULT_SEED


# --------------------------------------------------------------------------- #
# 4. Protected historical result directories cannot be written
# --------------------------------------------------------------------------- #
def test_stage_output_dir_is_inside_the_thesis_namespace():
    target = prov.output_dir(pc.SLUG, create=False)
    assert target.relative_to(prov.THESIS_RESULTS_ROOT.resolve()).as_posix() == pc.SLUG


def test_protected_results_roots_are_refused(monkeypatch):
    """Redirecting the thesis root onto a governed root must raise, not overwrite."""
    for protected in prov.PROTECTED_RESULTS_ROOTS:
        monkeypatch.setattr(prov, "THESIS_RESULTS_ROOT", prov.ROOT / protected)
        with pytest.raises(prov.ThesisProvenanceError, match="protected results root"):
            prov.output_dir(pc.SLUG, create=False)


def test_every_governed_results_root_is_protected():
    """The registry's governed roots under experiments/ must all be refused."""
    registry = json.loads((REPO_ROOT / "artifact_registry.json").read_text(encoding="utf-8"))
    governed = [
        root
        for root in registry["governed_roots"]
        if root.startswith("experiments/") and root != "experiments/results_thesis/positive_control"
    ]
    missing = sorted(set(governed) - set(prov.PROTECTED_RESULTS_ROOTS))
    assert missing == [], f"governed roots not protected from thesis writes: {missing}"


def test_undeclared_slug_cannot_claim_an_output_dir():
    with pytest.raises(prov.ThesisProvenanceError):
        prov.output_dir("not_a_declared_experiment", create=False)


# --------------------------------------------------------------------------- #
# 5. Attenuation arithmetic
# --------------------------------------------------------------------------- #
def test_attenuation_ratio_is_observed_over_injected():
    checkpoints = {
        "ic_injected": 0.40,
        "ic_raw_carrier": 0.40,
        "ic_panel_carrier": 0.20,
        "ic_model_input_carrier": 0.10,
        "ic_model_prediction": -0.05,
        "ic_final_evaluation": -0.05,
    }
    ratios = pc.attenuation_ratios(checkpoints)
    assert ratios["ic_raw_carrier"] == pytest.approx(1.0)
    assert ratios["ic_panel_carrier"] == pytest.approx(0.5)
    assert ratios["ic_model_input_carrier"] == pytest.approx(0.25)
    # A sign reversal must survive as a negative ratio, not be absolutized away.
    assert ratios["ic_model_prediction"] == pytest.approx(-0.125)
    assert "ic_injected" not in ratios


def test_attenuation_ratio_is_null_at_zero_injection():
    """Division by zero is reported as null, never as infinity or a substitute."""
    ratios = pc.attenuation_ratios(
        {"ic_injected": 0.0, "ic_raw_carrier": 0.1, "ic_panel_carrier": None,
         "ic_model_input_carrier": 0.05, "ic_model_prediction": 0.02,
         "ic_final_evaluation": 0.02}
    )
    assert set(ratios.values()) == {None}


def test_stagewise_ratio_chains_consecutive_checkpoints():
    ratios = pc.stagewise_ratios(
        {"ic_injected": 0.40, "ic_raw_carrier": 0.40, "ic_panel_carrier": 0.20,
         "ic_model_input_carrier": 0.10, "ic_model_prediction": 0.05,
         "ic_final_evaluation": 0.05}
    )
    assert ratios["ic_injected__to__ic_raw_carrier"] == pytest.approx(1.0)
    assert ratios["ic_raw_carrier__to__ic_panel_carrier"] == pytest.approx(0.5)
    assert ratios["ic_model_prediction__to__ic_final_evaluation"] == pytest.approx(1.0)


def test_pooled_spearman_equals_the_governed_statistic():
    """The checkpoint statistic must be the frozen baseline's, not a re-derivation."""
    rng = np.random.default_rng(3)
    frames = []
    for year in (2022, 2023, 2024):
        values = rng.normal(size=50)
        frames.append(pd.DataFrame({"year": year, "value": values, "target": values + rng.normal(size=50)}))
    frame = pd.concat(frames, ignore_index=True)
    pooled, n_used, per_year = pc.pooled_spearman_by_year(frame["value"], frame["target"], frame["year"])
    expected = [
        sig.spearman_ic(group["value"].to_numpy(float), group["target"].to_numpy(float))
        for _, group in frame.groupby("year", sort=True)
    ]
    assert pooled == pytest.approx(float(np.mean(expected)))
    assert n_used == 150
    assert sorted(per_year) == [2022, 2023, 2024]


def test_pooled_spearman_drops_null_pairs_and_reports_the_used_count():
    frame = pd.DataFrame(
        {"year": [2022] * 10, "value": [1, 2, 3, 4, 5, None, None, 8, 9, 10],
         "target": [1, 2, 3, 4, 5, 6, 7, None, 9, 10]}
    )
    pooled, n_used, _ = pc.pooled_spearman_by_year(frame["value"], frame["target"], frame["year"])
    assert n_used == 7
    assert pooled == pytest.approx(1.0)


def test_model_input_checkpoint_mirrors_the_real_imputation():
    """The checkpoint's NaN fill must be behaviourally identical to _fit_sklearn's.

    Asserted through predictions rather than by reading a constant, so the test
    still fails if run_experiments changes how it imputes.
    """
    rng = np.random.default_rng(17)
    x_train = rng.random((40, 5))
    y_train = rng.normal(size=40)
    x_test = rng.random((20, 5))
    x_test[::3, 2] = np.nan
    from_pipeline = rx._fit_sklearn(Ridge(alpha=1.0), x_train, y_train, x_test)
    mirrored = Ridge(alpha=1.0).fit(
        np.nan_to_num(x_train, nan=pc.RANK_IMPUTE_CENTER), y_train
    ).predict(np.nan_to_num(x_test, nan=pc.RANK_IMPUTE_CENTER))
    assert np.allclose(from_pipeline, mirrored)


def test_wilson_interval_brackets_the_point_estimate():
    low, high = pc._wilson_interval(160, 200)
    assert low < 0.80 < high
    assert pc._wilson_interval(0, 200)[0] == 0.0
    assert pc._wilson_interval(200, 200)[1] == 1.0
    assert pc._wilson_interval(0, 0) == [None, None]


# --------------------------------------------------------------------------- #
# 6. Injection is absent unless the stage is actively running
# --------------------------------------------------------------------------- #
def test_pipeline_override_is_restored_after_the_block():
    original = rx.TRAINING_MODELING
    with pc._pipeline_reads(Path("/nonexistent/injected.csv")):
        assert rx.TRAINING_MODELING != original
    assert rx.TRAINING_MODELING == original


def test_pipeline_override_is_restored_after_an_exception():
    original = rx.TRAINING_MODELING
    with pytest.raises(RuntimeError):
        with pc._pipeline_reads(Path("/nonexistent/injected.csv")):
            raise RuntimeError("boom")
    assert rx.TRAINING_MODELING == original


def test_running_a_repetition_leaves_the_pipeline_pointing_at_real_data(raw_table, carriers):
    original = rx.TRAINING_MODELING
    pc.run_repetition(
        raw_table, carriers["primary"], 0.40,
        injection_seed=1, permutation_seed=42, permutations=1_000, bootstraps=1_000,
    )
    assert rx.TRAINING_MODELING == original
    assert rx._modeling_csv() == original


def test_importing_the_stage_does_not_inject_anything(raw_table):
    """An isolated import must leave the source dataset bytes unchanged."""
    del raw_table  # The subprocess must establish both hashes around the import.
    dataset = str(rx.TRAINING_MODELING)
    script = f"""
import hashlib
from pathlib import Path

path = Path({dataset!r})

def digest():
    return hashlib.sha256(path.read_bytes()).hexdigest()

before = digest()
import experiments.thesis.positive_control
after = digest()
assert before == after, (before, after)
print(before)
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


# --------------------------------------------------------------------------- #
# 7. Ordinary production/research pipeline behaviour is unchanged
# --------------------------------------------------------------------------- #
def test_real_modeling_dataset_is_never_written(raw_table, carriers):
    digest_before = hashlib.sha256(rx.TRAINING_MODELING.read_bytes()).hexdigest()
    pc.run_repetition(
        raw_table, carriers["primary"], 0.40,
        injection_seed=2, permutation_seed=42, permutations=1_000, bootstraps=1_000,
    )
    assert hashlib.sha256(rx.TRAINING_MODELING.read_bytes()).hexdigest() == digest_before


def test_build_panel_is_unchanged_by_a_repetition(raw_table, carriers):
    before = rx.build_panel()
    pc.run_repetition(
        raw_table, carriers["primary"], 0.40,
        injection_seed=3, permutation_seed=42, permutations=1_000, bootstraps=1_000,
    )
    pd.testing.assert_frame_equal(before, rx.build_panel())


def test_injection_never_touches_the_target_or_other_columns(raw_table, carriers):
    carrier = carriers["primary"]
    injected = pc.inject_carrier(raw_table, carrier, 0.40, seed=8)
    others = [column for column in raw_table.columns if column != carrier]
    pd.testing.assert_frame_equal(injected[others], raw_table[others])
    assert injected[pc.TARGET_COLUMN].equals(raw_table[pc.TARGET_COLUMN])


def test_injection_preserves_missingness_exactly(raw_table, carriers):
    for role, carrier in carriers.items():
        injected = pc.inject_carrier(raw_table, carrier, 0.40, seed=13)
        assert injected[carrier].isna().equals(raw_table[carrier].isna()), role
        assert injected[carrier].notna().sum() == raw_table[carrier].notna().sum()


def test_injection_fabricates_no_new_values(raw_table, carriers):
    """Every emitted value must already exist in the column it came from."""
    carrier = carriers["secondary"]
    injected = pc.inject_carrier(raw_table, carrier, 0.40, seed=21)
    for year, group in raw_table.groupby(pc.YEAR_COLUMN):
        source = set(group[carrier].dropna().tolist())
        emitted = set(
            injected.loc[injected[pc.YEAR_COLUMN] == year, carrier].dropna().tolist()
        )
        assert emitted <= source, f"year {year} emitted values absent from the source column"


def test_carrier_rules_select_by_coverage_only(raw_table, carriers):
    features = pc.raw_feature_columns(raw_table)
    per_year = raw_table.groupby(pc.YEAR_COLUMN)[features].apply(lambda block: block.notna().mean())
    overall = raw_table[features].notna().mean()

    primary = carriers["primary"]
    assert bool((per_year[primary] >= 1.0).all())
    earlier_full = [
        c for c in features if c < primary and bool((per_year[c] >= 1.0).all())
    ]
    assert earlier_full == [], f"primary carrier rule skipped {earlier_full}"

    secondary = carriers["secondary"]
    assert float(overall[secondary]) < pc.SECONDARY_COVERAGE_CEILING
    earlier_partial = [
        c for c in features if c < secondary and float(overall[c]) < pc.SECONDARY_COVERAGE_CEILING
    ]
    assert earlier_partial == [], f"secondary carrier rule skipped {earlier_partial}"


def test_carrier_survives_feature_construction(raw_table, carriers):
    panel = rx.build_panel()
    for carrier in carriers.values():
        assert carrier in panel.columns, f"{carrier} is not on the modeled path"


# --------------------------------------------------------------------------- #
# Pre-registration integrity
# --------------------------------------------------------------------------- #
def test_preregistered_constants_match_the_protocol():
    protocol = (REPO_ROOT / "docs" / "thesis" / "PRE_EXPERIMENT_PROTOCOL.md").read_text(
        encoding="utf-8"
    )
    assert "IC_inject ∈ {0.00, 0.10, 0.20, 0.30, 0.40}" in protocol
    assert pc.IC_GRID == (0.00, 0.10, 0.20, 0.30, 0.40)
    assert "MDE_base = 0.182271" in protocol
    assert pc.MDE_BASE == 0.182271
    assert pc.CONFIRMATORY_FAMILY_SIZE == 5
    assert pc.PRIMARY_MODEL == "ridge"
    assert pc.DESCRIPTIVE_REPETITIONS == 200
    assert "R = 200" in protocol
    # ALPHA is pinned against the alpha the protocol fixes, not just against
    # itself: the protocol sets "α = 0.05 two-sided" in its Fixed constants and
    # the Stage 1 amendment's detection rule is `min(1, 5·p_j) < 0.05`. A future
    # drift of pc.ALPHA away from the preregistered 0.05 must fail here.
    assert "α = 0.05 two-sided" in protocol
    assert "min(1, 5·p_j) < 0.05" in protocol
    assert pc.ALPHA == 0.05


def test_sanity_control_is_outside_the_preregistered_grid():
    assert pc.SANITY_IC not in pc.IC_GRID
    assert pc.SANITY_IC > max(pc.IC_GRID)


def test_detection_threshold_reads_the_grid_without_interpolating():
    summaries = [
        {"ic_injected": theta, "detection_rate": rate, "detection_rate_ci_95": [rate, rate]}
        for theta, rate in zip(pc.IC_GRID, (0.05, 0.11, 0.42, 0.86, 0.99))
    ]
    result = pc.detection_threshold(summaries)
    assert result["reached"] is True
    assert result["interpolated"] is False
    # 0.30 is the lowest *grid* level at or above 80%; nothing between 0.20 and
    # 0.30 may be reported, even though the true crossing lies in that interval.
    assert result["lowest_grid_level_reaching_target"] == 0.30


def test_detection_threshold_reports_not_reached_rather_than_extrapolating():
    summaries = [
        {"ic_injected": theta, "detection_rate": rate, "detection_rate_ci_95": [rate, rate]}
        for theta, rate in zip(pc.IC_GRID, (0.04, 0.08, 0.2, 0.4, 0.6))
    ]
    result = pc.detection_threshold(summaries)
    assert result["reached"] is False
    assert result["lowest_grid_level_reaching_target"] is None


def test_detection_threshold_refuses_an_off_grid_arm():
    """The sanity arm must not yield a threshold — that would add a level post hoc."""
    summaries = [
        {"ic_injected": pc.SANITY_IC, "detection_rate": 1.0, "detection_rate_ci_95": [0.98, 1.0]}
    ]
    result = pc.detection_threshold(summaries)
    assert result["reached"] is None
    assert result["lowest_grid_level_reaching_target"] is None
    assert "does not cover the preregistered grid" in result["note"]


def test_confirmatory_gate_requires_monotonicity_and_both_gate_levels():
    def records(recovered: list[float], detected: list[bool]) -> list[dict]:
        return [
            {
                "repetition": pc.CONFIRMATORY_REPETITION,
                "ic_injected": theta,
                "checkpoints": {"ic_final_evaluation": ic},
                "detected": flag,
                "bonferroni_adjusted_p_value": 0.001 if flag else 0.9,
            }
            for theta, ic, flag in zip(pc.IC_GRID, recovered, detected)
        ]

    passing = pc.confirmatory_gate(
        records([0.01, 0.05, 0.12, 0.22, 0.31], [False, False, False, True, True])
    )
    assert passing["passed"] is True

    non_monotone = pc.confirmatory_gate(
        records([0.01, 0.05, 0.12, 0.09, 0.31], [False, False, False, True, True])
    )
    assert non_monotone["monotone_increasing"] is False
    assert non_monotone["passed"] is False

    one_gate_misses = pc.confirmatory_gate(
        records([0.01, 0.05, 0.12, 0.22, 0.31], [False, False, False, False, True])
    )
    assert one_gate_misses["gate_levels_all_reject"] is False
    assert one_gate_misses["passed"] is False


def test_confirmatory_gate_rejects_a_grid_that_is_not_the_preregistered_one():
    records = [
        {
            "repetition": pc.CONFIRMATORY_REPETITION,
            "ic_injected": theta,
            "checkpoints": {"ic_final_evaluation": 0.1},
            "detected": True,
            "bonferroni_adjusted_p_value": 0.001,
        }
        for theta in (0.0, 0.1, 0.2, 0.3, 0.5)
    ]
    with pytest.raises(pc.PositiveControlError, match="preregistered grid"):
        pc.confirmatory_gate(records)


def test_confirmatory_gate_rejects_none_or_degenerate_checkpoint_ic():
    def records(recovered):
        return [
            {
                "repetition": pc.CONFIRMATORY_REPETITION,
                "ic_injected": theta,
                "checkpoints": {"ic_final_evaluation": value},
                "detected": False,
                "bonferroni_adjusted_p_value": 0.9,
            }
            for theta, value in zip(pc.IC_GRID, recovered)
        ]

    for recovered in (
        [0.01, 0.05, None, 0.2, 0.3],
        [0.01, 0.05, 1.0, 0.2, 0.3],
    ):
        with pytest.raises(pc.PositiveControlError, match="finite and strictly inside"):
            pc.confirmatory_gate(records(recovered))


def test_bonferroni_uses_the_declared_family_size(raw_table, carriers):
    record = pc.run_repetition(
        raw_table, carriers["primary"], 0.40,
        injection_seed=6, permutation_seed=42, permutations=1_000, bootstraps=1_000,
    )
    expected = min(1.0, record["permutation_p_value_two_sided"] * pc.CONFIRMATORY_FAMILY_SIZE)
    assert record["bonferroni_adjusted_p_value"] == pytest.approx(expected, rel=1e-9)
    assert record["detected"] is bool(record["bonferroni_adjusted_p_value"] < pc.ALPHA)


# --------------------------------------------------------------------------- #
# Committed artifacts
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def committed_report() -> dict:
    path = OUTPUT_DIR / pc.OUTPUT_FILENAMES["report_json"]
    assert path.is_file(), (
        "Stage 1 report is declared in artifact_registry.json but is absent: "
        f"{path}"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_committed_report_carries_full_provenance(committed_report):
    provenance = committed_report["provenance"]
    assert provenance["git"]["sha"]
    assert provenance["seed"] == prov.seed_for(pc.SLUG)
    assert len(provenance["implementation_sha256"]) == 64
    assert provenance["source_dataset"]["sha256"] == prov.sha256_path(rx.TRAINING_MODELING)


def test_committed_report_used_the_preregistered_design(committed_report):
    design = committed_report["design"]
    assert design["ic_grid"] == list(pc.IC_GRID)
    assert design["model"] == pc.PRIMARY_MODEL
    assert design["confirmatory_family_size"] == pc.CONFIRMATORY_FAMILY_SIZE
    assert design["descriptive_repetitions"] == pc.DESCRIPTIVE_REPETITIONS
    assert design["permutations"] == sig.DEFAULT_PERMUTATIONS


def test_committed_report_keeps_its_claim_safety_block(committed_report):
    safety = committed_report["claim_safety"]
    assert safety["reliable_predictive_edge_established"] is False
    assert safety["investment_value_established"] is False
    assert safety["apparatus_validation_only"] is True
    assert committed_report["limitations"]


def test_committed_markdown_passes_the_shared_claim_safety_validator():
    path = OUTPUT_DIR / pc.OUTPUT_FILENAMES["report_md"]
    assert path.is_file(), (
        "Stage 1 Markdown report is declared in artifact_registry.json but is absent: "
        f"{path}"
    )
    pc.validate_claim_safety_text(path.read_text(encoding="utf-8"))


def test_committed_threshold_is_a_grid_point(committed_report):
    threshold = committed_report["detection_threshold"]["primary"]
    assert threshold["interpolated"] is False
    if threshold["reached"]:
        assert float(threshold["lowest_grid_level_reaching_target"]) in pc.IC_GRID


def test_gate_informativeness_is_recomputed_from_coherent_source_repetitions(committed_report):
    repetitions = pd.read_csv(OUTPUT_DIR / pc.OUTPUT_FILENAMES["repetitions"])
    primary = repetitions[repetitions["arm"] == "primary"]
    source_records = []
    for row in primary.to_dict(orient="records"):
        source_records.append(
            {
                "repetition": int(row["repetition"]),
                "ic_injected": float(row["ic_injected"]),
                "checkpoints": {"ic_final_evaluation": float(row["ic_final_evaluation"])},
                "detected": bool(row["detected"]),
            }
        )
    expected = pc.gate_informativeness(source_records)
    actual = committed_report["gate_informativeness"]
    assert actual["status"] == "POST_RUN_DIAGNOSTIC"
    assert actual["repetitions"] == pc.DESCRIPTIVE_REPETITIONS
    assert actual["probabilities"] == expected["probabilities"]
    assert "do not alter" in actual["note"]


def test_attenuation_artifact_labels_identity_and_background_diagnostics():
    table = pd.read_csv(OUTPUT_DIR / pc.OUTPUT_FILENAMES["attenuation"])
    required = {
        "checkpoint_role",
        "background_ic",
        "background_dominated",
        "background_adjusted_ic_heuristic",
        "background_adjusted_ratio_heuristic",
        "mean_ratio_to_injected",
        "ratio_suppressed_reason",
    }
    assert required <= set(table.columns)
    primary_identity = table[
        (table["arm"] == "primary")
        & table["checkpoint_role"].eq("identity_invariant")
    ]
    assert not primary_identity.empty
    # An identity/invariant checkpoint recovers theta by construction, so BOTH
    # attenuation ratios must be NA there — neither the plain ratio to injected
    # nor the background-adjusted heuristic may be populated, and the row must
    # say why. If either ratio becomes a number, this fails.
    assert primary_identity["mean_ratio_to_injected"].isna().all()
    assert primary_identity["background_adjusted_ratio_heuristic"].isna().all()
    assert (
        primary_identity["ratio_suppressed_reason"]
        == "identity/invariant checkpoint — attenuation ratio not interpreted"
    ).all()
    final_low = table[
        (table["arm"] == "primary")
        & table["checkpoint"].eq("ic_final_evaluation")
        & table["ic_injected"].eq(0.1)
    ].iloc[0]
    assert bool(final_low["background_dominated"])
    assert pd.isna(final_low["mean_ratio_to_injected"])
    assert final_low["ratio_suppressed_reason"] == "theta=0 background dominates"


def test_committed_report_suppresses_identity_invariant_attenuation_interpretations(
    committed_report,
):
    """The JSON report must not turn identity checks into attenuation claims."""
    roles = committed_report["checkpoint_roles"]
    identity_checkpoints = [
        name for name, role in roles.items() if role == "identity_invariant"
    ]
    assert identity_checkpoints

    for arm, summaries in committed_report["detection_curve"].items():
        for summary in summaries:
            for checkpoint in identity_checkpoints:
                assert summary["ratio_to_injected_summary"][checkpoint] is None, (
                    f"{arm} theta={summary['ic_injected']} exposed a ratio for {checkpoint}"
                )
                assert summary["background_adjusted_ic_heuristic"][checkpoint] is None, (
                    f"{arm} theta={summary['ic_injected']} exposed a background-adjusted "
                    f"IC heuristic for {checkpoint}"
                )
                assert summary["background_adjusted_ratio_heuristic"][checkpoint] is None, (
                    f"{arm} theta={summary['ic_injected']} exposed a background-adjusted "
                    f"ratio heuristic for {checkpoint}"
                )
                assert (
                    summary["attenuation_suppression_reason"][checkpoint]
                    == pc.IDENTITY_INVARIANT_SUPPRESSION_REASON
                )
                # Raw observed IC statistics remain available for apparatus checks.
                assert "mean" in summary["checkpoint_summary"][checkpoint]


def test_secondary_population_diagnostic_exposes_changed_n(committed_report):
    population = committed_report["secondary_population"]
    assert population["n_differs"] is True
    assert population["observed_carrier_checkpoint"]["n"] == 120
    assert population["post_imputation_full_cross_section_checkpoint"]["n"] == 240
    assert "not a pure attenuation coefficient" in population["interpretation"]
