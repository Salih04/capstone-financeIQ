from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.research import real_terms


REPO_ROOT = Path(__file__).resolve().parents[2]
NOMINAL_PATH = REPO_ROOT / "experiments" / "results" / "significance_report.json"
COMPARISON_PATH = REPO_ROOT / "experiments" / "results_real_terms" / "comparison_report.json"
REAL_TRY_PATH = REPO_ROOT / "experiments" / "results_real_terms" / "real_try" / "significance_report.json"
USD_PATH = REPO_ROOT / "experiments" / "results_real_terms" / "usd" / "significance_report.json"
REGIME_PATH = REPO_ROOT / "experiments" / "results_regime" / "regime_context_report.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _clear_cache() -> None:
    real_terms._load_cached.cache_clear()


def _bases_by_id(body: dict) -> dict:
    return {basis["basis_id"]: basis for basis in body["bases"]}


def test_endpoint_success_and_schema() -> None:
    _clear_cache()
    response = TestClient(app).get("/research/return-basis")
    assert response.status_code == 200
    body = response.json()

    assert body["task"] == "R3-UI-02"
    assert body["schema_version"] == 1
    assert set(_bases_by_id(body)) == {"nominal", "real_try", "usd"}
    assert isinstance(body["illustration_2022"], dict)
    assert isinstance(body["source_artifacts"], dict)


def test_each_basis_appears_exactly_once() -> None:
    _clear_cache()
    body = TestClient(app).get("/research/return-basis").json()
    ids = [basis["basis_id"] for basis in body["bases"]]
    assert ids == ["nominal", "real_try", "usd"]
    assert len(ids) == len(set(ids)) == 3


def test_every_basis_pairs_raw_and_adjusted_p() -> None:
    _clear_cache()
    body = TestClient(app).get("/research/return-basis").json()
    for basis in body["bases"]:
        # raw and adjusted live in the same object and neither may be null.
        assert "raw_p_value" in basis
        assert "adjusted_p_value" in basis
        assert basis["raw_p_value"] is not None
        assert basis["adjusted_p_value"] is not None


def test_no_basis_has_raw_p_without_adjusted_p() -> None:
    _clear_cache()
    body = TestClient(app).get("/research/return-basis").json()
    for basis in body["bases"]:
        if basis.get("raw_p_value") is not None:
            assert basis.get("adjusted_p_value") is not None


def test_displayed_numbers_byte_match_source_artifacts() -> None:
    _clear_cache()
    body = TestClient(app).get("/research/return-basis").json()
    bases = _bases_by_id(body)

    expectations = {
        "nominal": (_load(NOMINAL_PATH)["headline"], NOMINAL_PATH),
        "real_try": (_load(REAL_TRY_PATH)["headline"], REAL_TRY_PATH),
        "usd": (_load(USD_PATH)["headline"], USD_PATH),
    }
    for basis_id, (headline, path) in expectations.items():
        basis = bases[basis_id]
        # Exact passthrough — no recomputation, no precision change.
        assert basis["selected_model"] == headline["model"]
        assert basis["pooled_ic"] == headline["observed_ic"]
        assert basis["raw_p_value"] == headline["permutation_p_value_two_sided"]
        assert basis["adjusted_p_value"] == headline["bonferroni_adjusted_p_value"]
        assert basis["significant_fwer_0_05"] == headline["significant_fwer_0_05"]
        assert basis["significance_statement"] == headline["conclusion"]
        assert basis["source_artifact"] == str(path.relative_to(REPO_ROOT))


def test_alternative_bases_agree_with_comparison_report() -> None:
    _clear_cache()
    body = TestClient(app).get("/research/return-basis").json()
    bases = _bases_by_id(body)
    comparison = {b["basis_id"]: b for b in _load(COMPARISON_PATH)["bases"]}

    for basis_id in ("real_try", "usd"):
        headline = comparison[basis_id]["headline"]
        basis = bases[basis_id]
        assert basis["pooled_ic"] == headline["observed_ic"]
        assert basis["raw_p_value"] == headline["permutation_p_value_two_sided"]
        assert basis["adjusted_p_value"] == headline["bonferroni_adjusted_p_value"]


def test_source_provenance_present_for_every_family() -> None:
    _clear_cache()
    body = TestClient(app).get("/research/return-basis").json()
    for basis in body["bases"]:
        assert basis["source_artifact"]
        assert (REPO_ROOT / basis["source_artifact"]).is_file()
    assert set(body["source_artifacts"]) == {
        "nominal",
        "comparison",
        "real_try",
        "usd",
        "alternative_targets",
    }
    for rel in body["source_artifacts"].values():
        assert (REPO_ROOT / rel).is_file()


def test_2022_illustration_matches_committed_values() -> None:
    _clear_cache()
    body = TestClient(app).get("/research/return-basis").json()
    illus = body["illustration_2022"]

    # Nominal 185.94% and 64.27% CPI are byte-identical to the committed regime report.
    regime_2022 = next(
        row for row in _load(REGIME_PATH)["macro_context"] if row["year"] == 2022
    )
    assert illus["nominal_return_pct"] == regime_2022["bist100_return_pct"]["value"] == 185.94
    assert illus["cpi_december_yoy_pct"] == regime_2022["cpi_december_yoy_pct"]["value"] == 64.27
    # Real 74.07% is the METHODOLOGY-authored inflation-basis illustration.
    assert illus["real_return_pct"] == 74.07
    assert illus["source_artifact"] == real_terms._ILLUSTRATION_AUTHORITY
    assert illus["cross_reference_artifact"] == real_terms._ILLUSTRATION_CROSS_REFERENCE


def test_mandatory_backend_owned_copy_is_verbatim() -> None:
    _clear_cache()
    body = TestClient(app).get("/research/return-basis").json()
    assert body["caveat"] == (
        "The no-reliable-edge conclusion was re-evaluated separately on CPI-deflated "
        "TRY and USD bases; neither survives family-wise correction. Basis changes the "
        "unit of measurement, not the conclusion."
    )
    assert body["illustration_2022"]["qualifier"] == (
        "an inflation-basis illustration only, not a strategy-performance or "
        "investment-value statement."
    )


def test_conclusion_is_sourced_from_comparison_claim_safety() -> None:
    _clear_cache()
    body = TestClient(app).get("/research/return-basis").json()
    claim_safety = _load(COMPARISON_PATH)["claim_safety"]
    assert body["conclusion"] == claim_safety["conclusion"]
    assert body["claim_safety"] == claim_safety


def test_response_is_claim_safe() -> None:
    _clear_cache()
    body = TestClient(app).get("/research/return-basis").json()
    serialized = json.dumps(body).lower()
    for forbidden in ("recommendation", "undervalued", "market-beating", "contrarian", "attractive"):
        assert forbidden not in serialized


def test_missing_adjusted_p_cannot_produce_a_valid_response(monkeypatch) -> None:
    doctored = copy.deepcopy(_load(USD_PATH))
    doctored["headline"]["bonferroni_adjusted_p_value"] = None

    real = real_terms._load_report

    def fake_load(rel_path: str):
        if rel_path == real_terms._USD_REPORT_REL:
            return doctored
        return real(rel_path)

    monkeypatch.setattr(real_terms, "_load_report", fake_load)
    with pytest.raises(real_terms.ReturnBasisReportMissing):
        real_terms.payload()


def test_missing_source_file_raises_explicitly(monkeypatch, tmp_path) -> None:
    _clear_cache()

    def fake_root() -> Path:
        return tmp_path  # empty tree — no artifacts

    monkeypatch.setattr(real_terms, "resolve_repo_root", fake_root)
    with pytest.raises(real_terms.ReturnBasisReportMissing):
        real_terms.payload()


def test_missing_source_file_returns_503_from_route(monkeypatch, tmp_path) -> None:
    _clear_cache()

    def fake_root() -> Path:
        return tmp_path

    monkeypatch.setattr(real_terms, "resolve_repo_root", fake_root)
    response = TestClient(app).get("/research/return-basis")
    assert response.status_code == 503
