"""Walk-forward evaluation of the real user-facing serving heuristic (R3-SERV-01).

The heuristic is not reimplemented here.  Each split is exposed to the unchanged
``forecasting_csv_service`` through the backend's documented
``RESEARCH_REPO_ROOT`` override in an isolated temporary data root.  The harness
then calls the service's real ``train_parameters`` and ``run_forecast``
functions.  Realized test outcomes are kept outside that temporary scoring CSV
and are joined only after the service returns its serialized four-decimal score.

The statistical treatment imports ``experiments.significance.analyze_model`` so
within-year Spearman IC, seeded permutation, and seeded bootstrap behavior stay
identical to the canonical evaluation.  The serving heuristic is one
prespecified test outside, and never added to, the six-model ML Bonferroni
family.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable

import numpy as np
import pandas as pd

from experiments import significance
from experiments.run_experiments import SPLITS as CANONICAL_SPLITS


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "experiments" / "results_serving_eval"
MODELING_DATASET = (
    ROOT / "data" / "trusted_clean" / "modeling_dataset_training_2020_2025.csv"
)
SERVICE_FILE = ROOT / "backend" / "app" / "services" / "forecasting_csv_service.py"
CANONICAL_LEADERBOARD = ROOT / "experiments" / "leaderboard.csv"
CANONICAL_SIGNIFICANCE = ROOT / "experiments" / "results" / "significance_report.json"
CANONICAL_PREDICTIONS = {
    year: ROOT / "experiments" / "results" / f"predictions_test_{year}.csv"
    for year in (2023, 2024, 2025)
}
JSON_OUTPUT = RESULTS_DIR / "serving_eval_report.json"
MARKDOWN_OUTPUT = RESULTS_DIR / "serving_eval_report.md"
PREDICTION_OUTPUTS = {
    year: RESULTS_DIR / f"predictions_serving_{year}.csv"
    for year in (2023, 2024, 2025)
}
TASK_ID = "R3-SERV-01"
MODEL_NAME = "serving_heuristic"
TOP_N = 12
RANDOM_SEED = significance.DEFAULT_SEED
PERMUTATIONS = significance.DEFAULT_PERMUTATIONS
BOOTSTRAPS = significance.DEFAULT_BOOTSTRAPS
SINGLE_TEST_LABEL = "single prespecified test, outside the six-model Bonferroni family"
REGENERATION_COMMAND = "make research-serving-eval"
REVIEW_HANDOFF = "docs/R3_SERV_01_FABLE5_REVIEW_HANDOFF.md"
SERVICE_FUNCTIONS = (
    "backend/app/services/forecasting_csv_service.py::train_parameters",
    "backend/app/services/forecasting_csv_service.py::run_forecast",
)
REQUIRED_MODELING_COLUMNS = {"ticker", "year", "has_target", "next_year_return_pct"}
REQUIRED_REFERENCE_COLUMNS = {"ticker", "year", "model", "y_true", "y_pred"}


@dataclass(frozen=True)
class SplitSpec:
    name: str
    train_target_years: tuple[int, ...]
    train_feature_years: tuple[int, ...]
    test_feature_year: int
    test_target_year: int


@dataclass
class PreparedSplit:
    spec: SplitSpec
    training_rows: pd.DataFrame
    service_scoring_rows: pd.DataFrame
    realized_outcomes: pd.DataFrame
    panel_rows: int
    excluded_missing_outcome: tuple[str, ...]


def split_specs() -> tuple[SplitSpec, ...]:
    """Translate the canonical split constants without changing their boundaries."""
    specs = []
    for split in CANONICAL_SPLITS:
        test_feature_year = int(split["test_feature_year"])
        train_target_years = tuple(int(year) for year in split["train_target_years"])
        specs.append(
            SplitSpec(
                name=str(split["name"]),
                train_target_years=train_target_years,
                train_feature_years=tuple(year - 1 for year in train_target_years),
                test_feature_year=test_feature_year,
                test_target_year=test_feature_year + 1,
            )
        )
    return tuple(specs)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_record(path: Path, *, role: str) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Required R3-SERV-01 source is missing: {path}")
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
        "role": role,
    }


def _normalise_tickers(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["ticker"] = out["ticker"].astype(str).str.strip().str.upper()
    return out


def load_modeling_dataset(path: Path = MODELING_DATASET) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Training modeling dataset missing: {path}")
    frame = pd.read_csv(path)
    missing = REQUIRED_MODELING_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"{path} missing required columns: {sorted(missing)}")
    frame = _normalise_tickers(frame)
    frame["year"] = pd.to_numeric(frame["year"], errors="raise").astype(int)
    if frame.duplicated(["ticker", "year"]).any():
        duplicates = frame.loc[
            frame.duplicated(["ticker", "year"], keep=False), ["ticker", "year"]
        ].sort_values(["year", "ticker"])
        raise ValueError(
            "modeling dataset contains duplicate ticker/year rows: "
            f"{duplicates.to_dict(orient='records')}"
        )
    return frame.sort_values(["year", "ticker"], kind="mergesort").reset_index(drop=True)


def load_reference_cohort(path: Path, target_year: int) -> pd.DataFrame:
    """Load the exact evaluated ticker/outcome cohort shared by all canonical models."""
    if not path.is_file():
        raise FileNotFoundError(f"Canonical prediction dump missing: {path}")
    frame = pd.read_csv(path)
    missing = REQUIRED_REFERENCE_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"{path} missing required columns: {sorted(missing)}")
    frame = _normalise_tickers(frame)
    frame["year"] = pd.to_numeric(frame["year"], errors="raise").astype(int)
    if set(frame["year"].unique()) != {target_year}:
        raise ValueError(f"{path} must contain target year {target_year} only")
    if frame.duplicated(["ticker", "year", "model"]).any():
        raise ValueError(f"{path} contains duplicate ticker/year/model rows")
    numeric = frame[["y_true", "y_pred"]].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any() or not np.isfinite(numeric.to_numpy(float)).all():
        raise ValueError(f"{path} contains missing or non-finite required values")
    frame[["y_true", "y_pred"]] = numeric

    counts = frame.groupby("model", sort=True).size()
    if counts.nunique() != 1:
        raise ValueError(f"{path} models do not share one evaluated cohort size")
    outcome_counts = frame.groupby("ticker", sort=True)["y_true"].nunique(dropna=False)
    if not outcome_counts.eq(1).all():
        raise ValueError(f"{path} models disagree on realized outcomes")
    ticker_sets = {
        tuple(sorted(group["ticker"].tolist()))
        for _, group in frame.groupby("model", sort=True)
    }
    if len(ticker_sets) != 1:
        raise ValueError(f"{path} models do not share the same ticker cohort")

    reference = (
        frame[["ticker", "year", "y_true"]]
        .drop_duplicates(["ticker", "year"])
        .sort_values("ticker", kind="mergesort")
        .reset_index(drop=True)
    )
    return reference


def prepare_split(
    modeling: pd.DataFrame,
    reference: pd.DataFrame,
    spec: SplitSpec,
) -> PreparedSplit:
    """Create leakage-safe service inputs and keep outcomes evaluation-only."""
    if modeling.duplicated(["ticker", "year"]).any():
        raise ValueError("modeling dataset contains duplicate ticker/year rows")
    if reference.duplicated(["ticker", "year"]).any():
        raise ValueError("reference cohort contains duplicate ticker/year rows")
    if set(reference["year"].astype(int).unique()) != {spec.test_target_year}:
        raise ValueError("reference cohort target year does not match the split")

    train = modeling[modeling["year"].isin(spec.train_feature_years)].copy()
    train_target = pd.to_numeric(train["next_year_return_pct"], errors="coerce")
    train_has_target = train["has_target"].astype(str).str.lower().isin({"true", "1"})
    train = train[train_has_target & train_target.notna()].copy()
    if train.empty:
        raise ValueError(f"{spec.name} has no eligible training rows")
    if set(train["year"].unique()) != set(spec.train_feature_years):
        raise ValueError(f"{spec.name} is missing one or more training feature years")
    if int(train["year"].max()) >= spec.test_feature_year:
        raise ValueError(f"{spec.name} training window reaches the test feature year")
    train = train.sort_values(["year", "ticker"], kind="mergesort").reset_index(drop=True)

    panel = modeling[modeling["year"] == spec.test_feature_year].copy()
    if panel.empty:
        raise ValueError(f"{spec.name} has no feature-year panel")
    expected = set(reference["ticker"])
    available = set(panel["ticker"])
    missing_rows = sorted(expected - available)
    if missing_rows:
        raise ValueError(f"{spec.name} canonical cohort rows missing from modeling data: {missing_rows}")

    panel_target = pd.to_numeric(panel["next_year_return_pct"], errors="coerce")
    eligible_from_data = set(panel.loc[panel_target.notna(), "ticker"])
    unexpected_eligible = sorted(eligible_from_data - expected)
    if unexpected_eligible:
        raise ValueError(
            f"{spec.name} canonical dump omits rows with present outcomes: {unexpected_eligible}"
        )
    excluded = tuple(sorted(available - expected))
    if any(
        pd.notna(panel.loc[panel["ticker"] == ticker, "next_year_return_pct"].iloc[0])
        for ticker in excluded
    ):
        raise ValueError(f"{spec.name} non-cohort rows are not all missing-outcome rows")

    score_rows = panel[panel["ticker"].isin(expected)].copy()
    observed = score_rows[["ticker", "next_year_return_pct"]].rename(
        columns={"next_year_return_pct": "modeling_y_true"}
    )
    realized = reference.merge(observed, on="ticker", how="left", validate="one_to_one")
    if realized["modeling_y_true"].isna().any():
        raise ValueError(f"{spec.name} canonical cohort includes a missing modeling outcome")
    if not np.allclose(
        realized["y_true"].to_numpy(float),
        realized["modeling_y_true"].to_numpy(float),
        rtol=0.0,
        atol=1e-12,
    ):
        raise ValueError(f"{spec.name} canonical dump outcomes differ from modeling data")
    realized = realized[["ticker", "year", "y_true"]].sort_values(
        "ticker", kind="mergesort"
    ).reset_index(drop=True)

    # The actual service receives the feature rows but no realized test outcomes.
    service_rows = score_rows.sort_values("ticker", kind="mergesort").reset_index(drop=True)
    for column in [name for name in service_rows.columns if name.startswith("next_year_")]:
        service_rows[column] = np.nan
    service_rows["has_target"] = False

    return PreparedSplit(
        spec=spec,
        training_rows=train,
        service_scoring_rows=service_rows,
        realized_outcomes=realized,
        panel_rows=int(len(panel)),
        excluded_missing_outcome=excluded,
    )


def _load_service_module(repo_root: Path) -> ModuleType:
    """Load the real backend service after applying its documented root override."""
    backend = str(ROOT / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    previous = os.environ.get("RESEARCH_REPO_ROOT")
    os.environ["RESEARCH_REPO_ROOT"] = str(repo_root)
    try:
        module_name = f"_financeiq_serving_eval_{hashlib.sha256(str(repo_root).encode()).hexdigest()[:12]}"
        spec = importlib.util.spec_from_file_location(module_name, SERVICE_FILE)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load real service module from {SERVICE_FILE}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        if previous is None:
            os.environ.pop("RESEARCH_REPO_ROOT", None)
        else:
            os.environ["RESEARCH_REPO_ROOT"] = previous

    for function_name in ("train_parameters", "run_forecast"):
        function = getattr(module, function_name, None)
        source = Path(inspect.getsourcefile(function) or "").resolve() if function else None
        if function is None or source != SERVICE_FILE.resolve():
            raise RuntimeError(
                f"R3-SERV-01 must invoke {SERVICE_FILE}::{function_name}; got {source}"
            )
    return module


def invoke_loaded_service(
    service: ModuleType,
    spec: SplitSpec,
    *,
    top_n: int = TOP_N,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Call the two supported service functions; contains no scoring implementation."""
    trained = service.train_parameters(
        train_year_from=min(spec.train_feature_years),
        train_year_to=max(spec.train_feature_years),
        top_n=top_n,
        target_mode=service.TARGET_MODE_FINALIZED,
    )
    weights = {
        parameter["name"]: parameter["weight"]
        for parameter in trained["top_parameters"]
    }
    if not weights:
        raise ValueError(f"{spec.name} service returned no trained weights")
    scored = service.run_forecast(
        year=spec.test_feature_year,
        trained_weights=weights,
        risk_level="medium",
        user_type="individual",
    )
    return trained, scored


def invoke_real_service(prepared: PreparedSplit) -> tuple[dict[str, Any], dict[str, Any]]:
    """Expose one split through RESEARCH_REPO_ROOT, then invoke the unchanged service."""
    with tempfile.TemporaryDirectory(prefix=f"financeiq-{TASK_ID.lower()}-") as tmp:
        root = Path(tmp)
        clean = root / "data" / "trusted_clean"
        clean.mkdir(parents=True)
        prepared.training_rows.to_csv(
            clean / "modeling_dataset_training_2020_2025.csv",
            index=False,
            float_format="%.17g",
            lineterminator="\n",
        )
        prepared.service_scoring_rows.to_csv(
            clean / "modeling_dataset_public_2020_2025.csv",
            index=False,
            float_format="%.17g",
            lineterminator="\n",
        )
        prepared.service_scoring_rows.to_csv(
            clean / "modeling_dataset_2020_2025.csv",
            index=False,
            float_format="%.17g",
            lineterminator="\n",
        )
        service = _load_service_module(root)
        return invoke_loaded_service(service, prepared.spec)


def predictions_from_service(
    prepared: PreparedSplit,
    scored: dict[str, Any],
) -> pd.DataFrame:
    """Join service scores to held-out outcomes without changing service ordering."""
    items = scored.get("items")
    if not isinstance(items, list):
        raise ValueError(f"{prepared.spec.name} service response has no items list")
    if int(scored.get("year", -1)) != prepared.spec.test_feature_year:
        raise ValueError(f"{prepared.spec.name} service response year mismatch")
    if int(scored.get("stock_count", -1)) != len(items):
        raise ValueError(f"{prepared.spec.name} service stock_count mismatch")

    service_frame = pd.DataFrame(
        [
            {
                "ticker": str(item["ticker"]).strip().upper(),
                "y_pred": float(item["score"]),
                "service_rank": int(item["rank"]),
            }
            for item in items
        ]
    )
    if service_frame.duplicated("ticker").any():
        raise ValueError(f"{prepared.spec.name} service returned duplicate tickers")
    expected = set(prepared.realized_outcomes["ticker"])
    if set(service_frame["ticker"]) != expected:
        raise ValueError(f"{prepared.spec.name} service-scored cohort differs from canonical cohort")
    if not np.isfinite(service_frame["y_pred"].to_numpy(float)).all():
        raise ValueError(f"{prepared.spec.name} service returned non-finite scores")

    rows = service_frame.merge(
        prepared.realized_outcomes[["ticker", "y_true"]],
        on="ticker",
        how="left",
        validate="one_to_one",
    ).sort_values("service_rank", kind="mergesort")
    rows.insert(1, "year", prepared.spec.test_target_year)
    rows.insert(2, "model", MODEL_NAME)
    return rows[["ticker", "year", "model", "y_true", "y_pred"]].reset_index(drop=True)


def analyze_serving_predictions(
    predictions: pd.DataFrame,
    *,
    permutations: int = PERMUTATIONS,
    bootstraps: int = BOOTSTRAPS,
    seed: int = RANDOM_SEED,
) -> dict[str, Any]:
    """Return an explicit state before delegating valid data to canonical statistics."""
    required = {"ticker", "year", "model", "y_true", "y_pred", "split"}
    missing = required - set(predictions.columns)
    if missing:
        raise ValueError(f"serving predictions missing columns: {sorted(missing)}")
    if predictions.duplicated(["ticker", "year", "model"]).any():
        raise ValueError("serving predictions contain duplicate ticker/year/model rows")
    if predictions[["y_true", "y_pred"]].isna().any().any():
        return {
            "status": "insufficient_data",
            "reason": "missing outcome or service score remains after eligibility filtering",
        }
    if not np.isfinite(predictions[["y_true", "y_pred"]].to_numpy(float)).all():
        return {"status": "insufficient_data", "reason": "non-finite outcome or service score"}
    for split, group in predictions.groupby("split", sort=True):
        if len(group) < 3:
            return {
                "status": "insufficient_data",
                "reason": f"{split} has fewer than three eligible rows",
            }
        if group["y_true"].nunique(dropna=True) < 2:
            return {
                "status": "insufficient_data",
                "reason": f"{split} realized outcome is constant; Spearman IC is undefined",
            }
        if group["y_pred"].nunique(dropna=True) < 2:
            return {
                "status": "insufficient_data",
                "reason": f"{split} service output is constant; Spearman IC is undefined",
            }
    analysis = significance.analyze_model(
        predictions,
        permutations=permutations,
        bootstraps=bootstraps,
        seed=seed,
    )
    return {"status": "estimated", **analysis}


def format_conclusion(analysis: dict[str, Any]) -> str:
    if analysis.get("status") != "estimated":
        raise ValueError("Pre-committed numerical conclusion requires an estimated analysis")
    pooled = analysis["pooled"]
    ci = pooled["bootstrap_ci_95"]
    p_value = pooled["permutation_p_value_two_sided"]
    distinguishable = bool(p_value < 0.05)
    return (
        "The user-facing serving heuristic's walk-forward IC is "
        f"{pooled['observed_ic']:.3f} (95% CI [{ci[0]:.3f},{ci[1]:.3f}], "
        f"permutation p={p_value:.4f}); this "
        f"{'is' if distinguishable else 'is not'} distinguishable from the within-year null, "
        "and in either case does not establish investment value, implementability, or a "
        "reliable predictive edge."
    )


def _clean_manifest_of_record() -> Path:
    leaderboard_sha = _sha256(CANONICAL_LEADERBOARD)
    candidates = []
    for path in sorted((ROOT / "experiments" / "results" / "runs").glob("*/manifest.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("git", {}).get("dirty") is not False:
            continue
        if any(
            item.get("path") == "leaderboard.csv" and item.get("sha256") == leaderboard_sha
            for item in payload.get("artifacts", [])
        ):
            candidates.append(path)
    if not candidates:
        raise ValueError("No clean reproducibility manifest matches the canonical leaderboard")
    return candidates[-1]


def load_six_model_family_context(path: Path = CANONICAL_SIGNIFICANCE) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    multiplicity = report.get("analysis", {}).get("multiplicity", {})
    family = tuple(multiplicity.get("family", []))
    if family != tuple(significance.ML_MODELS):
        raise ValueError("Canonical significance report does not contain the prespecified six-model family")
    model_rows = []
    by_name = {row["model"]: row for row in report.get("models", [])}
    for model in family:
        pooled = by_name[model]["pooled"]
        model_rows.append(
            {
                "model": model,
                "pooled_ic": pooled["observed_ic"],
                "raw_permutation_p_value": pooled["permutation_p_value_two_sided"],
                "bonferroni_adjusted_p_value": pooled["bonferroni_adjusted_p_value"],
                "significant_fwer_0_05": pooled["significant_fwer_0_05"],
            }
        )
    return {
        "scope": "separate canonical ML family context; the serving heuristic is not a seventh model",
        "source": path.relative_to(ROOT).as_posix(),
        "method": multiplicity["method"],
        "family_size": multiplicity["family_size"],
        "family": list(family),
        "models": model_rows,
        "canonical_conclusion": report["headline"]["conclusion"],
    }


def _source_artifacts() -> list[dict[str, Any]]:
    manifest = _clean_manifest_of_record()
    sources = [
        _source_record(SERVICE_FILE, role="authoritative serving implementation invoked read-only"),
        _source_record(Path(__file__), role="R3-SERV-01 isolated evaluation harness"),
        _source_record(ROOT / "experiments" / "run_experiments.py", role="canonical split definitions"),
        _source_record(ROOT / "experiments" / "significance.py", role="canonical Spearman and resampling treatment"),
        _source_record(MODELING_DATASET, role="raw feature-year and prior-outcome input"),
        _source_record(CANONICAL_LEADERBOARD, role="protected canonical leaderboard"),
        _source_record(CANONICAL_SIGNIFICANCE, role="separate six-model family context"),
        _source_record(manifest, role="current clean reproducibility manifest of record"),
    ]
    sources.extend(
        _source_record(path, role=f"canonical evaluated cohort and outcome reference for {year}")
        for year, path in sorted(CANONICAL_PREDICTIONS.items())
    )
    return sources


def build_report(
    analysis: dict[str, Any],
    split_records: list[dict[str, Any]],
) -> dict[str, Any]:
    if analysis.get("status") != "estimated":
        raise ValueError(f"Production serving evaluation is {analysis.get('status')}: {analysis.get('reason')}")
    pooled = analysis["pooled"]
    conclusion = format_conclusion(analysis)
    return {
        "schema_version": "1.0.0",
        "task": TASK_ID,
        "status": "estimated",
        "service_path_parity": {
            "approximation_or_reimplementation_used": False,
            "invocation_mechanism": (
                "The unchanged backend service is loaded against an isolated temporary data root "
                "through the documented RESEARCH_REPO_ROOT override."
            ),
            "functions_invoked": list(SERVICE_FUNCTIONS),
            "test_outcomes_visible_to_training_or_scoring": False,
        },
        "evaluation_design": {
            "cohort": (
                "81-ticker internal training universe; exact canonical eligible evaluation panel "
                "of 80 tickers per target year"
            ),
            "return_basis": "nominal TRY T+1 realized return",
            "statistic": "equal-weighted mean of within-year Spearman ICs with average ranks for ties",
            "splits": split_records,
            "missing_data": (
                "Missing features remain null and follow run_forecast omission/confidence behavior; "
                "missing outcomes are excluded before within-year service percentiles are computed."
            ),
            "deterministic_ties": (
                "The eligible scoring panel is ticker-sorted before run_forecast; the service's "
                "stable score sort and ordinal rank assignment are retained unchanged."
            ),
        },
        "statistical_treatment": {
            "permutation": "two-sided; realized outcomes shuffled independently within each test year",
            "bootstrap": "tickers resampled with replacement independently within each test year",
            "permutations": PERMUTATIONS,
            "bootstraps": BOOTSTRAPS,
            "seed": RANDOM_SEED,
            "alpha_two_sided": 0.05,
        },
        "serving_result": {
            "test_label": SINGLE_TEST_LABEL,
            "pooled_ic": pooled["observed_ic"],
            "bootstrap_ci_95": pooled["bootstrap_ci_95"],
            "raw_permutation_p_value_two_sided": pooled["permutation_p_value_two_sided"],
            "distinguishable_from_within_year_null_0_05": bool(
                pooled["permutation_p_value_two_sided"] < 0.05
            ),
            "exploratory_by_year": analysis["exploratory_by_split"],
            "conclusion": conclusion,
        },
        "six_model_family_context": load_six_model_family_context(),
        "source_artifacts": _source_artifacts(),
        "artifact_ownership": {
            "owner": REGENERATION_COMMAND,
            "regeneration_command": REGENERATION_COMMAND,
            "hand_edit_forbidden": True,
            "generated_artifacts": [
                *(path.relative_to(ROOT).as_posix() for _, path in sorted(PREDICTION_OUTPUTS.items())),
                JSON_OUTPUT.relative_to(ROOT).as_posix(),
                MARKDOWN_OUTPUT.relative_to(ROOT).as_posix(),
            ],
        },
        "claim_safety": {
            "precommitted_conclusion": conclusion,
            "mcc_conclusion_changed": False,
            "investment_value_established": False,
            "implementability_established": False,
            "reliable_predictive_edge_established": False,
            "negative_result_interpreted_as_contrarian": False,
            "statement": (
                "One prespecified retrospective serving-path test cannot establish investment "
                "value, implementability, or a reliable predictive edge."
            ),
        },
        "limitations": [
            "Only three target years are observed, with 80 eligible tickers per year; estimates remain low-power and noisy.",
            "The cohort is retrospectively fixed and is not verified point-in-time BIST100 membership; survivorship and universe-selection look-ahead risks remain.",
            "Missing feature values remain null and reduce service coverage; no value is fabricated or imputed by this harness.",
            "Rows without realized outcomes are excluded and reported; the result does not generalize to those missing observations.",
            "Outcomes are nominal TRY returns from one unusual macro regime; regime robustness and economic implementation are not established.",
            "Exact artifact reproduction is numerical-environment-qualified even though seeded same-environment reruns are byte-deterministic.",
            "The raw serving p-value belongs to one prespecified test outside the six-model Bonferroni family and is not family-corrected.",
            "Research support only; not investment advice.",
        ],
        "independent_review": {
            "status": "PENDING",
            "required_reviewer": "Fable 5 in a separate context/model family from the implementer",
            "handoff": REVIEW_HANDOFF,
            "merge_ready": False,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    result = report["serving_result"]
    lines = [
        f"# Serving-heuristic walk-forward evaluation ({TASK_ID})",
        "",
        f"**Conclusion:** {result['conclusion']}",
        "",
        f"**Test framing:** {result['test_label']}.",
        "",
        "## Real service path invoked",
        "",
        *[f"- `{function}`" for function in report["service_path_parity"]["functions_invoked"]],
        "",
        report["service_path_parity"]["invocation_mechanism"],
        "No heuristic or scoring formula is copied into the experiment harness, and realized test outcomes are joined only after scoring.",
        "",
        "## Walk-forward design and cohort",
        "",
        "| Split | Training feature years | Training target years | Test feature year | Target year | Training n | Panel n | Eligible n | Missing-outcome exclusions |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for split in report["evaluation_design"]["splits"]:
        lines.append(
            f"| {split['name']} | {', '.join(map(str, split['train_feature_years']))} | "
            f"{', '.join(map(str, split['train_target_years']))} | {split['test_feature_year']} | "
            f"{split['test_target_year']} | {split['training_rows']} | {split['panel_rows']} | "
            f"{split['eligible_rows']} | {', '.join(split['excluded_missing_outcome']) or 'none'} |"
        )
    lines.extend(
        [
            "",
            report["evaluation_design"]["missing_data"],
            "",
            "Within each target year, the service score is compared with realized nominal-TRY T+1 outcomes using Spearman IC. The pooled statistic gives each year equal weight.",
            "",
            "## Serving result",
            "",
            f"- Pooled IC: **{result['pooled_ic']:.3f}**",
            f"- Bootstrap 95% CI: **[{result['bootstrap_ci_95'][0]:.3f}, {result['bootstrap_ci_95'][1]:.3f}]**",
            f"- Raw two-sided within-year permutation p-value: **{result['raw_permutation_p_value_two_sided']:.4f}**",
            f"- Treatment: {report['statistical_treatment']['permutations']:,} permutations and {report['statistical_treatment']['bootstraps']:,} bootstraps, seed {report['statistical_treatment']['seed']}",
            "",
            "This raw p-value is not family-corrected and must not be presented as such.",
            "",
            "### Exploratory per-year IC",
            "",
            "| Split | Target year | n | IC | Raw permutation p | Bootstrap 95% CI |",
            "| --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for split in result["exploratory_by_year"]:
        ci = split["bootstrap_ci_95"]
        lines.append(
            f"| {split['split']} | {split['year']} | {split['n']} | {split['observed_ic']:.3f} | "
            f"{split['permutation_p_value_two_sided']:.4f} | [{ci[0]:.3f}, {ci[1]:.3f}] |"
        )
    lines.extend(
        [
            "",
            "## Separate six-model ML family context",
            "",
            report["six_model_family_context"]["scope"].capitalize() + ".",
            "",
            "| Canonical ML model | Pooled IC | Raw p | Bonferroni p | FWER significant |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for model in report["six_model_family_context"]["models"]:
        lines.append(
            f"| {model['model']} | {model['pooled_ic']:.3f} | "
            f"{model['raw_permutation_p_value']:.4f} | "
            f"{model['bonferroni_adjusted_p_value']:.4f} | "
            f"{'yes' if model['significant_fwer_0_05'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            report["six_model_family_context"]["canonical_conclusion"],
            "",
            "## Source provenance",
            "",
            "| Source | SHA-256 | Role |",
            "| --- | --- | --- |",
        ]
    )
    for source in report["source_artifacts"]:
        lines.append(f"| `{source['path']}` | `{source['sha256']}` | {source['role']} |")
    lines.extend(
        [
            "",
            "## Limitations and claim boundary",
            "",
            *[f"- {limitation}" for limitation in report["limitations"]],
            "",
            report["claim_safety"]["statement"],
            "",
            "## Artifact ownership and review",
            "",
            f"Owner/regeneration command: `{report['artifact_ownership']['regeneration_command']}`. Generated files must not be hand-edited.",
            "",
            f"Independent review: **{report['independent_review']['status']}**. Handoff: `{report['independent_review']['handoff']}`. This task is not merge-ready until that separate review is performed.",
            "",
        ]
    )
    markdown = "\n".join(lines)
    forbidden = ("contrarian", "market-beating", "profitable trading", "validated alpha")
    if any(term in markdown.lower() for term in forbidden):
        raise ValueError("Generated serving report contains forbidden claim wording")
    return markdown


def _write_prediction_dump(frame: pd.DataFrame, path: Path) -> None:
    expected_columns = ["ticker", "year", "model", "y_true", "y_pred"]
    if list(frame.columns) != expected_columns:
        raise ValueError(f"prediction columns must be exactly {expected_columns}")
    frame.to_csv(path, index=False, float_format="%.17g", lineterminator="\n")


def run(
    *,
    modeling_path: Path = MODELING_DATASET,
    results_dir: Path = RESULTS_DIR,
) -> dict[str, Any]:
    modeling = load_modeling_dataset(modeling_path)
    prediction_frames: dict[int, pd.DataFrame] = {}
    split_records: list[dict[str, Any]] = []

    for spec in split_specs():
        reference = load_reference_cohort(CANONICAL_PREDICTIONS[spec.test_target_year], spec.test_target_year)
        prepared = prepare_split(modeling, reference, spec)
        trained, scored = invoke_real_service(prepared)
        predictions = predictions_from_service(prepared, scored)
        prediction_frames[spec.test_target_year] = predictions
        split_records.append(
            {
                "name": spec.name,
                "train_feature_years": list(spec.train_feature_years),
                "train_target_years": list(spec.train_target_years),
                "test_feature_year": spec.test_feature_year,
                "test_target_year": spec.test_target_year,
                "training_rows": int(trained["total_training_rows"]),
                "service_training_window": [
                    int(trained["train_year_from"]),
                    int(trained["train_year_to"]),
                ],
                "panel_rows": prepared.panel_rows,
                "eligible_rows": int(len(predictions)),
                "excluded_missing_outcome": list(prepared.excluded_missing_outcome),
                "selected_parameters": trained["top_parameters"],
                "prediction_artifact": f"experiments/results_serving_eval/predictions_serving_{spec.test_target_year}.csv",
            }
        )

    combined = pd.concat(
        [
            frame.assign(split=f"test_{year}")
            for year, frame in sorted(prediction_frames.items())
        ],
        ignore_index=True,
    )
    analysis = analyze_serving_predictions(combined)
    report = build_report(analysis, split_records)
    markdown = render_markdown(report)

    results_dir.mkdir(parents=True, exist_ok=True)
    for year, frame in sorted(prediction_frames.items()):
        _write_prediction_dump(frame, results_dir / f"predictions_serving_{year}.csv")
    (results_dir / JSON_OUTPUT.name).write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (results_dir / MARKDOWN_OUTPUT.name).write_text(markdown, encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()
    report = run(results_dir=args.results_dir)
    print(report["serving_result"]["conclusion"])
    print(f"Wrote {args.results_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
