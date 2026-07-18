from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE_PATH = ROOT / "frontend" / "src" / "pages" / "AutopsyPage.jsx"
CONTRACT_PATH = ROOT / "model_confidence_contract.json"

CAVEAT = (
    "This page documents evidence consistent with why no reliable signal was found: "
    "unstable feature relationships, overfitting under small n, sparse coverage, low "
    "statistical power, and a single macro regime. It explains the negative result; "
    "it does not promise a positive one under other conditions."
)


def test_autopsy_page_pins_claim_safe_findings_and_limitations():
    page = PAGE_PATH.read_text(encoding="utf-8")

    assert CAVEAT in page
    assert "Research support only · Not investment advice." in page
    assert page.count("This is consistent with") == 6
    assert page.count("it does not prove") == 6
    assert "Raw p=0.0183 and adjusted p=0.1098 stay paired." in page
    assert "not Bonferroni-adjusted family-wise power" in page
    assert "retrospectively fixed cohort" in page
    assert "nominal TRY" in page
    assert "environment-qualified" in page


def test_autopsy_page_has_no_recommendation_or_trading_claim_surface():
    page = PAGE_PATH.read_text(encoding="utf-8")
    forbidden = (
        r"\brecommendations?\b",
        r"\bverdicts?\b",
        r"\bexpected returns?\b",
        r"\bmarket[-\s]beating\b",
        r"\bprofitable trad(?:e|es|ing)\b",
    )

    for pattern in forbidden:
        assert re.search(pattern, page, flags=re.IGNORECASE) is None


def test_autopsy_sources_and_contract_registration_are_explicit():
    page = PAGE_PATH.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    for source in (
        "experiments/results/feature_stability_by_split.csv",
        "experiments/results/feature_stability_summary.csv",
        "experiments/results/coverage_impact.csv",
        "experiments/leaderboard.csv",
        "experiments/results/significance_report.json",
        "METHODOLOGY.md",
    ):
        assert source in page

    assert contract["version"] == "1.8.0"
    assert "frontend/src/pages/AutopsyPage.jsx" in contract["required_disclaimer"]["pages"]
