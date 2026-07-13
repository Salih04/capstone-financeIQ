"""Bind MCC policy assertions to their live, owning evidence artifacts.

This is deliberately a contract-policy test, not an evidence generator or a
second store of research metrics.  The contract remains the policy surface;
the generated reports remain the only source for their states and conclusions.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "model_confidence_contract.json"


@dataclass(frozen=True)
class EvidenceBinding:
    """Approved MCC evidence input and, for generated inputs, its sole owner."""

    path: str
    owner: str
    regeneration_command: str | None
    generator_path: str | None


# This list is structural metadata only: it intentionally contains no copied
# research values, thresholds, or conclusions.  Adding an evidence input
# requires adding its binding and explicit owner here, not treating a history
# record or arbitrary document as live MCC evidence.
EVIDENCE_BINDINGS = (
    EvidenceBinding(
        "experiments/results/significance_report.md",
        "experiments/significance.py",
        "make research-significance",
        "experiments/significance.py",
    ),
    EvidenceBinding(
        "experiments/leaderboard.csv",
        "experiments/run_experiments.py",
        "make research",
        "experiments/run_experiments.py",
    ),
    EvidenceBinding(
        "FINANCEIQ_DEMO_AND_CLAIMS_GUIDE.md",
        "human-reviewed claims authority",
        None,
        None,
    ),
    EvidenceBinding(
        "experiments/results_regime/regime_context_report.md",
        "experiments/regime_lens.py",
        "make research-regime",
        "experiments/regime_lens.py",
    ),
    EvidenceBinding(
        "experiments/results/friction_report.md",
        "experiments/friction_sim.py",
        "make research-friction",
        "experiments/friction_sim.py",
    ),
)


def _load_json(path: Path) -> dict[str, object]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise AssertionError(f"[MCC-EVIDENCE-MISSING] {path}: artifact is missing") from None
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"[MCC-EVIDENCE-JSON] {path}:{exc.lineno}: invalid JSON: {exc.msg}"
        ) from None
    assert isinstance(loaded, dict), f"[MCC-EVIDENCE-SCHEMA] {path}: expected JSON object"
    return loaded


def _required_field(
    document: dict[str, object], artifact: Path, dotted_path: str, command: str
) -> object:
    current: object = document
    for key in dotted_path.split("."):
        if not isinstance(current, dict) or key not in current:
            raise AssertionError(
                f"[MCC-EVIDENCE-SCHEMA] {artifact}: missing required field "
                f"{dotted_path}; regenerate via `{command}` or complete MCC review."
            )
        current = current[key]
    return current


def _evidence_basis(contract: dict[str, object]) -> dict[str, str]:
    evidence_basis = contract.get("evidence_basis")
    assert isinstance(evidence_basis, list), "[MCC-EVIDENCE-SCHEMA] contract: evidence_basis must be a list"
    result: dict[str, str] = {}
    for entry in evidence_basis:
        assert isinstance(entry, dict), "[MCC-EVIDENCE-SCHEMA] contract: evidence_basis entry must be an object"
        path, finding = entry.get("path"), entry.get("finding")
        assert isinstance(path, str) and path, "[MCC-EVIDENCE-SCHEMA] contract: evidence_basis path is required"
        assert isinstance(finding, str) and finding, f"[MCC-EVIDENCE-SCHEMA] {path}: finding is required"
        assert path not in result, f"[MCC-EVIDENCE-OWNERSHIP] {path}: duplicate MCC evidence entry"
        result[path] = finding
    return result


def _make_targets(root: Path) -> set[str]:
    return set(re.findall(r"^(\S+):", (root / "Makefile").read_text(encoding="utf-8"), re.MULTILINE))


def _assert_binding_ownership(root: Path, evidence_basis: dict[str, str]) -> None:
    bound_paths = {binding.path for binding in EVIDENCE_BINDINGS}
    assert set(evidence_basis) == bound_paths, (
        "[MCC-EVIDENCE-OWNERSHIP] contract evidence inputs must be exactly the approved live "
        f"bindings; expected {sorted(bound_paths)}, got {sorted(evidence_basis)}"
    )

    make_targets = _make_targets(root)
    for binding in EVIDENCE_BINDINGS:
        artifact = root / binding.path
        assert artifact.is_file(), (
            f"[MCC-EVIDENCE-MISSING] {binding.path}: cited evidence is missing; "
            f"regenerate via `{binding.regeneration_command}` or restore the authority artifact."
        )
        if binding.regeneration_command is None:
            continue
        assert binding.generator_path is not None
        assert (root / binding.generator_path).is_file(), (
            f"[MCC-EVIDENCE-OWNERSHIP] {binding.path}: owner {binding.owner} is missing; "
            f"cannot regenerate via `{binding.regeneration_command}`."
        )
        command_parts = binding.regeneration_command.split()
        assert command_parts[:1] == ["make"] and len(command_parts) == 2
        assert command_parts[1] in make_targets, (
            f"[MCC-EVIDENCE-OWNERSHIP] {binding.path}: regeneration target "
            f"`{binding.regeneration_command}` is missing from Makefile."
        )


def _assert_significance_binding(
    contract: dict[str, object], finding: str, report_path: Path
) -> None:
    report = _load_json(report_path)
    evidence_state = contract["evidence_state"]
    assert isinstance(evidence_state, dict)
    headline = _required_field(report, report_path, "headline", "make research-significance")
    assert isinstance(headline, dict), f"[MCC-EVIDENCE-SCHEMA] {report_path}: headline must be an object"
    significant = _required_field(
        report, report_path, "headline.significant_fwer_0_05", "make research-significance"
    )
    assert isinstance(significant, bool), (
        f"[MCC-EVIDENCE-SCHEMA] {report_path}: headline.significant_fwer_0_05 must be boolean"
    )
    assert evidence_state.get("ml_family_wise_significant") is significant, (
        "[MCC-EVIDENCE-STATE] evidence_state.ml_family_wise_significant disagrees with "
        f"{report_path}:headline.significant_fwer_0_05; regenerate via `make research-significance` "
        "and complete MCC review."
    )
    conclusion = _required_field(report, report_path, "headline.conclusion", "make research-significance")
    assert isinstance(conclusion, str), (
        f"[MCC-EVIDENCE-SCHEMA] {report_path}: headline.conclusion must be a string"
    )
    headline_conclusion = contract["approved_wording"]
    assert isinstance(headline_conclusion, dict)
    expected_conclusion = headline_conclusion.get("headline_conclusion")
    assert isinstance(expected_conclusion, str)
    expected_semantics = expected_conclusion.casefold().rstrip(".")
    report_semantics = conclusion.casefold()
    assert (
        "reliable predictive edge" in expected_semantics
        and "reliable predictive edge" in report_semantics
        and ("no reliable predictive edge" in report_semantics or "do not support" in report_semantics)
    ), (
        "[MCC-EVIDENCE-CONCLUSION] approved_wording.headline_conclusion is not supported by "
        f"{report_path}:headline.conclusion; regenerate via `make research-significance` and "
        "complete MCC review."
    )
    assert finding.casefold().startswith(
        "no ml model is statistically distinguishable from the within-year null"
    ), (
        "[MCC-EVIDENCE-CONCLUSION] contract significance finding is no longer anchored to the "
        "approved report conclusion; complete MCC review."
    )
    assert evidence_state.get("reliable_predictive_edge_observed") is False, (
        "[MCC-EVIDENCE-STATE] evidence_state.reliable_predictive_edge_observed must remain false "
        "while the significance headline reports no reliable predictive edge."
    )
    detectable_ic_definition = _required_field(
        report,
        report_path,
        "power_analysis.definitions.detectable_ic",
        "make research-significance",
    )
    assert isinstance(detectable_ic_definition, str) and "assumed" in detectable_ic_definition.casefold() and "not" in detectable_ic_definition.casefold(), (
        "[MCC-EVIDENCE-CONCLUSION] significance power definition no longer states that the "
        "detectable IC is assumed rather than an observed edge; regenerate via "
        "`make research-significance` and complete MCC review."
    )
    assert evidence_state.get("power_thresholds_are_observed_edge") is False, (
        "[MCC-EVIDENCE-STATE] evidence_state.power_thresholds_are_observed_edge must remain false "
        "while the significance report defines detectable IC as an assumed quantity."
    )
    assert evidence_state.get("conclusion") == expected_conclusion.casefold().rstrip("."), (
        "[MCC-EVIDENCE-STATE] evidence_state.conclusion must match "
        "approved_wording.headline_conclusion semantics."
    )


def _assert_regime_binding(contract: dict[str, object], finding: str, report_path: Path) -> None:
    report = _load_json(report_path)
    evidence_state = contract["evidence_state"]
    assert isinstance(evidence_state, dict)
    status = _required_field(
        report,
        report_path,
        "conditional_diagnostics.status",
        "make research-regime",
    )
    assert status == "not_computed_insufficient_regime_diversity", (
        "[MCC-EVIDENCE-STATE] regime report conditional_diagnostics.status changed from the "
        "MCC-approved untestable state; regenerate via `make research-regime` and complete MCC review."
    )
    assert evidence_state.get("regime_robustness_testable") is False, (
        "[MCC-EVIDENCE-STATE] evidence_state.regime_robustness_testable must be false while "
        "the regime report is not_computed_insufficient_regime_diversity."
    )
    finding_terms = finding.casefold()
    assert "untestable" in finding_terms and "not computed" in finding_terms, (
        "[MCC-EVIDENCE-CONCLUSION] contract regime finding is no longer anchored to the "
        "report's untestable state; complete MCC review."
    )


def _assert_friction_binding(contract: dict[str, object], finding: str, report_path: Path) -> None:
    report = _load_json(report_path)
    evidence_state = contract["evidence_state"]
    assert isinstance(evidence_state, dict)
    implementable = _required_field(
        report,
        report_path,
        "claim_safety.implementable_returns_established",
        "make research-friction",
    )
    investment_value = _required_field(
        report,
        report_path,
        "claim_safety.investment_value_established",
        "make research-friction",
    )
    assert implementable is False and investment_value is False, (
        "[MCC-EVIDENCE-STATE] friction claim_safety no longer preserves the approved "
        "non-implementable, non-investment-value state; regenerate via `make research-friction` "
        "and complete MCC review."
    )
    assert evidence_state.get("friction_sensitivity_establishes_implementable_returns") is False, (
        "[MCC-EVIDENCE-STATE] evidence_state.friction_sensitivity_establishes_implementable_returns "
        "must remain false while friction claim_safety.implementable_returns_established is false."
    )
    assert evidence_state.get("investment_value_evaluated") is False, (
        "[MCC-EVIDENCE-STATE] evidence_state.investment_value_evaluated must remain false while "
        "friction claim_safety.investment_value_established is false."
    )
    finding_terms = finding.casefold()
    assert "descriptive assumption sensitivities" in finding_terms and "investment value" in finding_terms, (
        "[MCC-EVIDENCE-CONCLUSION] contract friction finding is no longer anchored to the "
        "report's claim_safety state; complete MCC review."
    )


def _assert_leaderboard_structure(root: Path, finding: str) -> None:
    path = root / "experiments/leaderboard.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required_columns = {"split", "model", "kind", "spearman"}
    assert rows and required_columns <= set(rows[0]), (
        "[MCC-EVIDENCE-SCHEMA] experiments/leaderboard.csv: required walk-forward columns "
        f"{sorted(required_columns)} are missing; regenerate via `make research`."
    )
    observed_splits = {row["split"] for row in rows}
    assert observed_splits == {"test_2023", "test_2024", "test_2025"}, (
        "[MCC-EVIDENCE-STATE] experiments/leaderboard.csv: expected the three approved "
        f"walk-forward test splits, got {sorted(observed_splits)}; regenerate via `make research` "
        "and complete MCC review."
    )
    finding_terms = finding.casefold()
    assert "walk-forward rank signal" in finding_terms and "three test years" in finding_terms, (
        "[MCC-EVIDENCE-CONCLUSION] contract leaderboard finding is no longer anchored to the "
        "approved walk-forward evidence scope; complete MCC review."
    )


def _assert_authority_binding(root: Path, contract: dict[str, object], finding: str) -> None:
    authority_text = (root / "FINANCEIQ_DEMO_AND_CLAIMS_GUIDE.md").read_text(encoding="utf-8")
    approved = contract["approved_wording"]
    assert isinstance(approved, dict)
    disclaimer = approved.get("primary_disclaimer")
    assert isinstance(disclaimer, str) and disclaimer in authority_text, (
        "[MCC-EVIDENCE-CONCLUSION] FINANCEIQ_DEMO_AND_CLAIMS_GUIDE.md no longer contains the "
        "MCC primary disclaimer; complete human claims-authority review."
    )
    assert finding == "Research-support-only claim wording is authoritative.", (
        "[MCC-EVIDENCE-CONCLUSION] contract authority finding changed; complete human "
        "claims-authority review."
    )


def test_mcc_evidence_state_is_bound_to_approved_live_artifacts() -> None:
    contract = _load_json(CONTRACT_PATH)
    evidence_basis = _evidence_basis(contract)
    _assert_binding_ownership(REPO_ROOT, evidence_basis)
    _assert_significance_binding(
        contract,
        evidence_basis["experiments/results/significance_report.md"],
        REPO_ROOT / "experiments/results/significance_report.json",
    )
    _assert_regime_binding(
        contract,
        evidence_basis["experiments/results_regime/regime_context_report.md"],
        REPO_ROOT / "experiments/results_regime/regime_context_report.json",
    )
    _assert_friction_binding(
        contract,
        evidence_basis["experiments/results/friction_report.md"],
        REPO_ROOT / "experiments/results/friction_report.json",
    )
    _assert_leaderboard_structure(REPO_ROOT, evidence_basis["experiments/leaderboard.csv"])
    _assert_authority_binding(
        REPO_ROOT,
        contract,
        evidence_basis["FINANCEIQ_DEMO_AND_CLAIMS_GUIDE.md"],
    )


def test_significance_conclusion_mutation_is_rejected_from_a_temporary_copy(tmp_path: Path) -> None:
    """Prove the drift guard fails without modifying a committed evidence artifact."""
    contract = _load_json(CONTRACT_PATH)
    report_path = tmp_path / "significance_report.json"
    report = _load_json(REPO_ROOT / "experiments/results/significance_report.json")
    headline = report["headline"]
    assert isinstance(headline, dict)
    headline["conclusion"] = "Temporary fixture mutation: conclusion no longer supports the MCC."
    report_path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(AssertionError, match=r"\[MCC-EVIDENCE-CONCLUSION\]"):
        _assert_significance_binding(
            contract,
            _evidence_basis(contract)["experiments/results/significance_report.md"],
            report_path,
        )
