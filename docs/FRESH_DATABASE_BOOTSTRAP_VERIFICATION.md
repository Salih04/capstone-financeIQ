# Fresh-database bootstrap verification

**Status:** PASS — repaired and re-verified on 2026-07-12 against an isolated
local Postgres 16 scratch database. No production, shared, or existing project
database was used.

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

# Required fresh-database sequence.
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

## Repair

The original Alembic graph had no base-application-schema revision. Its first
revision, `20260406_0001_add_forecasting_tables`, referenced `users`, while
later revisions also assumed `users`, `computed_metrics`, and
`sector_normalized_features` already existed. Those tables had historically
come from SQLAlchemy `create_all`, not migration history.

Revision `20260405_0000_add_base_application_schema` now records the
pre-forecast application schema explicitly, and `20260406_0001` points to that
baseline. Inserting a baseline is necessary because an additive revision after
`20260406_0001` could never run before the failing foreign key. The forecast,
onboarding, quarterly-fundamentals, performance-index, and trusted-yearly
revisions remain separate and retain their original order.

## Observed result

The direct migration/load sequence exited `0`. Alembic applied the linear chain
from `20260405_0000` through head `20260406_0006`. The trusted loader then
validated the existing combined CSV and loaded 240 rows: 40 stocks for each year
from 2020 through 2025. It derived 40 company rows from those trusted tickers;
no sector values or other missing values were invented.

```text
Loaded: 240 created, 0 updated, 40 companies synced.
Summary:
  yearly_stocks rows : 240
  years              : [2020, 2021, 2022, 2023, 2024, 2025]
  companies          : 40
    2020: 40 stocks
    2021: 40 stocks
    2022: 40 stocks
    2023: 40 stocks
    2024: 40 stocks
    2025: 40 stocks
```

Running `backend/scripts/start_backend.sh` against the same scratch database
also succeeded. Its idempotent loader result was `0 created, 240 updated`,
Uvicorn reported `Application startup complete`, and an in-container request to
`http://127.0.0.1:8000/health` returned HTTP 200:

```json
{"status":"ok","version":"3.0.0"}
```

| Check | Observed value |
|---|---:|
| Migration head applied | Yes — `20260406_0006` |
| `users` table exists | Yes |
| `yearly_stocks` table exists | Yes |
| `yearly_stocks` rows | 240 |
| `python -m scripts.load_trusted_yearly` | Exit 0 |
| Docker backend boot | Yes |
| `GET /health` | HTTP 200 |

## Additional verification note

`alembic check` found no missing tables or columns after bootstrap. It reports
three existing indexes from revision `20260406_0005` as candidates for removal
because those indexes are not declared in current SQLAlchemy model metadata:
`ix_computed_metrics_company_period`,
`ix_quarterly_fundamentals_stock_period`, and
`ix_sector_normalized_company_period`. That pre-existing model/migration index
drift does not block bootstrap and was not changed in this narrowly scoped
repair.
