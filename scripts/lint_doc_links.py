#!/usr/bin/env python3
"""Lint repository-local Markdown links, cited paths, and current-state counts."""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote


BASELINE_PATH = "docs/VERIFICATION_BASELINE.md"
KNOWN_TOP_LEVEL_DIRS = {
    "backend",
    "data",
    "docs",
    "experiments",
    "frontend",
    "research_agent_training",
    "scripts",
    "tests",
}

# These files preserve dated observations, task instructions, or completion history.
# Their links and cited paths are still checked; only current-state count comparison is
# excluded so the lint never rewrites history to resemble today's repository.
TRUTH_DRIFT_EXCLUSIONS = {
    "CHANGELOG.md": "append-only release history",
    "DATA_01_DATA_DICTIONARY_AUDIT.md": "dated audit evidence",
    "FINANCEIQ_AGENT_TASK_QUEUE.md": "task packets and completion ledger",
    "FINANCEIQ_MODEL_VALIDITY_AUDIT.md": "dated audit evidence",
    "FINANCEIQ_MOONSHOT_ROADMAP.md": "strategic planning record",
    "FINANCEIQ_PHASE3_4_FRONTIER_PLAN.md": "dated planning and candidate record",
    "OPERATING_LAYER_VALIDATION.md": "completed validation evidence",
    "docs/archive/investigations/SMRTG_NOT_FOUND_INVESTIGATION.md": "dated investigation evidence",
    "TASK.md": "completed task packet and its historical verification transcript",
    "TASK_STATE.md": "append-only completion ledger",
    "docs/FRESH_DATABASE_BOOTSTRAP_VERIFICATION.md": "dated verification evidence",
    "docs/R2_LOOP_01_MIGRATION_VERIFICATION.md": "dated verification evidence",
    BASELINE_PATH: "the machine-read current baseline itself",
}

# Contextual exclusions are structural classes rather than snapshots of prose.
PATH_CONTEXT_EXCLUSIONS = {
    "(proposed)": "future path explicitly marked as proposed",
}
PATH_VALUE_EXCLUSIONS = {
    "frontend/.env.local": "developer-local environment file is intentionally untracked",
    "data/trusted_clean/partial_2026_ytd_returns.csv": "documented future-data example",
    "data/trusted_raw/bist100_daily.csv": "documented optional input example",
    "backend/backend/Dockerfile": "documented invalid Render configuration example",
    "experiments/results|reports/": "compact shorthand for two existing directories",
    "backend/experiments/": "documented untracked local directory with no repository role",
    "frontend/dist": "gitignored Vite build output cited by deployment documentation",
    "data/trusted_raw/prices/yahoo_chart_raw/SMRTG.IS_2022.json": "dated investigation observed local files that were never committed",
    "data/trusted_raw/prices/yahoo_chart_raw/SMRTG.IS_2023.json": "dated investigation observed local files that were never committed",
    "data/trusted_raw/prices/yahoo_chart_raw/SMRTG.IS_2024.json": "dated investigation observed local files that were never committed",
    "data/trusted_raw/prices/yahoo_chart_raw/SMRTG.IS_2025.json": "dated investigation observed local files that were never committed",
}
PLANNED_PATH_EXCLUSIONS = {
    "backend/app/services/research/calibration.py": "future task output in the queue",
    "backend/app/services/research/real_terms.py": "future task output in the queue",
    "docs/limitations_register.md": "future generated document in the queue",
    "data/trusted_clean/company_contexts/SMRTG_": "future promotion check in a dated investigation",
    "experiments/results_disagreement/": "future task output in the queue",
    "experiments/results_excess/": "future task output in the queue",
    "experiments/results_forward_2026/": "future task output in the queue",
    "experiments/results_influence/": "future task output in the queue",
    "experiments/results_missingness/": "future task output in the queue",
    "experiments/results_placebo/": "future task output in the queue",
    "experiments/results_rank_stability/": "future task output in the queue",
    "experiments/results_serving_eval/": "future task output in the queue",
    "tests/test_artifact_registry.py": "future task output in the queue",
}
ABSENCE_CONTEXT = re.compile(
    r"\b(absent|dead|does not exist|missing|not found|would look for)\b"
    r"|\bno\b.*\b(files?|matches?)\b",
    re.IGNORECASE,
)

MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
REFERENCE_LINK_RE = re.compile(r"^\s*\[[^\]]+\]:\s*(\S+)")
CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")
LINE_SUFFIX_RE = re.compile(r":\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*$")
GLOB_CHARS = set("*?[")


@dataclass(frozen=True)
class Baseline:
    root_passed: int
    backend_passed: int
    modeling_rows: int
    features: int
    target_rows: int
    inference_rows: int
    page_files: int
    route_declarations: int
    page_routes: int
    redirects: int


def _markdown_files(root: Path) -> list[Path]:
    files = list(root.glob("*.md"))
    docs = root / "docs"
    if docs.is_dir():
        files.extend(docs.glob("*.md"))
    return sorted(path for path in files if path.is_file())


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _require(pattern: str, text: str, label: str) -> tuple[str, ...]:
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    if not match:
        raise ValueError(
            f"{BASELINE_PATH}:1: [DOC-BASELINE] cannot parse {label}; "
            "keep the baseline table in its documented command/result form"
        )
    return match.groups()


def _load_baseline(root: Path) -> Baseline:
    path = root / BASELINE_PATH
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ValueError(f"{BASELINE_PATH}:1: [DOC-BASELINE] file is missing") from None

    root_passed = int(
        _require(
            r"PYTHONPATH=\. python -m pytest tests/[^\n]*?PASS[^\n]*?(\d+) passed",
            text,
            "root pytest result",
        )[0]
    )
    backend_passed = int(
        _require(
            r"PYTHONPATH=backend python -m pytest backend/tests[^\n]*?PASS[^\n]*?(\d+) passed",
            text,
            "backend pytest result",
        )[0]
    )
    data = tuple(
        int(value)
        for value in _require(
            r"make data-validate[^\n]*?PASS[^\n]*?(\d+) modeling rows, "
            r"(\d+) features, (\d+) target rows, (\d+) inference-only rows",
            text,
            "data-validation result",
        )
    )
    routes = tuple(
        int(value)
        for value in _require(
            r"found (\d+) `frontend/src/pages/\*Page\.jsx` files\.[^\n]*?contains "
            r"(\d+) `<Route>` declarations: (\d+) render page components and "
            r"(\d+) redirect",
            text,
            "frontend route inventory",
        )
    )
    return Baseline(root_passed, backend_passed, *data, *routes)


def _strip_markdown_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]
    return unquote(target.split("#", 1)[0].split("?", 1)[0])


def _expand_braces(value: str) -> list[str]:
    match = re.search(r"\{([^{}]+)\}", value)
    if not match:
        return [value]
    expanded: list[str] = []
    for choice in match.group(1).split(","):
        expanded.extend(
            _expand_braces(value[: match.start()] + choice + value[match.end() :])
        )
    return expanded


def _looks_like_repo_path(value: str) -> bool:
    if not value or value.startswith(("/", "http://", "https://", "mailto:")):
        return False
    if any(char.isspace() for char in value):
        return False
    first = value.removeprefix("./").split("/", 1)[0]
    has_extension = bool(re.search(r"\.[A-Za-z][A-Za-z0-9*?]*(?:$|[:#])", value))
    return "/" in value and (first in KNOWN_TOP_LEVEL_DIRS or has_extension)


def _path_exists(root: Path, value: str, *, markdown_file: Path | None) -> bool:
    value = LINE_SUFFIX_RE.sub("", value.rstrip(".,;"))
    if value in PATH_VALUE_EXCLUSIONS:
        return True
    if value.startswith(tuple(PLANNED_PATH_EXCLUSIONS)):
        return True
    if (
        any(marker in value for marker in ("<", ">", "…", "–", "20YY"))
        or "/." in value
    ):
        return True
    candidates = _expand_braces(value)
    base = markdown_file.parent if markdown_file is not None else root
    for candidate in candidates:
        if any(char in candidate for char in GLOB_CHARS):
            matches = list(base.glob(candidate))
            if not matches and markdown_file is None:
                matches = list(root.rglob(candidate))
            if not matches:
                return False
        elif not (base / candidate).exists():
            if markdown_file is not None or not list(root.rglob(candidate)):
                return False
    return True


def _lint_paths(root: Path, path: Path, lines: list[str]) -> list[str]:
    rel = _relative(root, path)
    errors: list[str] = []
    in_fence = False
    for line_number, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue

        raw_targets = MARKDOWN_LINK_RE.findall(line)
        reference = REFERENCE_LINK_RE.match(line)
        if reference:
            raw_targets.append(reference.group(1))
        for raw_target in raw_targets:
            target = _strip_markdown_target(raw_target)
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if not _path_exists(root, target, markdown_file=path):
                errors.append(
                    f"{rel}:{line_number}: [DOC-LINK] missing relative link target: {target}"
                )

        if (
            in_fence
            or any(marker in line for marker in PATH_CONTEXT_EXCLUSIONS)
            or ABSENCE_CONTEXT.search(line)
        ):
            continue
        for raw_value in CODE_SPAN_RE.findall(line):
            value = raw_value.strip()
            if not _looks_like_repo_path(value):
                continue
            if not _path_exists(root, value, markdown_file=None):
                errors.append(
                    f"{rel}:{line_number}: [DOC-PATH] missing cited repository path: {value}"
                )
    return errors


def _count_diagnostic(
    rel: str, line_number: int, label: str, observed: int, expected: int
) -> str | None:
    if observed == expected:
        return None
    return (
        f"{rel}:{line_number}: [DOC-TRUTH] stale active {label}: {observed}; "
        f"current {BASELINE_PATH} value is {expected}"
    )


def _lint_truth(root: Path, path: Path, lines: list[str], baseline: Baseline) -> list[str]:
    rel = _relative(root, path)
    if rel in TRUTH_DRIFT_EXCLUSIONS:
        return []

    errors: list[str] = []
    in_fence = False
    for line_number, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        lowered = line.casefold()

        checks: list[tuple[str, str, int]] = []
        if "backend" in lowered and "test" in lowered:
            checks.append(
                (
                    r"backend(?: suite)?[^\d\n]{0,30}(\d+)/(?:\d+)",
                    "backend passed tests",
                    baseline.backend_passed,
                )
            )
            checks.append(
                (r"(\d+) backend tests?", "backend passed tests", baseline.backend_passed)
            )
        if ("root" in lowered or "pipeline" in lowered) and "test" in lowered:
            checks.append(
                (
                    r"root(?: suite)?[^\d\n]{0,30}(\d+)/(?:\d+)",
                    "root passed tests",
                    baseline.root_passed,
                )
            )
            checks.append(
                (
                    r"(\d+) (?:pipeline|root) tests?",
                    "root passed tests",
                    baseline.root_passed,
                )
            )
        checks.append(
            (
                r"(\d+) `?frontend/src/pages/\*?Page\.jsx`? files",
                "frontend page-file count",
                baseline.page_files,
            )
        )
        checks.append(
            (
                r"(\d+) `<Route>` declarations",
                "route-declaration count",
                baseline.route_declarations,
            )
        )
        checks.append(
            (
                r"(\d+) render page components",
                "page-rendering route count",
                baseline.page_routes,
            )
        )
        checks.append((r"(\d+) redirect", "redirect route count", baseline.redirects))

        if ("training dataset" in lowered or "modeling dataset" in lowered) and "rows" in lowered:
            checks.append(
                (
                    r"(\d+) (?:modeling )?rows",
                    "modeling-row count",
                    baseline.modeling_rows,
                )
            )
            checks.append(
                (r"(\d+) target rows", "target-row count", baseline.target_rows)
            )
        if "data-validate" in lowered:
            checks.append((r"(\d+) features", "feature count", baseline.features))
            checks.append(
                (
                    r"(\d+) inference-only",
                    "inference-only row count",
                    baseline.inference_rows,
                )
            )

        for pattern, label, expected in checks:
            matches = list(re.finditer(pattern, line, re.IGNORECASE))
            if not matches or any(int(match.group(1)) == expected for match in matches):
                continue
            diagnostic = _count_diagnostic(
                rel, line_number, label, int(matches[0].group(1)), expected
            )
            if diagnostic:
                errors.append(diagnostic)
    return errors


def lint_repository(root: Path) -> list[str]:
    """Return stable file:line diagnostics; an empty list means the lint passes."""
    root = root.resolve()
    try:
        baseline = _load_baseline(root)
    except ValueError as exc:
        return [str(exc)]

    errors: list[str] = []
    for path in _markdown_files(root):
        lines = path.read_text(encoding="utf-8").splitlines()
        errors.extend(_lint_paths(root, path, lines))
        errors.extend(_lint_truth(root, path, lines, baseline))
    return sorted(set(errors))


def run_stale_fixture(root: Path) -> int:
    """Prove that a temporary stale active assertion produces a diagnostic."""
    root = root.resolve()
    try:
        baseline = _load_baseline(root)
        baseline_text = (root / BASELINE_PATH).read_text(encoding="utf-8")
    except ValueError as exc:
        print(exc)
        return 1

    stale_count = max(0, baseline.backend_passed - 1)
    with tempfile.TemporaryDirectory(prefix="financeiq-docs-lint-") as directory:
        fixture_root = Path(directory)
        (fixture_root / "docs").mkdir()
        (fixture_root / BASELINE_PATH).write_text(baseline_text, encoding="utf-8")
        (fixture_root / "backend" / "tests").mkdir(parents=True)
        (fixture_root / "frontend" / "src" / "pages").mkdir(parents=True)
        (fixture_root / "frontend" / "src" / "App.jsx").write_text(
            "", encoding="utf-8"
        )
        (fixture_root / "frontend" / "src" / "pages" / "FixturePage.jsx").write_text(
            "", encoding="utf-8"
        )
        (fixture_root / "REPO_MAP.md").write_text(
            f"Current: `backend/tests/` has {stale_count} backend tests.\n",
            encoding="utf-8",
        )
        errors = lint_repository(fixture_root)

    truth_errors = [error for error in errors if "[DOC-TRUTH]" in error]
    if len(errors) != 1 or len(truth_errors) != 1:
        for error in errors:
            print(error)
        print("Docs lint stale-fixture check FAILED: expected one DOC-TRUTH diagnostic.")
        return 1
    print(truth_errors[0])
    print("Docs lint stale-fixture check PASSED: deliberate drift was rejected.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to this script's parent repository)",
    )
    parser.add_argument(
        "--self-test-stale",
        action="store_true",
        help="run an isolated stale-current-assertion fixture and require rejection",
    )
    args = parser.parse_args(argv)
    if args.self_test_stale:
        return run_stale_fixture(args.root)
    errors = lint_repository(args.root)
    if errors:
        for error in errors:
            print(error)
        print(f"Docs lint FAILED: {len(errors)} violation(s).")
        return 1
    print("Docs lint PASSED: local links, cited paths, and active baseline assertions agree.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
