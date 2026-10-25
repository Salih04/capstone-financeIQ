"""Owner-approved E-1 filing-facts-only synthetic consumer; never a real exporter.

Pinned Kernel 4.0.0 / d7668217183220744f391bc5ae9fa25493aca8ce.
The b2200441 descriptor-relative byte verifier is preserved unchanged.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from pathlib import Path
import re
import stat


class SnapshotRejected(ValueError):
    """Snapshot or file cannot be safely accepted."""


class ContractUnverified(SnapshotRejected):
    """An approved exchange specification is required before consumption."""


CONTRACT_VERSION = "4.0.0"
HASH_ALGORITHM = "sha256:financeiq-pit-snapshot-v4"
DIMENSION_KEY = ("entity_id", "security_id", "field", "period_type", "period_basis",
                 "currency", "unit", "scale", "consolidation", "accounting_basis")
# Approved E-1 invented envelopes only. No arbitrary/real export can be enabled.
APPROVED_BYTES = frozenset({
    "db68071269e61e8b7eac3d1fa1e66eeefc8afd5bc51134786f645b0c948317bb",
    "ce151089c873355b840eda42177e99d2052f52bfc2e55a92892659b2bf1c71a6",
    "56403cfa3b89f2445f2c3166e944827f9122dd6a2b3d284c79631ec6ad6c6ef7",
    "6575b45303e97c2e853ea990a43495aed6dfb1006fd86836e15cc7ff1959d152",
    "d781510c82a81e41c92c01ce4b67cc5ca06e9cd672df309c59ff01494c5671c3",
    "8b9a77ad6c1a56d1c3e7eb08b4c51d28131c07bbf221423b0fc80cfe75f671cb",
})


def validate_contract_version(version: str) -> None:
    """Pin exact reviewed semantics; future minors need their own evidence."""
    if version != CONTRACT_VERSION:
        raise ContractUnverified("unsupported Kernel contract version")


def _json(payload: bytes) -> dict:
    import json

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise SnapshotRejected("duplicate JSON key")
            result[key] = value
        return result

    def nonfinite(value):
        raise SnapshotRejected("non-finite JSON value")

    try:
        return json.loads(payload, object_pairs_hook=pairs, parse_constant=nonfinite)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise SnapshotRejected("invalid snapshot JSON") from exc


def _canonical(value) -> bytes:
    import json
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _instant(value: str):
    from datetime import datetime
    grammar = (r"[0-9]{4}-[0-9]{2}-[0-9]{2}T([01][0-9]|2[0-3]):[0-5][0-9]:"
               r"[0-5][0-9](\.[0-9]{1,6})?(Z|[+-](0[0-9]|1[0-5]):[0-5][0-9])")
    if not isinstance(value, str) or not re.fullmatch(grammar, value):
        raise SnapshotRejected("invalid Kernel instant")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SnapshotRejected("invalid calendar instant") from exc


def _validate_envelope(payload: bytes, request: dict) -> dict:
    """Schema + cross-field checks; internal, never a real-export entry point."""
    from datetime import datetime, time, timedelta, timezone
    from decimal import Decimal, InvalidOperation
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    try:
        from jsonschema import Draft202012Validator, ValidationError
    except ImportError as exc:
        raise ContractUnverified("install requirements-synthetic.txt first") from exc

    envelope = _json(payload)
    if not isinstance(envelope, dict):
        raise SnapshotRejected("expected envelope object")
    validate_contract_version(envelope.get("contract_version"))
    if envelope.get("hash_algorithm") != HASH_ALGORITHM:
        raise SnapshotRejected("unsupported snapshot hash algorithm")
    schema_bytes = read_verified_file(
        Path(__file__).parent, "contract_v4/snapshot_envelope_v4.schema.json",
        "a7a2805670a0042d49e366a05e49c875c783db2bbd94314882fca30d972598da",
        algorithm="sha256")
    try:
        Draft202012Validator(_json(schema_bytes)).validate(envelope)
    except ValidationError as exc:
        raise SnapshotRejected("snapshot schema violation") from exc
    if not isinstance(request, dict) or set(request) != {
        "contract_version", "dimension_keys", "as_of", "valid_at", "system_as_of"
    }:
        raise SnapshotRejected("complete external request required")
    validate_contract_version(request["contract_version"])
    times = {}
    for name in ("as_of", "valid_at", "system_as_of"):
        value = envelope[name]
        if not value.endswith("Z"):
            raise SnapshotRejected("envelope query coordinates must be UTC")
        times[name] = _instant(value)
        if times[name] != _instant(request[name]):
            raise SnapshotRejected("request coordinate mismatch")
    keys = request["dimension_keys"]
    if not isinstance(keys, list) or not keys:
        raise SnapshotRejected("nonempty complete dimension keys required")
    requested = set()
    for key in keys:
        if not isinstance(key, dict) or set(key) != set(DIMENSION_KEY) or any(
            not isinstance(v, str) or not v for v in key.values()
        ):
            raise SnapshotRejected("partial dimension key")
        coordinate = tuple(key[n] for n in DIMENSION_KEY)
        if coordinate in requested:
            raise SnapshotRejected("duplicate requested dimension key")
        requested.add(coordinate)
    seen = set()
    ids = []
    for fact in envelope["facts"]:
        # A synthetic-only boundary, not a rights clearance mechanism.
        if (fact["extraction_method"] != "SYNTHETIC" or
                fact["entity_id"] != "SYN-ENTITY-1" or fact["field"] != "invented_sales"):
            raise SnapshotRejected("only approved invented filing facts allowed")
        coordinate = tuple(fact[n] for n in DIMENSION_KEY)
        if coordinate not in requested or coordinate in seen:
            raise SnapshotRejected("unrequested or duplicate dimension key")
        seen.add(coordinate)
        ids.append(fact["fact_version_id"])
        start = _instant(fact["valid_from"])
        end = _instant(fact["valid_to"]) if fact.get("valid_to") is not None else None
        if end is not None and end <= start:
            raise SnapshotRejected("invalid valid interval")
        if not (start <= times["valid_at"] and (end is None or times["valid_at"] < end)):
            raise SnapshotRejected("fact outside valid_at")
        lo, hi = fact["known_at_lower"], fact["known_at_upper"]
        if lo is None or hi is None or fact["known_at_precision"] == "UNKNOWN":
            raise SnapshotRejected("unknown publication bounds are not eligible")
        lo, hi = _instant(lo), _instant(hi)
        if lo > hi or hi > times["as_of"]:
            raise SnapshotRejected("publication bounds exceed as_of")
        if fact["known_at_precision"] == "EXACT_TIMESTAMP" and lo != hi:
            raise SnapshotRejected("exact publication needs equal bounds")
        if fact["known_at_precision"] in ("DATE_ONLY", "INTERVAL") and lo >= hi:
            raise SnapshotRejected("publication interval must be nonempty")
        if fact["known_at_precision"] == "DATE_ONLY":
            try:
                zone = ZoneInfo(fact.get("publication_timezone"))
                local_day = lo.astimezone(zone).date()
                a = datetime.combine(local_day, time(), zone).astimezone(timezone.utc)
                b = datetime.combine(local_day + timedelta(days=1), time(), zone).astimezone(timezone.utc)
            except (TypeError, ValueError, ZoneInfoNotFoundError) as exc:
                raise SnapshotRejected("invalid publication timezone") from exc
            if (lo, hi) != (a, b):
                raise SnapshotRejected("DATE_ONLY needs conservative local-day bounds")
        if _instant(fact["recorded_at"]) > times["system_as_of"]:
            raise SnapshotRejected("recorded_at exceeds system_as_of")
        if fact["measuring_unit_date"] is not None:
            try:
                datetime.strptime(fact["measuring_unit_date"], "%Y-%m-%d")
            except ValueError as exc:
                raise SnapshotRejected("invalid measuring-unit date") from exc
        value, kind = fact["value"], fact["value_type"]
        if kind == "DECIMAL_STRING":
            try:
                if not isinstance(value, str) or not re.fullmatch(r"-?[0-9]+(\.[0-9]+)?", value) or not Decimal(value).is_finite():
                    raise InvalidOperation
            except InvalidOperation as exc:
                raise SnapshotRejected("invalid decimal string") from exc
        elif type(value) is not {"INTEGER": int, "BOOLEAN": bool, "STRING": str}[kind]:
            raise SnapshotRejected("value_type mismatch")
    if ids != sorted(set(ids)):
        raise SnapshotRejected("fact IDs must be unique and sorted")
    hashed = {name: envelope[name] for name in ("contract_version", "dimension_key", "facts")}
    if not hmac.compare_digest(hashlib.sha256(_canonical(hashed)).hexdigest(), envelope["content_hash"]):
        raise SnapshotRejected("snapshot content hash mismatch")
    return envelope


class SyntheticSnapshot:
    """Retain verified bytes; fact access uses the existing PIT guard and full key."""
    def __init__(self, payload: bytes, request: dict):
        if hashlib.sha256(payload).hexdigest() not in APPROVED_BYTES:
            raise ContractUnverified("only pinned approved synthetic bytes are enabled")
        _validate_envelope(payload, request)
        self._payload = payload
        self._request = _canonical(request)

    @property
    def request(self) -> dict:
        return _json(self._request)

    @property
    def canonical_bytes(self) -> bytes:
        return _canonical(_json(self._payload))

    def fact(self, key: dict[str, str], *, prediction_time: str) -> dict | None:
        import pandas as pd
        from experiments.pit.guard import assert_point_in_time
        if not isinstance(key, dict) or set(key) != set(DIMENSION_KEY):
            raise SnapshotRejected("full dimension key required")
        if key not in self.request["dimension_keys"]:
            raise SnapshotRejected("dimension key was not requested")
        prediction = _instant(prediction_time)
        for fact in _json(self._payload)["facts"]:
            if all(fact[name] == key[name] for name in DIMENSION_KEY):
                # Use the conservative upper bound, never the lower bound.
                assert_point_in_time(
                    pd.DataFrame({"prediction_time": [pd.Timestamp(prediction)], "fact": [fact["value"]]}),
                    pd.DataFrame({"fact": [pd.Timestamp(_instant(fact["known_at_upper"]))]}),
                    ["fact"],
                )
                return fact  # Fresh parse: caller mutations never affect the snapshot.
        return None


def open_snapshot(directory: str | Path | None = None, *, reference: str = "",
                  expected_digest: str = "", request: dict | None = None) -> SyntheticSnapshot | None:
    """Explicit config only; None retains legacy, configured errors never fall back.

    File digest must come from the approved E-1 manifest, not from that file.
    Only its six pretty/canonical invented envelopes are enabled. No env lookup,
    discovery, network, exporter, identifier inference or real-data capability.
    """
    if directory is None:
        return None
    if not isinstance(expected_digest, str) or expected_digest not in APPROVED_BYTES:
        raise ContractUnverified("only pinned approved synthetic bytes are enabled")
    payload = read_verified_file(directory, reference, expected_digest, algorithm="sha256")
    return SyntheticSnapshot(payload, request)


def read_verified_file(
    root: str | Path,
    reference: str,
    expected_digest: str,
    *,
    algorithm: str,
    max_bytes: int = 16 * 1024 * 1024,
) -> bytes:
    """Read bounded bytes beneath root using an externally supplied digest.

    This is a transport primitive, not a manifest format or trust authority.
    Only SHA-256 is implemented here; this makes no claim about Kernel's hash
    algorithm. Directory descriptors and O_NOFOLLOW reject symlink traversal,
    including root ancestors. Returned bytes are the exact bytes hashed, with
    no parsing, imputation or identifier/timestamp transformation. No writes.
    """
    if algorithm != "sha256":
        raise SnapshotRejected("unsupported hash algorithm")
    if not isinstance(expected_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_digest):
        raise SnapshotRejected("expected a lowercase SHA-256 digest")
    if type(max_bytes) is not int or max_bytes <= 0:
        raise SnapshotRejected("max_bytes must be a positive integer")
    if not isinstance(reference, str) or not reference or any(
        not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", part)
        for part in reference.split("/")
    ):
        raise SnapshotRejected("unsafe relative file reference")

    descriptors: list[int] = []
    try:
        # Fail closed on platforms without descriptor-relative no-follow opens.
        if os.open not in os.supports_dir_fd or not hasattr(os, "O_NOFOLLOW"):
            raise SnapshotRejected("safe descriptor-relative access unavailable")
        directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        absolute_root = Path(root).absolute()
        if ".." in absolute_root.parts:
            raise SnapshotRejected("unsafe root path")
        current = os.open(absolute_root.anchor, directory_flags)
        descriptors.append(current)
        for part in (*absolute_root.parts[1:], *reference.split("/")[:-1]):
            current = os.open(part, directory_flags, dir_fd=current)
            descriptors.append(current)
        fd = os.open(reference.split("/")[-1],
                     os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=current)
        descriptors.append(fd)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise SnapshotRejected("expected a regular file with a single link")
        if info.st_size > max_bytes:
            raise SnapshotRejected("file exceeds byte limit")
        chunks = []
        total = 0
        while True:
            chunk = os.read(fd, min(65536, max_bytes + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise SnapshotRejected("file exceeds byte limit")
            chunks.append(chunk)
        payload = b"".join(chunks)
        if not hmac.compare_digest(hashlib.sha256(payload).hexdigest(), expected_digest):
            raise SnapshotRejected("content hash mismatch")
        return payload
    except (OSError, TypeError, ValueError) as exc:
        if isinstance(exc, SnapshotRejected):
            raise
        raise SnapshotRejected("file unavailable or unsafe") from exc
    finally:
        for fd in reversed(descriptors):
            os.close(fd)
