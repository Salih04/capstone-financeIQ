# Render Deploy

FinanceIQ backend lives in `backend/`. Do not use any retired numbered backend
folder in Render settings.

The committed `render.yaml` Blueprint deploys the backend with the **Docker**
runtime using the repo root as build context. The `backend/Dockerfile` copies
`backend/`, `data/`, `experiments/`, and `research_agent_training/` from the repo
root, so the build context **must** be the repo root.

## Option A — Blueprint (recommended)

Point Render at this repo and let it read `render.yaml`. It provisions a free
Postgres database and the Docker web service with all required env vars.

## Option B — Manual Docker Web Service

Create a Web Service from this repository with the **Docker** runtime:

```text
Root Directory:                 (empty / repo root)
Dockerfile Path:                backend/Dockerfile
Docker Build Context Directory: .
Docker Command:                 (blank — Dockerfile CMD honors $PORT)
```

### Wrong settings (these break the build)

- `Root Directory: backend` + `Dockerfile Path: backend/Dockerfile`
  → resolves to `backend/backend/Dockerfile` (not found).
- `Docker Build Context Directory: backend`
  → `COPY data/ ...`, `COPY experiments/ ...`, `COPY research_agent_training/ ...` fail.

## Environment Variables

Required:

```bash
DATABASE_URL=postgresql://...        # from the Render Postgres instance
SECRET_KEY=replace-with-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

Data path resolution inside the container (Dockerfile already sets these; keep
them if overriding):

```bash
RESEARCH_REPO_ROOT=/app
TRUSTED_DATASETS_DIR=/app/data/raw/yearly_xlsx
TRUSTED_OUT_DIR=/app/data/trusted
TRUSTED_COMBINED_CSV=/app/data/trusted/stocks_2020_2025.csv
```

Optional research-agent / auth compatibility:

```bash
RESEARCH_LLM_PROVIDER=none           # or openrouter / openai / lmstudio / ollama
OPENROUTER_API_KEY=
OPENAI_API_KEY=
SUPABASE_JWT_SECRET=
SUPABASE_JWT_AUDIENCE=authenticated
SUPABASE_AUTO_CREATE_USERS=true
```

Do not commit `.env` files or service-role keys.

## Private production lockdown (optional)

Defaults serve the open read-only demo. To restrict to approved, owner-created
users, set on the Render service:

```bash
PUBLIC_DEMO_MODE=false
REQUIRE_APPROVED_USER=true
APPROVED_EMAILS=owner@example.com,teammate@example.com
SUPABASE_URL=https://<project-ref>.supabase.co   # REQUIRED — JWKS verification of Supabase JWT Signing Keys
# SUPABASE_JWT_SECRET=<legacy HS256 secret>        # only if the project still issues HS256 tokens
ENABLE_PUBLIC_DOCS=false
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
CORS_ALLOW_ORIGINS=https://capstone-finance-iq.vercel.app
```

New Supabase projects sign access tokens with asymmetric **JWT Signing Keys**
(RS256/ES256); the backend verifies them against the project JWKS derived from
`SUPABASE_URL`. In private mode with neither `SUPABASE_URL` (JWKS) nor a matching
`SUPABASE_JWT_SECRET` the backend cannot verify tokens and denies all access
(fail closed). Empty `APPROVED_EMAILS` with `REQUIRE_APPROVED_USER=true` also
denies all. `/health` stays public.

## Note on native Python deploys

If you instead use Render's native Python runtime (`Root Directory: backend`,
`Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT`), do **not**
also set a Dockerfile — pick one strategy. With native Python from `backend/`,
set `RESEARCH_REPO_ROOT=..` and the `TRUSTED_*` paths relative to `backend/`.
The repo-root resolver (`backend/app/core/paths.py`) honors `RESEARCH_REPO_ROOT`
first, so either strategy works as long as the data tree is reachable.

## Health Check

After deploy:

```bash
curl https://your-render-service.onrender.com/health
curl https://your-render-service.onrender.com/research/runtime-status
```

`/research/runtime-status` reports loaded dataset rows/tickers, company-context
count, and any missing required files — use it to confirm the Docker image
shipped the `data/` tree. Then set Vercel `VITE_API_URL` to the Render backend URL.
