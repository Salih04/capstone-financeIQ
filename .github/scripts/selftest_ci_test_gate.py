"""Self-test for ci_test_gate.py: every weaker-gate shape must fail closed.

Uses only invented JUnit/baseline strings in temporary directories; it reads no
repository data. Run: python -B .github/scripts/selftest_ci_test_gate.py -v
"""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ci_test_gate as gate  # noqa: E402

BASELINE = (
    "| `PYTHONPATH=. python -m pytest tests/` | PASS — 10 collected, 10 passed |\n"
    "| `PYTHONPATH=backend python -m pytest backend/tests` | PASS — 4 collected, 4 passed (1 warning) |\n"
)
ROOT_SPEC = {"expected": {"from_baseline": "PYTHONPATH=. python -m pytest tests/"}, "deselect_list": "x"}
BACKEND_SPEC = {"expected": {"from_baseline": "PYTHONPATH=backend python -m pytest backend/tests"}}
SYNTHETIC_SPEC = {"expected": {"approved_collected": 3, "source": "approval record"}}
LISTED = ["tests/test_a.py::test_env_1", "tests/test_a.py::test_env_2"]
IDS = [f"tests/test_a.py::test_{i}" for i in range(8)] + LISTED


def junit_xml(tests: int, failures: int = 0, errors: int = 0, skipped: int = 0) -> str:
    return (
        '<?xml version="1.0"?><testsuites><testsuite name="pytest" '
        f'tests="{tests}" failures="{failures}" errors="{errors}" skipped="{skipped}"/></testsuites>'
    )


class GateTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)

    def junit(self, suite: str, xml: str, *, ids=None, deselect=None) -> dict:
        path = self.dir / f"{suite}.xml"
        path.write_text(xml)
        return gate.counts_from_junit(suite, path, collected_ids=ids, deselect_ids=deselect)

    def root(self, xml: str, *, ids=IDS, deselect=LISTED, listed=LISTED, baseline=BASELINE):
        counts = self.junit("root-portable", xml, ids=ids, deselect=deselect)
        return gate.evaluate(counts, ROOT_SPEC, baseline, listed)

    def test_exact_portable_run_passes(self):
        self.assertEqual(self.root(junit_xml(8)), (gate.PASS, []))

    def test_backend_and_synthetic_exact_runs_pass(self):
        backend = self.junit("backend", junit_xml(4))
        self.assertEqual(gate.evaluate(backend, BACKEND_SPEC, BASELINE, [])[0], gate.PASS)
        synthetic = dict(backend, collected=3, executed=3, passed=3)
        self.assertEqual(gate.evaluate(synthetic, SYNTHETIC_SPEC, None, [])[0], gate.PASS)

    def test_any_skip_fails(self):
        status, messages = self.root(junit_xml(8, skipped=1))
        self.assertEqual(status, gate.FAIL)
        self.assertTrue(any("skipped" in m for m in messages))

    def test_failures_and_errors_fail(self):
        self.assertEqual(self.root(junit_xml(8, failures=1))[0], gate.FAIL)
        self.assertEqual(self.root(junit_xml(8, errors=1))[0], gate.FAIL)

    def test_extra_filter_that_drops_tests_fails(self):
        # e.g. an added -k/--deselect: collect-only still sees ten, the run accounts for fewer.
        status, messages = self.root(junit_xml(7))
        self.assertEqual(status, gate.FAIL)
        self.assertTrue(any("collect-only" in m for m in messages))

    def test_shrunken_collection_fails(self):
        status, messages = self.root(junit_xml(6), ids=IDS[2:])
        self.assertEqual(status, gate.FAIL)
        self.assertTrue(any("below the approved" in m for m in messages))

    def test_grown_collection_warns_without_rewriting(self):
        ids = IDS + ["tests/test_a.py::test_new"]
        self.assertEqual(self.root(junit_xml(9), ids=ids)[0], gate.WARN)

    def test_stale_deselect_id_fails(self):
        ids = IDS[:-1] + ["tests/test_a.py::test_8"]
        status, messages = self.root(junit_xml(9), ids=ids)
        self.assertEqual(status, gate.FAIL)
        self.assertTrue(any("no longer collected" in m for m in messages))

    def test_unexpected_deselection_fails(self):
        counts = self.junit("backend", junit_xml(3), deselect=["backend/tests/test_x.py::test_y"])
        status, messages = gate.evaluate(counts, BACKEND_SPEC, BASELINE, [])
        self.assertEqual(status, gate.FAIL)
        self.assertTrue(any("deselected" in m for m in messages))

    def test_unparseable_or_partial_baseline_fails_closed(self):
        self.assertEqual(self.root(junit_xml(8), baseline="no table here")[0], gate.FAIL)
        self.assertEqual(self.root(junit_xml(8), baseline=None)[0], gate.FAIL)
        partial = BASELINE.replace("10 collected, 10 passed", "10 collected, 9 passed")
        self.assertEqual(self.root(junit_xml(8), baseline=partial)[0], gate.FAIL)
        duplicated = BASELINE + BASELINE
        self.assertEqual(self.root(junit_xml(8), baseline=duplicated)[0], gate.FAIL)

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

    def test_missing_counts_file_fails(self):
        manifest = {"suites": {"pit-synthetic": dict(SYNTHETIC_SPEC, job="j")}}
        self.assertEqual(gate.compare(manifest, ["pit-synthetic"], self.dir), 1)

    def test_workspace_check_reports_paths_outside_scope(self):
        (self.dir / ".git").mkdir()
        (self.dir / ".git" / "HEAD").write_text("x")
        (self.dir / "allowed").mkdir()
        (self.dir / "allowed" / "f.py").write_text("x")
        (self.dir / "data").mkdir()
        (self.dir / "data" / "outcomes.csv").write_text("x")
        self.assertEqual(gate.check_workspace(self.dir, ["allowed/"]), ["data/outcomes.csv"])


if __name__ == "__main__":
    unittest.main()
