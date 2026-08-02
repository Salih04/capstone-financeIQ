"""Tests for the registry-driven automated limitations register."""

from __future__ import annotations

import glob
import json
from dataclasses import replace
from pathlib import Path

import pytest

from scripts import build_limitations_register as register


REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "artifact_registry.json"
OUTPUT_PATH = REPO_ROOT / "docs/limitations_register.md"
BANNER = "GENERATED — regenerate via make limitations-register; do not hand-edit"

# Independent expectations: these are deliberately repeated here rather than
# being read from register.CURATED_SEEDS, so the tests can detect a curated
# constant that was accidentally changed, omitted, or rendered from another
# source.
EXPECTED_CURATED = {
    "retrospective cohort": {
        "source_path": "METHODOLOGY.md",
        "source_locator": "## Limitations",
        "source_text": (
            "Results therefore describe a retrospectively fixed repository\n"
            "  cohort and retain unresolved survivorship and universe-selection look-ahead\n"
            "  risk; missing history was not inferred or filled."
        ),
    },
    "sector unpopulated": {
        "source_path": "METHODOLOGY.md",
        "source_locator": "### Important data reality: source fields are mixed-quality",
        "source_text": (
            "`sector` identity column exists but is\n"
            "  currently unpopulated; it is not an accepted modeling feature."
        ),
    },
    "one regime": {
        "source_path": "METHODOLOGY.md",
        "source_locator": "## Regime Lens (R2-REGIME-01)",
        "source_text": (
            "2020–2025\n"
            "spans a single extraordinary Turkish macro regime (high inflation, deep TRY\n"
            "depreciation). Model behavior across regimes is therefore untested — this lens\n"
            "shows regime context and will only compute regime-conditional diagnostics when\n"
            "regime diversity exists."
        ),
    },
    "environment-qualified reproduction": {
        "source_path": "METHODOLOGY.md",
        "source_locator": "## Reproducibility and run provenance",
        "source_text": (
            "When the numerical\n"
            "environment differs, byte drift is reported explicitly and only semantic\n"
            "leaderboard reproduction within that strict tolerance can pass."
        ),
    },
    "manual shares": {
        "source_path": "FINANCEIQ_MODEL_VALIDITY_AUDIT.md",
        "source_locator": "## 6. Dataset limitations",
        "source_text": "Shares outstanding is manual — derived valuation is null until supplied.",
    },
    "deployment unverified": {
        "source_path": "FINANCEIQ_MODEL_VALIDITY_AUDIT.md",
        "source_locator": "## 16. Claims that must be avoided",
        "source_text": "Production-readiness or live-deployment claims (deployment liveness is unverified).",
    },
}


def independent_registered_json_paths(root: Path) -> list[str]:
    """Resolve the registry independently of the generator implementation."""

    registry = json.loads((root / "artifact_registry.json").read_text(encoding="utf-8"))
    paths: set[str] = set()
    for entry in registry["entries"]:
        for raw in glob.glob(str(root / entry["path_or_glob"]), recursive=True):
            path = Path(raw)
            if path.is_file() and path.suffix.casefold() == ".json":
                paths.add(path.resolve().relative_to(root.resolve()).as_posix())
    return sorted(paths)


def independent_limitations(root: Path) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for relative in independent_registered_json_paths(root):
        payload = json.loads((root / relative).read_text(encoding="utf-8"))
        if "limitations" in payload:
            assert isinstance(payload["limitations"], list)
            found[relative] = payload["limitations"]
    return found


def section_for(document: str, heading: str) -> str:
    start = document.index(heading) + len(heading)
    remainder = document[start:]
    next_heading = remainder.find("\n### ")
    return remainder if next_heading == -1 else remainder[:next_heading]


def independent_locator_section(document: str, locator: str) -> str:
    """Slice a cited section without reusing the generator's implementation."""

    level = len(locator) - len(locator.lstrip("#"))
    lines = document.split("\n")
    start = lines.index(locator)
    for offset, line in enumerate(lines[start + 1 :], start=start + 1):
        stripped = line.lstrip("#")
        depth = len(line) - len(stripped)
        if 0 < depth <= level and (stripped.startswith(" ") or not stripped):
            return "\n".join(lines[start + 1 : offset])
    return "\n".join(lines[start + 1 :])


def write_curated_sources(root: Path, seeds: tuple[register.CuratedSeed, ...]) -> None:
    """Write fixture sources in which every seed quotation sits under its locator."""

    blocks: dict[str, list[str]] = {}
    for seed in seeds:
        blocks.setdefault(seed.source_path, []).append(
            f"{seed.source_locator}\n\nfixture prelude\n{seed.source_text}\n"
        )
    for source_path, chunks in blocks.items():
        target = root / source_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# Fixture source\n\n" + "\n".join(chunks), encoding="utf-8")


def seeds_with_replacement(concept: str, **changes: object) -> tuple[register.CuratedSeed, ...]:
    """Return the full seed set with one member replaced, preserving concept coverage."""

    return tuple(
        replace(seed, **changes) if seed.concept == concept else seed
        for seed in register.CURATED_SEEDS
    )


def make_fixture_repo(tmp_path: Path, payload: object, *, raw_json: str | None = None) -> Path:
    root = tmp_path / "fixture-repo"
    reports = root / "reports"
    reports.mkdir(parents=True)
    (root / "artifact_registry.json").write_text(
        json.dumps(
            {
                "entries": [
                    {"path_or_glob": "reports/report.json"},
                ]
            }
        ),
        encoding="utf-8",
    )
    (reports / "report.json").write_text(
        raw_json if raw_json is not None else json.dumps(payload),
        encoding="utf-8",
    )
    return root


def test_generated_banner_exists() -> None:
    assert BANNER in OUTPUT_PATH.read_text(encoding="utf-8")


def test_generated_file_equals_fresh_generator_output() -> None:
    assert OUTPUT_PATH.read_bytes() == register.generate_document(REPO_ROOT).encode("utf-8")


def test_two_consecutive_generations_are_byte_identical() -> None:
    first = register.generate_document(REPO_ROOT).encode("utf-8")
    second = register.generate_document(REPO_ROOT).encode("utf-8")
    assert first == second


def test_every_registered_limitations_artifact_contributes_and_is_rendered() -> None:
    document = OUTPUT_PATH.read_text(encoding="utf-8")
    expected = independent_limitations(REPO_ROOT)
    assert expected
    for relative, limitations in expected.items():
        heading = f"### {relative}"
        assert document.count(heading) == 1
        section = section_for(document, heading)
        assert limitations
        for limitation in limitations:
            assert limitation in section


def test_registered_limitations_artifact_order_and_entry_order_are_preserved() -> None:
    document = OUTPUT_PATH.read_text(encoding="utf-8")
    expected = independent_limitations(REPO_ROOT)
    paths = list(expected)
    assert [document.index(f"### {path}") for path in paths] == sorted(
        document.index(f"### {path}") for path in paths
    )
    for path, limitations in expected.items():
        section = section_for(document, f"### {path}")
        positions = [section.index(limitation) for limitation in limitations]
        assert positions == sorted(positions)


def test_overlapping_registry_patterns_deduplicate_a_source_artifact(tmp_path: Path) -> None:
    root = tmp_path / "fixture-repo"
    reports = root / "reports"
    reports.mkdir(parents=True)
    (root / "artifact_registry.json").write_text(
        json.dumps(
            {
                "entries": [
                    {"path_or_glob": "reports/**/*.json"},
                    {"path_or_glob": "reports/report.json"},
                ]
            }
        ),
        encoding="utf-8",
    )
    (reports / "report.json").write_text(
        json.dumps({"limitations": ["one registered limitation"]}), encoding="utf-8"
    )

    resolved = register.resolve_registered_json_paths(root)
    assert list(resolved) == ["reports/report.json"]
    artifacts = register.discover_registered_limitations(root)
    assert [artifact.path for artifact in artifacts] == ["reports/report.json"]
    assert artifacts[0].limitations == ("one registered limitation",)


def test_unregistered_json_is_not_scanned(tmp_path: Path) -> None:
    root = make_fixture_repo(tmp_path, {"limitations": ["registered"]})
    (root / "unregistered.json").write_text(
        json.dumps({"limitations": ["must not be discovered"]}), encoding="utf-8"
    )
    artifacts = register.discover_registered_limitations(root)
    assert [artifact.path for artifact in artifacts] == ["reports/report.json"]


def test_no_registered_limitations_artifact_is_silently_omitted() -> None:
    expected = independent_limitations(REPO_ROOT)
    discovered = {artifact.path: artifact for artifact in register.discover_registered_limitations(REPO_ROOT)}
    assert set(discovered) == set(expected)
    assert all(discovered[path].limitations for path in expected)


def test_curated_entries_have_independent_citations_and_exact_source_text() -> None:
    document = OUTPUT_PATH.read_text(encoding="utf-8")
    actual = {seed.concept: seed for seed in register.CURATED_SEEDS}
    assert set(actual) == set(EXPECTED_CURATED)
    for concept, expected in EXPECTED_CURATED.items():
        seed = actual[concept]
        source = (REPO_ROOT / expected["source_path"]).read_text(encoding="utf-8")
        assert seed.source_path == expected["source_path"]
        assert seed.source_locator == expected["source_locator"]
        assert seed.source_text == expected["source_text"]
        assert expected["source_text"] in source
        assert expected["source_text"] in document
        assert f"Source: `{expected['source_path']}`" in document
        assert f"Locator: `{expected['source_locator']}`" in document


def test_curated_quotations_sit_inside_their_declared_locator_sections() -> None:
    """Every citation must resolve positionally, not merely somewhere in the file."""

    for concept, expected in EXPECTED_CURATED.items():
        document = (REPO_ROOT / expected["source_path"]).read_text(encoding="utf-8")
        section = independent_locator_section(document, expected["source_locator"])
        assert expected["source_text"] in section, concept


def test_corrected_sector_locator_replaces_the_section_that_lacks_the_quotation() -> None:
    """The DATA-06 heading does not contain the sector quotation; the data-reality one does."""

    document = (REPO_ROOT / "METHODOLOGY.md").read_text(encoding="utf-8")
    quotation = (
        "`sector` identity column exists but is\n"
        "  currently unpopulated; it is not an accepted modeling feature."
    )
    superseded = "### Sector-label provenance and sample sizes (DATA-06 audit, 2026-07-12)"
    corrected = "### Important data reality: source fields are mixed-quality"

    assert superseded in document
    assert quotation not in independent_locator_section(document, superseded)
    assert quotation in independent_locator_section(document, corrected)

    seed = next(s for s in register.CURATED_SEEDS if s.concept == "sector unpopulated")
    assert seed.source_locator == corrected
    assert f"Locator: `{corrected}`" in OUTPUT_PATH.read_text(encoding="utf-8")
    assert superseded not in OUTPUT_PATH.read_text(encoding="utf-8")


def test_locator_section_stops_at_the_next_same_or_higher_level_heading() -> None:
    document = (
        "# Title\n\n"
        "## Alpha\n\nalpha body\n\n"
        "### Alpha child\n\nchild body\n\n"
        "## Beta\n\nbeta body\n"
    )
    seed = replace(register.CURATED_SEEDS[0], source_locator="## Alpha")
    section = register.locator_section(seed, document)
    assert "alpha body" in section
    assert "child body" in section
    assert "beta body" not in section


def test_quotation_present_elsewhere_but_outside_its_locator_section_fails_closed(
    tmp_path: Path,
) -> None:
    root = tmp_path / "fixture-repo"
    root.mkdir()
    write_curated_sources(root, register.CURATED_SEEDS)
    decoy = "## Decoy section without the quotation"
    methodology = root / "METHODOLOGY.md"
    methodology.write_text(
        methodology.read_text(encoding="utf-8") + f"\n{decoy}\n\nunrelated prose\n",
        encoding="utf-8",
    )

    seeds = seeds_with_replacement("sector unpopulated", source_locator=decoy)
    with pytest.raises(register.LimitationsRegisterError, match="outside its cited section"):
        register.validate_curated_seeds(root, seeds)

    # The unmodified seed set still validates against the same fixture sources.
    assert register.validate_curated_seeds(root, register.CURATED_SEEDS)


def test_missing_locator_heading_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "fixture-repo"
    root.mkdir()
    write_curated_sources(root, register.CURATED_SEEDS)
    seeds = seeds_with_replacement("one regime", source_locator="## No such heading")
    with pytest.raises(
        register.LimitationsRegisterError, match="source_locator heading was not found"
    ):
        register.validate_curated_seeds(root, seeds)


def test_duplicate_locator_heading_fails_closed_as_ambiguous(tmp_path: Path) -> None:
    root = tmp_path / "fixture-repo"
    root.mkdir()
    write_curated_sources(root, register.CURATED_SEEDS)
    audit = root / "FINANCEIQ_MODEL_VALIDITY_AUDIT.md"
    audit.write_text(
        audit.read_text(encoding="utf-8") + "\n## 6. Dataset limitations\n\nduplicate\n",
        encoding="utf-8",
    )
    with pytest.raises(
        register.LimitationsRegisterError, match="source_locator heading is ambiguous"
    ):
        register.validate_curated_seeds(root, register.CURATED_SEEDS)


def test_non_heading_locator_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "fixture-repo"
    root.mkdir()
    write_curated_sources(root, register.CURATED_SEEDS)
    seeds = seeds_with_replacement("manual shares", source_locator="6. Dataset limitations")
    with pytest.raises(
        register.LimitationsRegisterError, match="must be a Markdown heading"
    ):
        register.validate_curated_seeds(root, seeds)


def test_quotation_drift_inside_the_correct_section_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "fixture-repo"
    root.mkdir()
    seed = next(s for s in register.CURATED_SEEDS if s.concept == "deployment unverified")
    drifted = replace(
        seed,
        source_text="Production readiness or live deployment claims (deployment liveness unverified).",
    )
    write_curated_sources(root, register.CURATED_SEEDS)
    with pytest.raises(register.LimitationsRegisterError, match="curated wording drift"):
        register.validate_curated_seeds(
            root, seeds_with_replacement("deployment unverified", source_text=drifted.source_text)
        )


def test_absolute_registry_path_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "fixture-repo"
    root.mkdir()
    (root / "artifact_registry.json").write_text(
        json.dumps({"entries": [{"path_or_glob": str(tmp_path / "outside.json")}]}),
        encoding="utf-8",
    )
    with pytest.raises(
        register.LimitationsRegisterError, match="must be repository-relative"
    ):
        register.discover_registered_limitations(root)


def test_parent_traversal_registry_path_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "fixture-repo"
    root.mkdir()
    (root / "artifact_registry.json").write_text(
        json.dumps({"entries": [{"path_or_glob": "../outside.json"}]}), encoding="utf-8"
    )
    with pytest.raises(
        register.LimitationsRegisterError, match="must not escape the repository"
    ):
        register.discover_registered_limitations(root)


def test_symlink_escaping_the_repository_root_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "fixture-repo"
    reports = root / "reports"
    reports.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    outside.write_text(json.dumps({"limitations": ["must never be read"]}), encoding="utf-8")
    (reports / "report.json").symlink_to(outside)
    (root / "artifact_registry.json").write_text(
        json.dumps({"entries": [{"path_or_glob": "reports/report.json"}]}), encoding="utf-8"
    )
    with pytest.raises(
        register.LimitationsRegisterError, match="escapes the repository root"
    ):
        register.discover_registered_limitations(root)


def test_generated_registry_entry_is_correct() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    matches = [
        entry
        for entry in registry["entries"]
        if entry.get("path_or_glob") == "docs/limitations_register.md"
    ]
    assert len(matches) == 1
    entry = matches[0]
    assert entry["artifact_class"] == "generated"
    assert entry["generator_command"] == "make limitations-register"
    assert entry["hand_edit_forbidden"] is True

    inputs = entry["inputs"]
    assert len(inputs) == len(set(inputs))
    # The generator never opens the universe audit, so declaring it would be false.
    assert "docs/universe_audit.md" not in inputs
    # The curated wording lives inside the generator, so the script is a real input.
    assert "scripts/build_limitations_register.py" in inputs
    for required in (
        "artifact_registry.json",
        "METHODOLOGY.md",
        "FINANCEIQ_MODEL_VALIDITY_AUDIT.md",
    ):
        assert required in inputs
    for declared in inputs:
        assert (REPO_ROOT / declared).is_file(), declared


def test_registry_inputs_cover_every_contributing_limitations_artifact() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    entry = next(
        e for e in registry["entries"] if e.get("path_or_glob") == "docs/limitations_register.md"
    )
    declared = {
        resolved
        for pattern in entry["inputs"]
        for resolved in (
            [pattern]
            if not any(character in pattern for character in "*?[")
            else [
                Path(raw).resolve().relative_to(REPO_ROOT.resolve()).as_posix()
                for raw in glob.glob(str(REPO_ROOT / pattern), recursive=True)
                if Path(raw).is_file()
            ]
        )
    }
    contributing = set(independent_limitations(REPO_ROOT))
    assert contributing <= declared

    # Nothing unrelated is declared: every input is the generator, the registry,
    # a cited curated source, or a contributing limitations artifact.
    allowed = contributing | {
        "scripts/build_limitations_register.py",
        "artifact_registry.json",
        "METHODOLOGY.md",
        "FINANCEIQ_MODEL_VALIDITY_AUDIT.md",
    }
    assert declared <= allowed


def test_valuation_limitations_prerequisite_is_strictly_a_non_empty_list_of_strings() -> None:
    payload = json.loads(
        (REPO_ROOT / "data/trusted_clean/free_valuation_history_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert isinstance(payload["limitations"], list)
    assert payload["limitations"]
    assert all(isinstance(item, str) and item.strip() for item in payload["limitations"])


def test_malformed_json_fails_closed(tmp_path: Path) -> None:
    root = make_fixture_repo(tmp_path, {}, raw_json="{not valid json")
    with pytest.raises(register.LimitationsRegisterError, match="malformed"):
        register.discover_registered_limitations(root)


@pytest.mark.parametrize(
    ("limitations", "message"),
    [
        ("legacy scalar", "expected non-empty list\\[str\\]"),
        ([], "list must not be empty"),
        ([1], "limitations\\[0\\]"),
        (["   "], "must not be blank"),
    ],
)
def test_invalid_limitations_shapes_fail_closed(
    tmp_path: Path, limitations: object, message: str
) -> None:
    payload = {"limitations": limitations}
    root = make_fixture_repo(tmp_path, payload)
    with pytest.raises(register.LimitationsRegisterError, match=message):
        register.discover_registered_limitations(root)


def test_missing_registry_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "fixture-repo"
    root.mkdir()
    with pytest.raises(register.LimitationsRegisterError, match="registry is missing"):
        register.discover_registered_limitations(root)


def test_invalid_registry_structure_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "fixture-repo"
    root.mkdir()
    (root / "artifact_registry.json").write_text(
        json.dumps({"entries": {}}), encoding="utf-8"
    )
    with pytest.raises(register.LimitationsRegisterError, match="entries must be a non-empty list"):
        register.discover_registered_limitations(root)


def test_unresolved_registered_path_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "fixture-repo"
    root.mkdir()
    (root / "artifact_registry.json").write_text(
        json.dumps({"entries": [{"path_or_glob": "reports/missing.json"}]}),
        encoding="utf-8",
    )
    with pytest.raises(register.LimitationsRegisterError, match="resolves to no paths"):
        register.discover_registered_limitations(root)


def test_curated_missing_source_and_wording_drift_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "fixture-repo"
    root.mkdir()
    write_curated_sources(root, register.CURATED_SEEDS)
    missing = seeds_with_replacement(
        register.CURATED_SEEDS[0].concept, source_path="missing.md"
    )
    with pytest.raises(register.LimitationsRegisterError, match="curated source is missing"):
        register.validate_curated_seeds(root, missing)

    drifted = seeds_with_replacement(
        register.CURATED_SEEDS[0].concept, source_text="wording drift"
    )
    with pytest.raises(register.LimitationsRegisterError, match="curated wording drift"):
        register.validate_curated_seeds(root, drifted)
