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
   confirmations if reviewers should verify accounts before entry.
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
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
SUPABASE_JWT_AUDIENCE=authenticated
SUPABASE_AUTO_CREATE_USERS=true
```

`SUPABASE_JWT_SECRET` belongs only on the backend. Do not expose it in Vite or
Vercel frontend variables.

Current verifier supports Supabase symmetric JWT secrets. If a project uses
asymmetric signing keys, add JWKS verification before relying on backend API
protection.

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
