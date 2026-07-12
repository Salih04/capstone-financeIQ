# Universe selection and survivorship audit

Audit date: 2026-07-12. Scope: the fixed 40-ticker public universe and the
81-ticker internal training universe used by FinanceIQ. This audit documents
what the repository proves; it does not reconstruct historical index membership
without evidence.

## Conclusion

The repository verifies membership in the **FinanceIQ configured universes**,
not point-in-time BIST100 membership. The 40-ticker cohort first appears in git
on 2026-06-05, after the 2020–2025 study window, and the explicit public-universe
configuration was added on 2026-06-10. No archived constituent lists,
membership-effective dates, delisting/suspension records, or contemporaneous
selection rule are present. The results therefore describe a retrospectively
fixed repository cohort and remain exposed to unresolved survivorship and
universe-selection look-ahead bias; they must not be generalized to the
companies that were actually eligible or in the BIST100 at each historical
date. (Git evidence: commits `fdfc4d717150e7dd91da98de0b40c352b7dcbaf6`
and `12781d4cb7a76047b46faeff9f6c6414733259ca`; configuration evidence:
`data/config/universe_public_40.csv:1-41`.)

## Evidence categories

### Verified FinanceIQ membership

- `data/config/universe_public_40.csv:1-41` defines exactly 40 tickers, each
  flagged for both the public and training universes. The file has no stated
  selection criterion or effective date. The current public modeling artifact
  contains exactly those 40 tickers, 240 rows, and years 2020–2025.
  (`data/trusted_clean/modeling_dataset_public_2020_2025.csv`.)
- `data/config/universe_training_bist100.csv:19-102` defines 81 training
  tickers: the public 40 plus 41 training-only names. The current training
  modeling artifact contains the same 81 tickers and 403 rows.
  (`data/trusted_clean/modeling_dataset_training_2020_2025.csv`.)
- The generated split audit independently reports 40 public, 81 training, 41
  training-only, no configured tickers missing from either output, no
  non-public tickers in the public output, and `validation_passed: true`.
  (`data/trusted_clean/universe_split_report.json:2-17`.)

These facts verify internal configuration and split integrity only. A row for a
ticker-year does not by itself prove that the security was listed, trading, or
an index constituent in that year.

### Repository-snapshot proxies, not historical membership

- The pipeline bootstraps the company universe from distinct ticker/`indices`
  pairs in the legacy `data/trusted/stocks_2020_2025.csv` and sets
  `is_bist100` by testing whether the undated `indices` text contains `XU100`.
  The code does not load a membership-effective date or a point-in-time
  constituent table. (`scripts/data_collection/pipeline.py:109-147`.)
- In that legacy file, all 40 tickers have one unchanged `indices` string across
  all six rows and all 240 rows contain `XU100`. That repetition is consistent
  with one repository snapshot copied across years; it is not evidence that all
  40 were constituents in every year. (`data/trusted/stocks_2020_2025.csv`;
  the file is explicitly treated as an unreliable reference in
  `scripts/data_collection/pipeline.py:7-16`.)
- The expansion candidate file explicitly describes itself as a static,
  manually curated list based on a "2024-2025 reference" and says its names are
  not in the public 40. It can support a current/recent-universe proxy only, not
  historical membership. (`data/config/bist100_candidates.csv:1-6`.)
- The training-only additions are sourced from unofficial yfinance financials,
  have FY2022+ coverage, and require a KAP cross-check. Their presence in the
  training config is therefore verified, but historical BIST100 membership is
  not. (`data/config/universe_training_bist100.csv:16-18,60-102`.)

### Git timing

| Evidence | First repository record | What it establishes |
|---|---|---|
| Base 40-ticker `company_universe.csv` | `fdfc4d717150e7dd91da98de0b40c352b7dcbaf6`, 2026-06-05 | The cohort existed in this repository by that commit; the commit message says the pipeline produced 240 rows / 40 inference rows. It does not state how the 40 were chosen. |
| Explicit public/training configs | `12781d4cb7a76047b46faeff9f6c6414733259ca`, 2026-06-10 | The 40-name public split became explicit; the commit says the initial public and training outputs were identical. |
| Nine training-only pilot names | `dcff51302af161c9df5919b6367a2dd7469f2da4`, 2026-06-10 | Training expanded to 49 without changing the public 40. |
| Static expansion-candidate file | `e452c663eb0f38b0612057d30f61ada0b9714969`, 2026-06-10 | A manually curated 2024–2025-reference candidate proxy was recorded. |
| Final 81-name training config | `6dcd210a7101b11f3bb1b1710e245a1c670f254d`, 2026-06-10 | Training expanded to 81 without changing the public 40. |

`git log --follow` shows no later membership change to
`data/config/universe_public_40.csv`; `git diff` against its introduction is
empty. This proves configuration stability only from 2026-06-10 onward, not
pre-specification before the 2020 study start.

## Price-coverage check against committed data

The committed Yahoo price file has 226 available public-universe ticker-years
out of 240 (94.2%). Thirty-five of the 40 public tickers have coverage for all
six years. The 14 missing observations are:

| Public ticker | Missing years |
|---|---|
| ASTOR | 2020, 2021, 2022 |
| CANTE | 2020 |
| DSTKF | 2020, 2021, 2022, 2023, 2024 |
| MIATK | 2020 |
| PASEU | 2020, 2021, 2022, 2023 |

These counts were checked row by row against
`data/trusted_raw/prices/yahoo_year_end_prices.csv` and agree with the public
rows' `price_data_available` flags in
`data/trusted_clean/modeling_dataset_public_2020_2025.csv`. The fetch report
labels the observations as retry failures; it does not identify IPO dates,
delistings, suspensions, symbol changes, or non-membership
(`data/trusted_raw/prices/yahoo_year_end_prices_report.md:3-38`). Therefore:

- incomplete price coverage disproves any claim that the repository has a
  complete observed 2020–2025 price panel for all 40 names;
- it does **not** prove why an observation is missing; and
- complete Yahoo price coverage would prove trading-price availability, not
  BIST100 constituent membership.

The public modeling artifact still contains 240 ticker-year rows and 200 target
rows because the company universe and realized-return targets are bootstrapped
from the legacy reference path (`scripts/data_collection/pipeline.py:109-147`).
Those row counts must not be used as listing-history evidence.

## Missing evidence and unresolved limitations

The repository cannot answer the following without new, sourced historical
records:

- the exact rule and decision date used to choose the original 40 names;
- BIST100 inclusion/removal effective dates for any public or training ticker;
- which companies were listed, delisted, suspended, renamed, or otherwise
  eligible in each year from 2020 through 2025;
- whether excluded, failed, or unavailable companies differ systematically from
  the retained cohort; or
- how results change under a true point-in-time, entry/exit-aware universe.

No inference has been made for these gaps. A future remediation would require a
sourced, dated constituent and security-status history with effective intervals;
until then, missing membership stays unknown rather than being filled from the
current/recent proxy.

## Reproduction checks used for this audit

```bash
git log --follow --date=iso-strict -- data/config/universe_public_40.csv
git log --follow --date=iso-strict -- data/config/universe_training_bist100.csv
git log --follow --date=iso-strict -- data/config/bist100_candidates.csv
git log --follow --date=iso-strict -- data/trusted_raw/company_universe.csv
git diff 12781d4cb7a76047b46faeff9f6c6414733259ca..HEAD -- data/config/universe_public_40.csv
```

The row-level cross-check parsed the two universe configs, the Yahoo year-end
price CSV, both modeling split CSVs, `company_year_returns.csv`, and
`universe_split_report.json`; it compared ticker sets, years, flags, row counts,
and non-null `year_end_close` / `price_data_available` values. No source or data
artifact was changed.
