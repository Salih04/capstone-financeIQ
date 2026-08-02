"""Build the deterministic, registry-driven limitations register."""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, NoReturn


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_FILENAME = "artifact_registry.json"
OUTPUT_RELATIVE_PATH = "docs/limitations_register.md"
BANNER = "GENERATED — regenerate via make limitations-register; do not hand-edit"
REQUIRED_CURATED_CONCEPTS = (
    "retrospective cohort",
    "sector unpopulated",
    "one regime",
    "environment-qualified reproduction",
    "manual shares",
    "deployment unverified",
)


class LimitationsRegisterError(ValueError):
    """Actionable fail-closed error raised by the generator."""


@dataclass(frozen=True)
class CuratedSeed:
    """A reviewed, source-bound seed limitation."""

    concept: str
    source_text: str
    source_path: str
    source_locator: str


# Reviewed immutable-style source quotations.  The line breaks in source_text
# deliberately mirror the cited repository documents; validation below requires
# every quotation to remain an exact substring of its cited source.
CURATED_SEEDS: tuple[CuratedSeed, ...] = (
    CuratedSeed(
        concept="retrospective cohort",
        source_text=(
            "Results therefore describe a retrospectively fixed repository\n"
            "  cohort and retain unresolved survivorship and universe-selection look-ahead\n"
            "  risk; missing history was not inferred or filled."
        ),
        source_path="METHODOLOGY.md",
        source_locator="## Limitations",
    ),
    CuratedSeed(
        concept="sector unpopulated",
        source_text=(
            "`sector` identity column exists but is\n"
            "  currently unpopulated; it is not an accepted modeling feature."
        ),
        source_path="METHODOLOGY.md",
        source_locator="### Important data reality: source fields are mixed-quality",
    ),
    CuratedSeed(
        concept="one regime",
        source_text=(
            "2020–2025\n"
            "spans a single extraordinary Turkish macro regime (high inflation, deep TRY\n"
            "depreciation). Model behavior across regimes is therefore untested — this lens\n"
            "shows regime context and will only compute regime-conditional diagnostics when\n"
            "regime diversity exists."
        ),
        source_path="METHODOLOGY.md",
        source_locator="## Regime Lens (R2-REGIME-01)",
    ),
    CuratedSeed(
        concept="environment-qualified reproduction",
        source_text=(
            "When the numerical\n"
            "environment differs, byte drift is reported explicitly and only semantic\n"
            "leaderboard reproduction within that strict tolerance can pass."
        ),
        source_path="METHODOLOGY.md",
        source_locator="## Reproducibility and run provenance",
    ),
    CuratedSeed(
        concept="manual shares",
        source_text="Shares outstanding is manual — derived valuation is null until supplied.",
        source_path="FINANCEIQ_MODEL_VALIDITY_AUDIT.md",
        source_locator="## 6. Dataset limitations",
    ),
    CuratedSeed(
        concept="deployment unverified",
        source_text="Production-readiness or live-deployment claims (deployment liveness is unverified).",
        source_path="FINANCEIQ_MODEL_VALIDITY_AUDIT.md",
        source_locator="## 16. Claims that must be avoided",
    ),
)


# A Markdown ATX heading: one to six leading '#' followed by whitespace or EOL.
_HEADING_PATTERN = re.compile(r"^(#{1,6})(?:\s|$)")
# Fenced code blocks are skipped so a '#' comment inside a fence cannot be
# mistaken for a heading and truncate a cited section early.
_FENCE_PATTERN = re.compile(r"^\s*(?:```|~~~)")


@dataclass(frozen=True)
class RegisteredJsonArtifact:
    """One normalized registered JSON path and its validated limitations."""

    path: str
    registry_patterns: tuple[str, ...]
    limitations: tuple[str, ...]


def _fail(message: str) -> NoReturn:
    raise LimitationsRegisterError(message)


def _repo_root(root: Path) -> Path:
    try:
        return root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        _fail(f"repository root cannot be resolved: {root}: {exc}")


def _repo_relative(root: Path, path: Path, *, context: str) -> tuple[str, Path]:
    root_resolved = _repo_root(root)
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        _fail(f"{context}: registered path cannot be resolved: {path}: {exc}")
    try:
        relative = resolved.relative_to(root_resolved)
    except ValueError:
        _fail(
            f"{context}: resolved path escapes the repository root: "
            f"{path} -> {resolved}"
        )
    if not resolved.is_file():
        _fail(f"{context}: resolved path is not a file: {path}")
    return relative.as_posix(), resolved


def _validate_registry_pattern(pattern: object, *, index: int) -> str:
    if not isinstance(pattern, str) or not pattern.strip():
        _fail(f"artifact_registry.json: entries[{index}].path_or_glob must be a non-empty string")
    if Path(pattern).is_absolute():
        _fail(
            f"artifact_registry.json: entries[{index}].path_or_glob must be repository-relative: {pattern!r}"
        )
    if ".." in PurePosixPath(pattern).parts:
        _fail(
            f"artifact_registry.json: entries[{index}].path_or_glob must not escape the repository: {pattern!r}"
        )
    return pattern


def load_registry(root: Path, registry_path: Path | None = None) -> dict[str, Any]:
    """Load and minimally validate the registry source inventory."""

    root = _repo_root(root)
    path = (registry_path or (root / REGISTRY_FILENAME)).resolve()
    if not path.is_file():
        _fail(f"registry is missing: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        _fail(f"registry is not valid UTF-8: {path}: {exc}")
    except json.JSONDecodeError as exc:
        _fail(f"registry is malformed JSON: {path}:{exc.lineno}: {exc.msg}")
    except OSError as exc:
        _fail(f"registry cannot be read: {path}: {exc}")
    if not isinstance(payload, dict):
        _fail(f"registry has invalid structure: top-level value must be an object: {path}")
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        _fail("registry has invalid structure: entries must be a non-empty list")
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            _fail(f"artifact_registry.json: entries[{index}] must be an object")
        _validate_registry_pattern(entry.get("path_or_glob"), index=index)
    return payload


def _resolve_registry_entry(root: Path, pattern: str, *, index: int) -> dict[str, Path]:
    """Resolve one registered path/glob to unique normalized repository paths."""

    root = _repo_root(root)
    raw_matches = sorted(glob.glob(str(root / pattern), recursive=True))
    if not raw_matches:
        _fail(
            f"registry entry entries[{index}] {pattern!r} resolves to no paths; "
            "registered paths are required to exist"
        )
    normalized: dict[str, Path] = {}
    for raw in raw_matches:
        candidate = Path(raw)
        if not candidate.is_file():
            continue
        relative, resolved = _repo_relative(
            root, candidate, context=f"registry entry entries[{index}] {pattern!r}"
        )
        prior = normalized.get(relative)
        if prior is not None and prior != resolved:
            _fail(
                f"registry entry entries[{index}] {pattern!r} has ambiguous normalized path "
                f"{relative!r}: {prior} and {resolved}"
            )
        normalized[relative] = resolved
    if not normalized:
        _fail(
            f"registry entry entries[{index}] {pattern!r} resolves to no files; "
            "registered paths are required to exist"
        )
    return normalized


def resolve_registered_json_paths(
    root: Path, registry_path: Path | None = None
) -> dict[str, tuple[str, ...]]:
    """Return normalized JSON paths mapped to the registry patterns that matched them.

    Resolution is intentionally driven only by ``artifact_registry.json``.  Repeated
    matches from overlapping registry patterns are deduplicated by their normalized
    repository-relative POSIX path.
    """

    root = _repo_root(root)
    registry = load_registry(root, registry_path)
    paths_to_patterns: dict[str, set[str]] = {}
    for index, entry in enumerate(registry["entries"]):
        pattern = _validate_registry_pattern(entry["path_or_glob"], index=index)
        # The generated document is itself registered, but it is legitimately
        # absent on the first invocation. It is not a source JSON artifact and
        # will be present for subsequent registry-coverage checks.
        if pattern == OUTPUT_RELATIVE_PATH and not (root / pattern).exists():
            continue
        for relative in _resolve_registry_entry(root, pattern, index=index):
            if relative.casefold().endswith(".json"):
                paths_to_patterns.setdefault(relative, set()).add(pattern)
    return {
        path: tuple(sorted(patterns))
        for path, patterns in sorted(paths_to_patterns.items())
    }


def _load_registered_json(root: Path, relative: str) -> Any:
    path = _repo_root(root) / relative
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        _fail(f"registered JSON is not valid UTF-8: {relative}: {exc}")
    except json.JSONDecodeError as exc:
        _fail(f"registered JSON is malformed: {relative}:{exc.lineno}: {exc.msg}")
    except OSError as exc:
        _fail(f"registered JSON cannot be read: {relative}: {exc}")


def _validate_limitations(relative: str, payload: Any) -> tuple[str, ...] | None:
    if not isinstance(payload, dict):
        _fail(f"registered JSON {relative} has invalid structure: top-level value must be an object")
    if "limitations" not in payload:
        return None
    limitations = payload["limitations"]
    if not isinstance(limitations, list):
        _fail(
            f"registered JSON {relative} has invalid limitations shape: expected non-empty list[str], "
            f"got {type(limitations).__name__}"
        )
    if not limitations:
        _fail(f"registered JSON {relative} has invalid limitations shape: list must not be empty")
    validated: list[str] = []
    for index, item in enumerate(limitations):
        if not isinstance(item, str):
            _fail(
                f"registered JSON {relative} has invalid limitations[{index}]: "
                f"expected non-empty string, got {type(item).__name__}"
            )
        if not item.strip():
            _fail(
                f"registered JSON {relative} has invalid limitations[{index}]: "
                "string must not be blank"
            )
        validated.append(item)
    return tuple(validated)


def discover_registered_limitations(
    root: Path, registry_path: Path | None = None
) -> tuple[RegisteredJsonArtifact, ...]:
    """Parse all registered JSON files and return only those with limitations."""

    root = _repo_root(root)
    resolved = resolve_registered_json_paths(root, registry_path)
    found: list[RegisteredJsonArtifact] = []
    for relative in sorted(resolved):
        payload = _load_registered_json(root, relative)
        limitations = _validate_limitations(relative, payload)
        if limitations is not None:
            found.append(
                RegisteredJsonArtifact(
                    path=relative,
                    registry_patterns=resolved[relative],
                    limitations=limitations,
                )
            )
    return tuple(found)


def _heading_level(line: str) -> int | None:
    """Return the ATX heading level of ``line``, or None when it is not a heading."""

    match = _HEADING_PATTERN.match(line)
    return len(match.group(1)) if match else None


def locator_section(seed: CuratedSeed, source_text: str) -> str:
    """Return the exact text of the section introduced by ``seed.source_locator``.

    The section runs from the line after the locator heading through, but not
    including, the next heading of the same or a higher level.  The returned slice
    is unmodified source text: no whitespace is normalized, collapsed, stripped, or
    reflowed, so the caller's substring check stays byte-exact.
    """

    context = (
        f"curated seed {seed.concept!r} in {seed.source_path} "
        f"(locator {seed.source_locator!r})"
    )
    level = _heading_level(seed.source_locator)
    if level is None:
        _fail(f"{context}: source_locator must be a Markdown heading beginning with '#'")
    lines = source_text.split("\n")
    headings: list[tuple[int, int]] = []
    matches: list[int] = []
    fenced = False
    for index, line in enumerate(lines):
        if _FENCE_PATTERN.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        line_level = _heading_level(line)
        if line_level is None:
            continue
        headings.append((index, line_level))
        if line == seed.source_locator:
            matches.append(index)
    if not matches:
        _fail(f"{context}: source_locator heading was not found in the cited source")
    if len(matches) > 1:
        _fail(
            f"{context}: source_locator heading is ambiguous: it occurs "
            f"{len(matches)} times in the cited source"
        )
    start = matches[0]
    end = len(lines)
    for index, line_level in headings:
        if index > start and line_level <= level:
            end = index
            break
    return "\n".join(lines[start + 1 : end])


def validate_curated_seeds(
    root: Path, seeds: Iterable[CuratedSeed] = CURATED_SEEDS
) -> tuple[CuratedSeed, ...]:
    """Validate the reviewed seed set and every exact source quotation."""

    root = _repo_root(root)
    seeds = tuple(seeds)
    concepts = [seed.concept for seed in seeds]
    missing = sorted(set(REQUIRED_CURATED_CONCEPTS) - set(concepts))
    if missing:
        _fail(f"curated seed list is missing required concepts: {', '.join(missing)}")
    duplicates = sorted({concept for concept in concepts if concepts.count(concept) > 1})
    if duplicates:
        _fail(f"curated seed list has duplicate concepts: {', '.join(duplicates)}")
    for seed in seeds:
        if not seed.concept.strip() or not seed.source_text:
            _fail(f"curated seed {seed.concept!r} is missing its concept or source text")
        source = root / seed.source_path
        if not source.is_file():
            _fail(
                f"curated source is missing for {seed.concept!r}: {seed.source_path} "
                f"({seed.source_locator})"
            )
        try:
            source_text = source.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            _fail(f"curated source cannot be read for {seed.concept!r}: {seed.source_path}: {exc}")
        if seed.source_text not in source_text:
            _fail(
                f"curated wording drift for {seed.concept!r}: exact source text was not found in "
                f"{seed.source_path} ({seed.source_locator})"
            )
        # Presence somewhere in the file is not enough: the quotation must sit
        # inside the section the register cites, or the published locator is false.
        if seed.source_text not in locator_section(seed, source_text):
            _fail(
                f"curated quotation is outside its cited section for {seed.concept!r}: exact "
                f"source text was not found under the locator in {seed.source_path} "
                f"({seed.source_locator})"
            )
    return seeds


def render_markdown(
    artifacts: Iterable[RegisteredJsonArtifact], seeds: Iterable[CuratedSeed]
) -> str:
    """Render the register with stable section and entry ordering."""

    lines = [
        "# Automated limitations register",
        "",
        f"> {BANNER}",
        "",
        "This document is an evidence register, not a new statistical conclusion. "
        "The auto-extracted section preserves registered artifact text verbatim; "
        "the curated section preserves reviewed source quotations verbatim.",
        "",
        "## Auto-extracted limitations",
        "",
    ]
    for artifact in artifacts:
        lines.extend(
            [
                f"### {artifact.path}",
                "",
                "Registered through: "
                + ", ".join(f"`{pattern}`" for pattern in artifact.registry_patterns),
                "",
            ]
        )
        lines.extend(f"- {limitation}" for limitation in artifact.limitations)
        lines.append("")

    lines.extend(["## Curated seed limitations", ""])
    for seed in seeds:
        lines.extend(
            [
                f"### {seed.concept}",
                "",
                f"Source: `{seed.source_path}`",
                f"Locator: `{seed.source_locator}`",
                "",
                "Exact source text:",
                "```text",
                seed.source_text,
                "```",
                "",
            ]
        )
    return "\n".join(lines).rstrip("\n") + "\n"


def generate_document(
    root: Path = ROOT, registry_path: Path | None = None
) -> str:
    """Generate the complete register text without writing any file."""

    root = _repo_root(root)
    artifacts = discover_registered_limitations(root, registry_path)
    seeds = validate_curated_seeds(root)
    return render_markdown(artifacts, seeds)


def write_document(
    root: Path = ROOT,
    output_path: Path | None = None,
    registry_path: Path | None = None,
) -> Path:
    """Generate and write the register using UTF-8 and stable LF newlines."""

    root = _repo_root(root)
    destination = output_path or (root / OUTPUT_RELATIVE_PATH)
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = generate_document(root, registry_path)
    try:
        with destination.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    except OSError as exc:
        _fail(f"generated document cannot be written: {destination}: {exc}")
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="repository root (defaults to this script's repository)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="output path (defaults to docs/limitations_register.md under --root)",
    )
    args = parser.parse_args(argv)
    try:
        destination = write_document(args.root, args.output)
    except LimitationsRegisterError as exc:
        print(f"limitations register generation failed: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {destination.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
