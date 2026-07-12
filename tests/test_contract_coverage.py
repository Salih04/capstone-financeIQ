"""Guard Model Confidence Contract coverage of routed React data pages."""

from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = REPO_ROOT / "frontend/src/App.jsx"
CONTRACT_PATH = REPO_ROOT / "model_confidence_contract.json"
PAGE_IMPORT = re.compile(
    r"^import\s+(?P<component>\w+)\s+from\s+'(?P<path>\./pages/\w+)'$",
    re.MULTILINE,
)
ROUTE_LINE = re.compile(r"^.*<Route\s+.*element=.*$", re.MULTILINE)
PAGE_COMPONENT = re.compile(r"<(?P<component>\w+Page)\b")


def _routed_page_paths(app_source: str) -> set[str]:
    """Map simply imported page components used in route elements to JSX paths."""
    imports = {
        match.group("component"): f"frontend/src/pages/{match.group('path').split('/')[-1]}.jsx"
        for match in PAGE_IMPORT.finditer(app_source)
    }
    route_components = {
        match.group("component")
        for route_line in ROUTE_LINE.findall(app_source)
        for match in PAGE_COMPONENT.finditer(route_line)
    }
    return {imports[component] for component in route_components & imports.keys()}


def _unregistered_routes(app_source: str, contract: dict[str, object]) -> set[str]:
    disclaimer = contract["required_disclaimer"]
    assert isinstance(disclaimer, dict)
    direct_pages = set(disclaimer["pages"])
    aliases = set(disclaimer["route_aliases"])
    exempt_pages = {entry["path"] for entry in disclaimer["exempt_pages"]}
    return _routed_page_paths(app_source) - direct_pages - aliases - exempt_pages


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_every_routed_page_is_registered_or_explicitly_exempted():
    missing = _unregistered_routes(APP_PATH.read_text(encoding="utf-8"), _contract())
    assert not missing, f"Routed pages missing Model Confidence Contract registration: {sorted(missing)}"


def test_unregistered_fake_route_is_detected_by_the_coverage_guard():
    fake_route = "\nimport FakeRoutePage from './pages/FakeRoutePage'\n<Route path=\"/fake\" element={<FakeRoutePage />} />\n"
    missing = _unregistered_routes(
        APP_PATH.read_text(encoding="utf-8") + fake_route,
        _contract(),
    )
    assert missing == {"frontend/src/pages/FakeRoutePage.jsx"}


def test_exempt_pages_have_reasons_and_versioning_policy_is_present():
    contract = _contract()
    disclaimer = contract["required_disclaimer"]
    assert isinstance(disclaimer, dict)
    assert all(entry["reason"].strip() for entry in disclaimer["exempt_pages"])
    procedure = contract["versioning_procedure"]
    assert isinstance(procedure, dict)
    assert "minor" in procedure["minor_bump"].casefold()
    assert "patch" in procedure["patch_bump"].casefold()
