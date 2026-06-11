# Render Deploy

FinanceIQ backend lives in `backend/`. Do not use any retired numbered backend
folder in Render settings. A `render.yaml` Blueprint is now present at repo root
and will configure new Render services automatically.

## CRITICAL: Stale Render Dashboard Setting

**Pushing code cannot fix a Root Directory already saved in the Render
Dashboard.** If your existing Render service was created with Root Directory set
to `2.backend` (or any retired path), that value lives in the Render UI and must
be changed manually — `render.yaml` only controls *new* services created via the
Blueprint flow.

### Fix an existing service manually

1. Open the Render Dashboard → your `financeiq-backend` service → **Settings**.
2. Under **Build & Deploy**, update:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Click **Save Changes**.
4. Then click **Manual Deploy → Clear build cache & deploy** to force a clean
   rebuild from the correct path.

## New Service via Blueprint

To create a new service that picks up `render.yaml` automatically, click
**New → Blueprint** in Render and point it at this repo. The Blueprint will
configure Root Directory, build/start commands, and env var stubs.

## Manual Render Settings (reference)

If not using the Blueprint, create a Web Service from this repository with:

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Use the native Python runtime. The frontend deploys separately on Vercel.

## Environment Variables

Required:

```bash
DATABASE_URL=postgresql://...
SECRET_KEY=replace-with-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

Recommended data path variables when Render runs from `backend/`:

```bash
TRUSTED_DATASETS_DIR=../data/raw/yearly_xlsx
TRUSTED_OUT_DIR=../data/trusted
TRUSTED_COMBINED_CSV=../data/trusted/stocks_2020_2025.csv
RESEARCH_REPO_ROOT=..
```

Optional research-agent / auth compatibility:

```bash
RESEARCH_LLM_PROVIDER=none
OPENROUTER_API_KEY=
OPENAI_API_KEY=
SUPABASE_JWT_SECRET=
SUPABASE_JWT_AUDIENCE=authenticated
SUPABASE_AUTO_CREATE_USERS=true
```

Do not commit `.env` files or service-role keys.

## Health Check

After deploy:

```bash
curl https://your-render-service.onrender.com/health
```

Then set Vercel `VITE_API_URL` to the Render backend URL.
