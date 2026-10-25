# FIQ-08 approved synthetic consumer — 2026-10-26

**Implemented and locally verified: E-1 filing-facts-only synthetic compatibility.**
Full six-domain FIQ-08 and real-data export remain unavailable. This record does
not adopt a research specification or authorize holdout/experiment access.

## Authority and immutable evidence

The owner explicitly authorized synthetic integration and, after successful
focused tests, task-branch push and a PR; merge/main push are excluded. Current
PR parent is origin/main `47f06a2893cbd89171a6acfcb1debee79e68e331`, refreshed
2026-10-26. Preserve the `b2200441` bounded byte verifier exactly. Its unmerged
parent governance draft is excluded from this PR; no FIQ-06 R14, FIQ-11 R7 or
other lane is incorporated. One new task commit contains this consumer and its
previously local prerequisite, rather than publishing unrelated ancestor changes.

Approved ZIP: `FIQ08_FactsOnly_Approved.zip` (the referenced chat's attachment;
`/mnt/data` is absent on this host). SHA-256:
`5dcbd0724e889ff456baa5fc64661c2c62a50b8444edd5cae6af272fb8eb282f`.
Kernel pin: `d7668217183220744f391bc5ae9fa25493aca8ce`, tree
`75897ce0d6fecaae172e4417776b8683f0538137`, contract `4.0.0`, algorithm
`sha256:financeiq-pit-snapshot-v4`. Approved manifest SHA-256:
`fc0cf0c8c1b230a8f06a7e989ecd9dbad6e208064321ac08ccadec2169be185d`.
ZIP CRC/path/type/size checks passed; all 14 manifest entries match SHA-256 and
size, and all 13 source Git blob IDs match package bytes. This task did not open
Kernel or recheck its Git tree; source-revision identity relies on the approved
E-1 evidence. Hashes prove integrity, not signed source authenticity.

Copy provenance: the ten fixture/digest/request files are byte-identical under
`tests/fixtures/kernel/contract_v4/`; two schema files are byte-identical under
`experiments/pit/contract_v4/`. The unmodified approved manifest is retained at
`tests/fixtures/kernel/SHA256_MANIFEST.txt`; other manifest entries are reference
inventory, not files added here. Package contract says hashes cover canonical
UTF-8 JSON `{contract_version, dimension_key, facts}`; full file SHA-256 separately
binds the query times, which are outside that content hash.

## Consumer and guard boundary

`open_snapshot(None)` returns None before IO or optional imports. No environment
lookup, autodiscovery or production entry-point change. A configured caller must
supply a relative file reference, approved external byte digest and the complete
request. Only the six approved pretty/canonical synthetic envelope byte hashes
are enabled; arbitrary exports fail closed. Configured errors never select legacy.
The public snapshot constructor enforces the same byte allowlist. No network,
Kernel write-back, real export, SQL, outcome/model or source acquisition path.

Validate the exact pinned envelope schema (including embedded fact schema),
contract/hash identifiers, full ten-component dimension key, canonical content
hash, external query coordinates, unique sorted fact IDs, requested keys and
valid/public/system time bounds. Reject unknown publication times. DATE_ONLY
uses the conservative upper bound of the evidenced IANA local day; preserve
precision, measuring-unit metadata and nulls. `value:null` is not valid in this
contract; missing facts remain absent, never fabricated/imputed. Published YTD
facts remain cumulative; there is no quarter subtraction or annual/issuer alias
mapping. `recorded_at` remains writer-asserted metadata, not proof of persisted
transaction visibility or rights.

`SyntheticSnapshot.fact(full_key, prediction_time=...)` calls the existing
`guard.assert_point_in_time` with `known_at_upper`. It returns a fresh fact copy
or None for a requested absent key; unrequested/partial keys reject. Query
coordinates and the complete request stay attached to the verified bytes.
The frozen annual panel is not fed invented filing facts; no unsupported durable-
ID-to-ticker or quarterly-to-annual mapping is invented. The five existing PIT
modules remain byte-identical. This is a synthetic consumer/guard boundary,
not fulfillment of the historical six-domain task card.

## Focused verification and limits

Optional dependency: `jsonschema==4.25.1` in `requirements-synthetic.txt`, installed
only in an external isolated test dependency directory. pandas is supplied by the
existing FinanceIQ development environment; neither is imported on the disabled
adapter path. Run with those dependencies available:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m unittest experiments.pit.test_kernel_snapshot -v
git diff --check
```

16 tests pass (no skips): original byte/path/link/size/read-only negative controls;
12 copied files' manifest/blob pins; 5/3/0-row pairs and exact canonical digests;
full-key separation and absent-key behavior; rehashed schema/time/outcome-field
attacks; duplicate JSON keys/non-finite values; unknown contract/hash identifiers;
request-coordinate binding; corruption without fallback; guard upper-bound
boundary; exact source hashes for all five legacy PIT modules plus byte-identical
legacy availability output in both modes using disposable synthetic CSV inputs.
The first run exposed an incorrect test inventory expectation (11 versus 12);
corrected the count and reran. No empirical files or experiment pipeline ran.
No broader root/data validation was run because it would exceed the owner's
focused synthetic/no-data scope. Local checks are not independent scientific
review, hosted CI or merge acceptance.

Real rights-cleared exports, additional transport domains, approved identity and
period mappings, and scientific FIQ-06/11/12 gates remain separate dependencies.
The following 2026-10-25 record is preserved as historical evidence, superseded
only for the narrowly approved synthetic interface described above.

---

# FIQ-08 bounded prerequisites — 2026-10-25

Exchange compatibility: **UNVERIFIED**. No exchange version is accepted.
This is not a completed export adapter or scientific adoption.

## Evidence and boundary

Base: `9473388fda3e6e946dda32fa0cf8034cf043f591`, preserving the governance
fast-path draft. Read root `AGENTS.md`, `docs/process/AGENTS.md`,
`docs/process/RESEARCH_CHARTER.md`, the repository map and only the exact FIQ-07
and FIQ-08 sections of `docs/process/TASKS_FINANCEIQ_2026-10-07.md`.
That task-card file has SHA-256
`f8802e0c5450f5d59f5a765a4273d74f70d6e3fc6e8243369826596c0b39d72d`.
FIQ-08 references contract 2.0.0 and KER-15 export; this is historical task
wording, not evidence of the current approved interface. FIQ-07 requires full
historical entity/security keys, membership provenance and snapshot hashes.

Targeted tracked-path checks in this FinanceIQ revision found no Kernel
exchange contract or synthetic export fixture. No Kernel repository, raw
source data, protected dataset or experiment output was opened to resolve it.
No claim is made that an approved contract does not exist elsewhere.

## Implemented

`kernel_snapshot.py` provides a contract-independent byte verifier: explicit
SHA-256 selection, digest verification, a byte limit, descriptor-relative
read-only access, and rejection of missing files, unsafe references, symlinks,
hardlinks and non-regular files. Digests must come from a separately trusted
authority; a matching hash alone does not establish provenance or schema.
The verifier neither parses nor exposes facts and cannot filter outcome
fields. It must only receive explicitly authorized, outcome-safe files.
All tests create synthetic bytes in disposable directories; none are Kernel
fixtures or evidence of exchange compatibility.

`validate_contract_version` rejects every version, including 2.0.0.
`open_snapshot(None)` returns None; every configured value, including an empty
string, fails before filesystem access. There is no environment-variable
setting, manifest parser, auto-discovery or legacy integration. Callers must
not catch a configured-snapshot rejection and fall back to legacy data.

The existing PIT modules are unchanged byte-for-byte from the base. Their
legacy behavior remains untouched because this module is not wired into them;
no claim of a synthetic end-to-end legacy equivalence run is made.

## Focused verification

Run from the isolated FinanceIQ worktree:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest experiments.pit.test_kernel_snapshot -v
```

9 synthetic tests passed. Coverage: exact-byte/null preservation, nested files,
corruption, unsafe/missing references, symlinks (including root), hardlinks,
FIFO rejection, hash policy, byte bounds, read-only open flags and unchanged
file bytes/mtime, no-configuration behavior and rejection of all versions and
configured paths before IO. `git diff --check` passed. An exact diff of the
five existing `experiments/pit/` modules against the base was empty.
No experiments, models, returns, holdout reads or broad test suite ran.

## Smallest next step from PIT Kernel

Supply one approved, outcome-free exchange specification pinned to an exact
revision (or an authorized synthetic export fixture with equivalent contract
authority). It must establish the current version and acceptance policy,
export entry point/layout, manifest schema, hash algorithm and exact hashed
bytes/canonicalization, file inventory/completeness rules, permitted fact
schemas and full historical dimension keys, null representation, and
`known_at`/filing-time semantics and bounds. Include a synthetic valid export
and its expected hashes. Do not supply raw data or outcomes.

Until then: manifest parsing, fact/outcome-field validation, filing-time guard
wiring, config/env selection and FIQ-07 integration remain blocked. No push,
PR, merge, Kernel changes or scientific acceptance is part of this task.
