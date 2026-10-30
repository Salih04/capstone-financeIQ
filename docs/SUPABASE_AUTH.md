# Supabase Auth Setup

FinanceIQ uses Supabase Auth only for frontend session management. The ML/data
pipeline stays local and unchanged.

## Frontend Environment

Create `frontend/.env.local`:

```bash
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-or-publishable-key
VITE_SUPABASE_AUTH_REDIRECT_URL=http://localhost:5173/auth/callback
```

Do not use the Supabase service-role key in frontend env.

## Supabase Dashboard

1. Create a Supabase project.
2. Authentication -> Providers -> Email: enable email/password. Enable email
   confirmations if reviewers should verify accounts before entry. The backend
   cannot see this setting: a private deployment with `APPROVED_EMAILS` admits
   Supabase users only after you confirm it is on and set
   `SUPABASE_EMAIL_CONFIRMATION_ENFORCED=true` (see `SECURITY.md`).
3. Authentication -> Providers -> Google: enable provider, add Google OAuth
   client ID and client secret.
4. Authentication -> URL Configuration:
   - Site URL for local Vite: `http://localhost:5173`
   - Local Docker frontend: `http://localhost:3000`
   - Production Site URL: `https://your-production-frontend`
   - Redirect URLs:
     - `http://localhost:5173/auth/callback`
     - `http://localhost:3000/auth/callback`
     - `https://your-production-frontend/auth/callback`
   - After changing Site URL or redirect URLs, send a fresh confirmation or
     password-recovery email. Old localhost confirmation links keep their old
     redirect target and should not be reused for production verification.
5. Google Cloud OAuth client:
   - Authorized JavaScript origins:
     - `http://localhost:5173`
     - `http://localhost:3000`
     - `https://your-production-frontend`
   - Authorized redirect URI:
     - Supabase callback URL from the Google provider panel.

## Backend Compatibility

Existing FastAPI endpoints still use `get_current_user`. Legacy `/auth/login`
JWTs continue to work for tests. To let Supabase-authenticated frontend sessions
call protected backend endpoints, set backend env:

```bash
SUPABASE_URL=https://your-project-ref.supabase.co
# SUPABASE_JWT_SECRET=your-supabase-jwt-secret  # only for legacy HS256 tokens
SUPABASE_JWT_AUDIENCE=authenticated
SUPABASE_AUTO_CREATE_USERS=false
SUPABASE_IDENTITY_BINDINGS={}
```

`SUPABASE_JWT_SECRET` belongs only on the backend. Do not expose it in Vite or
Vercel frontend variables.

The verifier supports asymmetric signing keys through the configured project's
JWKS and legacy HS256 secrets. Both signatures and the configured issuer must
verify before an exact immutable subject resolves through the explicit local
binding map. An empty map denies Supabase backend authentication. Email equality
never links users, and the deprecated auto-create flag has no effect. Existing
local accounts and their roles are not migrated or promoted by requests.

Before rollout, the owner must approve proof of each issuer/subject/local-id
binding and provisioning/first-admin arrangements. Do not populate mappings
from email matches, user-editable metadata, or unverified browser claims.
The [candidate runbook](SECURITY_REMEDIATION_2026-10-28.md) describes collision,
legacy-account, revocation and rollback constraints. No live mappings were
created by this change.

## Local Run

```bash
cd backend
cp .env.example .env
uvicorn app.main:app --reload --port 8000

cd ../frontend
cp .env.example .env.local
npm install
npm run dev
```

Open `http://localhost:5173/login`.
