"""Machine-checkable guards for the Stage 1b prospective registration.

These tests check the registration contract only. They do not implement or run
Stage 1b, create its future result root, or modify the historical Stage 1.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from experiments import significance as sig
from experiments.thesis import positive_control as stage1
from experiments.thesis import provenance as prov
from experiments.thesis import stage1b_registration as reg

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRATION_DOC = REPO_ROOT / reg.REGISTRATION_DOC
PROTOCOL_DOC = REPO_ROOT / reg.PROTOCOL_DOC
STAGE_1B_OUTPUT_DIR = REPO_ROOT / reg.STAGE_1B_RESULT_ROOT.rstrip("/")
STAGE_1_REPORT = REPO_ROOT / "experiments/results_thesis/positive_control/positive_control_report.json"
STAGE_1_IMPLEMENTATION = REPO_ROOT / "experiments/thesis/positive_control.py"
STAGE_1_OUTPUT_ROOT = REPO_ROOT / "experiments/results_thesis/positive_control"


def compact(text: str) -> str:
    """Normalize Markdown wrapping for semantic assertions."""
    return " ".join(text.replace("**", "").split())


@pytest.fixture(scope="module")
def doc() -> str:
    return REGISTRATION_DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def protocol() -> str:
    return PROTOCOL_DOC.read_text(encoding="utf-8")


def test_registered_grid_scope_and_repetition_count(doc):
    assert reg.IC_GRID == (0.00, 0.10, 0.20, 0.30, 0.35, 0.40)
    assert "{0.00, 0.10, 0.20, 0.30, 0.35, 0.40}" in doc
    assert reg.NEW_RUNG == 0.35
    assert set(reg.IC_GRID) - set(reg.STAGE_1_IC_GRID) == {0.35}
    assert reg.STAGE_1_IC_GRID == stage1.IC_GRID
    assert reg.REPETITIONS == 400
    assert reg.stage1b_repetition_ids() == tuple(range(200, 600))
    assert "R=400" in doc or "R = 400" in doc
    assert "200..599" in doc or "200 … 599" in doc


def test_only_equity_arm_is_registered_and_historical_arms_are_excluded(doc):
    assert reg.CARRIER == "equity"
    assert reg.STAGE_1B_CARRIERS == ("equity",)
    assert reg.EXCLUDED_STAGE_1_CARRIER_ARMS == ("current_ratio missingness arm",)
    assert reg.EXCLUDED_STAGE_1_THETA_ARMS == (0.90,)
    assert "only" in doc.lower() and "`equity`" in doc
    assert "`current_ratio` missingness arm" in doc
    assert "theta=0.90 sanity arm" in doc


def test_primary_model_and_stage1_machinery_are_preserved(doc, protocol):
    assert reg.PRIMARY_MODEL == "ridge" == stage1.PRIMARY_MODEL
    assert reg.ALPHA == 0.05 == stage1.ALPHA
    assert reg.PERMUTATIONS == sig.DEFAULT_PERMUTATIONS == 10_000
    assert reg.BOOTSTRAPS == sig.DEFAULT_BOOTSTRAPS == 10_000
    assert "`ridge`" in doc
    assert "α = 0.05 two-sided" in protocol


def test_operational_divisor_is_not_a_stage1b_family_size(doc):
    assert reg.STAGE1_OPERATIONAL_DIVISOR == 5
    assert not hasattr(reg, "BONFERRONI_FAMILY")
    assert "historical Stage 1" in doc
    assert "fixed operating point" in doc
    normalized = compact(doc)
    assert "six theta levels are not a hypothesis family" in normalized
    assert "no family-wise-error-control claim across its six levels" in normalized
    assert "Bonferroni across the 5" not in doc
    assert "Bonferroni-×5" not in doc


def test_primary_detection_rule_is_the_stage1_operating_point(doc, protocol):
    assert reg.PRIMARY_DETECTION_NAME == "Stage-1-operational-rule detection probability"
    assert reg.PRIMARY_DETECTION_RULE == "detected_stage1_rule = min(1, 5 * p_raw) < 0.05"
    assert reg.PRIMARY_DETECTION_RAW_EQUIVALENT.startswith("p_raw < 0.01")
    assert "Stage-1-operational-rule detection probability" in doc
    assert "detected_stage1_rule = min(1, 5 * p_raw) < 0.05" in doc
    assert "p_raw < 0.01" in doc
    assert "min(1, 5·p_j) < 0.05" in protocol

    # The strict inequality and the discrete p-value convention make p=.01
    # non-detecting, so the numerical rule is exactly the raw-p<.01 point.
    for p_raw in (0.0, 0.0099, 0.01, 0.0101, 0.0499, 0.05, 1.0):
        by_operating_rule = min(1.0, reg.STAGE1_OPERATIONAL_DIVISOR * p_raw) < reg.ALPHA
        assert by_operating_rule == (p_raw < 0.01)


def test_secondary_raw_p_diagnostic_is_non_gating(doc):
    assert reg.SECONDARY_DETECTION_NAME == (
        "raw-p<0.05 detection probability — secondary, non-gating diagnostic"
    )
    assert reg.SECONDARY_DIAGNOSTIC_RULE == "raw p < 0.05"
    assert reg.SECONDARY_IS_GATING is False
    assert "raw-p<0.05 detection probability — secondary, non-gating diagnostic" in doc
    assert "not a gate" in doc


def test_no_scientific_performance_gate_or_stage1_gate_reuse(doc):
    assert reg.HAS_PERFORMANCE_GATE is False
    normalized = compact(doc)
    assert "no scientific performance PASS/FAIL gate" in normalized
    assert "scientific result, not an integrity failure" in normalized
    assert "does not compute an 80%-detection gate" in normalized
    for historical_gate in (
        "confirmatory_gate",
        "gate_informativeness",
        "strict-monotonicity pass/fail",
        "GATE_LEVELS",
    ):
        assert historical_gate in normalized
    assert "No Stage 1b threshold crossing may be used as a success criterion" in normalized


def test_theta035_wording_is_mechanical_not_tuned(doc):
    section = compact(doc[doc.index("## Status of the 0.35 rung"):])
    assert "not derived from `MDE_BASE`" in section
    assert "not a realistic market IC" in section
    assert "not a SESOI" in section
    assert "not a tuned pass point" in section
    assert "mechanical midpoint" in section
    assert "Stage 1 descriptive reference" in section


def test_status_when_written_discloses_known_stage1_outcomes(doc):
    status = compact(doc[doc.index("## Status when this registration was written"):doc.index("## Scope and arm registration")])
    assert "FAILED AS WRITTEN — INFORMATIVE" in status
    assert "outcomes had already been inspected" in status
    assert "0.615 at θ = 0.30" in status
    assert "0.930 at θ = 0.40" in status
    assert "0.195" in status
    assert "theta=0 background/final evaluated IC was non-zero" in status
    assert "known interpretation" in status
    assert "prospective but NOT blind" in status
    assert "adding theta=0.35" in status
    assert "increasing from R=200 to R=400" in status
    assert "cannot flip a Stage 1b verdict" in status


def test_sesoi_and_claim_boundary_are_explicit(doc):
    assert reg.SESOI_STATUS == "UNRESOLVED"
    for phrase in (
        "does not establish, assume, estimate, or imply",
        "a realistic BIST IC magnitude",
        "a universal IC benchmark",
        "a smallest effect size of interest",
        "SESOI remains **UNRESOLVED**",
        "theta` is a synthetic copula design constant",
        "theta=0` is not a “zero-signal market world”",
        "real non-carrier features remain",
        "apparatus characterization only",
    ):
        assert phrase in doc


def test_fixed_level_index_mapping_is_exact_and_explicit(doc):
    assert reg.LEVEL_INDEX == {
        0.00: 0,
        0.10: 1,
        0.20: 2,
        0.30: 3,
        0.40: 4,
        0.35: 5,
    }
    assert reg.LEVEL_INDEX[0.40] == 4
    assert reg.LEVEL_INDEX[0.35] == 5
    assert tuple(reg.level_index_for(theta) for theta in reg.IC_GRID) == (0, 1, 2, 3, 5, 4)
    assert "theta-to-level-index mapping" in doc
    assert "0.40 | 4" in doc
    assert "0.35 | 5" in doc


def test_grid_iteration_cannot_silently_renumber_legacy_streams(doc):
    # Display order is numeric, while seed order is the frozen explicit map.
    naive_sorted_indices = {theta: i for i, theta in enumerate(sorted(reg.IC_GRID))}
    assert naive_sorted_indices[0.40] == 5
    assert reg.level_index_for(0.40) == 4
    assert reg.level_index_for(0.35) == 5
    assert "must not" in doc and "enumerate(sorted_grid)" in doc
    assert "silently move legacy theta=0.40 from index 4 to index 5" in doc


def test_seed_formulas_and_repetition_ranges_are_machine_checked(doc):
    assert reg.BASE_SEED == 42
    assert reg.INJECTION_SEED_FORMULA == (
        "base_seed*1_000_003 + level_index*10_007 + repetition"
    )
    assert reg.PERMUTATION_SEED_FORMULA == "significance.DEFAULT_SEED + repetition"
    assert "base seed is **42**" in doc
    assert reg.stage1_repetition_ids() == tuple(range(0, 200))
    assert reg.stage1b_repetition_ids() == tuple(range(200, 600))
    assert "level indices 0..4 × repetition IDs 0..199" in doc
    assert "new index 5 × repetition IDs 200..599" in doc
    assert "fresh repetition-ID range" in doc

    for theta in reg.IC_GRID:
        for repetition in (200, 599):
            expected = reg.BASE_SEED * 1_000_003 + reg.level_index_for(theta) * 10_007 + repetition
            assert stage1.derive_injection_seed(reg.BASE_SEED, reg.level_index_for(theta), repetition) == expected
    assert stage1.derive_permutation_seed(reg.BASE_SEED, 200) == sig.DEFAULT_SEED + 200


def test_stage1b_seed_streams_have_no_collision_or_stage1_overlap():
    stage1b_injection = {
        stage1.derive_injection_seed(reg.BASE_SEED, reg.level_index_for(theta), repetition)
        for theta in reg.IC_GRID
        for repetition in reg.stage1b_repetition_ids()
    }
    assert len(stage1b_injection) == 6 * 400

    stage1_injection = {
        stage1.derive_injection_seed(stream_seed, level_index, repetition)
        for stream_seed in (reg.BASE_SEED, reg.BASE_SEED + 1, reg.BASE_SEED + 2)
        for level_index in range(len(stage1.IC_GRID))
        for repetition in reg.stage1_repetition_ids()
    }
    stage1b_permutation = {
        stage1.derive_permutation_seed(reg.BASE_SEED, repetition)
        for repetition in reg.stage1b_repetition_ids()
    }
    stage1_permutation = {
        stage1.derive_permutation_seed(reg.BASE_SEED, repetition)
        for repetition in reg.stage1_repetition_ids()
    }

    all_stage1b_seeds = stage1b_injection | stage1b_permutation
    assert len(all_stage1b_seeds) == len(stage1b_injection) + len(stage1b_permutation)
    assert stage1b_injection.isdisjoint(stage1_injection)
    assert stage1b_permutation.isdisjoint(stage1_permutation)
    assert all_stage1b_seeds.isdisjoint(stage1_injection | stage1_permutation)


def test_stage1b_root_is_distinct_declared_and_absent(doc):
    assert reg.STAGE_1B_SLUG == "positive_control_calibration"
    assert reg.STAGE_1B_SLUG != reg.STAGE_1_SLUG == stage1.SLUG
    assert reg.STAGE_1B_RESULT_ROOT == "experiments/results_thesis/positive_control_calibration/"
    assert reg.RESULT_ROOT_EXISTS_AT_REGISTRATION is False
    assert reg.STAGE_1B_SLUG in prov.EXPERIMENT_SLUGS
    assert prov.seed_for(reg.STAGE_1B_SLUG) == 42
    assert STAGE_1B_OUTPUT_DIR != STAGE_1_OUTPUT_ROOT
    # IMPLEMENTATION-PHASE GUARD (result root absence). The implementation commit
    # adds the runner and the governance wiring but does NOT run Stage 1b, so this
    # guard survives it unchanged and sunsets only when the one governed run
    # executes. See tests/test_thesis_stage1b_implementation.py.
    assert not STAGE_1B_OUTPUT_DIR.exists()
    assert "must be absent now" in doc
    assert "does not create the result root" in doc


def test_governance_wiring_is_present_and_the_run_has_not_happened():
    """The inverted registration-phase guard: wiring present, run still absent.

    This replaces the pre-implementation ``..._are_deferred`` guard in the same
    commit that added the runner, the ``thesis-stage1b`` target, the
    ``governed_roots`` entry, and the per-artifact ownership contracts — exactly
    the sunset the registration's "Registration-phase guards" section requires.
    It is not a weakening: the pre-implementation absences are replaced by the
    stricter presence contract, and the one absence that must survive until the
    governed run — the result root — is asserted here too.
    """
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    registry = json.loads((REPO_ROOT / "artifact_registry.json").read_text(encoding="utf-8"))

    # 1. the runner exists and 2. the Makefile target exists.
    assert (REPO_ROOT / "experiments/thesis/positive_control_calibration.py").is_file()
    assert "thesis-stage1b:" in makefile
    assert (
        "PYTHONPATH=. python experiments/thesis/positive_control_calibration.py --run"
        in makefile
    )

    # 3. the governed root is registered.
    assert reg.STAGE_1B_RESULT_ROOT.rstrip("/") in registry["governed_roots"]

    # 4. one ownership contract per emitted governed output, none of which may
    #    sit in entries[] yet, because entries[] requires a real file on disk.
    prospective = {
        entry["path_or_glob"] for entry in registry["prospective_entries"]
    }
    assert prospective and all(
        path.startswith(reg.STAGE_1B_RESULT_ROOT) for path in prospective
    )
    assert all(
        entry["generator_command"] == "make thesis-stage1b"
        for entry in registry["prospective_entries"]
    )
    assert not any(
        entry["path_or_glob"].startswith(reg.STAGE_1B_RESULT_ROOT)
        for entry in registry["entries"]
    )

    # 5. and the run itself has still not happened.
    assert not STAGE_1B_OUTPUT_DIR.exists()


def test_closed_integrity_contract_has_only_machine_declared_conditions(doc):
    assert len(reg.MECHANICAL_PROVENANCE_CHECKS) == 13
    assert len(reg.MECHANISM_INVARIANT_CHECKS) == 7
    assert reg.DETERMINISTIC_INVALIDATION_CONDITIONS == (
        reg.MECHANICAL_PROVENANCE_CHECKS + reg.MECHANISM_INVARIANT_CHECKS
    )
    normalized = compact(doc).lower()
    for condition in reg.DETERMINISTIC_INVALIDATION_CONDITIONS:
        assert condition.lower() in normalized
    assert "complete and closed list" in doc
    assert "### A. Mechanical / provenance checks" in doc
    assert "### B. Mechanism invariant checks" in doc
    assert doc.index("### A. Mechanical / provenance checks") < doc.index(
        "### B. Mechanism invariant checks"
    )
    assert "No other statistical or scientific condition can" in doc


def test_integrity_exclusions_are_explicit_and_outcome_blind(doc):
    exclusions = (
        "recovered IC magnitude",
        "detection probability",
        "monotonicity",
        "Wilson interval position",
        "the Stage 1b theta=0 diagnostic",
        "a crossing location",
        "any performance statistic",
    )
    assert tuple(
        item for item in reg.INTEGRITY_CHECK_EXCLUSIONS
    ) == (
        "recovered IC magnitude",
        "detection probability",
        "monotonicity",
        "Wilson interval position",
        "Stage 1b theta=0 diagnostic",
        "crossing location",
        "any performance statistic",
    )
    normalized = compact(doc)
    for exclusion in exclusions:
        assert exclusion in normalized
    assert "No integrity check may inspect or threshold" in normalized
    assert "flat," in normalized
    assert "non-monotone" in normalized
    assert "high-background" in normalized
    assert "scientific result" in normalized
    assert "not an integrity failure" in normalized
    assert "hidden performance gate" in normalized


def test_fixed_panel_wording_and_pointwise_interval_boundary(doc, protocol):
    normalized = compact(doc)
    for phrase in (
        "Across Stage 1b repetitions the realized equity panel is fixed",
        "injection-draw randomness",
        "permutation Monte-Carlo randomness",
        "equity universe",
        "market panel",
        "time period",
        "PIT universe",
        "monthly sample",
        "not unconditional market-level power intervals",
        "shared across theta levels for the same repetition",
        "do not constitute simultaneous",
        "between-level comparison intervals",
    ):
        assert phrase in normalized
    assert "pointwise Wilson" in normalized
    assert "realized equity panel is fixed" in compact(protocol)


def test_r400_precision_language_does_not_claim_exact_precision(doc, protocol):
    assert "about **4.9 percentage-point half-width**" in doc
    assert "about **3.9 percentage-point half-width**" in doc
    assert "improves grid-point precision but does not identify an exact" in doc
    assert "No interpolation is confirmatory" in doc
    assert "4.9 percentage points" in compact(protocol)
    assert "3.9 percentage points" in compact(protocol)
    assert "±3pp" not in doc


def test_single_run_replay_crash_and_amendment_rules_are_frozen(doc, protocol):
    normalized = compact(doc)
    for phrase in (
        "one governed prospective Stage 1b run",
        "seed schedule is frozen",
        "deterministic replay with identical settings is verification",
        "execution crash may be repeated only with identical registered settings",
        "both attempts must be recorded",
        "post-outcome change",
        "grid, R, carrier, model, seed policy, detection rule, or inference",
        "dated amendment",
    ):
        assert phrase in normalized
    assert "deterministic replay with identical settings" in compact(protocol)


def test_status_and_stage1_primary_carrier_match_governed_report(doc):
    payload = json.loads(STAGE_1_REPORT.read_text(encoding="utf-8"))
    assert payload["confirmatory"]["passed"] is False
    assert payload["design"]["carriers"]["primary"] == "equity"
    assert payload["gate_informativeness"]["probabilities"]["original_stage_1_gate_passes"] == 0.195
    assert payload["background_ic_theta_zero"] != 0.0
    assert "FAILED AS WRITTEN — INFORMATIVE" in doc


def test_registration_module_import_remains_inert():
    dataset = REPO_ROOT / reg.DATASET_PATH
    before = hashlib.sha256(dataset.read_bytes()).hexdigest()
    assert before == reg.DATASET_SHA256
    script = (
        "import hashlib, pathlib\n"
        f"dataset = pathlib.Path({str(dataset)!r})\n"
        "before = hashlib.sha256(dataset.read_bytes()).hexdigest()\n"
        "import experiments.thesis.stage1b_registration as reg\n"
        "after = hashlib.sha256(dataset.read_bytes()).hexdigest()\n"
        "assert after == before\n"
        "assert not hasattr(reg, 'run')\n"
        "assert not hasattr(reg, 'run_repetition')\n"
        "assert not hasattr(reg, 'inject_carrier')\n"
        f"assert not pathlib.Path({str(STAGE_1B_OUTPUT_DIR)!r}).exists()\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert hashlib.sha256(dataset.read_bytes()).hexdigest() == before


def test_registration_module_has_no_pipeline_or_statistical_imports():
    import ast

    source = (REPO_ROOT / "experiments/thesis/stage1b_registration.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    # ``types`` (MappingProxyType) is stdlib and neither pipeline nor
    # statistical; it only freezes the LEVEL_INDEX mapping.
    assert set(imported) <= {"__future__", "types"}
    assert "pandas" not in source
    assert "numpy" not in source


def test_stage1_historical_implementation_and_artifacts_are_untouched():
    tracked_paths = [
        STAGE_1_IMPLEMENTATION,
        STAGE_1_OUTPUT_ROOT / "positive_control_report.json",
        STAGE_1_OUTPUT_ROOT / "positive_control_report.md",
        STAGE_1_OUTPUT_ROOT / "repetitions.csv",
        STAGE_1_OUTPUT_ROOT / "detection_curve.csv",
        STAGE_1_OUTPUT_ROOT / "attenuation_by_stage.csv",
        STAGE_1_OUTPUT_ROOT / "artifact_manifest.json",
    ]
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    changed_paths = {line[3:] for line in status if len(line) >= 4}
    for path in tracked_paths:
        relative = path.relative_to(REPO_ROOT).as_posix()
        assert relative not in changed_paths
    assert STAGE_1_IMPLEMENTATION.exists()
    assert STAGE_1_OUTPUT_ROOT.exists()


# --------------------------------------------------------------------------- #
# H1 — the operating divisor 5 is frozen against grid-length drift
# --------------------------------------------------------------------------- #
def test_operational_divisor_is_frozen_and_not_a_grid_length(doc):
    # Cross-module: 5 is the historical Stage 1 rule literal, equal to the
    # Stage 1 grid length / family size but NOT the Stage 1b grid length.
    assert reg.STAGE1_OPERATIONAL_DIVISOR == 5
    assert stage1.CONFIRMATORY_FAMILY_SIZE == 5
    assert reg.STAGE1_OPERATIONAL_DIVISOR == stage1.CONFIRMATORY_FAMILY_SIZE
    assert stage1.CONFIRMATORY_FAMILY_SIZE == len(stage1.IC_GRID)
    assert reg.STAGE1_OPERATIONAL_DIVISOR != len(reg.IC_GRID)
    assert len(reg.IC_GRID) == 6

    # Recomputing the divisor from the six-level grid would move the operating
    # point from ~p_raw<0.01 to ~p_raw<0.00833 — forbidden.
    normalized = compact(doc)
    assert "frozen literal inherited from the historical Stage 1 operating rule" in normalized
    assert "must not derive this divisor from `len(IC_GRID)`" in normalized
    assert "approximately `p_raw < 0.00833`" in normalized
    assert "not a six-level FWER procedure" in normalized


# --------------------------------------------------------------------------- #
# M1 — the real enumerate() drift site is named, and one real Stage 1 seed is
# carried forward against the actual Stage 1 derivation function.
# --------------------------------------------------------------------------- #
def test_named_enumerate_drift_site_is_disclosed(doc):
    normalized = compact(doc)
    assert "positive_control.run_arm()" in normalized
    assert "derives `level_index` with `enumerate(levels)`" in normalized
    assert "0.35 -> 4" in normalized and "0.40 -> 5" in normalized
    assert "stage1b_registration.LEVEL_INDEX" in normalized
    assert "stage1b_registration.level_index_for(theta)" in normalized
    # Report/display order may be numeric; only seed derivation is mapping-based.
    assert "scientific and report ordering may be numeric" in normalized
    assert "only the **seed derivation** is required to be mapping-based" in doc


def test_stage1_injection_seed_carry_forward_binds_to_real_function():
    # Pin a real Stage 1 seed example using the ACTUAL Stage 1 derivation
    # function (not a re-implemented formula): theta=0.40 -> level_index 4,
    # repetition 200.
    assert reg.level_index_for(0.40) == 4
    assert stage1.derive_injection_seed(reg.BASE_SEED, reg.level_index_for(0.40), 200) == 42_040_354
    # A naive enumerate(sorted(grid)) would misroute 0.40 to index 5 and break
    # this legacy stream identity.
    naive_index = {t: i for i, t in enumerate(sorted(reg.IC_GRID))}[0.40]
    assert naive_index == 5
    assert stage1.derive_injection_seed(reg.BASE_SEED, naive_index, 200) != 42_040_354


def test_permutation_seed_does_not_depend_on_theta_or_level(doc):
    # derive_permutation_seed's signature has no theta/level parameter, so the
    # permutation RNG stream is shared across theta levels for a repetition.
    import inspect

    params = list(inspect.signature(stage1.derive_permutation_seed).parameters)
    assert params == ["base_seed", "repetition"]
    for repetition in (200, 350, 599):
        assert stage1.derive_permutation_seed(reg.BASE_SEED, repetition) == sig.DEFAULT_SEED + repetition
    normalized = compact(doc)
    assert "permutation seed" in normalized
    assert "does not depend on theta" in normalized
    assert "shared across theta levels for the same repetition" in normalized
    assert "marginal" in normalized


# --------------------------------------------------------------------------- #
# M2 — governance wiring required before the first run
# --------------------------------------------------------------------------- #
def test_governance_wiring_before_first_run_is_complete(doc):
    normalized = compact(doc)
    for phrase in (
        "Governance wiring required before the first Stage 1b execution",
        "the Stage 1b runner",
        "a Makefile target (e.g. `thesis-stage1b`)",
        "`governed_roots`",
        "one `artifact_registry.json` entry for **every** emitted governed output".replace("**", ""),
        "tests proving registry coverage / no orphan outputs",
        "is **insufficient**".replace("**", ""),
        "The first Stage 1b run is **forbidden** until this governance wiring is committed".replace("**", ""),
    ):
        assert phrase in normalized


# --------------------------------------------------------------------------- #
# M3 — registration-phase guard sunset is declared
# --------------------------------------------------------------------------- #
def test_registration_phase_guard_sunset_is_declared(doc):
    normalized = compact(doc)
    assert "Registration-phase guards — sunset on implementation" in normalized
    assert "registration-phase only" in normalized
    assert "must replace/invert them in the same commit" in normalized
    for future_state in (
        "the runner exists",
        "the Makefile target exists",
        "the governed root exists in `artifact_registry.json`",
    ):
        assert future_state in normalized
    assert "Execution is still **not performed**".replace("**", "") in normalized
    assert "must not be deleted or weakened before" in normalized
    # The sunset has now happened for the wiring guards: the runner and the
    # Makefile target exist. The result-root absence is the one guard that must
    # survive the implementation commit and sunset only at the governed run.
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "thesis-stage1b:" in makefile
    assert (REPO_ROOT / "experiments/thesis/positive_control_calibration.py").is_file()
    assert not STAGE_1B_OUTPUT_DIR.exists()


# --------------------------------------------------------------------------- #
# M4 — Git chronology anchor wording is accurate (reviewed after 2026-08-29)
# --------------------------------------------------------------------------- #
def test_git_chronology_anchor_wording_is_accurate(doc):
    normalized = compact(doc)
    assert "Initial Stage 1b design work began on 2026-08-29" in normalized
    assert "committed before any Stage 1b implementation or run" in normalized
    assert "the authoritative prospective Git chronology anchor" in normalized
    assert "the reviewed-registration date is 2026-08-31" in normalized
    assert "Git-proven by this registration commit preceding the implementation and run commits" in normalized
    assert "No Stage 1b implementation or run commit SHA exists yet" in normalized


# --------------------------------------------------------------------------- #
# Low — Stage 1 detection disclosures are backed by the governed artifact
# --------------------------------------------------------------------------- #
def test_stage1_detection_disclosures_match_governed_artifact(doc):
    payload = json.loads(STAGE_1_REPORT.read_text(encoding="utf-8"))
    curve = {
        round(float(row["ic_injected"]), 2): float(row["detection_rate"])
        for row in payload["detection_curve"]["primary"]
    }
    assert curve[0.30] == pytest.approx(0.615, abs=5e-4)
    assert curve[0.40] == pytest.approx(0.930, abs=5e-4)
    # Prose must agree with the artifact it cites.
    assert "0.615 at θ = 0.30" in doc
    assert "0.930 at θ = 0.40" in doc
    # Existing artifact-backed checks stay green.
    assert payload["gate_informativeness"]["probabilities"]["original_stage_1_gate_passes"] == 0.195
    assert payload["background_ic_theta_zero"] != 0.0


# --------------------------------------------------------------------------- #
# Low — pin the remaining semantic registration constants
# --------------------------------------------------------------------------- #
def test_semantic_registration_constants_are_pinned(doc):
    assert reg.PROSPECTIVE_NOT_BLIND is True
    assert reg.NO_STAGE_1B_OUTCOME_INSPECTED is True
    assert reg.STAGE_1_STATUS == "FAILED AS WRITTEN — INFORMATIVE"
    assert reg.STAGE_2_STATUS == "BLOCKED"
    assert reg.DETECTION_INTERVAL == "pointwise 95% Wilson"
    assert reg.INJECTION_MECHANISM.startswith(
        "within-year permutation of the carrier's own observed values"
    )
    assert "rho = 2*sin(pi*theta/6)" in reg.INJECTION_MECHANISM

    normalized = compact(doc)
    assert "prospective but NOT blind".lower() in normalized.lower()
    assert reg.STAGE_1_STATUS in doc
    assert "Stage 2 remains **BLOCKED**".replace("**", "") in normalized
    assert "rho = 2*sin(pi*theta/6)" in normalized
    assert "Pointwise 95% Wilson" in doc


# --------------------------------------------------------------------------- #
# Low — LEVEL_INDEX is immutable at import; level_index_for stays the API
# --------------------------------------------------------------------------- #
def test_level_index_mapping_is_immutable():
    from types import MappingProxyType

    assert isinstance(reg.LEVEL_INDEX, MappingProxyType)
    with pytest.raises(TypeError):
        reg.LEVEL_INDEX[0.99] = 9  # type: ignore[index]
    with pytest.raises(TypeError):
        del reg.LEVEL_INDEX[0.00]  # type: ignore[misc]
    assert reg.LEVEL_INDEX == {0.00: 0, 0.10: 1, 0.20: 2, 0.30: 3, 0.40: 4, 0.35: 5}
    assert reg.level_index_for(0.35) == 5
    with pytest.raises(ValueError):
        reg.level_index_for(0.99)
