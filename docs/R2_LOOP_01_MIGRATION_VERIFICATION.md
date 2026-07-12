# R2-LOOP-01 scratch migration verification

**Status:** PASS — revision `20260713_0007` applied from an empty Postgres 16
database on 2026-07-13. The isolated Compose project and volume were removed
after inspection. No production, shared, or existing project database was used.

## Commands

```bash
printf 'services:\n  db:\n    ports: !reset []\n' | \
  docker compose -p financeiq-r2-loop-01 -f docker-compose.yml -f - up -d db

docker compose -p financeiq-r2-loop-01 run --rm --no-deps backend \
  alembic upgrade head

docker compose -p financeiq-r2-loop-01 exec -T db \
  psql -U postgres -d capstone_db \
  -c "SELECT version_num FROM alembic_version;" \
  -c "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema='public' AND table_name='analyst_verdicts' ORDER BY ordinal_position;" \
  -c "SELECT conname, contype, pg_get_constraintdef(oid) AS definition FROM pg_constraint WHERE conrelid='public.analyst_verdicts'::regclass ORDER BY conname;" \
  -c "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname='public' AND tablename='analyst_verdicts' ORDER BY indexname;"

docker compose -p financeiq-r2-loop-01 run --rm --no-deps backend alembic check
docker compose -p financeiq-r2-loop-01 down -v
```

## Observed result

- `alembic upgrade head` exited `0` and applied the complete linear history
  through `20260713_0007`.
- `analyst_verdicts` has the required eight columns: `id`, `ticker`, `year`,
  `verdict`, `reason_type`, nullable `note`, `user_id`, and `created_at`.
- Both enum-like fields have named database check constraints. Verdict accepts
  only `agree`, `disagree`, or `abstain`; reason type accepts only
  `evidence_quality`, `data_gap`, `methodology`, `model_instability`, or `other`.
- The `user_id → users.id` foreign key and composite `(ticker, year)` index exist.
- No generated research artifact or trusted dataset is owned or modified by
  this migration.

`alembic check` reached metadata comparison and reported only the three
pre-existing index-removal candidates already documented by BE-02:
`ix_computed_metrics_company_period`,
`ix_quarterly_fundamentals_stock_period`, and
`ix_sector_normalized_company_period`. It reported no drift for
`analyst_verdicts`. Fixing the older index metadata is outside R2-LOOP-01.

## Rollback boundary

Before a commit, the migration and table can be removed with the rest of this
task's uncommitted changes. After a migration is shipped, rollback must use a
new follow-up migration; editing the applied revision or relying on source-code
revert alone is not sufficient.
