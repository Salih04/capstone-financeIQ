# Security

FinanceIQ is a research/educational capstone. This documents its security posture
for the public repository.

## Secrets

- **No secrets are committed.** `.gitignore` excludes `.env` / `.env.*` (the only
  tracked env file is `backend/.env.example`, which holds placeholders).
- Docker images exclude secrets via `.dockerignore` / `frontend/.dockerignore`
  (`.env*`, `.git`, virtualenvs, caches, `node_modules`). Never bake a real
  `.env` into an image.
- Required runtime secrets are supplied via environment only:
  `SECRET_KEY` (JWT signing), `DATABASE_URL`, `OPENROUTER_API_KEY` /
  `OPENAI_API_KEY`, optional `SUPABASE_JWT_SECRET`. `docker-compose.yml` ships a
  dev-only `SECRET_KEY` fallback that must be overridden for any deployment.
- If a key is ever exposed, rotate it (OpenRouter dashboard, Supabase Project
  Settings → API/Database, regenerate `SECRET_KEY`).

## Access modes (demo vs private)

Research (`/research/*`) and CSV-forecasting (`/forecasting/options|train|run|
explain|inference`) endpoints go through the `require_access` dependency, gated
by env:

- **Demo (default, `PUBLIC_DEMO_MODE=true`)** — open read-only access. Serves only
  validated, already-public BIST research data; never mutates state. Preserves the
  current deployment and local dev.
- **Private (`PUBLIC_DEMO_MODE=false`)** — requires a verified authenticated user.
  Anonymous → 401, unapproved → 403. With `REQUIRE_APPROVED_USER=true` the
  verified email must be in `APPROVED_EMAILS` (case-insensitive); an empty
  allowlist denies everyone (**fail closed**). Verification uses token signatures
  only: Supabase **JWT Signing Keys** (RS256/ES256) are verified against the
  project JWKS derived from `SUPABASE_URL` (cached in memory), and legacy HS256
  tokens via `SUPABASE_JWT_SECRET`. The JWKS path never accepts HS256 (no
  alg-confusion). With no usable verifier configured, private mode denies all
  (fail closed). Email/claims are read only after the signature verifies; error
  responses never leak the allowlist or token claims.

DB-backed, admin, upload, and auth endpoints always require `get_current_user`.
`/health` is always public. The frontend (`ProtectedRoute` + `isApproved`) mirrors
this for UX, but is **not** the security boundary — the backend is.

Other private-production controls (all env-gated, default off to preserve dev):

- `ENABLE_PUBLIC_DOCS=false` disables `/docs`, `/redoc`, `/openapi.json`.
- `RATE_LIMIT_ENABLED=true` adds in-memory per-identity throttling on expensive
  endpoints (`/research/ask`, `/forecasting/train|inference`, company score/explain;
  `RATE_LIMIT_REQUESTS_PER_MINUTE`, default 60) → 429 on exceed. No Redis.
- `CORS_ALLOW_ORIGINS` pins allowed origins; wildcard auto-disables credentials.
- Frontend: `VITE_ENABLE_GOOGLE_AUTH` / `VITE_ENABLE_SIGNUP` (default off) hide
  Google/signup UI; API cache is cleared on logout and identity change.

## CORS

`CORS_ALLOW_ORIGINS` (comma-separated) configures allowed origins; default `*`
for the demo. Credentials are automatically disabled when `*` is used — auth is
Bearer-token based and needs no cookies. Set explicit origins in production.

## Reporting

This is an academic project, not a production service. Report issues via a GitHub
issue. Do not use it for real investment decisions — outputs are research support,
not investment advice.
