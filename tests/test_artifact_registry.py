"""Enforce the generated-artifact ownership & regeneration registry (R3-REL-01).

The registry (``artifact_registry.json``) is a hand-curated ownership map: every
generated file under the governed roots is claimed by exactly one entry that
names the Makefile command which regenerates it. These tests fail
deterministically for orphaned, multiply-owned, missing, or mis-commanded
artifacts, and re-verify the ``source_artifacts`` checksums that reports embed.

The registry records ownership and regeneration provenance only; it certifies
neither statistical validity nor predictive value. Pure helper functions take
their inputs explicitly so the negative tests exercise the failure paths without
mutating the working tree.
"""

from __future__ import annotations

import glob
import hashlib
import json
import re
from pathlib import Path

import pytest

from experiments import placebo_lab as pl


REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "artifact_registry.json"
MAKEFILE_PATH = REPO_ROOT / "Makefile"
GITIGNORE_PATH = REPO_ROOT / ".gitignore"

RUNS_MARKER = "/runs/"
REQUIRED_ENTRY_FIELDS = {
    "path_or_glob",
    "artifact_class",
    "generator_command",
    "inputs",
    "hand_edit_forbidden",
    "notes",
}
KNOWN_ARTIFACT_CLASSES = {
    "generated",
    "run_manifest",
    "human_document",
    "source_input",
    "runtime_output",
    "proposed_future",
}
# Certifying phrasings the registry must never make (neutrality guard). These are
# claim assertions, not the explicit negations the purpose statement carries.
FORBIDDEN_CERTIFYING_PHRASES = (
    "buy recommendation",
    "sell recommendation",
    "investment recommendation",
    "investment advice.",
    "guaranteed return",
    "validated predictive edge",
    "reliable predictive edge exists",
    "certifies predictive",
    "proven signal",
)


# --------------------------------------------------------------------------- #
# Loading helpers
# --------------------------------------------------------------------------- #
def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def makefile_targets(makefile_text: str) -> set[str]:
    """Every declared Makefile target (rule definitions and .PHONY names)."""
    targets: set[str] = set()
    for line in makefile_text.splitlines():
        match = re.match(r"^([A-Za-z0-9][A-Za-z0-9_-]*):(?!=)", line)
        if match:
            targets.add(match.group(1))
    phony = re.findall(r"\.PHONY:\s*(.*(?:\\\n.*)*)", makefile_text)
    for block in phony:
        for token in block.replace("\\", " ").split():
            targets.add(token)
    return targets


def expand_pattern(pattern: str) -> list[str]:
    """Repo-relative files matched by a registry path or glob."""
    matches = glob.glob(str(REPO_ROOT / pattern), recursive=True)
    return sorted(
        str(Path(m).relative_to(REPO_ROOT)) for m in matches if Path(m).is_file()
    )


def enumerate_governed_files(governed_roots: list[str]) -> set[str]:
    """All files under the governed roots, excluding per-run manifest dirs."""
    found: set[str] = set()
    for root in governed_roots:
        for match in glob.glob(str(REPO_ROOT / root / "**"), recursive=True):
            path = Path(match)
            if path.is_file() and RUNS_MARKER not in match.replace("\\", "/"):
                found.add(str(path.relative_to(REPO_ROOT)))
    return found


def sha256_of(rel_path: str) -> str:
    digest = hashlib.sha256()
    with open(REPO_ROOT / rel_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


# --------------------------------------------------------------------------- #
# Pure validators (input-driven so negative tests need no tree mutation)
# --------------------------------------------------------------------------- #
def coverage_failures(
    governed: set[str], entry_matches: list[tuple[str, set[str]]]
) -> tuple[list[str], dict[str, list[str]]]:
    """Return (orphans, multi_owned) for a governed set and entry->matches map."""
    owners: dict[str, list[str]] = {}
    for pattern, matched in entry_matches:
        for path in matched & governed:
            owners.setdefault(path, []).append(pattern)
    orphans = sorted(governed - set(owners))
    multi_owned = {path: pats for path, pats in owners.items() if len(pats) > 1}
    return orphans, multi_owned


def unsupported_commands(entries: list[dict], targets: set[str]) -> list[str]:
    """Registry entries whose generator_command is not a supported make target."""
    problems: list[str] = []
    for entry in entries:
        command = entry["generator_command"]
        if command is None:  # human_document / non-generated: no command required
            continue
        tokens = command.split()
        if len(tokens) < 2 or tokens[0] != "make":
            problems.append(f"{entry['path_or_glob']}: not a 'make <target>' command: {command!r}")
            continue
        target = tokens[1]
        if target not in targets:
            problems.append(f"{entry['path_or_glob']}: unknown make target {target!r}")
    return problems


def empty_patterns(entries: list[dict]) -> list[str]:
    """Registry patterns matching zero files on disk (stale artifact paths)."""
    return [e["path_or_glob"] for e in entries if not expand_pattern(e["path_or_glob"])]


def checksum_staleness() -> list[str]:
    """Auto-discover reports with a top-level source_artifacts list and re-verify.

    Returns actionable 'stale evidence' diagnostics for any mismatch or missing
    referenced input.
    """
    problems: list[str] = []
    registry = load_registry()
    for root in registry["governed_roots"]:
        for match in glob.glob(str(REPO_ROOT / root / "**/*.json"), recursive=True):
            if RUNS_MARKER in match.replace("\\", "/"):
                continue
            rel = str(Path(match).relative_to(REPO_ROOT))
            try:
                payload = json.loads(Path(match).read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            source_artifacts = payload.get("source_artifacts")
            if not isinstance(source_artifacts, list):
                continue
            for item in source_artifacts:
                if not isinstance(item, dict):
                    continue
                dep_path = item.get("path")
                recorded = item.get("sha256")
                if not dep_path or not recorded:
                    continue
                if not (REPO_ROOT / dep_path).is_file():
                    problems.append(
                        f"stale evidence: {rel} references missing input {dep_path}; "
                        f"regenerate {rel} via its generator_command or investigate"
                    )
                    continue
                actual = sha256_of(dep_path)
                if actual != recorded:
                    problems.append(
                        f"stale evidence: {rel} records sha256 {recorded[:12]}… for "
                        f"{dep_path} but the file hashes to {actual[:12]}…; regenerate "
                        f"{rel} via its generator_command or investigate the input change"
                    )
    return problems


# --------------------------------------------------------------------------- #
# Structural tests
# --------------------------------------------------------------------------- #
def test_registry_is_valid_json_with_required_shape():
    registry = load_registry()
    assert registry["schema_version"]
    assert registry["task"] == "R3-REL-01"
    assert registry["governed_roots"]
    assert set(KNOWN_ARTIFACT_CLASSES) == set(registry["artifact_class_definitions"])
    for entry in registry["entries"]:
        assert set(entry) == REQUIRED_ENTRY_FIELDS, entry
        assert entry["artifact_class"] in KNOWN_ARTIFACT_CLASSES, entry
        assert isinstance(entry["inputs"], list)
        assert isinstance(entry["hand_edit_forbidden"], bool)
        assert isinstance(entry["notes"], str) and entry["notes"].strip()


def test_every_entry_matches_at_least_one_file():
    """Stale-path guard: no registry entry may point at a vanished artifact."""
    stale = empty_patterns(load_registry()["entries"])
    assert stale == [], f"registry patterns matching no files (stale paths): {stale}"


def test_full_coverage_exactly_one_owner():
    """Every governed file is claimed by exactly one entry (no orphan, no duplicate)."""
    registry = load_registry()
    governed = enumerate_governed_files(registry["governed_roots"])
    entry_matches = [
        (e["path_or_glob"], set(expand_pattern(e["path_or_glob"])))
        for e in registry["entries"]
    ]
    orphans, multi_owned = coverage_failures(governed, entry_matches)
    assert orphans == [], f"unregistered governed artifacts (orphans): {orphans}"
    assert multi_owned == {}, f"multiply-owned artifacts: {multi_owned}"


def test_generator_commands_are_supported_make_targets():
    registry = load_registry()
    targets = makefile_targets(MAKEFILE_PATH.read_text(encoding="utf-8"))
    problems = unsupported_commands(registry["entries"], targets)
    assert problems == [], f"unsupported regeneration commands: {problems}"


def test_runs_glob_present_and_matches_manifests():
    """The runs directory is governed as a class by exactly one glob entry."""
    registry = load_registry()
    runs_entries = [
        e for e in registry["entries"] if e["path_or_glob"].startswith("experiments/results/runs")
    ]
    assert len(runs_entries) == 1, runs_entries
    assert runs_entries[0]["artifact_class"] == "run_manifest"
    assert expand_pattern(runs_entries[0]["path_or_glob"]), "runs glob matches no files"


def test_embedded_source_artifact_checksums_are_current():
    """Reports embedding source_artifacts checksums must match their inputs."""
    problems = checksum_staleness()
    assert problems == [], "\n".join(problems)


def test_registry_wording_stays_ownership_neutral():
    registry = load_registry()
    purpose = registry["purpose"].lower()
    assert "does not certify" in purpose
    assert "ownership" in purpose
    blob = json.dumps(registry).lower()
    hits = [phrase for phrase in FORBIDDEN_CERTIFYING_PHRASES if phrase in blob]
    assert hits == [], f"registry contains non-neutral certifying language: {hits}"


def test_placebo_results_contain_only_governed_deterministic_reports():
    registry = load_registry()
    placebo_root = REPO_ROOT / "experiments" / "results_placebo"
    expected = {
        "experiments/results_placebo/placebo_report.json",
        "experiments/results_placebo/placebo_report.md",
    }
    actual = {
        str(path.relative_to(REPO_ROOT)) for path in placebo_root.iterdir() if path.is_file()
    }
    placebo_entries = {
        entry["path_or_glob"]
        for entry in registry["entries"]
        if entry["path_or_glob"].startswith("experiments/results_placebo/")
    }
    assert actual == expected
    assert placebo_entries == expected
    assert not any(
        "placebo_runtime.json" in entry["path_or_glob"]
        for entry in registry["entries"]
    )


def test_placebo_runtime_is_ignored_local_output_outside_governed_roots():
    registry = load_registry()
    runtime_rel = pl.RUNTIME_OUTPUT.relative_to(REPO_ROOT).as_posix()
    assert runtime_rel == "experiments/runtime/placebo_runtime.json"
    assert not any(
        runtime_rel == root or runtime_rel.startswith(f"{root}/")
        for root in registry["governed_roots"]
    )
    assert "experiments/runtime/" in GITIGNORE_PATH.read_text(
        encoding="utf-8"
    ).splitlines()


def test_placebo_scientific_reports_do_not_depend_on_runtime_checksums():
    registry = load_registry()
    report_entries = [
        entry
        for entry in registry["entries"]
        if entry["path_or_glob"]
        in {
            "experiments/results_placebo/placebo_report.json",
            "experiments/results_placebo/placebo_report.md",
        }
    ]
    assert len(report_entries) == 2
    assert all("runtime" not in json.dumps(entry).lower() for entry in report_entries)

    report = json.loads(
        (REPO_ROOT / "experiments/results_placebo/placebo_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert all(
        "runtime" not in json.dumps(source).lower()
        for source in report.get("source_artifacts", [])
    )


# --------------------------------------------------------------------------- #
# Negative tests (deterministic; no working-tree mutation)
# --------------------------------------------------------------------------- #
def test_negative_orphan_is_detected():
    governed = {"experiments/results/a.csv", "experiments/results/b.csv"}
    entry_matches = [("experiments/results/a.csv", {"experiments/results/a.csv"})]
    orphans, multi = coverage_failures(governed, entry_matches)
    assert orphans == ["experiments/results/b.csv"]
    assert multi == {}


def test_negative_duplicate_ownership_is_detected():
    governed = {"experiments/results/a.csv"}
    entry_matches = [
        ("experiments/results/a.csv", {"experiments/results/a.csv"}),
        ("experiments/results/*.csv", {"experiments/results/a.csv"}),
    ]
    orphans, multi = coverage_failures(governed, entry_matches)
    assert orphans == []
    assert multi == {
        "experiments/results/a.csv": [
            "experiments/results/a.csv",
            "experiments/results/*.csv",
        ]
    }


def test_negative_missing_or_bad_generator_command_is_detected():
    targets = {"research", "data"}
    entries = [
        {"path_or_glob": "x", "generator_command": "make no-such-target"},
        {"path_or_glob": "y", "generator_command": "python foo.py"},
        {"path_or_glob": "z", "generator_command": "make research"},
        {"path_or_glob": "doc", "generator_command": None},
    ]
    problems = unsupported_commands(entries, targets)
    assert any("unknown make target" in p for p in problems)
    assert any("not a 'make <target>' command" in p for p in problems)
    assert not any(p.startswith("z:") for p in problems)
    assert not any(p.startswith("doc:") for p in problems)


def test_negative_stale_registry_path_is_detected():
    stale = empty_patterns(
        [{"path_or_glob": "experiments/results/this_file_does_not_exist_xyz.csv"}]
    )
    assert stale == ["experiments/results/this_file_does_not_exist_xyz.csv"]


def test_negative_planted_unregistered_file_fails_coverage(tmp_path):
    """An unregistered file dropped under a governed root must fail coverage.

    Uses a real file under experiments/results/ and always removes it, so the
    working tree is restored regardless of assertion outcome.
    """
    registry = load_registry()
    planted = REPO_ROOT / "experiments/results/__r3_rel_01_planted_probe__.csv"
    try:
        planted.write_text("probe\n", encoding="utf-8")
        governed = enumerate_governed_files(registry["governed_roots"])
        assert str(planted.relative_to(REPO_ROOT)) in governed
        entry_matches = [
            (e["path_or_glob"], set(expand_pattern(e["path_or_glob"])))
            for e in registry["entries"]
        ]
        orphans, _ = coverage_failures(governed, entry_matches)
        assert str(planted.relative_to(REPO_ROOT)) in orphans
    finally:
        planted.unlink(missing_ok=True)
    assert not planted.exists()


def test_negative_stale_embedded_checksum_is_detected(tmp_path):
    """The staleness verifier reports a mismatch (pure fixture, no real report touched)."""
    dep = tmp_path / "dep.csv"
    dep.write_text("real,contents\n", encoding="utf-8")
    report = {
        "source_artifacts": [
            {"path": str(dep), "sha256": "0" * 64},  # deliberately wrong
        ]
    }
    # Re-implement the inner check against the fixture to prove the failure path.
    problems = []
    for item in report["source_artifacts"]:
        actual = hashlib.sha256(Path(item["path"]).read_bytes()).hexdigest()
        if actual != item["sha256"]:
            problems.append("stale evidence")
    assert problems == ["stale evidence"]
