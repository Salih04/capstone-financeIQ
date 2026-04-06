# Forecasting Operations

## Migrations

Run forecasting schema migrations:

```bash
cd backend
alembic upgrade head
```

## Scheduled Retraining (MVP)

Run manual retraining job (can be triggered by cron):

```bash
cd backend
python scripts/retrain_forecasting.py
```

Example cron (daily 03:00):

```bash
0 3 * * * cd /path/to/Capstone_Code/backend && /usr/bin/python3 scripts/retrain_forecasting.py >> retrain.log 2>&1
```

This job:

- uses latest available year from imported winner data,
- retrains sector parameter rankings,
- produces fresh forecast runs per sector.

## Incremental Retraining

Run only when a newer data year arrives:

```bash
cd backend
python scripts/incremental_retrain.py
```

## Airflow (optional)

An Airflow DAG template is provided at:

`backend/airflow/dags/forecasting_retrain_dag.py`

Point your Airflow `dags_folder` to include this path and adjust `bash_command` to your deployment path.
