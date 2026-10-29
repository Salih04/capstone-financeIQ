"""Record and compare CI test-gate counts (collected/executed/skipped/deselected).

Stdlib only. Every gate in .github/workflows/verify.yml writes one counts file;
`compare` checks it against .github/ci-test-gates.json, whose root and backend
expectations are parsed from the dated docs/VERIFICATION_BASELINE.md table at
run time. Nothing here edits the baseline. See docs/CI_TEST_GATES.md.

A gate fails closed: failures, errors, any skip, an unexpected deselection, a
collected test that did not run, a collection below the approved count, or an
unparseable baseline all exit non-zero. A collection above the approved count
passes with a warning, because the dated baseline is refreshed only by a task
that owns verification truth.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import unittest
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / ".github" / "ci-test-gates.json"
BASELINE = REPO / "docs" / "VERIFICATION_BASELINE.md"

PASS, WARN, FAIL = "PASS", "PASS (warning)", "FAIL"


class GateError(Exception):
    """The gate cannot establish a trustworthy comparison."""


def read_listed_ids(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def read_collected_ids(path: Path) -> list[str]:
    """Node ids from `pytest --collect-only -q` output (summary lines dropped)."""
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if "::" in line]


def baseline_counts(text: str, command: str) -> tuple[int, int]:
    """(collected, passed) from the one baseline table row for `command`."""
    pattern = re.escape(f"`{command}`") + r"[^\n]*?(\d+) collected, (\d+) passed"
    matches = re.findall(pattern, text)
    if len(matches) != 1:
        raise GateError(
            f"{BASELINE.name}: expected exactly one result row for `{command}`, found {len(matches)}"
        )
    collected, passed = (int(value) for value in matches[0])
    if collected != passed:
        raise GateError(
            f"{BASELINE.name}: row for `{command}` records {passed} of {collected} passed; "
            "a dated baseline that is not a full pass cannot be a gate"
        )
    return collected, passed


def counts_from_junit(
    suite: str,
    junit: Path,
    *,
    collected_ids: list[str] | None = None,
    deselect_ids: list[str] | None = None,
) -> dict:
    root = ET.parse(junit).getroot()
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    if not suites:
        raise GateError(f"{junit}: no <testsuite> element")
    totals = {key: sum(int(s.get(key, 0)) for s in suites) for key in ("tests", "failures", "errors", "skipped")}
    deselect_ids = deselect_ids or []
    counts = {
        "suite": suite,
        "runner": "pytest",
        "collected": totals["tests"] + len(deselect_ids),
        "deselected": len(deselect_ids),
        "skipped": totals["skipped"],
        "executed": totals["tests"] - totals["skipped"],
        "failed": totals["failures"],
        "errors": totals["errors"],
        "other_non_pass": 0,
    }
    counts["passed"] = counts["executed"] - counts["failed"] - counts["errors"]
    if collected_ids is not None:
        counts["collect_only"] = len(collected_ids)
        counts["deselect_unresolved"] = sorted(set(deselect_ids) - set(collected_ids))
    return counts


def run_unittest(suite: str, *, name: str | None, discover: str | None, pattern: str) -> tuple[dict, bool]:
    """Load exactly like the documented `python -m unittest` command, then run."""
    # `python -m` puts the working directory first on sys.path; mirror it so
    # `experiments.*` imports resolve the same way the documented commands do.
    sys.path.insert(0, os.getcwd())
    loader = unittest.TestLoader()
    tests = loader.loadTestsFromName(name) if name else loader.discover(discover, pattern=pattern)
    collected = tests.countTestCases()
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    skipped = len(result.skipped)
    failed = len(result.failures)
    errors = len(result.errors)
    other = len(result.expectedFailures) + len(result.unexpectedSuccesses)
    executed = result.testsRun - skipped
    counts = {
        "suite": suite,
        "runner": "unittest",
        "collected": collected,
        "deselected": 0,
        "skipped": skipped,
        "executed": executed,
        "failed": failed,
        "errors": errors,
        "other_non_pass": other,
        "passed": executed - failed - errors - other,
    }
    return counts, result.wasSuccessful()


def expected_collected(spec: dict, baseline_text: str | None) -> tuple[int, str]:
    expected = spec["expected"]
    if "from_baseline" in expected:
        if baseline_text is None:
            raise GateError(f"{BASELINE.name} is required for `{expected['from_baseline']}`")
        collected, _ = baseline_counts(baseline_text, expected["from_baseline"])
        return collected, f"{BASELINE.name} row `{expected['from_baseline']}`"
    return int(expected["approved_collected"]), expected["source"]


def evaluate(counts: dict, spec: dict, baseline_text: str | None, listed_deselect: list[str]) -> tuple[str, list[str]]:
    problems: list[str] = []
    warnings: list[str] = []
    try:
        approved, source = expected_collected(spec, baseline_text)
    except GateError as exc:
        return FAIL, [str(exc)]

    if counts["failed"] or counts["errors"] or counts["other_non_pass"]:
        problems.append(
            f"{counts['failed']} failed, {counts['errors']} errors, "
            f"{counts['other_non_pass']} expected-failure/unexpected-success"
        )
    if counts["skipped"]:
        problems.append(f"{counts['skipped']} skipped; a skip is not a pass and weakens the gate")
    if counts["deselected"] != len(listed_deselect):
        problems.append(
            f"{counts['deselected']} deselected but the governed list holds {len(listed_deselect)}"
        )
    if counts.get("deselect_unresolved"):
        problems.append(f"deselect ids no longer collected: {counts['deselect_unresolved']}")
    if "collect_only" in counts and counts["collect_only"] != counts["collected"]:
        problems.append(
            f"collect-only found {counts['collect_only']} but the run accounts for {counts['collected']}"
        )
    accounted = counts["executed"] + counts["skipped"] + counts["deselected"]
    if accounted != counts["collected"]:
        problems.append(f"{counts['collected'] - accounted} collected tests neither ran, skipped nor deselected")
    if counts["passed"] != counts["executed"]:
        problems.append(f"{counts['passed']} of {counts['executed']} executed tests passed")
    if counts["collected"] < approved:
        problems.append(
            f"collected {counts['collected']} is below the approved {approved} ({source}); "
            "tests were removed or silently reverted"
        )
    elif counts["collected"] > approved:
        warnings.append(
            f"collected {counts['collected']} exceeds the approved {approved} ({source}); "
            "the dated record was not rewritten and needs a verification-truth refresh"
        )
    if problems:
        return FAIL, problems + warnings
    return (WARN if warnings else PASS), warnings


def _baseline_text() -> str | None:
    return BASELINE.read_text(encoding="utf-8") if BASELINE.is_file() else None


def _listed_deselect(spec: dict) -> list[str]:
    return read_listed_ids(REPO / spec["deselect_list"]) if "deselect_list" in spec else []


def _row(counts: dict | None, suite: str, status: str) -> str:
    if counts is None:
        return f"| {suite} | — | — | — | — | — | {status} |"
    return (
        f"| {suite} | {counts['collected']} | {counts['executed']} | {counts['passed']} | "
        f"{counts['skipped']} | {counts['deselected']} | {status} |"
    )


HEADER = [
    "| Gate | Collected | Executed | Passed | Skipped | Deselected | Status |",
    "|---|---|---|---|---|---|---|",
]


def _emit(lines: list[str]) -> None:
    text = "\n".join(lines) + "\n"
    print(text)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")


def _annotate(level: str, suite: str, messages: list[str]) -> None:
    for message in messages:
        print(f"::{level} title=test gate {suite}::{message}")


def compare(manifest: dict, suite_names: list[str], counts_dir: Path) -> int:
    baseline_text = _baseline_text()
    lines = list(HEADER)
    failed = False
    for suite in suite_names:
        spec = manifest["suites"][suite]
        path = counts_dir / f"{suite}.json"
        if not path.is_file():
            lines.append(_row(None, suite, "FAIL — no counts recorded"))
            _annotate("error", suite, ["no counts file; the gate did not run"])
            failed = True
            continue
        counts = json.loads(path.read_text(encoding="utf-8"))
        status, messages = evaluate(counts, spec, baseline_text, _listed_deselect(spec))
        lines.append(_row(counts, suite, status))
        _annotate("error" if status == FAIL else "warning", suite, messages)
        failed = failed or status == FAIL
    _emit(lines)
    return 1 if failed else 0


def summarize(manifest: dict, counts_dir: Path, needs: dict) -> int:
    status = compare(manifest, list(manifest["suites"]), counts_dir)
    lines = ["| Job | Result |", "|---|---|"]
    jobs = {spec["job"] for spec in manifest["suites"].values()} | {
        spec["job"] for spec in manifest.get("builds", {}).values()
    }
    for job in sorted(jobs):
        result = needs.get(job, {}).get("result", "missing")
        lines.append(f"| {job} | {result} |")
        if result != "success":
            _annotate("error", job, [f"job result is {result}, not success"])
            status = 1
    lines += ["", "**Not run in CI — these are not passes:**", ""]
    lines += [f"- {item['gate']}: {item['reason']} ({item['where']})" for item in manifest["not_run_in_ci"]]
    _emit(lines)
    return status


def check_workspace(root: Path, allowed: list[str]) -> list[str]:
    """Paths on disk (outside .git) that fall outside every allowed prefix."""
    unexpected = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not (Path(dirpath) == root and d == ".git")]
        for filename in filenames:
            rel = (Path(dirpath) / filename).relative_to(root).as_posix()
            if not any(rel == prefix or rel.startswith(prefix.rstrip("/") + "/") for prefix in allowed):
                unexpected.append(rel)
    return sorted(unexpected)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    sub = parser.add_subparsers(dest="command", required=True)

    junit = sub.add_parser("junit", help="record counts from a pytest JUnit XML report")
    junit.add_argument("--suite", required=True)
    junit.add_argument("--junit", type=Path, required=True)
    junit.add_argument("--collected-ids", type=Path)
    junit.add_argument("--out", type=Path, required=True)

    run = sub.add_parser("run-unittest", help="run a unittest suite and record its counts")
    run.add_argument("--suite", required=True)
    target = run.add_mutually_exclusive_group(required=True)
    target.add_argument("--name")
    target.add_argument("--discover")
    run.add_argument("--pattern", default="test*.py")
    run.add_argument("--out", type=Path, required=True)

    cmp_ = sub.add_parser("compare", help="compare recorded counts with approved expectations")
    cmp_.add_argument("--suite", action="append", required=True)
    cmp_.add_argument("--counts", type=Path, required=True)

    summ = sub.add_parser("summarize", help="compare every gate and check job results")
    summ.add_argument("--counts", type=Path, required=True)
    summ.add_argument("--needs-json", required=True)

    sub.add_parser("check-workspace", help="fail if files exist outside synthetic_workspace")

    args = parser.parse_args(argv)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))

    if args.command == "junit":
        spec = manifest["suites"][args.suite]
        if not args.junit.is_file():
            # A test step that never ran leaves no report; record nothing so
            # `compare` reports this gate as FAIL rather than crashing first.
            print(f"::error title=test gate {args.suite}::{args.junit} was not written")
            return 0
        ids = read_collected_ids(args.collected_ids) if args.collected_ids else None
        counts = counts_from_junit(args.suite, args.junit, collected_ids=ids, deselect_ids=_listed_deselect(spec))
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / f"{args.suite}.json").write_text(json.dumps(counts, indent=2) + "\n", encoding="utf-8")
        return 0
    if args.command == "run-unittest":
        if args.suite not in manifest["suites"]:
            raise GateError(f"{args.suite} is not declared in {args.manifest}")
        counts, ok = run_unittest(args.suite, name=args.name, discover=args.discover, pattern=args.pattern)
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / f"{args.suite}.json").write_text(json.dumps(counts, indent=2) + "\n", encoding="utf-8")
        return 0 if ok else 1
    if args.command == "compare":
        return compare(manifest, args.suite, args.counts)
    if args.command == "summarize":
        return summarize(manifest, args.counts, json.loads(args.needs_json))
    unexpected = check_workspace(Path.cwd(), manifest["synthetic_workspace"])
    for rel in unexpected:
        print(f"::error title=synthetic workspace::{rel} is outside the synthetic-only checkout")
    print(f"workspace check: {len(unexpected)} unexpected paths")
    return 1 if unexpected else 0


if __name__ == "__main__":
    sys.exit(main())
