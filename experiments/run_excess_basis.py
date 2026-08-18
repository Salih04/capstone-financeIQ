"""Generate isolated excess-target prediction dumps and significance evidence.

R3-TGT-01 is an additive research replay.  It fits the frozen nine-model
walk-forward harness against ``next_year_excess_return_vs_bist100`` and writes
only under ``experiments/results_excess``.  Canonical nominal artifacts are
read-only.  Aggregate excess metrics are reconstructed from the persisted
row-level dumps, then compared with the existing canonical target leaderboard;
disagreement is reported rather than patched.

Three reporting rules are enforced here rather than inherited from
``experiments/significance.py``:

* the bootstrap resamples **whole ticker trajectories** (one sampled ticker
  vector shared by every evaluation year), not ticker-year rows drawn
  independently within each year;
* the six prespecified ML-family members are reported symmetrically, with no
  model selected or privileged by any observed outcome statistic; and
* the power section is derived from the persisted dumps, so the reported current
  design is the design that was actually evaluated.

Because ``significance.build_report`` internally picks the family member with
the smallest raw permutation p-value, it is **never called** from this module.
Deleting the selected field afterwards would still mean the selection ran, so
the report is assembled here from per-model, non-selecting analyses instead.
The shared module still owns the permutation test, the equal-year statistic, the
Bonferroni convention, and the Fisher-z power primitives; those numbers are
consumed unchanged so the nominal artifacts it also serves are untouched.

Human review added five further reporting obligations, all of which are
evidence-driven rather than asserted:

* an **estimand-invariance audit** proving programmatically that the trusted
  excess target subtracts one common benchmark value inside each evaluation
  year, so within-year ranks — and therefore the Spearman IC estimand — are
  unchanged by the subtraction;
* a **second, distinct permutation analysis**.  The prespecified
  ``primary_independent_within_year_permutation`` is preserved byte-for-byte;
  the post-review ``trajectory_preserving_ticker_permutation_sensitivity``
  permutes ticker identities once per draw and reuses that single mapping in
  every evaluation year, so realized-outcome trajectories move as complete
  blocks.  The sensitivity never replaces or renames the primary analysis;
* **symmetric side-by-side reporting** of both analyses for all six family
  members, with no selected, headline, or minimum-p model;
* an explicit **cross-basis multiplicity** disclosure: nominal return is the
  sole confirmatory family and every alternative basis, this one included, is
  exploratory robustness; and
* evidence-level statements about the **coincident baselines**, the
  **predominantly negative IC signs**, and the **scope of the compact
  human-review package**.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import fnmatch
import json
import math
import os
import platform
import re
import stat
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.data_collection import derive_alternative_targets as alt
from experiments import run_experiments as exp
from experiments import significance
from experiments.run_alternative_targets import _prediction_rows

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "experiments" / "results_excess"
TARGET_COLUMN = "next_year_excess_return_vs_bist100"
BASIS_ID = "excess_vs_bist100"
BASIS_LABEL = "Excess return vs BIST100 (nominal TRY, percentage points)"
GENERATOR = "experiments/run_excess_basis.py"
REGENERATION_COMMAND = "make research-excess"
CANONICAL_TARGET_LEADERBOARD = (
    ROOT / "experiments" / "results" / "leaderboard_by_target.csv"
)
# Context only: the nominal basis evaluates a different, wider cohort. This is
# never the current excess-basis design, which is derived from the dumps.
NOMINAL_ROWS_PER_TEST_YEAR = 80

# The only evaluation years this isolated task may analyse.  Cluster keys are
# validated against this exact set before any integer conversion.
EXPECTED_EVALUATION_YEARS = (2023, 2024, 2025)

# Bounded temporary-output policy.  The default repository destination is
# OUTPUT_DIR; the only other accepted destination is a dedicated directory under
# the operating system's resolved temporary root.
TEMP_OUTPUT_PREFIX = "financeiq-r3-tgt-01-"

# Prespecified reporting order.  Both tuples are fixed before any excess-target
# result is observed and never reordered by an outcome statistic.
FROZEN_ML_FAMILY = tuple(significance.ML_MODELS)
FROZEN_BASELINES = tuple(
    name for name in exp.MODELS if name not in set(FROZEN_ML_FAMILY)
)

BOOTSTRAP_UNIT = "ticker_cluster"
BOOTSTRAP_CLUSTER_KEY = "ticker"
BOOTSTRAP_INTERVAL_CONVENTION = "percentile; 2.5th and 97.5th quantiles of the resample distribution"
MIN_CLUSTERS = 3
MIN_VALID_RESAMPLE_FRACTION = 0.9
MIN_VALID_RESAMPLES = 1_000

# ---------------------------------------------------------------------------
# Task-specific regeneration-recipe provenance
# ---------------------------------------------------------------------------
#
# R3-TGT-01 depends on its own regeneration *recipe*, not on the byte content of
# the whole Makefile.  The whole file is an invocation wrapper: unrelated targets
# added by other tasks change its bytes without changing how the excess artifacts
# are produced.  Only this named target's recipe and prerequisites are a genuine
# provenance dependency, so only they are hashed.
RESEARCH_EXCESS_TARGET = "research-excess"
MAKEFILE_NAME = "Makefile"

# ---------------------------------------------------------------------------
# Frozen R3-TGT-01 protected boundary
# ---------------------------------------------------------------------------
#
# The protected boundary is the curated data and the generated namespaces that
# already existed when R3-TGT-01 was frozen, and that the excess regeneration
# must never mutate.  It is an explicit *historical allow-list*, not a live
# ``results_*`` wildcard: namespaces introduced by later, unrelated governed
# tasks are deliberately NOT members (they are protected by their own tasks), so
# adding one can never enlarge or invalidate this boundary.  The excess task's
# own output namespace (``experiments/results_excess``) is excluded here and is
# verified separately as this task's artifacts.
FROZEN_BOUNDARY_DATA_DIRS = ("trusted", "trusted_clean", "config", "exports", "interim")
FROZEN_BOUNDARY_EXPERIMENT_DIRS = (
    "reports",
    "results",
    "results_disagreement",
    "results_forward_2026",
    "results_influence",
    "results_placebo",
    "results_rank_stability",
    "results_real_terms",
    "results_regime",
    "results_serving_eval",
)
FROZEN_BOUNDARY_EXTRA_FILES = (
    "experiments/leaderboard.csv",
    "model_confidence_contract.json",
)
# Pinned content identity of the frozen boundary: the sha256 of the sorted
# ``<repo-relative-posix-path>:<sha256>`` records of every member (see
# ``_frozen_boundary_digest``).  Computed once at freeze and re-asserted on every
# regeneration so a modified or removed original member fails closed, and so the
# set is never silently redefined from the current filesystem.  It is a content
# digest, not a file count, and does not move when unrelated namespaces appear.
#
# Deliberate re-pin (2026-07-30, R3-UI-03 cross-task compatibility repair):
# ``634d7151e75f0ec7a85e412f748ac81499a4fad5e9eac71ab1a5c920f0137dd9`` ->
# ``0b0083a458ff24e9414ed23c12fb58f40ebe22c94539e6979b0c7affcf6d76ba``.  The
# R3-UI-03 calibration-audit surface required the Model Confidence Contract minor
# bump v1.8.0 -> v1.9.0, and ``model_confidence_contract.json`` is a member of
# this boundary by design.  The member set is unchanged (351 members) and exactly
# one member's content moved: ``model_confidence_contract.json``
# (5767a9b6464680497fe3be168a2dcae7bbed20dac88182fe5abeeaea4472b702 ->
# 1797ee7873b8ba0d1a4ecabf805f6de305c2dedcff2dbfa6a10a7efa87e413de).  No curated
# data and no other generated artifact changed, and no excess statistical result
# changed.  The MCC is NOT exempted, removed, or special-cased: it stays a member
# and any further change to it still fails closed here.
#
# Deliberate re-pin (2026-08-02, R3-LIMITS-01 valuation-schema prerequisite):
# ``0b0083a458ff24e9414ed23c12fb58f40ebe22c94539e6979b0c7affcf6d76ba`` ->
# ``e55c62bfb729ce73dc008e90a2875fa252c3c399bf1f29112eafea16eba14c2f``.
# The sole changed boundary member is
# ``data/trusted_clean/free_valuation_history_report.json``: its registered
# producer normalized ``limitations`` from the original scalar to a one-item
# string list while preserving the scalar text byte-for-byte.  No exemption was
# added: the report remains a protected member and any further change still fails
# closed here.
#
# Deliberate re-pin (2026-08-02, R3-MEMO-01 cross-task compatibility repair):
# ``e55c62bfb729ce73dc008e90a2875fa252c3c399bf1f29112eafea16eba14c2f`` ->
# ``03f9a7923e2ff3f6aff02d4d1efe83a621a5e0e26a6ebe949b2336cccadeddfd``.  The
# claim-aware research memo compiler required the Model Confidence Contract minor
# bump v1.9.0 -> v1.10.0 (new ``scan.backend_response_files`` entry and one exact
# allowlist line for the authoritative primary disclaimer), and
# ``model_confidence_contract.json`` is a member of this boundary by design.  The
# member set is unchanged (351 members) and exactly one member's content moved:
# ``model_confidence_contract.json``
# (1797ee7873b8ba0d1a4ecabf805f6de305c2dedcff2dbfa6a10a7efa87e413de ->
# 59e0fae3be8972e258891e723fd49cf13e36a7d16e918722a5a18b690c55d8f7).  Every other
# member was compared against ``main`` and is byte-identical; no curated data, no
# other generated artifact, and no excess statistical result changed.  The MCC is
# NOT exempted, removed, or special-cased: it stays a member and any further
# change to it still fails closed here.
#
# Deliberate re-pin (2026-08-17, FI-DATA-PATH-01 provenance-path repair):
# ``03f9a7923e2ff3f6aff02d4d1efe83a621a5e0e26a6ebe949b2336cccadeddfd`` ->
# ``74a8ea09f43a260a3e4e8633ae93ff2d7c0e3c0626f5826cfba2fa1e8dc2eb03``.  The sole
# changed boundary member is ``data/trusted_clean/universe_split_report.json``
# (e60c386421cfd4bc2f5251db3a14531a50c59cf42f470fa1456df434d408feb4 ->
# 8f879061e9b4d3d6d5858fe1bc0951ebb72b1248de7ae97d5f992685c90aaae2): its
# registered producer, ``scripts/data_collection/split_universe_datasets.py``,
# embedded absolute output paths from the machine that last ran it
# (``/Users/salihcamci/Downloads/capstone-financeIQ/...``, a location that no
# longer exists) and now emits repo-relative POSIX paths instead.  Only the two
# ``outputs`` strings moved; every numeric field, row count, ticker count, and
# validation flag in the report is unchanged, and the split CSVs it describes are
# byte-identical across the regeneration.  The member set is unchanged (351
# members) and every other member was compared against ``main`` and is
# byte-identical.  No exemption was added: the report remains a protected member
# and any further change still fails closed here.
FROZEN_PROTECTED_BOUNDARY_SHA256 = (
    "74a8ea09f43a260a3e4e8633ae93ff2d7c0e3c0626f5826cfba2fa1e8dc2eb03"
)

# ---------------------------------------------------------------------------
# Estimand tracing (correction 1)
# ---------------------------------------------------------------------------

# The nominal target column is never assumed here.  ``run_experiments.TARGETS``
# is the repository's declared evaluation order and its first entry is the
# primary target; the excess column's derivation is then re-read from the
# pipeline source so the audit proves the minuend rather than trusting a name.
NOMINAL_TARGET_AUTHORITY = "experiments/run_experiments.py::TARGETS[0]"
EXCESS_DERIVATION_AUTHORITY = "scripts/data_collection/pipeline.py"
BENCHMARK_COLUMN_EXPECTED = "next_year_bist100_return_pct"
# Absolute tolerance on the within-year spread of (nominal - excess). The trusted
# columns are stored as rounded percentage points, so a common subtrahend still
# differs by float round-off at roughly 1e-13.
BENCHMARK_COMMON_VALUE_TOLERANCE = 1e-9

ESTIMAND_STATEMENT = (
    "The within-year Spearman IC evaluates ordinal cross-sectional ranking: whether "
    "a model orders the evaluated cohort correctly inside one evaluation year. It "
    "does not evaluate benchmark-relative magnitude accuracy, and it does not "
    "estimate alpha, economic outperformance, investment value, or a tradable "
    "strategy."
)
ESTIMAND_FITTING_NOTE = (
    "Benchmark subtraction may still affect fitting: it shifts the target by a "
    "year-level constant across the training panel, so models trained on pooled "
    "years can learn different coefficients than on the nominal basis. It does not "
    "alter within-year evaluation ranks, so the evaluated estimand is unchanged."
)

# ---------------------------------------------------------------------------
# Permutation analyses (corrections 2 and 3)
# ---------------------------------------------------------------------------

PRIMARY_PERMUTATION_ID = "primary_independent_within_year_permutation"
PRIMARY_PERMUTATION_NULL = (
    "Within each evaluation year, realized cross-sectional outcomes are exchangeable "
    "relative to the model predictions, with each year permuted independently."
)
PRIMARY_PERMUTATION_STATUS = "prespecified"

TRAJECTORY_SENSITIVITY_ID = "trajectory_preserving_ticker_permutation_sensitivity"
TRAJECTORY_SENSITIVITY_NULL = (
    "Ticker identities are exchangeable as complete cross-year trajectories: one "
    "permutation of the ticker universe is drawn per replication and applied "
    "identically in every evaluation year, so a ticker's realized outcomes move "
    "together and any cross-year persistence in the realized panel is preserved "
    "under the null."
)
TRAJECTORY_SENSITIVITY_STATUS = "post_review_sensitivity"
TRAJECTORY_SENSITIVITY_PROVENANCE = (
    "Added after human review at the reviewer's request. It is a sensitivity "
    "analysis, not a prespecified analysis and not a replacement for the primary "
    "independently-within-year permutation, which is retained unchanged."
)
# The frozen repository seed is reused deliberately: one documented seed governs
# every stochastic component of this task.
TRAJECTORY_SENSITIVITY_SEED = significance.DEFAULT_SEED
TRAJECTORY_SENSITIVITY_DRAWS = significance.DEFAULT_PERMUTATIONS
MIN_TRAJECTORY_TICKERS = MIN_CLUSTERS
MIN_VALID_PERMUTATION_DRAWS = 1_000
MIN_VALID_PERMUTATION_FRACTION = 0.9
# The pooled IC recomputed on the reindexed trajectory panel must agree with the
# pooled IC that analyze_model reports; Spearman IC is invariant to row order, so
# any disagreement beyond float round-off means the panels are not the same rows.
OBSERVED_IC_AGREEMENT_TOLERANCE = 1e-12

PREDICTION_CSV_SCHEMA_VERSION = "1.0.0"
LEADERBOARD_CSV_SCHEMA_VERSION = "1.0.0"

REPORTING_POLICY_STATEMENT = (
    "All six prespecified ML-family members are reported symmetrically. No model "
    "is selected or privileged using the observed excess-target IC, raw p-value, "
    "adjusted p-value, bootstrap interval, or any other outcome-derived statistic."
)
BOOTSTRAP_INTERPRETATION = (
    "A bootstrap interval is descriptive uncertainty evidence and does not replace "
    "the closed-family correction. No model survives family-wise correction, and no "
    "reliable predictive edge is established."
)

BASIS_LIMITATION = (
    "Excess returns subtract the BIST100 nominal TRY index return within one "
    "unusual macro regime; they are a descriptive benchmark-relative basis and "
    "do not represent an implementable benchmark-hedged position or investment value."
)
COVERAGE_LIMITATION = (
    "The evaluated cohort is the benchmark-covered public 40, not the wider internal "
    "training universe used by the nominal basis; rows without a valid excess target "
    "remain null and shrink the evaluated n per year rather than being filled."
)
CLUSTER_LIMITATION = (
    "The ticker-cluster bootstrap resamples 40 ticker trajectories, so its effective "
    "resolution is bounded by 40 clusters over three years; it describes sampling "
    "uncertainty and cannot substitute for family-wise multiplicity correction."
)
CROSS_BASIS_LIMITATION = (
    "Bonferroni correction here is within-basis only. Nominal return is the sole "
    "confirmatory family; the real-TRY, USD, and excess-return bases are exploratory "
    "robustness evaluations, and no correction in this repository controls "
    "multiplicity across the several target bases."
)
NEGATIVE_IC_LIMITATION = (
    "Predominantly negative IC signs are not interpreted as inverse alpha, a "
    "contrarian strategy, an actionable signal, or validated predictive evidence."
)
REVIEW_PACKAGE_LIMITATION = (
    "The compact human-review package supports review of the persisted "
    "prediction-to-significance layer only; it does not by itself reproduce feature "
    "construction or model fitting, and no claim of complete independent "
    "fitting-stage replication is made from it alone."
)

# ---------------------------------------------------------------------------
# Cross-basis multiplicity (correction 5)
# ---------------------------------------------------------------------------

CONFIRMATORY_BASIS_ID = "nominal_try_return"
CONFIRMATORY_BASIS_TARGET = "next_year_return_pct"
EXPLORATORY_BASES = (
    {
        "basis_id": "real_try_return",
        "target_column": "next_year_real_return_pct",
        "label": "CPI-deflated real TRY return",
    },
    {
        "basis_id": "usd_return",
        "target_column": "next_year_usd_return_pct",
        "label": "USD-converted return",
    },
    {
        "basis_id": BASIS_ID,
        "target_column": TARGET_COLUMN,
        "label": BASIS_LABEL,
    },
)

# ---------------------------------------------------------------------------
# Coincident baselines (correction 6)
# ---------------------------------------------------------------------------

COINCIDENT_BASELINE_CANDIDATES = ("baseline_equal_weight", "baseline_rank_score")
COINCIDENT_BASELINE_POLICY = (
    "Both specifications are retained for frozen-specification continuity. Neither "
    "is removed, because no repository authority has explicitly permitted removing a "
    "frozen model specification."
)
COINCIDENT_BASELINE_INTERPRETATION = (
    "Coincident baseline results must not be interpreted as independent baseline "
    "diversity: two baselines that agree at this level contribute one distinct "
    "comparison, not two."
)

# ---------------------------------------------------------------------------
# Negative IC signs (correction 7)
# ---------------------------------------------------------------------------

NEGATIVE_IC_NOTE = (
    "Predominantly negative IC signs may reflect sampling variation, "
    "feature-orientation effects, or systematic construction effects. They are not "
    "interpreted as inverse alpha, a contrarian strategy, an actionable signal, or "
    "validated predictive evidence."
)

# ---------------------------------------------------------------------------
# Human-review package scope (correction 8)
# ---------------------------------------------------------------------------

REVIEW_PACKAGE_SCOPE_STATEMENTS = (
    "The compact package supports review of the persisted prediction-to-significance "
    "layer: the row-level prediction dumps, the dump-reconstructed leaderboard, the "
    "significance report, and the artifact manifest.",
    "It does not alone provide standalone reproduction of feature construction and "
    "model fitting.",
    "The repository technical review separately covers governed source paths, "
    "protected hashes, split tracing, and implementation behavior.",
    "No claim of complete independent fitting-stage replication is made from the "
    "compact package alone.",
)

_UNSAFE_EXCESS_CLAIMS = (
    re.compile(r"\bsignal (?:vs|versus|against) (?:the )?(?:bist100 )?benchmark\b", re.I),
    re.compile(r"\bbeats? the (?:bist100 )?(?:benchmark|index|market)\b", re.I),
    re.compile(r"\boutperform(?:s|ed)? the bist100\b", re.I),
    re.compile(r"\bbenchmark[- ]beating\b", re.I),
    re.compile(r"\balpha (?:was )?(?:found|generated|captured|delivered)\b", re.I),
    # Human review added these: the ordinal estimand must not be upgraded into a
    # magnitude, alpha, or tradable-strategy claim, and the predominantly negative
    # ICs must not be flipped into a contrarian recommendation.
    re.compile(r"\bestimates (?:economic )?(?:alpha|outperformance)\b", re.I),
    re.compile(r"\bmeasures benchmark[- ]relative magnitude accuracy\b", re.I),
    re.compile(
        r"\bestablishes (?:a |an )?(?:inverse|contrarian) (?:alpha|signal|strategy|edge)\b",
        re.I,
    ),
    re.compile(r"\btrade the (?:negative|inverse) ic\b", re.I),
    re.compile(
        r"\btradable strategy (?:is |was )?(?:established|demonstrated|validated)\b", re.I
    ),
)

# Report-level guard against reintroducing a post-outcome winner.
_SELECTION_LANGUAGE = (
    re.compile(r"\bselected model\b", re.I),
    re.compile(r"\bheadline model\b", re.I),
    re.compile(r"\bbest[- ]performing model\b", re.I),
    re.compile(r"\bbest model\b", re.I),
    re.compile(r"\bstrongest model\b", re.I),
    re.compile(r"\bmost significant model\b", re.I),
    re.compile(r"\bsmallest (?:pooled )?(?:raw )?p[- ]value belongs to\b", re.I),
    re.compile(r"\bwinning model\b", re.I),
)
_FORBIDDEN_SELECTION_KEYS = (
    "selected_model",
    "headline_model",
    "best_model",
    "strongest_model",
    "winning_model",
    "most_significant_model",
    "headline",
)


class ExcessOutputPathError(ValueError):
    """Raised when an R3-TGT-01 output directory violates the bounded policy.

    A specific exception type is used deliberately: a caller must be able to tell
    a refused destination apart from an incidental filesystem ``OSError``.
    """


class ExcessPanelError(ValueError):
    """Base class for refusals of a malformed balanced ticker x year panel.

    Both resampling analyses share one panel contract, so they share one base
    class; each raises its own subclass so a caller can still tell which analysis
    refused the input.
    """


class ExcessBootstrapError(ExcessPanelError):
    """Raised when the persisted dumps cannot support a ticker-cluster bootstrap."""


class ExcessPermutationError(ExcessPanelError):
    """Raised when the trajectory-preserving permutation sensitivity refuses input.

    A distinct type keeps a refused permutation contract (per-year mappings, a
    mapping with duplicates, too few valid draws) separable from a refused
    bootstrap and from an incidental ``ValueError``.
    """


class ExcessEstimandError(ValueError):
    """Raised when the estimand-invariance audit cannot be established.

    The audit is a precondition, not a decoration: if the expected common
    within-year benchmark subtraction or the resulting rank invariance does not
    hold, the run fails rather than publishing an ordinal-estimand claim that the
    data does not support.
    """


class ExcessMakefileProvenanceError(ValueError):
    """Raised when the ``research-excess`` Makefile recipe cannot be located.

    The excess task depends on its own regeneration recipe, not on the whole
    Makefile.  If the target rule is missing the recipe-provenance authority
    cannot be built, so the run fails rather than silently recording an empty or
    misattributed recipe.  A distinct type keeps a removed/renamed target
    separable from an incidental parse or filesystem error.
    """


class ExcessFrozenBoundaryError(ValueError):
    """Raised when the frozen R3-TGT-01 protected boundary no longer matches its
    pinned authority.

    The boundary is a fixed historical set: the curated data and the generated
    namespaces that already existed when R3-TGT-01 was frozen.  It is never
    silently redefined from whatever files happen to exist now, so a mismatch
    (a modified or removed original member) fails closed instead of quietly
    re-freezing a new set.  Namespaces that later tasks add are not members and
    do not trigger this error.
    """


def validate_excess_claim_safety_text(text: str) -> None:
    """Reject benchmark-relative performance interpretations of this analysis."""
    alt.validate_claim_safety_text(text)
    for pattern in _UNSAFE_EXCESS_CLAIMS:
        if pattern.search(text):
            raise ValueError(f"Unsafe excess-basis claim: {pattern.pattern}")


def validate_no_selection_language(text: str) -> None:
    """Reject any reintroduced post-outcome model-selection framing."""
    for pattern in _SELECTION_LANGUAGE:
        if pattern.search(text):
            raise ValueError(f"Post-outcome model selection wording: {pattern.pattern}")


def assert_no_selection_keys(payload: object, *, path: str = "$") -> None:
    """Recursively reject selected/headline/best-model keys in generated JSON."""
    if isinstance(payload, dict):
        for key, value in payload.items():
            if str(key).lower() in _FORBIDDEN_SELECTION_KEYS:
                raise ValueError(f"post-outcome selection key at {path}.{key}")
            assert_no_selection_keys(value, path=f"{path}.{key}")
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            assert_no_selection_keys(value, path=f"{path}[{index}]")


def _resolve_output_dir(output_dir: Path | str | None) -> Path:
    """Resolve an output directory under the bounded R3-TGT-01 destination policy.

    Exactly two kinds of destination are accepted:

    * the default repository namespace ``experiments/results_excess``; and
    * a dedicated directory named ``financeiq-r3-tgt-01-*`` underneath the
      operating system's temporary root, for isolated tests and deterministic
      verification only.

    Everything else is refused: the repository root and every other
    in-repository path (nominal results, trusted data, backend, frontend), the
    home directory, ``/``, ``/etc``, the temporary root itself, and arbitrary
    external paths.  Symlinked destinations and symlinked path components
    between the temporary root and the destination are refused as well, and the
    fully resolved destination must still land under the resolved temporary
    root, so a symlink cannot be used to escape the allowed tree.

    ``tempfile.gettempdir()`` is the authority for the temporary root; it is not
    assumed to be ``/tmp`` (on macOS it is normally under ``/var/folders``).
    Refusal always happens before any file is created or overwritten.
    """
    if output_dir is None:
        return OUTPUT_DIR

    raw = Path(output_dir).expanduser()
    if not raw.is_absolute():
        raw = Path.cwd() / raw
    # Normalise lexically: resolving here would hide the symlink components the
    # policy has to inspect.
    lexical = Path(os.path.normpath(str(raw)))

    if lexical == OUTPUT_DIR or lexical == OUTPUT_DIR.resolve():
        return OUTPUT_DIR

    repo_root = ROOT.resolve()
    if lexical == repo_root or lexical.is_relative_to(repo_root):
        raise ExcessOutputPathError(
            "refusing to write outside the isolated excess namespace: "
            f"{lexical} is inside the repository but is not "
            f"{OUTPUT_DIR.relative_to(repo_root).as_posix()}"
        )

    raw_temp_root = Path(tempfile.gettempdir())
    real_temp_root = raw_temp_root.resolve()
    scan_root: Path | None = None
    for candidate_root in (raw_temp_root, real_temp_root):
        if lexical == candidate_root:
            raise ExcessOutputPathError(
                "refusing to write to the temporary root itself: "
                f"{lexical}; a dedicated {TEMP_OUTPUT_PREFIX}* directory is required"
            )
        if lexical.is_relative_to(candidate_root):
            scan_root = candidate_root
            break
    if scan_root is None:
        raise ExcessOutputPathError(
            "refusing an output directory outside the isolated excess namespace: "
            f"{lexical} is neither the default excess namespace nor a "
            f"{TEMP_OUTPUT_PREFIX}* directory under the temporary root reported by "
            "tempfile.gettempdir()"
        )

    if not lexical.name.startswith(TEMP_OUTPUT_PREFIX):
        raise ExcessOutputPathError(
            "refusing a temporary output directory whose name does not begin with "
            f"{TEMP_OUTPUT_PREFIX!r}: {lexical.name!r}"
        )

    if lexical.is_symlink():
        raise ExcessOutputPathError(
            f"refusing a symbolic-link output destination: {lexical}"
        )
    walked = scan_root
    for part in lexical.relative_to(scan_root).parts:
        walked = walked / part
        if walked.is_symlink():
            raise ExcessOutputPathError(
                "refusing an output path with a symbolic-link component between the "
                f"temporary root and the destination: {walked}"
            )

    resolved = lexical.resolve()
    if resolved == real_temp_root or not resolved.is_relative_to(real_temp_root):
        raise ExcessOutputPathError(
            "refusing an output path that resolves outside the temporary root: "
            f"{lexical} resolves to {resolved}"
        )
    return lexical


def build_output_path_policy() -> dict:
    """Record the bounded destination policy without recording a machine path."""
    return {
        "default_output_directory": OUTPUT_DIR.relative_to(ROOT.resolve()).as_posix(),
        "default_is_the_only_repository_destination": True,
        "temporary_override_scope": (
            "isolated tests and deterministic verification only; this generator is "
            "not a general arbitrary-output utility"
        ),
        "temporary_root_authority": "tempfile.gettempdir()",
        "temporary_root_hardcoded": False,
        "required_destination_name_prefix": TEMP_OUTPUT_PREFIX,
        "temporary_root_itself_accepted": False,
        "symlinked_destination_accepted": False,
        "symlinked_path_component_accepted": False,
        "resolved_containment_under_temporary_root_required": True,
        "arbitrary_external_paths_accepted": False,
        "refusal_exception": ExcessOutputPathError.__name__,
        "refusal_timing": "before any output file is created or overwritten",
    }


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    root = ROOT.resolve()
    if resolved.is_relative_to(root):
        return resolved.relative_to(root).as_posix()
    return resolved.as_posix()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


# Descriptor-anchored hashing flags (present on Linux/macOS; ``getattr`` keeps the
# import portable — the lexical symlink guards during collection still apply).
_EX_O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
_EX_O_DIRECTORY = getattr(os, "O_DIRECTORY", 0)


def _fd_identity(fd: int) -> tuple[int, int]:
    """``(st_dev, st_ino)`` of an open descriptor — its stable object identity."""
    info = os.fstat(fd)
    return info.st_dev, info.st_ino


def _revalidate_frozen_chain(
    root_fd: int,
    ancestors: list[str],
    ancestor_ids: list[tuple[int, int]],
    final: str,
    member_id: tuple[int, int],
    relative_posix: str,
) -> None:
    """Re-walk ``ancestors``/``final`` from ``root_fd`` and prove identity is stable.

    The first traversal opened and retained a descriptor for every ancestor and
    the final member.  Those descriptors keep pointing at the *original* objects
    even if the repository path is later re-pointed elsewhere — so verifying the
    member only against a retained parent descriptor cannot see an ancestor that
    was renamed away and replaced during hashing.  This re-opens each component
    fresh from ``root_fd`` with ``O_NOFOLLOW`` and requires the *current* path to
    still reach the very same ``(dev, ino)`` objects; anything else (a swapped,
    renamed-and-replaced, symlinked, deleted, or type-changed component anywhere
    in the chain) fails closed.
    """
    parent_fd = root_fd
    reopened: list[int] = []
    try:
        for depth, component in enumerate(ancestors):
            try:
                nxt = os.open(
                    component,
                    os.O_RDONLY | _EX_O_DIRECTORY | _EX_O_NOFOLLOW,
                    dir_fd=parent_fd,
                )
            except OSError as exc:
                raise ExcessFrozenBoundaryError(
                    f"frozen-boundary ancestor {component!r} of {relative_posix} could "
                    f"not be re-opened from the repository root after hashing (renamed, "
                    f"replaced, symlinked, or deleted during hashing): {exc}"
                ) from exc
            reopened.append(nxt)
            if _fd_identity(nxt) != ancestor_ids[depth]:
                raise ExcessFrozenBoundaryError(
                    f"frozen-boundary ancestor {component!r} of {relative_posix} no "
                    "longer identifies the object hashed under it (the current "
                    "repository path was re-pointed to a different directory during "
                    "hashing); failing closed"
                )
            parent_fd = nxt
        try:
            info = os.stat(final, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError as exc:
            raise ExcessFrozenBoundaryError(
                f"frozen-boundary member {relative_posix} is no longer reachable from "
                "the repository root after hashing (deleted or renamed during hashing)"
            ) from exc
        if stat.S_ISLNK(info.st_mode):
            raise ExcessFrozenBoundaryError(
                f"frozen-boundary member {relative_posix} became a symlink on the "
                "current repository path during hashing; failing closed"
            )
        if (info.st_dev, info.st_ino) != member_id:
            raise ExcessFrozenBoundaryError(
                f"frozen-boundary member {relative_posix} on the current repository "
                "path no longer identifies the hashed object (ancestor renamed and "
                "replaced during hashing); failing closed"
            )
    finally:
        for fd in reversed(reopened):
            os.close(fd)


def _sha256_member_anchored(root_fd: int, relative_posix: str) -> str:
    """Hash a frozen-boundary member strictly beneath ``root_fd`` without following.

    Never hashes by reopening a previously validated pathname: every ancestor
    component is opened with ``O_NOFOLLOW`` relative to the prior descriptor, the
    final member is opened ``O_RDONLY | O_NOFOLLOW``, validated by ``fstat`` on
    that exact descriptor (must be a regular file), and hashed from it.  A second
    ``fstat`` after hashing and a ``follow_symlinks=False`` stat of the path via
    the member's parent descriptor prove the member descriptor still identifies
    the same device/inode object with unchanged size and mtime, so a file swapped
    for a symlink, replaced by another regular file, truncated, or deleted between
    validation and hashing all fail closed.

    A retained parent descriptor is not enough on its own: it keeps pointing at
    the original directory even if a *higher* ancestor (e.g. ``data/trusted``) is
    renamed away and a different tree is installed on the same repository path
    while the member is being hashed.  After hashing, the whole chain is therefore
    re-walked from ``root_fd`` (:func:`_revalidate_frozen_chain`) and the current
    repository path is required to still reach the very same ``(dev, ino)`` objects
    for every ancestor and for the final member; an ancestor-replacement race fails
    closed instead of being silently accepted.
    """
    parts = relative_posix.split("/")
    ancestors, final = parts[:-1], parts[-1]
    opened: list[int] = []
    ancestor_ids: list[tuple[int, int]] = []
    parent_fd = root_fd
    try:
        for component in ancestors:
            try:
                nxt = os.open(
                    component,
                    os.O_RDONLY | _EX_O_DIRECTORY | _EX_O_NOFOLLOW,
                    dir_fd=parent_fd,
                )
            except OSError as exc:
                raise ExcessFrozenBoundaryError(
                    f"frozen-boundary ancestor {component!r} of {relative_posix} could "
                    f"not be opened without following a symlink: {exc}"
                ) from exc
            opened.append(nxt)
            ancestor_ids.append(_fd_identity(nxt))
            parent_fd = nxt

        try:
            member_fd = os.open(
                final, os.O_RDONLY | _EX_O_NOFOLLOW, dir_fd=parent_fd
            )
        except OSError as exc:
            raise ExcessFrozenBoundaryError(
                f"frozen-boundary member {relative_posix} could not be opened without "
                f"following a symlink (a symlink, missing, or non-regular file): {exc}"
            ) from exc
        try:
            first = os.fstat(member_fd)
            if not stat.S_ISREG(first.st_mode):
                raise ExcessFrozenBoundaryError(
                    f"frozen-boundary member is not a regular file: {relative_posix}"
                )
            digest = hashlib.sha256()
            while True:
                block = os.read(member_fd, 1024 * 1024)
                if not block:
                    break
                digest.update(block)
            after = os.fstat(member_fd)
            if (
                (first.st_dev, first.st_ino) != (after.st_dev, after.st_ino)
                or first.st_size != after.st_size
                or first.st_mtime_ns != after.st_mtime_ns
            ):
                raise ExcessFrozenBoundaryError(
                    f"frozen-boundary member changed while it was being hashed: "
                    f"{relative_posix}"
                )
            try:
                path_info = os.stat(final, dir_fd=parent_fd, follow_symlinks=False)
            except FileNotFoundError as exc:
                raise ExcessFrozenBoundaryError(
                    f"frozen-boundary member was deleted while being hashed: "
                    f"{relative_posix}"
                ) from exc
            if stat.S_ISLNK(path_info.st_mode):
                raise ExcessFrozenBoundaryError(
                    f"frozen-boundary member was replaced by a symlink while being "
                    f"hashed: {relative_posix}"
                )
            if (path_info.st_dev, path_info.st_ino) != (first.st_dev, first.st_ino):
                raise ExcessFrozenBoundaryError(
                    f"frozen-boundary member path no longer identifies the hashed "
                    f"object (replaced during hashing): {relative_posix}"
                )
            # Post-hash whole-chain revalidation from the repository root: the
            # current path must still reach the same ancestor and member objects.
            _revalidate_frozen_chain(
                root_fd,
                ancestors,
                ancestor_ids,
                final,
                (first.st_dev, first.st_ino),
                relative_posix,
            )
            return digest.hexdigest()
        finally:
            os.close(member_fd)
    finally:
        for fd in reversed(opened):
            os.close(fd)


def _source_record(path: Path, role: str) -> dict:
    return {
        "path": _display_path(path),
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
        "role": role,
    }


# ---------------------------------------------------------------------------
# Task-specific Makefile recipe provenance (static, non-executing parser)
# ---------------------------------------------------------------------------
#
# SECURITY CONTRACT — this authority NEVER invokes GNU Make.  The previous
# implementation shelled out to ``make --dry-run`` / ``make --print-data-base``
# to discover the effective recipe; but ``--dry-run`` still *executes* recursive
# sub-makes and force-run (``+``) recipe lines, can touch the filesystem, and can
# leak machine-specific executable paths.  Discovering a recipe by running a
# program that may itself run that recipe is unsafe, so recipe discovery is now a
# pure, side-effect-free parse of the Makefile bytes: no subprocess is launched,
# and no code path can execute a recipe command.
#
# It is deliberately NOT a general GNU Make implementation.  It supports only the
# narrow, statically reviewable form the repository's ``research-excess`` target
# actually uses, and it fails closed on anything outside that form BEFORE any
# command text could ever run.  ``MAKEFILE_ACCEPTED_SUBSET`` documents the exact
# contract, which is also embedded in the generated provenance metadata.  Only
# this one target's prerequisites and verbatim recipe lines are hashed; the whole
# Makefile is never hashed, so unrelated targets or variables added by other
# tasks never stale these artifacts, while a change to the research-excess recipe
# or its prerequisites always does.

MAKEFILE_ACCEPTED_SUBSET = (
    "Static, non-executing parse of a single research-excess rule; GNU Make is "
    "never invoked. Directive and rule detection operates on logical lines "
    "(backslash continuations joined) after leading whitespace is stripped, so a "
    "space-indented directive or rule is seen exactly as GNU Make sees it. "
    "Accepted: exactly one target-rule line 'research-excess:' (single ':', never "
    "'::' or ':='), optional whitespace-separated prerequisites with backslash "
    "continuation, and a contiguous block of tab-indented recipe lines recorded "
    "verbatim with backslash continuation preserved. Execution-significant recipe "
    "prefixes '@' and '-' are preserved as literal text so, e.g., 'false', "
    "'-false', '@false', and '-@false' produce distinct provenance. '.PHONY' is "
    "the one accepted special target and is NOT inert: whether research-excess is "
    "a .PHONY member decides whether an existing file of that name would suppress "
    "the recipe, so membership is parsed from every .PHONY line (leading "
    "whitespace and continuations included) and recorded truthfully as a hashed "
    "provenance field. Rejected (fail closed, before any command could run): a "
    "missing or renamed target, duplicate research-excess rule lines (at column 0 "
    "or space-indented), a '::' or ':=' form, a '+' recipe prefix, a global or "
    "target-scoped SHELL/.SHELLFLAGS/MAKESHELL/MAKEFLAGS assignment, any other "
    "special target ('.IGNORE', '.SILENT', '.ONESHELL', '.POSIX', '.RECIPEPREFIX', "
    "'.DELETE_ON_ERROR', '.NOTPARALLEL', '.SECONDEXPANSION', "
    "'.EXPORT_ALL_VARIABLES') whether global, target-scoped, or space-indented, an "
    "unsupported '.PHONY' form, '$(MAKE)'/'${MAKE}' or any recursive 'make' "
    "invocation, and any '$(...)' or '${...}' make variable/function reference "
    "(covering '$(shell ...)', '$(eval ...)', '$(call ...)', and ordinary variable "
    "expansion) in the recipe, the prerequisites, or a .PHONY member list. Escaped "
    "'$$' is left intact. Every rule line in the file is additionally checked for "
    "target-identity ambiguity, because a target expression this parser could not "
    "resolve might silently define, duplicate, or override research-excess: a "
    "multi-target rule naming research-excess in any position (including one "
    "assembled across backslash continuations), a target expression containing any "
    "'$(...)'/'${...}' variable-derived name (e.g. '$(TARGET):' or '${TARGET}:'), a "
    "pattern ('%') or glob ('*', '?', '[...]') target that could cover "
    "research-excess, a variable assignment whose literal value is research-excess, "
    "and more than one effective research-excess target definition in any mixture "
    "of literal and derived forms all fail closed, as do a static pattern rule and "
    "a ';' inline recipe on the research-excess rule line. No target expression whose "
    "effective identity cannot be established statically — without executing or "
    "expanding Make — is ever accepted. No general GNU Make equivalence is claimed."
)

# A research-excess rule line at column 0: single ':' (never '::' or ':='),
# capturing the prerequisite text that follows.
_RESEARCH_EXCESS_RULE_RE = re.compile(
    r"^" + re.escape(RESEARCH_EXCESS_TARGET) + r"[ \t]*:(?![:=])(?P<prereqs>.*)$"
)
# A '::' or ':=' definition of the target is outside the accepted simple form.
_RESEARCH_EXCESS_UNSUPPORTED_RE = re.compile(
    r"^" + re.escape(RESEARCH_EXCESS_TARGET) + r"[ \t]*(?:::|:?=)"
)
# Any make variable/function reference — rejected wholesale inside the target's
# recipe or prerequisites (covers $(MAKE), $(shell ...), $(eval ...), $(call ...),
# and ordinary $(VAR)/${VAR} expansion). An escaped '$$' is preceded by '$' and
# is left intact.
_MAKE_EXPANSION_RE = re.compile(r"(?<!\$)\$[({]")
# A recursive make invocation appearing as a command word (in addition to
# $(MAKE)): 'make' at the start or after a shell separator.
_RECURSIVE_MAKE_RE = re.compile(r"(?:^|[\s;&|()])make(?:\s|$)")

# Special-target directives (e.g. '.ONESHELL:', '.IGNORE:', '.SILENT:'). Matched
# on the *stripped* logical line, because GNU Make strips leading whitespace from
# any non-recipe line: '  .SILENT:' is as effective as '.SILENT:' at column 0.
# Only '.PHONY' is inside the accepted subset, and it is NOT treated as inert:
# .PHONY membership decides whether an existing file named 'research-excess'
# would make the target up to date and suppress the recipe, so membership is
# recorded truthfully in provenance instead of being ignored. Every other special
# target — '.IGNORE'/'.SILENT'/'.ONESHELL'/'.POSIX'/'.RECIPEPREFIX'/
# '.DELETE_ON_ERROR'/'.NOTPARALLEL'/'.SECONDEXPANSION'/'.EXPORT_ALL_VARIABLES',
# global, target-scoped, or whitespace-prefixed — changes execution semantics
# (error handling, echoing, one-shell recipes, the recipe-prefix character,
# parallelism, second expansion) and fails closed.
_SPECIAL_TARGET_RE = re.compile(r"^(\.[A-Za-z_][A-Za-z0-9_]*)\b")
_ALLOWED_SPECIAL_TARGETS = frozenset({".PHONY"})
# The only accepted '.PHONY' form: a single ':' followed by a literal member list.
_PHONY_RULE_RE = re.compile(r"^\.PHONY[ \t]*:(?![:=])(?P<members>.*)$")
# A global (or whitespace-prefixed) assignment to a variable that changes which
# shell runs every recipe, or with which flags. GNU Make honours these for
# research-excess too, while the recipe text stays byte-identical, so they are
# refused rather than silently misrepresented.
_SHELL_ASSIGNMENT_RE = re.compile(
    r"^(SHELL|MAKESHELL|MAKEFLAGS|\.SHELLFLAGS)[ \t]*(?:::=|:=|\+=|\?=|!=|=)"
)
# Column-0 global directives that can inject rules, expand text dynamically, or
# change execution for every target (including research-excess). None are part of
# the accepted subset; each fails closed before any recipe could be discovered.
_GLOBAL_DIRECTIVE_RE = re.compile(
    r"^(include|-include|sinclude|load|-load|define|endef|override|export|unexport|"
    r"vpath|VPATH)\b"
)
# A make variable assignment operator ('=', ':=', '::=', '+=', '?=', '!='). Used
# to tell a target-specific/global variable definition apart from a plain
# prerequisite list on the research-excess rule line.
_ASSIGNMENT_OPERATOR_RE = re.compile(r"(::=|:=|\+=|\?=|!=|=)")
# A whole-line variable definition ('NAME = value', 'NAME := value', ...). The
# name may not contain ':', '=', or whitespace, so a rule line such as
# 'target: VAR = value' is never mistaken for a plain variable definition, and a
# value that itself contains ':' (a URL, for instance) is never mistaken for a
# rule.
_VARIABLE_DEFINITION_RE = re.compile(
    r"^(?P<name>[^:=\s]+)[ \t]*(?P<op>::=|:=|\+=|\?=|!=|=)(?P<value>.*)$"
)
# Shell/Make glob metacharacters. GNU Make expands wildcards in target names, so
# a target token carrying one of these may resolve to research-excess.
_TARGET_GLOB_CHARS = "*?["


def _logical_make_lines(lines: list[str]) -> list[tuple[int, bool, str]]:
    """Group physical lines into ``(start_index, is_recipe_line, joined_text)``.

    GNU Make joins backslash-continued lines *before* deciding what a line means,
    so a directive whose member list continues onto tab-indented lines is one
    logical line, not a directive followed by recipe lines.  Classification uses
    the first physical line: a line that starts with a tab is recipe text (its
    continuations are consumed but its text is not interpreted as a directive),
    and everything else is a makefile line whose comment is stripped and whose
    continuations are joined with a single space, exactly as Make does.  Nothing
    here executes: it is string handling over the Makefile bytes.
    """
    grouped: list[tuple[int, bool, str]] = []
    index = 0
    total = len(lines)
    while index < total:
        start = index
        raw = lines[index]
        if raw.startswith("\t"):
            body = raw
            while body.rstrip().endswith("\\") and index + 1 < total:
                index += 1
                body = lines[index]
            grouped.append((start, True, ""))
        else:
            joined = _strip_make_comment(raw)
            while joined.rstrip().endswith("\\") and index + 1 < total:
                joined = joined.rstrip()[:-1]
                index += 1
                joined = joined + " " + _strip_make_comment(lines[index]).strip()
            grouped.append((start, False, joined))
        index += 1
    return grouped


def _rule_target_expression(text: str) -> str | None:
    """Return the target expression of a Make rule line, or ``None`` if not a rule.

    Pure string handling over one already-joined logical line: it scans for the
    first unescaped ``:`` that introduces a rule and returns everything before it.
    A ``:=`` or ``::=`` assignment operator is not a rule colon (so
    ``VAR := value`` is not a rule), while ``::`` is a double-colon rule and *is*
    reported so the caller can judge its target identity.  Nothing is executed and
    nothing is expanded.
    """
    index = 0
    total = len(text)
    while index < total:
        char = text[index]
        if char == "\\" and index + 1 < total:
            index += 2
            continue
        if char == ":":
            following = text[index + 1 : index + 3]
            if following.startswith("="):
                return None  # ':=' assignment, not a rule
            if following.startswith(":"):
                if following.startswith(":="):
                    return None  # '::=' assignment, not a rule
                return text[:index]  # '::' double-colon rule
            return text[:index]  # simple rule
        index += 1
    return None


def _target_token_covers_governed(token: str) -> bool:
    """True when a single target token could name ``research-excess``.

    A literal match is exact.  A ``%`` pattern target covers the governed target
    when its literal prefix and suffix bracket the name, and a glob target covers
    it when the shell pattern matches.  Both are judged statically, on the token
    text alone.
    """
    if token == RESEARCH_EXCESS_TARGET:
        return True
    if "%" in token:
        prefix, _sep, suffix = token.partition("%")
        return (
            RESEARCH_EXCESS_TARGET.startswith(prefix)
            and RESEARCH_EXCESS_TARGET.endswith(suffix)
            and len(prefix) + len(suffix) <= len(RESEARCH_EXCESS_TARGET)
        )
    if any(char in token for char in _TARGET_GLOB_CHARS):
        try:
            return fnmatch.fnmatchcase(RESEARCH_EXCESS_TARGET, token)
        except re.error:  # pragma: no cover - malformed pattern is ambiguous
            return True
    return False


def _check_rule_target_identity(stripped: str, line_number: int) -> bool:
    """Judge one rule line's target identity; return True when it defines the target.

    Fails closed on every target expression whose effective identity cannot be
    established statically without executing or expanding GNU Make:

    * a multi-target rule naming ``research-excess`` in any position (a
      backslash-continued target list is already one logical line here, so a
      continued multi-target rule is judged the same way);
    * a variable-derived target name (``$(TARGET):`` / ``${TARGET}:``), which
      could resolve to ``research-excess`` only by expansion;
    * a pattern or glob target that could cover ``research-excess``.

    A rule whose targets are literal names none of which is (or could be) the
    governed target is simply not this task's business and is left alone, so
    unrelated targets never move the authority.
    """
    expression = _rule_target_expression(stripped)
    if expression is None:
        return False
    expression = expression.strip()
    if not expression:
        return False
    if _MAKE_EXPANSION_RE.search(expression):
        raise ExcessMakefileProvenanceError(
            f"Makefile line {line_number} defines a target through a make "
            f"variable/function reference ({expression!r}); its effective target "
            "identity cannot be established statically without expanding Make, so it "
            f"could silently define, duplicate, or override {RESEARCH_EXCESS_TARGET!r} "
            "— failing closed"
        )
    tokens = expression.split()
    covering = [token for token in tokens if _target_token_covers_governed(token)]
    if not covering:
        return False
    if len(tokens) > 1:
        raise ExcessMakefileProvenanceError(
            f"Makefile line {line_number} is a multi-target rule naming "
            f"{RESEARCH_EXCESS_TARGET!r} ({expression!r}); a multi-target rule gives "
            "every listed target the same recipe and is outside the accepted "
            "single-target static subset — failing closed"
        )
    if covering[0] != RESEARCH_EXCESS_TARGET:
        raise ExcessMakefileProvenanceError(
            f"Makefile line {line_number} defines the governed target through the "
            f"ambiguous pattern or wildcard expression {expression!r}; its effective "
            "target identity cannot be established statically — failing closed"
        )
    return True


def _scan_global_make_semantics(
    lines: list[str],
) -> tuple[frozenset, list[tuple[int, bool, str]]]:
    """Fail closed on execution-affecting Make syntax; recover ``.PHONY`` membership.

    A file-level construct (``.ONESHELL:``, ``.SILENT:``, ``SHELL = …``,
    ``include``, ``define`` …) changes how *every* target — research-excess
    included — is parsed or executed while leaving the recipe text byte-identical,
    so the whole file is scanned, not merely the target's own lines.  Because GNU
    Make strips leading whitespace from non-recipe lines, the scan runs on stripped
    logical lines: ``  .IGNORE:`` and ``\\t.SILENT: research-excess`` written as a
    continuation are caught exactly like their column-0 forms.

    ``.PHONY`` is the one accepted special target, and it is represented rather
    than ignored: its membership decides whether an existing file named
    ``research-excess`` would suppress the recipe, so every ``.PHONY`` member list
    in the file is collected and returned for truthful recording in provenance.

    The same pass judges the *target identity* of every rule line in the file
    (:func:`_check_rule_target_identity`) and the value of every variable
    definition, so a multi-target rule, a variable-derived target name, a
    pattern/glob target, a variable whose literal value is ``research-excess``, and
    any duplicate mixture of literal and derived definitions all fail closed rather
    than leaving the recorded authority unchanged.

    This runs during a pure parse, strictly before any command could be executed by
    any tool.
    """
    phony: set = set()
    governed_rule_lines: list[int] = []
    grouped = _logical_make_lines(lines)
    for start, is_recipe, text in grouped:
        if is_recipe:
            continue
        stripped = text.strip()
        if not stripped:
            continue
        if _SHELL_ASSIGNMENT_RE.match(stripped):
            raise ExcessMakefileProvenanceError(
                f"Makefile line {start + 1} assigns an execution-affecting shell "
                "variable (SHELL/MAKESHELL/MAKEFLAGS/.SHELLFLAGS), which changes how "
                "the research-excess recipe is executed while leaving its text "
                "unchanged; this is outside the accepted static subset — failing closed"
            )
        special = _SPECIAL_TARGET_RE.match(stripped)
        if special:
            name = special.group(1)
            if name not in _ALLOWED_SPECIAL_TARGETS:
                raise ExcessMakefileProvenanceError(
                    f"Makefile line {start + 1} declares the execution-affecting "
                    f"special target {name!r}, which is outside the accepted static "
                    "subset and could change how research-excess runs; failing closed"
                )
            phony_match = _PHONY_RULE_RE.match(stripped)
            if phony_match is None:
                raise ExcessMakefileProvenanceError(
                    f"Makefile line {start + 1} uses an unsupported '.PHONY' form "
                    f"({stripped!r}); the accepted subset requires a single ':' "
                    "followed by a literal member list — failing closed"
                )
            members = phony_match.group("members")
            _reject_unsafe_make_text(members, where=".PHONY member list")
            phony.update(members.split())
            continue
        directive = _GLOBAL_DIRECTIVE_RE.match(stripped)
        if directive:
            raise ExcessMakefileProvenanceError(
                f"Makefile line {start + 1} uses the {directive.group(1)!r} directive, "
                "which is outside the accepted static subset (it can inject or alter "
                "rules or variables affecting research-excess); failing closed"
            )
        # A whole-line variable definition is judged before rule detection: its
        # value may legitimately contain ':' (a URL), and a variable whose literal
        # value is the governed target could be used to derive a target name that
        # only expansion would reveal.
        definition = _VARIABLE_DEFINITION_RE.match(stripped)
        if definition:
            value = definition.group("value")
            if RESEARCH_EXCESS_TARGET in value.split():
                raise ExcessMakefileProvenanceError(
                    f"Makefile line {start + 1} defines the variable "
                    f"{definition.group('name')!r} as {RESEARCH_EXCESS_TARGET!r}; a "
                    "variable that resolves to the governed target could derive a "
                    "target definition this static parser cannot distinguish from an "
                    "unrelated rule without expanding Make — failing closed"
                )
            continue
        if _check_rule_target_identity(stripped, start + 1):
            governed_rule_lines.append(start)
    if len(governed_rule_lines) > 1:
        raise ExcessMakefileProvenanceError(
            "multiple effective research-excess target definitions were found "
            f"(Makefile lines {[i + 1 for i in governed_rule_lines]}); duplicate or "
            "derived duplicate definitions fail closed rather than guessing which "
            "recipe GNU Make would execute"
        )
    return frozenset(phony), grouped


def _strip_make_comment(text: str) -> str:
    """Drop an unescaped ``#`` comment from a Make rule/prerequisite line.

    A backslash-escaped ``\\#`` is a literal hash and is preserved; the first
    unescaped ``#`` and everything after it is a comment and is removed, so a
    comment is never tokenised as a prerequisite.
    """
    out: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            out.append(ch)
            out.append(text[i + 1])
            i += 2
            continue
        if ch == "#":
            break
        out.append(ch)
        i += 1
    return "".join(out)


def _physical_lines(text: str) -> list[str]:
    """Split Makefile text into physical lines without trailing newlines."""
    return text.split("\n")


def _reject_unsafe_make_text(text: str, *, where: str) -> None:
    """Fail closed on any dynamic or recursive construct in ``text``.

    This runs during a pure parse, so a rejection happens strictly before any
    command could be executed by any tool.
    """
    if _MAKE_EXPANSION_RE.search(text):
        raise ExcessMakefileProvenanceError(
            f"{where} contains a make variable/function reference outside the "
            f"accepted static subset (e.g. $(...) / ${{...}}): {text!r}"
        )
    if "$(MAKE)" in text or "${MAKE}" in text or _RECURSIVE_MAKE_RE.search(text):
        raise ExcessMakefileProvenanceError(
            f"{where} invokes a recursive make, which is outside the accepted "
            f"static subset: {text!r}"
        )


def _effective_make_provenance(
    *, root: Path = ROOT, makefile: str = MAKEFILE_NAME
) -> dict:
    """Statically parse the single research-excess rule; never run GNU Make.

    ``root``/``makefile`` default to the repository Makefile; tests point them at
    temporary Makefiles.  The returned prerequisites and verbatim recipe lines are
    the only provenance dependency of this task, and computing them launches no
    subprocess and touches no file other than reading the Makefile bytes.
    """
    path = Path(root) / makefile
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ExcessMakefileProvenanceError(
            f"cannot read Makefile for research-excess provenance: {exc}"
        ) from exc

    lines = _physical_lines(text)

    # 0) Fail closed on any execution-affecting special target, shell assignment,
    #    or global directive anywhere in the file: these change how research-excess
    #    itself is parsed or executed, so a static recipe read would otherwise
    #    misrepresent the run. The same pass recovers '.PHONY' membership, which is
    #    execution-affecting and is recorded truthfully rather than ignored.
    phony_members, grouped = _scan_global_make_semantics(lines)

    # 1) Locate every research-excess *rule* line. Exactly one is required; zero
    #    (removed/renamed) and duplicates both fail closed. Detection runs on the
    #    start of each logical line with leading spaces stripped, so a
    #    space-indented duplicate rule — which GNU Make honours and which would
    #    override the recipe — is seen rather than skipped. Tab-started (recipe)
    #    logical lines and continuation lines are never rule lines.
    rule_indices: list[int] = []
    rule_heads: dict[int, str] = {}
    for start, is_recipe, _text in grouped:
        if is_recipe:
            continue
        head = lines[start].lstrip(" ")
        if _RESEARCH_EXCESS_RULE_RE.match(head):
            rule_indices.append(start)
            rule_heads[start] = head
        elif _RESEARCH_EXCESS_UNSUPPORTED_RE.match(head):
            raise ExcessMakefileProvenanceError(
                "research-excess is defined with an unsupported '::' or ':=' form; "
                "the accepted subset requires a single simple rule"
            )
    if not rule_indices:
        raise ExcessMakefileProvenanceError(
            f"Makefile target {RESEARCH_EXCESS_TARGET!r} was not found; the recipe "
            "is a required R3-TGT-01 regeneration-provenance authority"
        )
    if len(rule_indices) > 1:
        raise ExcessMakefileProvenanceError(
            "multiple research-excess rule definitions were found (lines "
            f"{[i + 1 for i in rule_indices]}); duplicate definitions fail closed "
            "rather than guessing which one GNU Make would execute"
        )

    rule_index = rule_indices[0]
    match = _RESEARCH_EXCESS_RULE_RE.match(rule_heads[rule_index])
    assert match is not None  # guaranteed by the rule_indices membership above

    # 2) Merge prerequisite continuations (a trailing backslash continues the
    #    prerequisite list onto the next physical line). An inline '#' comment is
    #    stripped from each physical line first, so a comment is never tokenised as
    #    a prerequisite and a backslash inside a comment never continues the line.
    prereq_text = _strip_make_comment(match.group("prereqs"))
    cursor = rule_index
    while prereq_text.rstrip().endswith("\\"):
        prereq_text = prereq_text.rstrip()[:-1] + " "
        cursor += 1
        if cursor >= len(lines):
            break
        prereq_text += _strip_make_comment(lines[cursor])
    # A static pattern rule ('research-excess: %.o: %.c') carries a second rule
    # colon in what would otherwise be the prerequisite list. Its effective target
    # identity and prerequisites cannot be established statically, so it fails
    # closed instead of being mis-tokenised as ordinary prerequisites.
    if _rule_target_expression(prereq_text) is not None:
        raise ExcessMakefileProvenanceError(
            "research-excess is written as a static pattern rule (a second rule "
            f"colon appears after the target: {prereq_text!r}); its effective target "
            "identity cannot be established statically — failing closed"
        )
    # A ';' recipe on the rule line itself is an execution-affecting command that
    # this parser does not record; accepting it would silently drop a command from
    # the recorded authority.
    if ";" in prereq_text:
        raise ExcessMakefileProvenanceError(
            "research-excess carries a ';' recipe on its rule line "
            f"({prereq_text!r}); an inline command is outside the accepted static "
            "subset and must never be silently dropped — failing closed"
        )
    # A target-specific/global variable definition on the rule line (e.g.
    # 'research-excess: VAR = value') is not a prerequisite list; it is an
    # unsupported target-assignment form and fails closed rather than being
    # mis-tokenised as prerequisites.
    if _ASSIGNMENT_OPERATOR_RE.search(prereq_text):
        raise ExcessMakefileProvenanceError(
            "research-excess is written with a target-specific variable assignment "
            f"rather than a plain prerequisite list: {prereq_text!r}; failing closed"
        )
    _reject_unsafe_make_text(prereq_text, where="research-excess prerequisites")
    # Drop an order-only '|' separator; order-only prerequisites still count as
    # prerequisites for provenance purposes.
    prerequisites = [tok for tok in prereq_text.replace("|", " ").split() if tok]
    if ".WAIT" in prerequisites:
        raise ExcessMakefileProvenanceError(
            "research-excess uses the '.WAIT' ordering prerequisite, which is outside "
            "the accepted static subset; failing closed"
        )

    # 3) Collect the contiguous tab-indented recipe block immediately following
    #    the rule (after any consumed prerequisite-continuation lines). A blank
    #    line, a comment, or any column-0 content terminates the block; a backslash
    #    continuation must continue onto another tab-indented recipe line, and any
    #    tab-indented command appearing later (after a blank or comment line, before
    #    the next column-0 rule) is an ambiguous, silently-ignored recipe line and
    #    fails closed instead.
    recipe: list[str] = []
    i = cursor + 1
    while i < len(lines):
        line = lines[i]
        if line.startswith("\t"):
            body = line[1:]
            while body.rstrip().endswith("\\"):
                if i + 1 >= len(lines) or not lines[i + 1].startswith("\t"):
                    raise ExcessMakefileProvenanceError(
                        "a research-excess recipe line ends with an ambiguous "
                        "backslash continuation not followed by a tab-indented recipe "
                        f"line: {body!r}; failing closed"
                    )
                i += 1
                body = body.rstrip()[:-1] + "\n" + lines[i][1:]
            recipe.append(body)
            i += 1
            continue
        break

    if not recipe:
        raise ExcessMakefileProvenanceError(
            f"no recipe was found for {RESEARCH_EXCESS_TARGET!r}; the excess "
            "artifacts cannot be regenerated and provenance cannot be recorded"
        )

    # A recipe command separated from the block by a blank or comment line must
    # never be silently dropped: scan the gap up to the next column-0 rule/target
    # and fail closed on any orphan tab-indented command.
    scan = i
    while scan < len(lines):
        line = lines[scan]
        if line.startswith("\t"):
            raise ExcessMakefileProvenanceError(
                f"an ambiguous tab-indented command appears at Makefile line "
                f"{scan + 1} after the research-excess recipe block (separated by a "
                "blank or comment line); a recipe command must never be silently "
                "ignored — failing closed"
            )
        if not line.strip() or line.lstrip().startswith("#"):
            scan += 1
            continue
        break

    # 4) Enforce the recipe control-prefix and dynamic-construct contract. A '+'
    #    prefix forces execution even under a dry run and is refused; '@' and '-'
    #    are execution-significant and preserved verbatim in the recorded recipe.
    for command in recipe:
        _reject_unsafe_make_text(command, where="research-excess recipe")
        prefix_run = command[: len(command) - len(command.lstrip("@-+ \t"))]
        if "+" in prefix_run:
            raise ExcessMakefileProvenanceError(
                "a '+' recipe prefix forces command execution and is outside the "
                f"accepted non-executing subset: {command!r}"
            )

    return {
        "prerequisites": prerequisites,
        "effective_recipe": recipe,
        "recipe_source_file": _display_path(path),
        "duplicate_recipe_overridden": False,
        "phony": RESEARCH_EXCESS_TARGET in phony_members,
    }


def _recipe_provenance_digest(
    prerequisites: list[str], recipe: list[str], *, phony: bool
) -> str:
    """Deterministic sha256 over the effective target/prerequisites/phony/recipe record.

    Repository-relative and machine-independent: it contains no source-file line
    numbers (so an unrelated target added above research-excess does not move it)
    and no environment-derived values, only the parsed prerequisites, the
    ``.PHONY`` membership of this target, and the verbatim recipe lines for this
    one target.  ``.PHONY`` membership is inside the digest because it is
    execution-affecting: without it, an existing file named ``research-excess``
    would make the target up to date and the recipe would not run at all, while the
    recorded recipe text stayed identical.
    """
    canonical = "\n".join(
        [
            f"target:{RESEARCH_EXCESS_TARGET}",
            "prerequisites:" + " ".join(prerequisites),
            f"phony:{'yes' if phony else 'no'}",
            "recipe:",
            *recipe,
        ]
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_makefile_target_provenance() -> dict:
    """Record the research-excess recipe as the task's Makefile provenance.

    The authority is a static, non-executing parse of the Makefile bytes under the
    narrow contract in :data:`MAKEFILE_ACCEPTED_SUBSET`; GNU Make is never invoked,
    so no code path can execute the recipe while discovering it.  Editing the
    recipe, changing its prerequisites, or removing/duplicating the target all
    change the recorded value or fail closed, while unrelated targets and unrelated
    variables never do.
    """
    makefile_path = ROOT / MAKEFILE_NAME
    effective = _effective_make_provenance()
    return {
        "makefile": _display_path(makefile_path),
        "target": RESEARCH_EXCESS_TARGET,
        "authority": (
            "Static, non-executing parse of the Makefile bytes under a narrow "
            "research-excess contract; GNU Make is never invoked and no recipe "
            "command can execute during provenance computation"
        ),
        "accepted_subset": MAKEFILE_ACCEPTED_SUBSET,
        "make_invoked": False,
        "prerequisites": effective["prerequisites"],
        "recipe": effective["effective_recipe"],
        "recipe_source_file": effective["recipe_source_file"],
        "duplicate_recipe_overridden": effective["duplicate_recipe_overridden"],
        "phony": effective["phony"],
        "phony_semantics": (
            "True when research-excess is declared a .PHONY member (any .PHONY line "
            "in the file, leading whitespace and backslash continuations included). "
            "Membership is execution-affecting — without it an existing file named "
            "'research-excess' would make the target up to date and the recipe would "
            "not run — so it is recorded truthfully and hashed, never ignored."
        ),
        "recipe_sha256": _recipe_provenance_digest(
            effective["prerequisites"],
            effective["effective_recipe"],
            phony=effective["phony"],
        ),
        "recipe_sha256_definition": (
            "sha256 of the newline-joined parsed authority: a 'target:<name>' line, "
            "a 'prerequisites:<space-joined prerequisites>' line, a "
            "'phony:<yes|no>' line, a 'recipe:' line, and each verbatim recipe "
            "command line (execution-significant '@'/'-' prefixes preserved). No "
            "source line numbers and no environment-derived values: "
            "repository-relative and machine-independent."
        ),
        "provenance_scope": (
            "Only the research-excess prerequisites and verbatim recipe lines are a "
            "provenance dependency of this task. The whole Makefile is an invocation "
            "wrapper, not a statistical source input, so unrelated targets or "
            "variables added by other tasks do not change this recipe hash and do "
            "not stale these artifacts, while a change to the research-excess recipe "
            "or its prerequisites always does."
        ),
    }


# ---------------------------------------------------------------------------
# Frozen R3-TGT-01 protected boundary
# ---------------------------------------------------------------------------


def _assert_relative_clean(relative: str) -> None:
    """Reject an absolute or traversing frozen-boundary authority path."""
    candidate = Path(relative)
    if candidate.is_absolute():
        raise ExcessFrozenBoundaryError(
            f"frozen-boundary member path must be repository-relative: {relative!r}"
        )
    if ".." in candidate.parts:
        raise ExcessFrozenBoundaryError(
            f"frozen-boundary member path must not traverse with '..': {relative!r}"
        )


def _assert_no_symlink_ancestors(root: Path, target: Path) -> None:
    """lstat every component from ``root`` down to ``target``; reject symlinks.

    A protected member replaced by a symlink — or living under a symlinked parent
    that points outside the repository — must never be followed and hashed as
    though it were a genuine historical member.
    """
    try:
        relative = target.relative_to(root)
    except ValueError as exc:
        raise ExcessFrozenBoundaryError(
            f"frozen-boundary member is not inside the repository root: {target}"
        ) from exc
    walked = root
    for part in relative.parts:
        walked = walked / part
        if walked.is_symlink():
            raise ExcessFrozenBoundaryError(
                f"frozen-boundary path passes through a symlink component: {walked}"
            )


def _collect_regular_files(base: Path, into: list[Path]) -> None:
    """Recursively collect regular files under ``base`` without following symlinks.

    Every entry is inspected with ``lstat`` (``follow_symlinks=False``): a symlink
    is refused rather than followed, a directory is descended, a regular file is
    collected, and any other type (device, FIFO, socket) is refused.
    """
    with os.scandir(base) as scan:
        entries = sorted(scan, key=lambda entry: entry.name)
    for entry in entries:
        path = Path(entry.path)
        if entry.is_symlink():
            raise ExcessFrozenBoundaryError(
                f"a symlink is not a permitted frozen-boundary member: {path}"
            )
        info = entry.stat(follow_symlinks=False)
        mode = info.st_mode
        if stat.S_ISDIR(mode):
            _collect_regular_files(path, into)
        elif stat.S_ISREG(mode):
            into.append(path)
        else:
            raise ExcessFrozenBoundaryError(
                f"a non-regular file is not a permitted frozen-boundary member: {path}"
            )


def _frozen_boundary_members(root: Path) -> list[tuple[str, str]]:
    """``(<repo-relative posix path>, sha256)`` for every frozen-boundary member.

    Membership is the explicit historical allow-list of
    :data:`FROZEN_BOUNDARY_DATA_DIRS`, :data:`FROZEN_BOUNDARY_EXPERIMENT_DIRS`,
    and :data:`FROZEN_BOUNDARY_EXTRA_FILES`.  Namespaces that are not on the
    allow-list — including any added by later, unrelated tasks — are never
    members.  Every member is validated before it is hashed: no symlinked
    ancestor or member is followed, every member is a regular file that resolves
    inside the repository, and duplicate normalized paths are rejected.  Members
    are returned sorted by path so the digest is deterministic and identical to
    the historical enumeration for an unmodified repository.
    """
    root_resolved = root.resolve()
    collected: list[Path] = []

    def add_namespace(base: Path) -> None:
        _assert_relative_clean(base.relative_to(root).as_posix())
        _assert_no_symlink_ancestors(root, base)
        if base.is_symlink():
            raise ExcessFrozenBoundaryError(
                f"frozen-boundary namespace replaced by a symlink: {base}"
            )
        if not base.exists():
            # A never-created allow-listed namespace contributes no members, exactly
            # as the historical enumeration treated an absent directory.
            return
        if not base.is_dir():
            raise ExcessFrozenBoundaryError(
                f"frozen-boundary namespace is not a directory: {base}"
            )
        _collect_regular_files(base, collected)

    for name in FROZEN_BOUNDARY_DATA_DIRS:
        add_namespace(root / "data" / name)
    for name in FROZEN_BOUNDARY_EXPERIMENT_DIRS:
        add_namespace(root / "experiments" / name)
    for relative in FROZEN_BOUNDARY_EXTRA_FILES:
        _assert_relative_clean(relative)
        candidate = root / relative
        _assert_no_symlink_ancestors(root, candidate)
        try:
            info = os.lstat(candidate)
        except FileNotFoundError as exc:
            raise ExcessFrozenBoundaryError(
                f"required frozen-boundary member is missing: {relative}"
            ) from exc
        if stat.S_ISLNK(info.st_mode):
            raise ExcessFrozenBoundaryError(
                f"required frozen-boundary member replaced by a symlink: {candidate}"
            )
        if not stat.S_ISREG(info.st_mode):
            raise ExcessFrozenBoundaryError(
                f"required frozen-boundary member is not a regular file: {candidate}"
            )
        collected.append(candidate)

    # Reject duplicate normalized paths and prove containment before any hashing.
    seen: dict[str, Path] = {}
    for path in collected:
        relative = path.relative_to(root).as_posix()
        if ".." in Path(relative).parts:
            raise ExcessFrozenBoundaryError(
                f"frozen-boundary member path traverses with '..': {relative}"
            )
        if relative in seen:
            raise ExcessFrozenBoundaryError(
                f"duplicate normalized frozen-boundary member path: {relative}"
            )
        seen[relative] = path
        resolved = path.resolve()
        if resolved != root_resolved and root_resolved not in resolved.parents:
            raise ExcessFrozenBoundaryError(
                f"frozen-boundary member resolves outside the repository: {path}"
            )

    # Hash only after every containment and file-type check has passed, and hash
    # each member through a descriptor anchored beneath the repository root — never
    # by reopening the previously validated pathname — so a symlink or file swapped
    # in after validation is refused rather than followed.
    try:
        root_fd = os.open(
            str(root), os.O_RDONLY | _EX_O_DIRECTORY | _EX_O_NOFOLLOW
        )
    except OSError as exc:
        raise ExcessFrozenBoundaryError(
            f"frozen-boundary repository root could not be anchored: {exc}"
        ) from exc
    try:
        return [
            (relative, _sha256_member_anchored(root_fd, relative))
            for relative in sorted(seen)
        ]
    finally:
        os.close(root_fd)


def _frozen_boundary_digest(members: list[tuple[str, str]]) -> str:
    """sha256 over the sorted ``<path>:<sha256>`` records of the boundary members."""
    joined = "\n".join(f"{relative}:{digest}" for relative, digest in members)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def frozen_boundary_files(root: Path) -> list[Path]:
    """Absolute paths of the frozen-boundary members (one shared discovery rule)."""
    return [root / relative for relative, _digest in _frozen_boundary_members(root)]


def verify_frozen_boundary_digest(
    digest: str, *, expected: str = FROZEN_PROTECTED_BOUNDARY_SHA256
) -> None:
    """Fail closed unless ``digest`` matches the pinned frozen-boundary authority.

    Keeps the boundary from being silently redefined from whatever files happen
    to exist now: a modified or removed original member changes the digest and is
    rejected here.
    """
    if digest != expected:
        raise ExcessFrozenBoundaryError(
            "frozen R3-TGT-01 protected boundary does not match its pinned authority: "
            f"expected {expected}, computed {digest}. The boundary is a fixed historical "
            "set and is never silently redefined from the current filesystem; investigate "
            "the change, or, if an original member changed deliberately, update the pinned "
            "authority on purpose."
        )


def build_frozen_protected_boundary() -> dict:
    """Enumerate, verify against the pinned authority, and describe the boundary."""
    members = _frozen_boundary_members(ROOT)
    digest = _frozen_boundary_digest(members)
    verify_frozen_boundary_digest(digest)
    by_root: dict[str, int] = {}
    for relative, _digest in members:
        parts = relative.split("/")
        key = "/".join(parts[:2]) if len(parts) > 1 else relative
        by_root[key] = by_root.get(key, 0) + 1
    return {
        "policy": (
            "Curated data and the generated namespaces that already existed when "
            "R3-TGT-01 was frozen, which this excess regeneration must never mutate. "
            "Explicit historical allow-list: namespaces added by later, unrelated "
            "governed tasks are not members and are protected by their own tasks, so "
            "adding one never changes this boundary."
        ),
        "data_roots": [f"data/{name}" for name in FROZEN_BOUNDARY_DATA_DIRS],
        "experiment_roots": [
            f"experiments/{name}" for name in FROZEN_BOUNDARY_EXPERIMENT_DIRS
        ],
        "extra_files": list(FROZEN_BOUNDARY_EXTRA_FILES),
        "excluded_namespaces": [
            "experiments/results_excess (this task's own output namespace; verified "
            "separately as this task's artifacts, not as a boundary member)"
        ],
        "later_unrelated_additions_are_members": False,
        "member_count": len(members),
        "member_count_by_root": dict(sorted(by_root.items())),
        "members_sha256": digest,
        "members_pinned_authority_sha256": FROZEN_PROTECTED_BOUNDARY_SHA256,
        "members_sha256_definition": (
            "sha256 of the newline-joined '<repo-relative-posix-path>:<sha256>' records "
            "for every boundary member, sorted by path. A content digest, not a file "
            "count: it detects modification or removal of an original member and is "
            "unchanged by later, unrelated namespace additions."
        ),
    }


def _json_safe(value: object) -> object:
    """Coerce estimator parameters into deterministic, strictly-valid JSON."""
    if isinstance(value, (bool, str)) or value is None:
        return value
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        number = float(value)
        return number if math.isfinite(number) else repr(number)
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in sorted(value.items())}
    return f"<{type(value).__module__}.{type(value).__name__}>"


# ---------------------------------------------------------------------------
# Estimand-invariance audit
# ---------------------------------------------------------------------------


def _excess_derivation_from_source() -> tuple[str, str]:
    """Parse the pipeline source for the excess target's minuend and subtrahend.

    The nominal column is traced rather than assumed: the pipeline's assignment
    to ``next_year_excess_return_vs_bist100`` is located in the AST and both
    operand column names are read off the subtraction.  A renamed or restructured
    derivation therefore fails the audit instead of silently invalidating it.
    """
    path = ROOT / EXCESS_DERIVATION_AUTHORITY
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as parse_error:
        raise ExcessEstimandError(
            f"cannot read the excess-target derivation authority {EXCESS_DERIVATION_AUTHORITY}: "
            f"{parse_error}"
        ) from parse_error

    def _column(node: ast.AST) -> str | None:
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, str)
        ):
            return node.slice.value
        return None

    found: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        if _column(node.targets[0]) != TARGET_COLUMN:
            continue
        value = node.value
        if not isinstance(value, ast.BinOp) or not isinstance(value.op, ast.Sub):
            continue
        left = _column(value.left)
        right = _column(value.right)
        if left is not None and right is not None:
            found.append((left, right))

    if len(found) != 1:
        raise ExcessEstimandError(
            f"expected exactly one `{TARGET_COLUMN} = <nominal> - <benchmark>` assignment in "
            f"{EXCESS_DERIVATION_AUTHORITY}; found {len(found)}: {found}"
        )
    return found[0]


def resolve_nominal_target_column() -> dict:
    """Resolve the nominal target column from repository authority, not assumption.

    Two independent authorities must agree:

    * ``run_experiments.TARGETS`` declares the evaluated targets in order, and its
      first entry is the repository's primary target; and
    * the pipeline source derives the excess column as ``nominal - benchmark``.

    The name is accepted only when the pipeline's minuend is exactly the declared
    primary target, so a rename on either side fails the run.
    """
    targets = list(exp.TARGETS)
    if not targets:
        raise ExcessEstimandError("run_experiments.TARGETS is empty; no primary target declared")
    nominal = targets[0]
    if TARGET_COLUMN not in targets:
        raise ExcessEstimandError(
            f"{TARGET_COLUMN} is not among the declared targets {targets}"
        )
    minuend, subtrahend = _excess_derivation_from_source()
    if minuend != nominal:
        raise ExcessEstimandError(
            f"the pipeline derives {TARGET_COLUMN} from {minuend!r}, but the declared "
            f"primary target is {nominal!r}; the estimand audit refuses to guess"
        )
    if subtrahend != BENCHMARK_COLUMN_EXPECTED:
        raise ExcessEstimandError(
            f"the pipeline subtracts {subtrahend!r}, not the expected benchmark column "
            f"{BENCHMARK_COLUMN_EXPECTED!r}"
        )
    return {
        "nominal_target_column": nominal,
        "excess_target_column": TARGET_COLUMN,
        "benchmark_column": subtrahend,
        "declared_targets_in_order": targets,
        "nominal_target_authority": NOMINAL_TARGET_AUTHORITY,
        "excess_derivation_authority": EXCESS_DERIVATION_AUTHORITY,
        "derivation": f"{TARGET_COLUMN} = {minuend} - {subtrahend}",
        "derivation_traced_not_assumed": True,
        "trace_method": (
            "AST parse of the pipeline assignment, cross-checked against the declared "
            "target order; no column name is hardcoded as the nominal target"
        ),
    }


def build_estimand_invariance_audit(predictions: pd.DataFrame) -> dict:
    """Prove per year that subtracting the benchmark leaves stock-return ranks fixed.

    For every evaluation year the audit joins the trusted nominal target onto the
    exact evaluated rows, checks that ``nominal - excess`` is one common value
    inside that year, checks that the value equals the persisted benchmark
    column, and counts rank mismatches between the two targets.  A non-common
    subtrahend or any rank mismatch raises :class:`ExcessEstimandError`.
    """
    authority = resolve_nominal_target_column()
    nominal_column = authority["nominal_target_column"]
    benchmark_column = authority["benchmark_column"]

    modeling_path = exp._modeling_csv()
    modeling = pd.read_csv(modeling_path)
    required = {"ticker", "target_year", nominal_column, benchmark_column, TARGET_COLUMN}
    missing = sorted(required - set(modeling.columns))
    if missing:
        raise ExcessEstimandError(
            f"{_display_path(modeling_path)} is missing columns required by the estimand "
            f"audit: {missing}"
        )
    trusted = modeling[sorted(required)].copy()

    # One model's rows carry the evaluated cohort and realized outcomes; every
    # model shares them, which is verified rather than assumed.
    per_model_rows = {
        str(model): group[["ticker", "year", "y_true"]]
        .sort_values(["year", "ticker"])
        .reset_index(drop=True)
        for model, group in predictions.groupby("model", sort=True)
    }
    reference_name = sorted(per_model_rows)[0]
    reference = per_model_rows[reference_name]
    for name, frame in per_model_rows.items():
        if not reference.equals(frame):
            raise ExcessEstimandError(
                f"evaluated cohort or realized outcomes differ between models "
                f"{reference_name!r} and {name!r}; the estimand audit requires one shared panel"
            )

    per_year: list[dict] = []
    total_mismatches = 0
    for year, group in reference.groupby("year", sort=True):
        evaluation_year = int(year)
        merged = group.merge(
            trusted,
            left_on=["ticker", "year"],
            right_on=["ticker", "target_year"],
            how="left",
            validate="one_to_one",
        )
        if merged[nominal_column].isna().any() or merged[benchmark_column].isna().any():
            absent = sorted(
                merged.loc[
                    merged[nominal_column].isna() | merged[benchmark_column].isna(),
                    "ticker",
                ].tolist()
            )
            raise ExcessEstimandError(
                f"{evaluation_year}: trusted nominal or benchmark values are missing for "
                f"{absent[:5]}; the audit never fills them"
            )

        evaluated_excess = merged["y_true"].to_numpy(dtype=float)
        trusted_excess = merged[TARGET_COLUMN].to_numpy(dtype=float)
        if not np.allclose(evaluated_excess, trusted_excess, rtol=0.0, atol=1e-9):
            raise ExcessEstimandError(
                f"{evaluation_year}: evaluated y_true does not match the trusted "
                f"{TARGET_COLUMN} column"
            )

        nominal = merged[nominal_column].to_numpy(dtype=float)
        implied = nominal - evaluated_excess
        spread = float(np.max(implied) - np.min(implied)) if len(implied) else 0.0
        persisted = merged[benchmark_column].to_numpy(dtype=float)
        persisted_spread = (
            float(np.max(persisted) - np.min(persisted)) if len(persisted) else 0.0
        )
        if spread > BENCHMARK_COMMON_VALUE_TOLERANCE:
            raise ExcessEstimandError(
                f"{evaluation_year}: nominal minus excess is not one common value within the "
                f"year (spread {spread!r} exceeds {BENCHMARK_COMMON_VALUE_TOLERANCE!r}); the "
                "expected common benchmark subtraction does not hold"
            )
        if persisted_spread > BENCHMARK_COMMON_VALUE_TOLERANCE:
            raise ExcessEstimandError(
                f"{evaluation_year}: the persisted {benchmark_column} column is not constant "
                f"within the year (spread {persisted_spread!r})"
            )
        common = float(np.mean(implied))
        if abs(common - float(np.mean(persisted))) > BENCHMARK_COMMON_VALUE_TOLERANCE:
            raise ExcessEstimandError(
                f"{evaluation_year}: the implied subtrahend {common!r} does not match the "
                f"persisted {benchmark_column} value {float(np.mean(persisted))!r}"
            )

        nominal_ranks = pd.Series(nominal).rank(method="average").to_numpy()
        excess_ranks = pd.Series(evaluated_excess).rank(method="average").to_numpy()
        mismatches = int(np.sum(nominal_ranks != excess_ranks))
        total_mismatches += mismatches
        per_year.append(
            {
                "evaluation_year": evaluation_year,
                "evaluated_rows": int(len(merged)),
                "common_benchmark_return_pct": round(common, 10),
                "persisted_benchmark_column_value": round(float(np.mean(persisted)), 10),
                "within_year_subtrahend_spread": spread,
                "common_subtrahend_confirmed": True,
                "rank_mismatch_count": mismatches,
                "ranks_identical": mismatches == 0,
            }
        )

    years = [entry["evaluation_year"] for entry in per_year]
    if tuple(years) != EXPECTED_EVALUATION_YEARS:
        raise ExcessEstimandError(
            f"the estimand audit expects evaluation years {list(EXPECTED_EVALUATION_YEARS)}; "
            f"got {years}"
        )
    if total_mismatches != 0:
        raise ExcessEstimandError(
            f"benchmark subtraction changed within-year ranks in {total_mismatches} rows; the "
            "ordinal-invariance precondition does not hold"
        )

    return {
        "audit_id": "estimand_rank_invariance",
        "evaluated_years": years,
        **authority,
        "rank_method": "average ranks, computed independently within each evaluation year",
        "within_year_subtrahend_tolerance": BENCHMARK_COMMON_VALUE_TOLERANCE,
        "per_year": per_year,
        "total_rank_mismatch_count": total_mismatches,
        "ranks_identical_in_every_year": total_mismatches == 0,
        "estimand": "within-year ordinal cross-sectional ranking",
        "estimand_statement": ESTIMAND_STATEMENT,
        "evaluates_ordinal_cross_sectional_ranking": True,
        "evaluates_benchmark_relative_magnitude_accuracy": False,
        "estimates_alpha": False,
        "estimates_economic_outperformance": False,
        "establishes_investment_value": False,
        "represents_a_tradable_strategy": False,
        "fitting_effect_note": ESTIMAND_FITTING_NOTE,
        "benchmark_subtraction_may_affect_fitting": True,
        "benchmark_subtraction_alters_within_year_evaluation_ranks": False,
        "interpretation": (
            "Within each evaluation year the benchmark subtraction is one common constant, so "
            f"the {TARGET_COLUMN} ranks equal the {nominal_column} ranks in every year and the "
            "total rank mismatch count is 0. The within-year Spearman IC reported here is "
            "therefore the same ordinal ranking estimand as on the nominal basis, evaluated on "
            "a different cohort. Identical evaluation ranks do not make the two analyses "
            "identical: the shifted target can still change what the models fit, and an "
            "unchanged ordinal estimand is not evidence of alpha, benchmark-relative magnitude "
            "accuracy, investment value, or a tradable strategy."
        ),
        "failure_policy": (
            "The run fails with ExcessEstimandError if the common within-year benchmark "
            "subtraction or the resulting rank invariance does not hold."
        ),
    }


# ---------------------------------------------------------------------------
# Ticker-cluster bootstrap
# ---------------------------------------------------------------------------


def _is_null_scalar(value: object) -> bool:
    """Null test that never raises on exotic scalar types."""
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


BOOTSTRAP_CONTEXT = "ticker-cluster bootstrap"
PERMUTATION_CONTEXT = "trajectory-preserving ticker permutation"


def validated_cluster_year(
    value: object,
    *,
    position: int,
    context: str = BOOTSTRAP_CONTEXT,
    error: type[ExcessPanelError] = ExcessBootstrapError,
) -> int:
    """Return a canonical integer evaluation year, or refuse the value outright.

    Nothing is floored, truncated, rounded, or coerced with ``astype(int)``
    before validation: a value becomes an ``int`` only after it has been proven
    to be a finite mathematical integer inside the expected evaluation-year set.
    Booleans, strings, non-numeric objects, NaN, and both infinities are refused
    rather than interpreted.

    ``context`` and ``error`` let the trajectory-preserving permutation reuse this
    identical contract while reporting its own analysis name and exception type;
    the defaults preserve the bootstrap's original messages exactly.
    """
    prefix = f"{context} refuses year value at row {position}"
    if isinstance(value, (bool, np.bool_)):
        raise error(f"{prefix}: booleans are not years ({value!r})")
    if value is None:
        raise error(f"{prefix}: refuses null year values")
    if isinstance(value, (str, bytes)):
        raise error(
            f"{prefix}: strings are never coerced to years ({value!r}); a canonical "
            "integer year is required"
        )
    if isinstance(value, (int, np.integer)):
        year = int(value)
    elif isinstance(value, (float, np.floating)):
        number = float(value)
        if math.isnan(number):
            raise error(f"{prefix}: refuses NaN year values")
        if math.isinf(number):
            raise error(f"{prefix}: refuses non-finite year values ({number!r})")
        if not number.is_integer():
            raise error(
                f"{prefix}: refuses a fractional year ({number!r}); no floor, "
                "truncation, or rounding is applied"
            )
        year = int(number)
    else:
        if _is_null_scalar(value):
            raise error(f"{prefix}: refuses null year values")
        raise error(
            f"{prefix}: refuses a non-numeric year ({value!r}, "
            f"{type(value).__name__}); ambiguous coercion is not attempted"
        )
    if year not in EXPECTED_EVALUATION_YEARS:
        raise error(
            f"{prefix}: {year} is outside the expected evaluation years "
            f"{list(EXPECTED_EVALUATION_YEARS)}"
        )
    return year


def validated_cluster_ticker(
    value: object,
    *,
    position: int,
    context: str = BOOTSTRAP_CONTEXT,
    error: type[ExcessPanelError] = ExcessBootstrapError,
) -> str:
    """Return a ticker identity, or refuse it; whitespace is never normalized."""
    prefix = f"{context} refuses ticker value at row {position}"
    if isinstance(value, (bool, np.bool_)):
        raise error(f"{prefix}: refuses a non-string ticker ({value!r})")
    if value is None or (not isinstance(value, str) and _is_null_scalar(value)):
        raise error(f"{prefix}: refuses null ticker values")
    if not isinstance(value, str):
        raise error(
            f"{prefix}: refuses a non-string ticker ({value!r}, {type(value).__name__})"
        )
    if not value:
        raise error(f"{prefix}: refuses an empty ticker")
    if not value.strip():
        raise error(f"{prefix}: refuses a whitespace-only ticker ({value!r})")
    if value != value.strip():
        raise error(
            f"{prefix}: refuses leading or trailing whitespace ({value!r}); the "
            "identity is not silently normalized"
        )
    return value


def _cluster_panel(
    predictions: pd.DataFrame,
    *,
    context: str = BOOTSTRAP_CONTEXT,
    error: type[ExcessPanelError] = ExcessBootstrapError,
    minimum_tickers: int = MIN_CLUSTERS,
) -> tuple[list[str], list[int], dict]:
    """Validate one model's rows and return its ticker identities and year arrays.

    The contract is the balanced 40-ticker x 3-year panel both resampling
    analyses require: no duplicate ticker/year rows, no malformed ticker or year
    values, the exact expected evaluation years, an identical ticker set in every
    year, finite targets and predictions, and enough tickers to resample at all.
    """
    required = {"ticker", "year", "y_true", "y_pred"}
    missing = sorted(required - set(predictions.columns))
    if missing:
        raise error(f"{context} requires columns {sorted(required)}; missing {missing}")
    if predictions.empty:
        raise error(f"{context} received no rows")

    # Strict cluster-key validation happens first and element by element, so no
    # malformed value can reach a grouping key or an integer cast.
    ticker_values = [
        validated_cluster_ticker(value, position=position, context=context, error=error)
        for position, value in enumerate(predictions["ticker"].tolist())
    ]
    year_values = [
        validated_cluster_year(value, position=position, context=context, error=error)
        for position, value in enumerate(predictions["year"].tolist())
    ]

    if predictions[["y_true", "y_pred"]].isna().any().any():
        raise error(
            f"{context} refuses null ticker, year, y_true, or y_pred values"
        )
    try:
        values = predictions[["y_true", "y_pred"]].to_numpy(dtype=float)
    except (TypeError, ValueError) as convert_error:
        raise error(
            f"{context} refuses non-numeric y_true or y_pred values: {convert_error}"
        ) from convert_error
    if not np.isfinite(values).all():
        raise error(f"{context} refuses non-finite predictions")

    # Every value is now a proven identity or a proven in-set integer, so the
    # canonical integer dtype can be applied safely.
    panel = pd.DataFrame(
        {
            "ticker": pd.Series(ticker_values, dtype="object"),
            "year": pd.Series(year_values, dtype="int64"),
            "y_true": values[:, 0],
            "y_pred": values[:, 1],
        }
    )

    if panel.duplicated(["ticker", "year"]).any():
        duplicated = panel[panel.duplicated(["ticker", "year"], keep=False)]
        keys = sorted({(row.ticker, int(row.year)) for row in duplicated.itertuples()})
        raise error(
            f"duplicate ticker/year rows prevent a trajectory bootstrap: {keys[:5]}"
        )

    tickers = sorted(set(ticker_values))
    years = sorted(set(year_values))
    if len(tickers) < minimum_tickers:
        raise error(
            f"{context} needs at least {minimum_tickers} tickers; got {len(tickers)}"
        )
    if tuple(years) != EXPECTED_EVALUATION_YEARS:
        raise error(
            f"{context} expects evaluation years "
            f"{list(EXPECTED_EVALUATION_YEARS)}; got {years}"
        )

    # Complete trajectories are the declared unit: every sampled ticker must
    # contribute an observation in every evaluation year.  Ragged coverage is
    # refused rather than silently degraded into a different estimator.
    per_year: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    incomplete: dict[int, list[str]] = {}
    for year in years:
        group = panel[panel["year"].eq(year)].set_index("ticker")
        absent = sorted(set(tickers) - set(group.index))
        if absent:
            incomplete[year] = absent
            continue
        ordered = group.reindex(tickers)
        per_year[year] = (
            ordered["y_true"].to_numpy(dtype=float),
            ordered["y_pred"].to_numpy(dtype=float),
        )
    if incomplete:
        detail = {year: names[:5] for year, names in sorted(incomplete.items())}
        raise error(
            "inconsistent ticker coverage prevents the declared complete-trajectory "
            f"bootstrap; tickers missing per year: {detail}"
        )
    return tickers, years, per_year


def ticker_cluster_bootstrap(
    predictions: pd.DataFrame,
    *,
    bootstraps: int = significance.DEFAULT_BOOTSTRAPS,
    seed: int = significance.DEFAULT_SEED,
    draws: np.ndarray | None = None,
) -> dict:
    """Bootstrap complete ticker trajectories for one model.

    ``N`` ticker identities are sampled with replacement from the ``N`` unique
    tickers.  A single sampled ticker vector is reused for every evaluation
    year, so a ticker's 2023, 2024, and 2025 observations always move together
    and a ticker drawn twice contributes its whole trajectory twice.  Years are
    never resampled independently.  The statistic is the equal-year mean of the
    valid within-year Spearman ICs, matching the observed pooled statistic.

    ``draws`` allows a test to supply a deterministic sample matrix; production
    runs leave it ``None`` and use the frozen seed.
    """
    if bootstraps < 1:
        raise ExcessBootstrapError("bootstraps must be positive")

    tickers, years, per_year = _cluster_panel(predictions)
    cluster_count = len(tickers)

    if draws is None:
        rng = np.random.default_rng(seed)
        draws = rng.integers(0, cluster_count, size=(bootstraps, cluster_count))
    else:
        draws = np.asarray(draws, dtype=int)
        if draws.ndim != 2 or draws.shape[1] != cluster_count:
            raise ExcessBootstrapError(
                f"supplied draws must have shape (resamples, {cluster_count}); got {draws.shape}"
            )
        if draws.size and (draws.min() < 0 or draws.max() >= cluster_count):
            raise ExcessBootstrapError("supplied draws index tickers outside the cohort")
        bootstraps = int(draws.shape[0])

    per_year_distributions: dict[int, np.ndarray] = {}
    for year in years:
        y_true, y_pred = per_year[year]
        # One sampled ticker vector, applied identically to every year.
        sampled_true = y_true[draws]
        sampled_pred = y_pred[draws]
        true_rank = pd.DataFrame(sampled_true).rank(axis=1, method="average").to_numpy()
        pred_rank = pd.DataFrame(sampled_pred).rank(axis=1, method="average").to_numpy()
        per_year_distributions[year] = significance._rowwise_correlation(
            true_rank, pred_rank
        )

    stacked = np.vstack([per_year_distributions[year] for year in years])
    valid_years_per_draw = np.sum(np.isfinite(stacked), axis=0)
    pooled = np.full(bootstraps, np.nan, dtype=float)
    usable = valid_years_per_draw > 0
    if usable.any():
        pooled[usable] = np.nanmean(stacked[:, usable], axis=0)

    valid_resamples = int(np.sum(np.isfinite(pooled)))
    invalid_resamples = int(bootstraps - valid_resamples)
    minimum_valid = max(1, math.ceil(MIN_VALID_RESAMPLE_FRACTION * bootstraps))
    if bootstraps >= MIN_VALID_RESAMPLES:
        minimum_valid = max(minimum_valid, MIN_VALID_RESAMPLES)
    if valid_resamples < minimum_valid:
        raise ExcessBootstrapError(
            f"only {valid_resamples} of {bootstraps} ticker-cluster resamples produced a "
            f"finite equal-year IC (minimum {minimum_valid}); refusing to report an interval"
        )

    interval = significance._ci(pooled)
    if not all(math.isfinite(bound) for bound in interval):
        raise ExcessBootstrapError("ticker-cluster bootstrap produced a non-finite interval")

    diagnostics = {
        "unit": BOOTSTRAP_UNIT,
        "cluster_key": BOOTSTRAP_CLUSTER_KEY,
        "clusters": cluster_count,
        "trajectory_years": years,
        "observations_per_trajectory": len(years),
        "requested_resamples": int(bootstraps),
        "valid_resamples": valid_resamples,
        "invalid_resamples": invalid_resamples,
        "seed": int(seed),
        "interval_convention": BOOTSTRAP_INTERVAL_CONVENTION,
        "statistic": "equal-year mean of the valid within-year Spearman ICs",
        "shared_sample_across_years": True,
        "multiplicity_preserved": True,
        "independent_within_year_resampling": False,
    }
    per_year_summary = {}
    for year in years:
        distribution = per_year_distributions[year]
        finite = int(np.sum(np.isfinite(distribution)))
        per_year_summary[year] = {
            "bootstrap_ci_95": significance._ci(distribution),
            "valid_resamples": finite,
            "invalid_resamples": int(len(distribution) - finite),
        }
    return {
        "bootstrap_ci_95": interval,
        "diagnostics": diagnostics,
        "pooled_distribution": pooled,
        "per_year_distributions": per_year_distributions,
        "per_year": per_year_summary,
        "tickers": tickers,
        "years": years,
    }


def cluster_bootstrap_by_model(
    predictions: pd.DataFrame,
    *,
    bootstraps: int = significance.DEFAULT_BOOTSTRAPS,
    seed: int = significance.DEFAULT_SEED,
) -> dict[str, dict]:
    """Run the ticker-cluster bootstrap once per model, each from the frozen seed."""
    results: dict[str, dict] = {}
    for model in sorted(predictions["model"].unique().tolist()):
        results[str(model)] = ticker_cluster_bootstrap(
            predictions[predictions["model"].eq(model)],
            bootstraps=bootstraps,
            seed=seed,
        )
    return results


def apply_cluster_bootstrap(report: dict, predictions: pd.DataFrame) -> dict:
    """Replace inherited within-year row intervals with ticker-cluster intervals."""
    bootstraps = int(report["analysis"]["bootstraps"])
    seed = int(report["analysis"]["seed"])
    by_model = cluster_bootstrap_by_model(
        predictions, bootstraps=bootstraps, seed=seed
    )
    split_years = {
        str(split): int(group["year"].iloc[0])
        for split, group in predictions.groupby("split", sort=True)
    }
    for result in report["models"]:
        cluster = by_model[result["model"]]
        pooled = result["pooled"]
        pooled["bootstrap_ci_95"] = cluster["bootstrap_ci_95"]
        pooled["bootstrap"] = cluster["diagnostics"]
        for split in result["exploratory_by_split"]:
            year = split_years[split["split"]]
            summary = cluster["per_year"][year]
            split["bootstrap_ci_95"] = summary["bootstrap_ci_95"]
            split["bootstrap"] = {
                "unit": BOOTSTRAP_UNIT,
                "cluster_key": BOOTSTRAP_CLUSTER_KEY,
                "year": year,
                "note": (
                    "marginal year view of the shared ticker-cluster resample; the "
                    "same sampled ticker vector is used in every year"
                ),
                "valid_resamples": summary["valid_resamples"],
                "invalid_resamples": summary["invalid_resamples"],
            }
    reference = by_model[FROZEN_ML_FAMILY[0]]["diagnostics"]
    report["analysis"]["bootstrap"] = (
        "ticker-cluster bootstrap: complete ticker trajectories resampled with "
        "replacement; one sampled ticker vector is shared by every evaluation year"
    )
    report["analysis"]["bootstrap_procedure"] = {
        "unit": BOOTSTRAP_UNIT,
        "cluster_key": BOOTSTRAP_CLUSTER_KEY,
        "clusters": reference["clusters"],
        "trajectory_years": reference["trajectory_years"],
        "requested_resamples": reference["requested_resamples"],
        "seed": seed,
        "interval_convention": BOOTSTRAP_INTERVAL_CONVENTION,
        "description": (
            "For each resample, N ticker identities are drawn with replacement from "
            "the N cohort tickers. That single ticker vector is applied to every "
            "evaluation year, so each sampled ticker contributes its complete "
            "trajectory and repeated tickers keep their multiplicity. Years are never "
            "resampled independently. The statistic is the equal-year mean of the "
            "valid within-year Spearman ICs."
        ),
        "role": (
            "descriptive sampling uncertainty; it does not replace or weaken the "
            "Bonferroni family-wise correction"
        ),
    }
    return report


# ---------------------------------------------------------------------------
# Trajectory-preserving ticker permutation (post-review sensitivity)
# ---------------------------------------------------------------------------


def trajectory_permutation_matrix(
    ticker_count: int, draws: int, seed: int
) -> np.ndarray:
    """Draw ``draws`` independent permutations of ``ticker_count`` ticker indices.

    ``argsort`` of uniform draws yields one duplicate-free permutation per row by
    construction, which is what separates this from a bootstrap: no ticker is
    ever drawn twice and none is dropped.
    """
    if ticker_count < 1:
        raise ExcessPermutationError("a permutation needs at least one ticker index")
    if draws < 1:
        raise ExcessPermutationError("permutation draws must be positive")
    rng = np.random.default_rng(seed)
    return np.argsort(rng.random((draws, ticker_count)), axis=1)


def validate_trajectory_permutation_matrix(
    matrix: np.ndarray, ticker_count: int
) -> np.ndarray:
    """Refuse anything that is not one duplicate-free mapping per draw.

    A ``(draws, years, tickers)`` array is rejected explicitly: independently
    generated per-year mappings break the trajectory-preserving contract, because
    a ticker's realized outcomes would no longer move together.
    """
    array = np.asarray(matrix)
    if array.ndim == 3:
        raise ExcessPermutationError(
            "refusing a per-year permutation mapping with shape "
            f"{array.shape}: the trajectory-preserving sensitivity applies one shared "
            "mapping to every evaluation year, so independently generated per-year "
            "mappings cannot satisfy its contract"
        )
    if array.ndim != 2:
        raise ExcessPermutationError(
            f"permutation mappings must have shape (draws, {ticker_count}); got {array.shape}"
        )
    if array.shape[1] != ticker_count:
        raise ExcessPermutationError(
            f"permutation mappings must have shape (draws, {ticker_count}); got {array.shape}"
        )
    if not np.issubdtype(array.dtype, np.integer):
        raise ExcessPermutationError(
            f"permutation mappings must be integer ticker indices; got dtype {array.dtype}"
        )
    if array.size:
        expected = np.arange(ticker_count)
        if not np.array_equal(np.sort(array, axis=1), np.broadcast_to(expected, array.shape)):
            raise ExcessPermutationError(
                "refusing a mapping that is not a duplicate-free one-to-one permutation of "
                "the ticker universe; this is a permutation test, not a bootstrap"
            )
    return array


def apply_trajectory_permutation(values: np.ndarray, mapping: np.ndarray) -> np.ndarray:
    """Relabel one year's outcome vector under a shared ticker mapping.

    ``values`` is ordered by the sorted ticker universe, so applying the same
    ``mapping`` to every year moves each ticker's whole trajectory as one block.
    """
    return np.asarray(values, dtype=float)[mapping]


def _validated_trajectory_panel(
    predictions: pd.DataFrame,
) -> tuple[list[str], list[int], dict]:
    """Validate the balanced ticker x year panel this sensitivity requires."""
    return _cluster_panel(
        predictions,
        context=PERMUTATION_CONTEXT,
        error=ExcessPermutationError,
        minimum_tickers=MIN_TRAJECTORY_TICKERS,
    )


def trajectory_preserving_permutation(
    predictions: pd.DataFrame,
    *,
    draws: int = TRAJECTORY_SENSITIVITY_DRAWS,
    seed: int = TRAJECTORY_SENSITIVITY_SEED,
    permutation_matrix: np.ndarray | None = None,
) -> dict:
    """Permute whole ticker trajectories, sharing one mapping across all years.

    Each draw permutes the sorted ticker universe once and applies that single
    mapping in 2023, 2024, and 2025.  Prediction rows stay fixed; only the
    realized-outcome labels move, and they move as complete trajectories.  The
    Spearman IC is recomputed independently within each year, the equal-year mean
    of the valid yearly ICs is the null statistic, and the two-sided Monte Carlo
    p-value is ``(extreme_count + 1) / (draw_count + 1)``.

    ``permutation_matrix`` lets a test supply deterministic mappings; production
    runs leave it ``None`` and use the frozen documented seed.
    """
    tickers, years, per_year = _validated_trajectory_panel(predictions)
    ticker_count = len(tickers)

    if permutation_matrix is None:
        if draws < 1:
            raise ExcessPermutationError("permutation draws must be positive")
        mappings = trajectory_permutation_matrix(ticker_count, draws, seed)
    else:
        mappings = validate_trajectory_permutation_matrix(permutation_matrix, ticker_count)
        draws = int(mappings.shape[0])

    observed_by_year: dict[int, float] = {}
    null_by_year: dict[int, np.ndarray] = {}
    for year in years:
        y_true, y_pred = per_year[year]
        observed_by_year[year] = significance.spearman_ic(y_true, y_pred)
        # Prediction rows are fixed; only the realized-outcome labels move, and
        # they move under the same mapping in every year.
        permuted_true = apply_trajectory_permutation(y_true, mappings)
        repeated_pred = np.broadcast_to(y_pred, permuted_true.shape)
        true_rank = pd.DataFrame(permuted_true).rank(axis=1, method="average").to_numpy()
        pred_rank = pd.DataFrame(repeated_pred).rank(axis=1, method="average").to_numpy()
        null_by_year[year] = significance._rowwise_correlation(true_rank, pred_rank)

    observed_values = [observed_by_year[year] for year in years]
    if not all(math.isfinite(value) for value in observed_values):
        raise ExcessPermutationError(
            "the observed within-year ICs are not all finite; refusing to report a "
            "trajectory-preserving p-value"
        )
    observed_ic = float(np.mean(observed_values))

    stacked = np.vstack([null_by_year[year] for year in years])
    valid_years_per_draw = np.sum(np.isfinite(stacked), axis=0)
    pooled = np.full(draws, np.nan, dtype=float)
    usable = valid_years_per_draw > 0
    if usable.any():
        pooled[usable] = np.nanmean(stacked[:, usable], axis=0)

    finite = pooled[np.isfinite(pooled)]
    valid_draws = int(finite.size)
    invalid_draws = int(draws - valid_draws)
    minimum_valid = max(1, math.ceil(MIN_VALID_PERMUTATION_FRACTION * draws))
    if draws >= MIN_VALID_PERMUTATION_DRAWS:
        minimum_valid = max(minimum_valid, MIN_VALID_PERMUTATION_DRAWS)
    if valid_draws < minimum_valid:
        raise ExcessPermutationError(
            f"only {valid_draws} of {draws} trajectory-preserving permutation draws produced a "
            f"finite equal-year IC (minimum {minimum_valid}); refusing to report a p-value"
        )

    extreme_count = int(np.sum(np.abs(finite) >= abs(observed_ic)))
    raw_p = float((extreme_count + 1) / (valid_draws + 1))
    return {
        "analysis_id": TRAJECTORY_SENSITIVITY_ID,
        "observed_ic": observed_ic,
        "observed_ic_by_year": {int(year): float(observed_by_year[year]) for year in years},
        "permutation_p_value_two_sided": raw_p,
        "observed_null_percentile": significance._percentile(observed_ic, pooled),
        "extreme_count": extreme_count,
        "requested_draws": int(draws),
        "valid_draws": valid_draws,
        "invalid_draws": invalid_draws,
        "p_value_formula": "(extreme_count + 1) / (draw_count + 1)",
        "p_value_denominator": valid_draws + 1,
        "pooled_null_distribution": pooled,
        "tickers": tickers,
        "years": years,
    }


def trajectory_sensitivity_by_model(
    predictions: pd.DataFrame,
    *,
    draws: int = TRAJECTORY_SENSITIVITY_DRAWS,
    seed: int = TRAJECTORY_SENSITIVITY_SEED,
) -> dict[str, dict]:
    """Run the sensitivity once per model, each from the same frozen seed."""
    results: dict[str, dict] = {}
    for model in sorted(predictions["model"].unique().tolist()):
        results[str(model)] = trajectory_preserving_permutation(
            predictions[predictions["model"].eq(model)],
            draws=draws,
            seed=seed,
        )
    return results


def trajectory_sensitivity_diagnostics(result: dict) -> dict:
    """Public, JSON-safe description of one model's sensitivity run."""
    return {
        "analysis_id": TRAJECTORY_SENSITIVITY_ID,
        "status": TRAJECTORY_SENSITIVITY_STATUS,
        "prespecified": False,
        "added_after_human_review": True,
        "replaces_primary_analysis": False,
        "null_hypothesis": TRAJECTORY_SENSITIVITY_NULL,
        "provenance": TRAJECTORY_SENSITIVITY_PROVENANCE,
        "permutation_unit": "complete cross-year ticker trajectory",
        "shared_mapping_across_years": True,
        "independent_per_year_mapping": False,
        "prediction_rows_fixed": True,
        "duplicate_free_one_to_one_mapping": True,
        "is_bootstrap": False,
        "requested_draws": result["requested_draws"],
        "valid_draws": result["valid_draws"],
        "invalid_draws": result["invalid_draws"],
        "seed": int(TRAJECTORY_SENSITIVITY_SEED),
        "seed_frozen_and_documented": True,
        "statistic": "equal-year mean of the valid within-year Spearman ICs",
        "two_sided": True,
        "p_value_formula": result["p_value_formula"],
        "p_value_denominator": result["p_value_denominator"],
        "extreme_count": result["extreme_count"],
        "multiplicity_method": "Bonferroni",
        "family_size": len(FROZEN_ML_FAMILY),
    }


def apply_trajectory_sensitivity(report: dict, predictions: pd.DataFrame) -> dict:
    """Attach the post-review sensitivity beside the unchanged primary analysis.

    The primary permutation values are never overwritten: the sensitivity lands
    in its own ``trajectory_preserving_sensitivity`` block, carries its own
    Bonferroni adjustment across the same frozen six-model family, and is labelled
    post-review throughout.
    """
    by_model = trajectory_sensitivity_by_model(predictions)
    family = set(FROZEN_ML_FAMILY)
    family_size = len(FROZEN_ML_FAMILY)

    for result in report["models"]:
        name = result["model"]
        sensitivity = by_model[name]
        pooled = result["pooled"]
        # Spearman IC is order-invariant, so the reindexed trajectory panel must
        # reproduce the pooled IC the primary analysis reported.
        if abs(sensitivity["observed_ic"] - pooled["observed_ic"]) > OBSERVED_IC_AGREEMENT_TOLERANCE:
            raise ExcessPermutationError(
                f"{name}: the trajectory panel pooled IC {sensitivity['observed_ic']!r} does not "
                f"match the primary pooled IC {pooled['observed_ic']!r}"
            )
        raw_p = sensitivity["permutation_p_value_two_sided"]
        block = {
            **trajectory_sensitivity_diagnostics(sensitivity),
            "observed_ic": sensitivity["observed_ic"],
            "permutation_p_value_two_sided": raw_p,
            "observed_null_percentile": sensitivity["observed_null_percentile"],
        }
        if name in family:
            adjusted = min(1.0, raw_p * family_size)
            block["bonferroni_adjusted_p_value"] = adjusted
            block["significant_fwer_0_05"] = bool(adjusted < 0.05)
        else:
            block["bonferroni_adjusted_p_value"] = None
            block["significant_fwer_0_05"] = None
            block["multiplicity_method"] = "none; baselines sit outside the corrected family"
        pooled["trajectory_preserving_sensitivity"] = block

    reference = by_model[FROZEN_ML_FAMILY[0]]
    report["analysis"]["primary_permutation"] = {
        "analysis_id": PRIMARY_PERMUTATION_ID,
        "status": PRIMARY_PERMUTATION_STATUS,
        "prespecified": True,
        "unchanged_by_human_review": True,
        "null_hypothesis": PRIMARY_PERMUTATION_NULL,
        "permutation_unit": "within-year row permutation of realized returns",
        "independent_per_year_permutation": True,
        "draws": int(report["analysis"]["permutations"]),
        "seed": int(report["analysis"]["seed"]),
        "two_sided": True,
        "tail": "absolute; |null| >= |observed|",
        "monte_carlo_correction": "(extreme_count + 1) / (draw_count + 1)",
        "statistic": "equal-weighted mean of within-year Spearman ICs",
        "multiplicity_method": "Bonferroni",
        "family_size": len(FROZEN_ML_FAMILY),
        "family_wise_alpha": 0.05,
        "renamed_or_replaced_by_the_sensitivity": False,
    }
    report["analysis"]["trajectory_preserving_sensitivity"] = {
        **trajectory_sensitivity_diagnostics(reference),
        "algorithm": [
            "Use the balanced 40-ticker x 3-year panel of persisted prediction rows.",
            "Sort and validate the unique ticker universe.",
            "Generate one permutation of ticker identities per draw.",
            "Apply that same ticker permutation mapping in 2023, 2024, and 2025.",
            "Keep the prediction rows fixed.",
            "Move each realized-outcome ticker trajectory as a complete block across all years.",
            "Recompute the Spearman IC independently within each year.",
            "Take the equal-year mean of the valid yearly ICs.",
            "Repeat for 10,000 draws from the frozen documented seed.",
            "Compute the two-sided Monte Carlo p-value (extreme_count + 1) / (draw_count + 1).",
            "Apply the same frozen six-model Bonferroni correction min(1, raw_p * 6).",
        ],
        "refused_inputs": [
            "ragged ticker coverage",
            "missing years",
            "duplicate ticker/year rows",
            "malformed ticker or year values",
            "unequal ticker sets across years",
            "non-finite targets or predictions",
            "insufficient tickers",
            "insufficient valid permutation draws",
            "independently generated per-year permutation mappings",
            "mappings that are not duplicate-free one-to-one permutations",
        ],
        "refusal_exceptions": [
            ExcessPermutationError.__name__,
            ExcessPanelError.__name__,
        ],
        "trajectory_years": reference["years"],
        "ticker_universe_size": len(reference["tickers"]),
    }
    return report


def build_significance_comparison(report: dict) -> dict:
    """Report both analyses symmetrically for every frozen family member.

    Every member carries the same seven fields; nothing is ranked, and no member
    is named as strongest, headline, or minimum-p.  The baselines are kept in a
    separate structure outside the corrected family.
    """
    by_name = {result["model"]: result for result in report["models"]}
    family_rows = []
    for model in FROZEN_ML_FAMILY:
        pooled = by_name[model]["pooled"]
        sensitivity = pooled["trajectory_preserving_sensitivity"]
        primary_rejects = bool(pooled["significant_fwer_0_05"])
        sensitivity_rejects = bool(sensitivity["significant_fwer_0_05"])
        family_rows.append(
            {
                "model": model,
                "pooled_equal_year_ic": pooled["observed_ic"],
                "primary_raw_permutation_p": pooled["permutation_p_value_two_sided"],
                "primary_bonferroni_p": pooled["bonferroni_adjusted_p_value"],
                "primary_rejects_fwer_0_05": primary_rejects,
                "sensitivity_raw_permutation_p": sensitivity["permutation_p_value_two_sided"],
                "sensitivity_bonferroni_p": sensitivity["bonferroni_adjusted_p_value"],
                "sensitivity_rejects_fwer_0_05": sensitivity_rejects,
                "ticker_cluster_bootstrap_ci_95": pooled["bootstrap_ci_95"],
                "either_family_corrected_analysis_rejects_fwer_0_05": (
                    primary_rejects or sensitivity_rejects
                ),
            }
        )

    baseline_rows = []
    for model in FROZEN_BASELINES:
        pooled = by_name[model]["pooled"]
        sensitivity = pooled["trajectory_preserving_sensitivity"]
        baseline_rows.append(
            {
                "model": model,
                "pooled_equal_year_ic": pooled["observed_ic"],
                "primary_raw_permutation_p": pooled["permutation_p_value_two_sided"],
                "sensitivity_raw_permutation_p": sensitivity["permutation_p_value_two_sided"],
                "ticker_cluster_bootstrap_ci_95": pooled["bootstrap_ci_95"],
                "inside_corrected_family": False,
                "bonferroni_adjusted": False,
            }
        )

    primary_rejecting = sorted(
        row["model"] for row in family_rows if row["primary_rejects_fwer_0_05"]
    )
    sensitivity_rejecting = sorted(
        row["model"] for row in family_rows if row["sensitivity_rejects_fwer_0_05"]
    )
    either_rejecting = sorted(
        row["model"]
        for row in family_rows
        if row["either_family_corrected_analysis_rejects_fwer_0_05"]
    )
    any_rejects = bool(either_rejecting)
    conclusion = (
        "At least one family member is distinguishable from at least one of the two nulls "
        "after the six-model Bonferroni correction; this alone would not establish a "
        "reliable predictive edge, and the sensitivity is not a prespecified confirmatory "
        "test."
        if any_rejects
        else "Neither the prespecified primary permutation nor the post-review "
        "trajectory-preserving sensitivity rejects for any of the six family members after "
        "the six-model Bonferroni correction at a family-wise alpha of 0.05."
    )
    return {
        "scope": "prespecified six-model ML family, reported symmetrically",
        "fields_reported_for_every_member": [
            "pooled_equal_year_ic",
            "primary_raw_permutation_p",
            "primary_bonferroni_p",
            "sensitivity_raw_permutation_p",
            "sensitivity_bonferroni_p",
            "ticker_cluster_bootstrap_ci_95",
            "either_family_corrected_analysis_rejects_fwer_0_05",
        ],
        "primary_analysis_id": PRIMARY_PERMUTATION_ID,
        "sensitivity_analysis_id": TRAJECTORY_SENSITIVITY_ID,
        "sensitivity_status": TRAJECTORY_SENSITIVITY_STATUS,
        "sensitivity_is_prespecified": False,
        "sensitivity_replaces_primary": False,
        "sensitivity_provenance": TRAJECTORY_SENSITIVITY_PROVENANCE,
        "family": family_rows,
        "baselines_outside_the_corrected_family": {
            "note": (
                "The three baselines sit outside the six-model correction family. Their "
                "p-values are unadjusted context and are never folded into the family gate."
            ),
            "rows": baseline_rows,
        },
        "models_rejecting_under_primary_after_correction": primary_rejecting,
        "models_rejecting_under_sensitivity_after_correction": sensitivity_rejecting,
        "models_rejecting_under_either_after_correction": either_rejecting,
        "any_model_rejects_under_either_after_correction": any_rejects,
        "conclusion": conclusion,
        "ordering": "frozen prespecified order; never reordered by an observed statistic",
        "selection_performed": False,
    }


# ---------------------------------------------------------------------------
# Symmetric family reporting
# ---------------------------------------------------------------------------


def order_models_frozen(report: dict) -> dict:
    """Order reported models by frozen prespecified order, never by outcome."""
    by_name = {result["model"]: result for result in report["models"]}
    expected = [*FROZEN_ML_FAMILY, *FROZEN_BASELINES]
    missing = [name for name in expected if name not in by_name]
    unexpected = sorted(set(by_name) - set(expected))
    if missing or unexpected:
        raise ValueError(
            f"reported models do not match the frozen family; missing={missing}, unexpected={unexpected}"
        )
    report["models"] = [by_name[name] for name in expected]
    return report


def build_family_conclusion(report: dict) -> dict:
    """Summarize the closed-family gate without naming a privileged model.

    Both family-corrected analyses are counted from their computed adjusted
    p-values; non-rejection is never assumed.  When the post-review sensitivity
    is attached, its survivors are counted separately and the sentence names both
    analyses rather than collapsing them into one.
    """
    family = [
        result for result in report["models"] if result["model"] in set(FROZEN_ML_FAMILY)
    ]
    surviving = sorted(
        result["model"]
        for result in family
        if result["pooled"]["significant_fwer_0_05"]
    )
    any_survives = bool(surviving)
    sensitivity_surviving = sorted(
        result["model"]
        for result in family
        if result["pooled"].get("trajectory_preserving_sensitivity", {}).get(
            "significant_fwer_0_05"
        )
    )
    has_sensitivity = all(
        "trajectory_preserving_sensitivity" in result["pooled"] for result in family
    )
    either_surviving = sorted(set(surviving) | set(sensitivity_surviving))

    if not has_sensitivity:
        conclusion = (
            "At least one model in the prespecified six-model ML family is distinguishable "
            "from the within-year null after Bonferroni correction; this alone would not "
            "establish a reliable predictive edge."
            if any_survives
            else "No model in the prespecified six-model ML family is distinguishable from "
            "the within-year null after Bonferroni correction across the family. The excess "
            "return basis establishes no reliable predictive edge."
        )
    elif either_surviving:
        conclusion = (
            "At least one model in the prespecified six-model ML family is distinguishable "
            "from a null after Bonferroni correction under the prespecified primary "
            "permutation, the post-review trajectory-preserving sensitivity, or both. That "
            "alone would not establish a reliable predictive edge, and the sensitivity is a "
            "post-review robustness check rather than a prespecified confirmatory test."
        )
    else:
        conclusion = (
            "No model in the prespecified six-model ML family is distinguishable from the "
            "within-year null after Bonferroni correction across the family, and none is "
            "distinguishable under the post-review trajectory-preserving sensitivity after "
            "the same six-model correction. The excess return basis establishes no reliable "
            "predictive edge."
        )

    payload = {
        "scope": "prespecified six-model ML family",
        "multiplicity_method": "Bonferroni",
        "family_size": len(FROZEN_ML_FAMILY),
        "family_wise_alpha": 0.05,
        "models_surviving_family_wise_correction": surviving,
        "count_surviving_family_wise_correction": len(surviving),
        "any_model_survives_family_wise_correction": any_survives,
        "conclusion": conclusion,
        "bootstrap_interpretation": BOOTSTRAP_INTERPRETATION,
        "reliable_predictive_edge_established": False,
    }
    if has_sensitivity:
        payload.update(
            {
                "primary_analysis_id": PRIMARY_PERMUTATION_ID,
                "sensitivity_analysis_id": TRAJECTORY_SENSITIVITY_ID,
                "sensitivity_status": TRAJECTORY_SENSITIVITY_STATUS,
                "sensitivity_is_prespecified": False,
                "models_surviving_sensitivity_family_wise_correction": sensitivity_surviving,
                "count_surviving_sensitivity_family_wise_correction": len(
                    sensitivity_surviving
                ),
                "any_model_survives_sensitivity_family_wise_correction": bool(
                    sensitivity_surviving
                ),
                "models_surviving_either_family_wise_correction": either_surviving,
                "any_model_survives_either_family_wise_correction": bool(either_surviving),
                "conclusion_derivation": (
                    "computed from the adjusted p-values of both family-corrected analyses; "
                    "non-rejection is never assumed"
                ),
            }
        )
    return payload


def build_reporting_policy() -> dict:
    return {
        "statement": REPORTING_POLICY_STATEMENT,
        "model_presentation": "symmetric across the prespecified ML family",
        "ordering": "frozen prespecified order; never reordered by an outcome statistic",
        "frozen_ml_family_order": list(FROZEN_ML_FAMILY),
        "frozen_baseline_order": list(FROZEN_BASELINES),
        "result_driven_selection_performed": False,
        "outcome_statistics_excluded_from_selection": [
            "observed_ic",
            "permutation_p_value_two_sided",
            "bonferroni_adjusted_p_value",
            "bootstrap_ci_95",
            "observed_null_percentile",
        ],
        "headline_scope": "family-level only; no individual model is singled out",
        "report_construction": {
            "builder": f"{GENERATOR}::build_family_report",
            "significance_build_report_invoked": False,
            "outcome_dependent_selection_helpers_invoked": [],
            "note": (
                "The report is assembled from per-model, non-selecting analyses. No "
                "helper that chooses a minimum raw p-value, minimum adjusted p-value, "
                "strongest IC, narrowest interval, or any other outcome-derived winner "
                "is executed at any intermediate or final layer, so no selected field "
                "ever exists to be deleted afterwards."
            ),
        },
    }


def build_cross_basis_multiplicity() -> dict:
    """Record the owner-authorized confirmatory/exploratory basis boundary."""
    return {
        "confirmatory_family": {
            "basis_id": CONFIRMATORY_BASIS_ID,
            "target_column": CONFIRMATORY_BASIS_TARGET,
            "role": "sole confirmatory family",
            "note": (
                "Nominal return is the only confirmatory target basis in this repository. "
                "Its artifacts and conclusion are unchanged by this task."
            ),
        },
        "exploratory_bases": [
            {**basis, "role": "exploratory robustness evaluation"}
            for basis in EXPLORATORY_BASES
        ],
        "this_basis_id": BASIS_ID,
        "this_basis_role": "exploratory robustness evaluation",
        "within_basis_correction": {
            "method": "Bonferroni",
            "family": list(FROZEN_ML_FAMILY),
            "family_size": len(FROZEN_ML_FAMILY),
            "scope": "the six-model ML family within this single target basis",
        },
        "controls_multiplicity_across_target_bases": False,
        "cross_basis_correction_prespecified": False,
        "statement": (
            "Nominal return is the sole confirmatory family. The real-TRY, USD, and "
            "excess-return analyses are exploratory robustness evaluations. Within-basis "
            "Bonferroni corrections do not control multiplicity across the several target "
            "bases, so the number of bases examined inflates the chance that some basis "
            "eventually produces a small p-value."
        ),
        "future_result_policy": (
            "A future significant alternative-basis result must not be described as "
            "confirmatory without a separately prespecified cross-basis correction."
        ),
        "nominal_artifacts_altered": False,
    }


def build_coincident_baseline_evidence(predictions: pd.DataFrame) -> dict:
    """Determine, from the persisted rows, how far two baselines actually coincide.

    Three nested levels are tested in order — identical prediction values,
    identical prediction ranks, identical IC — and only the strongest level the
    evidence supports is reported.  Nothing is asserted that the dumps do not
    show.
    """
    left_name, right_name = COINCIDENT_BASELINE_CANDIDATES
    frames = {}
    for name in (left_name, right_name):
        rows = predictions[predictions["model"].eq(name)]
        if rows.empty:
            raise ValueError(f"persisted dumps contain no rows for {name}")
        frames[name] = rows.sort_values(["year", "ticker"]).reset_index(drop=True)
    left, right = frames[left_name], frames[right_name]

    aligned = left["ticker"].equals(right["ticker"]) and left["year"].equals(right["year"])
    if not aligned:
        raise ValueError(
            f"{left_name} and {right_name} do not cover the same ticker/year rows; the "
            "coincidence check requires an aligned panel"
        )

    identical_values = bool(
        np.array_equal(
            left["y_pred"].to_numpy(dtype=float), right["y_pred"].to_numpy(dtype=float)
        )
    )
    per_year = []
    ranks_identical = True
    ic_identical = True
    for year in sorted({int(value) for value in left["year"].tolist()}):
        left_year = left[left["year"].eq(year)]
        right_year = right[right["year"].eq(year)]
        left_pred = left_year["y_pred"].to_numpy(dtype=float)
        right_pred = right_year["y_pred"].to_numpy(dtype=float)
        year_values = bool(np.array_equal(left_pred, right_pred))
        year_ranks = bool(
            np.array_equal(
                pd.Series(left_pred).rank(method="average").to_numpy(),
                pd.Series(right_pred).rank(method="average").to_numpy(),
            )
        )
        left_ic = significance.spearman_ic(
            left_year["y_true"].to_numpy(dtype=float), left_pred
        )
        right_ic = significance.spearman_ic(
            right_year["y_true"].to_numpy(dtype=float), right_pred
        )
        year_ic = bool(left_ic == right_ic)
        ranks_identical = ranks_identical and year_ranks
        ic_identical = ic_identical and year_ic
        per_year.append(
            {
                "evaluation_year": year,
                "rows": int(len(left_year)),
                "identical_prediction_values": year_values,
                "max_absolute_prediction_difference": float(
                    np.max(np.abs(left_pred - right_pred))
                ),
                "identical_prediction_ranks": year_ranks,
                "identical_within_year_ic": year_ic,
            }
        )

    if identical_values:
        level = "identical_prediction_values"
        strongest = (
            f"`{left_name}` and `{right_name}` produce bitwise-identical prediction values "
            "on every evaluated ticker and year in the persisted dumps, which necessarily "
            "makes their ranks and their ICs identical as well."
        )
    elif ranks_identical:
        level = "identical_prediction_ranks_only"
        strongest = (
            f"`{left_name}` and `{right_name}` produce identical prediction ranks within "
            "every evaluated year, though their prediction values differ."
        )
    elif ic_identical:
        level = "identical_ic_values_only"
        strongest = (
            f"`{left_name}` and `{right_name}` produce identical IC values, though their "
            "prediction values and ranks differ."
        )
    else:
        level = "not_coincident"
        strongest = (
            f"`{left_name}` and `{right_name}` are not coincident in the persisted dumps."
        )

    return {
        "compared_models": list(COINCIDENT_BASELINE_CANDIDATES),
        "evidence_source": "persisted R3-TGT-01 prediction dumps",
        "equality_level": level,
        "identical_prediction_values": identical_values,
        "identical_prediction_ranks": ranks_identical,
        "identical_ic_values": ic_identical,
        "max_absolute_prediction_difference": float(
            np.max(
                np.abs(
                    left["y_pred"].to_numpy(dtype=float)
                    - right["y_pred"].to_numpy(dtype=float)
                )
            )
        ),
        "per_year": per_year,
        "strongest_supported_statement": strongest,
        "wording_policy": (
            "Only the strongest level the persisted evidence actually supports is stated; "
            "weaker or stronger characterisations are not used."
        ),
        "specifications_retained": True,
        "retention_policy": COINCIDENT_BASELINE_POLICY,
        "removal_permitted_by_repository_authority": False,
        "independent_baseline_diversity": False,
        "interpretation": COINCIDENT_BASELINE_INTERPRETATION,
    }


def build_ic_sign_note(report: dict) -> dict:
    """State the family-level IC-sign caution alongside the counted evidence."""
    by_name = {result["model"]: result for result in report["models"]}
    signs = {
        model: float(by_name[model]["pooled"]["observed_ic"]) for model in FROZEN_ML_FAMILY
    }
    negative = sorted(model for model, value in signs.items() if value < 0)
    positive = sorted(model for model, value in signs.items() if value > 0)
    zero = sorted(model for model, value in signs.items() if value == 0)
    return {
        "scope": "prespecified six-model ML family",
        "family_size": len(FROZEN_ML_FAMILY),
        "negative_pooled_ic_count": len(negative),
        "positive_pooled_ic_count": len(positive),
        "zero_pooled_ic_count": len(zero),
        "models_with_negative_pooled_ic": negative,
        "models_with_positive_pooled_ic": positive,
        "predominantly_negative": len(negative) > len(FROZEN_ML_FAMILY) / 2,
        "note": NEGATIVE_IC_NOTE,
        "possible_explanations": [
            "sampling variation",
            "feature-orientation effects",
            "systematic construction effects",
        ],
        "interpreted_as_inverse_alpha": False,
        "interpreted_as_contrarian_strategy": False,
        "interpreted_as_actionable_signal": False,
        "interpreted_as_validated_predictive_evidence": False,
        "tree_models_selected_or_privileged": False,
        "selection_note": (
            "The note is family-level. No member is selected or privileged by the sign or "
            "magnitude of its IC, and the tree-based members are not singled out."
        ),
    }


def build_review_package_scope() -> dict:
    """State what the compact human-review package does and does not support."""
    return {
        "supports": (
            "review of the persisted prediction-to-significance layer: row-level prediction "
            "dumps, the dump-reconstructed leaderboard, the significance report, and the "
            "artifact manifest"
        ),
        "standalone_feature_construction_reproduction": False,
        "standalone_model_fitting_reproduction": False,
        "complete_independent_fitting_stage_replication_claimed": False,
        "repository_technical_review_covers": [
            "governed source paths",
            "protected hashes",
            "split tracing",
            "implementation behavior",
        ],
        "statements": list(REVIEW_PACKAGE_SCOPE_STATEMENTS),
    }


# ---------------------------------------------------------------------------
# Power analysis derived from the persisted dumps
# ---------------------------------------------------------------------------

# Hypothetical planning horizons.  ``0`` additional years is deliberately absent:
# 40 rows over three years *is* the current design, and restating it as a
# planning sensitivity is what made the reviewed report contradict itself.
PLANNING_ADDITIONAL_TEST_YEARS = (1, 2, 3, 5, 7)
CURRENT_DESIGN_STATUS = "observed"
HYPOTHETICAL_DESIGN_STATUS = "hypothetical"
POWER_DEDUPLICATION_KEY = ("rows_per_year", "test_years")

# The reviewed report inherited prose calling 80 rows the current dump design
# while its own tables reported 40. These patterns fail the build if that
# contradiction is reintroduced in JSON or Markdown.
_CURRENT_DESIGN_ROW_CONTRADICTIONS = (
    re.compile(
        r"current[- ]?(?:dump |prediction[- ]dump )?(?:design|evaluation)?[^.\n]{0,40}\b80[- ]row",
        re.I,
    ),
    re.compile(r"\b80[- ]rows?\b[^.\n]{0,40}\b(?:current|actual)\b[^.\n]{0,40}\bdesign\b", re.I),
    re.compile(r"\b80\s+rows?\s+per\s+(?:evaluation\s+|test\s+)?year\b", re.I),
    re.compile(r"\bcurrent\s+design\b[^.\n]{0,60}\b80\b", re.I),
    re.compile(r"\b80[- ]row\s+prediction[- ]dump\s+design\b", re.I),
)


def validate_no_current_design_row_contradiction(text: str) -> None:
    """Reject any statement that presents 80 rows as this evaluation's design."""
    for pattern in _CURRENT_DESIGN_ROW_CONTRADICTIONS:
        match = pattern.search(text)
        if match:
            raise ValueError(
                "report states a row count that contradicts the observed current "
                f"design: {match.group(0)!r}"
            )


def _year_phrase(years: list[int]) -> str:
    """Render evaluation years as prose, e.g. ``2023, 2024, and 2025``."""
    if len(years) == 1:
        return str(years[0])
    return ", ".join(str(year) for year in years[:-1]) + f", and {years[-1]}"


def observed_current_design(evaluated_rows_per_year: dict[int, int]) -> dict:
    """Describe the design that was actually evaluated, straight from the dumps."""
    years = sorted(int(year) for year in evaluated_rows_per_year)
    if tuple(years) != EXPECTED_EVALUATION_YEARS:
        raise ValueError(
            f"persisted dumps must cover evaluation years {list(EXPECTED_EVALUATION_YEARS)}; got {years}"
        )
    distinct = sorted({int(value) for value in evaluated_rows_per_year.values()})
    if len(distinct) != 1:
        raise ValueError(
            f"power analysis requires one common evaluated-row count per year; got {distinct}"
        )
    rows_per_year = distinct[0]
    return {
        "design_id": "current_design",
        "status": CURRENT_DESIGN_STATUS,
        "rows_per_year": rows_per_year,
        "years": years,
        "test_years": len(years),
        "total_evaluated_rows_per_model": rows_per_year * len(years),
        "derivation": (
            "computed from the persisted R3-TGT-01 prediction dumps, not from a "
            "planning assumption"
        ),
        "description": (
            f"The evaluated design is {rows_per_year} rows per evaluation year in "
            f"{_year_phrase(years)}."
        ),
    }


def build_power_analysis(
    evaluated_rows_per_year: dict[int, int],
    *,
    simulations: int = significance.DEFAULT_POWER_SIMULATIONS,
    seed: int = significance.DEFAULT_SEED,
) -> dict:
    """Build the power section around exactly one observed design.

    Two analytic views of that single design are reported -- one evaluation year
    on its own, and the three years pooled -- and both are marked as views of
    ``current_design`` rather than as separate designs.  Hypothetical planning
    horizons live in their own structure, are labelled hypothetical, and are
    deduplicated against the observed design on ``(rows_per_year, test_years)``
    so no planning row can be mistaken for current evidence.
    """
    current = observed_current_design(evaluated_rows_per_year)
    rows_per_year = current["rows_per_year"]
    test_years = current["test_years"]

    views = []
    view_specs = (
        (
            "single_evaluation_year",
            1,
            "one evaluation year of the current design, viewed on its own",
        ),
        (
            "pooled_evaluation_years",
            test_years,
            "all evaluation years of the current design, pooled with equal weights",
        ),
    )
    for view_index, (view_id, split_count, label) in enumerate(view_specs):
        detectable = significance.minimum_detectable_ic(
            n_per_split=rows_per_year,
            split_count=split_count,
        )
        simulated_at_mde = significance.simulate_fisher_power(
            detectable,
            n_per_split=rows_per_year,
            split_count=split_count,
            simulations=simulations,
            seed=seed + view_index * 100,
        )
        curve = []
        for point_index, multiplier in enumerate((0.0, 0.5, 1.0, 1.25)):
            true_ic = min(0.95, detectable * multiplier)
            curve.append(
                {
                    "assumed_true_ic": float(true_ic),
                    "analytic_power": significance.fisher_power(
                        true_ic,
                        n_per_split=rows_per_year,
                        split_count=split_count,
                    ),
                    "simulated_rejection_rate": significance.simulate_fisher_power(
                        true_ic,
                        n_per_split=rows_per_year,
                        split_count=split_count,
                        simulations=simulations,
                        seed=seed + view_index * 100 + point_index + 1,
                    ),
                }
            )
        difference = abs(simulated_at_mde - significance.POWER_TARGET)
        views.append(
            {
                "view_id": view_id,
                "view_of": "current_design",
                "label": label,
                "n_per_split": rows_per_year,
                "split_count": split_count,
                "total_evaluated_rows": rows_per_year * split_count,
                "analytic_minimum_detectable_abs_ic": detectable,
                "simulated_power_at_analytic_mde": simulated_at_mde,
                "absolute_power_difference": difference,
                "agreement_within_tolerance": difference
                <= significance.POWER_AGREEMENT_TOLERANCE,
                "simulation_curve": curve,
            }
        )
    current["views"] = views

    planning_rows = significance.PUBLIC_UNIVERSE_PLANNING_N
    entries = []
    excluded: list[dict] = []
    for additional in (0, *PLANNING_ADDITIONAL_TEST_YEARS):
        total_years = test_years + additional
        if (planning_rows, total_years) == (rows_per_year, test_years):
            excluded.append(
                {
                    "planning_rows_per_year": planning_rows,
                    "total_test_years": total_years,
                    "reason": (
                        "identical to the observed current design; a hypothetical entry "
                        "may never restate current evidence"
                    ),
                }
            )
            continue
        entries.append(
            {
                "status": HYPOTHETICAL_DESIGN_STATUS,
                "is_current_evidence": False,
                "additional_test_years": additional,
                "total_test_years": total_years,
                "planning_rows_per_year": planning_rows,
                "analytic_minimum_detectable_abs_ic": significance.minimum_detectable_ic(
                    n_per_split=planning_rows,
                    split_count=total_years,
                ),
            }
        )

    return {
        "method": (
            "two-sided Fisher z approximation for independent within-year Spearman ICs; "
            "equal year weights and variance 1/(n-3)"
        ),
        "alpha_two_sided": significance.POWER_ALPHA,
        "target_power": significance.POWER_TARGET,
        "multiplicity_scope": (
            "single prespecified IC test at alpha=0.05; this power calculation does not "
            "represent Bonferroni-adjusted family-wise power across six ML models"
        ),
        "simulation": {
            "method": (
                "seeded Gaussian-copula draws calibrated to assumed Spearman IC, converted "
                "to ranks, and rejected with the same Fisher-z approximation"
            ),
            "simulations_per_curve_point": simulations,
            "seed": seed,
            "agreement_tolerance_absolute_power": significance.POWER_AGREEMENT_TOLERANCE,
        },
        "definitions": {
            "observed_ic": "sample estimate computed from persisted prediction dumps",
            "detectable_ic": (
                "assumed true absolute IC yielding 80% long-run rejection probability under "
                "the stated approximation; not a hard significance cutoff"
            ),
            "statistical_power": (
                "long-run probability of rejecting a zero-IC null when the stated true IC "
                "and design assumptions hold"
            ),
            "practical_relevance": (
                "not evaluated by this calculation; detectability does not establish economic "
                "value, robustness, implementability, or investment relevance"
            ),
        },
        "current_design": current,
        "hypothetical_planning_sensitivities": {
            "status": HYPOTHETICAL_DESIGN_STATUS,
            "is_current_evidence": False,
            "label": (
                "hypothetical planning horizons for the public-universe scale; never a "
                "description of the evidence that exists today"
            ),
            "framing": (
                "The pipeline is ready for more data; this is pipeline capability, not a "
                "promise that more data will produce predictive skill or practical returns."
            ),
            "planning_rows_per_year": planning_rows,
            "deduplicated_against_current_design": True,
            "deduplication_key": list(POWER_DEDUPLICATION_KEY),
            "excluded_duplicates_of_current_design": excluded,
            "entries": entries,
        },
        "non_rejection_interpretation": (
            "The detectable |IC| at the current design is large relative to any plausible "
            "annual equity-ranking IC, so the family-wide failure to reject is a low-power "
            "non-rejection. It does not establish that the true IC is zero, and it is not "
            "evidence of predictive validity in either direction."
        ),
        "limitations": [
            "Only three test years are observed; treating within-year IC estimates as independent is an approximation.",
            "The calculation assumes equal per-year sample sizes and a stable true IC across years, neither of which establishes regime generality.",
            f"The evaluated design is {rows_per_year} rows per evaluation year across "
            f"{_year_phrase(current['years'])}; the additional-test-year table is a "
            "hypothetical planning horizon and is not current evidence.",
            "The cohort is retrospective rather than verified point-in-time membership, and reproducibility remains numerical-environment-qualified.",
            "Power bounds detection under assumptions; it neither estimates the true IC nor establishes practical investment relevance.",
            "A low-power non-rejection is not a demonstration that the true IC is zero, and no power figure here is a statement of predictive validity.",
        ],
    }


def validate_power_design_consistency(
    report: dict, markdown: str, evaluated_rows_per_year: dict[int, int]
) -> None:
    """Fail the build if the power section drifts from the persisted dumps."""
    power = report["power_analysis"]
    current = power["current_design"]
    observed_rows = sorted({int(value) for value in evaluated_rows_per_year.values()})
    observed_years = sorted(int(year) for year in evaluated_rows_per_year)
    if observed_rows != [current["rows_per_year"]]:
        raise ValueError(
            f"current design rows_per_year {current['rows_per_year']} does not match the "
            f"persisted dumps {observed_rows}"
        )
    if current["years"] != observed_years:
        raise ValueError("current design years do not match the persisted dumps")
    if current["status"] != CURRENT_DESIGN_STATUS:
        raise ValueError("the current design must be marked as observed")

    observed_designs = _observed_design_count(power)
    if observed_designs != 1:
        raise ValueError(
            f"exactly one observed power design is allowed; found {observed_designs}"
        )

    hypothetical = power["hypothetical_planning_sensitivities"]
    current_key = (current["rows_per_year"], current["test_years"])
    for entry in hypothetical["entries"]:
        if entry["status"] != HYPOTHETICAL_DESIGN_STATUS or entry["is_current_evidence"]:
            raise ValueError("planning entries must be labelled hypothetical")
        if (entry["planning_rows_per_year"], entry["total_test_years"]) == current_key:
            raise ValueError(
                "a hypothetical planning entry duplicates the observed current design"
            )

    for text in (json.dumps(report, indent=2, sort_keys=True, allow_nan=False), markdown):
        validate_no_current_design_row_contradiction(text)

    expected_sentence = (
        f"The current evaluated design is {current['rows_per_year']} rows per "
        f"evaluation year across {_year_phrase(current['years'])}"
    )
    if expected_sentence not in markdown:
        raise ValueError("Markdown does not state the observed current design")
    for view in current["views"]:
        row = (
            f"| {view['view_id']} | {view['n_per_split']} | {view['split_count']} | "
            f"{view['total_evaluated_rows']} |"
        )
        if row not in markdown:
            raise ValueError(f"Markdown omits the current-design view {view['view_id']}")
    for entry in hypothetical["entries"]:
        row = (
            f"| {entry['additional_test_years']} | {entry['total_test_years']} | "
            f"{entry['planning_rows_per_year']} |"
        )
        if row not in markdown:
            raise ValueError("Markdown omits a hypothetical planning entry")


def _observed_design_count(payload: object) -> int:
    """Count objects in the power section that declare themselves observed."""
    total = 0
    if isinstance(payload, dict):
        if payload.get("status") == CURRENT_DESIGN_STATUS:
            total += 1
        for value in payload.values():
            total += _observed_design_count(value)
    elif isinstance(payload, list):
        for value in payload:
            total += _observed_design_count(value)
    return total


# ---------------------------------------------------------------------------
# Non-selecting family report construction
# ---------------------------------------------------------------------------


def build_family_report(
    predictions: pd.DataFrame,
    sources: list[dict],
    evaluated_rows_per_year: dict[int, int],
    *,
    permutations: int = significance.DEFAULT_PERMUTATIONS,
    bootstraps: int = significance.DEFAULT_BOOTSTRAPS,
    seed: int = significance.DEFAULT_SEED,
    power_simulations: int = significance.DEFAULT_POWER_SIMULATIONS,
) -> dict:
    """Assemble the R3-TGT-01 report without ever selecting a model.

    ``significance.build_report`` is not used: it chooses the family member with
    the smallest raw permutation p-value and embeds it as a headline. Removing
    that field after the fact would still have executed the selection, so the
    report is built here from ``significance.analyze_model``, which analyses one
    model at a time and compares nothing.

    Each member is analysed independently from the same frozen seed, so the
    numbers do not depend on the iteration order, and the members are emitted in
    the frozen prespecified order rather than in any outcome order.
    """
    observed = sorted(predictions["model"].unique().tolist())
    expected = [*FROZEN_ML_FAMILY, *FROZEN_BASELINES]
    if observed != sorted(expected):
        raise ValueError(
            f"prediction dumps do not contain the frozen nine-model family: {observed}"
        )

    family = set(FROZEN_ML_FAMILY)
    results = []
    for model in expected:
        result = significance.analyze_model(
            predictions[predictions["model"] == model],
            permutations=permutations,
            bootstraps=bootstraps,
            seed=seed,
        )
        result.update(
            {"model": model, "kind": "ml" if model in family else "baseline"}
        )
        results.append(result)

    family_size = len(FROZEN_ML_FAMILY)
    for result in results:
        pooled = result["pooled"]
        if result["kind"] == "ml":
            adjusted = min(1.0, pooled["permutation_p_value_two_sided"] * family_size)
            pooled["bonferroni_adjusted_p_value"] = adjusted
            pooled["significant_fwer_0_05"] = bool(adjusted < 0.05)
        else:
            pooled["bonferroni_adjusted_p_value"] = None
            pooled["significant_fwer_0_05"] = None

    evaluated_per_split = sorted(
        int(value)
        for value in predictions.groupby(["split", "model"], sort=True).size().unique()
    )
    evaluated_label = ", ".join(str(value) for value in evaluated_per_split)
    report = {
        "schema_version": 2,
        "analysis": {
            "statistic": "equal-weighted mean of within-split Spearman ICs",
            "permutation": "two-sided; realized returns shuffled independently within each test year",
            "bootstrap": "tickers resampled with replacement independently within each test year",
            "permutations": permutations,
            "bootstraps": bootstraps,
            "seed": seed,
            "evaluated_tickers_per_model_split": evaluated_per_split,
            "multiplicity": {
                "method": "Bonferroni",
                "family": list(FROZEN_ML_FAMILY),
                "family_size": family_size,
                "family_wise_alpha": 0.05,
            },
        },
        "source_artifacts": sources,
        "power_analysis": build_power_analysis(
            evaluated_rows_per_year,
            simulations=power_simulations,
            seed=seed,
        ),
        "models": results,
        "limitations": [
            f"Only three test years with {evaluated_label} evaluated tickers per model and split; estimates remain noisy.",
            "The cohort is a retrospectively fixed repository universe, not verified point-in-time BIST100 membership.",
            "Prediction artifact byte reproducibility is environment-qualified; manifests separate same-environment byte identity from cross-environment semantic checks.",
            BASIS_LIMITATION,
            "Research support only; not investment advice.",
        ],
    }
    assert_no_selection_keys(report)
    return report


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


def effective_estimator_parameters() -> dict:
    """Read effective parameters from the estimators the frozen path constructs.

    The ML entries in ``run_experiments.MODELS`` build their estimator inline,
    so the instance is captured by temporarily standing in for ``_fit_sklearn``.
    Nothing is fitted and no default is transcribed by hand: every value comes
    from ``estimator.get_params(deep=False)`` on the real object.
    """
    captured: dict[str, object] = {}
    original = exp._fit_sklearn

    def _capture(model, x_train, y_train, x_test):
        captured["estimator"] = model
        return np.zeros(len(x_test), dtype=float)

    probe_x = np.zeros((4, 3), dtype=float)
    probe_y = np.zeros(4, dtype=float)
    parameters: dict[str, dict] = {}
    exp._fit_sklearn = _capture
    try:
        for name in FROZEN_ML_FAMILY:
            captured.clear()
            _kind, fit = exp.MODELS[name]
            fit(probe_x, probe_y, probe_x)
            estimator = captured.get("estimator")
            if estimator is None:
                raise ValueError(f"could not capture the estimator used by {name}")
            parameters[name] = {
                "estimator_class": type(estimator).__name__,
                "estimator_module": type(estimator).__module__,
                "extraction": "estimator.get_params(deep=False)",
                "parameters": _json_safe(estimator.get_params(deep=False)),
            }
    finally:
        exp._fit_sklearn = original

    for name in FROZEN_BASELINES:
        _kind, fit = exp.MODELS[name]
        parameters[name] = {
            "estimator_class": None,
            "estimator_module": getattr(fit, "__module__", None),
            "extraction": "deterministic scoring function; no fitted estimator",
            "parameters": {},
            "callable": getattr(fit, "__name__", repr(fit)),
        }
    return parameters


def _package_version(package: str) -> str | None:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def environment_provenance() -> dict:
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_version_info": list(sys.version_info[:3]),
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "packages": {
            "numpy": _package_version("numpy"),
            "pandas": _package_version("pandas"),
            "scipy": _package_version("scipy"),
            "scikit-learn": _package_version("scikit-learn"),
        },
        "determinism": (
            "Regeneration is deterministic within this recorded numerical "
            "environment: repeated runs of the recorded command on the same "
            "interpreter, package versions, and platform reproduce identical output "
            "bytes. Byte identity across different environments is not claimed."
        ),
    }


def _feature_column_provenance(feature_cols: list[str]) -> dict:
    joined = "\n".join(feature_cols)
    return {
        "count": len(feature_cols),
        "columns": list(feature_cols),
        "sha256": hashlib.sha256(joined.encode("utf-8")).hexdigest(),
        "checksum_definition": "sha256 of the newline-joined feature column names in fitting order",
    }


def _schema_versions() -> dict:
    return {
        "prediction_csv": {
            "version": PREDICTION_CSV_SCHEMA_VERSION,
            "columns": list(significance.REQUIRED_COLUMNS),
            "float_format": "%.17g",
            "line_terminator": "\\n",
        },
        "leaderboard_csv": {
            "version": LEADERBOARD_CSV_SCHEMA_VERSION,
            "key_columns": ["target", "split", "model", "kind"],
            "line_terminator": "\\n",
        },
        "significance_report_json": {"version": 2},
        "artifact_manifest_json": {"version": "2.0.0"},
    }


def _frozen_provenance(feature_cols: list[str] | None = None) -> dict:
    model_seeds = {
        name: config["seed"]
        for name, config in exp.MODEL_CONFIGS.items()
        if config["seed"] is not None
    }
    provenance = {
        "target": TARGET_COLUMN,
        "generator": GENERATOR,
        "regeneration_command": REGENERATION_COMMAND,
        "seeds": {
            "model_seeds": model_seeds,
            "significance_seed": significance.DEFAULT_SEED,
            "bootstrap_seed": significance.DEFAULT_SEED,
            "permutation_seed": significance.DEFAULT_SEED,
        },
        "preprocessing": (
            "Existing build_panel_for_target rules: year-local feature percentile "
            "ranks, existing feature registry exclusions, null target rows dropped, "
            "and ML-only missing-feature rank-center handling unchanged."
        ),
        "walk_forward_splits": exp.SPLITS,
        "model_specifications": exp.MODEL_CONFIGS,
        "model_family_membership": {
            "ml_family": list(FROZEN_ML_FAMILY),
            "baselines_outside_family": list(FROZEN_BASELINES),
        },
        "effective_estimator_parameters": effective_estimator_parameters(),
        "resampling": {
            "permutations": significance.DEFAULT_PERMUTATIONS,
            "bootstraps": significance.DEFAULT_BOOTSTRAPS,
            "bootstrap_unit": BOOTSTRAP_UNIT,
            "bootstrap_cluster_key": BOOTSTRAP_CLUSTER_KEY,
            "permutation_unit": "within-year row permutation of realized returns",
        },
        "schema_versions": _schema_versions(),
        "environment": environment_provenance(),
        "output_path_policy": build_output_path_policy(),
        "selection_policy": (
            "Frozen nine-model family; no search, additions, removals, tuning, or "
            "selection based on excess-target results. " + REPORTING_POLICY_STATEMENT
        ),
    }
    if feature_cols is not None:
        provenance["feature_columns"] = _feature_column_provenance(feature_cols)
    return provenance


def _read_only_sources() -> list[dict]:
    return [
        _source_record(
            exp._modeling_csv(),
            "trusted modeling features and excess-return target",
        ),
        _source_record(
            CANONICAL_TARGET_LEADERBOARD,
            "read-only aggregate excess leaderboard used only for comparison",
        ),
        _source_record(ROOT / GENERATOR, "R3-TGT-01 generator"),
        _source_record(
            ROOT / "experiments" / "run_experiments.py",
            "frozen preprocessing, splits, models, and metrics",
        ),
        _source_record(
            ROOT / "experiments" / "run_alternative_targets.py",
            "existing isolated prediction-dump fitting path",
        ),
        _source_record(
            ROOT / "experiments" / "significance.py",
            "seeded IC, permutation, and Bonferroni conventions",
        ),
    ]
    # The whole Makefile is deliberately NOT a source_artifact: it is an
    # invocation wrapper, not a statistical input, so unrelated targets added by
    # other tasks would otherwise stale these artifacts. The research-excess
    # regeneration recipe is recorded truthfully and task-specifically by
    # build_makefile_target_provenance() instead.


def _write_prediction_dumps(
    panel: pd.DataFrame, feature_cols: list[str], output_dir: Path
) -> list[Path]:
    paths: list[Path] = []
    for split in exp.SPLITS:
        predictions, _discarded_ephemeral_metrics = _prediction_rows(
            panel, feature_cols, split
        )
        path = output_dir / f"predictions_{split['name']}.csv"
        pd.DataFrame(predictions, columns=significance.REQUIRED_COLUMNS).to_csv(
            path,
            index=False,
            float_format="%.17g",
            lineterminator="\n",
        )
        paths.append(path)
    return paths


def _evaluated_rows_per_year(predictions: pd.DataFrame) -> dict[int, int]:
    """Return per-model n for each target year, requiring uniform model coverage."""
    per_year: dict[int, int] = {}
    for year, group in predictions.groupby("year", sort=True):
        counts = sorted(group.groupby("model").size().unique().tolist())
        if len(counts) != 1:
            raise ValueError(
                f"evaluated rows differ across models for year {year}: {counts}"
            )
        per_year[int(year)] = int(counts[0])
    return per_year


def reconstruct_leaderboard(predictions: pd.DataFrame) -> pd.DataFrame:
    """Rebuild aggregate excess metrics exclusively from persisted dump rows."""
    rows: list[dict] = []
    expected_models = list(exp.MODELS)
    observed_models = sorted(predictions["model"].unique().tolist())
    if observed_models != sorted(expected_models):
        raise ValueError(
            f"prediction dumps do not contain the frozen nine-model family: {observed_models}"
        )

    for split in exp.SPLITS:
        split_name = split["name"]
        for model, (kind, _score) in exp.MODELS.items():
            group = predictions[
                predictions["split"].eq(split_name) & predictions["model"].eq(model)
            ]
            if group.empty:
                raise ValueError(f"missing persisted rows for {split_name}/{model}")
            metrics = exp._metrics(
                group["y_true"].to_numpy(dtype=float),
                group["y_pred"].to_numpy(dtype=float),
            )
            if not metrics:
                raise ValueError(f"insufficient persisted rows for {split_name}/{model}")
            rows.append(
                {
                    "target": TARGET_COLUMN,
                    "split": split_name,
                    "model": model,
                    "kind": kind,
                    **{key: value for key, value in metrics.items() if key != "n"},
                }
            )
    return pd.DataFrame(rows)


def compare_existing_aggregate(reconstructed: pd.DataFrame) -> dict:
    """Compare with the canonical aggregate and report every disagreement."""
    existing_all = pd.read_csv(CANONICAL_TARGET_LEADERBOARD)
    existing = existing_all[existing_all["target"].eq(TARGET_COLUMN)].copy()
    columns = reconstructed.columns.tolist()
    missing_columns = sorted(set(columns) - set(existing.columns))
    extra_columns = sorted(set(existing.columns) - set(columns))
    keys = ["target", "split", "model", "kind"]
    mismatches: list[dict] = []

    if not missing_columns:
        left = reconstructed.sort_values(keys).reset_index(drop=True)
        right = existing[columns].sort_values(keys).reset_index(drop=True)
        if len(left) != len(right):
            mismatches.append(
                {
                    "type": "row_count",
                    "reconstructed": int(len(left)),
                    "existing": int(len(right)),
                }
            )
        for index in range(min(len(left), len(right))):
            row_key = {key: left.at[index, key] for key in keys}
            for column in columns:
                left_value = left.at[index, column]
                right_value = right.at[index, column]
                if pd.isna(left_value) and pd.isna(right_value):
                    continue
                if isinstance(left_value, (int, float)) and isinstance(
                    right_value, (int, float)
                ):
                    equal = math.isclose(
                        float(left_value),
                        float(right_value),
                        rel_tol=0.0,
                        abs_tol=1e-12,
                    )
                else:
                    equal = left_value == right_value
                if not equal:
                    mismatches.append(
                        {
                            "type": "value",
                            "key": row_key,
                            "column": column,
                            "reconstructed": None if pd.isna(left_value) else left_value,
                            "existing": None if pd.isna(right_value) else right_value,
                        }
                    )

    status = (
        "match"
        if not missing_columns and not extra_columns and not mismatches
        else "disagreement_reported_not_patched"
    )
    return {
        "status": status,
        "existing_artifact": _display_path(CANONICAL_TARGET_LEADERBOARD),
        "existing_artifact_sha256": _sha256(CANONICAL_TARGET_LEADERBOARD),
        "comparison_tolerance": {"relative": 0.0, "absolute": 1e-12},
        "reconstructed_rows": int(len(reconstructed)),
        "existing_rows": int(len(existing)),
        "missing_columns_in_existing": missing_columns,
        "extra_columns_in_existing": extra_columns,
        "mismatches": mismatches,
        "policy": "Any disagreement is reported here; the canonical aggregate is never patched.",
    }


def _write_manifest(
    output_dir: Path,
    output_paths: list[Path],
    read_only_sources: list[dict],
    feature_cols: list[str],
    family_conclusion: dict,
    report: dict,
) -> Path:
    manifest_path = output_dir / "artifact_manifest.json"
    payload = {
        "schema_version": "2.0.0",
        "task": "R3-TGT-01",
        **_frozen_provenance(feature_cols),
        "reporting_policy": build_reporting_policy(),
        "family_conclusion": family_conclusion,
        "estimand_invariance_audit": report["estimand_invariance_audit"],
        "cross_basis_multiplicity": report["cross_basis_multiplicity"],
        "coincident_baselines": report["coincident_baselines"],
        "ic_sign_note": report["ic_sign_note"],
        "review_package_scope": report["review_package_scope"],
        "makefile_target_provenance": report["makefile_target_provenance"],
        "frozen_protected_boundary": report["frozen_protected_boundary"],
        "permutation_analyses": {
            "primary": report["analysis"]["primary_permutation"],
            "post_review_sensitivity": report["analysis"][
                "trajectory_preserving_sensitivity"
            ],
        },
        "source_artifacts": read_only_sources,
        "artifacts": [
            {
                "path": _display_path(path),
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
            }
            for path in sorted(output_paths)
        ],
        "manifest_self_record": {
            "path": _display_path(manifest_path),
            "sha256": None,
            "reason": "A deterministic manifest cannot embed its own checksum without recursion.",
        },
        "claim_safety": {
            "descriptive_research_evidence_only": True,
            "investment_value_established": False,
            "reliable_predictive_edge_established": False,
        },
    }
    assert_no_selection_keys(payload)
    manifest_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest_path


# ---------------------------------------------------------------------------
# Markdown rendering (family-level; no privileged model)
# ---------------------------------------------------------------------------


def _fmt(value: float | None, digits: int = 3) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"


def render_family_markdown(
    report: dict, per_year: dict[int, int], aggregate_comparison: dict
) -> str:
    """Render the report with all six family members treated identically."""
    family_conclusion = report["family_conclusion"]
    analysis = report["analysis"]
    procedure = analysis["bootstrap_procedure"]
    evaluated = analysis["evaluated_tickers_per_model_split"]
    evaluated_label = ", ".join(str(value) for value in evaluated)
    by_name = {result["model"]: result for result in report["models"]}
    audit = report["estimand_invariance_audit"]
    primary = analysis["primary_permutation"]
    sensitivity = analysis["trajectory_preserving_sensitivity"]
    comparison = report["significance_comparison"]
    cross_basis = report["cross_basis_multiplicity"]
    coincident = report["coincident_baselines"]
    sign_note = report["ic_sign_note"]
    package_scope = report["review_package_scope"]
    recipe_provenance = report["makefile_target_provenance"]
    boundary = report["frozen_protected_boundary"]

    lines = [
        f"# {BASIS_LABEL} evaluation (R3-TGT-01)",
        "",
        "Descriptive historical research evidence only; not investment value or "
        "investment advice. The nominal TRY evaluation remains the canonical "
        "headline and is not replaced.",
        "",
        f"Target: `{TARGET_COLUMN}`. Generator: `{GENERATOR}`. Regenerate with "
        f"`{REGENERATION_COMMAND}` using the recorded frozen splits, model "
        "specifications, and seeds.",
        "",
        "## Family-level conclusion",
        "",
        family_conclusion["conclusion"],
        "",
        family_conclusion["bootstrap_interpretation"],
        "",
        "## Reporting policy",
        "",
        report["reporting_policy"]["statement"],
        "",
        "Models appear below in the frozen prespecified order "
        f"({', '.join(FROZEN_ML_FAMILY)}), which is fixed in advance and is never "
        "reordered by an observed statistic.",
        "",
        "## Estimand: within-year ordinal ranking",
        "",
        audit["estimand_statement"],
        "",
        f"The nominal target column is traced from repository authority "
        f"(`{audit['nominal_target_authority']}`) rather than assumed, and the derivation "
        f"`{audit['derivation']}` is read from `{audit['excess_derivation_authority']}`. "
        "The audit below then checks, on the exact evaluated rows, that the subtraction is "
        "one common value inside each evaluation year and that the two targets rank the "
        "cohort identically. The run fails if either condition does not hold.",
        "",
        "| Evaluation year | Evaluated rows | Common BIST100 return subtracted (pp) | "
        "Within-year subtrahend spread | Rank mismatches |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for entry in audit["per_year"]:
        lines.append(
            f"| {entry['evaluation_year']} | {entry['evaluated_rows']} | "
            f"{entry['common_benchmark_return_pct']:.2f} | "
            f"{entry['within_year_subtrahend_spread']:.2e} | "
            f"{entry['rank_mismatch_count']} |"
        )
    lines.extend(
        [
            "",
            f"Nominal target column: `{audit['nominal_target_column']}`. Excess target "
            f"column: `{audit['excess_target_column']}`. Total rank mismatch count across "
            f"{_year_phrase(audit['evaluated_years'])}: "
            f"**{audit['total_rank_mismatch_count']}**.",
            "",
            audit["interpretation"],
            "",
            audit["fitting_effect_note"],
            "",
            "## Permutation analyses: prespecified primary and post-review sensitivity",
            "",
            "Two permutation analyses are reported side by side. They answer different "
            "questions and neither replaces the other.",
            "",
            f"**`{primary['analysis_id']}`** ({primary['status']}, unchanged). Null: "
            f"{primary['null_hypothesis']} It uses {primary['draws']:,} draws at seed "
            f"{primary['seed']}, a two-sided absolute tail, the Monte Carlo correction "
            f"`{primary['monte_carlo_correction']}`, the equal-year pooled IC, and "
            f"{primary['family_size']}-model Bonferroni adjustment. Human review did not "
            "change its seed, draw count, tail, correction, statistic, or family size, and "
            "it was not renamed or replaced.",
            "",
            f"**`{sensitivity['analysis_id']}`** ({sensitivity['status']}). Null: "
            f"{sensitivity['null_hypothesis']} It uses {sensitivity['requested_draws']:,} "
            f"draws at frozen seed {sensitivity['seed']}, a two-sided absolute tail, the "
            f"same Monte Carlo correction `{sensitivity['p_value_formula']}`, the equal-year "
            f"pooled IC, and the same {sensitivity['family_size']}-model Bonferroni "
            "adjustment applied independently to its own raw p-values.",
            "",
            sensitivity["provenance"],
            "",
            "Sensitivity algorithm, per draw:",
            "",
            *[f"{index}. {step}" for index, step in enumerate(sensitivity["algorithm"], 1)],
            "",
            "Each mapping is a duplicate-free one-to-one permutation of the "
            f"{sensitivity['ticker_universe_size']}-ticker universe: this is a permutation "
            "test, not a bootstrap. The following inputs are refused rather than degraded "
            f"({', '.join(sensitivity['refusal_exceptions'])}): "
            f"{'; '.join(sensitivity['refused_inputs'])}.",
            "",
            "## Evaluated cohort",
            "",
            "The evaluated cohort is the benchmark-covered public 40: the 40 tickers "
            "that carry a valid BIST100-relative excess target. It is a subset of the "
            "wider internal training universe used by the nominal basis. Rows without a "
            "valid excess target remain null and are never filled.",
            "",
            "| Test year | Evaluated rows (excess basis) | Nominal-basis rows (context) |",
            "| ---: | ---: | ---: |",
        ]
    )
    for year, rows in sorted(per_year.items()):
        lines.append(f"| {year} | {rows} | {NOMINAL_ROWS_PER_TEST_YEAR} |")
    lines.extend(
        [
            "",
            f"The {NOMINAL_ROWS_PER_TEST_YEAR}-row column is nominal-basis context on a "
            "different target and a wider cohort. It is not this evaluation's design. "
            f"{report['power_analysis']['current_design']['description']}",
        ]
    )

    lines.extend(
        [
            "",
            f"Aggregate leaderboard reconstruction status: "
            f"**{aggregate_comparison['status']}**. The existing aggregate is read-only; "
            "any disagreement is reported in the JSON artifact and is not patched.",
            "",
            "## Prespecified six-model ML family",
            "",
            "All six members are reported with the same schema, in the frozen order. Both "
            "analyses appear for every member: raw and Bonferroni-adjusted p-values are "
            "paired for the prespecified primary permutation and, separately, for the "
            "post-review trajectory-preserving sensitivity. No member is singled out as "
            "strongest, and no minimum-p member is identified.",
            "",
            "| Model | Pooled IC | Permutation p (raw) | Bonferroni-adjusted p | "
            "Sensitivity permutation p (raw) | Sensitivity Bonferroni-adjusted p | "
            "Either corrected analysis rejects at FWER 0.05 | "
            "Ticker-cluster bootstrap 95% interval |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    comparison_rows = {row["model"]: row for row in comparison["family"]}
    for model in FROZEN_ML_FAMILY:
        row = comparison_rows[model]
        interval = row["ticker_cluster_bootstrap_ci_95"]
        lines.append(
            f"| {model} | {_fmt(row['pooled_equal_year_ic'])} | "
            f"{_fmt(row['primary_raw_permutation_p'], 4)} | "
            f"{_fmt(row['primary_bonferroni_p'], 4)} | "
            f"{_fmt(row['sensitivity_raw_permutation_p'], 4)} | "
            f"{_fmt(row['sensitivity_bonferroni_p'], 4)} | "
            f"{'yes' if row['either_family_corrected_analysis_rejects_fwer_0_05'] else 'no'} | "
            f"[{_fmt(interval[0])}, {_fmt(interval[1])}] |"
        )

    lines.extend(
        [
            "",
            f"{family_conclusion['count_surviving_family_wise_correction']} of "
            f"{family_conclusion['family_size']} family members survive the Bonferroni "
            "gate at a family-wise alpha of 0.05 under the prespecified primary "
            "permutation, and "
            f"{family_conclusion['count_surviving_sensitivity_family_wise_correction']} of "
            f"{family_conclusion['family_size']} survive it under the post-review "
            "trajectory-preserving sensitivity. Both counts are computed from the adjusted "
            "p-values above; neither is assumed.",
            "",
            comparison["conclusion"],
            "",
            "## Non-family baselines",
            "",
            "These three baselines sit outside the ML family. They are context only: "
            "their p-values are unadjusted and are not part of the corrected family, under "
            "either analysis.",
            "",
            "| Baseline | Pooled IC | Permutation p (raw, unadjusted) | "
            "Sensitivity permutation p (raw, unadjusted) | "
            "Ticker-cluster bootstrap 95% interval |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    baseline_rows = {
        row["model"]: row
        for row in comparison["baselines_outside_the_corrected_family"]["rows"]
    }
    for model in FROZEN_BASELINES:
        row = baseline_rows[model]
        interval = row["ticker_cluster_bootstrap_ci_95"]
        lines.append(
            f"| {model} | {_fmt(row['pooled_equal_year_ic'])} | "
            f"{_fmt(row['primary_raw_permutation_p'], 4)} | "
            f"{_fmt(row['sensitivity_raw_permutation_p'], 4)} | "
            f"[{_fmt(interval[0])}, {_fmt(interval[1])}] |"
        )

    lines.extend(
        [
            "",
            "## Resampling procedure",
            "",
            "The pooled statistic is the equal-weighted mean of within-year Spearman ICs. "
            "Realized returns are shuffled within each test year for the permutation test; "
            "years are never pooled before permuting.",
            "",
            procedure["description"],
            "",
            f"Bootstrap unit: `{procedure['unit']}`; cluster key: `{procedure['cluster_key']}`; "
            f"{procedure['clusters']} clusters over trajectory years "
            f"{', '.join(str(year) for year in procedure['trajectory_years'])}; "
            f"{procedure['requested_resamples']} resamples at seed {procedure['seed']}; "
            f"interval convention: {procedure['interval_convention']}.",
            "",
            f"Interval role: {procedure['role']}.",
            "",
        ]
    )

    power = report["power_analysis"]
    current_design = power["current_design"]
    hypothetical = power["hypothetical_planning_sensitivities"]
    lines.extend(
        [
            "## Statistical power and minimum detectable IC",
            "",
            "Observed IC, detectable IC, and statistical power answer different questions. "
            "Observed IC is the sample estimate from the persisted dumps. Detectable IC is "
            "the assumed true |IC| that reaches 80% long-run rejection probability here; it "
            "is not a hard significance cutoff. Statistical power is that long-run probability, "
            "not the probability that a reported model is true. Practical investment relevance "
            "is not evaluated by this calculation.",
            "",
            f"The analytic calculation uses a two-sided Fisher-z approximation for Spearman "
            f"IC at alpha={power['alpha_two_sided']:.2f} and target power "
            f"{power['target_power']:.0%}. It covers one prespecified IC test; it is not the "
            "Bonferroni-adjusted family-wise power of the six-model family.",
            "",
            "### Current design (observed)",
            "",
            f"The current evaluated design is {current_design['rows_per_year']} rows per "
            f"evaluation year across {_year_phrase(current_design['years'])}, "
            f"{current_design['total_evaluated_rows_per_model']} evaluated rows per model in "
            "total. It is read from the persisted prediction dumps rather than assumed. The "
            "two rows below are two views of that one design, not two designs.",
            "",
            "| View of the current design | Rows/year | Test years | Total rows | Detectable \\|IC\\| (analytic) | Simulated power at analytic MDE | Agreement |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for view in current_design["views"]:
        lines.append(
            f"| {view['view_id']} | {view['n_per_split']} | "
            f"{view['split_count']} | {view['total_evaluated_rows']} | "
            f"{_fmt(view['analytic_minimum_detectable_abs_ic'])} | "
            f"{_fmt(view['simulated_power_at_analytic_mde'], 3)} | "
            f"{'within ±0.05' if view['agreement_within_tolerance'] else 'outside ±0.05'} |"
        )
    lines.extend(
        [
            "",
            "The seeded Gaussian-copula rank simulation checks several assumed true ICs for "
            "each view; full curves are in `significance_report.json`. Agreement means the "
            "simulated rejection rate at the analytic MDE is within 0.05 of 80%, not that the "
            "approximation or underlying design assumptions are proven correct.",
            "",
            power["non_rejection_interpretation"],
            "",
            "### Hypothetical planning horizons (not current evidence)",
            "",
            hypothetical["label"].capitalize() + ".",
            "",
            hypothetical["framing"],
            "",
            "These rows are hypothetical. They describe evidence that does not exist "
            "yet. They are deduplicated against the observed design on the pair "
            f"({', '.join(hypothetical['deduplication_key'])}), so none of them "
            "restates the current design.",
            "",
            "| Additional test years (hypothetical) | Total test years | Planning rows/year | Detectable \\|IC\\| (analytic) |",
            "| ---: | ---: | ---: | ---: |",
        ]
    )
    for entry in hypothetical["entries"]:
        lines.append(
            f"| {entry['additional_test_years']} | {entry['total_test_years']} | "
            f"{entry['planning_rows_per_year']} | "
            f"{_fmt(entry['analytic_minimum_detectable_abs_ic'])} |"
        )
    lines.extend(
        [
            "",
            "Power-analysis limits:",
            "",
            *[f"- {limitation}" for limitation in power["limitations"]],
            "",
            "## Exploratory per-year results",
            "",
            f"The excess-basis dumps evaluate n={evaluated_label} per model and year from the "
            "benchmark-covered public 40. Each year below is a marginal view of the same "
            "shared ticker-cluster resample. With only three test years these rows remain "
            "exploratory and must not be promoted as discoveries.",
            "",
            "| Model | Year | n | IC | Permutation p | Ticker-cluster bootstrap 95% interval |",
            "| --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for model in [*FROZEN_ML_FAMILY, *FROZEN_BASELINES]:
        for split in by_name[model]["exploratory_by_split"]:
            interval = split["bootstrap_ci_95"]
            lines.append(
                f"| {model} | {split['year']} | {split['n']} | "
                f"{_fmt(split['observed_ic'])} | "
                f"{_fmt(split['permutation_p_value_two_sided'], 4)} | "
                f"[{_fmt(interval[0])}, {_fmt(interval[1])}] |"
            )

    lines.extend(
        [
            "",
            "## Cross-basis multiplicity",
            "",
            cross_basis["statement"],
            "",
            f"Confirmatory family: `{cross_basis['confirmatory_family']['basis_id']}` "
            f"(`{cross_basis['confirmatory_family']['target_column']}`). Exploratory "
            "robustness bases: "
            + ", ".join(f"`{basis['basis_id']}`" for basis in cross_basis["exploratory_bases"])
            + f". This evaluation is `{cross_basis['this_basis_id']}`, an "
            f"{cross_basis['this_basis_role']}.",
            "",
            cross_basis["future_result_policy"],
            "",
            "The canonical nominal artifacts are not altered by this task.",
            "",
            "## Coincident baseline specifications",
            "",
            coincident["strongest_supported_statement"],
            "",
            f"Equality level established from the persisted dumps: "
            f"`{coincident['equality_level']}`; maximum absolute prediction difference "
            f"{coincident['max_absolute_prediction_difference']:.1f} across all evaluated "
            "rows. " + coincident["wording_policy"],
            "",
            coincident["interpretation"],
            "",
            coincident["retention_policy"],
            "",
            "## Interpretation of predominantly negative IC signs",
            "",
            f"{sign_note['negative_pooled_ic_count']} of {sign_note['family_size']} "
            "prespecified ML-family members have a negative pooled equal-year IC on this "
            "basis.",
            "",
            sign_note["note"],
            "",
            sign_note["selection_note"],
            "",
            "## Scope of the compact human-review package",
            "",
            *[f"- {statement}" for statement in package_scope["statements"]],
            "",
            "## Provenance and protected boundary",
            "",
            "Provenance here is descriptive metadata about how these artifacts are "
            "regenerated and bounded. It does not affect any statistical result, "
            "conclusion, or claim boundary above, and neither the owner-authorized "
            "compatibility repair nor this metadata strengthens statistical validity.",
            "",
            "- Statistical source inputs are recorded under `source_artifacts` (the trusted "
            "modeling dataset, the read-only canonical leaderboard, and the frozen "
            "generator, experiment, and significance modules), each pinned by whole-file "
            "sha256.",
            "- Regeneration-recipe provenance is the single `research-excess` Makefile "
            f"target recipe (`{recipe_provenance['recipe_sha256'][:12]}…`), not the whole "
            "Makefile. Unrelated Makefile targets added by other tasks do not stale these "
            "artifacts, while editing this recipe or its prerequisites is still detected.",
            "- The frozen protected boundary is an explicit historical allow-list of "
            f"{boundary['member_count']} curated-data and pre-existing generated files that "
            "this regeneration must never mutate, pinned by a content digest. Namespaces "
            "added by later, unrelated governed tasks are not members of this historical "
            "set, were not part of the R3-TGT-01 review, and are governed by their own "
            "tasks; they cannot enlarge or invalidate this boundary.",
            "",
            "## Required limitations",
            "",
            *[f"- {limitation}" for limitation in report["limitations"]],
            "",
            "The absence of a detectable signal in this small, fixed cohort and single regime "
            "does not establish that other markets or better point-in-time datasets are unpredictable.",
            "",
            "This excess-return-basis evaluation is a descriptive historical research result; "
            "it does not establish signal, investment value, or a reliable predictive edge. "
            "Any isolated year or uncorrected p-value remains exploratory and must not be "
            "promoted as a finding.",
            "",
        ]
    )
    markdown = "\n".join(lines)
    forbidden = ("proves", "confirms market efficiency")
    if any(term in markdown.lower() for term in forbidden):
        raise ValueError("generated report contains forbidden overclaim wording")
    validate_excess_claim_safety_text(markdown)
    validate_no_selection_language(markdown)
    validate_no_current_design_row_contradiction(markdown)
    return markdown


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run(output_dir: Path | str | None = None) -> tuple[Path, Path, Path]:
    """Regenerate the isolated excess-basis artifacts.

    ``output_dir`` defaults to ``experiments/results_excess``.  The only other
    accepted destination is a ``financeiq-r3-tgt-01-*`` directory under the
    operating system's temporary root; :func:`_resolve_output_dir` refuses
    everything else before any file is created or overwritten.
    """
    target_dir = _resolve_output_dir(output_dir)
    panel, feature_cols = exp.build_panel_for_target(TARGET_COLUMN)
    if panel is None:
        raise ValueError(f"no usable rows for {TARGET_COLUMN}")
    target_dir.mkdir(parents=True, exist_ok=True)

    prediction_paths = _write_prediction_dumps(panel, feature_cols, target_dir)
    prediction_frame, prediction_sources = significance.load_prediction_dumps(target_dir)
    per_year = _evaluated_rows_per_year(prediction_frame)

    leaderboard = reconstruct_leaderboard(prediction_frame)
    leaderboard_path = target_dir / "leaderboard.csv"
    leaderboard.to_csv(leaderboard_path, index=False, lineterminator="\n")
    aggregate_comparison = compare_existing_aggregate(leaderboard)

    read_only_sources = _read_only_sources()
    report_sources = [*prediction_sources, *read_only_sources]

    # significance.build_report is never called here: it selects the family
    # member with the smallest raw permutation p-value, and deleting that field
    # afterwards would still have executed the selection. The report is built
    # from per-model, non-selecting analyses, and the inherited within-year row
    # bootstrap is replaced by the ticker-cluster procedure.
    # Precondition, not decoration: the ordinal-estimand claim is only published
    # if the common within-year benchmark subtraction and the resulting rank
    # invariance are proven on these exact evaluated rows.
    estimand_audit = build_estimand_invariance_audit(prediction_frame)

    report = build_family_report(prediction_frame, report_sources, per_year)
    report = order_models_frozen(report)
    report = apply_cluster_bootstrap(report, prediction_frame)
    # The prespecified permutation above is left untouched; the post-review
    # sensitivity is attached beside it with its own Bonferroni adjustment.
    report = apply_trajectory_sensitivity(report, prediction_frame)

    report["task"] = "R3-TGT-01"
    report["provenance"] = _frozen_provenance(feature_cols)
    report["reporting_policy"] = build_reporting_policy()
    report["estimand_invariance_audit"] = estimand_audit
    report["significance_comparison"] = build_significance_comparison(report)
    report["cross_basis_multiplicity"] = build_cross_basis_multiplicity()
    report["coincident_baselines"] = build_coincident_baseline_evidence(prediction_frame)
    report["ic_sign_note"] = build_ic_sign_note(report)
    report["review_package_scope"] = build_review_package_scope()
    report["makefile_target_provenance"] = build_makefile_target_provenance()
    report["frozen_protected_boundary"] = build_frozen_protected_boundary()
    report["family_conclusion"] = build_family_conclusion(report)
    report["target_basis"] = {
        "id": BASIS_ID,
        "label": BASIS_LABEL,
        "target_column": TARGET_COLUMN,
        "evaluated_rows_per_year": per_year,
        "nominal_basis_rows_per_test_year_context": NOMINAL_ROWS_PER_TEST_YEAR,
        "cohort": "benchmark-covered public 40",
        "cohort_note": (
            "The evaluated cohort is the 40-ticker benchmark-covered public universe, "
            "a subset of the wider internal training universe used by the nominal "
            "basis. Missing excess targets remain null and are never filled."
        ),
    }
    report["analysis"]["aggregate_leaderboard_reconstruction"] = aggregate_comparison
    report["limitations"].extend(
        [
            COVERAGE_LIMITATION,
            CLUSTER_LIMITATION,
            CROSS_BASIS_LIMITATION,
            NEGATIVE_IC_LIMITATION,
            REVIEW_PACKAGE_LIMITATION,
        ]
    )
    report["claim_safety"] = {
        "descriptive_research_evidence_only": True,
        "investment_value_established": False,
        "reliable_predictive_edge_established": False,
        "benchmark_relative_signal_established": False,
        "result_driven_model_selection_performed": False,
        "multiplicity_gate": "Bonferroni across the same six-model ML family",
        "cross_basis_multiplicity_controlled": False,
        "confirmatory_family": CONFIRMATORY_BASIS_ID,
        "this_basis_role": "exploratory robustness evaluation",
        "estimand": "within-year ordinal cross-sectional ranking",
        "alpha_estimated": False,
        "benchmark_relative_magnitude_accuracy_evaluated": False,
        "tradable_strategy_established": False,
        "inverse_alpha_or_contrarian_interpretation": False,
        "bootstrap_interpretation": BOOTSTRAP_INTERPRETATION,
        "statement": (
            "Descriptive historical research result on a benchmark-relative basis; "
            "it does not establish signal, investment value, or a reliable predictive edge."
        ),
    }
    assert_no_selection_keys(report)

    json_path = target_dir / "significance_report.json"
    markdown_path = target_dir / "significance_report.md"
    # Render and cross-check before writing: the JSON and the Markdown must
    # agree about the observed design, and neither may call 80 rows current.
    markdown = render_family_markdown(report, per_year, aggregate_comparison)
    validate_power_design_consistency(report, markdown, per_year)
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(markdown, encoding="utf-8")

    manifest_path = _write_manifest(
        target_dir,
        [*prediction_paths, leaderboard_path, json_path, markdown_path],
        read_only_sources,
        feature_cols,
        report["family_conclusion"],
        report,
    )

    family_conclusion = report["family_conclusion"]
    print(
        f"[{BASIS_ID}] six-model ML family reported symmetrically in frozen order; "
        f"{family_conclusion['count_surviving_family_wise_correction']} of "
        f"{family_conclusion['family_size']} survive Bonferroni at FWER 0.05"
    )
    print(
        f"Bootstrap unit: {BOOTSTRAP_UNIT} "
        f"({report['analysis']['bootstrap_procedure']['clusters']} ticker trajectories, "
        f"seed {report['analysis']['bootstrap_procedure']['seed']})"
    )
    print(
        f"Estimand audit: {estimand_audit['total_rank_mismatch_count']} rank mismatches "
        f"across {len(estimand_audit['evaluated_years'])} evaluation years; the within-year "
        "IC estimand is unchanged by benchmark subtraction"
    )
    print(
        f"Post-review sensitivity ({TRAJECTORY_SENSITIVITY_ID}): "
        f"{family_conclusion['count_surviving_sensitivity_family_wise_correction']} of "
        f"{family_conclusion['family_size']} survive Bonferroni at FWER 0.05"
    )
    print(f"Aggregate reconstruction: {aggregate_comparison['status']}")
    print(family_conclusion["conclusion"])
    print(family_conclusion["bootstrap_interpretation"])
    print("The canonical nominal TRY artifacts and conclusion are unchanged.")
    return json_path, markdown_path, manifest_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Optional isolated output directory for tests and deterministic "
            "verification. Defaults to experiments/results_excess. The only other "
            f"accepted destination is a {TEMP_OUTPUT_PREFIX}* directory under the "
            "temporary root reported by tempfile.gettempdir(); every other path, "
            "including symlinked ones, is refused."
        ),
    )
    args = parser.parse_args(argv)
    run(args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
