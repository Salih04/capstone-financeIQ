# Parallel security remediation candidate — 2026-10-28

Local engineering candidate only. No adoption, independent-review closure,
publication, deployment, live configuration or account migration is asserted.
Research support only; not investment advice.

## Provenance and scope

Fresh fetch on 2026-10-28 verified `origin/main` at
`efe3ed32ca958074c01ee9488f1f768a9d812c61`. The unmerged candidate
`82398ab1c9e2398c7f1db3d82c1126ff1c4d6970` exists locally, has sole parent
`2abf4221df8fa0201743a79614c74056f49ab0d8`, whose sole parent is that main.
The source candidate and primary checkout were clean at inspection. This lane
starts exactly at the candidate on `codex/fiq-security-parallel-20261028`, in a
new isolated worktree. No FIQ-09 or paper branch was integrated. The separate
read-only review's checkout, files and execution were not changed.

Read authority: root/process AGENTS and paired CLAUDE consistency; current
Research Charter and scoped owner addendum; repository map; security/auth
contracts and exact implementation. The owner's current task permits parallel
fixes and a local commit, not merge/deploy or owner-only policy decisions.
Older context and the unmerged parent's security assertions are dated evidence,
not proof of adoption or live behavior.

## Reproduced defects and changes

| Boundary | Negative control at original candidate | Candidate behavior |
| --- | --- | --- |
| `GET /score-runs/{id}` | Another active user received the owner's run, details and private explanation in both demo/private modes | Shared owner/admin guard rejects with 403 before serialization; missing run stays 404 |
| Report services | Calling CSV/JSON/PDF generators without a caller returned owned records despite router protection | Generators require an authenticated caller and invoke the same guard; missing caller gets 401 |
| Stale service caller | A retained admin object could export another user's run after local role revocation | Guard re-reads the local account with `populate_existing=True`; current active status and role govern |
| Supabase email collision | Signed tokens with another subject but the local admin's email resolved to that admin, even without email attestation | Identity is configured issuer + exact signed subject, bound to an existing local id; email is never a lookup/link key |
| Bootstrap/recreation | A new token with an admin claim created a local admin; an old token recreated a deleted local user | No request-time provisioning/linking; missing binding or account gets 401, even with auto-create explicitly true |

The report router already established owner/admin access. This rule is reused
for the score detail and services. `/users/me/score-runs` remains owner-scoped.
Owners and active admins retain detail/CSV/JSON/PDF access. Demo still permits
anonymous access through the established public research gate; it never opens
persisted user-owned scores. No new score/model calculation was used in testing.

Supabase verification retains JWKS/asymmetric and HS256 paths, requires subject
and expiration, and requires the configured project issuer before local binding.
Anonymous identities are refused for local account resolution. A changed or
absent token email cannot relink the user. Existing private allowlist attestation
is retained, with an additional requirement that the token email matches the
bound local contact email; user-writable email-verification metadata is ignored.

The parent's local-role ceiling and disabled-account checks are retained, not
represented as independently accepted or newly adopted policy. Stored local
revocation cannot be undone by an old higher-role token. The existing behavior
where a lower signed provider role permanently lowers the local role is retained;
changing that authority model requires an owner decision. No role/policy sweep
or session table, revocation endpoint, token lifetime, live migration or bootstrap
admin workflow was introduced.

## Verification and limits

Environment: task-only Python 3.12.3 environment installed from
`requirements-root.txt` (PyJWT 2.15.1, FastAPI 0.136.3, pytest 9.0.3);
PostgreSQL `16.15-alpine`, exclusively in the task-owned container
`fiq-security-parallel-20261028-pg`. Only existing Alembic migrations through
`20260713_0007` were applied to two new disposable databases. No running review
or application database was used. SQLite test storage now uses a unique
temporary directory per process, replacing deletion of a shared fixed path.

| Check | Original candidate baseline | This candidate |
| --- | --- | --- |
| Full backend collection only | 730 collected | 777 collected; +39 security and +8 configuration cases |
| Original 34 new synthetic cases, SQLite | 14 failed / 20 passed / 0 skipped, before production edits | Same 34 passed after fixes; final security module adds five more controls |
| Original 34 cases, migrated PostgreSQL | 14 failed / 20 passed / 0 skipped; five later cases explicitly deselected | Included in final 39 security cases |
| Existing safe auth/JWKS/shared-write selection | 34 passed, 12 deselected, 0 skipped | 34 passed, same 12 deselected, 0 skipped |
| Existing synthetic numeric/config selection | 107 passed, 0 skipped | 115 passed, including eight new binding-config tests |
| Combined SQLite selection | 141 existing passed, 12 deselected across the two baseline runs | 188 passed, 12 deselected, 0 skipped (39 new security + 8 new config) |
| Existing PostgreSQL integrity tests | 7 passed, 0 skipped | Included in 46 passed, 0 skipped (39 security + 7 integrity) |
| Claims/docs lint | Both passed | Both passed after code/docs changes |

The three additional direct-service stale-object controls first failed, then
passed after refreshing local authority in the shared guard. One PostgreSQL
repeat returned 44 passes / two test failures because its tests assumed a
globally empty user table while earlier synthetic integrity tests left rows.
Assertions now measure account-count deltas and absence of the deleted email;
the same 46-case run passed against that nonempty database. This was fixture
repair, not a product fix or an ignored failure. An extra baseline comparison
was interrupted after detecting the wrong source directory; it supplies no
verification result.

Scoped secret scanning initially flagged the numeric-suffixed synthetic test
secret placeholder. It was replaced with a readable test-only placeholder that
fits the existing scanner policy; no scanner rule or allowlist was changed.
The staged diff passed the same configured scanner (no leaks); four relevant
HS256/JWKS binding/bootstrap controls passed again after that placeholder edit.
Collection comparison found only the intentional old auto-provision test rename
to its fail-closed regression, plus 47 genuinely new cases; no unrelated test
was removed.

Exact safe selection (run from the repository root, with task Python on PATH):

```bash
PYTHONPATH=backend python -m pytest \
  backend/tests/test_security_parallel.py \
  backend/tests/test_auth_hardening.py backend/tests/test_supabase_jwks.py \
  backend/tests/test_shared_record_authz.py \
  backend/tests/test_missing_value_semantics.py backend/tests/test_config.py \
  -q -k 'not private and not a01' --tb=short

# Set FIQ_TEST_POSTGRES_URL only to a new disposable, already-migrated DB.
PYTHONPATH=backend python -m pytest \
  backend/tests/test_security_parallel.py backend/tests/test_postgres_integrity.py \
  -q --tb=short
PYTHONPATH=backend python -m pytest backend/tests --collect-only -q
make claims-lint docs-lint
```

The actual final test runs additionally loaded a task-only audit guard from
`/tmp/fiq-security-evidence-20261028/fiq_safe_tests.py` via
`PYTHONPATH=backend:/tmp/fiq-security-evidence-20261028` and
`-p fiq_safe_tests`. It refuses reads under this worktree's data/result paths
and external socket connections. The named PostgreSQL URL referred only to
loopback and the task container. Evidence logs, original backend source archive,
guard and test environment are outside the worktree, under that evidence
directory and `/tmp/fiq-security-env-20261028`. These temporary artifacts are
local evidence, not a durable evidence store or committed dependency.

For an equivalent negative-control replay, extract only `backend/` from
`82398ab1c9e2398c7f1db3d82c1126ff1c4d6970` into a fresh external scratch
directory with `git archive`; copy this candidate's isolated test conftest and
`test_security_parallel.py` there. Keep the archived production implementation
unchanged. Run that test file from the scratch root using `PYTHONPATH=backend`
and `-k 'not direct_report_service_checks and not missing_expiration and not jwks_verified'`.
Those exclusions select the original 34 controls; the expected original result
is 14 failures / 20 passes. An optional migrated disposable PostgreSQL URL
exercises the same controls on that engine. Never inject defects or replay
against the separate review checkout or a live DB.

No full backend/root **execution**: successful research endpoints and many
existing suites consume real capstone results, snapshots or source files. That
would exceed this lane's no-results/no-raw-data boundary. The 12 deselections
are the explicit `not private and not a01` selection, not skips or CI's root
deselect list. Synthetic `/gate` tests cover allowed/private/public behavior
without those artifacts. Collection does not imply 777 passing tests.
Deprecation and short test-only HMAC-secret warnings remain visible in logs;
they were not suppressed. No hosted CI, frontend build, live Supabase session,
holdout access, data acquisition, experiment or independent review was run.

## Owner approval required before rollout

The technical safe default is **empty bindings and no implicit provisioning**.
This intentionally refuses previously email-linked Supabase backend accounts
until individually verified bindings exist. It does not block legacy login or
open demo gates, and it never changes an existing account's ownership. Blindly
deploying an empty map to a Supabase-dependent installation would interrupt its
protected workflows. This candidate is not deployment authorization.

1. **Approve the binding/provisioning mechanism.** `SUPABASE_IDENTITY_BINDINGS`
   is a small operator-reviewed bridge, not a durable database identity registry.
   It is scoped to the configured `SUPABASE_URL` issuer; subject values are exact,
   local ids positive integers, and multiple subjects cannot silently share an
   account. Example only: `{"verified-subject-placeholder":17}`. No real mapping
   was prepared or installed. Decide whether to adopt this bridge or authorize
   a separate reviewed issuer/subject table and Alembic migration. No migration
   filename or production SQL is invented here.
2. **Prove each legacy binding out of band.** Use authorized server/provider
   identity evidence and authenticated ownership of the intended local account.
   Email equality, case-folded equality, a matching display name, or a user's
   metadata is insufficient. Audit possible preclaimed legacy accounts,
   case-only duplicates, provider email changes, deleted/recreated identities
   and already assigned admin roles before granting a binding. Do not merge,
   sweep, relink, delete or promote accounts automatically. Approval and actual
   evidence remain owner work; no live inventory was inspected.
3. **Approve first-admin recovery and role authority.** Existing authenticated
   admin role-management remains available. New admin creation/recovery has no
   public/request-time bootstrap. Choose an authorized offline provisioning
   process separately. Decide whether the retained provider-role lowering
   behavior should persist; token role promotion is not a safe fallback.
4. **Set revocation requirements explicitly.** Local disable/delete/role
   downgrade is checked on subsequent requests; direct score services also
   refresh it. This does not revoke the provider session or every issued JWT.
   Logout, password change/reset, local re-enable and later legitimate role
   regrant are not bound to a session version here. In particular an unexpired
   old token may become usable again after re-enable/regrant. Decide required
   revocation latency, local session/version or denylist design, provider-session
   validation, token lifetime and rollout/rotation. No claim of immediate global
   token revocation is made.
5. **Control mapping lifecycle.** Never repoint an existing subject or reuse a
   local numeric id for a different person. Remove/revoke approved mappings
   before account deletion, project replacement or restore; preserve a private
   audited history. Changing the project URL while reusing a mapping needs new
   owner proof, because the config map is scoped by the running configuration,
   not an immutable database record. Keep workers consistent. Mapping removal
   must reach every worker to take effect. An incorrect operator mapping can
   grant access; tests cannot prove real account ownership.
6. **Separate adoption from deployment.** Reconcile the exact commit with the
   independent review when that review finishes, without changing its input or
   findings now. Diff its findings against this lane's original candidate and
   final commit; keep untested/owner-only items open. Only a separately authorized
   rollout may set issuer, bindings, verified-email attestation and other live
   controls, after synthetic staging checks and a recoverable configuration plan.

Rollback should fail closed: withdraw affected bindings/disable affected local
accounts using the approved incident process. Reverting to email-based linking
or request-time claim provisioning would reopen the reproduced defects. No
runtime rollback, key rotation or live account change was executed here.

## External references checked 2026-10-28

- [Supabase users](https://supabase.com/docs/guides/auth/users) and
  [JWT fields](https://supabase.com/docs/guides/auth/jwt-fields): project user id
  and signed subject support identity binding; mutable email is not the key.
- [Supabase sessions](https://supabase.com/docs/guides/auth/sessions): JWT expiry
  and session existence are separate checks; this candidate does not add a
  live `auth.sessions` check or provider network dependency.
- [Server user validation](https://supabase.com/docs/reference/python/auth-getuser)
  is an available integration path for a separately scoped revocation design;
  it was not implemented or claimed as exercised.
- The current changelog was read; the relevant
  [TLS deprecation notice](https://supabase.com/changelog/cbc-tls-ciphers-deprecated)
  changes transport compatibility, not this local binding contract. No live
  TLS/provider configuration was tested or altered.
