from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "frontend" / "src" / "pages" / "AutopsyPage.jsx"
REPORT = ROOT / "experiments" / "results" / "friction_report.json"
CONTRACT = ROOT / "model_confidence_contract.json"


def test_autopsy_friction_panel_has_in_drawing_stamp_and_scope_boundaries() -> None:
    page = PAGE.read_text(encoding="utf-8")
    report = json.loads(REPORT.read_text(encoding="utf-8"))

    assert report["chart_stamp"] in page
    assert '<foreignObject x="18" y="12" width="884" height="42">' in page
    assert '<div className="ap-friction-stamp">{stamp}</div>' in page
    assert "81-ticker training universe, nominal TRY." in page
    assert "raw score magnitudes never cross model boundaries" in page
    assert "not realizable returns or investment value" in page
    assert "CPI-deflated TRY and USD-basis evidence remain separate" in page
    assert "No bid–ask spread, market impact, liquidity, capacity, or tradeability is inferred." in page


def test_contract_registers_friction_evidence_and_passthrough_service() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert contract["version"] == "1.7.0"
    assert contract["evidence_state"]["friction_sensitivity_establishes_implementable_returns"] is False
    assert "backend/app/services/research/significance.py" in contract["scan"]["backend_response_files"]
    assert any(item["path"] == "experiments/results/friction_report.md" for item in contract["evidence_basis"])


def test_friction_outputs_exclude_wealth_path_and_horizon_scaling_series() -> None:
    paths = [
        ROOT / "experiments" / "friction_sim.py",
        ROOT / "experiments" / "results" / "friction_report.json",
        ROOT / "experiments" / "results" / "friction_report.md",
        ROOT / "experiments" / "results" / "friction_plot.csv",
        PAGE,
    ]
    text = "\n".join(path.read_text(encoding="utf-8").casefold() for path in paths)
    forbidden = ["cum" + "prod", "cum" + "ulative", "annual" + "ized", "com" + "pounded"]

    for term in forbidden:
        assert term not in text
