"""Shared, fail-closed citation resolution for evidence-composing services.

Extracted from ``courtroom_service`` so the Courtroom and the research memo
resolve sources through one contract.  The module is deliberately narrow: it is
not a general file-reading API.  It only supports the source formats the two
services actually cite — JSON artifacts addressed by dotted field path, and
Markdown/text documents addressed by heading locator plus an exact contiguous
quotation.

Every helper fails closed.  A missing path, a path outside the repository, an
absolute path, a malformed document, an absent field, a false locator, or a
value that no longer matches the source raises instead of degrading to a
plausible answer.  Loaders return newly constructed objects so a response can
never alias a cached source document.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any

from app.core.paths import resolve_repo_root


REPO_ROOT = resolve_repo_root()

_INDEXED_SEGMENT = re.compile(r"^([^\[\]]+)\[(\d+)\]$")
# A Markdown ATX heading: one to six leading '#' followed by whitespace or EOL.
_HEADING_PATTERN = re.compile(r"^(#{1,6})(?:\s|$)")
# Fenced blocks are skipped so a '#' inside a fence cannot truncate a section.
_FENCE_PATTERN = re.compile(r"^\s*(?:```|~~~)")


class CitationError(ValueError):
    """Raised when a source cannot be read, located, or value-matched."""


def assert_repo_relative(relative: str) -> str:
    """Validate a repository-relative POSIX path without touching the filesystem."""
    if not isinstance(relative, str) or not relative.strip():
        raise CitationError("source path must be a non-empty repository-relative string")
    if relative != relative.strip():
        raise CitationError(f"source path must not be padded with whitespace: {relative!r}")
    if "\\" in relative:
        raise CitationError(f"source path must use POSIX separators: {relative!r}")
    if PurePosixPath(relative).is_absolute() or Path(relative).is_absolute():
        raise CitationError(f"source path must be repository-relative: {relative!r}")
    parts = PurePosixPath(relative).parts
    if not parts or ".." in parts:
        raise CitationError(f"source path must not escape the repository: {relative!r}")
    return relative


def repo_path(relative: str) -> Path:
    """Resolve a repository-relative POSIX path to a contained regular file."""
    assert_repo_relative(relative)
    candidate = REPO_ROOT / relative
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise CitationError(f"source is missing: {relative}") from exc
    root = REPO_ROOT.resolve()
    if root not in resolved.parents:
        raise CitationError(f"source resolves outside the repository: {relative}")
    if not resolved.is_file():
        raise CitationError(f"source is not a regular file: {relative}")
    return resolved


def relative_to_repo(path: Path) -> str:
    """Repository-relative POSIX form, or the bare filename when outside the root.

    The filename fallback preserves the Courtroom's existing behaviour for
    monkeypatched, out-of-tree fixture paths.  Citation construction never uses
    this helper; it uses :func:`assert_repo_relative` instead, which refuses.
    """
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.name


@lru_cache(maxsize=32)
def _read_json_cached(path: str, mtime: float) -> dict[str, Any]:
    del mtime
    with Path(path).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("expected a JSON object")
    return value


def load_json_document(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Load a JSON object, returning ``(document, error)`` — never raising.

    The returned document is a deep copy, so callers can never mutate or alias
    the cached source.  ``error`` carries the Courtroom's existing wording.
    """
    if not path.is_file():
        return None, "artifact is missing"
    try:
        document = _read_json_cached(str(path), path.stat().st_mtime)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return None, f"artifact is malformed ({type(exc).__name__})"
    return copy.deepcopy(document), None


def load_json_artifact(relative: str) -> dict[str, Any]:
    """Load a registered JSON artifact by repository-relative path, or fail closed."""
    document, error = load_json_document(repo_path(relative))
    if document is None:
        raise CitationError(f"{relative}: {error}")
    return document


@lru_cache(maxsize=16)
def _read_text_cached(path: str, mtime: float) -> str:
    del mtime
    return Path(path).read_text(encoding="utf-8")


def load_text_artifact(relative: str) -> str:
    """Load a UTF-8 text/Markdown source by repository-relative path."""
    path = repo_path(relative)
    try:
        return _read_text_cached(str(path), path.stat().st_mtime)
    except (OSError, UnicodeDecodeError) as exc:
        raise CitationError(f"{relative}: source cannot be read ({type(exc).__name__})") from exc


def sha256_of(relative: str) -> str:
    """SHA-256 of the exact bytes of a repository-relative source file."""
    digest = hashlib.sha256()
    with repo_path(relative).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_field(document: Any, field_path: str, *, source: str) -> Any:
    """Resolve a dotted field path (with ``name[index]`` segments), failing closed."""
    if not isinstance(field_path, str) or not field_path.strip():
        raise CitationError(f"{source}: field path must be a non-empty string")
    value: Any = document
    for segment in field_path.split("."):
        match = _INDEXED_SEGMENT.fullmatch(segment)
        key, index = (match.group(1), int(match.group(2))) if match else (segment, None)
        if not isinstance(value, dict) or key not in value:
            raise CitationError(f"{source}: field is absent: {field_path}")
        value = value[key]
        if index is not None:
            if not isinstance(value, list) or not 0 <= index < len(value):
                raise CitationError(f"{source}: field index is out of range: {field_path}")
            value = value[index]
    return copy.deepcopy(value)


def _heading_level(line: str) -> int | None:
    match = _HEADING_PATTERN.match(line)
    return len(match.group(1)) if match else None


def locator_section(text: str, locator: str, *, source: str) -> str:
    """Return the exact, unnormalized text under a unique Markdown heading.

    No whitespace is collapsed, stripped, or reflowed, so a caller's substring
    check stays byte-exact.  An absent or ambiguous locator fails closed.
    """
    level = _heading_level(locator)
    if level is None:
        raise CitationError(f"{source}: locator must be a Markdown heading: {locator!r}")
    lines = text.split("\n")
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
        if line == locator:
            matches.append(index)
    if not matches:
        raise CitationError(f"{source}: locator heading was not found: {locator!r}")
    if len(matches) > 1:
        raise CitationError(f"{source}: locator heading is ambiguous: {locator!r}")
    start = matches[0]
    end = len(lines)
    for index, line_level in headings:
        if index > start and line_level <= level:
            end = index
            break
    return "\n".join(lines[start + 1 : end])


def verify_json_field(relative: str, field_path: str, expected: Any) -> Any:
    """Re-read a JSON field and refuse unless it equals ``expected`` exactly."""
    actual = resolve_field(load_json_artifact(relative), field_path, source=relative)
    if actual != expected or type(actual) is not type(expected):
        raise CitationError(
            f"{relative}: cited value does not match the source at {field_path}"
        )
    return actual


def verify_text_span(relative: str, locator: str, quoted_text: str) -> str:
    """Refuse unless ``quoted_text`` is contiguous inside the located section."""
    if not isinstance(quoted_text, str) or not quoted_text:
        raise CitationError(f"{relative}: quoted text must be a non-empty string")
    section = locator_section(load_text_artifact(relative), locator, source=relative)
    if quoted_text not in section:
        raise CitationError(
            f"{relative}: quoted text was not found under the locator {locator!r}"
        )
    return quoted_text
