"""Authorized synthetic transport tests; no data, guard or experiment imports."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.pit.kernel_snapshot import (
    ContractUnverified, SnapshotRejected, open_snapshot,
    read_verified_file, validate_contract_version, _validate_envelope, _canonical, DIMENSION_KEY,
)


class SnapshotSafeguardsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.payload = b'{"known_at":"2000-01-01T00:00:00Z","entity_id":"synthetic-old","value":null}'
        (self.root / "facts.json").write_bytes(self.payload)
        self.digest = hashlib.sha256(self.payload).hexdigest()

    def read(self, reference="facts.json", **kwargs):
        return read_verified_file(self.root, reference, self.digest,
                                  algorithm="sha256", **kwargs)

    def test_exact_bytes_preserve_null_timestamp_and_historical_id(self):
        self.assertEqual(self.read(), self.payload)
        self.assertIsNone(json.loads(self.read())["value"])

    def test_nested_file(self):
        (self.root / "nested").mkdir()
        (self.root / "facts.json").rename(self.root / "nested/facts.json")
        self.assertEqual(self.read("nested/facts.json"), self.payload)

    def test_corruption(self):
        (self.root / "facts.json").write_bytes(self.payload + b" ")
        with self.assertRaisesRegex(SnapshotRejected, "hash mismatch"):
            self.read()

    def test_missing_and_unsafe_references(self):
        for reference in ("missing", "", "/facts.json", "../facts.json", "a/../facts.json",
                          "./facts.json", "a//b", "a/", "a\\b", "https://host/file", "a\x00b"):
            with self.subTest(reference=reference), self.assertRaises(SnapshotRejected):
                self.read(reference)

    def test_symlink_file_directory_and_root(self):
        (self.root / "link").symlink_to(self.root / "facts.json")
        (self.root / "alias").symlink_to(self.root, target_is_directory=True)
        for reference in ("link", "alias/facts.json"):
            with self.subTest(reference=reference), self.assertRaises(SnapshotRejected):
                self.read(reference)
        with self.assertRaises(SnapshotRejected):
            read_verified_file(self.root / "alias", "facts.json", self.digest, algorithm="sha256")

    def test_nonregular_and_hardlinked_files(self):
        os.mkfifo(self.root / "pipe")
        os.link(self.root / "facts.json", self.root / "hardlink")
        for reference in ("pipe", "hardlink", "facts.json"):
            with self.subTest(reference=reference), self.assertRaises(SnapshotRejected):
                self.read(reference)

    def test_hash_policy_and_bounds(self):
        for algorithm, digest in (("md5", self.digest), ("SHA256", self.digest),
                                  ("sha256", "bad"), ("sha256", self.digest.upper())):
            with self.subTest(algorithm=algorithm, digest=digest), self.assertRaises(SnapshotRejected):
                read_verified_file(self.root, "facts.json", digest, algorithm=algorithm)
        for limit in (1, 0, -1, True):
            with self.subTest(limit=limit), self.assertRaises(SnapshotRejected):
                self.read(max_bytes=limit)

    def test_read_only(self):
        before = (self.root / "facts.json").stat()
        real_open = os.open
        modes = []

        def observe(*args, **kwargs):
            modes.append(args[1])
            return real_open(*args, **kwargs)

        with patch("os.open", side_effect=observe) as observed:
            with patch("os.supports_dir_fd", {observed}):
                self.assertEqual(self.read(), self.payload)
        self.assertTrue(modes)
        for mode in modes:
            self.assertEqual(mode & os.O_ACCMODE, os.O_RDONLY)
            self.assertFalse(mode & (os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        self.assertEqual((self.root / "facts.json").read_bytes(), self.payload)
        self.assertEqual((self.root / "facts.json").stat().st_mtime_ns, before.st_mtime_ns)
        self.assertEqual(list(self.root.iterdir()), [self.root / "facts.json"])

    def test_versions_and_config_fail_closed_without_io(self):
        with patch("os.open", side_effect=AssertionError("unexpected IO")):
            self.assertIsNone(open_snapshot())
            validate_contract_version("4.0.0")
            for value in ("", "2.0.0", "3.0.0", "4.1.0", "999.0.0", None):
                with self.subTest(version=value), self.assertRaises(ContractUnverified):
                    validate_contract_version(value)
            for directory in ("", self.root, "missing"):
                with self.subTest(directory=directory), self.assertRaises(ContractUnverified):
                    open_snapshot(directory)


FIXTURES = Path(__file__).resolve().parents[2] / "tests/fixtures/kernel/contract_v4"


class SyntheticContractTest(unittest.TestCase):
    def setUp(self):
        self.envelope = json.loads((FIXTURES / "expected_snapshot.json").read_bytes())
        self.request = json.loads((FIXTURES / "request.json").read_bytes())

    def validate(self, mutate=None, *, rehash=True):
        import copy
        envelope = copy.deepcopy(self.envelope)
        if mutate:
            mutate(envelope)
        if rehash:
            envelope["content_hash"] = hashlib.sha256(_canonical({
                n: envelope[n] for n in ("contract_version", "dimension_key", "facts")
            })).hexdigest()
        return _validate_envelope(_canonical(envelope), self.request)

    def test_manifest_pins_all_copied_bytes(self):
        base = FIXTURES.parents[3]
        manifest = FIXTURES.parent / "SHA256_MANIFEST.txt"
        self.assertEqual(hashlib.sha256(manifest.read_bytes()).hexdigest(),
                         "fc0cf0c8c1b230a8f06a7e989ecd9dbad6e208064321ac08ccadec2169be185d")
        checked = 0
        for line in manifest.read_text().splitlines():
            if line.startswith("#") or not line:
                continue
            digest, size, blob, package, _, _ = line.split("\t")
            if package.startswith("fixtures/"):
                path = FIXTURES / Path(package).name
            elif package.startswith("schemas/"):
                path = base / "experiments/pit/contract_v4" / Path(package).name
            else:
                continue
            payload = path.read_bytes()
            self.assertEqual(len(payload), int(size))
            self.assertEqual(hashlib.sha256(payload).hexdigest(), digest)
            self.assertEqual(hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest(), blob)
            checked += 1
        self.assertEqual(checked, 12)

    def test_three_approved_pairs_and_canonical_hashes(self):
        digests = json.loads((FIXTURES / "digests.json").read_bytes())
        for filename, request_name, count in (
            ("expected_snapshot.json", "request.json", 5),
            ("expected_pre_annual_snapshot.json", "pre_annual_request.json", 3),
            ("expected_empty_snapshot.json", "empty_request.json", 0),
        ):
            with self.subTest(filename=filename):
                request = json.loads((FIXTURES / request_name).read_bytes())
                for name in (filename, digests["snapshots"][filename]["canonical_bytes_file"]):
                    payload = (FIXTURES / name).read_bytes()
                    snapshot = open_snapshot(FIXTURES, reference=name,
                                             expected_digest=hashlib.sha256(payload).hexdigest(), request=request)
                    canonical = snapshot.canonical_bytes
                    self.assertEqual(canonical, (FIXTURES / digests["snapshots"][filename]["canonical_bytes_file"]).read_bytes())
                    self.assertEqual(len(json.loads(canonical)["facts"]), count)
                    self.assertEqual(hashlib.sha256(canonical).hexdigest(),
                                     digests["snapshots"][filename]["canonical_bytes_sha256"])
                    self.assertEqual(json.loads(canonical)["content_hash"], digests["snapshots"][filename]["content_hash"])

    def test_existing_guard_uses_upper_bound_and_full_key(self):
        from experiments.pit.guard import PointInTimeViolation
        payload = (FIXTURES / "expected_snapshot.json").read_bytes()
        snapshot = open_snapshot(FIXTURES, reference="expected_snapshot.json",
                                 expected_digest=hashlib.sha256(payload).hexdigest(), request=self.request)
        source = self.envelope["facts"][3]  # DATE_ONLY
        key = {n: source[n] for n in DIMENSION_KEY}
        with self.assertRaises(PointInTimeViolation):
            snapshot.fact(key, prediction_time="2024-11-08T20:59:59Z")
        returned = snapshot.fact(key, prediction_time=source["known_at_upper"])
        self.assertEqual(returned, source)
        returned["value"] = "changed"
        self.assertEqual(snapshot.fact(key, prediction_time=source["known_at_upper"]), source)
        with self.assertRaises(SnapshotRejected):
            snapshot.fact({"entity_id": "SYN-ENTITY-1"}, prediction_time=source["known_at_upper"])
        absent = dict(key, security_id="SYN-ABSENT")
        with self.assertRaises(SnapshotRejected):
            snapshot.fact(absent, prediction_time=source["known_at_upper"])
        empty_payload = (FIXTURES / "expected_empty_snapshot.json").read_bytes()
        empty = open_snapshot(FIXTURES, reference="expected_empty_snapshot.json",
                              expected_digest=hashlib.sha256(empty_payload).hexdigest(),
                              request=json.loads((FIXTURES / "empty_request.json").read_bytes()))
        self.assertIsNone(empty.fact(key, prediction_time=source["known_at_upper"]))
        original_request = snapshot.request
        original_request["dimension_keys"].clear()
        self.assertTrue(snapshot.request["dimension_keys"])
        historical = {n: self.envelope["facts"][0][n] for n in DIMENSION_KEY}
        restated = dict(historical, accounting_basis="IAS29_RESTATED")
        self.assertNotEqual(snapshot.fact(historical, prediction_time=self.request["as_of"])["fact_version_id"],
                            snapshot.fact(restated, prediction_time=self.request["as_of"])["fact_version_id"])
        self.assertIsNone(snapshot.fact(historical, prediction_time=self.request["as_of"])["measuring_unit_date"])

    def test_rehashed_schema_and_temporal_attacks(self):
        cases = [
            lambda e: e.update(contract_version="999.0.0"),
            lambda e: e.update(hash_algorithm="sha256:financeiq-pit-snapshot-v999"),
            lambda e: e.update(outcome="forbidden"),
            lambda e: e["facts"][0].update(outcome="forbidden"),
            lambda e: e["facts"][0].pop("measuring_unit_date"),
            lambda e: e["facts"][0].update(measuring_unit_date="2024-01-01"),
            lambda e: e["facts"][1].update(measuring_unit_date="2025-02-30"),
            lambda e: e["facts"][0].update(currency="USD\n"),
            lambda e: e["facts"][0].update(value=None),
            lambda e: e["facts"][0].update(value_type="INTEGER", value=True),
            lambda e: e["facts"][0].update(value="NaN"),
            lambda e: e["facts"][0].update(known_at_upper=None),
            lambda e: e["facts"][0].update(known_at_precision="UNKNOWN"),
            lambda e: e["facts"][0].update(known_at_lower="2026-04-02T00:00:00Z"),
            lambda e: e["facts"][0].update(known_at_upper="2026-04-02T00:00:00Z"),
            lambda e: e["facts"][0].update(known_at_upper="2025-03-07T16:00:00.0000001Z"),
            lambda e: e["facts"][0].update(valid_to="2024-01-01T00:00:00Z"),
            lambda e: e["facts"][0].update(recorded_at="2026-04-02T00:00:00Z"),
            lambda e: e["facts"][3].update(publication_timezone=None),
            lambda e: e["facts"][3].update(publication_timezone="UTC"),
            lambda e: e["facts"][0].update(field="return"),
            lambda e: e["facts"][0].update(extraction_method="PARSER"),
            lambda e: e["facts"].append(e["facts"][0]),
            lambda e: e["facts"].reverse(),
            lambda e: e["dimension_key"].reverse(),
            lambda e: e.update(as_of="2026-04-01T00:00:00Z"),
        ]
        for i, mutate in enumerate(cases):
            with self.subTest(case=i), self.assertRaises(SnapshotRejected):
                self.validate(mutate)
        with self.assertRaisesRegex(SnapshotRejected, "content hash"):
            self.validate(lambda e: e["facts"][0].update(value="4501"), rehash=False)

    def test_request_binding_and_json_ambiguity(self):
        for name in ("as_of", "valid_at", "system_as_of"):
            request = dict(self.request, **{name: "2000-01-01T00:00:00Z"})
            with self.subTest(name=name), self.assertRaises(SnapshotRejected):
                _validate_envelope(_canonical(self.envelope), request)
        with self.assertRaises(SnapshotRejected):
            _validate_envelope(b'{"contract_version":"4.0.0","contract_version":"4.0.0"}', self.request)
        with self.assertRaises(SnapshotRejected):
            _validate_envelope(b'{"bad":NaN}', self.request)
        with self.assertRaises(SnapshotRejected):
            _validate_envelope(_canonical(self.envelope), dict(self.request, dimension_keys=[{"entity_id":"x"}]))

    def test_configured_corruption_never_falls_back(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            source = (FIXTURES / "expected_snapshot.json").read_bytes()
            (root / "snapshot.json").write_bytes(source + b" ")
            with self.assertRaisesRegex(SnapshotRejected, "hash mismatch"):
                open_snapshot(root, reference="snapshot.json", expected_digest=hashlib.sha256(source).hexdigest(), request=self.request)
        with patch("os.open", side_effect=AssertionError("unexpected IO")):
            with self.assertRaises(ContractUnverified):
                open_snapshot("real-export", reference="snapshot.json", expected_digest="0" * 64, request=self.request)

    def test_unconfigured_legacy_sources_and_synthetic_output_byte_identical(self):
        from experiments.pit import config, panel
        legacy_hashes = {
            "__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "config.py": "7b1733351408e66d3c6dadb5c7b9098f00e3db75737db5673699a4483b4d870c",
            "guard.py": "f22882c2494b6eb0a6489d37d8a14a21d38644ebfb3a796c2a39d1d1cda3d4f5",
            "panel.py": "17df492aeee73a8bef391208eafc06608f6e7bb052b0db8425ed2317fdb08be8",
            "prices.py": "db12b32d4c1a178ecd905b4e35a0ed7e617a212126cef0346fcea62f30f9bc67",
        }
        for name, digest in legacy_hashes.items():
            self.assertEqual(hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest(), digest)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            deadlines = root / "deadlines.csv"
            filings = root / "filings.csv"
            deadlines.write_text("ticker,fiscal_year,solo_deadline,consolidated_deadline\nSYN,2000,2001-02-01,2001-03-01\n")
            filings.write_text("ticker,fiscal_year,public_on_or_before\nSYN,2000,2001-02-02\n")
            with patch.object(config, "DEADLINES_PATH", deadlines), patch.object(config, "FILING_SAMPLE_PATH", filings):
                for mode, expected in ((config.STANDARDIZED_CUTOFF_MODE, b'[["SYN",2000,"2001-03-01T23:59:59"]]'),
                                       (config.ACTUAL_FILING_DATE_MODE, b'[["SYN",2000,"2001-02-02T23:59:59"]]')):
                    before = _canonical([[t,y,v.isoformat()] for (t,y),v in panel.statement_availability(mode).items()])
                    with patch("os.open", side_effect=AssertionError("unexpected IO")):
                        self.assertIsNone(open_snapshot(None))
                    after = _canonical([[t,y,v.isoformat()] for (t,y),v in panel.statement_availability(mode).items()])
                    self.assertEqual(before, expected)
                    self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
