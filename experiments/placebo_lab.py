"""Negative-control / placebo laboratory for the evaluation machinery (R3-NULL-01).

This module answers one narrow question: does the committed significance rig
usually fail to reject inputs that are known to carry no signal, with false
positives controlled by the family-wise gate? It never touches the canonical
datasets, prediction dumps, leaderboard, or significance artifacts. For each
seeded repetition it builds an isolated in-memory panel that keeps the real
tickers, feature-years, splits, and next-year targets but replaces every feature
column with independent ``N(0,1)`` noise, runs the same six-model ML family
through the same walk-forward split logic, and feeds the resulting predictions to
``experiments.significance`` verbatim (identical permutation count, bootstrap
count, seed, and Bonferroni family-wise gate). It then reports the empirical
family-wise rejection rate against its binomial expectation under alpha.

Placebo runs test the evaluation machinery, not the market; the expected outcome
is failure to reject known-null inputs in approximately (1 − α) of repetitions,
and any placebo ‘significance’ is a false positive at rate α or a numerical
artifact — never a signal.

Design decisions bound by the packet:
* R >= 20 seeded repetitions (default 25).
* Features replaced with independent N(0,1) noise, redrawn per repetition; the
  noise varies independently across rows, features, years, and repetitions and is
  never seeded per ticker (which would forge cross-year structure).
* Targets, splits, model definitions, and significance settings are the real
  ones, imported from ``experiments.run_experiments`` and
  ``experiments.significance``.
* The family-wise gate uses the six-model ML family (identical to the real
  evaluation's Bonferroni selection family). Baselines and the analytic power
  analysis sit outside that gate and are omitted so the 20x-harness cost stays
  tractable, exactly as the packet permits -- documented in the report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

from experiments import run_experiments as rx
from experiments import significance as sig


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "experiments" / "results_placebo"
JSON_OUTPUT = OUTPUT_DIR / "placebo_report.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "placebo_report.md"
RUNTIME_OUTPUT = ROOT / "experiments" / "runtime" / "placebo_runtime.json"

DEFAULT_REPETITIONS = 25
DEFAULT_BASE_SEED = 314159
FAMILY_WISE_ALPHA = 0.05
ROUND_DIGITS = 10

# The six-model ML selection family and significance settings are pinned to the
# real evaluation so the placebo cannot silently diverge from it.
ML_FAMILY = tuple(sig.ML_MODELS)
FAMILY_SIZE = len(ML_FAMILY)
PANEL_ID_COLUMNS = ("ticker", "feature_year", "target_return")

CLAIM_SAFETY_SENTENCE = (
    "Placebo runs test the evaluation machinery, not the market; the expected "
    "outcome is failure to reject known-null inputs in approximately (1 − α) of "
    "repetitions, and any placebo ‘significance’ is a false positive at rate α or "
    "a numerical artifact — never a signal."
)


# --------------------------------------------------------------------------- #
# Claim safety
# --------------------------------------------------------------------------- #
def validate_claim_safety_text(text: str) -> None:
    """Reject language that would read a placebo result as a market signal.

    The patterns target affirmative unsafe *interpretations* (signal/edge/alpha
    captured, market edge, profitable trading), not the mandatory safety
    sentence, which contains the words "significance" and "signal" only inside an
    explicit negation ("never a signal").
    """
    unsafe_patterns = {
        "alpha_captured": r"\b(?:captur\w+\s+alpha|alpha\s+captur\w+)\b",
        "market_edge": r"\bmarket[- ]edge\b",
        "profitable": r"\bprofitab\w+\b",
        "qualified_signal": r"\b(?:real|genuine|actual|true)\s+(?:signal|edge|alpha)\b",
        "reliable_signal": r"\breliable\s+(?:signal|edge|alpha)\b",
        "signal_found": r"\b(?:signal|edge|alpha)\s+(?:found|detected|captured|discovered|confirmed|established|present)\b",
        "found_signal": r"\b(?:found|detected|discover\w+|produc\w+|reveal\w+|captur\w+)\s+(?:a\s+|an\s+|real\s+|genuine\s+)*(?:signal|market\s+edge|alpha)\b",
        "placebo_is_signal": r"\bplacebo\w*\s+(?:is|was|are|were|shows?|proves?|establish\w*)\s+(?:a\s+)?(?:signal|edge|alpha)\b",
        "market_beating": r"\b(?:market[- ]beating|outperform(?:s|ed)\s+the\s+market)\b",
        "recommendation": r"\b(?:buy|sell|hold)\s+recommendation\b",
    }
    violations = [
        name
        for name, pattern in unsafe_patterns.items()
        if re.search(pattern, text, flags=re.IGNORECASE)
    ]
    if violations:
        raise ValueError(f"Unsafe placebo claim(s): {', '.join(violations)}")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rounded(value: float | int | None, digits: int = ROUND_DIGITS) -> float | None:
    if value is None:
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return round(number, digits)


def reference_panel() -> tuple[pd.DataFrame, list[str]]:
    """Build the real modeling panel once (read-only) and return (panel, features).

    Delegates to ``run_experiments.build_panel`` so the tickers, feature-years,
    and next-year targets are exactly those the real evaluation uses. The canonical
    CSV is only read; the returned frame is the placebo's structural template.
    """
    panel = rx.build_panel()
    feature_columns = [c for c in panel.columns if c not in PANEL_ID_COLUMNS]
    return panel, feature_columns


def build_noise_panel(
    reference: pd.DataFrame, feature_columns: list[str], seed: int
) -> pd.DataFrame:
    """Return a copy of ``reference`` with every feature replaced by N(0,1) noise.

    Identity, split/year, and target columns are preserved byte-for-byte. The
    noise is a single contiguous ``standard_normal`` draw of shape
    ``(rows, features)`` so every (row, feature) cell is an independent N(0,1):
    the noise varies across rows (each row is a distinct ticker-year), across
    features, and -- because rows span feature-years -- across years, with no
    per-ticker seeding that could forge cross-year structure. The input frame is
    never mutated.
    """
    rng = np.random.default_rng(seed)
    noise_panel = reference.copy(deep=True)
    noise_values = rng.standard_normal(size=(len(reference), len(feature_columns)))
    noise_panel[list(feature_columns)] = noise_values
    return noise_panel


def _write_ml_prediction_dumps(
    noise_panel: pd.DataFrame, feature_columns: list[str], results_dir: Path
) -> None:
    """Run the six-model ML family through the real walk-forward split logic.

    This mirrors ``run_experiments.run`` exactly (same split filters, same model
    callables, same prediction-dump schema and float format) but restricted to
    the ML family that constitutes the significance Bonferroni gate.
    """
    ml_models = {
        name: fn for name, (kind, fn) in rx.MODELS.items() if kind == "ml"
    }
    if sorted(ml_models) != sorted(ML_FAMILY):
        raise ValueError(
            f"ML family drift: run_experiments exposes {sorted(ml_models)} "
            f"but significance gate expects {sorted(ML_FAMILY)}"
        )
    for split in rx.SPLITS:
        train = noise_panel[
            (noise_panel["feature_year"] + 1).isin(split["train_target_years"])
        ]
        test = noise_panel[noise_panel["feature_year"] == split["test_feature_year"]]
        x_train = train[feature_columns].to_numpy(float)
        y_train = train["target_return"].to_numpy(float)
        x_test = test[feature_columns].to_numpy(float)
        y_test = test["target_return"].to_numpy(float)
        train_mask = ~np.isnan(y_train)
        x_train, y_train = x_train[train_mask], y_train[train_mask]

        prediction_rows: list[dict[str, object]] = []
        for name in ML_FAMILY:
            predicted = np.asarray(ml_models[name](x_train, y_train, x_test), dtype=float)
            evaluated = ~np.isnan(y_test) & ~np.isnan(predicted)
            prediction_rows.extend(
                {
                    "ticker": ticker,
                    "year": split["test_feature_year"] + 1,
                    "model": name,
                    "y_true": float(actual),
                    "y_pred": float(prediction),
                }
                for ticker, actual, prediction in zip(
                    test.loc[evaluated, "ticker"], y_test[evaluated], predicted[evaluated]
                )
            )
        pd.DataFrame(
            prediction_rows, columns=["ticker", "year", "model", "y_true", "y_pred"]
        ).to_csv(
            results_dir / f"predictions_{split['name']}.csv",
            index=False,
            float_format="%.17g",
        )


def _family_wise_gate(
    results_dir: Path,
    *,
    permutations: int,
    bootstraps: int,
    significance_seed: int,
) -> dict[str, object]:
    """Apply the real significance family-wise gate to one placebo repetition.

    Reuses ``significance.analyze_model`` verbatim for the pooled within-year
    Spearman IC and two-sided permutation p-value, then applies the same
    Bonferroni arithmetic ``significance.build_report`` uses:
    ``adjusted = min(1, raw_p * family_size)`` and reject iff ``adjusted < 0.05``.
    """
    predictions, _sources = sig.load_prediction_dumps(results_dir)
    present = set(predictions["model"].unique())
    missing = sorted(set(ML_FAMILY) - present)
    if missing:
        raise ValueError(f"placebo prediction dumps missing ML models: {missing}")

    pooled_ic: dict[str, float | None] = {}
    raw_p: dict[str, float] = {}
    for model in ML_FAMILY:
        analysis = sig.analyze_model(
            predictions[predictions["model"] == model],
            permutations=permutations,
            bootstraps=bootstraps,
            seed=significance_seed,
        )["pooled"]
        pooled_ic[model] = _rounded(analysis["observed_ic"])
        raw_p[model] = float(analysis["permutation_p_value_two_sided"])

    min_model = min(ML_FAMILY, key=lambda name: (raw_p[name], name))
    min_raw_p = raw_p[min_model]
    adjusted = min(1.0, min_raw_p * FAMILY_SIZE)
    return {
        "pooled_ic_by_model": {model: pooled_ic[model] for model in sorted(ML_FAMILY)},
        "raw_p_by_model": {model: _rounded(raw_p[model]) for model in sorted(ML_FAMILY)},
        "min_raw_p_value": _rounded(min_raw_p),
        "min_raw_p_model": min_model,
        "bonferroni_adjusted_min_p": _rounded(adjusted),
        "family_wise_rejected": bool(adjusted < FAMILY_WISE_ALPHA),
    }


def run_repetition(
    reference: pd.DataFrame,
    feature_columns: list[str],
    *,
    rep_index: int,
    seed: int,
    permutations: int,
    bootstraps: int,
    significance_seed: int,
) -> dict[str, object]:
    """Execute one isolated placebo repetition and return its explicit record.

    A repetition never omits itself silently: any failure is captured as an
    explicit ``failed`` status carrying the error, and the record is still
    returned so the report retains every repetition.
    """
    started = time.perf_counter()
    record: dict[str, object] = {
        "rep_index": int(rep_index),
        "seed": int(seed),
        "status": "pending",
    }
    try:
        noise_panel = build_noise_panel(reference, feature_columns, seed)
        with tempfile.TemporaryDirectory(prefix="placebo_rep_") as tmp:
            results_dir = Path(tmp)
            _write_ml_prediction_dumps(noise_panel, feature_columns, results_dir)
            gate = _family_wise_gate(
                results_dir,
                permutations=permutations,
                bootstraps=bootstraps,
                significance_seed=significance_seed,
            )
        record.update(gate)
        record["status"] = "complete"
    except Exception as exc:  # explicit failure, never a silent drop
        record["status"] = "failed"
        record["error"] = f"{type(exc).__name__}: {exc}"
        record["family_wise_rejected"] = None
        record["min_raw_p_value"] = None
    record["runtime_seconds"] = _rounded(time.perf_counter() - started, 4)
    return record


# --------------------------------------------------------------------------- #
# Binomial reference
# --------------------------------------------------------------------------- #
def zero_success_clopper_pearson_upper_bound(
    n: int, confidence: float = 0.95
) -> float:
    """Exact two-sided Clopper-Pearson upper bound when zero events occur.

    For zero events in ``n`` Bernoulli trials, the two-sided upper endpoint
    solves ``(1 - p_upper) ** n = (1 - confidence) / 2``. Therefore
    ``p_upper = 1 - ((1 - confidence) / 2) ** (1 / n)``. This closed form keeps
    the reported R=25 interval deterministic without adding an interval-library
    dependency.
    """
    if n < 1:
        raise ValueError("n must be positive")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be strictly between 0 and 1")
    return 1.0 - ((1.0 - confidence) / 2.0) ** (1.0 / n)


def binomial_reference(count: int, n: int, alpha: float) -> dict[str, object]:
    """Compare an observed family-wise rejection count with Binomial(n, alpha).

    Under the null, the Bonferroni family-wise gate rejects with probability at
    most ``alpha``; ``alpha * n`` is therefore an upper-reference expectation.
    Tail probabilities are exact (n is small).
    """
    def pmf(k: int) -> float:
        return math.comb(n, k) * alpha**k * (1.0 - alpha) ** (n - k)

    upper_tail = sum(pmf(k) for k in range(count, n + 1))  # P(X >= count)
    lower_tail = sum(pmf(k) for k in range(0, count + 1))  # P(X <= count)
    confidence = 0.95
    zero_event_upper = (
        zero_success_clopper_pearson_upper_bound(n, confidence)
        if count == 0 and n
        else None
    )
    return {
        "alpha": alpha,
        "repetitions_scored": int(n),
        "expected_rejections": _rounded(alpha * n),
        "observed_rejections": int(count),
        "observed_rate": _rounded(count / n) if n else None,
        "pmf_at_observed": _rounded(pmf(count) if n else None),
        "p_value_upper_tail_ge_observed": _rounded(upper_tail if n else None),
        "p_value_lower_tail_le_observed": _rounded(lower_tail if n else None),
        "exact_two_sided_confidence_level": confidence,
        "exact_two_sided_clopper_pearson_upper_bound": _rounded(zero_event_upper),
        "exact_interval_method": (
            "For 0/n events, solve (1 - p_upper)^n = (1 - confidence)/2, "
            "so p_upper = 1 - ((1 - confidence)/2)^(1/n)."
            if zero_event_upper is not None
            else "The closed-form zero-event endpoint is not applicable when the observed count is nonzero."
        ),
        "note": (
            "Bonferroni control makes alpha*n an upper reference; observed at or "
            "below it is the expected, on-spec outcome and is not evidence of skill."
        ),
    }


# --------------------------------------------------------------------------- #
# Report assembly
# --------------------------------------------------------------------------- #
def _deterministic_record(record: dict[str, object]) -> dict[str, object]:
    """Project a repetition record to its seeded, reproducible fields.

    Wall-clock ``runtime_seconds`` is intentionally excluded so the committed
    report is byte-identical across reruns; per-repetition runtime is preserved
    separately in the runtime log (see ``build_runtime_log``).
    """
    deterministic = {
        "rep_index": int(record["rep_index"]),
        "seed": int(record["seed"]),
        "status": record["status"],
        "family_wise_rejected": record.get("family_wise_rejected"),
        "min_raw_p_value": record.get("min_raw_p_value"),
        "min_raw_p_model": record.get("min_raw_p_model"),
        "bonferroni_adjusted_min_p": record.get("bonferroni_adjusted_min_p"),
        "pooled_ic_by_model": record.get("pooled_ic_by_model"),
        "raw_p_by_model": record.get("raw_p_by_model"),
    }
    if record["status"] == "failed":
        deterministic["error"] = record.get("error")
    return deterministic


def build_runtime_log(
    repetitions: list[dict[str, object]], *, base_seed: int
) -> dict[str, object]:
    """Per-repetition wall-clock, kept out of the byte-identical scientific report."""
    per_rep = [
        {
            "rep_index": int(r["rep_index"]),
            "seed": int(r["seed"]),
            "status": r["status"],
            "runtime_seconds": r.get("runtime_seconds"),
        }
        for r in repetitions
    ]
    total = sum(
        float(r["runtime_seconds"])
        for r in per_rep
        if r["runtime_seconds"] is not None
    )
    return {
        "task": "R3-NULL-01",
        "artifact": "wall-clock timing log",
        "determinism_note": (
            "Wall-clock timings are NOT deterministic and are deliberately kept out "
            "of placebo_report.{json,md}; only this file varies between reruns. The "
            "scientific report is byte-identical across seeded reruns."
        ),
        "base_noise_seed": int(base_seed),
        "generator_command": "make research-placebo",
        "total_runtime_seconds": _rounded(total, 4),
        "per_repetition": per_rep,
    }


def build_report(
    reference: pd.DataFrame,
    feature_columns: list[str],
    repetitions: list[dict[str, object]],
    *,
    permutations: int,
    bootstraps: int,
    significance_seed: int,
    base_seed: int,
) -> dict[str, object]:
    """Assemble the deterministic placebo report from all repetition records."""
    modeling_csv = rx._modeling_csv()
    source_artifacts = []
    if modeling_csv.is_file():
        source_artifacts.append(
            {
                "path": modeling_csv.relative_to(ROOT).as_posix(),
                "sha256": _sha256(modeling_csv),
                "rows": int(sum(1 for _ in modeling_csv.open("rb")) - 1),
                "role": "read-only structural template (tickers, years, targets); features are discarded and replaced by noise",
            }
        )

    completed = [r for r in repetitions if r["status"] == "complete"]
    failed = [r for r in repetitions if r["status"] == "failed"]
    rejection_count = sum(1 for r in completed if r["family_wise_rejected"])
    scored = len(completed)

    min_p_values = [
        float(r["min_raw_p_value"])
        for r in completed
        if r["min_raw_p_value"] is not None
    ]
    pooled_ics = [
        float(v)
        for r in completed
        for v in r["pooled_ic_by_model"].values()
        if v is not None
    ]

    def _distribution(values: list[float]) -> dict[str, float | None]:
        if not values:
            return {"count": 0, "min": None, "mean": None, "max": None}
        return {
            "count": len(values),
            "min": _rounded(min(values)),
            "mean": _rounded(sum(values) / len(values)),
            "max": _rounded(max(values)),
        }

    analysis_status = (
        "complete" if not failed else "partial_with_explicit_failed_repetitions"
    )
    binomial = binomial_reference(rejection_count, scored, FAMILY_WISE_ALPHA)

    report = {
        "schema_version": "1.1.0",
        "task": "R3-NULL-01",
        "analysis_status": analysis_status,
        "claim_safety_sentence": CLAIM_SAFETY_SENTENCE,
        "generated_by": {
            "module": "experiments/placebo_lab.py",
            "generator_command": "make research-placebo",
            "isolation": "each repetition scores an in-memory noise panel written to a private tempfile.TemporaryDirectory; no canonical dataset, dump, leaderboard, or significance artifact is read for features or written to",
            "determinism": "fixed base_seed + repetition index for feature noise; fixed significance seed for permutation/bootstrap resampling",
            "deterministic_ordering": "repetitions in ascending rep_index; per-model maps sorted by model name",
            "serialization": "sorted-key UTF-8 JSON, newline-terminated; Markdown newline-terminated",
            "pooled_ic_and_gate_source": "experiments.significance.analyze_model + build_report Bonferroni arithmetic (reused verbatim)",
        },
        "design": {
            "question": "Does the committed significance rig fail to reject known-null (pure-noise) inputs in approximately (1 - alpha) of repetitions, with any rejection counted as a family-wise false positive?",
            "repetitions": len(repetitions),
            "base_noise_seed": int(base_seed),
            "noise_distribution": "independent N(0,1) per (row, feature); a fresh (rows x features) draw per repetition",
            "noise_independence": "varies across rows, features, years, and repetitions; never seeded per ticker",
            "features_replaced": "all",
            "feature_count": len(feature_columns),
            "feature_columns": sorted(feature_columns),
            "panel_rows": int(len(reference)),
            "feature_years": sorted(int(y) for y in reference["feature_year"].unique()),
            "target_years": sorted(int(s["test_feature_year"]) + 1 for s in rx.SPLITS),
            "splits": [s["name"] for s in rx.SPLITS],
            "targets_identical_to_real_run": True,
            "splits_identical_to_real_run": True,
            "model_definitions_identical_to_real_run": True,
            "significance_settings_identical_to_real_run": True,
            "model_family": list(ML_FAMILY),
            "model_family_size": FAMILY_SIZE,
            "model_family_choice": (
                "Six-model ML family only -- identical to the real evaluation's "
                "Bonferroni selection family in experiments/significance.py. Baseline "
                "models and the analytic power analysis are outside the family-wise "
                "gate and are omitted to keep the 20x-harness runtime tractable, as "
                "the R3-NULL-01 packet permits."
            ),
            "permutations": permutations,
            "bootstraps": bootstraps,
            "significance_seed": significance_seed,
            "family_wise_alpha": FAMILY_WISE_ALPHA,
            "family_wise_gate": "reject the family iff min_raw_permutation_p * family_size < 0.05 (Bonferroni)",
        },
        "source_artifacts": source_artifacts,
        "repetitions": [_deterministic_record(r) for r in repetitions],
        "summary": {
            "repetitions_total": len(repetitions),
            "repetitions_completed": len(completed),
            "repetitions_failed": len(failed),
            "failed_rep_indices": sorted(int(r["rep_index"]) for r in failed),
            "family_wise_rejection_count": int(rejection_count),
            "family_wise_rejection_rate": _rounded(rejection_count / scored) if scored else None,
            "binomial_reference": binomial,
            "min_raw_p_value_distribution": _distribution(min_p_values),
            "pooled_ic_distribution": _distribution(pooled_ics),
        },
        "findings": [
            "The rejection count is the result: it is compared with the Binomial(R, alpha) expectation, and every repetition -- including any that rejected -- is retained in full.",
            "A placebo repetition that rejects is a false positive of the rig at rate alpha or a numerical artifact, never evidence about any market or ticker.",
            "Features are fully overwritten by independent N(0,1) noise; only the real tickers, feature-years, splits, and targets are kept so the machinery runs unchanged.",
            "No canonical dataset, prediction dump, leaderboard, or significance artifact is modified; each repetition is scored in a private temporary directory.",
        ],
        "claim_safety": {
            "tests_the_evaluation_machinery_not_the_market": True,
            "expected_outcome_is_nonrejection_at_rate_one_minus_alpha": True,
            "placebo_significance_is_a_signal": False,
            "market_edge_established": False,
            "alpha_captured": False,
            "profitable_strategy_established": False,
            "predictive_validity_established": False,
            "reliable_predictive_edge_established": False,
            "canonical_artifacts_modified": False,
            "rejecting_repetitions_hidden": False,
        },
        "limitations": [
            "This is a test of the evaluation rig on synthetic noise, not a market study; nothing here supports or refutes any claim about BIST equities.",
            "The gate uses the six-model ML Bonferroni family and the committed permutation/bootstrap settings; it does not re-run the analytic power analysis or the baseline models.",
            "Bonferroni control is conservative, so the empirical rejection rate is expected to sit at or below alpha rather than exactly at it.",
            f"R={len(repetitions)} is a low-resolution negative-control smoke test.",
            f"{rejection_count}/{scored} does not certify exact family-wise calibration at alpha={FAMILY_WISE_ALPHA}.",
            "It can expose gross anti-conservatism but cannot precisely estimate the Type-I error rate.",
            (
                f"For {rejection_count}/{scored}, the exact two-sided 95% Clopper-Pearson binomial upper bound is approximately "
                f"{binomial['exact_two_sided_clopper_pearson_upper_bound']:.3f} "
                f"(unrounded {binomial['exact_two_sided_clopper_pearson_upper_bound']}) using the documented zero-event closed form."
                if rejection_count == 0 and scored
                else "The exact zero-event Clopper-Pearson upper-bound formula does not apply because the observed rejection count is nonzero."
            ),
            "Reproduction is numerical-environment-qualified; byte identity holds within a fixed Python and numerical-package environment.",
            "The conclusion of the project is unchanged: no reliable predictive edge. Research support only; not investment advice.",
        ],
    }
    return report


def render_markdown(report: dict[str, object]) -> str:
    """Render the deterministic Markdown companion to the JSON report."""
    design = report["design"]
    summary = report["summary"]
    binomial = summary["binomial_reference"]
    interval_result = (
        f"- Exact two-sided {int(binomial['exact_two_sided_confidence_level'] * 100)}% "
        f"Clopper-Pearson upper bound for 0/{binomial['repetitions_scored']}: "
        f"{binomial['exact_two_sided_clopper_pearson_upper_bound']}"
        if binomial["exact_two_sided_clopper_pearson_upper_bound"] is not None
        else "- Exact zero-event Clopper-Pearson upper bound: not applicable because the observed rejection count is nonzero"
    )
    lines = [
        "# Negative-control / placebo laboratory",
        "",
        "## Question and estimand",
        "",
        "This R3-NULL-01 artifact tests whether the committed significance rig "
        "usually *fails to reject* known-null inputs, with any rejection counted "
        "as a family-wise false positive. Each of "
        f"{design['repetitions']} seeded repetitions rebuilds the real modeling "
        "panel but replaces every feature column with independent N(0,1) noise, "
        "runs the same six-model ML family through the same walk-forward splits, "
        "and applies the same permutation + Bonferroni family-wise gate from "
        "`experiments/significance.py`. Targets, splits, model definitions, and "
        "significance settings are the real ones; only the features are noise.",
        "",
        f"> {report['claim_safety_sentence']}",
        "",
        "## Design",
        "",
        f"- Repetitions: {design['repetitions']} (base noise seed {design['base_noise_seed']})",
        f"- Panel: {design['panel_rows']} rows, {design['feature_count']} features fully replaced by noise",
        f"- Feature-years: {design['feature_years']}; target years: {design['target_years']}",
        f"- Model family (family-wise gate): {', '.join(design['model_family'])}",
        f"- Significance: {design['permutations']} permutations, {design['bootstraps']} bootstraps, "
        f"seed {design['significance_seed']}, Bonferroni family size {design['model_family_size']}, "
        f"alpha {design['family_wise_alpha']}",
        f"- Model-family choice: {design['model_family_choice']}",
        "",
        "## Result",
        "",
        f"- Repetitions completed: {summary['repetitions_completed']} / {summary['repetitions_total']} "
        f"(failed: {summary['repetitions_failed']})",
        f"- Family-wise rejections: **{summary['family_wise_rejection_count']}** "
        f"(rate {summary['family_wise_rejection_rate']})",
        f"- Binomial expectation under alpha={binomial['alpha']}: "
        f"{binomial['expected_rejections']} rejections over "
        f"{binomial['repetitions_scored']} scored repetitions",
        f"- P(X >= observed) = {binomial['p_value_upper_tail_ge_observed']}; "
        f"P(X <= observed) = {binomial['p_value_lower_tail_le_observed']}",
        interval_result,
        f"- Interval method: {binomial['exact_interval_method']}",
        f"- Pooled-IC distribution across repetitions/models: "
        f"min {report['summary']['pooled_ic_distribution']['min']}, "
        f"mean {report['summary']['pooled_ic_distribution']['mean']}, "
        f"max {report['summary']['pooled_ic_distribution']['max']}",
        "",
        binomial["note"],
        "",
        "## Per-repetition records",
        "",
        "Optional per-repetition wall-clock output is local runtime data outside "
        "this governed results directory; it is excluded so this scientific report "
        "is byte-identical across seeded reruns.",
        "",
        "| Rep | Seed | Status | Min raw p | Bonferroni min p | Rejected (FWER) |",
        "|---:|---:|---|---:|---:|---|",
    ]
    for record in report["repetitions"]:
        rejected = record.get("family_wise_rejected")
        rejected_label = "yes" if rejected else "no" if rejected is not None else "n/a"
        lines.append(
            f"| {record['rep_index']} | {record['seed']} | {record['status']} | "
            f"{record.get('min_raw_p_value')} | {record.get('bonferroni_adjusted_min_p')} | "
            f"{rejected_label} |"
        )
    lines.extend(["", "## Interpretation boundaries", ""])
    lines.extend(f"- {item}" for item in report["findings"])
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.extend(
        [
            "",
            "The conclusion remains: no reliable predictive edge. Research support only; not investment advice.",
            "",
        ]
    )
    text = "\n".join(lines)
    validate_claim_safety_text(text)
    return text


def run(
    output_dir: Path = OUTPUT_DIR,
    *,
    runtime_output: Path | None = None,
    repetitions: int = DEFAULT_REPETITIONS,
    base_seed: int = DEFAULT_BASE_SEED,
    permutations: int = sig.DEFAULT_PERMUTATIONS,
    bootstraps: int = sig.DEFAULT_BOOTSTRAPS,
    significance_seed: int = sig.DEFAULT_SEED,
) -> tuple[Path, Path]:
    """Generate the isolated placebo artifacts; never touches canonical data."""
    if repetitions < 20:
        raise ValueError("R3-NULL-01 requires at least 20 placebo repetitions")
    reference, feature_columns = reference_panel()
    records = [
        run_repetition(
            reference,
            feature_columns,
            rep_index=index,
            seed=base_seed + index,
            permutations=permutations,
            bootstraps=bootstraps,
            significance_seed=significance_seed,
        )
        for index in range(repetitions)
    ]
    report = build_report(
        reference,
        feature_columns,
        records,
        permutations=permutations,
        bootstraps=bootstraps,
        significance_seed=significance_seed,
        base_seed=base_seed,
    )
    markdown = render_markdown(report)
    runtime_log = build_runtime_log(records, base_seed=base_seed)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / JSON_OUTPUT.name
    markdown_path = output_dir / MARKDOWN_OUTPUT.name
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(markdown, encoding="utf-8")
    if runtime_output is not None:
        runtime_path = Path(runtime_output)
        runtime_path.parent.mkdir(parents=True, exist_ok=True)
        runtime_path.write_text(
            json.dumps(runtime_log, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    print(
        f"[placebo] reps={report['summary']['repetitions_total']} "
        f"completed={report['summary']['repetitions_completed']} "
        f"rejections={report['summary']['family_wise_rejection_count']} "
        f"rate={report['summary']['family_wise_rejection_rate']} "
        f"status={report['analysis_status']} -> {output_dir}"
    )
    return json_path, markdown_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument(
        "--runtime-output",
        type=Path,
        default=RUNTIME_OUTPUT,
        help="Local ignored timing log; pass an explicit path to relocate it.",
    )
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    parser.add_argument("--base-seed", type=int, default=DEFAULT_BASE_SEED)
    parser.add_argument("--permutations", type=int, default=sig.DEFAULT_PERMUTATIONS)
    parser.add_argument("--bootstraps", type=int, default=sig.DEFAULT_BOOTSTRAPS)
    parser.add_argument("--significance-seed", type=int, default=sig.DEFAULT_SEED)
    args = parser.parse_args()
    run(
        args.output_dir,
        runtime_output=args.runtime_output,
        repetitions=args.repetitions,
        base_seed=args.base_seed,
        permutations=args.permutations,
        bootstraps=args.bootstraps,
        significance_seed=args.significance_seed,
    )


if __name__ == "__main__":
    main()
