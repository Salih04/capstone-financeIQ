"""Record and compare CI test-gate counts (collected/executed/skipped/deselected).

Stdlib only. Every gate in .github/workflows/verify.yml writes one counts file;
`compare` checks it against .github/ci-test-gates.json, whose root and backend
expectations are parsed from the dated docs/VERIFICATION_BASELINE.md table at
run time. Nothing here edits the baseline. See docs/CI_TEST_GATES.md.

A gate fails closed: failures, errors, any skip, XFAIL or XPASS, a deselected
id outside the governed list, a collected test that did not run or was dropped
without a deselection record, a collection below the approved count, a missing
or malformed report, or an unparseable baseline all exit non-zero. A collection
above the approved count passes with a warning, because the dated baseline is
refreshed only by a task that owns verification truth.

pytest gates need two reports from the same run: the JUnit XML and the
ci_pytest_ledger.py ledger. JUnit alone cannot show an XPASS or a deselection.
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


LEDGER_SCHEMA = "financeiq-ci-pytest-ledger/1"
LEDGER_OUTCOMES = {"passed", "failed", "error", "skipped", "xfailed", "xpassed", "incomplete"}
COUNT_FIELDS = ("collected", "deselected", "skipped", "executed", "failed", "errors", "other_non_pass", "passed")
PASSING = {"passed", "xpassed"}  # what JUnit shows as a pass; the ledger tells them apart


def junit_address(node_id: str) -> tuple[str, str]:
    """(classname, name) that pytest's JUnit writer derives from a node id."""
    path, bracket, params = node_id.partition("[")
    names = path.split("::")
    names[0] = re.sub(r"\.py$", "", names[0].replace("/", "."))
    names[-1] += bracket + params
    return ".".join(names[:-1]), names[-1]


def read_junit_cases(junit: Path) -> dict[tuple[str, str], bool]:
    """{(classname, name): passed} for every <testcase>; a repeated case passes only if every copy does."""
    try:
        root = ET.parse(junit).getroot()
    except (ET.ParseError, OSError) as exc:
        raise GateError(f"malformed JUnit report {junit.name}: {exc}") from exc
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    if root.tag not in ("testsuite", "testsuites") or not suites:
        raise GateError(f"malformed JUnit report {junit.name}: no <testsuite> element")
    cases: dict[tuple[str, str], bool] = {}
    for suite in suites:
        declared = suite.get("tests")
        if declared is not None:
            try:
                expected = int(declared)
            except ValueError as exc:
                raise GateError(
                    f"JUnit test count is invalid: {declared!r}"
                ) from exc
            actual = sum(1 for _ in suite.iter("testcase"))
            if expected != actual:
                raise GateError(
                    f"JUnit test count mismatch: declared {expected}, "
                    f"found {actual}"
                )
    for case in (case for suite in suites for case in suite.iter("testcase")):
        key = (case.get("classname", ""), case.get("name", ""))
        passed = not any(child.tag in ("failure", "error", "skipped") for child in case)
        if key in cases:
            raise GateError(
                f"duplicate JUnit testcase address {key!r} in {junit.name}"
            )
        cases[key] = passed
    return cases


def read_ledger(ledger: Path) -> dict:
    try:
        doc = json.loads(ledger.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GateError(f"malformed ledger {ledger.name}: {exc}") from exc
    lists = ("collected", "deselected", "selected")
    if (
        not isinstance(doc, dict)
        or doc.get("schema") != LEDGER_SCHEMA
        or any(not isinstance(doc.get(key), list) or not all(isinstance(i, str) for i in doc[key]) for key in lists)
        or not isinstance(doc.get("outcomes"), dict)
        or any(not isinstance(v, str) or v not in LEDGER_OUTCOMES for v in doc["outcomes"].values())
        or any(type(doc.get(key)) is not int for key in ("exitstatus", "collection_errors"))
    ):
        raise GateError(f"malformed ledger {ledger.name}: not a {LEDGER_SCHEMA} document")
    for key in lists:
        if len(set(doc[key])) != len(doc[key]):
            raise GateError(f"malformed ledger {ledger.name}: duplicate node ids in {key}")
    collected = set(doc["collected"])
    if not set(doc["deselected"]) <= collected or not set(doc["selected"]) <= collected:
        raise GateError(f"malformed ledger {ledger.name}: deselected or selected ids that were never collected")
    if set(doc["deselected"]) & set(doc["selected"]) or not set(doc["outcomes"]) <= set(doc["selected"]):
        raise GateError(f"malformed ledger {ledger.name}: outcomes for ids that were not selected")
    return doc


def counts_from_pytest(
    suite: str,
    junit: Path,
    ledger: Path | None,
    *,
    collected_ids: list[str] | None = None,
    deselect_ids: list[str] | None = None,
) -> dict:
    """Counts from the pytest ledger, cross-checked test by test against JUnit.

    A missing, unparseable or inconsistent report yields a `malformed` record,
    which `evaluate` always fails, instead of raising.
    """
    try:
        return _counts_from_pytest(suite, junit, ledger, collected_ids=collected_ids, deselect_ids=deselect_ids)
    except (GateError, OSError) as exc:
        return malformed(suite, "pytest", str(exc))


def _counts_from_pytest(
    suite: str,
    junit: Path,
    ledger: Path | None,
    *,
    collected_ids: list[str] | None,
    deselect_ids: list[str] | None,
) -> dict:
    if ledger is None:
        raise GateError(
            "no pytest ledger: JUnit alone cannot show an XPASS or a deselection, "
            "so the run cannot be accepted (load -p ci_pytest_ledger)"
        )
    doc = read_ledger(ledger)
    cases = read_junit_cases(junit)
    outcomes: dict[str, str] = doc["outcomes"]
    # Every selected pytest node must have a distinct JUnit identity.
    selected_addresses: dict[tuple[str, str], str] = {}
    for node_id in doc["selected"]:
        address = junit_address(node_id)
        if address in selected_addresses:
            raise GateError(
                f"colliding ledger JUnit address {address!r}: "
                f"{selected_addresses[address]!r} and {node_id!r}"
            )
        selected_addresses[address] = node_id
    reported = {
        junit_address(node_id): outcome in PASSING
        for node_id, outcome in outcomes.items()
    }
    if reported != cases:
        differ = sorted(f"{c}::{n}" for c, n in set(reported) ^ set(cases))
        differ += sorted(f"{c}::{n}" for (c, n), ok in reported.items() if (c, n) in cases and cases[(c, n)] != ok)
        raise GateError(f"the JUnit report and the ledger disagree on {len(differ)} tests, e.g. {differ[:3]}")

    tally = {outcome: 0 for outcome in LEDGER_OUTCOMES}
    for outcome in outcomes.values():
        tally[outcome] += 1
    deselected = doc["deselected"]
    dropped = sorted(set(doc["collected"]) - set(doc["selected"]) - set(deselected))
    executed = len(outcomes) - tally["skipped"]
    counts = {
        "suite": suite,
        "runner": "pytest",
        "evidence": "ledger+junit",
        "pytest_version": doc.get("pytest_version"),
        "collected": len(doc["collected"]),
        "deselected": len(deselected),
        "skipped": tally["skipped"],
        "executed": executed,
        "failed": tally["failed"],
        "errors": tally["error"] + tally["incomplete"],
        "other_non_pass": tally["xfailed"] + tally["xpassed"],
        "xfailed": tally["xfailed"],
        "xpassed": tally["xpassed"],
        "passed": tally["passed"],
        "exitstatus": doc["exitstatus"],
        "collection_errors": doc["collection_errors"],
        "deselected_ids": sorted(deselected),
        "dropped_ids": dropped,
        "not_reported_ids": sorted(set(doc["selected"]) - set(outcomes)),
    }
    if deselect_ids is not None:
        counts["governed_deselect"] = sorted(deselect_ids)
    if collected_ids is not None:
        counts["collect_only"] = len(collected_ids)
        counts["collect_only_mismatch"] = sorted(set(collected_ids) ^ set(doc["collected"]))
    return counts


def malformed(suite: str, runner: str, reason: str) -> dict:
    return {"suite": suite, "runner": runner, "malformed": reason}


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


def _integrity(counts: object, spec: dict, suite: str | None) -> list[str]:
    """Reasons a counts record cannot be trusted at all."""
    if not isinstance(counts, dict):
        return ["counts record is not a JSON object"]
    if counts.get("malformed"):
        return [f"malformed report: {counts['malformed']}"]
    problems = []
    if suite is not None and counts.get("suite") != suite:
        problems.append(f"counts record names suite {counts.get('suite')!r}, expected {suite!r}")
    runner = spec.get("runner")
    if runner is not None and counts.get("runner") != runner:
        problems.append(f"counts record names runner {counts.get('runner')!r}, expected {runner!r}")
    bad = [key for key in COUNT_FIELDS if type(counts.get(key)) is not int or counts[key] < 0]
    if bad:
        problems.append(f"malformed counts record: {bad} missing or not non-negative integers")
    if counts.get("runner") == "pytest" and counts.get("evidence") != "ledger+junit":
        problems.append("pytest counts without a ledger cannot exclude an XPASS or a deselection")
    return problems


def evaluate(
    counts: dict, spec: dict, baseline_text: str | None, listed_deselect: list[str], *, suite: str | None = None
) -> tuple[str, list[str]]:
    problems: list[str] = []
    warnings: list[str] = []
    try:
        approved, source = expected_collected(spec, baseline_text)
    except GateError as exc:
        return FAIL, [str(exc)]
    integrity = _integrity(counts, spec, suite)
    if integrity:
        return FAIL, integrity

    if counts["failed"] or counts["errors"]:
        problems.append(f"{counts['failed']} failed, {counts['errors']} errors")
    if counts.get("xpassed"):
        problems.append(f"{counts['xpassed']} XPASS; a test marked xfail that passes is not a pass")
    if counts.get("xfailed"):
        problems.append(f"{counts['xfailed']} XFAIL; an expected failure is not a pass")
    other = counts["other_non_pass"] - counts.get("xpassed", 0) - counts.get("xfailed", 0)
    if other:
        problems.append(f"{other} expected-failure/unexpected-success")
    if counts["skipped"]:
        problems.append(f"{counts['skipped']} skipped; a skip is not a pass and weakens the gate")
    if counts.get("exitstatus", 0):
        problems.append(f"pytest exit status {counts['exitstatus']}")
    if counts.get("collection_errors"):
        problems.append(f"{counts['collection_errors']} collection errors")

    listed = set(listed_deselect)
    if counts["runner"] == "pytest":
        deselected = set(counts.get("deselected_ids", []))
        unknown = sorted(deselected - listed)
        unapplied = sorted(listed - deselected)
        if unknown:
            problems.append(f"{len(unknown)} deselected ids not in the governed deselect list: {unknown[:5]}")
        if unapplied:
            problems.append(f"{len(unapplied)} governed deselect ids were not deselected by this run: {unapplied[:5]}")
    if counts["deselected"] != len(listed):
        problems.append(f"{counts['deselected']} deselected but the governed list holds {len(listed)}")
    if counts.get("dropped_ids"):
        problems.append(
            f"{len(counts['dropped_ids'])} collected tests removed without a deselection record: {counts['dropped_ids'][:5]}"
        )
    if counts.get("not_reported_ids"):
        problems.append(
            f"{len(counts['not_reported_ids'])} selected tests never reported an outcome: {counts['not_reported_ids'][:5]}"
        )
    if "collect_only" in counts and (counts["collect_only"] != counts["collected"] or counts.get("collect_only_mismatch")):
        problems.append(
            f"collect-only found {counts['collect_only']} but the run collected {counts['collected']} "
            f"({len(counts.get('collect_only_mismatch', []))} ids differ)"
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
    if not isinstance(counts, dict) or any(type(counts.get(key)) is not int for key in COUNT_FIELDS):
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
        try:
            counts = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            counts = malformed(suite, spec.get("runner", "?"), f"unreadable counts file: {exc}")
        status, messages = evaluate(counts, spec, baseline_text, _listed_deselect(spec), suite=suite)
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
    """Paths under root that break the synthetic-only scope, sorted.

    Reported: files outside every allowed prefix; directories that are neither
    inside an allowed prefix nor an ancestor of one (even empty ones); every
    symlink anywhere, including .git, since none is tracked and any one can
    reach outside the scope; and anything that is not a regular file. Symlinks
    are never followed. An unreadable directory raises rather than hiding.
    """
    prefixes = [prefix.rstrip("/") for prefix in allowed]

    def inside(rel: str) -> bool:
        return any(rel == prefix or rel.startswith(prefix + "/") for prefix in prefixes)

    def ancestor(rel: str) -> bool:
        return any(prefix.startswith(rel + "/") for prefix in prefixes)

    def raise_error(exc: OSError) -> None:
        raise exc

    unexpected = []
    for dirpath, dirnames, filenames in os.walk(root, onerror=raise_error):
        here = Path(dirpath)
        for name in sorted(dirnames + filenames):
            path = here / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                unexpected.append(f"{rel} (symlink)")
            elif here == root and name == ".git":
                continue
            elif name in dirnames:
                if not (inside(rel) or ancestor(rel)):
                    unexpected.append(f"{rel}/")
            elif not path.is_file():
                unexpected.append(f"{rel} (not a regular file)")
            elif not inside(rel):
                unexpected.append(rel)
        # Never descend into .git or through a symlink (os.walk already does not follow).
        dirnames[:] = [d for d in dirnames if not (here == root and d == ".git") and not (here / d).is_symlink()]
    return sorted(unexpected)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    sub = parser.add_subparsers(dest="command", required=True)

    junit = sub.add_parser("junit", help="record counts from a pytest JUnit XML report")
    junit.add_argument("--suite", required=True)
    junit.add_argument("--junit", type=Path, required=True)
    junit.add_argument("--ledger", type=Path, help="ci_pytest_ledger.py output of the same run; required to pass")
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
        ledger = args.ledger
        if ledger is not None and not ledger.is_file():
            print(f"::error title=test gate {args.suite}::{ledger} was not written")
            ledger = None
        try:
            ids = read_collected_ids(args.collected_ids) if args.collected_ids else None
        except OSError as exc:
            # Recorded, not raised, so `compare` prints the table and fails the gate.
            counts = malformed(args.suite, "pytest", f"unreadable collect-only ids: {exc}")
        else:
            counts = counts_from_pytest(
                args.suite, args.junit, ledger, collected_ids=ids, deselect_ids=_listed_deselect(spec)
            )
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
        print(f"::error title=synthetic workspace::{rel} breaks the synthetic-only checkout")
    print(f"workspace check: {len(unexpected)} unexpected paths")
    return 1 if unexpected else 0


if __name__ == "__main__":
    sys.exit(main())
