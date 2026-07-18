from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE_PATH = ROOT / "frontend/src/pages/CourtroomPage.jsx"
SERVICE_PATH = ROOT / "backend/app/services/courtroom_service.py"
CONTRACT_PATH = ROOT / "model_confidence_contract.json"


def test_courtroom_surface_is_registered_and_pins_no_adjudication_structure():
    page = PAGE_PATH.read_text(encoding="utf-8")
    service = SERVICE_PATH.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert contract["version"] == "1.8.0"
    assert "frontend/src/pages/CourtroomPage.jsx" in contract["required_disclaimer"]["pages"]
    assert "backend/app/services/courtroom_service.py" in contract["scan"]["backend_response_files"]
    assert 'PERSONA_ORDER = ("bull", "bear", "skeptic", "risk")' in service
    assert "EVIDENCE_BUDGET = 4" in service
    assert '"personas": []' in service
    assert '"status": "insufficient_data"' in service
    assert "riskLast(report?.personas)" in page
    assert ".cq-persona.is-risk" in page
    assert "position: sticky" in page
    assert "Historical research support only · Not investment advice." in page


def test_courtroom_copy_has_no_unsafe_adjudication_or_return_claim_language():
    text = "\n".join(
        [
            PAGE_PATH.read_text(encoding="utf-8"),
            SERVICE_PATH.read_text(encoding="utf-8"),
        ]
    )
    closing = (
        "A structured debate over historical, validated evidence. No persona forecasts "
        "returns; no verdict is issued; nothing here is investment advice."
    )
    assert "A structured debate over historical, validated evidence. No persona forecasts " in text
    assert "returns; no verdict is issued; nothing here is investment advice." in text
    assert text.casefold().count("verdict") == 1
    checked = text.replace(closing, "")
    for pattern in (
        r"\b(?:buy|sell|hold)\b",
        r"\bwinner\b",
        r"\bconsensus(?: score)?\b",
        r"\bexpected[-_ ]returns?\b",
        r"\bmarket[-\s]beating\b",
        r"\bprofitable\s+trad(?:e|es|ing)\b",
        r"\b(?:issues?|renders?|reaches?)\s+(?:a\s+)?verdict\b",
    ):
        assert re.search(pattern, checked, flags=re.IGNORECASE) is None


def test_courtroom_api_items_require_exact_citation_and_limitation_fields():
    service = SERVICE_PATH.read_text(encoding="utf-8")

    assert 'return {"field": field, "value": value, "source_file": source_file}' in service
    assert '"statement": statement' in service
    assert '"citation": _citation(field, value, source_file)' in service
    assert '"limitation": limitation' in service
