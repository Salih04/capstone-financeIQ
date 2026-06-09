#!/bin/sh
set -eu

attempt=1
max_attempts="${DB_WAIT_ATTEMPTS:-30}"
migration_state=""

echo "Waiting for database..."
until migration_state="$(python -m scripts.migration_state)"; do
  if [ "$attempt" -ge "$max_attempts" ]; then
    echo "Database unavailable after ${max_attempts} attempts."
    exit 1
  fi
  echo "Database unavailable; retry ${attempt}/${max_attempts}..."
  attempt=$((attempt + 1))
  sleep 2
done

if [ "${RUN_DB_MIGRATIONS:-1}" = "1" ]; then
  if [ "$migration_state" = "stamp" ]; then
    echo "Existing schema without Alembic version detected; stamping head."
    alembic stamp head
  fi

  echo "Running Alembic migrations..."
  alembic upgrade head
else
  echo "Skipping Alembic migrations because RUN_DB_MIGRATIONS=${RUN_DB_MIGRATIONS}."
fi

if [ "${LOAD_TRUSTED_DATA:-1}" = "1" ]; then
  echo "Loading trusted yearly data..."
  python -m scripts.load_trusted_yearly
else
  echo "Skipping trusted yearly data load because LOAD_TRUSTED_DATA=${LOAD_TRUSTED_DATA}."
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
