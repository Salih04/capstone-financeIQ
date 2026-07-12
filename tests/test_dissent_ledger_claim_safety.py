from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPONENT_PATH = ROOT / "frontend" / "src" / "components" / "DissentLedger.jsx"
SERVICE_PATH = ROOT / "backend" / "app" / "services" / "analyst_verdict_service.py"
CONTRACT_PATH = ROOT / "model_confidence_contract.json"
BOUNDARY = "Records disagreement for research; never a score input."


def test_both_existing_labs_render_the_same_pinned_boundary():
    component = COMPONENT_PATH.read_text(encoding="utf-8")
    assert BOUNDARY in component
    assert "not consensus, a recommendation, or a crowd signal" in component
    assert "not investment advice" in component

    for page_name in ("LabelingLabPage.jsx", "ValidationLabPage.jsx"):
        page = (ROOT / "frontend" / "src" / "pages" / page_name).read_text(encoding="utf-8")
        assert "import DissentLedger from '../components/DissentLedger'" in page
        assert "<DissentLedger />" in page


def test_contract_registers_the_dissent_boundary_and_response_service():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert contract["version"] == "1.7.0"
    assert contract["approved_wording"]["dissent_ledger_boundary"] == BOUNDARY
    assert "backend/app/services/analyst_verdict_service.py" in contract["scan"]["backend_response_files"]
    assert contract["evidence_state"]["reliable_predictive_edge_observed"] is False


def test_dissent_storage_is_absent_from_scoring_and_trusted_data_paths():
    forbidden_consumers = (
        "backend/app/routers/scoring.py",
        "backend/app/services/scoring_service.py",
        "backend/app/services/forecasting_csv_service.py",
        "experiments/run_experiments.py",
        "scripts/data_collection/build_all.py",
    )
    for relative_path in forbidden_consumers:
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "AnalystVerdict" not in source
        assert "analyst_verdicts" not in source

    service = SERVICE_PATH.read_text(encoding="utf-8")
    assert "from app.services.scoring_service" not in service
    assert "data/trusted" not in service
