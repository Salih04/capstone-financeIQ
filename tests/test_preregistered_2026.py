"""Tests for the pre-registered 2026 forward-outcome protocol (R3-PREREG-01).

These tests prove genuine pre-registration discipline: no 2026 outcomes exist at
implementation time; the frozen ranking equals the live production inference
output at freeze time (service-path parity, no reimplementation); the frozen
bytes are deterministic and checksum-anchored; the evaluator is inert without
outcomes and refuses to run on tampered/malformed/insufficient inputs; and no
cell of the interpretation grid — including the strongest — licenses an
investment claim.
"""

from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from experiments import freeze_forward_ranking as frz
from experiments import evaluate_preregistered_2026 as ev


REPO_ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_service_directly(monkeypatch: pytest.MonkeyPatch):
    """Independent test-side import of the real production service file.

    This is NOT experiment code; it is the shipped backend service, imported the
    same way the app would. The equivalence test compares the freeze harness
    against THIS, so a reimplementation or drift in the freeze script fails.
    """
    backend = str(REPO_ROOT / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    monkeypatch.setenv("RESEARCH_REPO_ROOT", str(REPO_ROOT))
    spec = importlib.util.spec_from_file_location("_direct_prereg_service", frz.SERVICE_FILE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------- #
# Pre-registration timing
# --------------------------------------------------------------------------- #
def test_no_2026_outcome_file_at_implementation_time():
    """Genuine pre-registration: the sourced outcome file must not exist yet."""
    assert not ev.OUTCOME_FILE.exists()
    # And no partial-2026 target file has leaked into the modeling data either.
    assert not (REPO_ROOT / "data" / "trusted_clean" / "partial_2026_ytd_returns.csv").exists()


# --------------------------------------------------------------------------- #
# Service-path parity (no reimplementation, correct years)
# --------------------------------------------------------------------------- #
def test_freeze_invokes_real_service_functions_by_identity():
    service = frz.load_service_module(REPO_ROOT)
    for name in ("inference_forecast", "train_parameters", "run_forecast"):
        function = getattr(service, name)
        assert Path(inspect.getsourcefile(function)).resolve() == frz.SERVICE_FILE.resolve()


def test_freeze_uses_feature_year_2025_target_year_2026():
    assert frz.FEATURE_YEAR == 2025
    assert frz.TARGET_YEAR == 2026
    frame = pd.read_csv(frz.FROZEN_RANKING_PATH)
    assert set(frame["feature_year"].unique()) == {2025}
    assert set(frame["target_year"].unique()) == {2026}
    assert (frame["realized_return_available"].astype(str) == "False").all()


def test_frozen_ranking_equals_live_production_inference(monkeypatch: pytest.MonkeyPatch):
    """REQUIRED equivalence test: frozen ranking == live service output at freeze time.

    Invokes the real service path directly AND the freeze harness, and compares
    eligible tickers, scores, order, and ranks at production serialization
    precision. Fails if the freeze script reimplements or drifts from the service.
    """
    # (1) Direct, independent invocation of the shipped service.
    service = _load_service_directly(monkeypatch)
    direct = service.inference_forecast(input_year=2025, top_n=12)
    direct_rows = [
        (r["rank"], str(r["ticker"]).upper(), round(float(r["score"]), 4))
        for r in direct["rankings"]
    ]

    # (2) The freeze harness build (its own service load), and the committed CSV.
    provenance = frz._provenance()
    service_h = frz.load_service_module(REPO_ROOT)
    inference_h = frz.invoke_production_inference(service_h)
    frame_h = frz.build_frozen_frame(inference_h, provenance=provenance)
    harness_rows = list(
        zip(
            frame_h["frozen_rank"].tolist(),
            frame_h["ticker"].tolist(),
            [round(float(s), 4) for s in frame_h["frozen_score"].tolist()],
        )
    )

    committed = pd.read_csv(frz.FROZEN_RANKING_PATH)
    committed_rows = list(
        zip(
            committed["frozen_rank"].tolist(),
            committed["ticker"].str.upper().tolist(),
            [round(float(s), 4) for s in committed["frozen_score"].tolist()],
        )
    )

    # Eligible tickers, scores, order, and ranks all agree three ways.
    assert harness_rows == direct_rows
    assert committed_rows == direct_rows
    assert [r[1] for r in committed_rows] == [r[1] for r in direct_rows]  # exact order


def test_deterministic_tie_handling_preserves_service_order():
    """Frozen ranks are the contiguous 1..N production order; ties follow the service."""
    frame = pd.read_csv(frz.FROZEN_RANKING_PATH)
    assert frame["frozen_rank"].tolist() == list(range(1, len(frame) + 1))
    # Scores are non-increasing down the frozen order (service sorts desc, stable).
    scores = frame["frozen_score"].tolist()
    assert all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))


def test_freeze_is_byte_deterministic(tmp_path: Path):
    one = tmp_path / "a"
    two = tmp_path / "b"
    assert frz.freeze(results_dir=one)["status"] == "frozen_created"
    assert frz.freeze(results_dir=two)["status"] == "frozen_created"
    assert (one / "forward_ranking_2026.csv").read_bytes() == (
        two / "forward_ranking_2026.csv"
    ).read_bytes()
    assert (one / "freeze_manifest.json").read_bytes() == (
        two / "freeze_manifest.json"
    ).read_bytes()


def _freeze_and_capture(results_dir: Path) -> tuple[bytes, bytes]:
    result = frz.freeze(results_dir=results_dir)
    assert result["status"] == "frozen_created"
    return (
        (results_dir / frz.FROZEN_RANKING_PATH.name).read_bytes(),
        (results_dir / frz.FREEZE_MANIFEST_PATH.name).read_bytes(),
    )


def test_first_time_freeze_creates_artifacts(tmp_path: Path):
    results_dir = tmp_path / "first"
    result = frz.freeze(results_dir=results_dir)
    assert result["ok"] is True
    assert result["status"] == "frozen_created"
    assert (results_dir / "forward_ranking_2026.csv").is_file()
    assert (results_dir / "freeze_manifest.json").is_file()


def test_same_state_rerun_is_identical_and_does_not_rewrite(tmp_path: Path):
    results_dir = tmp_path / "same"
    original = _freeze_and_capture(results_dir)
    csv_path = results_dir / "forward_ranking_2026.csv"
    manifest_path = results_dir / "freeze_manifest.json"
    mtimes = (csv_path.stat().st_mtime_ns, manifest_path.stat().st_mtime_ns)

    result = frz.freeze(results_dir=results_dir)

    assert result["status"] == "already_frozen_identical"
    assert result["artifacts_unchanged"] is True
    assert (csv_path.read_bytes(), manifest_path.read_bytes()) == original
    assert (csv_path.stat().st_mtime_ns, manifest_path.stat().st_mtime_ns) == mtimes


def test_differing_candidate_refuses_and_preserves_existing_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    results_dir = tmp_path / "candidate-drift"
    original = _freeze_and_capture(results_dir)
    real_builder = frz.build_frozen_frame

    def drifted(*args, **kwargs):
        frame = real_builder(*args, **kwargs)
        frame.loc[0, "frozen_score"] += 0.0001
        return frame

    monkeypatch.setattr(frz, "build_frozen_frame", drifted)
    result = frz.freeze(results_dir=results_dir)
    assert result["status"] == "freeze_refused"
    assert result["reason_code"] == "semantic_ranking_drift"
    assert (
        (results_dir / "forward_ranking_2026.csv").read_bytes(),
        (results_dir / "freeze_manifest.json").read_bytes(),
    ) == original


@pytest.mark.parametrize(
    ("provenance_field", "replacement", "reason_code"),
    [
        ("freeze_git_sha", "f" * 40, "freeze_git_sha_drift"),
        ("service_source_sha256", "e" * 64, "service_checksum_drift"),
        ("public_dataset_sha256", "d" * 64, "source_data_checksum_drift"),
    ],
)
def test_provenance_drift_refuses_without_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    provenance_field: str,
    replacement: str,
    reason_code: str,
):
    results_dir = tmp_path / provenance_field
    original = _freeze_and_capture(results_dir)
    real_provenance = frz._provenance

    def changed_provenance():
        provenance = real_provenance()
        provenance[provenance_field] = replacement
        if provenance_field == "freeze_git_sha":
            provenance["freeze_identifier"] = f"{frz.PROTOCOL_IDENTIFIER}:{replacement[:12]}"
        return provenance

    monkeypatch.setattr(frz, "_provenance", changed_provenance)
    result = frz.freeze(results_dir=results_dir)
    assert result["status"] == "freeze_refused"
    assert result["reason_code"] == reason_code
    assert (
        (results_dir / "forward_ranking_2026.csv").read_bytes(),
        (results_dir / "freeze_manifest.json").read_bytes(),
    ) == original


def test_manually_altered_csv_refuses_and_is_not_replaced(tmp_path: Path):
    results_dir = tmp_path / "manual-csv"
    _freeze_and_capture(results_dir)
    csv_path = results_dir / "forward_ranking_2026.csv"
    manifest_path = results_dir / "freeze_manifest.json"
    csv_path.write_bytes(csv_path.read_bytes() + b"\n")
    altered = (csv_path.read_bytes(), manifest_path.read_bytes())

    result = frz.freeze(results_dir=results_dir)

    assert result["status"] == "freeze_refused"
    assert result["reason_code"] == "freeze_manifest_ranking_checksum_mismatch"
    assert (csv_path.read_bytes(), manifest_path.read_bytes()) == altered


def test_manually_altered_manifest_refuses_and_is_not_replaced(tmp_path: Path):
    results_dir = tmp_path / "manual-manifest"
    _freeze_and_capture(results_dir)
    csv_path = results_dir / "forward_ranking_2026.csv"
    manifest_path = results_dir / "freeze_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["freeze_git_sha"] = "0" * 40
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    altered = (csv_path.read_bytes(), manifest_path.read_bytes())

    result = frz.freeze(results_dir=results_dir)

    assert result["status"] == "freeze_refused"
    assert result["reason_code"] == "freeze_git_sha_internal_mismatch"
    assert (csv_path.read_bytes(), manifest_path.read_bytes()) == altered


def test_noncanonical_manifest_hashes_requested_results_csv_and_has_no_machine_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    results_dir = tmp_path / "noncanonical"
    monkeypatch.setattr(frz, "_git_sha", lambda: "1" * 40)
    result = frz.freeze(results_dir=results_dir)
    csv_path = results_dir / "forward_ranking_2026.csv"
    manifest_path = results_dir / "freeze_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert result["status"] == "frozen_created"
    assert manifest["frozen_ranking"]["sha256"] == _sha256(csv_path)
    assert manifest["frozen_ranking"]["sha256"] != _sha256(frz.FROZEN_RANKING_PATH)
    output_blob = csv_path.read_text(encoding="utf-8") + manifest_path.read_text(encoding="utf-8")
    assert str(REPO_ROOT) not in output_blob
    assert str(tmp_path) not in output_blob


def test_git_sha_and_source_checksums_are_recorded():
    frame = pd.read_csv(frz.FROZEN_RANKING_PATH)
    git_sha = str(frame["freeze_git_sha"].iloc[0])
    assert git_sha == "unavailable" or len(git_sha) == 40
    # Service and dataset checksums stamped in the CSV match the files on disk.
    assert str(frame["service_source_sha256"].iloc[0]) == _sha256(frz.SERVICE_FILE)
    assert str(frame["public_dataset_sha256"].iloc[0]) == _sha256(frz.PUBLIC_DATASET)
    assert str(frame["training_dataset_sha256"].iloc[0]) == _sha256(frz.TRAINING_DATASET)
    assert (frame["protocol_identifier"].astype(str) == frz.PROTOCOL_IDENTIFIER).all()


def test_manifest_protected_source_checksums_verify():
    """Every source artifact the manifest names must still hash to its recorded value."""
    manifest = json.loads(frz.FREEZE_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["reimplementation_used"] is False
    assert manifest["protocol_identifier"] == frz.PROTOCOL_IDENTIFIER
    for item in manifest["source_artifacts"]:
        path = REPO_ROOT / item["path"]
        assert path.is_file(), item["path"]
        assert _sha256(path) == item["sha256"], item["path"]


# --------------------------------------------------------------------------- #
# Frozen-artifact checksum verification + tamper rejection
# --------------------------------------------------------------------------- #
def test_frozen_artifact_checksum_matches_committed_anchor():
    assert _sha256(frz.FROZEN_RANKING_PATH) == ev.EXPECTED_FROZEN_RANKING_SHA256
    result = ev.check_frozen_ranking()
    assert result["ok"] is True
    assert result["sha256"] == ev.EXPECTED_FROZEN_RANKING_SHA256


def test_frozen_ranking_tamper_is_rejected(tmp_path: Path):
    tampered = tmp_path / "forward_ranking_2026.csv"
    frame = pd.read_csv(frz.FROZEN_RANKING_PATH)
    frame.loc[0, "frozen_score"] = float(frame.loc[0, "frozen_score"]) + 1.0
    tampered.write_text(frame.to_csv(index=False, lineterminator="\n"), encoding="utf-8")
    result = ev.check_frozen_ranking(tampered)
    assert result["ok"] is False
    assert result["status"] == "frozen_ranking_tampered"


def test_protocol_identifier_mismatch_is_rejected(tmp_path: Path):
    swapped = tmp_path / "forward_ranking_2026.csv"
    frame = pd.read_csv(frz.FROZEN_RANKING_PATH)
    frame["protocol_identifier"] = "SOME-OTHER-PROTOCOL"
    swapped.write_text(frame.to_csv(index=False, lineterminator="\n"), encoding="utf-8")
    # Anchor the expected sha to this file so only the protocol id differs.
    result = ev.check_frozen_ranking(
        swapped, expected_sha256=_sha256(swapped), expected_protocol=frz.PROTOCOL_IDENTIFIER
    )
    assert result["ok"] is False
    assert result["status"] == "protocol_identifier_mismatch"


# --------------------------------------------------------------------------- #
# Inert absent-data behavior
# --------------------------------------------------------------------------- #
def test_evaluator_returns_outcome_data_absent_with_no_metric():
    state = ev.evaluate()
    assert state["status"] == "outcome_data_absent"
    assert state["metric_computed"] is False
    assert "spearman_ic" not in state
    assert "permutation_p_value_two_sided" not in state
    assert state["frozen_cohort_size"] == 40
    assert state["usable_cohort_size"] == 0
    assert state["missing_outcome_count"] == 40
    assert state["included_tickers"] == []
    assert len(state["excluded_tickers"]) == 40


def test_absent_state_writes_no_result_artifact(tmp_path: Path):
    # evaluate() itself never writes; confirm no report appears under the results dir.
    before = set(p.name for p in frz.FROZEN_RANKING_PATH.parent.iterdir())
    ev.evaluate()
    after = set(p.name for p in frz.FROZEN_RANKING_PATH.parent.iterdir())
    assert before == after
    assert "evaluation_2026_report.json" not in after


def test_missing_frozen_ranking_is_reported(tmp_path: Path):
    state = ev.evaluate(frozen_path=tmp_path / "nope.csv", outcome_file=tmp_path / "nope2.csv")
    assert state["status"] == "frozen_ranking_missing"
    assert state["metric_computed"] is False


def test_within_year_permutation_p_preserves_finite_behavior():
    y_true = np.array([1.0, 4.0, 2.0, 8.0, 5.0, 7.0])
    y_pred = np.array([1.5, 3.5, 2.5, 7.0, 5.5, 6.5])

    result = ev.within_year_permutation_p(y_true, y_pred, permutations=1_000, seed=17)

    assert result == pytest.approx(3 / 1_001)


@pytest.mark.parametrize(
    ("y_true", "y_pred"),
    [
        (np.array([1.0, 2.0, 3.0]), np.array([4.0, 4.0, 4.0])),
        (np.array([2.0, 2.0, 2.0]), np.array([1.0, 2.0, 3.0])),
    ],
)
def test_within_year_permutation_p_rejects_constant_observed_statistic(
    y_true: np.ndarray, y_pred: np.ndarray
):
    with pytest.raises(ev.significance.DegenerateStatisticError):
        ev.within_year_permutation_p(y_true, y_pred, permutations=20)


@pytest.mark.parametrize("observed", [np.nan, np.inf, -np.inf])
def test_within_year_permutation_p_rejects_nonfinite_observed(
    monkeypatch: pytest.MonkeyPatch, observed: float
):
    monkeypatch.setattr(ev.significance, "spearman_ic", lambda *_args: observed)

    with pytest.raises(ev.significance.DegenerateStatisticError):
        ev.within_year_permutation_p(np.arange(4.0), np.arange(4.0), permutations=20)


def test_within_year_permutation_p_rejects_unusable_null_distribution(
    monkeypatch: pytest.MonkeyPatch,
):
    calls = 0

    def observed_then_nonfinite(*_args):
        nonlocal calls
        calls += 1
        return 0.25 if calls == 1 else np.nan

    monkeypatch.setattr(ev.significance, "spearman_ic", observed_then_nonfinite)

    with pytest.raises(ev.significance.DegenerateStatisticError):
        ev.within_year_permutation_p(np.arange(4.0), np.arange(4.0), permutations=20)


# --------------------------------------------------------------------------- #
# Future outcome-schema refusals (all inert until valid data exists)
# --------------------------------------------------------------------------- #
def _valid_outcomes(n: int = 30) -> pd.DataFrame:
    tickers = pd.read_csv(frz.FROZEN_RANKING_PATH)["ticker"].tolist()[:n]
    returns = np.arange(n, dtype=float)
    start_prices = np.full(n, 100.0)
    end_prices = start_prices * (1.0 + returns / 100.0)
    return pd.DataFrame(
        {
            "ticker": tickers,
            "target_year": [2026] * n,
            "realized_return_pct": returns,
            "start_adjusted_close_try": start_prices,
            "end_adjusted_close_try": end_prices,
            "start_price_date": ["2025-12-31"] * n,
            "end_price_date": ["2026-12-31"] * n,
            "price_basis": [ev.PRICE_BASIS] * n,
            "currency": [ev.CURRENCY] * n,
            "valuation_date_rule": [ev.VALUATION_DATE_RULE] * n,
            "return_convention": [ev.RETURN_CONVENTION] * n,
            "source": [ev.OUTCOME_SOURCE] * n,
            "source_url_or_record_id": ["yahoo-chart-raw-record"] * n,
            "as_of_date": ["2027-01-05"] * n,
            "start_snapshot_sha256": ["a" * 64] * n,
            "end_snapshot_sha256": ["b" * 64] * n,
            "source_symbol": [f"{ticker}.IS" for ticker in tickers],
            "symbol_mapping_note": [""] * n,
            "exclusion_reason": [""] * n,
        }
    )


@pytest.mark.parametrize("column", ev.OUTCOME_REQUIRED_COLUMNS)
def test_every_outcome_schema_field_is_mandatory(column: str):
    bad = _valid_outcomes().drop(columns=[column])
    result = ev.validate_outcomes(bad)
    assert result["ok"] is False
    assert result["status"] == "outcome_schema_malformed"


def test_duplicate_tickers_are_rejected():
    dup = _valid_outcomes()
    dup = pd.concat([dup, dup.iloc[[0]]], ignore_index=True)
    result = ev.validate_outcomes(dup)
    assert result["ok"] is False
    assert result["status"] == "duplicate_tickers"


def test_wrong_target_year_is_rejected():
    bad = _valid_outcomes()
    bad["target_year"] = 2027
    result = ev.validate_outcomes(bad)
    assert result["ok"] is False
    assert result["status"] == "wrong_target_year"


def test_per_row_missing_source_is_rejected():
    bad = _valid_outcomes()
    bad.loc[0, "source"] = ""
    result = ev.validate_outcomes(bad)
    assert result["ok"] is False
    assert result["status"] == "outcome_provenance_absent"


def test_per_row_missing_as_of_date_is_rejected():
    bad = _valid_outcomes()
    bad.loc[0, "as_of_date"] = ""
    result = ev.validate_outcomes(bad)
    assert result["ok"] is False
    assert result["status"] == "outcome_provenance_absent"


def test_per_row_missing_snapshot_provenance_is_rejected():
    bad = _valid_outcomes()
    bad.loc[0, "end_snapshot_sha256"] = ""
    result = ev.validate_outcomes(bad)
    assert result["ok"] is False
    assert result["status"] == "outcome_provenance_absent"


def test_29_usable_rows_is_explicit_insufficient_data():
    result = ev.validate_outcomes(_valid_outcomes(n=29))
    assert result["ok"] is False
    assert result["status"] == "insufficient_data"
    assert result["usable_cohort_size"] == 29
    assert "spearman_ic" not in result
    assert "permutation_p_value_two_sided" not in result


def test_30_usable_rows_reaches_permitted_evaluation_path():
    result = ev.validate_outcomes(_valid_outcomes(n=30))
    assert result["ok"] is True
    assert result["status"] == "outcomes_validated"
    assert result["usable_cohort_size"] == 30


def test_membership_lists_are_complete_deterministic_disjoint_and_cover_frozen_cohort():
    frame = _valid_outcomes(n=35)
    frame.loc[0:2, "realized_return_pct"] = np.nan
    frame.loc[0:2, "exclusion_reason"] = ["missing_start_quote", "delisted_no_quote", "missing_end_quote"]
    first = ev.validate_outcomes(frame)
    second = ev.validate_outcomes(frame.sample(frac=1.0, random_state=7))
    assert first["ok"] is True
    assert first["included_tickers"] == second["included_tickers"]
    assert first["excluded_tickers"] == second["excluded_tickers"]
    included = set(first["included_tickers"])
    excluded = {item["ticker"] for item in first["excluded_tickers"]}
    frozen = set(pd.read_csv(frz.FROZEN_RANKING_PATH)["ticker"])
    assert included.isdisjoint(excluded)
    assert included | excluded == frozen
    assert first["frozen_cohort_size"] == 40
    assert first["usable_cohort_size"] == 32
    assert first["missing_outcome_count"] == 8


def test_null_outcomes_are_excluded_not_imputed():
    frame = _valid_outcomes(n=35)
    frame.loc[0:4, "realized_return_pct"] = np.nan
    result = ev.validate_outcomes(frame)
    assert result["ok"] is True
    assert len(result["usable"]) == 30
    assert result["usable"]["realized_return_pct"].isna().sum() == 0
    assert {item["ticker"] for item in result["excluded_tickers"]}.issuperset(
        set(frame.loc[0:4, "ticker"])
    )


def test_unexpected_ticker_is_rejected_before_merge():
    bad = _valid_outcomes()
    bad.loc[0, "ticker"] = "NOTFROZEN"
    result = ev.validate_outcomes(bad)
    assert result["ok"] is False
    assert result["status"] == "unexpected_tickers"


@pytest.mark.parametrize("value", [np.inf, -np.inf])
def test_non_finite_realized_return_is_malformed(value: float):
    bad = _valid_outcomes()
    bad.loc[0, "realized_return_pct"] = value
    result = ev.validate_outcomes(bad)
    assert result["ok"] is False
    assert result["status"] == "outcome_data_malformed"
    assert result["reason_code"] == "non_finite_realized_return"


def test_submitted_return_is_independently_recomputed():
    result = ev.validate_outcomes(_valid_outcomes())
    assert result["ok"] is True
    assert result["usable"]["recomputed_return_pct"].tolist() == pytest.approx(
        result["usable"]["realized_return_pct"].tolist(), abs=ev.RETURN_TOLERANCE_PCT
    )


def test_return_recomputation_mismatch_is_rejected():
    bad = _valid_outcomes()
    bad.loc[0, "realized_return_pct"] += 0.01
    result = ev.validate_outcomes(bad)
    assert result["ok"] is False
    assert result["status"] == "return_recomputation_mismatch"


def test_unsupported_price_basis_is_rejected():
    bad = _valid_outcomes()
    bad.loc[0, "price_basis"] = "raw_close"
    result = ev.validate_outcomes(bad)
    assert result["ok"] is False
    assert result["reason_code"] == "unsupported_price_basis"


def test_invalid_date_rule_is_rejected():
    bad = _valid_outcomes()
    bad.loc[0, "end_price_date"] = "2026-11-30"
    result = ev.validate_outcomes(bad)
    assert result["ok"] is False
    assert result["reason_code"] == "invalid_date_rule"


def test_target_year_and_nominal_try_rules_remain_pinned():
    wrong_year = _valid_outcomes()
    wrong_year["target_year"] = 2025
    assert ev.validate_outcomes(wrong_year)["status"] == "wrong_target_year"
    wrong_currency = _valid_outcomes()
    wrong_currency["currency"] = "USD"
    result = ev.validate_outcomes(wrong_currency)
    assert result["reason_code"] == "unsupported_price_basis"


def test_validation_completes_before_statistical_functions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    outcome_file = tmp_path / "fixture.csv"
    outcome_file.write_text(_valid_outcomes(n=29).to_csv(index=False), encoding="utf-8")

    def forbidden(*args, **kwargs):
        raise AssertionError("statistical function called before validation completed")

    monkeypatch.setattr(ev.significance, "spearman_ic", forbidden)
    monkeypatch.setattr(ev, "within_year_permutation_p", forbidden)
    state = ev.evaluate(outcome_file=outcome_file)
    assert state["status"] == "insufficient_data"
    assert state["metric_computed"] is False


# --------------------------------------------------------------------------- #
# Estimated path exists and stays claim-safe (isolated schema fixture only)
# --------------------------------------------------------------------------- #
def test_positive_significant_cell_still_denies_reliable_edge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """The strongest permitted cell must still deny a reliable edge."""
    outcomes = _valid_outcomes(n=40)
    returns = np.arange(40, 0, -1, dtype=float)
    outcomes["realized_return_pct"] = returns
    outcomes["end_adjusted_close_try"] = 100.0 * (1.0 + returns / 100.0)
    outcome_file = tmp_path / "realized_2026_returns.csv"
    outcome_file.write_text(outcomes.to_csv(index=False), encoding="utf-8")

    # Keep the permutation fast but real; determinism of the cell is unaffected.
    original_perm = ev.within_year_permutation_p
    monkeypatch.setattr(
        ev,
        "within_year_permutation_p",
        lambda y_true, y_pred, **k: original_perm(y_true, y_pred, permutations=200),
    )
    state = ev.evaluate(outcome_file=outcome_file)

    assert state["status"] == "estimated"
    assert state["metric_computed"] is True
    assert state["spearman_ic"] > 0
    assert state["distinguishable_from_within_year_null"] is True
    assert state["interpretation_cell"] == "positive_and_statistically_distinguishable"
    # The strongest cell still explicitly denies a reliable predictive edge.
    assert "cannot establish a reliable predictive edge" in state["claim_boundary"]
    assert "0.431" in state["claim_boundary"]
    assert state["descriptive_power_context"]["is_additional_hypothesis_test"] is False
    assert state["descriptive_power_context"]["is_pass_fail_or_meaningfulness_threshold"] is False
    assert [key for key in state if "p_value" in key] == ["permutation_p_value_two_sided"]
    # No advice wording leaks into the machine result.
    blob = json.dumps(state).lower()
    for token in ("buy", "sell", "hold recommendation", "investment advice", "price target", "guaranteed"):
        assert token not in blob


def test_power_table_matches_committed_method_and_covers_30_through_40():
    assert set(ev.DETECTABLE_ABS_IC_BY_USABLE_N) == set(range(30, 41))
    for n, frozen_value in ev.DETECTABLE_ABS_IC_BY_USABLE_N.items():
        computed = ev.significance.minimum_detectable_ic(
            n_per_split=n,
            split_count=1,
            alpha=ev.ALPHA,
            target_power=ev.TARGET_POWER,
        )
        assert frozen_value == pytest.approx(computed, abs=5e-7)
    assert ev.DETECTABLE_ABS_IC_BY_USABLE_N[40] == pytest.approx(0.431, abs=0.001)


def test_selected_power_context_changes_with_usable_rows_and_weakens_as_n_decreases():
    selected = [ev.descriptive_power_context(n)["analytic_minimum_detectable_abs_ic"] for n in range(30, 41)]
    assert len(set(selected)) == 11
    assert selected == sorted(selected, reverse=True)


def test_interpretation_cell_helper_is_total():
    seen = {
        ev._interpretation_cell(p, d)
        for p in (True, False)
        for d in (True, False)
    }
    assert seen == {
        "positive_and_statistically_distinguishable",
        "positive_and_not_distinguishable",
        "negative_and_statistically_distinguishable",
        "negative_and_not_distinguishable",
    }


# --------------------------------------------------------------------------- #
# Protocol document: leading boundary, grid completeness, no advice wording
# --------------------------------------------------------------------------- #
def _protocol_text() -> str:
    return (REPO_ROOT / "docs" / "PREREGISTERED_2026_EVALUATION.md").read_text(encoding="utf-8")


def _protocol_prose() -> str:
    """Protocol text with markdown emphasis/backticks removed for substring checks."""
    return _protocol_text().replace("*", "").replace("`", "")


def test_protocol_leads_with_required_power_boundary():
    text = _protocol_text()
    assert (
        "The pre-registered 2026 evaluation is nearly powerless by design; its value is"
        in text
    )
    # Committed checksum and protocol identifier are pinned in the doc.
    assert ev.EXPECTED_FROZEN_RANKING_SHA256 in text
    assert frz.PROTOCOL_IDENTIFIER in text


def test_interpretation_grid_is_complete():
    prose = _protocol_prose().lower()
    for phrase in (
        "positive and statistically distinguishable",
        "positive and not distinguishable",
        "negative and statistically distinguishable",
        "negative and not distinguishable",
        "undefined or insufficient data",
    ):
        assert phrase in prose
    # Every-cell boundary language present.
    assert "0.431" in prose
    assert "cannot establish a reliable predictive edge" in prose
    assert "evidence" in prose and "mcc" in prose


def test_protocol_contains_no_investment_advice_wording():
    """The doc denies advice; it must never phrase advice affirmatively."""
    prose = _protocol_prose().lower()
    forbidden_affirmative = [
        "you should buy",
        "you should sell",
        "we recommend buying",
        "we recommend selling",
        "expected return of ",
        "will outperform",
        "guaranteed return",
        "price target",
        "buy signal",
        "sell signal",
    ]
    hits = [p for p in forbidden_affirmative if p in prose]
    assert hits == [], f"protocol contains affirmative advice wording: {hits}"
    # And the explicit product-standard denial is present.
    assert "not investment advice" in prose


# --------------------------------------------------------------------------- #
# Artifact-registry ownership + protected artifacts
# --------------------------------------------------------------------------- #
def test_frozen_artifacts_have_exactly_one_registry_owner():
    registry = json.loads((REPO_ROOT / "artifact_registry.json").read_text(encoding="utf-8"))
    assert "experiments/results_forward_2026" in registry["governed_roots"]
    for target in (
        "experiments/results_forward_2026/forward_ranking_2026.csv",
        "experiments/results_forward_2026/freeze_manifest.json",
    ):
        owners = [e for e in registry["entries"] if e["path_or_glob"] == target]
        assert len(owners) == 1, target
        assert owners[0]["generator_command"] == "make freeze-forward-2026"
        assert owners[0]["hand_edit_forbidden"] is True


def test_makefile_has_additive_freeze_and_evaluate_targets():
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "\nfreeze-forward-2026:" in makefile
    assert "\nevaluate-forward-2026:" in makefile
    assert "freeze-forward-2026 evaluate-forward-2026" in makefile  # in .PHONY block


def test_protected_service_and_dataset_inputs_unchanged():
    """The frozen ranking's declared protected inputs still match their recorded checksums."""
    manifest = json.loads(frz.FREEZE_MANIFEST_PATH.read_text(encoding="utf-8"))
    by_path = {i["path"]: i["sha256"] for i in manifest["source_artifacts"]}
    for rel in (
        "backend/app/services/forecasting_csv_service.py",
        "data/trusted_clean/modeling_dataset_public_2020_2025.csv",
        "data/trusted_clean/modeling_dataset_training_2020_2025.csv",
        "data/trusted_clean/modeling_dataset_2020_2025.csv",
    ):
        assert _sha256(REPO_ROOT / rel) == by_path[rel]
