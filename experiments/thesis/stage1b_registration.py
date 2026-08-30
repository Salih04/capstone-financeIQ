"""Stage 1b prospective registration constants — machine-checkable.

REGISTRATION ONLY. Importing this module runs nothing, reads no dataset, writes
no file, fits no model, and cannot execute the Stage 1b experiment. It holds the
frozen Stage 1b design constants declared in
``docs/thesis/STAGE_1B_REGISTRATION.md`` so that a focused test can prove
"code constants == registration" before any Stage 1b run exists.

Chronology (stated prominently, per the registration):

* Stage 1b is **prospective but NOT blind** — it was designed *after* Stage 1
  outcomes were known.
* **No Stage 1b outcome has been inspected**, generated, or estimated.
* Stage 1 remains **FAILED AS WRITTEN — INFORMATIVE** and is frozen.
* Stage 2 remains **BLOCKED**.

The seed-derivation framework, the ridge model, the frozen panel, the
walk-forward splits, ``experiments/significance.py``, 10,000 permutations,
10,000 bootstraps, and the Stage-1-operational-rule detection point are all
reused unchanged from Stage 1. The only new grid rung is ``0.35``.
"""

from __future__ import annotations

from types import MappingProxyType

# --------------------------------------------------------------------------- #
# Namespace
# --------------------------------------------------------------------------- #
#: Stage 1 (historical, frozen) output slug.
STAGE_1_SLUG = "positive_control"
#: Stage 1b future isolated output slug. Distinct root; Stage 1 is never
#: overwritten. ``experiments/results_thesis/positive_control_calibration/``
#: must not exist until the single registered run is executed.
STAGE_1B_SLUG = "positive_control_calibration"

#: Future result root declared now but required to be absent until the one
#: registered run. It is intentionally not created by this module.
STAGE_1B_RESULT_ROOT = (
    "experiments/results_thesis/positive_control_calibration/"
)
RESULT_ROOT_EXISTS_AT_REGISTRATION = False

#: The registration document this module is checked against.
REGISTRATION_DOC = "docs/thesis/STAGE_1B_REGISTRATION.md"
PROTOCOL_DOC = "docs/thesis/PRE_EXPERIMENT_PROTOCOL.md"

# --------------------------------------------------------------------------- #
# Prospective grid
# --------------------------------------------------------------------------- #
#: Stage 1 grid, carried over unchanged.
STAGE_1_IC_GRID: tuple[float, ...] = (0.00, 0.10, 0.20, 0.30, 0.40)

#: Stage 1b prospective grid. The ONLY new rung vs Stage 1 is 0.35 — the
#: mechanical midpoint of the already-observed 0.30–0.40 detection bracket,
#: used to localize that bracket. It is NOT a realistic-market IC claim, NOT a
#: SESOI, and NOT tuned to create a pass.
IC_GRID: tuple[float, ...] = (0.00, 0.10, 0.20, 0.30, 0.35, 0.40)
NEW_RUNG: float = 0.35

#: Fixed theta -> level_index map for the seed streams. Legacy Stage 1 indices
#: are preserved EXACTLY (0.00→0 … 0.40→4); 0.35 gets a stable NEW index (5)
#: so no existing Stage 1 seed stream is renumbered. Implementations must use
#: this map (via ``level_index_for``), never ``enumerate(sorted(IC_GRID))`` and
#: never ``enumerate(levels)`` as ``positive_control.run_arm`` does for Stage 1.
#: Wrapped in ``MappingProxyType`` so the frozen mapping is immutable at import;
#: ``level_index_for(theta)`` remains the public lookup path.
LEVEL_INDEX: "MappingProxyType[float, int]" = MappingProxyType(
    {
        0.00: 0,
        0.10: 1,
        0.20: 2,
        0.30: 3,
        0.40: 4,
        0.35: 5,
    }
)

# --------------------------------------------------------------------------- #
# Repetitions — fresh, non-overlapping with Stage 1
# --------------------------------------------------------------------------- #
#: Stage 1 used global repetition ids 0–199 (confirmatory arm = id 0).
STAGE_1_REPETITION_ID_START = 0
STAGE_1_REPETITION_ID_STOP = 200  # exclusive

#: Stage 1b uses global repetition ids 200–599 — 400 FRESH repetitions per
#: level. Stage 1 repetitions are never reused in Stage 1b estimates.
REPETITION_ID_START = 200
REPETITION_ID_STOP = 600  # exclusive
REPETITIONS = 400

#: Stage 1b runs only the primary equity arm. These Stage 1 arms are explicitly
#: historical and excluded: the current_ratio missingness arm and theta=0.90
#: sanity arm.
STAGE_1B_CARRIERS: tuple[str, ...] = ("equity",)
EXCLUDED_STAGE_1_CARRIER_ARMS: tuple[str, ...] = (
    "current_ratio missingness arm",
)
EXCLUDED_STAGE_1_THETA_ARMS: tuple[float, ...] = (0.90,)

# --------------------------------------------------------------------------- #
# Carrier / model / significance machinery — all unchanged from Stage 1
# --------------------------------------------------------------------------- #
#: Same Stage 1 carrier. No new synthetic feature column is added.
CARRIER = "equity"
#: Same Stage 1 injection mechanism: within-year reassignment/permutation of
#: ``equity``'s OWN observed values, same Gaussian-copula relationship
#: (rho = 2*sin(pi*theta/6)), missingness preserved, no fabricated values, no
#: mutation of data/trusted*, data/trusted_clean*, or data/provenance*.
INJECTION_MECHANISM = (
    "within-year permutation of the carrier's own observed values into the order "
    "of a Gaussian-copula latent score s = rho*z + sqrt(1-rho^2)*eps, "
    "rho = 2*sin(pi*theta/6); missingness preserved exactly; no fabricated values"
)

PRIMARY_MODEL = "ridge"
ALPHA = 0.05
# FROZEN LITERAL. This is the historical Stage 1 operating-rule divisor, retained
# unchanged as one fixed operating point solely for comparability of the
# descriptive curve. It is NOT a Stage 1b hypothesis-family size. The Stage 1b
# implementation MUST NOT recompute it from ``len(IC_GRID)``, ``len`` of the
# Stage 1b theta grid, ``positive_control.CONFIRMATORY_FAMILY_SIZE``, or the
# number of Stage 1b levels. The Stage 1b grid has six levels, but the operating
# point stays ``min(1, 5 * p_raw) < 0.05`` (≈ p_raw < 0.01). Recomputing the
# divisor as 6 would silently move the operating point to ≈ p_raw < 0.00833 and
# is FORBIDDEN. By construction 5 == the *Stage 1* grid length and == the
# *Stage 1* CONFIRMATORY_FAMILY_SIZE, and 5 != len(IC_GRID) here.
STAGE1_OPERATIONAL_DIVISOR = 5
PERMUTATIONS = 10_000
BOOTSTRAPS = 10_000

INJECTION_SEED_FORMULA = (
    "base_seed*1_000_003 + level_index*10_007 + repetition"
)
PERMUTATION_SEED_FORMULA = "significance.DEFAULT_SEED + repetition"

#: Base seed for the Stage 1b slug via ``provenance.seed_for``. The Stage 1
#: seed-derivation formulas (``positive_control.derive_injection_seed`` /
#: ``derive_permutation_seed``) are reused unchanged.
BASE_SEED = 42

# --------------------------------------------------------------------------- #
# Detection — primary rule is the Stage 1 operational rule, unchanged
# --------------------------------------------------------------------------- #
#: Primary result name. This is an operating point, not a six-level FWER claim.
PRIMARY_DETECTION_NAME = "Stage-1-operational-rule detection probability"
#: The historical Stage 1 numerical operating rule, retained unchanged.
PRIMARY_DETECTION_RULE = "detected_stage1_rule = min(1, 5 * p_raw) < 0.05"
#: Equivalent per-cell raw threshold under the discrete permutation convention.
PRIMARY_DETECTION_RAW_EQUIVALENT = (
    "p_raw < 0.01 (subject to the discrete permutation p-value convention)"
)

#: SECONDARY diagnostic — clearly labeled, NON-GATING.
SECONDARY_DETECTION_NAME = (
    "raw-p<0.05 detection probability — secondary, non-gating diagnostic"
)
SECONDARY_DIAGNOSTIC_RULE = "raw p < 0.05"
SECONDARY_IS_GATING = False

#: Stage 1b has NO scientific performance PASS/FAIL gate. Only deterministic
#: integrity failures invalidate the run. A scientifically weak calibration
#: result is still a valid experimental result.
HAS_PERFORMANCE_GATE = False

#: Pointwise 95% Wilson intervals for detection probabilities. The permutation
#: seed (``derive_permutation_seed(base_seed, repetition)``) does not depend on
#: theta or level index, so the permutation RNG stream is shared across all theta
#: levels for the same repetition id. These are therefore marginal intervals: no
#: simultaneous or between-theta comparison interval is claimed.
DETECTION_INTERVAL = "pointwise 95% Wilson"

#: Explicit integrity exclusions. These are scientific outcomes, never run
#: validity gates.
INTEGRITY_CHECK_EXCLUSIONS: tuple[str, ...] = (
    "recovered IC magnitude",
    "detection probability",
    "monotonicity",
    "Wilson interval position",
    "Stage 1b theta=0 diagnostic",
    "crossing location",
    "any performance statistic",
)

# --------------------------------------------------------------------------- #
# Status flags
# --------------------------------------------------------------------------- #
#: Prospective but NOT blind — designed after Stage 1 outcomes were known.
PROSPECTIVE_NOT_BLIND = True
#: No Stage 1b outcome was inspected when the registration was written.
NO_STAGE_1B_OUTCOME_INSPECTED = True
#: SESOI remains UNRESOLVED. Do not define a final SESOI from the current
#: literature packet.
SESOI_STATUS = "UNRESOLVED"
#: Stage 1 classification, frozen.
STAGE_1_STATUS = "FAILED AS WRITTEN — INFORMATIVE"
#: Stage 2 gate, unchanged.
STAGE_2_STATUS = "BLOCKED"

# --------------------------------------------------------------------------- #
# Source dataset — registered hash (a mismatch invalidates the run)
# --------------------------------------------------------------------------- #
DATASET_PATH = "data/trusted_clean/modeling_dataset_training_2020_2025.csv"
DATASET_SHA256 = "3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78"

# --------------------------------------------------------------------------- #
# Deterministic invalidation conditions (run validity is governed by this
# CLOSED list ONLY — there is no statistical performance failure condition).
# --------------------------------------------------------------------------- #
MECHANICAL_PROVENANCE_CHECKS: tuple[str, ...] = (
    "registered source dataset hash matches",
    "source remains unchanged",
    "complete 6 × 400 matrix",
    "no missing/duplicate repetition cells",
    "declared seed formulas reproduced",
    "no seed collision",
    "no Stage 1 repetition/seed overlap",
    "Stage 1b writes only to its isolated namespace",
    "Stage 1 historical namespace is not overwritten",
    "no data/trusted*, data/trusted_clean*, or data/provenance* mutation",
    "required outputs finite",
    "replay deterministic",
    "runtime override restored on every exit path",
)

MECHANISM_INVARIANT_CHECKS: tuple[str, ...] = (
    "carrier observed-value multiset preserved within year",
    "carrier missingness mask preserved",
    "targets unchanged",
    "non-carrier features unchanged",
    "equity reaches the modeled feature path",
    "identity/invariant checkpoint ICs agree within the already governed Stage 1 numerical tolerance",
    "ridge prediction IC and final evaluation IC agree within the already governed Stage 1 numerical tolerance",
)

DETERMINISTIC_INVALIDATION_CONDITIONS: tuple[str, ...] = (
    *MECHANICAL_PROVENANCE_CHECKS,
    *MECHANISM_INVARIANT_CHECKS,
)


def stage1b_repetition_ids() -> tuple[int, ...]:
    """The 400 fresh global repetition ids Stage 1b will use (200–599)."""
    return tuple(range(REPETITION_ID_START, REPETITION_ID_STOP))


def stage1_repetition_ids() -> tuple[int, ...]:
    """The Stage 1 global repetition ids (0–199), for non-overlap checks."""
    return tuple(range(STAGE_1_REPETITION_ID_START, STAGE_1_REPETITION_ID_STOP))


def level_index_for(theta: float) -> int:
    """Return the frozen seed level index; never infer it from display order."""
    try:
        return LEVEL_INDEX[theta]
    except KeyError as exc:
        raise ValueError(f"theta {theta!r} is not in the registered grid") from exc
