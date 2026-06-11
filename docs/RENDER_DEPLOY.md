# Render Deploy

FinanceIQ backend lives in `backend/`. Do not use any retired numbered backend
folder in Render settings.

## Manual Render Settings

Create a Web Service from this repository:

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
