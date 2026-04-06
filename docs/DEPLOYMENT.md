# Deployment Automation Roadmap (MVP+)

## What is included now

- Dockerized app (`docker-compose.yml`)
- Infrastructure starter folders:
  - `infra/aws/`
  - `infra/azure/`
  - `infra/gcp/`
- AWS Terraform starter in `infra/aws/main.tf`

## Recommended CI/CD pipeline

1. Build backend and frontend images
2. Run backend compile checks and frontend build checks
3. Apply DB migrations (`alembic upgrade head`)
4. Deploy to target cloud environment
5. Trigger post-deploy smoke tests (`/health`, key forecasting endpoints)

## Environment variables (minimum)

- `DATABASE_URL`
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`

## Incremental and scheduled learning in production

- Batch retrain: `python scripts/retrain_forecasting.py`
- Incremental retrain: `python scripts/incremental_retrain.py`
- Airflow DAG template: `backend/airflow/dags/forecasting_retrain_dag.py`

## Next automation step

- Add GitHub Actions workflow for test/build/deploy per cloud target.
