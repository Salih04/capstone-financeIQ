"""Stage 1 — raw-layer positive control / synthetic signal injection.

Pre-registered in ``docs/thesis/PRE_EXPERIMENT_PROTOCOL.md`` (Stage 1 entry plus
the dated 2026-08-27 implementation amendment). Nothing here may be tuned after
looking at a result; the injection grid, the repetition count, the carrier
selection rules, the family size, and the seeds are all fixed in that document.

What this does
--------------
A synthetic signal of *known* strength is written into one **raw** feature
column of the modeling CSV — in that column's own units, with its own
missingness, before ``run_experiments.build_panel()`` does any feature
construction — and the unmodified walk-forward pipeline is then asked to
recover it.

The injection is a within-year permutation of the carrier column's *own*
observed values, ordered by a Gaussian-copula latent score built from the
future-return ranking:

    z = Phi^-1(rank(y)/(n+1)), rescaled to unit sd    (normal scores of the target)
    rho = 2 * sin(pi * theta / 6)                     (Gaussian-copula Spearman identity)
    s   = rho * z + sqrt(1 - rho^2) * eps             (eps ~ N(0,1), declared seed)
    carrier'[i] = sorted(carrier_observed)[rank(s_i) - 1]

Consequences, each of which is a property of the construction rather than an
assumption:

* the carrier's within-year marginal distribution is preserved *exactly*
  (it is a permutation of its own values) — nothing is fabricated or imputed;
* its missingness pattern is preserved *exactly* — null stays null;
* the target column and every other feature column are bit-identical;
* ``theta = 0`` reduces to a plain random within-year permutation, so the null
  rung forces no correlation whatsoever;
* ``carrier'`` is a strictly increasing function of ``s`` on the observed
  cells, so the realized rank correlation to the target equals that of ``s``.

``rho = 2 sin(pi theta / 6)`` is the same identity ``significance.py`` already
uses in ``simulate_fisher_power``, which is what makes the empirical detection
curve comparable to the governed analytic power machinery.

Claim discipline
----------------
This is apparatus validation on synthetic input. It says nothing about BIST,
about returns, or about investment value. A recovered IC here is a measurement
of the measuring instrument, and the repository's committed finding — pooled
walk-forward IC statistically indistinguishable from zero after multiplicity
correction — is untouched by it.

Run:
    make thesis-positive-control
Outputs: experiments/results_thesis/positive_control/
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import platform
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments import run_experiments as rx  # noqa: E402
from experiments import significance as sig  # noqa: E402
from experiments.placebo_lab import validate_claim_safety_text  # noqa: E402
from experiments.thesis import provenance as prov  # noqa: E402

SLUG = "positive_control"

# --------------------------------------------------------------------------- #
# Pre-registered constants. Every one of these is fixed in
# docs/thesis/PRE_EXPERIMENT_PROTOCOL.md and must not be edited to change an
# outcome. Changing one requires a dated amendment in that document.
# --------------------------------------------------------------------------- #

#: Stage 1 injection grid, straddling the frozen baseline MDE. Fixed constants
#: section of the protocol. No level may be added, removed, or interpolated.
IC_GRID: tuple[float, ...] = (0.00, 0.10, 0.20, 0.30, 0.40)

#: Committed `current_three_year_pooled` analytic MDE from the frozen baseline.
MDE_BASE = 0.182271

#: Grid levels above MDE_BASE, which the Stage 1 pass rule requires to reject.
GATE_LEVELS: tuple[float, ...] = (0.30, 0.40)

#: The single prespecified model for the confirmatory family.
PRIMARY_MODEL = "ridge"

#: Confirmatory family: 5 injection levels x 1 model. Bonferroni across it.
CONFIRMATORY_FAMILY_SIZE = len(IC_GRID)

#: Repetitions per level in each descriptive arm (amendment, fixed pre-run).
DESCRIPTIVE_REPETITIONS = 200

#: Repetition index 0 *is* the confirmatory run; its permutation seed is the
#: governed default so the confirmatory arm uses significance.py's own setting.
CONFIRMATORY_REPETITION = 0

#: Governed significance defaults, used unchanged.
PERMUTATIONS = sig.DEFAULT_PERMUTATIONS
BOOTSTRAPS = sig.DEFAULT_BOOTSTRAPS
ALPHA = 0.05

#: Strong-signal sanity control. Explicitly OUTSIDE the preregistered grid: it
#: is a smoke test with an expected answer, is excluded from the power curve,
#: and may not be used to locate the >=80% detection threshold.
SANITY_IC = 0.90

#: Carrier selection rules, applied to the raw feature columns. Both are
#: coverage rules — properties of the data, not of any experimental outcome.
PRIMARY_CARRIER_RULE = "alphabetically first feature column with 100% coverage in every panel year"
SECONDARY_CARRIER_RULE = "alphabetically first feature column with overall coverage below 0.60"
SECONDARY_COVERAGE_CEILING = 0.60

#: NaN fill the ML path applies to rank-normalized features. Mirrors
#: run_experiments._fit_sklearn; tests assert the two stay behaviourally equal.
RANK_IMPUTE_CENTER = 0.5

ROUND_DIGITS = 12

CLAIM_SAFETY_SENTENCE = (
    "This stage injects a synthetic relationship into one raw column and measures how "
    "much of it survives the pipeline. It is apparatus validation on manufactured input, "
    "not evidence about BIST equities: recovering an injected quantity says only that the "
    "instrument responds to a known input, and the repository's committed walk-forward "
    "null is untouched by anything measured here."
)

PANEL_ID_COLUMNS = ("ticker", "feature_year", "target_return")
TARGET_COLUMN = "next_year_return_pct"
YEAR_COLUMN = "year"

OUTPUT_FILENAMES = {
    "report_json": "positive_control_report.json",
    "report_md": "positive_control_report.md",
    "repetitions": "repetitions.csv",
    "detection_curve": "detection_curve.csv",
    "attenuation": "attenuation_by_stage.csv",
}

#: Ordered attenuation checkpoints. Each is a single identifiable scalar: an
#: equal-year-weighted pooled Spearman IC over the three test cross-sections.
CHECKPOINTS: tuple[tuple[str, str], ...] = (
    ("ic_injected", "intended injected IC (design constant theta)"),
    ("ic_raw_carrier", "identity/invariant checkpoint: realized IC of the carrier column in the raw CSV, observed cells only, before feature construction"),
    ("ic_panel_carrier", "identity/invariant checkpoint: IC of the carrier after build_panel's within-year rank-percentile normalization"),
    ("ic_model_input_carrier", "identity/invariant checkpoint: IC of the carrier column as the model actually receives it, after NaN -> 0.5 rank imputation, full cross-section"),
    ("ic_model_prediction", "substantive transition: IC of the fitted ridge prediction vector against the realized target"),
    ("ic_final_evaluation", "evaluation identity checkpoint: pooled IC as reported by the governed significance machinery"),
)

# These roles prevent an invariant checkpoint from being mistaken for a
# measured attenuation stage. The meaningful transition in the primary arm is
# carrier signal -> fitted model prediction.
CHECKPOINT_ROLES: dict[str, str] = {
    "ic_injected": "design_constant",
    "ic_raw_carrier": "identity_invariant",
    "ic_panel_carrier": "identity_invariant",
    "ic_model_input_carrier": "identity_invariant",
    "ic_model_prediction": "substantive_transition",
    "ic_final_evaluation": "evaluation_identity",
}

# Reporting-only suppression rule. It does not alter the experiment or any
# inference: when the theta=0 background is at least half as large as theta, a
# ratio to theta is too easy to misread as a pipeline coefficient.
BACKGROUND_DOMINANCE_FRACTION = 0.5

IDENTITY_INVARIANT_SUPPRESSION_REASON = (
    "identity/invariant checkpoint — attenuation ratio not interpreted"
)


class PositiveControlError(RuntimeError):
    """Raised when the stage would violate its own pre-registration."""


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_path(path: Path) -> str:
    return prov.sha256_path(path)


def _rounded(value: float | None, digits: int = ROUND_DIGITS) -> float | None:
    if value is None:
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return round(float(value), digits)


def _git_metadata() -> dict:
    def _git(*args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
        )
        return result.stdout.strip()

    try:
        sha = _git("rev-parse", "HEAD")
        dirty = bool(_git("status", "--porcelain", "--untracked-files=normal"))
    except (OSError, subprocess.CalledProcessError):
        return {"sha": None, "short_sha": "nogit", "dirty": None}
    return {"sha": sha, "short_sha": sha[:8], "dirty": dirty}


def implementation_hash() -> str:
    """SHA256 of this module's own source.

    Recorded with every result so a later reader can tell whether the injection
    code that produced an artifact is the code now on disk.
    """
    return _sha256_path(Path(__file__).resolve())


def derive_injection_seed(base_seed: int, level_index: int, repetition: int) -> int:
    """Deterministic per-(level, repetition) injection seed.

    Declared formula, not a clock read and not a runtime choice. Distinct
    ``(level_index, repetition)`` pairs give distinct streams, and the same pair
    always gives the same stream.
    """
    if level_index < 0 or repetition < 0:
        raise ValueError("level_index and repetition must be non-negative")
    return int(base_seed * 1_000_003 + level_index * 10_007 + repetition)


def derive_permutation_seed(base_seed: int, repetition: int) -> int:
    """Permutation seed for a repetition, shared across levels.

    Depending on the repetition only (not the level) means a given repetition
    resamples identically at every injection level, so differences along the
    curve come from the injection rather than from permutation noise.
    Repetition 0 returns ``significance.DEFAULT_SEED`` so the confirmatory arm
    runs on the governed default.
    """
    if repetition < 0:
        raise ValueError("repetition must be non-negative")
    del base_seed  # deliberately unused: repetition 0 must be the governed default
    return int(sig.DEFAULT_SEED + repetition)


def latent_correlation_for_ic(theta: float) -> float:
    """Gaussian-copula Pearson correlation delivering Spearman IC ``theta``.

    Inverts ``rho_s = (6/pi) asin(rho_p / 2)``. This is the identity
    ``significance.simulate_fisher_power`` already uses, so the injected level
    and the governed analytic power curve are expressed on the same scale.
    """
    if not -1.0 < theta < 1.0:
        raise ValueError("theta must be strictly between -1 and 1")
    return 2.0 * math.sin(math.pi * theta / 6.0)


def pooled_spearman_by_year(
    values: pd.Series, targets: pd.Series, years: pd.Series
) -> tuple[float | None, int, dict[int, float]]:
    """Equal-weight mean of within-year Spearman ICs — the frozen baseline statistic.

    Pairs with a null on either side are dropped within their own year, so the
    returned ``n`` reports how many rows actually contributed. Returns
    ``(pooled_ic, n_used, per_year)``.
    """
    frame = pd.DataFrame(
        {"value": pd.to_numeric(values, errors="coerce").to_numpy(dtype=float),
         "target": pd.to_numeric(targets, errors="coerce").to_numpy(dtype=float),
         "year": np.asarray(years)}
    ).dropna(subset=["value", "target"])
    per_year: dict[int, float] = {}
    total = 0
    for year, group in frame.groupby("year", sort=True):
        if len(group) < 3:
            continue
        ic = sig.spearman_ic(group["value"].to_numpy(float), group["target"].to_numpy(float))
        if math.isfinite(ic):
            per_year[int(year)] = float(ic)
            total += len(group)
    if not per_year:
        return None, 0, {}
    return float(np.mean(list(per_year.values()))), int(total), per_year


# --------------------------------------------------------------------------- #
# Carrier selection
# --------------------------------------------------------------------------- #
def raw_feature_columns(raw: pd.DataFrame) -> list[str]:
    """Feature columns of the raw modeling CSV, exactly as build_panel selects them."""
    return sorted(rx._feature_cols(raw))


def select_carriers(raw: pd.DataFrame) -> dict[str, str]:
    """Apply the pre-registered carrier rules to the raw table.

    Both rules are coverage rules. They read the data's missingness only and
    cannot see any experimental result, which is why they can be applied at run
    time without becoming a post-hoc choice.
    """
    features = raw_feature_columns(raw)
    per_year = raw.groupby(YEAR_COLUMN)[features].apply(lambda block: block.notna().mean())
    overall = raw[features].notna().mean()

    full = [c for c in features if bool((per_year[c] >= 1.0).all())]
    if not full:
        raise PositiveControlError(
            f"no feature column satisfies the primary carrier rule ({PRIMARY_CARRIER_RULE})"
        )
    partial = [c for c in features if float(overall[c]) < SECONDARY_COVERAGE_CEILING]
    if not partial:
        raise PositiveControlError(
            f"no feature column satisfies the secondary carrier rule ({SECONDARY_CARRIER_RULE})"
        )
    return {"primary": full[0], "secondary": partial[0]}


# --------------------------------------------------------------------------- #
# Injection
# --------------------------------------------------------------------------- #
def inject_carrier(
    raw: pd.DataFrame, carrier: str, theta: float, *, seed: int
) -> pd.DataFrame:
    """Return a copy of ``raw`` with a known-strength signal in ``carrier``.

    The carrier's observed values are permuted **within each year** into the
    order of a Gaussian-copula latent score built from that year's future-return
    ranking. Nothing else in the table changes, and no value is invented: the
    output column is a rearrangement of the input column's own numbers.

    ``theta = 0`` gives ``rho = 0``, i.e. a latent score independent of the
    target — a plain random permutation that forces no correlation.
    """
    if carrier not in raw.columns:
        raise PositiveControlError(f"carrier column {carrier!r} is not in the raw table")
    if TARGET_COLUMN not in raw.columns:
        raise PositiveControlError(f"raw table has no {TARGET_COLUMN!r} column")
    if not 0.0 <= theta < 1.0:
        raise ValueError("theta must satisfy 0 <= theta < 1")

    rho = latent_correlation_for_ic(theta)
    residual = math.sqrt(max(0.0, 1.0 - rho * rho))
    rng = np.random.default_rng(seed)
    injected = raw.copy(deep=True)
    carrier_values = pd.to_numeric(raw[carrier], errors="coerce")
    target_values = pd.to_numeric(raw[TARGET_COLUMN], errors="coerce")

    for year in sorted(raw[YEAR_COLUMN].unique()):
        year_mask = (raw[YEAR_COLUMN] == year).to_numpy()
        observed_mask = year_mask & carrier_values.notna().to_numpy()
        observed_index = np.flatnonzero(observed_mask)
        if observed_index.size == 0:
            continue

        # eps is drawn for every observed cell, for every year, in a fixed order,
        # so the stream does not depend on how many rows happen to have targets.
        noise = rng.standard_normal(observed_index.size)
        latent = noise.astype(float, copy=True)

        has_target = target_values.to_numpy()[observed_index]
        target_mask = np.isfinite(has_target)
        if rho != 0.0 and int(target_mask.sum()) >= 3:
            targets = has_target[target_mask]
            ranks = pd.Series(targets).rank(method="average").to_numpy(dtype=float)
            uniform = ranks / (len(targets) + 1.0)
            scores = np.asarray(
                [sig._STANDARD_NORMAL.inv_cdf(float(u)) for u in uniform], dtype=float
            )
            spread = float(scores.std(ddof=0))
            if spread > 0.0:
                scores = scores / spread
            latent[target_mask] = rho * scores + residual * noise[target_mask]

        # Strictly increasing reassignment of the column's own observed values.
        order = np.argsort(np.argsort(latent, kind="stable"), kind="stable")
        sorted_values = np.sort(carrier_values.to_numpy()[observed_index])
        injected.iloc[observed_index, injected.columns.get_loc(carrier)] = sorted_values[order]

    return injected


@contextlib.contextmanager
def _pipeline_reads(path: Path) -> Iterator[None]:
    """Point ``run_experiments`` at ``path`` for the duration of the block.

    The real modeling CSV is never modified. The override is restored on every
    exit path, so the production pipeline is unchanged the moment the block ends
    — ``tests/test_thesis_positive_control.py`` asserts exactly that. The
    temporary mutation of ``run_experiments.TRAINING_MODELING`` is process-global
    and not thread-safe; this experiment is intentionally single-threaded.
    Architectural redesign is outside this bounded task.
    """
    original = rx.TRAINING_MODELING
    rx.TRAINING_MODELING = path
    try:
        yield
    finally:
        rx.TRAINING_MODELING = original


# --------------------------------------------------------------------------- #
# One repetition
# --------------------------------------------------------------------------- #
def _ridge_predictions(
    panel: pd.DataFrame, feature_columns: list[str], carrier: str
) -> tuple[pd.DataFrame, dict]:
    """Run the prespecified model through the real walk-forward split logic.

    Mirrors ``run_experiments.run`` — same split filters, same model callable,
    same prediction-dump schema — restricted to the one prespecified model. Also
    returns the carrier column *as the model received it*, which is the
    missingness/transform attenuation checkpoint.
    """
    model_fn = rx.MODELS[PRIMARY_MODEL][1]
    carrier_index = feature_columns.index(carrier)
    prediction_rows: list[dict] = []
    model_input_rows: list[dict] = []

    for split in rx.SPLITS:
        train = panel[(panel["feature_year"] + 1).isin(split["train_target_years"])]
        test = panel[panel["feature_year"] == split["test_feature_year"]]
        x_train = train[feature_columns].to_numpy(float)
        y_train = train["target_return"].to_numpy(float)
        x_test = test[feature_columns].to_numpy(float)
        y_test = test["target_return"].to_numpy(float)
        train_mask = ~np.isnan(y_train)
        x_train, y_train = x_train[train_mask], y_train[train_mask]

        predicted = np.asarray(model_fn(x_train, y_train, x_test), dtype=float)
        evaluated = ~np.isnan(y_test) & ~np.isnan(predicted)
        # The same imputation _fit_sklearn applies internally, so this is the
        # carrier vector the estimator actually saw.
        seen_carrier = np.nan_to_num(x_test, nan=RANK_IMPUTE_CENTER)[:, carrier_index]
        year = split["test_feature_year"] + 1

        for ticker, actual, prediction, seen in zip(
            test.loc[evaluated, "ticker"],
            y_test[evaluated],
            predicted[evaluated],
            seen_carrier[evaluated],
        ):
            prediction_rows.append(
                {
                    "ticker": ticker,
                    "year": year,
                    "model": PRIMARY_MODEL,
                    "y_true": float(actual),
                    "y_pred": float(prediction),
                    "split": split["name"],
                }
            )
            model_input_rows.append(
                {"year": year, "carrier_seen": float(seen), "y_true": float(actual)}
            )

    return pd.DataFrame(prediction_rows), {"model_input": pd.DataFrame(model_input_rows)}


def run_repetition(
    raw: pd.DataFrame,
    carrier: str,
    theta: float,
    *,
    injection_seed: int,
    permutation_seed: int,
    permutations: int = PERMUTATIONS,
    bootstraps: int = BOOTSTRAPS,
) -> dict:
    """Inject, run the real pipeline, and measure every attenuation checkpoint.

    The injected table is written to a private temporary directory and deleted
    when the repetition ends. It is never written under ``data/``.
    """
    injected = inject_carrier(raw, carrier, theta, seed=injection_seed)
    test_feature_years = sorted(split["test_feature_year"] for split in rx.SPLITS)

    with tempfile.TemporaryDirectory(prefix="financeiq-positive-control-") as scratch:
        injected_path = Path(scratch) / "modeling_dataset_training_injected.csv"
        injected.to_csv(injected_path, index=False)
        injected_sha = _sha256_path(injected_path)
        with _pipeline_reads(injected_path):
            panel = rx.build_panel()

    feature_columns = [c for c in panel.columns if c not in PANEL_ID_COLUMNS]
    if carrier not in feature_columns:
        raise PositiveControlError(
            f"carrier {carrier!r} did not survive feature construction; "
            "the injection site is not on the modeled path"
        )

    # Checkpoint 1 — realized pre-pipeline IC, read straight off the raw table.
    # Measured from the carrier column itself, never from the latent score and
    # never from any model output.
    raw_test = injected[injected[YEAR_COLUMN].isin(test_feature_years)]
    ic_raw, n_raw, raw_by_year = pooled_spearman_by_year(
        raw_test[carrier], raw_test[TARGET_COLUMN], raw_test[YEAR_COLUMN]
    )

    # Checkpoint 2 — after within-year rank-percentile feature construction.
    panel_test = panel[panel["feature_year"].isin(test_feature_years)]
    ic_panel, n_panel, panel_by_year = pooled_spearman_by_year(
        panel_test[carrier], panel_test["target_return"], panel_test["feature_year"]
    )

    predictions, extras = _ridge_predictions(panel, feature_columns, carrier)
    model_input = extras["model_input"]

    # Checkpoint 3 — after the ML path's NaN -> 0.5 imputation, full cross-section.
    ic_model_input, n_model_input, model_input_by_year = pooled_spearman_by_year(
        model_input["carrier_seen"], model_input["y_true"], model_input["year"]
    )

    # Checkpoint 4 — the model's own prediction vector.
    ic_prediction, n_prediction, prediction_by_year = pooled_spearman_by_year(
        predictions["y_pred"], predictions["y_true"], predictions["year"]
    )

    # Checkpoint 5 — the governed significance machinery, called unchanged.
    analysis = sig.analyze_model(
        predictions[sig.REQUIRED_COLUMNS + ["split"]],
        permutations=permutations,
        bootstraps=bootstraps,
        seed=permutation_seed,
    )
    pooled = analysis["pooled"]
    raw_p = float(pooled["permutation_p_value_two_sided"])
    adjusted_p = min(1.0, raw_p * CONFIRMATORY_FAMILY_SIZE)

    checkpoints = {
        "ic_injected": float(theta),
        "ic_raw_carrier": ic_raw,
        "ic_panel_carrier": ic_panel,
        "ic_model_input_carrier": ic_model_input,
        "ic_model_prediction": ic_prediction,
        "ic_final_evaluation": float(pooled["observed_ic"]),
    }
    counts = {
        "ic_injected": None,
        "ic_raw_carrier": n_raw,
        "ic_panel_carrier": n_panel,
        "ic_model_input_carrier": n_model_input,
        "ic_model_prediction": n_prediction,
        "ic_final_evaluation": int(pooled["n"]),
    }

    return {
        "carrier": carrier,
        "ic_injected": _rounded(theta),
        "injection_seed": int(injection_seed),
        "permutation_seed": int(permutation_seed),
        "injected_dataset_sha256": injected_sha,
        "checkpoints": {k: _rounded(v) for k, v in checkpoints.items()},
        "checkpoint_n": counts,
        "attenuation_ratio": attenuation_ratios(checkpoints),
        "stagewise_ratio": stagewise_ratios(checkpoints),
        "per_year": {
            "ic_raw_carrier": {str(k): _rounded(v) for k, v in raw_by_year.items()},
            "ic_panel_carrier": {str(k): _rounded(v) for k, v in panel_by_year.items()},
            "ic_model_input_carrier": {str(k): _rounded(v) for k, v in model_input_by_year.items()},
            "ic_model_prediction": {str(k): _rounded(v) for k, v in prediction_by_year.items()},
        },
        "permutation_p_value_two_sided": _rounded(raw_p),
        "bonferroni_adjusted_p_value": _rounded(adjusted_p),
        "detected": bool(adjusted_p < ALPHA),
        "bootstrap_ci_95": [_rounded(v) for v in pooled["bootstrap_ci_95"]],
    }


def attenuation_ratios(checkpoints: dict[str, float | None]) -> dict[str, float | None]:
    """``IC_observed / IC_injected`` at each checkpoint.

    Undefined at ``theta = 0`` — division by zero is a null, never an infinity
    and never a silently substituted value.
    """
    theta = checkpoints.get("ic_injected")
    ratios: dict[str, float | None] = {}
    for name, _ in CHECKPOINTS:
        if name == "ic_injected":
            continue
        observed = checkpoints.get(name)
        if theta in (None, 0.0) or observed is None:
            ratios[name] = None
        else:
            ratios[name] = _rounded(float(observed) / float(theta))
    return ratios


def stagewise_ratios(checkpoints: dict[str, float | None]) -> dict[str, float | None]:
    """``IC_stage / IC_previous_stage`` — where each stage's loss actually happens."""
    names = [name for name, _ in CHECKPOINTS]
    ratios: dict[str, float | None] = {}
    for previous, current in zip(names, names[1:]):
        before, after = checkpoints.get(previous), checkpoints.get(current)
        if before in (None, 0.0) or after is None:
            ratios[f"{previous}__to__{current}"] = None
        else:
            ratios[f"{previous}__to__{current}"] = _rounded(float(after) / float(before))
    return ratios


# --------------------------------------------------------------------------- #
# Arms
# --------------------------------------------------------------------------- #
def _summarize(values: list[float | None]) -> dict[str, float | None]:
    clean = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    if not clean:
        return {"n": 0, "mean": None, "sd": None, "p05": None, "p50": None, "p95": None}
    array = np.asarray(clean, dtype=float)
    return {
        "n": len(clean),
        "mean": _rounded(float(array.mean())),
        "sd": _rounded(float(array.std(ddof=1))) if len(clean) > 1 else None,
        "p05": _rounded(float(np.quantile(array, 0.05))),
        "p50": _rounded(float(np.quantile(array, 0.50))),
        "p95": _rounded(float(np.quantile(array, 0.95))),
    }


def _summarize_counts(values: list[int | None]) -> dict[str, object]:
    """Summarize checkpoint row counts without treating missing as zero."""
    clean = [int(v) for v in values if v is not None]
    if not clean:
        return {"n": 0, "unique": [], "min": None, "max": None, "all_equal": False}
    unique = sorted(set(clean))
    return {
        "n": len(clean),
        "unique": unique,
        "min": min(clean),
        "max": max(clean),
        "all_equal": len(unique) == 1,
    }


def _count_value(summary: dict[str, object]) -> int | list[int] | None:
    """Use a scalar for stable counts and retain all values when they vary."""
    unique = summary["unique"]
    if not isinstance(unique, list) or not unique:
        return None
    return unique[0] if len(unique) == 1 else unique


def _wilson_interval(successes: int, trials: int, alpha: float = 0.05) -> list[float | None]:
    """Wilson interval conditional on the fixed realized panel.

    The interval captures only the repetition-to-repetition variation over the
    declared repetitions: across repetitions the synthetic injection draw
    changes and the permutation-test RNG changes, so the variation carries
    injection-draw randomness plus permutation Monte-Carlo randomness. It does
    not include resampling uncertainty from drawing a different equity panel or
    a different time sample.
    """
    if trials <= 0:
        return [None, None]
    z = sig._STANDARD_NORMAL.inv_cdf(1.0 - alpha / 2.0)
    phat = successes / trials
    denominator = 1.0 + z * z / trials
    centre = (phat + z * z / (2 * trials)) / denominator
    margin = z * math.sqrt(phat * (1 - phat) / trials + z * z / (4 * trials * trials)) / denominator
    return [_rounded(max(0.0, centre - margin)), _rounded(min(1.0, centre + margin))]


def run_arm(
    raw: pd.DataFrame,
    *,
    arm: str,
    carrier: str,
    levels: tuple[float, ...],
    repetitions: int,
    base_seed: int,
    permutations: int = PERMUTATIONS,
    bootstraps: int = BOOTSTRAPS,
    progress: bool = False,
) -> list[dict]:
    """Run every ``(level, repetition)`` cell of one arm and return flat records."""
    records: list[dict] = []
    for level_index, theta in enumerate(levels):
        for repetition in range(repetitions):
            record = run_repetition(
                raw,
                carrier,
                theta,
                injection_seed=derive_injection_seed(base_seed, level_index, repetition),
                permutation_seed=derive_permutation_seed(base_seed, repetition),
                permutations=permutations,
                bootstraps=bootstraps,
            )
            record.update({"arm": arm, "level_index": level_index, "repetition": repetition})
            records.append(record)
        if progress:
            print(
                f"[positive-control] {arm} carrier={carrier} theta={theta:.2f} "
                f"reps={repetitions} done",
                flush=True,
            )
    return records


def aggregate_level(records: list[dict]) -> dict:
    """Collapse one arm/level cell into its curve point.

    ``detection_rate`` is the empirical fraction of repetitions whose
    Bonferroni-adjusted permutation p falls below alpha. It is a measured
    rejection frequency over the declared repetitions, not an analytic power.
    """
    if not records:
        raise PositiveControlError("cannot aggregate an empty level")
    thetas = {record["ic_injected"] for record in records}
    if len(thetas) != 1:
        raise PositiveControlError(f"level records disagree on ic_injected: {sorted(thetas)}")
    theta = float(next(iter(thetas)))
    detections = sum(1 for record in records if record["detected"])
    trials = len(records)

    summary = {
        "arm": records[0]["arm"],
        "carrier": records[0]["carrier"],
        "ic_injected": _rounded(theta),
        "repetitions": trials,
        "detections": detections,
        "detection_rate": _rounded(detections / trials),
        "detection_rate_ci_95": _wilson_interval(detections, trials),
        "checkpoint_summary": {
            name: _summarize([record["checkpoints"][name] for record in records])
            for name, _ in CHECKPOINTS
        },
        "checkpoint_n_summary": {
            name: _summarize_counts([record["checkpoint_n"][name] for record in records])
            for name, _ in CHECKPOINTS
        },
        "ratio_to_injected_summary": {
            name: (
                None
                if CHECKPOINT_ROLES[name] == "identity_invariant"
                else _summarize([record["attenuation_ratio"][name] for record in records])
            )
            for name, _ in CHECKPOINTS
            if name != "ic_injected"
        },
        "attenuation_suppression_reason": {
            name: (
                IDENTITY_INVARIANT_SUPPRESSION_REASON
                if CHECKPOINT_ROLES[name] == "identity_invariant"
                else None
            )
            for name, _ in CHECKPOINTS
        },
        "permutation_p_summary": _summarize(
            [record["permutation_p_value_two_sided"] for record in records]
        ),
    }
    recovered = summary["checkpoint_summary"]["ic_final_evaluation"]["mean"]
    summary["recovery_bias"] = (
        None if recovered is None else _rounded(float(recovered) - theta)
    )
    return summary


def analytic_comparison(level_summaries: list[dict], *, n_per_split: int, split_count: int) -> list[dict]:
    """Compare each level's measured detection rate against the governed power machinery.

    Two analytic references are reported as diagnostics, because they answer
    different questions:

    * ``analytic_power_at_injected`` assumes the model's IC equals the injected
      IC — i.e. that the pipeline loses nothing. It is a naive scale reference.
    * ``analytic_power_at_recovered`` evaluates the same governed function at
      the IC the pipeline actually produced. It is a recovered-scale reference,
      not a test-only residual attribution.

    The empirical repetitions hold the realized equity panel fixed. Across
    repetitions the synthetic injection changes and the permutation-test RNG
    changes, so the empirical detection-rate variation carries injection-draw
    randomness plus permutation Monte-Carlo randomness. It still does not carry
    resampling uncertainty from drawing another market panel or time sample.
    Fisher-z analytic/simulation power instead integrates over cross-sectional
    sampling variability. The curves therefore condition on different
    randomness; their residual difference cannot be attributed simply to the
    test, and they are not interchangeable power estimates.

    Both use ``alpha = 0.05 / 5``, the Bonferroni-adjusted per-test level that
    the empirical detection rule applies.
    """
    bonferroni_alpha = ALPHA / CONFIRMATORY_FAMILY_SIZE
    rows = []
    for summary in level_summaries:
        theta = float(summary["ic_injected"])
        recovered = summary["checkpoint_summary"]["ic_final_evaluation"]["mean"]
        row = {
            "arm": summary["arm"],
            "ic_injected": _rounded(theta),
            "empirical_detection_rate": summary["detection_rate"],
            "empirical_detection_rate_ci_95": summary["detection_rate_ci_95"],
            "mean_recovered_ic": recovered,
            "analytic_power_at_injected": None,
            "analytic_power_at_recovered": None,
            "simulated_power_at_recovered": None,
        }
        if theta > 0.0:
            row["analytic_power_at_injected"] = _rounded(
                sig.fisher_power(
                    theta, n_per_split=n_per_split, split_count=split_count,
                    alpha=bonferroni_alpha,
                )
            )
        if recovered is not None and 0.0 < abs(float(recovered)) < 1.0:
            row["analytic_power_at_recovered"] = _rounded(
                sig.fisher_power(
                    float(recovered), n_per_split=n_per_split, split_count=split_count,
                    alpha=bonferroni_alpha,
                )
            )
            row["simulated_power_at_recovered"] = _rounded(
                sig.simulate_fisher_power(
                    float(recovered), n_per_split=n_per_split, split_count=split_count,
                    simulations=sig.DEFAULT_POWER_SIMULATIONS, seed=sig.DEFAULT_SEED,
                    alpha=bonferroni_alpha,
                )
            )
        rows.append(row)
    return rows


def detection_threshold(level_summaries: list[dict], *, target: float = 0.80) -> dict:
    """Lowest **preregistered grid level** reaching ``target`` detection.

    No interpolation and no added level: the protocol fixes the grid, so the
    answer is one of its five points or "not reached on this grid". Reporting a
    fitted crossing between grid points would be inventing a level after seeing
    results, which the protocol forbids.

    An arm that does not cover exactly the preregistered grid — the strong-signal
    sanity control is the one such arm — gets no threshold at all. Reading a
    threshold off an off-grid level is precisely the post-hoc level addition the
    protocol rules out.
    """
    ordered = sorted(level_summaries, key=lambda item: float(item["ic_injected"]))
    if [_rounded(float(item["ic_injected"])) for item in ordered] != [
        _rounded(level) for level in sorted(IC_GRID)
    ]:
        return {
            "target_detection_rate": target,
            "reached": None,
            "lowest_grid_level_reaching_target": None,
            "observed_detection_rate": None,
            "observed_detection_rate_ci_95": None,
            "interpolated": False,
            "note": (
                "Not applicable: this arm does not cover the preregistered grid, so no "
                "detection threshold may be read from it."
            ),
        }
    for summary in ordered:
        rate = summary["detection_rate"]
        if rate is not None and float(rate) >= target:
            return {
                "target_detection_rate": target,
                "reached": True,
                "lowest_grid_level_reaching_target": _rounded(float(summary["ic_injected"])),
                "observed_detection_rate": rate,
                "observed_detection_rate_ci_95": summary["detection_rate_ci_95"],
                "interpolated": False,
                "note": (
                    "Read off the preregistered grid only. The true crossing lies somewhere "
                    "at or below this level; this design cannot localize it further without "
                    "adding levels, which the protocol forbids."
                ),
            }
    return {
        "target_detection_rate": target,
        "reached": False,
        "lowest_grid_level_reaching_target": None,
        "observed_detection_rate": None,
        "observed_detection_rate_ci_95": None,
        "interpolated": False,
        "note": "No preregistered grid level reached the target detection rate.",
    }


def confirmatory_gate(records: list[dict]) -> dict:
    """Apply the Stage 1 pass rule to the confirmatory arm, exactly as written.

    Pass requires recovered IC to increase monotonically across the five levels
    **and** both levels above ``MDE_base`` to reject at FWER 0.05. This function
    reads the rule; it does not negotiate with it.
    """
    confirmatory = [r for r in records if r.get("repetition") == CONFIRMATORY_REPETITION]
    try:
        confirmatory = sorted(confirmatory, key=lambda r: float(r["ic_injected"]))
        levels = [float(r["ic_injected"]) for r in confirmatory]
    except (KeyError, TypeError, ValueError) as exc:
        raise PositiveControlError(
            "confirmatory arm must contain numeric injection levels on the preregistered grid"
        ) from exc
    if levels != sorted(IC_GRID):
        raise PositiveControlError(
            f"confirmatory arm must cover exactly the preregistered grid; got {levels}"
        )
    raw_recovered = []
    for record in confirmatory:
        checkpoints = record.get("checkpoints")
        raw_recovered.append(
            checkpoints.get("ic_final_evaluation")
            if isinstance(checkpoints, dict)
            else None
        )
    try:
        recovered = [float(value) for value in raw_recovered]
    except (TypeError, ValueError) as exc:
        raise PositiveControlError(
            "confirmatory checkpoint IC must be finite and strictly inside (-1, 1)"
        ) from exc
    if any(not math.isfinite(value) or not -1.0 < value < 1.0 for value in recovered):
        raise PositiveControlError(
            "confirmatory checkpoint IC must be finite and strictly inside (-1, 1)"
        )
    monotone = all(b > a for a, b in zip(recovered, recovered[1:]))
    gate_rows = [r for r in confirmatory if float(r["ic_injected"]) in GATE_LEVELS]
    gate_rejects = {
        _rounded(float(r["ic_injected"])): bool(r["detected"]) for r in gate_rows
    }
    all_gate_reject = all(gate_rejects.values()) and len(gate_rejects) == len(GATE_LEVELS)
    return {
        "family_size": CONFIRMATORY_FAMILY_SIZE,
        "multiplicity": "Bonferroni across the 5 preregistered injection levels",
        "alpha_family_wise": ALPHA,
        "levels": [_rounded(v) for v in levels],
        "recovered_ic": [_rounded(v) for v in recovered],
        "adjusted_p_values": [r["bonferroni_adjusted_p_value"] for r in confirmatory],
        "monotone_increasing": bool(monotone),
        "gate_levels": [_rounded(v) for v in GATE_LEVELS],
        "gate_level_rejects": gate_rejects,
        "gate_levels_all_reject": bool(all_gate_reject),
        "passed": bool(monotone and all_gate_reject),
        "rule": (
            "Stage 1 pass requires recovered IC strictly increasing across the five "
            "preregistered levels AND both levels above MDE_base rejecting at FWER 0.05."
        ),
    }


def gate_informativeness(records: list[dict]) -> dict:
    """Measure the original gate on coherent five-level descriptive draws.

    Each repetition contributes one five-level draw. This is a post-run
    diagnostic of how informative the gate is on the fixed panel; it cannot
    alter the confirmatory gate or the Stage 1 classification.
    """
    by_repetition: dict[int, list[dict]] = {}
    for record in records:
        by_repetition.setdefault(int(record["repetition"]), []).append(record)
    if not by_repetition:
        raise PositiveControlError("gate informativeness requires descriptive repetitions")

    expected_levels = [_rounded(level) for level in sorted(IC_GRID)]
    draws: list[dict[str, bool]] = []
    for repetition, draw in sorted(by_repetition.items()):
        ordered = sorted(draw, key=lambda r: float(r["ic_injected"]))
        levels = [_rounded(float(r["ic_injected"])) for r in ordered]
        if levels != expected_levels:
            raise PositiveControlError(
                "gate informativeness requires one coherent record for every preregistered "
                f"level in repetition {repetition}; got {levels}"
            )
        try:
            recovered = [
                float(r["checkpoints"]["ic_final_evaluation"])
                for r in ordered
                if isinstance(r.get("checkpoints"), dict)
            ]
        except (KeyError, TypeError, ValueError) as exc:
            raise PositiveControlError(
                "gate informativeness requires finite recovered IC at every grid level"
            ) from exc
        if len(recovered) != len(expected_levels) or any(
            not math.isfinite(value) for value in recovered
        ):
            raise PositiveControlError(
                "gate informativeness requires finite recovered IC at every grid level"
            )
        monotone = all(b > a for a, b in zip(recovered, recovered[1:]))
        high_grid = [
            r for r in ordered if _rounded(float(r["ic_injected"])) in GATE_LEVELS
        ]
        if len(high_grid) != len(GATE_LEVELS):
            raise PositiveControlError(
                f"gate informativeness could not identify both required high-grid levels in repetition {repetition}"
            )
        high_grid_reject = all(bool(r["detected"]) for r in high_grid)
        draws.append(
            {
                "strictly_monotone_recovered_ic": monotone,
                "both_required_high_grid_levels_reject": high_grid_reject,
                "original_stage_1_gate_passes": monotone and high_grid_reject,
            }
        )

    trials = len(draws)
    counts = {
        name: sum(1 for draw in draws if draw[name])
        for name in draws[0]
    }
    return {
        "status": "POST_RUN_DIAGNOSTIC",
        "repetitions": trials,
        "coherent_draw_definition": (
            "one existing primary descriptive repetition across all five preregistered levels"
        ),
        "counts": counts,
        "probabilities": {
            name: _rounded(count / trials) for name, count in counts.items()
        },
        "note": (
            "Descriptive only. These probabilities do not alter the original gate, its "
            "thresholds, or the Stage 1 status."
        ),
    }
# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def _flatten_record(record: dict) -> dict:
    flat = {
        "arm": record["arm"],
        "carrier": record["carrier"],
        "ic_injected": record["ic_injected"],
        "repetition": record["repetition"],
        "injection_seed": record["injection_seed"],
        "permutation_seed": record["permutation_seed"],
        "injected_dataset_sha256": record["injected_dataset_sha256"],
        "permutation_p_value_two_sided": record["permutation_p_value_two_sided"],
        "bonferroni_adjusted_p_value": record["bonferroni_adjusted_p_value"],
        "detected": record["detected"],
    }
    for name, _ in CHECKPOINTS:
        flat[name] = record["checkpoints"][name]
        flat[f"n_{name}"] = record["checkpoint_n"][name]
        if name != "ic_injected":
            flat[f"ratio_to_injected_{name}"] = record["attenuation_ratio"][name]
    return flat


def build_report(
    *,
    arms: dict[str, list[dict]],
    carriers: dict[str, str],
    raw_path: Path,
    base_seed: int,
    started_at: str,
    duration_seconds: float,
    n_per_split: int,
    split_count: int,
) -> dict:
    primary = arms["primary"]
    level_summaries = {
        arm: [
            aggregate_level([r for r in records if r["level_index"] == index])
            for index in sorted({r["level_index"] for r in records})
        ]
        for arm, records in arms.items()
    }
    gate = confirmatory_gate(primary)
    gate_diagnostic = gate_informativeness(primary)
    primary_zero = [s for s in level_summaries["primary"] if float(s["ic_injected"]) == 0.0]
    background = (
        primary_zero[0]["checkpoint_summary"]["ic_final_evaluation"]["mean"]
        if primary_zero
        else None
    )

    for arm, summaries in level_summaries.items():
        # The background is the arm's own theta = 0 rung. An arm without one --
        # the sanity control -- gets no background adjustment rather than a
        # self-referential zero.
        zero_rungs = [s for s in summaries if float(s["ic_injected"]) == 0.0]
        background_by_checkpoint = {
            name: (
                zero_rungs[0]["checkpoint_summary"][name]["mean"]
                if zero_rungs
                else None
            )
            for name, _ in CHECKPOINTS
        }
        for summary in summaries:
            theta = float(summary["ic_injected"])
            summary["background_ic"] = {
                name: _rounded(value) for name, value in background_by_checkpoint.items()
            }
            summary["background_dominated"] = {}
            summary["background_adjusted_ic_heuristic"] = {}
            summary["background_adjusted_ratio_heuristic"] = {}
            for name, _ in CHECKPOINTS:
                observed = summary["checkpoint_summary"][name]["mean"]
                background_ic = background_by_checkpoint[name]
                non_transition_role = CHECKPOINT_ROLES.get(name) in (
                    "identity_invariant",
                    "design_constant",
                )
                if CHECKPOINT_ROLES.get(name) == "identity_invariant":
                    summary["background_dominated"][name] = None
                    summary["background_adjusted_ic_heuristic"][name] = None
                    summary["background_adjusted_ratio_heuristic"][name] = None
                    continue
                if theta <= 0.0 or observed is None or background_ic is None:
                    summary["background_dominated"][name] = None
                    summary["background_adjusted_ic_heuristic"][name] = None
                    summary["background_adjusted_ratio_heuristic"][name] = None
                    continue
                adjusted = float(observed) - float(background_ic)
                dominated = abs(float(background_ic)) >= BACKGROUND_DOMINANCE_FRACTION * abs(theta)
                summary["background_dominated"][name] = bool(dominated)
                summary["background_adjusted_ic_heuristic"][name] = _rounded(adjusted)
                # Identity/invariant checkpoints (and the injected design constant)
                # recover theta by construction, so a background-adjusted ratio there
                # sits near 1.0 and reads as a measured attenuation coefficient when it
                # is nothing of the kind. Suppress it, exactly as the plain attenuation
                # ratio is already suppressed for these rows.
                summary["background_adjusted_ratio_heuristic"][name] = (
                    None
                    if dominated or non_transition_role
                    else _rounded(adjusted / theta)
                )
            summary["background_adjusted_recovered_ic_heuristic"] = summary[
                "background_adjusted_ic_heuristic"
            ]["ic_final_evaluation"]

    secondary_population = None
    if "secondary" in level_summaries:
        secondary_zero = [
            s for s in level_summaries["secondary"] if float(s["ic_injected"]) == 0.0
        ]
        if secondary_zero:
            zero = secondary_zero[0]
            observed_n = _count_value(zero["checkpoint_n_summary"]["ic_raw_carrier"])
            imputed_n = _count_value(
                zero["checkpoint_n_summary"]["ic_model_input_carrier"]
            )
            secondary_population = {
                "observed_carrier_checkpoint": {
                    "checkpoint": "ic_raw_carrier",
                    "n": observed_n,
                },
                "post_imputation_full_cross_section_checkpoint": {
                    "checkpoint": "ic_model_input_carrier",
                    "n": imputed_n,
                },
                "n_differs": observed_n != imputed_n,
                "interpretation": (
                    "The secondary stagewise ratio mixes missingness/imputation dilution with "
                    "a changed evaluation population; it is not a pure attenuation coefficient."
                ),
            }

    return {
        "schema_version": 4,
        "experiment": SLUG,
        "stage": "Stage 1 — raw-layer positive control / synthetic signal injection",
        "protocol": "docs/thesis/PRE_EXPERIMENT_PROTOCOL.md",
        "claim_safety": {
            "descriptive_research_evidence_only": True,
            "reliable_predictive_edge_established": False,
            "investment_value_established": False,
            "apparatus_validation_only": True,
            "statement": CLAIM_SAFETY_SENTENCE,
        },
        "provenance": {
            "git": _git_metadata(),
            "seed": base_seed,
            "implementation_sha256": implementation_hash(),
            "significance_module_sha256": _sha256_path(ROOT / "experiments" / "significance.py"),
            "pipeline_module_sha256": _sha256_path(ROOT / "experiments" / "run_experiments.py"),
            "source_dataset": {
                "path": raw_path.relative_to(ROOT).as_posix(),
                "sha256": _sha256_path(raw_path),
                "size_bytes": raw_path.stat().st_size,
            },
            "python": platform.python_version(),
            "platform": platform.platform(),
            "started_at_utc": started_at,
            "duration_seconds": _rounded(duration_seconds, 3),
        },
        "design": {
            "injection_site": (
                "one raw feature column of the modeling CSV, in its own units, before "
                "run_experiments.build_panel() performs feature construction"
            ),
            "mechanism": (
                "within-year permutation of the carrier's own observed values into the order "
                "of a Gaussian-copula latent score s = rho*z + sqrt(1-rho^2)*eps, where z is "
                "the unit-scaled normal score of the future-return ranking and "
                "rho = 2*sin(pi*theta/6)"
            ),
            "preserved_exactly": [
                "carrier within-year marginal distribution (permutation of its own values)",
                "carrier missingness pattern (null stays null; nothing imputed)",
                "target column and every non-carrier column, bit-identical",
                "year structure, ticker structure, row count",
            ],
            "not_preserved": [
                "the carrier's correlations with the other 39 features, which the permutation "
                "destroys; the theta=0 rung carries identical damage and is therefore the "
                "correct background for comparison"
            ],
            "ic_grid": list(IC_GRID),
            "mde_base": MDE_BASE,
            "gate_levels": list(GATE_LEVELS),
            "model": PRIMARY_MODEL,
            "confirmatory_family_size": CONFIRMATORY_FAMILY_SIZE,
            "multiplicity": "Bonferroni across the 5 preregistered levels",
            "descriptive_repetitions": DESCRIPTIVE_REPETITIONS,
            "permutations": PERMUTATIONS,
            "bootstraps": BOOTSTRAPS,
            "alpha_family_wise": ALPHA,
            "carriers": carriers,
            "carrier_rules": {
                "primary": PRIMARY_CARRIER_RULE,
                "secondary": SECONDARY_CARRIER_RULE,
            },
            "n_per_split": n_per_split,
            "split_count": split_count,
            "seed_formulas": {
                "injection": "base_seed*1000003 + level_index*10007 + repetition",
                "permutation": "significance.DEFAULT_SEED + repetition (repetition 0 = governed default)",
            },
        },
        "checkpoint_definitions": {name: description for name, description in CHECKPOINTS},
        "checkpoint_roles": CHECKPOINT_ROLES,
        "confirmatory": gate,
        "gate_informativeness": gate_diagnostic,
        "detection_curve": {arm: summaries for arm, summaries in level_summaries.items()},
        "detection_threshold": {
            arm: detection_threshold(summaries) for arm, summaries in level_summaries.items()
        },
        "analytic_vs_empirical_power": {
            arm: analytic_comparison(summaries, n_per_split=n_per_split, split_count=split_count)
            for arm, summaries in level_summaries.items()
        },
        "background_ic_theta_zero": background,
        "secondary_population": secondary_population,
        "limitations": [
            "Signal is injected into one carrier column; the recovered IC therefore reflects "
            "the pipeline's ability to isolate one informative feature among 40, not its "
            "ability to aggregate signal spread across many.",
            "The injection permutes the carrier's values within each year, which destroys that "
            "column's joint structure with the other features. The theta=0 rung shares the "
            "damage, so comparisons along the curve are internally consistent, but the absolute "
            "recovered IC is not the IC an equally strong naturally-occurring feature would give.",
            "The theta=0 rung is not a zero-IC world: the other 39 features retain whatever weak "
            "real structure they carry, so recovered IC at theta=0 estimates that background "
            "rather than zero.",
            "Only three test cross-sections of about 80 rows exist. Detection rates are measured "
            "over 200 repetitions and carry binomial uncertainty of roughly +/-3 percentage points.",
            "The detection threshold is read off five preregistered grid points. The true "
            "crossing is not localized, and no interpolated value is reported.",
            "Each Wilson detection-rate interval is conditional on the one fixed realized panel. "
            "It captures only the repetition-to-repetition variation over the declared repetitions "
            "-- across repetitions the synthetic injection draw changes and the permutation-test "
            "RNG changes, so it carries injection-draw randomness plus permutation Monte-Carlo "
            "randomness -- and excludes resampling uncertainty from drawing a different equity "
            "panel or time sample.",
            "The realized equity panel is fixed across repetitions. The synthetic injection "
            "changes across repetitions and the permutation-test RNG also changes across "
            "repetitions, so the empirical detection-rate variation includes injection-draw "
            "randomness plus permutation Monte-Carlo randomness; it still does not include "
            "resampling uncertainty from drawing another market panel or time sample. Fisher-z "
            "analytic/simulation power instead integrates over cross-sectional sampling "
            "variability, so the two curves condition on different randomness; their residual "
            "difference cannot be attributed simply to the test, and the curves are diagnostic "
            "rather than interchangeable power estimates.",
            "The raw, feature-construction, and model-input/imputation checkpoints for the primary "
            "100%-coverage carrier are identity/invariant checks, not empirical claims of no "
            "attenuation. The substantive measured transition is carrier signal to fitted model "
            "prediction.",
            "The secondary carrier changes row population: its observed-carrier checkpoint n "
            "differs from the post-imputation full-cross-section n. Its stagewise ratio therefore "
            "mixes missingness/imputation dilution with changed evaluation population and is not "
            "a pure attenuation coefficient.",
            "Any background-adjusted ratio is a heuristic descriptive diagnostic, not a mathematically "
            "exact decomposition of Spearman IC. The ratio is emitted as NA for identity/invariant "
            "checkpoints and the injected design constant -- where it would sit near 1.0 by "
            "construction and could be misread as a measured attenuation coefficient -- and for "
            "levels where the theta=0 background dominates.",
            "The temporary run_experiments.TRAINING_MODELING override is process-global and this "
            "experiment is single-threaded; concurrent execution is outside this task's scope.",
            "Results describe this pipeline on this panel with this carrier. They do not "
            "generalize to other designs, frequencies, universes, or feature sets, and they "
            "establish nothing about BIST returns or investment value.",
        ],
    }


def render_markdown(report: dict) -> str:
    design = report["design"]
    gate = report["confirmatory"]
    lines: list[str] = [
        "# Stage 1 — raw-layer positive control",
        "",
        report["claim_safety"]["statement"],
        "",
        f"Protocol: `{report['protocol']}` · git `{report['provenance']['git']['short_sha']}` · "
        f"seed {report['provenance']['seed']} · implementation "
        f"`{report['provenance']['implementation_sha256'][:12]}`",
        "",
        "## Design",
        "",
        f"- Injection site: {design['injection_site']}",
        f"- Mechanism: {design['mechanism']}",
        f"- Preregistered grid: {design['ic_grid']} (MDE_base {design['mde_base']})",
        f"- Model: `{design['model']}` · family {design['confirmatory_family_size']} · "
        f"{design['multiplicity']}",
        f"- Carriers: primary `{design['carriers']['primary']}`, "
        f"secondary `{design['carriers']['secondary']}`",
        f"- Repetitions per descriptive level: {design['descriptive_repetitions']} · "
        f"permutations {design['permutations']}",
        "",
        "## Confirmatory arm (the preregistered Stage 1 test)",
        "",
        f"- Recovered IC by level: {gate['recovered_ic']}",
        f"- Adjusted p by level: {gate['adjusted_p_values']}",
        f"- Monotone increasing: **{gate['monotone_increasing']}**",
        f"- Both gate levels reject: **{gate['gate_levels_all_reject']}**",
        f"- Stage 1 gate: **{'PASSED' if gate['passed'] else 'NOT PASSED'}**",
        "",
        "## Gate informativeness diagnostic (POST-RUN)",
        "",
        (
            "Using the existing primary descriptive repetitions as coherent five-level draws "
            f"({report['gate_informativeness']['repetitions']} draws): "
            f"P(strictly monotone recovered IC) = "
            f"{report['gate_informativeness']['probabilities']['strictly_monotone_recovered_ic']}; "
            f"P(both required high-grid levels reject) = "
            f"{report['gate_informativeness']['probabilities']['both_required_high_grid_levels_reject']}; "
            f"P(original Stage 1 gate passes) = "
            f"{report['gate_informativeness']['probabilities']['original_stage_1_gate_passes']}."
        ),
        "This is a descriptive post-run diagnostic of gate informativeness. It does not alter the "
        "gate, its thresholds, or the Stage 1 status.",
        "",
        "## Detection curve — primary carrier",
        "",
        "| injected IC | detections / reps | detection rate | 95% CI | mean recovered IC | "
        "recovery bias |",
        "|---|---|---|---|---|---|",
    ]
    for summary in report["detection_curve"]["primary"]:
        recovered = summary["checkpoint_summary"]["ic_final_evaluation"]["mean"]
        ci = summary["detection_rate_ci_95"]
        lines.append(
            f"| {summary['ic_injected']:.2f} | {summary['detections']}/{summary['repetitions']} | "
            f"{summary['detection_rate']:.3f} | [{ci[0]:.3f}, {ci[1]:.3f}] | "
            f"{recovered:.4f} | {summary['recovery_bias']:+.4f} |"
        )

    threshold = report["detection_threshold"]["primary"]
    lines += [
        "",
        "### >=80% detection on the preregistered grid",
        "",
        (
            f"Lowest grid level reaching 80% detection: **{threshold['lowest_grid_level_reaching_target']}** "
            f"(observed {threshold['observed_detection_rate']})."
            if threshold["reached"]
            else "**No preregistered grid level reached 80% detection.**"
        ),
        "",
        threshold["note"],
        "",
        "## Attenuation by stage — primary carrier",
        "",
        "Raw IC values are shown at every checkpoint. The raw, feature-construction, and "
        "model-input/imputation rows are identity/invariant checkpoints; only the carrier-signal "
        "to fitted-prediction transition is a substantive attenuation measurement.",
        "",
        "| injected IC | " + " | ".join(
            f"{name} ({CHECKPOINT_ROLES[name]})" for name, _ in CHECKPOINTS
        ) + " |",
        "|---" * (len(CHECKPOINTS) + 1) + "|",
    ]
    for summary in report["detection_curve"]["primary"]:
        cells = []
        for name, _ in CHECKPOINTS:
            mean = summary["checkpoint_summary"][name]["mean"]
            cells.append("n/a" if mean is None else f"{mean:.4f}")
        lines.append(f"| {summary['ic_injected']:.2f} | " + " | ".join(cells) + " |")

    lines += [
        "",
        "### Background-adjusted diagnostic (heuristic only)",
        "",
        "The background-adjusted quantity is `(recovered IC - theta=0 background IC) / "
        "injected IC`. It is a heuristic descriptive diagnostic, not a mathematically exact "
        "decomposition of Spearman IC. The ratio is emitted as NA for identity/invariant "
        "checkpoints and the injected design constant (where it sits near 1.0 by construction "
        "and is not a measured coefficient) and where the theta=0 background dominates; the "
        "full per-checkpoint columns and the suppression reason are in "
        "`attenuation_by_stage.csv`.",
        "",
        "| injected IC | final theta=0 background IC | heuristic adjusted final IC | heuristic ratio |",
        "|---|---|---|---|",
    ]
    for summary in report["detection_curve"]["primary"]:
        lines.append(
            f"| {summary['ic_injected']:.2f} | "
            f"{summary['background_ic']['ic_final_evaluation']} | "
            f"{summary['background_adjusted_recovered_ic_heuristic']} | "
            f"{summary['background_adjusted_ratio_heuristic']['ic_final_evaluation']} |"
        )

    lines += [
        "",
        "## Analytic vs empirical power — primary carrier",
        "",
        "Analytic references come from `experiments/significance.py`, called unchanged, at the "
        "Bonferroni-adjusted per-test alpha. The empirical repetitions hold the realized equity "
        "panel fixed; across repetitions the synthetic injection changes and the permutation-test "
        "RNG changes, so the empirical detection-rate variation carries injection-draw randomness "
        "plus permutation Monte-Carlo randomness, but not resampling uncertainty from another "
        "market panel or time sample. Fisher-z analytic/simulation power instead integrates over "
        "cross-sectional sampling variability. The curves therefore condition on different "
        "randomness, so their residual difference cannot be attributed simply to the test. They "
        "are useful diagnostics but are not interchangeable power estimates.",
        "",
        "| injected IC | empirical detection | analytic power at injected IC | "
        "analytic power at recovered IC | simulated power at recovered IC |",
        "|---|---|---|---|---|",
    ]
    for row in report["analytic_vs_empirical_power"]["primary"]:
        lines.append(
            f"| {row['ic_injected']:.2f} | {row['empirical_detection_rate']} | "
            f"{row['analytic_power_at_injected']} | {row['analytic_power_at_recovered']} | "
            f"{row['simulated_power_at_recovered']} |"
        )

    lines += [
        "",
        "## Secondary descriptive carrier (missingness channel)",
        "",
        f"Carrier `{design['carriers']['secondary']}` carries the same injection at roughly half "
        "coverage. It makes no confirmatory claim; it exists to isolate how much signal the "
        "NaN -> 0.5 rank imputation removes.",
        "",
        (
            "Its observed-carrier checkpoint n = "
            f"{report['secondary_population']['observed_carrier_checkpoint']['n']} differs from "
            "the post-imputation full-cross-section checkpoint n = "
            f"{report['secondary_population']['post_imputation_full_cross_section_checkpoint']['n']}. "
            "The secondary stagewise ratio therefore mixes missingness/imputation dilution with a "
            "changed evaluation population; it is not a pure attenuation coefficient."
        ) if report.get("secondary_population") else "Secondary population counts were unavailable.",
        "",
        "| injected IC | raw carrier IC (n) | after imputation (n) | recovered IC | detection rate |",
        "|---|---|---|---|---|",
    ]
    for summary in report["detection_curve"].get("secondary", []):
        cs = summary["checkpoint_summary"]
        raw_n = _count_value(summary["checkpoint_n_summary"]["ic_raw_carrier"])
        input_n = _count_value(
            summary["checkpoint_n_summary"]["ic_model_input_carrier"]
        )
        lines.append(
            f"| {summary['ic_injected']:.2f} | {cs['ic_raw_carrier']['mean']} ({raw_n}) | "
            f"{cs['ic_model_input_carrier']['mean']} ({input_n}) | "
            f"{cs['ic_final_evaluation']['mean']} | "
            f"{summary['detection_rate']} |"
        )

    if "sanity" in report["detection_curve"]:
        sanity = report["detection_curve"]["sanity"][0]
        lines += [
            "",
            "## Strong-signal sanity control",
            "",
            f"Outside the preregistered grid and excluded from the power curve. At injected IC "
            f"{sanity['ic_injected']:.2f} the pipeline recovers "
            f"{sanity['checkpoint_summary']['ic_final_evaluation']['mean']} with detection rate "
            f"{sanity['detection_rate']}.",
        ]

    lines += ["", "## Limitations", ""]
    lines += [f"- {item}" for item in report["limitations"]]
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def run(
    *,
    repetitions: int = DESCRIPTIVE_REPETITIONS,
    permutations: int = PERMUTATIONS,
    bootstraps: int = BOOTSTRAPS,
    include_secondary: bool = True,
    include_sanity: bool = True,
    progress: bool = True,
) -> Path:
    started = datetime.now(timezone.utc)
    clock = time.perf_counter()
    base_seed = prov.seed_for(SLUG)
    output = prov.output_dir(SLUG)

    raw_path = rx.TRAINING_MODELING
    if not raw_path.is_file():
        raise PositiveControlError(f"modeling dataset not found: {raw_path}")
    raw_sha_before = _sha256_path(raw_path)
    raw = pd.read_csv(raw_path)
    carriers = select_carriers(raw)

    reference_panel = rx.build_panel()
    test_years = sorted(split["test_feature_year"] for split in rx.SPLITS)
    per_split = sorted(
        int(count)
        for count in reference_panel[reference_panel["feature_year"].isin(test_years)]
        .groupby("feature_year")
        .size()
        .unique()
    )
    if len(per_split) != 1:
        raise PositiveControlError(
            "Fisher-z analytic comparison is undefined for unequal test cross-section sizes; "
            f"this fixed-panel stage requires one common test-split size, got {per_split}"
        )
    n_per_split, split_count = per_split[0], len(rx.SPLITS)

    arms: dict[str, list[dict]] = {
        "primary": run_arm(
            raw, arm="primary", carrier=carriers["primary"], levels=IC_GRID,
            repetitions=repetitions, base_seed=base_seed, permutations=permutations,
            bootstraps=bootstraps, progress=progress,
        )
    }
    if include_secondary:
        arms["secondary"] = run_arm(
            raw, arm="secondary", carrier=carriers["secondary"], levels=IC_GRID,
            repetitions=repetitions, base_seed=base_seed + 1, permutations=permutations,
            bootstraps=bootstraps, progress=progress,
        )
    if include_sanity:
        arms["sanity"] = run_arm(
            raw, arm="sanity", carrier=carriers["primary"], levels=(SANITY_IC,),
            repetitions=repetitions, base_seed=base_seed + 2, permutations=permutations,
            bootstraps=bootstraps, progress=progress,
        )

    if _sha256_path(raw_path) != raw_sha_before:
        raise PositiveControlError(
            "the real modeling dataset changed during the run; injection must never touch it"
        )

    report = build_report(
        arms=arms, carriers=carriers, raw_path=raw_path, base_seed=base_seed,
        started_at=started.isoformat().replace("+00:00", "Z"),
        duration_seconds=time.perf_counter() - clock,
        n_per_split=n_per_split, split_count=split_count,
    )
    markdown = render_markdown(report)
    validate_claim_safety_text(markdown)

    report_json = output / OUTPUT_FILENAMES["report_json"]
    report_md = output / OUTPUT_FILENAMES["report_md"]
    repetitions_csv = output / OUTPUT_FILENAMES["repetitions"]
    curve_csv = output / OUTPUT_FILENAMES["detection_curve"]
    attenuation_csv = output / OUTPUT_FILENAMES["attenuation"]

    report_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_md.write_text(markdown, encoding="utf-8")

    flat = [_flatten_record(record) for records in arms.values() for record in records]
    pd.DataFrame(flat).to_csv(repetitions_csv, index=False, float_format="%.17g")

    curve_rows = []
    attenuation_rows = []
    for arm, summaries in report["detection_curve"].items():
        for summary in summaries:
            curve_rows.append(
                {
                    "arm": arm,
                    "carrier": summary["carrier"],
                    "ic_injected": summary["ic_injected"],
                    "repetitions": summary["repetitions"],
                    "detections": summary["detections"],
                    "detection_rate": summary["detection_rate"],
                    "detection_rate_ci_low": summary["detection_rate_ci_95"][0],
                    "detection_rate_ci_high": summary["detection_rate_ci_95"][1],
                    "mean_recovered_ic": summary["checkpoint_summary"]["ic_final_evaluation"]["mean"],
                    "sd_recovered_ic": summary["checkpoint_summary"]["ic_final_evaluation"]["sd"],
                    "recovery_bias": summary["recovery_bias"],
                    "background_ic": summary["background_ic"]["ic_final_evaluation"],
                    "background_dominated": summary["background_dominated"][
                        "ic_final_evaluation"
                    ],
                    "background_adjusted_recovered_ic_heuristic": summary[
                        "background_adjusted_recovered_ic_heuristic"
                    ],
                    "background_adjusted_ratio_heuristic": summary[
                        "background_adjusted_ratio_heuristic"
                    ]["ic_final_evaluation"],
                    "n_raw_carrier": _count_value(
                        summary["checkpoint_n_summary"]["ic_raw_carrier"]
                    ),
                    "n_model_input_carrier": _count_value(
                        summary["checkpoint_n_summary"]["ic_model_input_carrier"]
                    ),
                }
            )
            for name, description in CHECKPOINTS:
                stats = summary["checkpoint_summary"][name]
                role = CHECKPOINT_ROLES[name]
                ratio_stats = summary["ratio_to_injected_summary"].get(name)
                ratio_suppressed = (
                    name == "ic_injected"
                    or role == "identity_invariant"
                    or summary["background_dominated"][name] is True
                    or ratio_stats is None
                )
                attenuation_rows.append(
                    {
                        "arm": arm,
                        "carrier": summary["carrier"],
                        "ic_injected": summary["ic_injected"],
                        "checkpoint": name,
                        "checkpoint_role": role,
                        "checkpoint_description": description,
                        "mean_ic": stats["mean"],
                        "sd_ic": stats["sd"],
                        "p05_ic": stats["p05"],
                        "p95_ic": stats["p95"],
                        "background_ic": summary["background_ic"][name],
                        "background_dominated": summary["background_dominated"][name],
                        "background_adjusted_ic_heuristic": summary[
                            "background_adjusted_ic_heuristic"
                        ][name],
                        "background_adjusted_ratio_heuristic": summary[
                            "background_adjusted_ratio_heuristic"
                        ][name],
                        "mean_ratio_to_injected": (
                            None if ratio_suppressed else ratio_stats["mean"]
                        ),
                        "sd_ratio_to_injected": (
                            None if ratio_suppressed else ratio_stats["sd"]
                        ),
                        "ratio_suppressed_reason": (
                            IDENTITY_INVARIANT_SUPPRESSION_REASON
                            if role == "identity_invariant"
                            else "injected design constant — ratio to itself not interpreted"
                            if name == "ic_injected"
                            else "theta=0 background dominates"
                            if summary["background_dominated"][name] is True
                            else None
                        ),
                    }
                )
    pd.DataFrame(curve_rows).to_csv(curve_csv, index=False, float_format="%.17g")
    pd.DataFrame(attenuation_rows).to_csv(attenuation_csv, index=False, float_format="%.17g")

    prov.write_manifest(
        SLUG,
        artifacts=[report_json, report_md, repetitions_csv, curve_csv, attenuation_csv],
        source_artifacts=[(raw_path, "modeling dataset (read-only; never modified)")],
        extra={
            "stage": "Stage 1 — raw-layer positive control",
            "git": _git_metadata(),
            "implementation_sha256": implementation_hash(),
            "ic_grid": list(IC_GRID),
            "repetitions_per_level": repetitions,
            "permutations": permutations,
            "confirmatory_family_size": CONFIRMATORY_FAMILY_SIZE,
            "confirmatory_passed": report["confirmatory"]["passed"],
        },
    )
    if progress:
        print(f"[positive-control] wrote {report_json.relative_to(ROOT)}")
    return report_json


def replay_check(*, repetitions: int = 1, permutations: int = 2_000) -> dict:
    """Run the confirmatory grid twice and confirm the two runs are identical.

    Determinism is a property the stage claims, so it is measured rather than
    assumed.
    """
    raw = pd.read_csv(rx.TRAINING_MODELING)
    carrier = select_carriers(raw)["primary"]
    base_seed = prov.seed_for(SLUG)
    runs = [
        run_arm(
            raw, arm="replay", carrier=carrier, levels=IC_GRID, repetitions=repetitions,
            base_seed=base_seed, permutations=permutations, bootstraps=permutations,
            progress=False,
        )
        for _ in range(2)
    ]
    first = json.dumps(runs[0], sort_keys=True)
    second = json.dumps(runs[1], sort_keys=True)
    return {
        "identical": first == second,
        "digest": _sha256_bytes(first.encode("utf-8")),
        "cells": len(runs[0]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--repetitions", type=int, default=DESCRIPTIVE_REPETITIONS,
        help="repetitions per level in each descriptive arm (pre-registered default: 200)",
    )
    parser.add_argument("--permutations", type=int, default=PERMUTATIONS)
    parser.add_argument("--bootstraps", type=int, default=BOOTSTRAPS)
    parser.add_argument("--skip-secondary", action="store_true")
    parser.add_argument("--skip-sanity", action="store_true")
    parser.add_argument(
        "--replay-check", action="store_true",
        help="run the confirmatory grid twice and report whether the results are identical",
    )
    args = parser.parse_args()

    if args.replay_check:
        result = replay_check()
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result["identical"] else 1)

    run(
        repetitions=args.repetitions,
        permutations=args.permutations,
        bootstraps=args.bootstraps,
        include_secondary=not args.skip_secondary,
        include_sanity=not args.skip_sanity,
    )


if __name__ == "__main__":
    main()
