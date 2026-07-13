# Authenticated E2E / visual-verification spike (R3-E2E-01)

**Status:** research spike — **memo only, zero code**. Observed 2026-07-13 at git
`8c731e11` on branch `local/r3-e2e-01-auth-setup-156e10`; working tree clean.

**Why this exists.** Four Phase-2 reports recorded "protected-page visual
verification blocked by missing approved Supabase session." The one existing E2E
spec assumes open email/password signup, which contradicts the private-lockdown
auth defaults. The demo runbook forbids weakening auth for a presentation
(`docs/DEMO_RUNBOOK.md` § "Authentication unavailable"). This memo owns the
decision and the evidence for a reliable authenticated E2E / visual approach; it
implements nothing. The follow-up implementation task is drafted in §12 and is
already listed (not started) in the queue's Later backlog.

**Hard constraints (restated, binding on any follow-up).** No auth weakening; no
bypass flag reachable by a production code path; no committed secrets; no CAPTCHA
circumvention; protected routes stay protected; Supabase policies, session
validation, and route guards are untouched.

---

## 1. Current authentication lifecycle (mapped)

Every claim below is grounded in a read file.

- **Supabase client init** — `frontend/src/lib/supabaseClient.js`. `createClient`
  runs only when both `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are set
  (`isSupabaseConfigured`); otherwise `supabase` is `null`. Session options:
  `persistSession: true`, `autoRefreshToken: true`, `detectSessionInUrl: true`.
  Because `persistSession` is true, the session lives in browser **localStorage**
  under the Supabase `sb-<project-ref>-auth-token` key — the state Playwright's
  `storageState` captures.
- **Sign-in UI** — `frontend/src/pages/LoginPage.jsx`. Modes are
  `login | signup | forgot | reset-password`. Signup collapses to login unless
  `VITE_ENABLE_SIGNUP` is true (`normalizeMode`, and the guarded `auth.register`
  call). Google is behind `VITE_ENABLE_GOOGLE_AUTH`. Both default OFF
  (`frontend/src/lib/authConfig.js`).
- **Session context** — `frontend/src/context/AuthContext.jsx`. On mount it calls
  `supabase.auth.getSession()` then subscribes with
  `supabase.auth.onAuthStateChange`; `loading` starts `true` only when Supabase is
  configured. `login` uses `signInWithPassword`; `logout` calls
  `supabase.auth.signOut()` and clears the API cache. Approval is derived as
  `approved: isApproved(user?.email)`.
- **Approval gate** — `frontend/src/lib/authConfig.js`. `isApproved` returns true
  unless `VITE_REQUIRE_APPROVED_USER` is set, in which case the lowercased email
  must be in `VITE_APPROVED_EMAILS`; an empty allowlist denies everyone (fail
  closed).
- **Route protection** — `frontend/src/components/ProtectedRoute.jsx`, wired by the
  `Protected` wrapper in `frontend/src/App.jsx`. Order: `loading` → renders
  `AUTH SIGNAL LOCKING`; `!isAuth` → `<Navigate to="/login">`; authenticated but
  `!approved` → an in-place **PRIVATE DEPLOYMENT** block (not a redirect) with a
  sign-out button; else children. Every research/forecasting page in
  `frontend/src/App.jsx` is wrapped in `Protected`; `/` and `*` redirect via
  `<Navigate>`.
- **Logout** — `AuthContext.logout` (above); the block screen in
  `ProtectedRoute.jsx` also exposes it.
- **Public-demo + protected API behavior** — `backend/app/core/dependencies.py`
  `require_access`. With `PUBLIC_DEMO_MODE=true` (the default,
  `backend/app/config.py`) it behaves like `optional_user`: returns the verified
  user if a valid token is present, else `None`, and **never blocks** — so
  read-only research endpoints answer without a token. With
  `PUBLIC_DEMO_MODE=false`: no/invalid token → 401; with `REQUIRE_APPROVED_USER`
  the verified email must be in `APPROVED_EMAILS` (empty allowlist → 403, fail
  closed). Token verification is signature-only: legacy `SECRET_KEY` HS256 JWTs
  (`_legacy_user`) or Supabase JWTs (`_supabase_user` → `decode_supabase_token`).
- **Backend Supabase verification** — proven by `backend/tests/test_supabase_jwks.py`:
  asymmetric RS256 via JWKS (network mocked) and the HS256 legacy-secret fallback,
  plus fail-closed behavior when no verifier is configured, and the private-mode
  200/401/403 matrix against `/research/summary`.
- **Legacy token minting** — `backend/app/routers/auth.py` `POST /auth/login`
  issues a `create_access_token({"sub": user.id})` HS256 JWT signed with the
  backend `SECRET_KEY`. This is a **backend** credential; the browser Supabase
  client will not accept it as a Supabase session (different signer).

**Consequence for testing.** To render a protected page in a real browser, the
app needs (a) a Supabase session in localStorage that (b) carries an email in
`VITE_APPROVED_EMAILS` (or a test build that sets `VITE_REQUIRE_APPROVED_USER`
false). A backend legacy JWT satisfies the API but **cannot** drive the frontend
UI. This is the crux the follow-up must respect.

---

## 2. Current E2E framework state

- **Runner** — Playwright (`@playwright/test` `^1.52.0`), script `"e2e":
  "playwright test"` in `frontend/package.json`.
- **Config** — `frontend/playwright.config.js`: `testDir: ./tests`, `timeout`
  120s, `headless`, `baseURL` from `E2E_BASE_URL` (default
  `http://localhost:3000`). There are **no** browser `projects`, **no** `webServer`
  (nothing starts Vite/Docker), **no** `retries`, **no** `trace`, and **no**
  `screenshot`/video capture configured.
- **Only spec** — `frontend/tests/e2e-forecasting.spec.js`. It navigates to
  `/login`, clicks the Turkish signup buttons (`kayıt ol`, `hesap oluştur`),
  creates a throwaway account, and waits for a post-login route. This **only works
  when `VITE_ENABLE_SIGNUP=true`**; under the locked-down defaults the signup path
  collapses to login (`normalizeMode`) and the spec cannot pass. It also assumes a
  server already running on `baseURL`. So today there is effectively **no
  green authenticated E2E** and **no visual-regression** coverage.

CI assumptions: none are encoded in-repo for this suite (no `webServer`, no CI
workflow references the `e2e` script that this spike found); any CI story is
greenfield and is part of the follow-up, not an existing constraint.

---

## 3. Test categories (kept distinct)

The blocker conflated four different things; the follow-up must not:

1. **Auth integration tests** — already covered on the backend by
   `backend/tests/test_supabase_jwks.py` (verification, fail-closed, 200/401/403).
   No browser needed.
2. **Protected-route E2E** — does an unauthenticated visit redirect to `/login`,
   and can an *approved* session open a protected route in a real browser? Needs a
   browser + a session.
3. **Visual-regression** — pixel/DOM snapshots of protected pages. Needs the same
   session as (2) **plus** deterministic data and a screenshot baseline; strictly a
   superset of (2). Out of scope for the minimal follow-up.
4. **Demo/public smoke** — the read-only API path that works under
   `PUBLIC_DEMO_MODE=true` (`make demo-check`, `scripts/demo_smoke.py`). Needs no
   session and already exists.

---

## 4. Approaches evaluated

### A. Playwright `storageState` reuse after a one-time manual login (recommended)

- **How.** A developer signs in once, manually, against a **local/dev** Supabase
  project with an approved test user, through the real `/login` UI (real
  `signInWithPassword`, real guards). Playwright's global setup saves the browser
  context (`storageState`) — cookies + localStorage, including the Supabase
  `sb-<ref>-auth-token` — to an untracked file; protected-route specs load it via
  `storageState`. The real integration (Supabase client + `ProtectedRoute` +
  approval gate in `frontend/src/lib/authConfig.js`) is exercised, not stubbed.
- **Feasibility — supported by repo evidence.** `persistSession: true` in
  `frontend/src/lib/supabaseClient.js` guarantees the session is in localStorage,
  which is exactly what `storageState` serializes. The approval gate keys on
  `VITE_APPROVED_EMAILS`, so the manual user's email is a documented env
  prerequisite, not a code change.
- **Cost / caveats.** Supabase access tokens are short-lived; the saved state
  expires (see §8). It requires a real dev Supabase project to exist. It does not
  itself start a server (no `webServer` today — the follow-up adds one).
- **Secret posture.** The saved state contains live tokens → it is secret-grade
  and must never be committed (see §7). No password ever enters a tracked file.

### B. Dedicated local-only Supabase test project with a seeded approved user

- **How.** A separate Supabase project used only for tests, with one pre-seeded
  approved user whose credentials come from **env/CI secret storage** (never
  committed). Global setup logs that user in programmatically
  (`signInWithPassword`) and saves `storageState` as in (A); the difference is the
  credentials are injected rather than typed by a human once.
- **Feasibility.** Fully supported — it is (A) with automated login. `SUPABASE_AUTH.md`
  already documents standing up a project and enabling email/password. Best for CI
  (unattended, rotatable).
- **Caveats.** Requires provisioning a project and storing two secrets
  (email + password) in CI. More setup than (A); overkill for a first local-only
  foundation. Recommended as the **CI evolution** of (A), not the starting point.

### C. API-level-only assertion expansion (complement, always available)

- **How.** Assert protected behavior through the backend contract instead of the
  browser: `require_access` returns data under `PUBLIC_DEMO_MODE=true`; a legacy
  `POST /auth/login` HS256 token (`backend/app/routers/auth.py`) exercises the
  authenticated 200 path; the private-mode 401/403 matrix is already proven by
  `backend/tests/test_supabase_jwks.py`. Page **visuals stay manual**.
- **Feasibility.** Fully supported today; no Supabase project, no browser, no
  secret. This is the honest fallback the four blocked reports should have taken,
  and it is the **skip target** (§9) when no approved session exists.
- **Limit.** It does not verify the `ProtectedRoute` render path or any pixels —
  it is a complement to (A)/(B), not a replacement.

### D. Deterministic local auth adapter in an explicitly isolated test build (evaluated, constrained)

- **How (only safe shape).** A test-only entry that logs into the **real** local
  Supabase project via `signInWithPassword` and hands the real session to the real
  client — i.e. it automates login without replacing Supabase. This reduces to (B).
- **Rejected shape.** Any adapter that *fakes* a session (injects a synthetic
  `session` object, forces `isAuth`/`approved` true, or short-circuits
  `ProtectedRoute.jsx`) is **rejected**: it would (i) not test the real
  integration and (ii) risk activating in production. `isApproved` and
  `require_access` are the guards; a fake adapter bypasses both. Not pursued.

### E. API-created Supabase session (evaluated, not first choice)

- Supabase admin/API session creation (e.g. a `service_role` action) is **not
  evidenced** in this repo's config or docs and would require a service-role key,
  which `docs/SUPABASE_AUTH.md` explicitly forbids outside the backend and which
  must never reach test fixtures or the browser. Marked **needs verification** and
  not recommended; (A)/(B) reach the same place with only an anon key + user
  credentials.

---

## 5. Rejected approaches (and why)

- **Re-enabling `VITE_ENABLE_SIGNUP` for tests** (what the current spec implicitly
  needs) — weakens the private-lockdown posture and diverges the test build from
  production auth. Rejected.
- **A production-reachable bypass flag / demo login** — forbidden by the packet and
  by `docs/DEMO_RUNBOOK.md`; `isApproved` and `require_access` fail closed by
  design. Rejected.
- **Committing any session state, token, password, or `service_role` key** —
  forbidden; see §7. Rejected.
- **Fully stubbing Supabase** — leaves the real integration untested (defeats the
  purpose). Rejected (see D).
- **Depending on a developer's permanent personal session** — non-reproducible,
  expires, and risks a real personal account in test logs. Rejected in favor of a
  dedicated approved **test** user.

---

## 6. Recommendation

**Adopt Approach A now** (Playwright `storageState` from a one-time manual login
against a local/dev Supabase project), **structured so it upgrades to B for CI**
(seeded test user injected from CI secrets) without rework. Keep **Approach C** as
the always-on complement and the skip target. This is the smallest design that
tests the *real* guard chain, commits no secrets, and can never weaken production.

### Exact env prerequisites (the recommended approach names its own)

Frontend (dev/test build only — all `VITE_*` values are public by design per
`frontend/.env.example`, so none are secrets):

- `VITE_SUPABASE_URL` — the **local/dev** Supabase project URL.
- `VITE_SUPABASE_ANON_KEY` — that project's anon/publishable key (public).
- `VITE_REQUIRE_APPROVED_USER=true` and
  `VITE_APPROVED_EMAILS=<test-user-email>` — so the approval gate is exercised, not
  disabled.
- `VITE_ENABLE_SIGNUP=false`, `VITE_ENABLE_GOOGLE_AUTH=false` — production-matching.
- `VITE_API_URL` — the local backend.

Test-runner env (the two **secrets**, provided via local shell / CI secret store,
never committed):

- `E2E_SUPABASE_TEST_EMAIL`
- `E2E_SUPABASE_TEST_PASSWORD`

Plus `E2E_BASE_URL` (already read by the config and the existing spec).

Backend, only if a follow-up also asserts the *private-mode* API in a browser flow
(otherwise `PUBLIC_DEMO_MODE=true` needs nothing): `SUPABASE_JWT_SECRET`
(or `SUPABASE_URL` for JWKS), `PUBLIC_DEMO_MODE=false`, `REQUIRE_APPROVED_USER=true`,
`APPROVED_EMAILS=<test-user-email>` — matching the matrix already proven in
`backend/tests/test_supabase_jwks.py`.

---

## 7. Secret-handling & threat boundaries

- **Secret-grade artifacts:** the saved `storageState` file (live access + refresh
  tokens) and `E2E_SUPABASE_TEST_PASSWORD`. **Public/non-secret:** every `VITE_*`
  value (shipped in the browser bundle) and `E2E_SUPABASE_TEST_EMAIL`.
- **Never committed / never printed:** the follow-up's saved-state path must live
  under an already-ignored location. Note the current `.gitignore` covers `.env`,
  `.env.*` (keeping `.env.example`), `frontend/.env.local`, `*.pem`, `*.key`,
  `*.secret`, `*.db` — but **not** an arbitrary `storageState` JSON. Placing the
  file under a dot-directory such as a test-local `.auth/` folder (dotted path) is
  the safe pattern; the follow-up must add an explicit ignore entry and prove it
  with a tracked-file grep before any commit.
- **Threat model.** The realistic leak vectors are: a committed state file; tokens
  in Playwright traces/screenshots; credentials echoed in CI logs. Mitigations:
  ignore the state path; keep `trace`/`screenshot` off for the auth-setup step (or
  scrub); pass credentials only through secret env, never CLI args or fixtures.
- **Production isolation.** Nothing in Approach A/B adds a code path that changes
  runtime behavior. The guards (`ProtectedRoute.jsx`, `authConfig.js`,
  `require_access`) are unmodified; tests merely supply a *real* approved session.
  There is no flag that, if set in production, would grant access — the only lever
  is possessing valid approved credentials, which is the intended boundary.

---

## 8. Expiration, rotation, failure, cleanup (for saved session state)

- **Expiration.** Supabase access tokens are short-lived; a saved `storageState`
  goes stale. Global setup must **re-login and re-save** on each run (or when the
  state is older than a small TTL), not reuse an indefinitely cached file.
- **Rotation.** The test user's password rotates via the CI secret store; no
  tracked file changes when it rotates.
- **Failure.** If login fails or the project/env is absent, setup must **fail
  visibly** (clear message: missing/invalid auth config) — never silently fall
  through to an unauthenticated run reported as pass (see §9).
- **Cleanup.** The saved-state file, any temporary browser profile, screenshots,
  and traces are ephemeral build artifacts: gitignored, removed after the run, and
  never staged. No throwaway user is created per-run under Approach A/B (a single
  seeded user is reused), so there is no per-run user cleanup — a strict
  improvement over the current signup-per-run spec.

---

## 9. Skip semantics (blocker ≠ pass)

The suite must **distinguish skipped-with-blocker from passed**:

- The unauth-redirect spec (§10 scenario 1) needs no session and always runs.
- Session-dependent specs check for the required env / valid saved state in global
  setup. If absent, they **skip with an explicit annotation** naming the blocker
  ("approved Supabase test session unavailable") — Playwright `test.skip(...)` with
  a reason, surfaced in the report — rather than passing vacuously. This is the
  disciplined version of what the four Phase-2 reports should have recorded.

---

## 10. Verification scenarios the follow-up must satisfy

1. **Unauthenticated → login redirect.** Visit a `Protected` route with no state →
   `ProtectedRoute.jsx` `!isAuth` branch → URL becomes `/login`. No session needed.
2. **Missing auth config fails visibly.** With Supabase env unset, global setup
   errors clearly (config missing) and session specs skip-with-blocker, never pass.
3. **Approved session opens the packet route.** With a valid saved state whose email
   is approved, at least one protected route renders (children branch), proving the
   real guard chain.
4. **Logout / expired state restores redirect.** After `logout` (or an expired
   token), the same route redirects to `/login` again.
5. **No secret material in tracked files, output, screenshots, traces, or logs.**
   Enforced by the ignore entry + a secret-pattern grep gate in the follow-up.
6. **Test-only config cannot activate in a production build.** No bypass exists to
   activate; the guard is a real approved session. An explicit guard test asserts
   there is no runtime flag that forces `approved`/`isAuth` true.
7. **Skipped-with-blocker ≠ passed** — see §9.
8. **Public smoke + production frontend build still pass** — unchanged by a
   memo, and a hard gate for the follow-up.

---

## 11. Ownership

- **This memo:** Ops/Frontend, complete at `8c731e11`.
- **Follow-up harness:** Ops/Frontend, Opus-class, per §12. It owns the Playwright
  global-setup, the ignore entry, the skip semantics, and the CI secret wiring.

---

## 12. Drafted follow-up implementation task (not started)

> Already referenced in `FINANCEIQ_AGENT_TASK_QUEUE.md` Later-backlog row
> "(follow-up) · Authenticated E2E implementation · Wave 3E". Draft only — do not
> start under R3-E2E-01.

**Title:** Authenticated protected-route E2E foundation (storageState, Approach A).
**Wave/gate:** 3E, after R3-E2E-01. **Model/effort:** Opus, medium. Review: Terra low.
**Scope (minimal, binding):**

- Add a Playwright global-setup that logs the seeded **approved** test user into
  the **local/dev** Supabase project via `signInWithPassword` and saves
  `storageState` to an ignored dotted path (proposed: a test-local `.auth/`
  directory). No fake session, no bypass.
- Add `projects` to `frontend/playwright.config.js`: an unauthenticated project
  (redirect spec) + an authenticated project consuming the saved state. Add a
  `webServer` (or documented external server) so `baseURL` is real. Keep `trace`
  and `screenshot` off for the auth-setup phase.
- Add exactly these specs: (1) unauth → `/login` redirect; (2) approved session
  opens **one** packet-specified protected route; (3) logout/expired → redirect.
  Session specs **skip-with-blocker** when env/state is unavailable (§9).
- Retire or rewrite `frontend/tests/e2e-forecasting.spec.js` so nothing depends on
  `VITE_ENABLE_SIGNUP=true`.
- Add the `.gitignore` entry for the state path and a secret-pattern grep gate over
  changed files + generated test outputs. Add the §10.6 production-isolation guard
  test.

**Env prerequisites:** exactly §6 (public `VITE_*` + the two secret
`E2E_SUPABASE_TEST_*` values). **Do NOT touch:** `ProtectedRoute.jsx`,
`AuthContext.jsx`, `authConfig.js`, `supabaseClient.js`, `dependencies.py`,
`config.py`, deployment configs. **Acceptance:** scenarios §10 pass or
skip-with-blocker; `npm run build`, `make claims-lint`, `make docs-lint`, backend
suite, and public smoke stay green; no secret in any tracked file. **Stop:** if no
local/dev Supabase project can be provisioned, ship Approach C (API-only) plus the
unauth-redirect spec and record the visual gap — that finding is an acceptable
deliverable.

---

## 13. Stop-condition result

A constraint-satisfying approach **does** exist (A → B, with C as complement), so
the packet's "if no approach satisfies the constraints, that finding is the
deliverable" stop condition did not trigger. The single unresolved external
dependency is provisioning a local/dev Supabase test project with an approved test
user; until it exists, the honest posture is Approach C + skip-with-blocker (§9),
never a fabricated pass.
