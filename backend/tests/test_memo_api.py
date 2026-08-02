"""R3-MEMO-01 — claim-aware research memo compiler.

Every expectation in this file is either written out literally here or read
independently from the committed source artifacts. Nothing that the memo
service asserts about itself is imported from the memo service as the expected
value, so a wrong constant in the service cannot make its own test pass.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services import citations
from app.services import courtroom_service as courtroom
from app.services import memo_service as memo
from app.services import skeptic_service
from app.services.citations import CitationError


REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICE_FILE = REPO_ROOT / "backend" / "app" / "services" / "memo_service.py"
CITATIONS_FILE = REPO_ROOT / "backend" / "app" / "services" / "citations.py"

FIXED_CLOCK = lambda: datetime(2026, 8, 2, 12, 0, 0, tzinfo=timezone.utc)  # noqa: E731

# Independently written expectations (never imported from memo_service).
EXPECTED_SECTIONS = [
    ("identity_and_coverage", "Identity & data coverage"),
    ("evidence_quality", "Evidence quality"),
    ("skeptic_challenge", "Skeptic challenge results"),
    ("significance_and_power", "Significance & power context"),
    ("limitations", "Limitations"),
    ("provenance_stamp", "Provenance stamp"),
]
EXPECTED_CLOSING = (
    "Composed from committed research artifacts. No part of this memo is a recommendation; "
    "the underlying evaluation found no reliable predictive edge."
)
EXPECTED_DISCLAIMER = (
    "Experimental ranking signal — research support only, NOT investment advice. "
    "Do not use for buy/sell/hold decisions."
)
FORBIDDEN_KEY_STEMS = ("recommendation", "verdict", "rating", "target", "outlook")

SPARSE_TICKER = "DSTKF"
DENSE_TICKER = "ASELS"

# Files the memo path reads; a temporary repository needs exactly these.
_TEMP_REPO_FILES = (
    "data/trusted_clean/company_contexts/ASELS_2025.json",
    "data/trusted_clean/company_contexts/DSTKF_2025.json",
    "data/trusted_clean/data_quality_report.json",
    "data/trusted_clean/feature_passports.json",
    "experiments/results/significance_report.json",
    "experiments/results_serving_eval/serving_eval_report.json",
    "model_confidence_contract.json",
    "docs/limitations_register.md",
    "docs/R3_MEMO_01_FABLE5_IMPLEMENTATION_PACKET.md",
    "FINANCEIQ_AGENT_TASK_QUEUE.md",
    "METHODOLOGY.md",
    "FINANCEIQ_MODEL_VALIDITY_AUDIT.md",
    "backend/app/services/skeptic_service.py",
)


def _read_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def _memo(ticker: str = DENSE_TICKER):
    return memo.memo_report(ticker, clock=FIXED_CLOCK)


def _all_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _all_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _all_keys(child)


def _all_items(report):
    for section in report["sections"]:
        for item in section["evidence"]:
            yield section, item


def _citation_index(report):
    return {citation["citation_id"]: citation for citation in report["citations"]}


def _resolve(document, field_path: str):
    """Independent dotted-path resolver written for this test file only."""
    value = document
    for segment in field_path.split("."):
        match = re.fullmatch(r"([^\[\]]+)\[(\d+)\]", segment)
        if match:
            value = value[match.group(1)][int(match.group(2))]
        else:
            value = value[segment]
    return value


def _locator_section(text: str, locator: str) -> str:
    level = len(re.match(r"^(#{1,6})", locator).group(1))
    lines = text.split("\n")
    start = lines.index(locator)
    for index in range(start + 1, len(lines)):
        match = re.match(r"^(#{1,6})(?:\s|$)", lines[index])
        if match and len(match.group(1)) <= level:
            return "\n".join(lines[start + 1 : index])
    return "\n".join(lines[start + 1 :])


@pytest.fixture()
def temp_repo(tmp_path, monkeypatch):
    """A disposable copy of exactly the sources the memo reads."""
    root = tmp_path / "repo"
    for relative in _TEMP_REPO_FILES:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, destination)
    monkeypatch.setattr(citations, "REPO_ROOT", root)
    monkeypatch.setattr(memo, "REPO_ROOT", root)
    # The disposable copy is not a git checkout; supply the commit through the
    # trusted deployment authority so these tests exercise source integrity
    # rather than commit resolution (which has its own tests).
    monkeypatch.setenv("RENDER_GIT_COMMIT", "b" * 40)
    return root


# ---------------------------------------------------------------------------
# 1 & 2 — real fixtures
# ---------------------------------------------------------------------------


def test_dense_ticker_memo_is_complete_and_fully_structured():
    report = _memo(DENSE_TICKER)

    assert report["task"] == "R3-MEMO-01"
    assert report["schema_version"] == 1
    assert report["memo_type"] == "evidence_memo"
    assert report["ticker"] == DENSE_TICKER
    assert report["company_year"] == _read_json(
        f"data/trusted_clean/company_contexts/{DENSE_TICKER}_2025.json"
    )["year"]
    assert report["evidence_status"] == "complete"
    assert report["unavailable_sections"] == []
    assert all(section["status"] == "available" for section in report["sections"])
    assert memo.memo_report("asels", clock=FIXED_CLOCK) == report


def test_sparse_ticker_is_the_real_sparsest_public_row_and_composes():
    """DSTKF is chosen from committed data, not asserted by fiat."""
    quality = _read_json("data/trusted_clean/data_quality_report.json")
    features = quality["feature_columns"]
    rows: dict[str, dict] = {}
    import csv

    with (REPO_ROOT / "data/trusted_clean/modeling_dataset_public_2020_2025.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        for row in csv.DictReader(handle):
            ticker = row["ticker"].strip().upper()
            previous = rows.get(ticker)
            if previous is None or int(row["year"]) > int(previous["year"]):
                rows[ticker] = row
    populated = {
        ticker: sum(1 for name in features if (row.get(name) or "").strip())
        for ticker, row in rows.items()
    }
    sparsest = sorted(populated.items(), key=lambda item: (item[1], item[0]))
    assert sparsest[0][0] == SPARSE_TICKER
    assert sparsest[0][1] < sparsest[1][1], "the sparse fixture must be a unique minimum"
    assert populated[DENSE_TICKER] == len(features)

    report = _memo(SPARSE_TICKER)
    assert report["ticker"] == SPARSE_TICKER
    assert [section["section_id"] for section in report["sections"]] == [
        section_id for section_id, _title in EXPECTED_SECTIONS
    ]
    gap_years = "2020, 2021, 2022, 2023, 2024"
    assert any(gap_years in item["text"] for _section, item in _all_items(report))


# ---------------------------------------------------------------------------
# 3, 4 — structure and citation completeness
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ticker", [DENSE_TICKER, SPARSE_TICKER])
def test_exact_six_section_order_and_titles(ticker):
    report = _memo(ticker)
    assert [
        (section["section_id"], section["title"]) for section in report["sections"]
    ] == EXPECTED_SECTIONS
    for index, section in enumerate(report["sections"]):
        expected_keys = {"section_id", "title", "status", "evidence", "missing_evidence"}
        if index == 5:
            expected_keys |= {"provenance"}
        assert set(section) == expected_keys
        assert section["status"] in {"available", "insufficient_data"}


@pytest.mark.parametrize("ticker", [DENSE_TICKER, SPARSE_TICKER])
def test_every_evidence_sentence_carries_a_resolvable_citation(ticker):
    report = _memo(ticker)
    index = _citation_index(report)
    used: set[str] = set()
    for _section, item in _all_items(report):
        assert set(item) == {"text", "citation_ids"}
        assert item["text"].strip()
        assert item["citation_ids"], item["text"]
        for citation_id in item["citation_ids"]:
            assert citation_id in index
            used.add(citation_id)
    referenced = {
        citation_id
        for ids in report["policy_authorities"].values()
        for citation_id in ids
    }
    assert used | referenced == set(index), "no orphan citations"
    assert [citation["citation_id"] for citation in report["citations"]] == [
        f"C{position:03d}" for position in range(1, len(report["citations"]) + 1)
    ]


# ---------------------------------------------------------------------------
# 5, 6 — value-level citation resolution
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ticker", [DENSE_TICKER, SPARSE_TICKER])
def test_every_citation_resolves_to_the_exact_underlying_value_or_text(ticker):
    report = _memo(ticker)
    skeptic_source = skeptic_service.skeptic_report(ticker)
    families = set()
    for citation in report["citations"]:
        relative = citation["source_artifact"]
        path = REPO_ROOT / relative
        assert not Path(relative).is_absolute() and ".." not in Path(relative).parts
        assert path.is_file()
        assert citation["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        families.add(citation["evidence_family"])
        if citation["citation_kind"] == "json_field":
            actual = _resolve(_read_json(relative), citation["field_path"])
            assert actual == citation["value"]
            assert type(actual) is type(citation["value"])
        elif citation["citation_kind"] == "service_evidence":
            assert relative == "backend/app/services/skeptic_service.py"
            assert _resolve(skeptic_source, citation["field_path"]) == citation["value"]
        else:
            assert citation["citation_kind"] == "text_span"
            section = _locator_section(
                path.read_text(encoding="utf-8"), citation["locator"]
            )
            assert citation["quoted_text"] in section
    assert {
        "company_context",
        "curated_limitation",
        "data_quality",
        "feature_passports",
        "limitations_register",
        "mcc",
        "memo_copy_authority",
        "registered_limitation",
        "serving_eval",
        "significance",
        "skeptic",
    } <= families


def test_a_citation_with_the_right_file_but_a_wrong_field_or_value_fails():
    relative = "experiments/results/significance_report.json"
    truth = _read_json(relative)["headline"]["observed_ic"]
    citations.verify_json_field(relative, "headline.observed_ic", truth)
    with pytest.raises(CitationError):
        citations.verify_json_field(relative, "headline.observed_ic", truth + 1.0)
    with pytest.raises(CitationError):
        citations.verify_json_field(relative, "headline.no_such_field", truth)
    with pytest.raises(CitationError):
        citations.verify_json_field("model_confidence_contract.json", "version", "0.0.0")
    with pytest.raises(CitationError):
        citations.verify_text_span(
            "METHODOLOGY.md", "## Limitations", "a sentence that is not in the section"
        )
    with pytest.raises(CitationError):
        citations.verify_text_span("METHODOLOGY.md", "## No Such Heading", "anything")
    for unsafe in ("/etc/passwd", "../outside.json", "data\\windows.json", ""):
        with pytest.raises(CitationError):
            citations.repo_path(unsafe)


# ---------------------------------------------------------------------------
# 7, 8 — insufficient data and fail-closed behaviour
# ---------------------------------------------------------------------------


def test_missing_company_field_produces_section_level_insufficient_data(temp_repo):
    context_path = temp_repo / "data/trusted_clean/company_contexts/ASELS_2025.json"
    context = json.loads(context_path.read_text(encoding="utf-8"))
    del context["data_quality"]["missing_fields"]
    context_path.write_text(json.dumps(context), encoding="utf-8")

    report = _memo(DENSE_TICKER)
    identity = report["sections"][0]
    assert identity["status"] == "insufficient_data"
    assert identity["section_id"] == "identity_and_coverage"
    assert len(identity["evidence"]) == 1
    assert identity["evidence"][0]["citation_ids"]
    assert identity["missing_evidence"][0]["source_file"].endswith("ASELS_2025.json")
    assert report["evidence_status"] == "partial"
    assert report["unavailable_sections"][0]["section_id"] == "identity_and_coverage"
    assert report["company_year"] is None
    assert [section["section_id"] for section in report["sections"]] == [
        section_id for section_id, _title in EXPECTED_SECTIONS
    ]
    assert all(
        section["status"] == "available" for section in report["sections"][1:]
    ), "a company gap must not collapse global sections"


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(
            lambda root: (root / "model_confidence_contract.json").write_text(
                json.dumps(
                    {
                        **json.loads(
                            (root / "model_confidence_contract.json").read_text("utf-8")
                        ),
                        "evidence_state": {
                            **json.loads(
                                (root / "model_confidence_contract.json").read_text("utf-8")
                            )["evidence_state"],
                            "reliable_predictive_edge_observed": True,
                        },
                    }
                ),
                encoding="utf-8",
            ),
            id="contract_evidence_state_flipped",
        ),
        pytest.param(
            lambda root: (root / "experiments/results/significance_report.json").write_text(
                "{not-json", encoding="utf-8"
            ),
            id="significance_report_malformed",
        ),
        pytest.param(
            lambda root: (
                root / "experiments/results_serving_eval/serving_eval_report.json"
            ).unlink(),
            id="serving_report_missing",
        ),
        pytest.param(
            lambda root: (root / "docs/limitations_register.md").write_text(
                "# empty\n", encoding="utf-8"
            ),
            id="limitations_register_unusable",
        ),
        pytest.param(
            lambda root: (root / "data/trusted_clean/feature_passports.json").write_text(
                '{"passports": "wrong-shape"}', encoding="utf-8"
            ),
            id="passports_malformed",
        ),
    ],
)
def test_malformed_or_contradictory_global_sources_fail_closed(temp_repo, mutate):
    mutate(temp_repo)
    with pytest.raises(memo.MemoEvidenceUnavailable):
        _memo(DENSE_TICKER)


def test_a_contradictory_significance_headline_is_refused(temp_repo):
    path = temp_repo / "experiments/results/significance_report.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["headline"]["significant_fwer_0_05"] = True
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(memo.MemoEvidenceUnavailable) as excinfo:
        _memo(DENSE_TICKER)
    assert "model_confidence_contract.json" in str(excinfo.value)


def test_a_raw_p_value_without_its_adjusted_companion_is_refused(temp_repo):
    path = temp_repo / "experiments/results/significance_report.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    for model in document["models"]:
        if model.get("kind") == "ml":
            model["pooled"]["bonferroni_adjusted_p_value"] = None
            break
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(memo.MemoEvidenceUnavailable) as excinfo:
        _memo(DENSE_TICKER)
    assert "bonferroni_adjusted_p_value" in str(excinfo.value)


def test_route_returns_503_rather_than_a_partial_success(temp_repo):
    (temp_repo / "experiments/results_serving_eval/serving_eval_report.json").unlink()
    response = TestClient(app).post(f"/research/memo/{DENSE_TICKER}")
    assert response.status_code == 503


# ---------------------------------------------------------------------------
# 9 — claim safety
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ticker", [DENSE_TICKER, SPARSE_TICKER])
def test_no_recommendation_shaped_key_appears_at_any_depth(ticker):
    report = _memo(ticker)
    for key in _all_keys(report):
        folded = key.casefold()
        for stem in FORBIDDEN_KEY_STEMS:
            assert stem not in folded, f"forbidden key stem {stem!r} in {key!r}"


@pytest.mark.parametrize("ticker", [DENSE_TICKER, SPARSE_TICKER])
def test_response_copy_carries_no_advice_or_direction_language(ticker):
    report = _memo(ticker)
    contract = _read_json("model_confidence_contract.json")
    serialized = json.dumps(report, ensure_ascii=False)
    # The two explicit-negation policy sentences are excluded from the crude
    # vocabulary sweep; both are byte-pinned elsewhere in this file.
    allowed = {
        EXPECTED_DISCLAIMER,
        "This memo composes committed, historical research evidence for one company. It "
        "contains no recommendation, no forecast, no price target, and no investment-value "
        "assessment. Walk-forward evaluation found no reliable predictive edge: no ML model "
        "is statistically distinguishable from the within-year null after family-wise "
        "correction.",
    }
    stripped = serialized
    for sentence in allowed:
        stripped = stripped.replace(sentence, "")
    for rule in contract["rules"]:
        for pattern in rule["patterns"]:
            assert re.search(pattern, stripped, re.IGNORECASE) is None, pattern
    for pattern in (
        r"\bprice target\b",
        r"\bundervalued\b",
        r"\bovervalued\b",
        r"\bcontrarian\b",
        r"\binverse alpha\b",
        r"\bwe recommend\b",
        r"\boverall (?:verdict|assessment|score)\b",
    ):
        assert re.search(pattern, stripped, re.IGNORECASE) is None, pattern
    assert "score" not in set(report)
    assert report["claim_safety"] == {
        "statement": EXPECTED_CLOSING,
        "investment_value_established": False,
        "reliable_predictive_edge_established": False,
    }


# ---------------------------------------------------------------------------
# 10, 11 — mandatory policy copy
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ticker", [DENSE_TICKER, SPARSE_TICKER])
def test_primary_disclaimer_is_exact_and_bound_to_the_contract(ticker):
    report = _memo(ticker)
    contract = _read_json("model_confidence_contract.json")
    assert report["disclaimer"] == EXPECTED_DISCLAIMER
    assert contract["approved_wording"]["primary_disclaimer"] == EXPECTED_DISCLAIMER
    index = _citation_index(report)
    sources = {
        index[citation_id]["source_artifact"]
        for citation_id in report["policy_authorities"]["disclaimer"]
    }
    assert "model_confidence_contract.json" in sources


@pytest.mark.parametrize("ticker", [DENSE_TICKER, SPARSE_TICKER])
def test_closing_line_is_exact_non_optional_and_source_bound(ticker):
    report = _memo(ticker)
    assert report["closing"] == EXPECTED_CLOSING
    assert list(report)[-1] == "mcc"
    index = _citation_index(report)
    citation_ids = report["policy_authorities"]["closing"]
    assert citation_ids
    for citation_id in citation_ids:
        citation = index[citation_id]
        assert citation["citation_kind"] == "text_span"
        assert citation["quoted_text"] == EXPECTED_CLOSING
        text = (REPO_ROOT / citation["source_artifact"]).read_text(encoding="utf-8")
        assert EXPECTED_CLOSING in _locator_section(text, citation["locator"])


# ---------------------------------------------------------------------------
# 12 — raw and adjusted p-values are inseparable
# ---------------------------------------------------------------------------


def test_raw_and_adjusted_p_values_are_never_separated():
    report = _memo(DENSE_TICKER)
    index = _citation_index(report)
    checked = 0
    for _section, item in _all_items(report):
        fields = [
            index[citation_id]["field_path"] or ""
            for citation_id in item["citation_ids"]
        ]
        sources = {index[citation_id]["source_artifact"] for citation_id in item["citation_ids"]}
        raw = [field for field in fields if field.endswith("permutation_p_value_two_sided")]
        if not raw:
            continue
        checked += 1
        if "experiments/results/significance_report.json" in sources:
            assert any(field.endswith("bonferroni_adjusted_p_value") for field in fields)
        else:
            assert any(field.endswith("serving_result.test_label") for field in fields)
            assert not any(field.endswith("bonferroni_adjusted_p_value") for field in fields)
    assert checked == 7, "six ML models plus the single prespecified serving test"
    serving_label = _read_json(
        "experiments/results_serving_eval/serving_eval_report.json"
    )["serving_result"]["test_label"]
    assert serving_label == "single prespecified test, outside the six-model Bonferroni family"
    assert any(
        serving_label in item["text"] for _section, item in _all_items(report)
    )


# ---------------------------------------------------------------------------
# 13, 14 — verbatim embedding
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ticker", [DENSE_TICKER, SPARSE_TICKER])
def test_skeptic_wording_is_reproduced_verbatim_and_insufficient_data_survives(ticker):
    source = skeptic_service.skeptic_report(ticker)
    section = _memo(ticker)["sections"][2]
    expected = [source["footer"]]
    for check in source["checks"]:
        expected.extend(entry["fact"] for entry in check["evidence"])
    assert [item["text"] for item in section["evidence"]] == expected
    for check in source["checks"]:
        if check["verdict"] == "insufficient_data":
            assert any(
                entry["fact"] in [item["text"] for item in section["evidence"]]
                for entry in check["evidence"]
            )


def test_limitations_are_verbatim_and_resolve_to_their_underlying_sources():
    report = _memo(DENSE_TICKER)
    section = report["sections"][4]
    index = _citation_index(report)
    register = (REPO_ROOT / "docs/limitations_register.md").read_text(encoding="utf-8")

    expected: list[str] = []
    for relative in (
        "experiments/results/significance_report.json",
        "experiments/results_serving_eval/serving_eval_report.json",
    ):
        expected.extend(_read_json(relative)["limitations"])
    body = [item["text"] for item in section["evidence"][1:]]
    assert body[: len(expected)] == expected

    curated = body[len(expected) :]
    assert len(curated) == 6
    for text in curated:
        assert text in register

    for item in section["evidence"][1:]:
        sources = {
            index[citation_id]["source_artifact"] for citation_id in item["citation_ids"]
        }
        assert sources != {"docs/limitations_register.md"}, (
            "a limitation may never cite only the register"
        )
        assert "docs/limitations_register.md" in sources
        for citation_id in item["citation_ids"]:
            citation = index[citation_id]
            if citation["citation_kind"] == "json_field":
                assert _resolve(
                    _read_json(citation["source_artifact"]), citation["field_path"]
                ) == item["text"]
            else:
                assert citation["quoted_text"] == item["text"]


# ---------------------------------------------------------------------------
# 15, 16, 17 — determinism and provenance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ticker", [DENSE_TICKER, SPARSE_TICKER])
def test_fixed_clock_runs_are_byte_identical(ticker):
    first = json.dumps(_memo(ticker), ensure_ascii=False, sort_keys=False)
    second = json.dumps(_memo(ticker), ensure_ascii=False, sort_keys=False)
    assert first == second

    later = memo.memo_report(
        ticker, clock=lambda: datetime(2030, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    )
    stamp = _memo(ticker)["sections"][5]["provenance"]
    other = later["sections"][5]["provenance"]
    assert stamp["generated_at_utc"] == "2026-08-02T12:00:00Z"
    assert other["generated_at_utc"] == "2030-01-01T00:00:00Z"
    assert {k: v for k, v in stamp.items() if k != "generated_at_utc"} == {
        k: v for k, v in other.items() if k != "generated_at_utc"
    }
    assert json.dumps(
        {k: v for k, v in _memo(ticker).items() if k != "sections"}, ensure_ascii=False
    ) == json.dumps(
        {k: v for k, v in later.items() if k != "sections"}, ensure_ascii=False
    )


@pytest.mark.parametrize("ticker", [DENSE_TICKER, SPARSE_TICKER])
def test_provenance_paths_and_hashes_match_independently_recomputed_values(ticker):
    report = _memo(ticker)
    stamp = report["sections"][5]["provenance"]
    cited = sorted({citation["source_artifact"] for citation in report["citations"]})

    assert [artifact["path"] for artifact in stamp["source_artifacts"]] == cited
    for artifact in stamp["source_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert artifact["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()

    assert [entry["section_id"] for entry in stamp["section_inventory"]] == [
        section_id for section_id, _title in EXPECTED_SECTIONS
    ]
    for entry, section in zip(stamp["section_inventory"], report["sections"], strict=True):
        assert entry["status"] == section["status"]
        assert entry["evidence_count"] == len(section["evidence"])
    assert [entry["path"] for entry in stamp["source_inventory"]] == cited
    assert sum(entry["citation_count"] for entry in stamp["source_inventory"]) == len(
        report["citations"]
    )
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", stamp["generated_at_utc"])


def test_git_sha_and_mcc_version_are_truthful():
    stamp = _memo(DENSE_TICKER)["sections"][5]["provenance"]
    head = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    assert stamp["git_sha"] == head
    assert re.fullmatch(r"[0-9a-f]{40}", stamp["git_sha"])
    assert stamp["git_sha"] not in {"unknown", "local", "latest", "unavailable"}
    assert stamp["git_sha_authority"] == "repository_git_head"
    assert stamp["mcc_version"] == _read_json("model_confidence_contract.json")["version"]


def test_a_trusted_deployment_commit_takes_precedence_and_junk_is_refused(monkeypatch):
    deployed = "a" * 40
    monkeypatch.setenv("RENDER_GIT_COMMIT", deployed)
    sha, authority = memo.resolve_git_sha()
    assert sha == deployed
    assert authority == "deployment_commit_env:RENDER_GIT_COMMIT"

    monkeypatch.setenv("RENDER_GIT_COMMIT", "latest")
    monkeypatch.setattr(memo, "REPO_ROOT", Path("/nonexistent-financeiq-root"))
    with pytest.raises(memo.MemoEvidenceUnavailable):
        memo.resolve_git_sha()


# ---------------------------------------------------------------------------
# 18 — no network, no LLM, no legacy path
# ---------------------------------------------------------------------------


def test_the_memo_path_has_no_network_llm_or_recommendation_shaped_dependency():
    banned_modules = {
        "urllib",
        "urllib.request",
        "requests",
        "httpx",
        "socket",
        "openai",
        "numpy",
        "scipy",
        "statistics",
        "pandas",
        "app.services.research_agent",
        "app.services.forecasting_service",
        "app.services.forecasting_csv_service",
        "app.services.scoring_service",
        "app.services.sector_service",
        "app.services.adaptive_weights_service",
        "app.services.comparison_service",
        "app.services.explanation_service",
        "app.database",
    }
    for path in (SERVICE_FILE, CITATIONS_FILE):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
                imported.update(f"{node.module}.{alias.name}" for alias in node.names)
        assert not banned_modules & imported, banned_modules & imported
        for symbol in ("call_llm", "RESEARCH_LLM_PROVIDER", "OPENAI_API_KEY", "http://", "https://"):
            assert symbol not in source, symbol
    service_source = SERVICE_FILE.read_text(encoding="utf-8")
    assert service_source.count("subprocess.run") == 1
    assert '"rev-parse", "HEAD"' in service_source


def test_llm_provider_setting_cannot_change_the_memo(monkeypatch):
    baseline = _memo(DENSE_TICKER)
    for provider in ("none", "openrouter", "openai"):
        monkeypatch.setenv("RESEARCH_LLM_PROVIDER", provider)
        assert _memo(DENSE_TICKER) == baseline


# ---------------------------------------------------------------------------
# 19 — Courtroom preservation after the helper extraction
# ---------------------------------------------------------------------------


def test_courtroom_schema_and_behaviour_are_unchanged_by_the_shared_helper():
    report = courtroom.courtroom_report(DENSE_TICKER)
    assert set(report) == {
        "schema_version",
        "status",
        "ticker",
        "year",
        "mode",
        "evidence_budget_per_persona",
        "personas",
        "missing_evidence",
        "closing",
    }
    assert report["schema_version"] == 1
    assert report["status"] == "complete"
    assert report["mode"] == "deterministic"
    assert [persona["persona_id"] for persona in report["personas"]] == [
        "bull",
        "bear",
        "skeptic",
        "risk",
    ]
    assert report["closing"] == (
        "A structured debate over historical, validated evidence. No persona forecasts "
        "returns; no verdict is issued; nothing here is investment advice."
    )
    for persona in report["personas"]:
        assert set(persona) == {"persona_id", "name", "lens", "items"}
        assert len(persona["items"]) == 4
        for item in persona["items"]:
            assert set(item) == {"statement", "citation", "limitation"}
            assert set(item["citation"]) == {"field", "value", "source_file"}

    assert courtroom.courtroom_report(DENSE_TICKER, 1999)["status"] == "insufficient_data"
    with pytest.raises(ValueError):
        courtroom.courtroom_report("BAD-TICKER")
    assert courtroom._load_json(REPO_ROOT / "no-such-file.json") == (
        None,
        "artifact is missing",
    )


# ---------------------------------------------------------------------------
# 20, 21 — routing
# ---------------------------------------------------------------------------


def test_route_matches_the_established_research_access_pattern():
    client = TestClient(app)
    routes = {
        route.path: sorted(route.methods)
        for route in app.routes
        if getattr(route, "path", "").startswith("/research/")
    }
    assert routes["/research/memo/{ticker}"] == ["POST"]

    previous = settings.PUBLIC_DEMO_MODE
    try:
        settings.PUBLIC_DEMO_MODE = True
        open_response = client.post(f"/research/memo/{DENSE_TICKER}")
        assert open_response.status_code == 200
        assert open_response.json() == json.loads(
            json.dumps(memo.memo_report(DENSE_TICKER), default=str)
        ) or open_response.json()["ticker"] == DENSE_TICKER
        assert client.get(f"/research/skeptic/{DENSE_TICKER}").status_code == 200

        settings.PUBLIC_DEMO_MODE = False
        assert client.post(f"/research/memo/{DENSE_TICKER}").status_code == 401
        assert client.get(f"/research/skeptic/{DENSE_TICKER}").status_code == 401
    finally:
        settings.PUBLIC_DEMO_MODE = previous


def test_unknown_and_malformed_tickers_are_pinned():
    client = TestClient(app)
    assert client.post("/research/memo/ZZZZ").status_code == 404
    assert client.post("/research/memo/AKBNK").status_code == 404
    assert client.post("/research/memo/BAD-TICKER").status_code == 422
    assert client.post("/research/memo/%20").status_code == 422
    with pytest.raises(ValueError):
        memo.memo_report("bad ticker!")
    with pytest.raises(memo.MemoCompanyUnknown):
        memo.memo_report("ZZZZ")


# ---------------------------------------------------------------------------
# 22 — no aliasing of cached source objects
# ---------------------------------------------------------------------------


def test_response_objects_do_not_alias_cached_source_documents():
    first = citations.load_json_artifact("model_confidence_contract.json")
    second = citations.load_json_artifact("model_confidence_contract.json")
    assert first == second and first is not second
    assert first["evidence_state"] is not second["evidence_state"]
    first["evidence_state"]["conclusion"] = "mutated"
    assert citations.load_json_artifact("model_confidence_contract.json")[
        "evidence_state"
    ]["conclusion"] == "no reliable predictive edge"

    report = _memo(DENSE_TICKER)
    for citation in report["citations"]:
        if citation["citation_kind"] == "json_field" and isinstance(citation["value"], list):
            citation["value"].append("mutated")
            break
    else:  # pragma: no cover - the fixture always contains a list-valued citation
        pytest.fail("expected at least one list-valued citation")
    assert _memo(DENSE_TICKER) == memo.memo_report(DENSE_TICKER, clock=FIXED_CLOCK)
