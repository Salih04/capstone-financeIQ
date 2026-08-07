# Per-cell provenance — public modeling dataset (passports v2)

- Task: `R4-PROV-01`
- Provenance schema version: `2.0.0`
- Dataset: `data/trusted_clean/modeling_dataset_public_2020_2025.csv`
- Records: `data/provenance/cell_provenance_public_2020_2025.csv`
- Coverage: 14640 cells = 240 rows x 61 columns (13682 present, 958 null)

> Lineage record only. This artifact states where each dataset value was copied or computed from and how strong that evidence is. It certifies nothing about point-in-time correctness, data-rights clearance, source accuracy, completeness, predictive validity, causal validity, statistical significance, or investment usefulness, and it is not investment advice. The project's walk-forward finding (no reliable predictive edge) is unchanged by this artifact.

## Evidence level

| evidence_level | cells | meaning |
|---|---|---|
| `cell_verified` | 8243 | The dataset value was compared against a specific (source_artifact, source_field, ticker, year) upstream value and matched under the recorded value-equality rule. Strongest available evidence. |
| `column_asserted` | 3715 | No cell-level upstream source file carries this field; provenance is inherited from the passports-v1 column assertion. Weaker than cell_verified and labelled as such. |
| `derived_chain` | 2640 | The value is a deterministic function of the named upstream_cells of this same dataset. Provenance is the chain, not a copied source value. |
| `unknown` | 42 | No source could be verified and no chain asserted. Always carries a resolution_note. |

## Source class

| source_class | cells |
|---|---|
| `corrected_balance_2024` | 434 |
| `corrected_yearly_csv` | 2398 |
| `derived` | 5520 |
| `metadata` | 2160 |
| `unknown` | 42 |
| `vendor_xlsx` | 3606 |
| `yahoo_fetch` | 480 |

## Transformation

| transform_id | cells | meaning |
|---|---|---|
| `T_COPY` | 5496 | Value copied unchanged from source_artifact.source_field at the same (ticker, year). |
| `T_METADATA` | 1920 | Identifier, cohort, or row-state metadata assignment. |
| `T_NULL_PRESERVED` | 958 | The cell is null and was never filled; the pipeline's no-imputation contract is the provenance. |
| `T_OVERRIDE_2024` | 434 | Value taken from the reviewed 2024 balance-sheet override in preference to the vendor snapshot. |
| `T_PRICE_WINDOW` | 1197 | Price momentum, drawdown, or history count computed over a T-bounded price window. |
| `T_RANK_WITHIN_YEAR` | 800 | Rank, percentile, or flag computed within the target year. |
| `T_RATIO` | 3153 | Deterministic arithmetic on named upstream cells (valuation ratios, margins, excess return). |
| `T_SHIFT_T1` | 640 | Outcome from year T+1 shifted back onto feature year T. |
| `T_UNRESOLVED` | 42 | No transformation could be established. |

## Resolution notes

| resolution_note | cells | meaning |
|---|---|---|
| `(empty)` | 8243 | cell_verified with a single candidate source |
| `column_asserted_no_cell_source` | 3120 | No upstream file carries this field at cell granularity. |
| `derived_from_dataset_cells` | 2277 | Value is computed from the named upstream_cells. |
| `null_preserved` | 958 | Cell is null; no value was ever filled. |
| `value_unparseable` | 42 | The dataset or upstream value could not be parsed for comparison (includes empty upstream fields). |

## Verified source artifacts

| source_artifact | cells verified |
|---|---|
| `(none)` | 6397 |
| `data/trusted_clean/company_year_returns.csv` | 1480 |
| `data/trusted_raw/bist100_benchmark_returns.csv` | 226 |
| `data/trusted_raw/financials/candidate_from_yearly_snapshots.csv` | 2406 |
| `data/trusted_raw/financials/corrected_balance_sheet_2024.csv` | 434 |
| `data/trusted_raw/financials/corrected_yearly_financials_candidate.csv` | 2398 |
| `data/trusted_raw/financials/free_valuation_history_candidate.csv` | 1073 |
| `data/trusted_raw/prices/yahoo_year_end_prices.csv` | 226 |

## Unknown provenance

42 cells could not be attributed to any candidate source and are recorded as `unknown` with a mandatory reason code. They are reported, never repaired: no dataset value was changed and no tolerance was widened.

| column | unknown cells |
|---|---|
| `financial_debt_ratio` | 40 |
| `operating_income` | 1 |
| `roe` | 1 |

Complete list (also in the JSON report as `unknown_cells`):

```
AEFES|2024|financial_debt_ratio
ARCLK|2024|financial_debt_ratio
ASELS|2024|financial_debt_ratio
ASTOR|2024|financial_debt_ratio
BIMAS|2024|financial_debt_ratio
BRSAN|2024|financial_debt_ratio
BTCIM|2024|financial_debt_ratio
CANTE|2024|financial_debt_ratio
CCOLA|2024|financial_debt_ratio
CIMSA|2024|financial_debt_ratio
DOAS|2024|financial_debt_ratio
DSTKF|2024|financial_debt_ratio
ENKAI|2024|financial_debt_ratio
EREGL|2024|financial_debt_ratio
FROTO|2024|financial_debt_ratio
GUBRF|2024|financial_debt_ratio
HEKTS|2024|financial_debt_ratio
KONTR|2024|financial_debt_ratio
KRDMD|2024|financial_debt_ratio
KUYAS|2024|financial_debt_ratio
MAVI|2024|financial_debt_ratio
MGROS|2020|roe
MGROS|2024|financial_debt_ratio
MIATK|2024|financial_debt_ratio
OYAKC|2024|financial_debt_ratio
PASEU|2024|financial_debt_ratio
PETKM|2024|financial_debt_ratio
PGSUS|2024|financial_debt_ratio
SASA|2024|financial_debt_ratio
SISE|2024|financial_debt_ratio
TAVHL|2024|financial_debt_ratio
TCELL|2024|financial_debt_ratio
THYAO|2024|financial_debt_ratio
TOASO|2024|financial_debt_ratio
TRALT|2024|financial_debt_ratio
TRALT|2024|operating_income
TRMET|2024|financial_debt_ratio
TSKB|2024|financial_debt_ratio
TTKOM|2024|financial_debt_ratio
TUPRS|2024|financial_debt_ratio
TURSG|2024|financial_debt_ratio
ULKER|2024|financial_debt_ratio
```

## Multiple candidate sources

0 cells were verified by more than one candidate source; the frozen source priority selected one and the record carries `multi_candidate_priority_applied`. Selection is never silent.

## Query examples

Which cells came from the reviewed 2024 balance-sheet override:

```bash
awk -F, 'NR==1 || $6=="corrected_balance_2024"' data/provenance/cell_provenance_public_2020_2025.csv
```

Which cells have no verified source:

```bash
awk -F, 'NR==1 || $7=="unknown"' data/provenance/cell_provenance_public_2020_2025.csv
```

Provenance of one cell:

```bash
grep '^AEFES|2024|total_assets,' data/provenance/cell_provenance_public_2020_2025.csv
```

## Caveats

- cell_verified means the dataset value equals a specific upstream value under the recorded equality rule; it does not mean the upstream value is correct.
- column_asserted records inherit passports-v1 column-level provenance because no upstream file carries the field at cell granularity; they are strictly weaker than cell_verified and were never upgraded by inference.
- unknown records are reported, never repaired: no dataset value was changed, no tolerance was widened, and no nearest candidate was substituted.
- Null cells are recorded as preserved nulls. The pipeline never imputes; for null cells source_class names the column's declared source family rather than a verified attribution, and evidence_level plus resolution_note carry the honesty.
- Lineage depth is bounded at the nearest upstream artifact at which a value was verified, plus intra-dataset upstream_cells. No deeper materialized evidence exists in this repository, and none was invented.
- Scope is exactly the 240-row x 61-column public modeling dataset. The full and training datasets, external markets, and experiment outputs are out of scope.
- The manual-shares component of the upstream valuation inputs is not attributed at cell level by this artifact; valuation cells are recorded against the valuation candidate file they were verified against.
