"""Synthetic-only tests, runnable without repository hooks or pytest plugins."""

import ast
import json
import multiprocessing
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from experiments.research_core import guard, ledger


def hold_lock(path, ready, release):
    with ledger._locked(Path(path), write=True):
        ready.set()
        release.wait(10)


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "synthetic.jsonl"

    def rewrite(self, record):
        self.path.write_bytes(ledger.canonical(record) + b"\n")

    def assert_rejected_unchanged(self, error):
        original = self.path.read_bytes()
        result = ledger.verify(self.path)
        self.assertFalse(result.valid)
        self.assertEqual(result.error, error)
        with self.assertRaises(ledger.LedgerError) as caught:
            ledger.append(self.path)
        self.assertEqual(caught.exception.code, error)
        self.assertEqual(original, self.path.read_bytes())

    def test_initial_and_subsequent_append(self):
        first = ledger.create(self.path, {"synthetic_label": "one"})
        prefix = self.path.read_bytes()
        second = ledger.append(self.path, {"synthetic_label": "two"})
        self.assertTrue(self.path.read_bytes().startswith(prefix))
        self.assertIsNone(first["previous_hash"])
        self.assertEqual(second["previous_hash"], first["hash"])
        self.assertNotEqual(first["event_id"], second["event_id"])
        self.assertTrue(first["recorded_at"].endswith("Z"))
        self.assertEqual(first["schema_version"], 1)
        self.assertEqual(ledger.verify(self.path), ledger.Verification(True, 2, second["hash"]))

    def test_deterministic_serialization(self):
        self.assertEqual(ledger.canonical({"b": None, "a": 1}), b'{"a":1,"b":null}')
        self.assertEqual(ledger.canonical({"a": 1, "b": None}), ledger.canonical({"b": None, "a": 1}))

    def test_missing_information_is_null(self):
        self.assertIsNone(ledger.create(self.path)["metadata"])
        record = ledger.append(self.path, {"unknown": None, "nested": {"unknown": None}})
        self.assertEqual(record["metadata"], {"unknown": None, "nested": {"unknown": None}})
        self.assertIn(b'"unknown":null', self.path.read_bytes())
        self.assertTrue(ledger.verify(self.path).valid)

    def test_modified_history_detected(self):
        ledger.create(self.path, {"label": "before"})
        ledger.append(self.path)
        self.path.write_bytes(self.path.read_bytes().replace(b"before", b"after!"))
        self.assert_rejected_unchanged("hash_mismatch")
        self.assertEqual(ledger.verify(self.path).line, 1)

    def test_broken_link_detected_even_with_rehashed_record(self):
        ledger.create(self.path)
        second = ledger.append(self.path)
        first_line = self.path.read_bytes().splitlines(keepends=True)[0]
        second["previous_hash"] = None
        second["hash"] = ledger._hash(second)
        self.path.write_bytes(first_line + ledger.canonical(second) + b"\n")
        self.assert_rejected_unchanged("broken_link")

    def test_missing_ledger_rejected_without_creation(self):
        self.assertEqual(ledger.verify(self.path).error, "missing_ledger")
        with self.assertRaises(ledger.LedgerError):
            ledger.append(self.path)
        self.assertFalse(self.path.exists())

    def test_empty_ledger_rejected(self):
        self.path.touch()
        self.assert_rejected_unchanged("empty_ledger")

    def test_corrupt_ledger_rejected(self):
        self.path.write_bytes(b"not-json\n")
        self.assert_rejected_unchanged("malformed_record")

    def test_truncated_tail_rejected_without_repair(self):
        ledger.create(self.path)
        ledger.append(self.path)
        self.path.write_bytes(self.path.read_bytes()[:-5])
        self.assert_rejected_unchanged("truncated_tail")

    def test_missing_final_newline_rejected(self):
        ledger.create(self.path)
        self.path.write_bytes(self.path.read_bytes()[:-1])
        self.assert_rejected_unchanged("truncated_tail")

    def test_unknown_schema_rejected(self):
        record = ledger.create(self.path)
        record["schema_version"] = 2
        record["hash"] = ledger._hash(record)
        self.rewrite(record)
        self.assert_rejected_unchanged("unknown_schema")

    def test_missing_envelope_field_rejected(self):
        record = ledger.create(self.path)
        del record["metadata"]
        self.rewrite(record)
        self.assert_rejected_unchanged("invalid_fields")

    def test_duplicate_id_rejected(self):
        first = ledger.create(self.path)
        second = ledger.append(self.path)
        prefix = self.path.read_bytes().splitlines(keepends=True)[0]
        second["event_id"] = first["event_id"]
        second["hash"] = ledger._hash(second)
        self.path.write_bytes(prefix + ledger.canonical(second) + b"\n")
        self.assert_rejected_unchanged("duplicate_event")

    def test_noncanonical_json_rejected(self):
        record = ledger.create(self.path)
        self.path.write_text(json.dumps(record) + "\n")
        self.assert_rejected_unchanged("noncanonical_record")

    def test_invalid_values_rejected_before_creation(self):
        for value in ({"value": float("nan")}, {"value": object()}, []):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises((TypeError, ValueError)):
                    ledger.create(self.path, value)
                self.assertFalse(self.path.exists())

    def test_create_never_overwrites(self):
        ledger.create(self.path)
        original = self.path.read_bytes()
        with self.assertRaises(ledger.LedgerError) as caught:
            ledger.create(self.path)
        self.assertEqual(caught.exception.code, "ledger_exists")
        self.assertEqual(self.path.read_bytes(), original)

    def test_concurrent_access_explicitly_rejected(self):
        ledger.create(self.path)
        original = self.path.read_bytes()
        ctx = multiprocessing.get_context("spawn")
        ready, release = ctx.Event(), ctx.Event()
        process = ctx.Process(target=hold_lock, args=(str(self.path), ready, release))
        process.start()
        try:
            self.assertTrue(ready.wait(10), "child did not obtain lock")
            with self.assertRaises(ledger.LedgerError) as caught:
                ledger.append(self.path)
            self.assertEqual(caught.exception.code, "ledger_busy")
            self.assertEqual(ledger.verify(self.path).error, "ledger_busy")
            self.assertEqual(self.path.read_bytes(), original)
        finally:
            release.set()
            process.join(10)
            if process.is_alive():
                process.terminate()
                process.join()
        self.assertEqual(process.exitcode, 0)
        ledger.append(self.path)
        self.assertEqual(ledger.verify(self.path).count, 2)

    def test_unsupported_locking_denies_operations(self):
        with patch.object(ledger, "fcntl", None):
            self.assertEqual(ledger.verify(self.path).error, "locking_unsupported")
            with self.assertRaises(ledger.LedgerError):
                ledger.create(self.path)
        self.assertFalse(self.path.exists())

    def test_symlink_rejected(self):
        target = Path(self.temp.name) / "target.jsonl"
        ledger.create(target)
        original = target.read_bytes()
        self.path.symlink_to(target)
        self.assert_rejected_unchanged("open_failed")
        self.assertEqual(target.read_bytes(), original)

    def test_guard_denies_all_requests_without_inspecting_them(self):
        class Untouchable:
            def __str__(self):
                raise AssertionError("argument inspected")

        for kwargs in ({}, {"study_id": "synthetic", "registered": True},
                       {"policy": lambda: True}, {"adopted": True, "configured": True}):
            with self.subTest(kwargs=tuple(kwargs)):
                with self.assertRaises(guard.ProtectedAccessDenied):
                    guard.require_protected_access(Untouchable(), **kwargs)

    def test_no_legacy_experiment_import_or_activation(self):
        # A fresh interpreter imports the core and uses it with only synthetic metadata.
        code = """
import sys, tempfile
from pathlib import Path
before = set(sys.modules)
from experiments.research_core import ledger, guard
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / 'synthetic.jsonl'
    ledger.create(path)
    ledger.append(path)
    assert ledger.verify(path).valid
    try:
        guard.require_protected_access()
    except guard.ProtectedAccessDenied:
        pass
    else:
        raise AssertionError('access allowed')
allowed = {'experiments', 'experiments.research_core',
           'experiments.research_core.ledger', 'experiments.research_core.guard'}
assert not {name for name in set(sys.modules) - before
            if name.startswith('experiments') and name not in allowed}
"""
        subprocess.run([sys.executable, "-B", "-c", code], check=True, timeout=20)
        # The guard stays standalone: no imports and no resource-access calls.
        tree = ast.parse(Path(guard.__file__).read_text())
        self.assertFalse(any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(tree)))
        self.assertEqual({n.func.id for n in ast.walk(tree)
                          if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)},
                         {"ProtectedAccessDenied"})


if __name__ == "__main__":
    unittest.main()
