from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments import regime_lens


def _regimes() -> list[dict[str, str]]:
    return [
        {
            "regime_id": "observed_2020_2025_macro_period",
            "start_date": "2020-01-01",
            "end_date": "2025-12-31",
        }
    ]


def test_regime_assignment_is_deterministic_and_boundaries_are_inclusive() -> None:
    regimes = _regimes()
    assert regime_lens.assign_regime("2020-01-01", regimes) == "observed_2020_2025_macro_period"
    assert regime_lens.assign_regime("2025-12-31", regimes) == "observed_2020_2025_macro_period"
    assert regime_lens.assign_regime("2023-06-30", regimes) == "observed_2020_2025_macro_period"
    assert regime_lens.assign_regime("2019-12-31", regimes) is None
    assert regime_lens.assign_regime("2026-01-01", regimes) is None
    assert regime_lens.assign_regime(None, regimes) is None
    assert regime_lens.assign_regime("not-a-date", regimes) is None


def test_missing_macro_values_remain_null_and_require_null_metadata() -> None:
    frame = regime_lens.load_context(validate_shared=False)
    frame.loc[frame["year"].eq(2023), [
        "policy_rate_year_end_pct",
        "policy_rate_effective_date",
        "policy_rate_source_id",
    ]] = None

    validated = regime_lens._validate_frame(frame)
    report = regime_lens.build_report(validated)
    row = next(item for item in report["macro_context"] if item["year"] == 2023)
    assert row["policy_rate_year_end_pct"] == {
        "value": None,
        "effective_date": None,
        "source_id": None,
        "source": None,
    }

    invalid = frame.copy()
    invalid.loc[invalid["year"].eq(2023), "policy_rate_year_end_pct"] = 42.5
    with pytest.raises(ValueError, match="must carry both"):
        regime_lens._validate_frame(invalid)


def test_committed_macro_context_matches_shared_effective_dated_sources() -> None:
    frame = regime_lens.load_context()
    assert frame["year"].tolist() == list(range(2020, 2026))
    for value_column, (date_column, source_column) in regime_lens.METRICS.items():
        present = frame[value_column].notna()
        assert frame.loc[present, date_column].notna().all()
        assert frame.loc[present, source_column].notna().all()


def test_single_regime_emits_untestable_state_and_no_conditional_statistics() -> None:
    report = regime_lens.build_report(regime_lens.load_context())
    diagnostics = report["conditional_diagnostics"]
    assert diagnostics == {
        "computed": False,
        "status": "not_computed_insufficient_regime_diversity",
        "required_distinct_regimes": 2,
        "observed_distinct_regimes": 1,
        "reason": "All three test years map to the same task-defined observed period; a per-regime number would only relabel the aggregate.",
    }
    assert set(report["design"]["test_year_assignments"].values()) == {
        "observed_2020_2025_macro_period"
    }
    serialized = json.dumps(report, sort_keys=True).casefold()
    assert "per_regime" not in serialized
    assert "observed_ic" not in serialized


@pytest.mark.parametrize(
    "unsafe",
    [
        "We found a regime-specific edge.",
        "Regime robustness was established.",
        "Macro conditions caused the ranking result.",
        "Inflation explains the model failure.",
        "This regime predicts future returns.",
    ],
)
def test_claim_safety_rejects_regime_edge_and_causal_language(unsafe: str) -> None:
    with pytest.raises(ValueError, match="Unsafe regime-lens claim"):
        regime_lens.validate_claim_safety_text(unsafe)


def test_regime_workflow_is_byte_deterministic(tmp_path: Path) -> None:
    first = regime_lens.run(tmp_path / "first")
    second = regime_lens.run(tmp_path / "second")
    assert [path.name for path in first] == [path.name for path in second]
    assert [path.read_bytes() for path in first] == [path.read_bytes() for path in second]
    regime_lens.validate_claim_safety_text(first[1].read_text(encoding="utf-8"))
    assert regime_lens.MANDATORY_STATEMENT in first[1].read_text(encoding="utf-8")
