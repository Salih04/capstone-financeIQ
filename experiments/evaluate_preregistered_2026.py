"""Inert evaluator for the pre-registered 2026 forward-outcome protocol.

The evaluator exists before outcomes and therefore returns
``outcome_data_absent`` today. If a future manually sourced outcome file is
present, it validates the complete frozen cohort, auditable Yahoo adjusted-close
inputs, per-row provenance, and return recomputation before calling either
Spearman IC or the one seeded permutation test.

Power disclosure is descriptive context selected from the pre-frozen n=30..40
Fisher-z table. It is not a second test, a pass/fail threshold, or evidence of a
reliable predictive edge. See ``docs/PREREGISTERED_2026_EVALUATION.md``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd

from experiments import significance
from experiments.freeze_forward_ranking import (
    FROZEN_RANKING_PATH,
    PINNED_FROZEN_RANKING_SHA256,
    PROTOCOL_DOCUMENT,
    PROTOCOL_IDENTIFIER,
    ROOT,
    TARGET_YEAR,
    TASK_ID,
)

# ---------------------------------------------------------------------------
# Committed anchors and the predeclared future outcome contract
# ---------------------------------------------------------------------------
EXPECTED_FROZEN_RANKING_SHA256 = PINNED_FROZEN_RANKING_SHA256
OUTCOME_FILE = ROOT / "data" / "trusted_raw" / "realized_2026_returns.csv"

START_YEAR = 2025
END_YEAR = 2026
MIN_USABLE_ROWS = 30
PRICE_BASIS = "yahoo_adjusted_close"
CURRENCY = "TRY"
OUTCOME_SOURCE = "yahoo_chart_api"
VALUATION_DATE_RULE = "last_valid_quote_on_or_before_dec31_within_dec20_dec31"
RETURN_CONVENTION = "nominal_try_calendar_year_adjusted_close_return_pct"
RETURN_TOLERANCE_PCT = 1e-6

OUTCOME_REQUIRED_COLUMNS = (
    "ticker",
    "target_year",
    "realized_return_pct",
    "start_adjusted_close_try",
    "end_adjusted_close_try",
    "start_price_date",
    "end_price_date",
    "price_basis",
    "currency",
    "valuation_date_rule",
    "return_convention",
    "source",
    "source_url_or_record_id",
    "as_of_date",
    "start_snapshot_sha256",
    "end_snapshot_sha256",
    "source_symbol",
    "symbol_mapping_note",
    "exclusion_reason",
)
OUTCOME_PROVENANCE_COLUMNS = (
    "source",
    "source_url_or_record_id",
    "as_of_date",
    "start_price_date",
    "end_price_date",
    "start_snapshot_sha256",
    "end_snapshot_sha256",
    "source_symbol",
)

PERMUTATION_SEED = significance.DEFAULT_SEED
PERMUTATIONS = significance.DEFAULT_PERMUTATIONS
ALPHA = significance.POWER_ALPHA
TARGET_POWER = significance.POWER_TARGET

# Precomputed with experiments.significance.minimum_detectable_ic using one
# split, alpha=0.05, target_power=0.80. Six decimals is the frozen disclosure
# precision; n=40 therefore reproduces the documented approximately 0.431.
DETECTABLE_ABS_IC_BY_USABLE_N = {
    30: 0.492355,
    31: 0.484960,
    32: 0.477886,
    33: 0.471110,
    34: 0.464614,
    35: 0.458377,
    36: 0.452383,
    37: 0.446618,
    38: 0.441066,
    39: 0.435716,
    40: 0.430555,
}
POWER_METHOD = (
    "two-sided Fisher z approximation for one within-year Spearman IC; "
    "variance 1/(n-3), alpha=0.05, target power=0.80"
)

REGENERATION_COMMAND = "make evaluate-forward-2026"
FUTURE_REPORT_PATH = FROZEN_RANKING_PATH.parent / "evaluation_2026_report.json"

STATE_ABSENT = "outcome_data_absent"
STATE_ESTIMATED = "estimated"
STATE_INSUFFICIENT = "insufficient_data"
REFUSAL_STATES = {
    "frozen_ranking_missing",
    "frozen_ranking_tampered",
    "protocol_identifier_mismatch",
    "outcome_schema_malformed",
    "duplicate_tickers",
    "unexpected_tickers",
    "wrong_target_year",
    "outcome_provenance_absent",
    "outcome_data_malformed",
    "return_recomputation_mismatch",
    STATE_INSUFFICIENT,
}

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def _blank(value: Any) -> bool:
    if value is None or pd.isna(value):
        return True
    return str(value).strip().lower() in {"", "nan", "none", "null"}


def _parse_iso_date(value: Any) -> dt.date | None:
    if _blank(value):
        return None
    try:
        return dt.date.fromisoformat(str(value).strip())
    except ValueError:
        return None


def check_frozen_ranking(
    frozen_path: Path = FROZEN_RANKING_PATH,
    *,
    expected_sha256: str = EXPECTED_FROZEN_RANKING_SHA256,
    expected_protocol: str = PROTOCOL_IDENTIFIER,
) -> dict[str, Any]:
    """Verify the frozen ranking checksum and protocol without mutating it."""
    if not frozen_path.is_file():
        return {
            "ok": False,
            "status": "frozen_ranking_missing",
            "reason": f"Frozen ranking not found at {_display_path(frozen_path)}",
        }
    actual = _sha256(frozen_path)
    if actual != expected_sha256:
        return {
            "ok": False,
            "status": "frozen_ranking_tampered",
            "reason": (
                "Frozen ranking checksum does not match the committed anchor; refusing "
                "to evaluate."
            ),
            "expected_sha256": expected_sha256,
            "actual_sha256": actual,
        }
    frame = pd.read_csv(frozen_path)
    identifiers = set(frame.get("protocol_identifier", pd.Series(dtype=str)).astype(str).unique())
    if identifiers != {expected_protocol}:
        return {
            "ok": False,
            "status": "protocol_identifier_mismatch",
            "reason": (
                f"Frozen ranking protocol identifier {sorted(identifiers)} does not match "
                f"the expected {expected_protocol!r}."
            ),
        }
    return {
        "ok": True,
        "status": "frozen_ranking_verified",
        "sha256": actual,
        "rows": int(len(frame)),
    }


def _membership_disclosure(
    frozen_tickers: Sequence[str],
    included_tickers: Sequence[str],
    exclusion_reasons: dict[str, str],
) -> dict[str, Any]:
    frozen = [str(t).strip().upper() for t in frozen_tickers]
    included_set = {str(t).strip().upper() for t in included_tickers}
    included = [ticker for ticker in frozen if ticker in included_set]
    excluded = [
        {
            "ticker": ticker,
            "reason": exclusion_reasons.get(ticker, "outcome_row_absent"),
        }
        for ticker in frozen
        if ticker not in included_set
    ]
    return {
        "frozen_cohort_size": len(frozen),
        "usable_cohort_size": len(included),
        "missing_outcome_count": len(excluded),
        "included_tickers": included,
        "excluded_tickers": excluded,
    }


def _validation_failure(status: str, reason: str, **details: Any) -> dict[str, Any]:
    return {"ok": False, "status": status, "reason": reason, **details}


def validate_outcomes(
    outcomes: pd.DataFrame,
    *,
    frozen_tickers: Sequence[str] | None = None,
    target_year: int = TARGET_YEAR,
    min_usable_rows: int = MIN_USABLE_ROWS,
) -> dict[str, Any]:
    """Validate future sourced outcomes before any statistical calculation.

    Ordinary missing returns remain null and are disclosed as exclusions.
    Non-numeric or infinite values, unexpected/duplicate tickers, unsupported
    conventions, missing usable-row provenance, and recomputation disagreement
    are malformed data and are refused.
    """
    if frozen_tickers is None:
        frozen_tickers = pd.read_csv(FROZEN_RANKING_PATH)["ticker"].tolist()
    frozen = [str(t).strip().upper() for t in frozen_tickers]
    frozen_set = set(frozen)

    missing_columns = [column for column in OUTCOME_REQUIRED_COLUMNS if column not in outcomes]
    if missing_columns:
        return _validation_failure(
            "outcome_schema_malformed",
            f"Outcome file is missing required columns: {missing_columns}",
            missing_columns=missing_columns,
        )

    frame = outcomes.copy()
    raw_tickers = frame["ticker"].copy()
    if raw_tickers.map(_blank).any():
        return _validation_failure(
            "outcome_data_malformed", "Outcome file contains an empty ticker.",
            reason_code="empty_ticker",
        )
    frame["ticker"] = raw_tickers.astype(str).str.strip().str.upper()

    if frame["ticker"].duplicated().any():
        duplicates = sorted(frame.loc[frame["ticker"].duplicated(keep=False), "ticker"].unique())
        return _validation_failure(
            "duplicate_tickers",
            f"Outcome file contains duplicate tickers: {duplicates}",
            duplicate_tickers=duplicates,
        )
    unexpected = sorted(set(frame["ticker"]) - frozen_set)
    if unexpected:
        return _validation_failure(
            "unexpected_tickers",
            f"Outcome file contains tickers outside the frozen cohort: {unexpected}",
            unexpected_tickers=unexpected,
        )

    target = pd.to_numeric(frame["target_year"], errors="coerce")
    target_valid = (
        target.notna()
        & np.isfinite(target.to_numpy(dtype=float, na_value=np.nan))
        & target.eq(target_year)
    )
    if not target_valid.all():
        return _validation_failure(
            "wrong_target_year",
            f"Every outcome row must declare target_year == {target_year}.",
        )

    raw_realized = frame["realized_return_pct"]
    null_return = raw_realized.map(_blank)
    realized = pd.to_numeric(raw_realized, errors="coerce")
    invalid_numeric = ~null_return & realized.isna()
    if invalid_numeric.any():
        tickers = frame.loc[invalid_numeric, "ticker"].tolist()
        return _validation_failure(
            "outcome_data_malformed",
            f"Non-numeric realized returns are malformed for: {tickers}",
            reason_code="non_numeric_realized_return",
        )
    non_finite = ~null_return & ~np.isfinite(realized.to_numpy(dtype=float, na_value=np.nan))
    if non_finite.any():
        tickers = frame.loc[non_finite, "ticker"].tolist()
        return _validation_failure(
            "outcome_data_malformed",
            f"Non-finite realized returns are malformed for: {tickers}",
            reason_code="non_finite_realized_return",
        )

    usable_mask = ~null_return
    usable = frame.loc[usable_mask].copy()
    usable["realized_return_pct"] = realized.loc[usable_mask].astype(float)

    for index, row in usable.iterrows():
        ticker = str(row["ticker"])
        missing_provenance = [
            column for column in OUTCOME_PROVENANCE_COLUMNS if _blank(row[column])
        ]
        if missing_provenance:
            return _validation_failure(
                "outcome_provenance_absent",
                f"Usable outcome row {ticker} lacks provenance fields: {missing_provenance}",
                ticker=ticker,
                missing_fields=missing_provenance,
            )
        for column in ("start_snapshot_sha256", "end_snapshot_sha256"):
            if not _SHA256_RE.fullmatch(str(row[column]).strip().lower()):
                return _validation_failure(
                    "outcome_provenance_absent",
                    f"Usable outcome row {ticker} lacks a valid {column}.",
                    ticker=ticker,
                    missing_fields=[column],
                )
        if str(row["source"]).strip() != OUTCOME_SOURCE:
            return _validation_failure(
                "outcome_data_malformed",
                f"Unsupported source for {ticker}; expected {OUTCOME_SOURCE!r}.",
                reason_code="unsupported_source",
            )
        if str(row["price_basis"]).strip() != PRICE_BASIS or str(row["currency"]).strip() != CURRENCY:
            return _validation_failure(
                "outcome_data_malformed",
                f"Unsupported price basis or currency for {ticker}.",
                reason_code="unsupported_price_basis",
            )
        if str(row["valuation_date_rule"]).strip() != VALUATION_DATE_RULE:
            return _validation_failure(
                "outcome_data_malformed",
                f"Unsupported valuation-date rule for {ticker}.",
                reason_code="invalid_date_rule",
            )
        if str(row["return_convention"]).strip() != RETURN_CONVENTION:
            return _validation_failure(
                "outcome_data_malformed",
                f"Unsupported return convention for {ticker}.",
                reason_code="unsupported_return_convention",
            )

        source_symbol = str(row["source_symbol"]).strip().upper()
        expected_symbol = f"{ticker}.IS"
        if source_symbol != expected_symbol and _blank(row["symbol_mapping_note"]):
            return _validation_failure(
                "outcome_provenance_absent",
                f"Source symbol {source_symbol!r} for {ticker} requires an explicit mapping note.",
                ticker=ticker,
                missing_fields=["symbol_mapping_note"],
            )

        start_date = _parse_iso_date(row["start_price_date"])
        end_date = _parse_iso_date(row["end_price_date"])
        as_of_date = _parse_iso_date(row["as_of_date"])
        start_min, start_max = dt.date(START_YEAR, 12, 20), dt.date(START_YEAR, 12, 31)
        end_min, end_max = dt.date(END_YEAR, 12, 20), dt.date(END_YEAR, 12, 31)
        if (
            start_date is None
            or end_date is None
            or as_of_date is None
            or not start_min <= start_date <= start_max
            or not end_min <= end_date <= end_max
            or as_of_date < end_date
        ):
            return _validation_failure(
                "outcome_data_malformed",
                f"Price/as-of dates do not satisfy the pinned year-end rule for {ticker}.",
                reason_code="invalid_date_rule",
            )

        prices = pd.to_numeric(
            pd.Series([row["start_adjusted_close_try"], row["end_adjusted_close_try"]]),
            errors="coerce",
        ).to_numpy(dtype=float)
        if not np.isfinite(prices).all() or (prices <= 0).any():
            return _validation_failure(
                "outcome_data_malformed",
                f"Adjusted-close inputs must be positive finite values for {ticker}.",
                reason_code="invalid_price",
            )
        computed = (prices[1] / prices[0] - 1.0) * 100.0
        submitted = float(row["realized_return_pct"])
        if not math.isclose(computed, submitted, rel_tol=0.0, abs_tol=RETURN_TOLERANCE_PCT):
            return _validation_failure(
                "return_recomputation_mismatch",
                f"Submitted realized return disagrees with adjusted-close recomputation for {ticker}.",
                ticker=ticker,
                submitted_return_pct=submitted,
                recomputed_return_pct=computed,
                tolerance_percentage_points=RETURN_TOLERANCE_PCT,
            )
        usable.loc[index, "recomputed_return_pct"] = computed

    included = set(usable["ticker"].tolist())
    exclusion_reasons: dict[str, str] = {}
    provided = set(frame["ticker"])
    for ticker in frozen:
        if ticker not in provided:
            exclusion_reasons[ticker] = "outcome_row_absent"
    for _, row in frame.loc[null_return].iterrows():
        reason = (
            str(row["exclusion_reason"]).strip()
            if not _blank(row["exclusion_reason"])
            else "realized_return_missing"
        )
        exclusion_reasons[str(row["ticker"])] = reason
    disclosure = _membership_disclosure(frozen, included, exclusion_reasons)

    if len(usable) < min_usable_rows:
        return _validation_failure(
            STATE_INSUFFICIENT,
            f"Only {len(usable)} usable frozen-cohort outcomes remain; the floor is {min_usable_rows}.",
            usable=usable,
            **disclosure,
        )
    return {"ok": True, "status": "outcomes_validated", "usable": usable, **disclosure}


def within_year_permutation_p(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    permutations: int = PERMUTATIONS,
    seed: int = PERMUTATION_SEED,
) -> float:
    """The one two-sided within-year seeded permutation p-value."""
    observed = abs(significance.spearman_ic(y_true, y_pred))
    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_true, dtype=float)
    count = 0
    for _ in range(permutations):
        if abs(significance.spearman_ic(rng.permutation(y_true), y_pred)) >= observed:
            count += 1
    return (1 + count) / (1 + permutations)


def descriptive_power_context(usable_rows: int) -> dict[str, Any]:
    detectable = DETECTABLE_ABS_IC_BY_USABLE_N[usable_rows]
    return {
        "usable_rows": usable_rows,
        "analytic_minimum_detectable_abs_ic": detectable,
        "alpha_two_sided": ALPHA,
        "target_power": TARGET_POWER,
        "method": POWER_METHOD,
        "is_additional_hypothesis_test": False,
        "is_pass_fail_or_meaningfulness_threshold": False,
        "interpretation": (
            "Descriptive sample-size context only. Smaller n has weaker power; exceeding this "
            "value does not establish reliability, validation, or practical relevance."
        ),
    }


def evaluate(
    *,
    frozen_path: Path = FROZEN_RANKING_PATH,
    outcome_file: Path = OUTCOME_FILE,
) -> dict[str, Any]:
    """Return one structured state; compute nothing until all validation passes."""
    integrity = check_frozen_ranking(frozen_path)
    base = {
        "task": TASK_ID,
        "protocol_identifier": PROTOCOL_IDENTIFIER,
        "protocol_document": PROTOCOL_DOCUMENT,
        "target_year": TARGET_YEAR,
    }
    if not integrity["ok"]:
        return {
            **base,
            "status": integrity["status"],
            "reason": integrity["reason"],
            "metric_computed": False,
        }

    frozen = pd.read_csv(frozen_path)
    frozen["ticker"] = frozen["ticker"].astype(str).str.strip().str.upper()
    frozen_tickers = frozen["ticker"].tolist()
    if not outcome_file.is_file():
        disclosure = _membership_disclosure(
            frozen_tickers,
            [],
            {ticker: "outcome_file_absent" for ticker in frozen_tickers},
        )
        return {
            **base,
            "status": STATE_ABSENT,
            "reason": (
                "No sourced 2026 outcome file is present. This is the expected pre-outcome "
                "state; no statistical function was called."
            ),
            "expected_outcome_file": _display_path(outcome_file),
            "frozen_ranking_sha256": integrity["sha256"],
            "metric_computed": False,
            **disclosure,
        }

    validation = validate_outcomes(pd.read_csv(outcome_file), frozen_tickers=frozen_tickers)
    if not validation["ok"]:
        disclosure = {
            key: validation[key]
            for key in (
                "frozen_cohort_size",
                "usable_cohort_size",
                "missing_outcome_count",
                "included_tickers",
                "excluded_tickers",
            )
            if key in validation
        }
        return {
            **base,
            "status": validation["status"],
            "reason": validation["reason"],
            "metric_computed": False,
            **disclosure,
        }

    # Left alignment keeps every frozen ticker explicit; validation has already
    # rejected duplicates and unexpected rows. Only disclosed usable rows enter
    # the statistic after the complete cohort has been accounted for.
    aligned = frozen[["ticker", "frozen_score"]].merge(
        validation["usable"][["ticker", "realized_return_pct"]],
        on="ticker",
        how="left",
        validate="one_to_one",
        indicator=True,
    )
    included = aligned.loc[aligned["_merge"].eq("both")].copy()
    if included["ticker"].tolist() != validation["included_tickers"]:
        raise RuntimeError("Internal cohort disclosure and left alignment disagree")

    y_pred = included["frozen_score"].to_numpy(dtype=float)
    y_true = included["realized_return_pct"].to_numpy(dtype=float)
    ic = significance.spearman_ic(y_true, y_pred)
    p_value = within_year_permutation_p(y_true, y_pred)
    distinguishable = bool(p_value < ALPHA)
    positive = bool(ic > 0)
    power_context = descriptive_power_context(len(included))
    return {
        **base,
        "status": STATE_ESTIMATED,
        "metric_computed": True,
        "usable_rows": int(len(included)),
        "spearman_ic": ic,
        "permutation_p_value_two_sided": p_value,
        "permutations": PERMUTATIONS,
        "seed": PERMUTATION_SEED,
        "alpha": ALPHA,
        "distinguishable_from_within_year_null": distinguishable,
        "ic_sign": "positive" if positive else ("negative" if ic < 0 else "zero"),
        "interpretation_cell": _interpretation_cell(positive, distinguishable),
        "descriptive_power_context": power_context,
        "claim_boundary": (
            f"This is one retrospective {len(included)}-row outcome year. The pre-specified "
            f"descriptive detectable absolute IC is {power_context['analytic_minimum_detectable_abs_ic']:.3f} "
            "at 80% power under the committed Fisher-z method; it is not a pass/fail or "
            "meaningfulness threshold. One result cannot establish a reliable predictive edge, "
            "and no product or Model Confidence Contract claim changes automatically."
        ),
        "frozen_ranking_sha256": integrity["sha256"],
        "frozen_cohort_size": validation["frozen_cohort_size"],
        "usable_cohort_size": validation["usable_cohort_size"],
        "missing_outcome_count": validation["missing_outcome_count"],
        "included_tickers": validation["included_tickers"],
        "excluded_tickers": validation["excluded_tickers"],
    }


def _interpretation_cell(positive: bool, distinguishable: bool) -> str:
    if positive and distinguishable:
        return "positive_and_statistically_distinguishable"
    if positive and not distinguishable:
        return "positive_and_not_distinguishable"
    if not positive and distinguishable:
        return "negative_and_statistically_distinguishable"
    return "negative_and_not_distinguishable"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen", type=Path, default=FROZEN_RANKING_PATH)
    parser.add_argument("--outcomes", type=Path, default=OUTCOME_FILE)
    args = parser.parse_args()
    state = evaluate(frozen_path=args.frozen, outcome_file=args.outcomes)
    print(json.dumps(state, indent=2, sort_keys=True, ensure_ascii=False))

    if state["status"] == STATE_ESTIMATED:
        FUTURE_REPORT_PATH.write_text(
            json.dumps(state, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return 0
    if state["status"] == STATE_ABSENT:
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
