from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


with DAG(
    dag_id="forecasting_retrain_daily",
    start_date=datetime(2026, 4, 1),
    schedule="0 3 * * *",
    catchup=False,
    tags=["forecasting", "retrain"],
) as dag:
    run_retrain = BashOperator(
        task_id="run_forecasting_retrain",
        bash_command="cd /opt/app/backend && python scripts/retrain_forecasting.py",
    )

    run_retrain
