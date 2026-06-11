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

## Intentionally public endpoints

Read-only research endpoints (`/research/*`) and the CSV-backed forecasting
endpoints (`/forecasting/options|train|run|explain|inference`) use the
`optional_user` dependency and are **public by design** for the demo. They serve
only validated, already-public BIST research data and never mutate state. DB-backed,
admin, upload, and auth endpoints remain authenticated (`get_current_user`).

## CORS

`CORS_ALLOW_ORIGINS` (comma-separated) configures allowed origins; default `*`
for the demo. Credentials are automatically disabled when `*` is used — auth is
Bearer-token based and needs no cookies. Set explicit origins in production.

## Reporting

This is an academic project, not a production service. Report issues via a GitHub
issue. Do not use it for real investment decisions — outputs are research support,
not investment advice.
