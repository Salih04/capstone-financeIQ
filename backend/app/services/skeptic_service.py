"""Deterministic challenges to FinanceIQ ranking evidence.

The service reads committed artifacts only.  It does not calculate or alter a
score, and it keeps every finding separate from serving outputs.  Missing or
malformed evidence produces an ``insufficient_data`` check instead of an
inferred fact.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.paths import resolve_repo_root


REPO_ROOT = resolve_repo_root()
CLEAN_DIR = REPO_ROOT / "data" / "trusted_clean"
RESULTS_DIR = REPO_ROOT / "experiments" / "results"

PUBLIC_DATASET = CLEAN_DIR / "modeling_dataset_public_2020_2025.csv"
DATA_QUALITY_REPORT = CLEAN_DIR / "data_quality_report.json"
FROZEN_EVIDENCE = CLEAN_DIR / "frozen_column_evidence.json"
FEATURE_PASSPORTS = CLEAN_DIR / "feature_passports.json"
SIGNIFICANCE_REPORT = RESULTS_DIR / "significance_report.json"
UNIVERSE_AUDIT = REPO_ROOT / "docs" / "universe_audit.md"
CONFIDENCE_CONTRACT = REPO_ROOT / "model_confidence_contract.json"
PREDICTION_FILES = tuple(
    RESULTS_DIR / f"predictions_test_{year}.csv" for year in (2023, 2024, 2025)
)

PUBLIC_DATASET_SOURCE = "data/trusted_clean/modeling_dataset_public_2020_2025.csv"
QUALITY_SOURCE = "data/trusted_clean/data_quality_report.json"
FROZEN_SOURCE = "data/trusted_clean/frozen_column_evidence.json"
PASSPORT_SOURCE = "data/trusted_clean/feature_passports.json"
SIGNIFICANCE_SOURCE = "experiments/results/significance_report.json"
UNIVERSE_SOURCE = "docs/universe_audit.md"
CONTRACT_SOURCE = "model_confidence_contract.json"
METHODOLOGY_SOURCE = "METHODOLOGY.md"

FOOTER = (
    "**Surviving these checks means *not obviously broken*, not *predictive* — "
    "walk-forward IC remains ≈ 0 and no model survives family-wise correction.**"
)

_CHECK_IDS = (
    "staleness_frozen_probe",
    "missingness_attack",
    "instability_probe",
    "cohort_integrity_challenge",
    "universe_scale_reminder",
    "backtest_reminder",
)


def _evidence(fact: str, source_file: str) -> dict[str, str]:
    return {"fact": fact, "source_file": source_file}


def _check(
    check_id: str,
    verdict: str,
    evidence: list[dict[str, str]],
    severity: str,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "verdict": verdict,
        "evidence": evidence,
        "severity": severity,
    }


def _insufficient(check_id: str, source_file: str, reason: str) -> dict[str, Any]:
    return _check(
        check_id,
        "insufficient_data",
        [_evidence(f"Evidence unavailable: {reason}", source_file)],
        "high",
    )


def _is_populated(value: Any) -> bool:
    if value is None or (isinstance(value, str) and not value.strip()):
        return False
    try:
        return not bool(pd.isna(value))
    except (TypeError, ValueError):
        return True


def staleness_frozen_probe(
    latest_row: dict[str, Any] | None,
    quality_report: dict[str, Any] | None,
    frozen_evidence: dict[str, Any] | None,
    passports_artifact: dict[str, Any] | None,
) -> dict[str, Any]:
    """Challenge current inputs against rejected frozen paths and lineage gaps."""
    if latest_row is None:
        return _insufficient(
            _CHECK_IDS[0], PUBLIC_DATASET_SOURCE, "no public-universe row exists for this ticker"
        )
    if not quality_report or not isinstance(quality_report.get("feature_columns"), list):
        return _insufficient(_CHECK_IDS[0], QUALITY_SOURCE, "feature registry is missing")
    if not frozen_evidence or not isinstance(frozen_evidence.get("columns"), dict):
        return _insufficient(_CHECK_IDS[0], FROZEN_SOURCE, "frozen-column evidence is missing")
    if not passports_artifact or not isinstance(passports_artifact.get("passports"), list):
        return _insufficient(_CHECK_IDS[0], PASSPORT_SOURCE, "feature passports are missing")

    features = quality_report["feature_columns"]
    populated = sorted(name for name in features if _is_populated(latest_row.get(name)))
    frozen_remaining = set(quality_report.get("frozen_feature_columns_remaining", []))
    current_frozen = sorted(frozen_remaining.intersection(populated))
    legacy_name_overlap = sorted(set(frozen_evidence["columns"]).intersection(populated))

    passports = {
        item.get("name"): item
        for item in passports_artifact["passports"]
        if isinstance(item, dict) and item.get("name")
    }
    lineage_gaps = sorted(
        name
        for name in populated
        if name not in passports or passports[name].get("source_class") == "unknown"
    )

    evidence = [
        _evidence(
            f"The latest row ({int(latest_row['year'])}) has {len(populated)}/{len(features)} "
            f"populated feature inputs; {len(current_frozen)} are recorded as frozen features "
            "remaining in the accepted dataset.",
            QUALITY_SOURCE,
        ),
        _evidence(
            f"{len(legacy_name_overlap)} populated feature names also appear in the legacy "
            "frozen-column audit. Name overlap alone is not lineage; accepted replacement "
            "paths are documented by the quality report and passports.",
            FROZEN_SOURCE,
        ),
        _evidence(
            f"{len(lineage_gaps)} populated inputs have source_class=unknown or no passport"
            + (f": {', '.join(lineage_gaps)}." if lineage_gaps else "."),
            PASSPORT_SOURCE,
        ),
    ]
    if current_frozen:
        return _check(_CHECK_IDS[0], "fail", evidence, "high")
    if lineage_gaps:
        return _check(_CHECK_IDS[0], "warn", evidence, "moderate")
    return _check(_CHECK_IDS[0], "pass", evidence, "low")


def missingness_attack(
    latest_row: dict[str, Any] | None,
    quality_report: dict[str, Any] | None,
) -> dict[str, Any]:
    """Compare latest-row feature coverage with report-derived dataset coverage."""
    if latest_row is None:
        return _insufficient(
            _CHECK_IDS[1], PUBLIC_DATASET_SOURCE, "no public-universe row exists for this ticker"
        )
    if not quality_report:
        return _insufficient(_CHECK_IDS[1], QUALITY_SOURCE, "quality report is missing")
    features = quality_report.get("feature_columns")
    missingness = quality_report.get("missingness")
    if not isinstance(features, list) or not features or not isinstance(missingness, dict):
        return _insufficient(_CHECK_IDS[1], QUALITY_SOURCE, "coverage statistics are incomplete")
    if any(name not in missingness for name in features):
        return _insufficient(
            _CHECK_IDS[1], QUALITY_SOURCE, "one or more feature coverage statistics are absent"
        )

    populated = sum(_is_populated(latest_row.get(name)) for name in features)
    coverage = populated / len(features)
    threshold = sum(1.0 - float(missingness[name]) for name in features) / len(features)
    verdict = "warn" if coverage < threshold else "pass"
    return _check(
        _CHECK_IDS[1],
        verdict,
        [
            _evidence(
                f"Latest-row feature coverage is {populated}/{len(features)} ({coverage:.4f}) "
                f"for year {int(latest_row['year'])}.",
                PUBLIC_DATASET_SOURCE,
            ),
            _evidence(
                f"Warning threshold is {threshold:.4f}, the arithmetic mean of the report's "
                "per-feature populated fractions; it is artifact-derived, not an uncited "
                "heuristic.",
                QUALITY_SOURCE,
            ),
        ],
        "moderate" if verdict == "warn" else "low",
    )


def instability_probe(
    ticker: str,
    prediction_rows: pd.DataFrame | None,
    model_kinds: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Measure within-split rank spread across persisted model outputs."""
    if prediction_rows is None or prediction_rows.empty:
        return _insufficient(_CHECK_IDS[2], SIGNIFICANCE_SOURCE, "evaluation rows are missing")
    required = {"ticker", "year", "model"}
    if not required.issubset(prediction_rows.columns) or not {
        "rank",
        "y_pred",
    }.intersection(prediction_rows.columns):
        return _insufficient(_CHECK_IDS[2], SIGNIFICANCE_SOURCE, "evaluation schema is incomplete")

    value_column = "rank" if "rank" in prediction_rows.columns else "y_pred"
    frame = prediction_rows[sorted(required) + [value_column]].copy()
    frame["ticker"] = frame["ticker"].astype(str).str.strip().str.upper()
    frame[value_column] = pd.to_numeric(frame[value_column], errors="coerce")
    frame = frame.dropna(subset=["year", "model", value_column])
    if value_column == "y_pred":
        frame["rank"] = frame.groupby(["year", "model"])["y_pred"].rank(
            ascending=False, method="average"
        )
    ticker_rows = frame[frame["ticker"] == ticker]
    if ticker_rows.empty:
        return _insufficient(
            _CHECK_IDS[2], SIGNIFICANCE_SOURCE, "ticker is absent from persisted evaluation rows"
        )

    summaries: list[dict[str, Any]] = []
    for year, group in ticker_rows.groupby("year"):
        if group["model"].nunique() < 2:
            continue
        field_sizes = frame[frame["year"] == year].groupby("model")["ticker"].nunique()
        field_size = int(field_sizes.min())
        low = group.sort_values(["rank", "model"]).iloc[0]
        high = group.sort_values(["rank", "model"]).iloc[-1]
        summaries.append(
            {
                "year": int(year),
                "models": int(group["model"].nunique()),
                "field_size": field_size,
                "threshold": field_size / 2.0,
                "min_rank": float(low["rank"]),
                "min_model": str(low["model"]),
                "max_rank": float(high["rank"]),
                "max_model": str(high["model"]),
                "spread": float(high["rank"] - low["rank"]),
            }
        )
    if not summaries:
        return _insufficient(
            _CHECK_IDS[2], SIGNIFICANCE_SOURCE, "fewer than two model ranks are available per split"
        )

    worst = max(summaries, key=lambda item: (item["spread"], item["year"]))
    unstable = any(item["spread"] > item["threshold"] for item in summaries)
    model_kinds = model_kinds or {}
    low_kind = model_kinds.get(worst["min_model"], "unclassified")
    high_kind = model_kinds.get(worst["max_model"], "unclassified")
    split_facts = "; ".join(
        f"{item['year']}: spread {item['spread']:.1f}/{item['field_size']}"
        for item in sorted(summaries, key=lambda item: item["year"])
    )
    split_evidence = [
        _evidence(
            f"{item['year']} within-split rank spread is {item['spread']:.1f} across "
            f"{item['models']} models in a {item['field_size']}-ticker field; a spread "
            "greater than half the field triggers this deterministic warning.",
            f"experiments/results/predictions_test_{item['year']}.csv",
        )
        for item in sorted(summaries, key=lambda item: item["year"])
    ]
    return _check(
        _CHECK_IDS[2],
        "warn" if unstable else "pass",
        [
            _evidence(
                f"Within-split rank spreads across models are {split_facts}.",
                f"experiments/results/predictions_test_{worst['year']}.csv",
            ),
            *split_evidence,
            _evidence(
                f"The widest span is {worst['min_rank']:.1f} ({worst['min_model']}, {low_kind}) "
                f"to {worst['max_rank']:.1f} ({worst['max_model']}, {high_kind}) in "
                f"{worst['year']}; this is disagreement among evaluation outputs, not a "
                "separate score for the ticker.",
                f"experiments/results/predictions_test_{worst['year']}.csv",
            ),
        ],
        "high" if unstable else "low",
    )


_GAP_ROW = re.compile(r"^\|\s*([A-Z0-9.]+)\s*\|\s*([0-9, ]+)\s*\|$", re.MULTILINE)


def cohort_integrity_challenge(ticker: str, audit_text: str | None) -> dict[str, Any]:
    """Surface retrospective-cohort and observed price-coverage limitations."""
    if not audit_text:
        return _insufficient(_CHECK_IDS[3], UNIVERSE_SOURCE, "universe audit is missing")
    normalized_audit = re.sub(r"\s+", " ", audit_text.replace("**", ""))
    required_phrases = (
        "retrospectively fixed repository cohort",
        "unresolved survivorship",
        "does not prove why an observation is missing",
    )
    if any(phrase not in normalized_audit for phrase in required_phrases):
        return _insufficient(
            _CHECK_IDS[3],
            UNIVERSE_SOURCE,
            "required cohort or missing-evidence findings are absent",
        )

    gaps = {
        match.group(1): [int(year.strip()) for year in match.group(2).split(",")]
        for match in _GAP_ROW.finditer(audit_text)
    }
    evidence = [
        _evidence(
            "The configured cohort is retrospective rather than verified point-in-time "
            "membership, leaving survivorship and universe-selection look-ahead risk unresolved.",
            UNIVERSE_SOURCE,
        )
    ]
    if ticker in gaps:
        evidence.append(
            _evidence(
                f"Observed public price coverage is missing for {ticker} in "
                f"{', '.join(str(year) for year in gaps[ticker])}; the repository does not "
                "establish why those observations are missing.",
                UNIVERSE_SOURCE,
            )
        )
    else:
        evidence.append(
            _evidence(
                f"No ticker-specific price gap is listed for {ticker}; complete observed price "
                "coverage would still not establish historical constituent membership.",
                UNIVERSE_SOURCE,
            )
        )
    evidence.append(
        _evidence(
            "Selection rules, membership-effective dates, security-status history, and outcomes "
            "under an entry/exit-aware universe are missing evidence and remain unknown.",
            UNIVERSE_SOURCE,
        )
    )
    return _check(_CHECK_IDS[3], "warn", evidence, "high" if ticker in gaps else "moderate")


def universe_scale_reminder(
    significance_report: dict[str, Any] | None,
    public_ticker_count: int | None,
    confidence_contract: dict[str, Any] | None,
) -> dict[str, Any]:
    """Report sample scale, detectable-IC bands, and confidence-language limits."""
    if not significance_report:
        return _insufficient(_CHECK_IDS[4], SIGNIFICANCE_SOURCE, "significance report is missing")
    try:
        evaluated_values = significance_report["analysis"]["evaluated_tickers_per_model_split"]
        designs = {
            item["design_id"]: item for item in significance_report["power_analysis"]["designs"]
        }
        one_year = designs["current_one_split"]
        three_year = designs["current_three_year_pooled"]
        definition = significance_report["power_analysis"]["definitions"]["detectable_ic"]
        reliable_edge = confidence_contract["evidence_state"]["reliable_predictive_edge_observed"]
    except (KeyError, TypeError):
        return _insufficient(
            _CHECK_IDS[4],
            SIGNIFICANCE_SOURCE,
            "power, sample-size, or contract fields are incomplete",
        )
    if public_ticker_count is None or not evaluated_values:
        return _insufficient(
            _CHECK_IDS[4],
            PUBLIC_DATASET_SOURCE,
            "public or evaluated-universe count is unavailable",
        )

    evaluated = (
        int(evaluated_values[0])
        if len(evaluated_values) == 1
        else [int(value) for value in evaluated_values]
    )
    return _check(
        _CHECK_IDS[4],
        "warn",
        [
            _evidence(
                f"The configured public artifact contains {public_ticker_count} tickers.",
                PUBLIC_DATASET_SOURCE,
            ),
            _evidence(
                f"Persisted evaluation uses {evaluated} rows per model and split; the 80-row "
                f"detectable |IC| bands are {one_year['analytic_minimum_detectable_abs_ic']:.3f} "
                f"for one year and {three_year['analytic_minimum_detectable_abs_ic']:.3f} for "
                "the three-year design.",
                SIGNIFICANCE_SOURCE,
            ),
            _evidence(
                f"The report defines detectable IC as {definition}. These IC bands are not "
                "rank-position thresholds, so a ticker-level rank difference is not resolved by "
                "this calculation.",
                SIGNIFICANCE_SOURCE,
            ),
            _evidence(
                "The confidence contract records reliable_predictive_edge_observed="
                f"{str(reliable_edge).lower()}; "
                "confidence wording must remain diagnostic and cannot upgrade this evidence state.",
                CONTRACT_SOURCE,
            ),
        ],
        "high",
    )


def backtest_reminder(significance_report: dict[str, Any] | None) -> dict[str, Any]:
    """Always-last family-wise result and baseline interpretation."""
    if not significance_report:
        return _insufficient(_CHECK_IDS[5], SIGNIFICANCE_SOURCE, "significance report is missing")
    try:
        headline = significance_report["headline"]["conclusion"]
        baseline = next(
            model
            for model in significance_report["models"]
            if model.get("model") == "baseline_equal_weight"
        )
        ml_models = [model for model in significance_report["models"] if model.get("kind") == "ml"]
        none_survive = all(model["pooled"]["significant_fwer_0_05"] is False for model in ml_models)
        baseline_ic = float(baseline["pooled"]["observed_ic"])
    except (KeyError, StopIteration, TypeError):
        return _insufficient(
            _CHECK_IDS[5],
            SIGNIFICANCE_SOURCE,
            "headline, baseline, or ML family evidence is incomplete",
        )
    if not ml_models or not none_survive:
        return _insufficient(
            _CHECK_IDS[5],
            SIGNIFICANCE_SOURCE,
            "the committed family-wise conclusion is inconsistent",
        )

    return _check(
        _CHECK_IDS[5],
        "warn",
        [
            _evidence(headline, SIGNIFICANCE_SOURCE),
            _evidence(
                f"The equal-weight baseline pooled IC {baseline_ic:.3f} is reported as descriptive "
                "baseline context outside the six-model ML correction family, not as a validated "
                "edge.",
                METHODOLOGY_SOURCE,
            ),
        ],
        "high",
    )


@lru_cache(maxsize=16)
def _load_json_cached(path: str, mtime: float) -> dict[str, Any]:
    del mtime
    with Path(path).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("expected a JSON object")
    return value


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return _load_json_cached(str(path), path.stat().st_mtime)
    except (OSError, ValueError, json.JSONDecodeError):
        return None


@lru_cache(maxsize=8)
def _load_csv_cached(path: str, mtime: float) -> pd.DataFrame:
    del mtime
    return pd.read_csv(path)


def _load_csv(path: Path) -> pd.DataFrame | None:
    if not path.is_file():
        return None
    try:
        return _load_csv_cached(str(path), path.stat().st_mtime).copy()
    except (OSError, ValueError, pd.errors.ParserError):
        return None


@lru_cache(maxsize=4)
def _load_text_cached(path: str, mtime: float) -> str:
    del mtime
    return Path(path).read_text(encoding="utf-8")


def _load_text(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        return _load_text_cached(str(path), path.stat().st_mtime)
    except OSError:
        return None


def _latest_public_row(ticker: str, frame: pd.DataFrame | None) -> dict[str, Any] | None:
    if frame is None or not {"ticker", "year"}.issubset(frame.columns):
        return None
    rows = frame[frame["ticker"].astype(str).str.strip().str.upper() == ticker].copy()
    if rows.empty:
        return None
    rows["year"] = pd.to_numeric(rows["year"], errors="coerce")
    rows = rows.dropna(subset=["year"]).sort_values("year")
    return None if rows.empty else rows.iloc[-1].to_dict()


@lru_cache(maxsize=4)
def _prediction_ranks_cached(signature: tuple[tuple[str, float], ...]) -> pd.DataFrame:
    frames = [pd.read_csv(path) for path, _mtime in signature]
    frame = pd.concat(frames, ignore_index=True)
    frame["ticker"] = frame["ticker"].astype(str).str.strip().str.upper()
    frame["y_pred"] = pd.to_numeric(frame["y_pred"], errors="coerce")
    frame["rank"] = frame.groupby(["year", "model"])["y_pred"].rank(
        ascending=False, method="average"
    )
    return frame


def _prediction_rows() -> pd.DataFrame | None:
    if any(not path.is_file() for path in PREDICTION_FILES):
        return None
    try:
        signature = tuple((str(path), path.stat().st_mtime) for path in PREDICTION_FILES)
        return _prediction_ranks_cached(signature).copy()
    except (OSError, ValueError, pd.errors.ParserError):
        return None


def skeptic_report(ticker: str) -> dict[str, Any]:
    """Build the six-check report from repository artifacts only."""
    ticker = str(ticker).strip().upper()
    if not ticker or not re.fullmatch(r"[A-Z0-9.]{1,16}", ticker):
        raise ValueError("ticker must contain 1-16 uppercase letters, digits, or dots")

    public_frame = _load_csv(PUBLIC_DATASET)
    latest_row = _latest_public_row(ticker, public_frame)
    quality = _load_json(DATA_QUALITY_REPORT)
    frozen = _load_json(FROZEN_EVIDENCE)
    passports = _load_json(FEATURE_PASSPORTS)
    significance = _load_json(SIGNIFICANCE_REPORT)
    contract = _load_json(CONFIDENCE_CONTRACT)
    audit_text = _load_text(UNIVERSE_AUDIT)
    predictions = _prediction_rows()

    model_kinds = {
        model.get("model"): model.get("kind", "unclassified")
        for model in (significance or {}).get("models", [])
        if isinstance(model, dict) and model.get("model")
    }
    public_count = None
    if public_frame is not None and "ticker" in public_frame.columns:
        public_count = int(public_frame["ticker"].astype(str).str.upper().nunique())

    checks = [
        staleness_frozen_probe(latest_row, quality, frozen, passports),
        missingness_attack(latest_row, quality),
        instability_probe(ticker, predictions, model_kinds),
        cohort_integrity_challenge(ticker, audit_text),
        universe_scale_reminder(significance, public_count, contract),
        backtest_reminder(significance),
    ]
    return {"ticker": ticker, "checks": checks, "footer": FOOTER}
