# DATA-01 — Data dictionary cross-check

Audit date: 2026-07-12

## Scope

Compared the header of `data/trusted_clean/modeling_dataset_2020_2025.csv`
with `data/trusted_clean/data_dictionary.md` and with the roles produced by
`scripts.data_collection.validate.feature_registry`.

## Drift found

- Dataset columns: **61**
- Dictionary entries before regeneration: **58**
- Missing dictionary entries:
  - `is_public_universe`
  - `is_training_universe`
  - `universe_source`
- Stale dictionary entries naming columns absent from the dataset: **none**
- Duplicate dictionary entries: **none**

All three missing columns are universe metadata. Their correct registry role is
`metadata` and their leakage risk is `none`; they are not predictive features.

## Cause and correction

`build_all` generated the dictionary while building the 40-ticker base dataset.
The later training-universe integration added the three metadata columns, while
`make data-validate` validated the final dataset without regenerating the
dictionary.

`scripts/data_collection/build_all.py` now generates the dictionary from the
loaded dataset in both build and `--validate-only` modes. Running
`make data-validate` therefore refreshed the generated dictionary from the
actual 403-row final dataset; no trusted CSV data was hand-edited.

## Final cross-check

- Dataset columns: **61**
- Dictionary entries: **61**
- Missing entries: **none**
- Stale entries: **none**
- Role or leakage-risk mismatches against `feature_registry`: **none**
- Validation: **VALID** — 403 rows, 40 features, 321 target rows, 82
  inference-only rows, benchmark available

The no-fabrication, no-imputation, and T→T+1 leakage boundaries are unchanged.
