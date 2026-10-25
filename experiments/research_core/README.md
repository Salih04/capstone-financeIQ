# Inert research-safety core

Research support, not investment advice. This is a technical prototype only.
FIQ-11 R7 is an unadopted candidate and supplies no scientific permissions.

`ledger.create(path, metadata=None)` exclusively creates a ledger with its first
event. `ledger.append(path, metadata=None)` requires an existing valid ledger.
`ledger.verify(path)` returns validity, count and head, or an error code and line
where available. Paths are explicit; there is no default study or data path.
An empty file is invalid, and a missing file is never recreated by append.

Schema 1 has `schema_version`, a unique UUID `event_id`, UTC `recorded_at`,
`previous_hash` (null for the first event), nullable `metadata`, and `hash`.
The SHA-256 digest covers the canonical JSON object excluding `hash`.
JSON is ASCII-escaped UTF-8, sorted by key, with compact separators, no NaN or
infinity, and one newline per record. Metadata must be a JSON object or null;
unknown values must be passed as null, never guessed. No scientific metadata
schema, trial classification, completeness claim or history import is supplied.
The verifier requires every envelope field; missing envelopes are corruption,
distinct from explicitly null unknown metadata.

Append validates the entire chain under a nonblocking exclusive POSIX `flock`,
then appends and fsyncs. Verification takes a nonblocking shared lock. Overlapping
writers are explicitly rejected as `ledger_busy`; callers may retry separately.
Unsupported locking platforms fail closed. Use a local filesystem supporting
these locks and regular files with one hard link; symlinks are rejected.
All writers must cooperate and leave file identity and parent directories stable.
Network filesystems, hostile filesystem replacement and noncooperating writers
are outside this prototype's guarantees. I/O failures propagate; an operation
that errors may already have appended bytes, so verify before a manual retry.
Partial writes or crashes may leave an invalid tail; no history is repaired,
deleted, rewritten or silently truncated. Creation is explicit and exclusive;
parent directories must already exist. Parent-directory crash durability is not
guaranteed by file fsync alone.

A hash chain is not independent proof of event time or tamper-proof storage.
Someone with write access can rewrite the entire chain or remove a complete
suffix; without an independently retained trusted head those changes cannot
be detected. Timestamps are local recording times, not proof of event occurrence.

`guard.require_protected_access(...)` always raises `ProtectedAccessDenied`,
without inspecting its arguments. There is no policy loader, approval check,
registration acceptance, unlock mechanism, holdout join, evaluation runner or
legacy integration. Existing experiment paths remain unchanged and are not
secured by this standalone guard. No scientific or operational access gate opens.

Run only the focused synthetic suite from the repository root:

```sh
python3 -B -m unittest discover -s experiments/research_core/tests -p 'test_*.py' -v
git diff --check
```

Tests create synthetic metadata only in temporary directories. They never import
legacy experiments or read study data, outcomes, protected files or task queues.
