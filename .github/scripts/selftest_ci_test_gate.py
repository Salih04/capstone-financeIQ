"""Self-test for ci_test_gate.py: every weaker-gate shape must fail closed.

Uses only invented test files, JUnit/ledger/baseline strings and directories in
temporary directories; it reads no repository data. The pytest cases run real
pytest on throwaway synthetic suites. Run:
python -B .github/scripts/selftest_ci_test_gate.py -v
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import ci_test_gate as gate  # noqa: E402

BASELINE = (
    "| `PYTHONPATH=. python -m pytest tests/` | PASS — 10 collected, 10 passed |\n"
    "| `PYTHONPATH=backend python -m pytest backend/tests` | PASS — 4 collected, 4 passed (1 warning) |\n"
)
ROOT_SPEC = {"runner": "pytest", "expected": {"from_baseline": "PYTHONPATH=. python -m pytest tests/"}, "deselect_list": "x"}
BACKEND_SPEC = {"runner": "pytest", "expected": {"from_baseline": "PYTHONPATH=backend python -m pytest backend/tests"}}
SYNTHETIC_SPEC = {"runner": "unittest", "expected": {"approved_collected": 3, "source": "approval record"}}
LISTED = ["tests/test_a.py::test_env_1", "tests/test_a.py::test_env_2"]
IDS = [f"tests/test_a.py::test_{i}" for i in range(8)] + LISTED


def junit_xml(outcomes: dict[str, str]) -> str:
    """A pytest-shaped JUnit report; xpassed is written as a plain pass, as pytest does."""
    child = {
        "failed": '<failure message="x"/>',
        "error": '<error message="x"/>',
        "skipped": '<skipped type="pytest.skip" message="x"/>',
        "xfailed": '<skipped type="pytest.xfail" message="x"/>',
    }
    cases = []
    for node_id, outcome in outcomes.items():
        classname, name = gate.junit_address(node_id)
        cases.append(f'<testcase classname="{classname}" name="{name}">{child.get(outcome, "")}</testcase>')
    return f'<?xml version="1.0"?><testsuites><testsuite name="pytest">{"".join(cases)}</testsuite></testsuites>'


def ledger_doc(collected, deselected=(), outcomes=None, **extra) -> dict:
    deselected = list(deselected)
    selected = [i for i in collected if i not in deselected]
    doc = {
        "schema": gate.LEDGER_SCHEMA,
        "pytest_version": "synthetic",
        "exitstatus": 0,
        "collection_errors": 0,
        "collected": list(collected),
        "deselected": deselected,
        "selected": selected,
        "outcomes": dict(outcomes) if outcomes is not None else {i: "passed" for i in selected},
    }
    doc.update(extra)
    return doc


class GateCase(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)

    def reports(self, suite: str, ledger: dict | str, xml: str | None = None) -> tuple[Path, Path]:
        junit_path, ledger_path = self.dir / f"{suite}.xml", self.dir / f"{suite}.ledger.json"
        ledger_path.write_text(ledger if isinstance(ledger, str) else json.dumps(ledger))
        if xml is None:
            xml = junit_xml(json.loads(ledger_path.read_text())["outcomes"])
        junit_path.write_text(xml)
        return junit_path, ledger_path

    def counts(self, suite: str, ledger, xml=None, *, ids=None, listed=()) -> dict:
        junit_path, ledger_path = self.reports(suite, ledger, xml)
        return gate.counts_from_pytest(suite, junit_path, ledger_path, collected_ids=ids, deselect_ids=list(listed))

    def root(self, ledger=None, xml=None, *, ids=IDS, listed=LISTED, baseline=BASELINE):
        ledger = ledger_doc(IDS, LISTED) if ledger is None else ledger
        counts = self.counts("root-portable", ledger, xml, ids=ids, listed=listed)
        return gate.evaluate(counts, ROOT_SPEC, baseline, list(listed))

    def backend(self, ledger, xml=None, baseline=BASELINE):
        counts = self.counts("backend", ledger, xml)
        return gate.evaluate(counts, BACKEND_SPEC, baseline, [])

    def assertFails(self, result, fragment: str):
        status, messages = result
        self.assertEqual(status, gate.FAIL, messages)
        self.assertTrue(any(fragment in m for m in messages), messages)


class CountRulesTest(GateCase):
    def test_exact_portable_run_passes(self):
        self.assertEqual(self.root(), (gate.PASS, []))

    def test_backend_and_synthetic_exact_runs_pass(self):
        backend_ids = [f"backend/tests/test_b.py::test_{i}" for i in range(4)]
        self.assertEqual(self.backend(ledger_doc(backend_ids))[0], gate.PASS)
        synthetic = {
            "suite": "s", "runner": "unittest", "collected": 3, "deselected": 0, "skipped": 0,
            "executed": 3, "failed": 0, "errors": 0, "other_non_pass": 0, "passed": 3,
        }
        self.assertEqual(gate.evaluate(synthetic, SYNTHETIC_SPEC, None, [])[0], gate.PASS)

    def test_any_skip_fails(self):
        outcomes = {i: "passed" for i in IDS[:8]} | {IDS[0]: "skipped"}
        self.assertFails(self.root(ledger_doc(IDS, LISTED, outcomes)), "skipped")

    def test_failures_and_errors_fail(self):
        for outcome in ("failed", "error"):
            outcomes = {i: "passed" for i in IDS[:8]} | {IDS[0]: outcome}
            self.assertEqual(self.root(ledger_doc(IDS, LISTED, outcomes))[0], gate.FAIL)

    def test_shrunken_collection_fails(self):
        ledger = ledger_doc(IDS[2:], LISTED)
        self.assertFails(self.root(ledger, ids=IDS[2:]), "below the approved")

    def test_grown_collection_warns_without_rewriting(self):
        ids = IDS + ["tests/test_a.py::test_new"]
        self.assertEqual(self.root(ledger_doc(ids, LISTED), ids=ids)[0], gate.WARN)

    def test_stale_deselect_id_fails(self):
        ids = IDS[:-1] + ["tests/test_a.py::test_8"]
        self.assertFails(self.root(ledger_doc(ids, LISTED[:1]), ids=ids), "governed deselect")

    def test_collect_only_disagreeing_with_the_run_fails(self):
        self.assertFails(self.root(ids=IDS + ["tests/test_a.py::test_extra"]), "collect-only")

    def test_unparseable_or_partial_baseline_fails_closed(self):
        self.assertEqual(self.root(baseline="no table here")[0], gate.FAIL)
        self.assertEqual(self.root(baseline=None)[0], gate.FAIL)
        partial = BASELINE.replace("10 collected, 10 passed", "10 collected, 9 passed")
        self.assertEqual(self.root(baseline=partial)[0], gate.FAIL)
        self.assertEqual(self.root(baseline=BASELINE + BASELINE)[0], gate.FAIL)

    def test_unittest_runner_counts_and_flags_skips(self):
        module = self.dir / "synthetic_gate_case.py"
        module.write_text(
            "import unittest\n"
            "class T(unittest.TestCase):\n"
            "    def test_a(self): pass\n"
            "    def test_b(self): pass\n"
            "    @unittest.skip('missing input')\n"
            "    def test_c(self): pass\n"
        )
        sys.path.insert(0, str(self.dir))
        self.addCleanup(sys.path.remove, str(self.dir))
        counts, ok = gate.run_unittest("synthetic", name="synthetic_gate_case", discover=None, pattern="")
        self.assertTrue(ok)  # unittest itself calls a skip a success ...
        self.assertEqual((counts["collected"], counts["executed"], counts["skipped"]), (3, 2, 1))
        self.assertEqual(gate.evaluate(counts, SYNTHETIC_SPEC, None, [])[0], gate.FAIL)  # ... the gate does not

    def test_unittest_unexpected_success_fails(self):
        module = self.dir / "synthetic_gate_xpass.py"
        module.write_text(
            "import unittest\n"
            "class T(unittest.TestCase):\n"
            "    def test_a(self): pass\n"
            "    def test_b(self): pass\n"
            "    @unittest.expectedFailure\n"
            "    def test_c(self): pass\n"
        )
        sys.path.insert(0, str(self.dir))
        self.addCleanup(sys.path.remove, str(self.dir))
        counts, ok = gate.run_unittest("synthetic", name="synthetic_gate_xpass", discover=None, pattern="")
        self.assertFalse(ok)
        self.assertEqual(gate.evaluate(counts, SYNTHETIC_SPEC, None, [])[0], gate.FAIL)

    def test_missing_counts_file_fails(self):
        manifest = {"suites": {"pit-synthetic": dict(SYNTHETIC_SPEC, job="j")}}
        self.assertEqual(gate.compare(manifest, ["pit-synthetic"], self.dir), 1)


class XpassAndDeselectionTest(GateCase):
    """Regression: XPASS and unknown deselections used to be accepted as PASS."""

    def test_xpass_is_not_a_pass(self):
        outcomes = {i: "passed" for i in IDS[:8]} | {IDS[3]: "xpassed"}
        self.assertFails(self.root(ledger_doc(IDS, LISTED, outcomes)), "XPASS")

    def test_xfail_is_not_a_pass(self):
        outcomes = {i: "passed" for i in IDS[:8]} | {IDS[3]: "xfailed"}
        self.assertFails(self.root(ledger_doc(IDS, LISTED, outcomes)), "XFAIL")

    def test_580_collected_1_unknown_deselected_579_passed_fails(self):
        # The reported shape: the run collected 580, an ungoverned filter deselected
        # one, and the 579 that ran all passed, matching a 579 baseline row.
        ids = [f"backend/tests/test_b.py::test_{i}" for i in range(580)]
        baseline = BASELINE.replace("4 collected, 4 passed", "579 collected, 579 passed")
        counts = self.counts("backend", ledger_doc(ids, ids[:1]))
        self.assertEqual((counts["collected"], counts["deselected"], counts["passed"]), (580, 1, 579))
        self.assertFails(gate.evaluate(counts, BACKEND_SPEC, baseline, []), "not in the governed deselect list")

    def test_same_count_but_different_deselected_id_fails(self):
        swapped = [IDS[0], LISTED[1]]
        outcomes = {i: "passed" for i in IDS if i not in swapped}
        self.assertFails(self.root(ledger_doc(IDS, swapped, outcomes)), "not in the governed deselect list")

    def test_tests_dropped_without_a_deselect_record_fail(self):
        ledger = ledger_doc(IDS, LISTED)
        ledger["selected"] = ledger["selected"][1:]
        del ledger["outcomes"][IDS[0]]
        self.assertFails(self.root(ledger), "without a deselection record")

    def test_selected_test_without_an_outcome_fails(self):
        ledger = ledger_doc(IDS, LISTED)
        del ledger["outcomes"][IDS[0]]
        self.assertFails(self.root(ledger), "never reported")

    def test_nonzero_pytest_exit_or_collection_error_fails(self):
        self.assertFails(self.root(ledger_doc(IDS, LISTED, exitstatus=2)), "exit status")
        self.assertFails(self.root(ledger_doc(IDS, LISTED, collection_errors=1)), "collection error")


class MalformedReportTest(GateCase):
    """A report the gate cannot trust fails closed instead of passing or crashing."""

    def test_pytest_gate_without_ledger_fails_closed(self):
        junit_path = self.dir / "backend.xml"
        junit_path.write_text(junit_xml({f"backend/tests/test_b.py::test_{i}": "passed" for i in range(4)}))
        manifest_path = self.dir / "manifest.json"
        manifest_path.write_text(json.dumps({"suites": {"backend": dict(BACKEND_SPEC, job="j")}}))
        out = self.dir / "counts"
        gate.main(["--manifest", str(manifest_path), "junit", "--suite", "backend", "--junit", str(junit_path), "--out", str(out)])
        status, messages = gate.evaluate(json.loads((out / "backend.json").read_text()), BACKEND_SPEC, BASELINE, [])
        self.assertEqual(status, gate.FAIL)
        self.assertTrue(any("ledger" in m for m in messages), messages)

    def test_unparseable_reports_fail(self):
        ledger = ledger_doc(IDS, LISTED)
        self.assertFails(self.root(ledger, xml="<testsuites><testsuite"), "malformed")
        self.assertFails(self.root("{not json", xml=junit_xml(ledger["outcomes"])), "malformed")
        self.assertFails(self.root(dict(ledger, schema="other/9")), "malformed")
        self.assertFails(self.root(dict(ledger, outcomes={IDS[0]: "mostly-passed"})), "malformed")
        self.assertFails(self.root(dict(ledger, collected=IDS + IDS[:1])), "malformed")

    def test_ledger_and_junit_disagreeing_fails(self):
        ledger = ledger_doc(IDS, LISTED)
        failing_junit = junit_xml(ledger["outcomes"] | {IDS[0]: "failed"})
        self.assertFails(self.root(ledger, xml=failing_junit), "disagree")
        short_junit = junit_xml({i: "passed" for i in IDS[1:8]})
        self.assertFails(self.root(ledger, xml=short_junit), "disagree")

    def test_corrupt_or_mismatched_counts_file_fails_in_compare(self):
        manifest = {"suites": {"backend": dict(BACKEND_SPEC, job="j")}}
        (self.dir / "backend.json").write_text("{broken")
        self.assertEqual(gate.compare(manifest, ["backend"], self.dir), 1)
        good = self.counts("backend", ledger_doc([f"backend/tests/test_b.py::test_{i}" for i in range(4)]))
        for bad in (dict(good, suite="root-portable"), dict(good, passed="4"), dict(good, skipped=-1)):
            self.assertEqual(gate.evaluate(bad, BACKEND_SPEC, BASELINE, [], suite="backend")[0], gate.FAIL)
        self.assertEqual(gate.evaluate(good, BACKEND_SPEC, BASELINE, [], suite="backend")[0], gate.PASS)


class RealPytestTest(GateCase):
    """End to end: real pytest on invented suites, through the ledger plugin."""

    def run_pytest(self, files: dict[str, str], *args: str) -> tuple[Path, Path]:
        work = self.dir / "work"
        for rel, text in files.items():
            (work / rel).parent.mkdir(parents=True, exist_ok=True)
            (work / rel).write_text(text)
        junit_path, ledger_path = self.dir / "run.xml", self.dir / "run.ledger.json"
        env = dict(os.environ, PYTHONPATH=str(SCRIPTS), PYTHONDONTWRITEBYTECODE="1", CI_TEST_GATE_LEDGER=str(ledger_path))
        env.pop("PYTEST_ADDOPTS", None)
        subprocess.run(
            [sys.executable, "-B", "-m", "pytest", "suite", "-q", "-p", "no:cacheprovider",
             "-p", "ci_pytest_ledger", f"--junitxml={junit_path}", *args],
            cwd=work, env=env, capture_output=True, text=True, check=False,
        )
        return junit_path, ledger_path

    def evaluate_run(self, files, *args, approved: int, listed=()):
        junit_path, ledger_path = self.run_pytest(files, *args)
        counts = gate.counts_from_pytest("synthetic", junit_path, ledger_path, deselect_ids=list(listed))
        spec = {"runner": "pytest", "expected": {"approved_collected": approved, "source": "synthetic"}}
        return counts, gate.evaluate(counts, spec, None, list(listed))

    PLAIN = {"suite/test_plain.py": "def test_a(): pass\ndef test_b(): pass\ndef test_c(): pass\n"}

    def test_clean_run_passes(self):
        counts, result = self.evaluate_run(self.PLAIN, approved=3)
        self.assertEqual(result, (gate.PASS, []))
        self.assertEqual((counts["collected"], counts["executed"], counts["passed"]), (3, 3, 3))

    def test_real_non_strict_xpass_fails(self):
        files = {"suite/test_x.py": (
            "import pytest\n"
            "def test_a(): pass\n"
            "def test_b(): pass\n"
            "@pytest.mark.xfail(reason='synthetic')\n"
            "def test_c(): pass\n"
        )}
        counts, result = self.evaluate_run(files, approved=3)
        self.assertFails(result, "XPASS")
        self.assertEqual(counts["xpassed"], 1)

    def test_real_strict_xpass_and_xfail_fail(self):
        files = {"suite/test_x.py": (
            "import pytest\n"
            "def test_a(): pass\n"
            "@pytest.mark.xfail(reason='synthetic', strict=True)\n"
            "def test_b(): pass\n"
            "@pytest.mark.xfail(reason='synthetic')\n"
            "def test_c(): assert False\n"
        )}
        self.assertEqual(self.evaluate_run(files, approved=3)[1][0], gate.FAIL)

    def test_real_580_collected_one_deselected_579_passed_fails(self):
        files = {"suite/test_many.py": (
            "import pytest\n"
            "@pytest.mark.parametrize('n', range(580))\n"
            "def test_n(n): pass\n"
        )}
        counts, result = self.evaluate_run(files, "--deselect", "suite/test_many.py::test_n[0]", approved=579)
        self.assertEqual((counts["collected"], counts["deselected"], counts["passed"]), (580, 1, 579))
        self.assertFails(result, "not in the governed deselect list")

    def test_real_keyword_filter_and_hook_deselection_fail(self):
        self.assertFails(self.evaluate_run(self.PLAIN, "-k", "not test_b", approved=3)[1], "governed deselect")
        hooked = dict(self.PLAIN, **{"suite/conftest.py": (
            "def pytest_collection_modifyitems(config, items):\n"
            "    dropped = [i for i in items if i.name == 'test_b']\n"
            "    items[:] = [i for i in items if i.name != 'test_b']\n"
            "    config.hook.pytest_deselected(items=dropped)\n"
        )})
        self.assertFails(self.evaluate_run(hooked, approved=3)[1], "governed deselect")

    def test_real_silent_drop_without_deselect_hook_fails(self):
        dropping = dict(self.PLAIN, **{"suite/conftest.py": (
            "def pytest_collection_modifyitems(items):\n"
            "    items[:] = [i for i in items if i.name != 'test_b']\n"
        )})
        self.assertFails(self.evaluate_run(dropping, approved=3)[1], "without a deselection record")

    def test_real_governed_deselection_passes_only_for_the_exact_id(self):
        governed = ["suite/test_plain.py::test_b"]
        _, ok = self.evaluate_run(self.PLAIN, "--deselect", governed[0], approved=3, listed=governed)
        self.assertEqual(ok, (gate.PASS, []))
        _, wrong = self.evaluate_run(self.PLAIN, "--deselect", "suite/test_plain.py::test_c", approved=3, listed=governed)
        self.assertFails(wrong, "not in the governed deselect list")

    def test_plugin_refuses_to_run_without_a_ledger_path(self):
        work = self.dir / "work"
        (work / "suite").mkdir(parents=True)
        (work / "suite" / "test_plain.py").write_text(self.PLAIN["suite/test_plain.py"])
        env = dict(os.environ, PYTHONPATH=str(SCRIPTS), PYTHONDONTWRITEBYTECODE="1")
        env.pop("CI_TEST_GATE_LEDGER", None)
        done = subprocess.run(
            [sys.executable, "-B", "-m", "pytest", "suite", "-q", "-p", "no:cacheprovider", "-p", "ci_pytest_ledger"],
            cwd=work, env=env, capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(done.returncode, 0)


class WorkspaceTest(GateCase):
    def layout(self) -> Path:
        root = self.dir / "ws"
        (root / ".git").mkdir(parents=True)
        (root / ".git" / "HEAD").write_text("x")
        (root / "allowed").mkdir()
        (root / "allowed" / "f.py").write_text("x")
        (root / "docs").mkdir()
        (root / "docs" / "KEEP.md").write_text("x")
        self.forbidden = self.dir / "forbidden"
        self.forbidden.mkdir()
        (self.forbidden / "outcomes.csv").write_text("synthetic")
        return root

    ALLOWED = ["allowed/", "docs/KEEP.md"]

    def test_workspace_check_reports_paths_outside_scope(self):
        root = self.layout()
        (root / "data").mkdir()
        (root / "data" / "outcomes.csv").write_text("x")
        self.assertEqual(gate.check_workspace(root, self.ALLOWED), ["data/", "data/outcomes.csv"])

    def test_clean_workspace_passes(self):
        self.assertEqual(gate.check_workspace(self.layout(), self.ALLOWED), [])

    def test_directory_symlink_outside_scope_fails(self):
        root = self.layout()
        os.symlink(self.forbidden, root / "data")
        self.assertEqual(gate.check_workspace(root, self.ALLOWED), ["data (symlink)"])

    def test_symlink_inside_allowed_prefix_fails(self):
        root = self.layout()
        os.symlink(self.forbidden, root / "allowed" / "escape")
        os.symlink(self.forbidden / "outcomes.csv", root / "allowed" / "leak.csv")
        os.symlink(self.dir / "missing", root / "allowed" / "dangling")
        self.assertEqual(
            gate.check_workspace(root, self.ALLOWED),
            ["allowed/dangling (symlink)", "allowed/escape (symlink)", "allowed/leak.csv (symlink)"],
        )

    def test_symlinked_git_dir_and_special_files_fail(self):
        root = self.dir / "ws2"
        root.mkdir()
        os.symlink(self.layout() / ".git", root / ".git")
        (root / "allowed").mkdir()
        os.mkfifo(root / "allowed" / "pipe")
        self.assertEqual(gate.check_workspace(root, self.ALLOWED), [".git (symlink)", "allowed/pipe (not a regular file)"])

    def test_empty_directory_outside_scope_fails(self):
        root = self.layout()
        (root / "data" / "raw").mkdir(parents=True)
        self.assertEqual(gate.check_workspace(root, self.ALLOWED), ["data/", "data/raw/"])


if __name__ == "__main__":
    unittest.main()
