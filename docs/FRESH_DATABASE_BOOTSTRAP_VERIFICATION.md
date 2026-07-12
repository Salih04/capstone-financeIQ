# Fresh-database bootstrap verification

**Status:** BLOCKED — verified on 2026-07-12 against an isolated local Postgres
16 scratch database. No production, shared, or existing project database was
used.

## Scope

This record tests the documented bootstrap order:

1. start an empty Postgres database;
2. run `alembic upgrade head`;
3. run `python -m scripts.load_trusted_yearly`;
4. boot the backend.

The trusted-data loader remains the only load path. It validates the trusted CSV
before writing, preserves missing values as null, and derives company rows
without inventing sectors. This check makes no claim about returns, predictive
skill, or investment advice.

## Isolated scratch database commands

The normal host port `5432` was already occupied by the existing local Compose
stack, so the scratch service was started with its host port removed. The
database remained reachable to the Compose backend over the private
`financeiq-be02_default` network.

```bash
# The project name gives the test its own volume: financeiq-be02_postgres_data.
printf 'services:\n  db:\n    ports: !reset []\n' | \
  docker compose -p financeiq-be02 -f docker-compose.yml -f - up -d db

docker compose -p financeiq-be02 build backend

# Required fresh-database sequence (failed at the migration step; see below).
docker compose -p financeiq-be02 run --rm --no-deps backend \
  sh -lc 'alembic upgrade head && python -m scripts.load_trusted_yearly'

# Test the repository's Docker startup path directly.
docker compose -p financeiq-be02 run --rm --no-deps backend \
  sh scripts/start_backend.sh

# Inspect the scratch database only.
docker compose -p financeiq-be02 exec -T db psql -U postgres -d capstone_db -c \
  "SELECT to_regclass('public.alembic_version'),\
          to_regclass('public.yearly_stocks'),\
          to_regclass('public.users');"

# Roll back the scratch database and its isolated volume.
docker compose -p financeiq-be02 down -v
```

## Observed result

Both the direct sequence and `backend/scripts/start_backend.sh` exited `1` at
the first Alembic migration, `20260406_0001_add_forecasting_tables`.

```text
psycopg2.errors.UndefinedTable: relation "users" does not exist
...
CREATE TABLE forecast_runs (...,
    FOREIGN KEY(created_by_user_id) REFERENCES users (id))
```

The migration chain's initial revision creates `forecast_runs` with a foreign
key to `users`, but no preceding migration creates the `users` table. PostgreSQL
rolls the failed DDL back: after the run, `alembic_version`, `yearly_stocks`, and
`users` were all absent.

| Check | Observed value |
|---|---:|
| Migration head applied | No — stops at `20260406_0001` |
| `yearly_stocks` table exists | No |
| `yearly_stocks` rows | Not reached (table absent) |
| `python -m scripts.load_trusted_yearly` | Not run (guarded by failed `&&` migration command) |
| Docker backend boot | No — startup script exits during Alembic |

## Required follow-up

Fresh-database bootstrap cannot be marked working until the Alembic history can
create the base application schema before migrations that reference `users`.
This BE-02 task intentionally does not add or alter migrations. After that
separate migration repair, rerun this exact scratch procedure and record the
actual `yearly_stocks` row count plus a successful backend `/health` response.
