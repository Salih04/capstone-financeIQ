"""Local append-only JSONL prototype, using cooperative POSIX file locks.

Hashes are not independent proof of event time or tamper-proof storage.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
from uuid import UUID, uuid4

try:
    import fcntl
except ImportError:  # No unsafe fallback on unsupported platforms.
    fcntl = None


FIELDS = {"schema_version", "event_id", "recorded_at", "previous_hash", "metadata", "hash"}


class LedgerError(ValueError):
    def __init__(self, code: str, line: int | None = None):
        self.code = code
        self.line = line
        super().__init__(f"{code}" + (f" at line {line}" if line is not None else ""))


@dataclass(frozen=True)
class Verification:
    valid: bool
    count: int = 0
    head: str | None = None
    error: str | None = None
    line: int | None = None


def canonical(value: object) -> bytes:
    """Deterministic UTF-8 JSON; non-finite numbers are rejected."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def _hash(record: dict) -> str:
    return hashlib.sha256(canonical({k: v for k, v in record.items() if k != "hash"})).hexdigest()


@contextmanager
def _locked(path: Path, *, create: bool = False, write: bool = False):
    if fcntl is None or not hasattr(os, "O_NOFOLLOW"):
        raise LedgerError("locking_unsupported")
    flags = (os.O_RDWR | os.O_APPEND) if write else os.O_RDONLY
    flags |= os.O_NOFOLLOW | os.O_NONBLOCK
    if create:
        flags |= os.O_CREAT | os.O_EXCL
    try:
        fd = os.open(path, flags, 0o600)
    except FileNotFoundError as exc:
        raise LedgerError("missing_ledger") from exc
    except FileExistsError as exc:
        raise LedgerError("ledger_exists") from exc
    except OSError as exc:
        raise LedgerError("open_failed") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise LedgerError("unsafe_file")
        try:
            fcntl.flock(fd, (fcntl.LOCK_EX if write else fcntl.LOCK_SH) | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise LedgerError("ledger_busy") from exc
        with os.fdopen(fd, "r+b" if write else "rb", closefd=False) as stream:
            yield stream
    finally:
        os.close(fd)


def _scan(stream) -> tuple[int, str | None, set[str]]:
    previous = None
    seen = set()
    count = 0
    for number, raw in enumerate(stream, 1):
        if not raw.endswith(b"\n"):
            raise LedgerError("truncated_tail", number)
        try:
            record = json.loads(raw)
            if not isinstance(record, dict) or set(record) != FIELDS:
                raise LedgerError("invalid_fields", number)
            if type(record["schema_version"]) is not int or record["schema_version"] != 1:
                raise LedgerError("unknown_schema", number)
            if canonical(record) + b"\n" != raw:
                raise LedgerError("noncanonical_record", number)
            if str(UUID(record["event_id"])) != record["event_id"]:
                raise LedgerError("invalid_event_id", number)
            timestamp = datetime.fromisoformat(record["recorded_at"].replace("Z", "+00:00"))
            if timestamp.tzinfo != timezone.utc or not record["recorded_at"].endswith("Z"):
                raise LedgerError("invalid_timestamp", number)
            if record["metadata"] is not None and not isinstance(record["metadata"], dict):
                raise LedgerError("invalid_metadata", number)
            if record["event_id"] in seen:
                raise LedgerError("duplicate_event", number)
            if record["previous_hash"] != previous:
                raise LedgerError("broken_link", number)
            if record["hash"] != _hash(record):
                raise LedgerError("hash_mismatch", number)
        except (TypeError, ValueError, AttributeError, OverflowError, RecursionError) as exc:
            if isinstance(exc, LedgerError):
                raise
            raise LedgerError("malformed_record", number) from exc
        seen.add(record["event_id"])
        previous = record["hash"]
        count += 1
    if count == 0:
        raise LedgerError("empty_ledger")
    return count, previous, seen


def verify(path: str | Path) -> Verification:
    """Report validity or a clear failure; never create or repair a file."""
    try:
        with _locked(Path(path)) as stream:
            count, head, _ = _scan(stream)
        return Verification(True, count, head)
    except LedgerError as exc:
        return Verification(False, error=exc.code, line=exc.line)
    except OSError:
        return Verification(False, error="io_failed")


def _append(path: str | Path, metadata: dict | None, *, create: bool) -> dict:
    # Validate and detach caller metadata before touching the ledger.
    if metadata is not None and not isinstance(metadata, dict):
        raise LedgerError("invalid_metadata")
    metadata = json.loads(canonical(metadata))
    with _locked(Path(path), create=create, write=True) as stream:
        previous = None
        seen = set()
        if not create:
            _, previous, seen = _scan(stream)
        event_id = str(uuid4())
        while event_id in seen:
            event_id = str(uuid4())
        record = dict(schema_version=1, event_id=event_id,
                      recorded_at=datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
                      previous_hash=previous, metadata=metadata)
        record["hash"] = _hash(record)
        raw = canonical(record) + b"\n"
        # O_APPEND and the exclusive lock cover the whole verify/append/fsync operation.
        # A partial I/O failure is preserved as an invalid tail, never rolled back.
        stream.seek(0, os.SEEK_END)
        if stream.write(raw) != len(raw):
            raise LedgerError("short_write")
        stream.flush()
        os.fsync(stream.fileno())
        return record


def create(path: str | Path, metadata: dict | None = None) -> dict:
    """Exclusively create a new ledger with its first event; never overwrite."""
    return _append(path, metadata, create=True)


def append(path: str | Path, metadata: dict | None = None) -> dict:
    """Verify then append; missing, empty, corrupt or busy ledgers are rejected."""
    return _append(path, metadata, create=False)
