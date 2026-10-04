# Availability-aware point-in-time evaluation protocol (PIT-v2)

**Status:** post-hoc protocol, registered by
[`PREREGISTRATION_AMENDMENT_2026-10-04.md`](PREREGISTRATION_AMENDMENT_2026-10-04.md)
before any PIT-v2 outcome was computed. Implementation:
[`experiments/pit/`](../experiments/pit/), runner
[`experiments/pit_v2_evaluation.py`](../experiments/pit_v2_evaluation.py),
results [`experiments/results_pit_v2/`](../experiments/results_pit_v2/).

## 1. Principle

A feature's timestamp is the moment the underlying information became public,
not the end of the period it describes. A value may score a company only if it
was public before the prediction time, and the return it is scored against
starts after that. Availability is computed from recorded timestamps and
checked by code; names such as `lagged_` carry no weight.

The published design assumed that fiscal-year-T statements are known on
31 December T. They are not: Turkish listed companies file them up to 70 days
later in a normal year and up to 141 days later (20 May 2024) for FY2023
([audit](audit/PUBLICATION_LAG_AUDIT.md)).

## 2. Two availability modes, never mixed

| Mode | Statement `available_at` | Use |
| --- | --- | --- |
| `ACTUAL_FILING_DATE` | 23:59:59 Istanbul on the verified date the annual report was public ([`filing_dates_sample.csv`](../data/pit/filing_dates_sample.csv)) | Implemented and tested. Rows without a verified date are unavailable; there is no fallback. Coverage is 6 of 323 evaluable company-years, so this mode is **not** run on the full universe |
| `STANDARDIZED_CONSERVATIVE_CUTOFF` | 23:59:59 Istanbul on the statutory filing deadline for that fiscal year ([`reporting_deadlines.csv`](../data/pit/reporting_deadlines.csv)); a ticker-specific extension overrides the general row | Canonical full-universe evaluation |

Exact filing timestamps were not recovered for the whole universe: KAP has no
documented bulk export, and the project forbids scraper code
([agent rules](process/AGENTS.md)). The standardized mode is therefore the
canonical result and is labelled as such everywhere.

## 3. Choosing the standardized cutoff

The cutoff is the calendar date after whose close all fiscal-year-T statements
are treated as public. It was validated against regulatory deadlines and
dated sample filings before any outcome was computed.

| Fiscal year | Latest statutory deadline (listed companies) | Source |
| --- | --- | --- |
| 2019–2022, 2024, 2025 | 10–13 March of T+1 (70 days, consolidated) | SPK II-14.1 art. 10; FY2024 confirmed by MKK General Letter 1000 |
| 2022, SASA only | **10 May 2023** (earthquake-region extension) | MKK General Letter 971, Ek-1 |
| 2023 (first TMS 29 year) | **20 May 2024** (consolidated), 9 May 2024 (solo) | MKK General Letter 1000 attachment, SPK decision 81/1820 |

**An end-of-March cutoff is not conservative**: it precedes the FY2023
deadline for every company and SASA's FY2022 deadline. The registered cutoff
is therefore:

- **Primary:** 31 May of T+1 for every fiscal year (`uniform_05_31`). It is on
  or after every statutory deadline in the sample, and every sampled filing
  (latest: ASELSAN FY2023, 26 March 2024) precedes it. Cost: statements are up
  to 11 weeks staler than necessary in normal years.
- **Sensitivity S1:** last day of the month of the latest statutory deadline
  (`deadline_month_end`: 31 March, except 31 May for FY2023). The extension
  for FY2023 was announced in December 2023, so the rule was knowable in
  advance. SASA FY2022 is not public at its prediction time and is masked.

Residual risk: a company that filed after the statutory deadline would be
treated as public too early. No late filing was found in the sample; late
filing among the 81 companies is not excluded by evidence.

## 4. Timeline of one observation (standardized mode)

```
FY T ends     deadline(T)        cutoff C(T)      prediction date P(T)        exit
31 Dec T  ->  e.g. 11 Mar T+1 -> 31 May T+1  ->  first trading day > C(T) -> last trading day <= C(T+1)
              statements public  price features   signal formed, entry at     label realised
                                 as of last close  the close of P(T)
                                 <= C(T)
```

- `prediction_time` = 18:00 Istanbul on P(T). Price features use closes on or
  before C(T) (`available_at` = 18:10 on the quote date).
- Target: `adjclose(exit) / adjclose(entry) − 1`, in percent.
- Consecutive windows do not overlap: the exit of window T (≤ C(T+1)) precedes
  the entry of window T+1 (> C(T+1)). Training labels used to score year T end
  before P(T); the runner asserts this for every split.

## 5. Canonical target

| Item | Definition |
| --- | --- |
| Instrument | Ordinary share, Yahoo symbol `TICKER.IS`, Borsa Istanbul, TRY |
| Price series | Yahoo Chart API daily `adjclose` (split- and dividend-adjusted) |
| Dividends | Included: `adjclose` reinvests cash dividends on the ex-date (total return, gross of tax) |
| Splits, bonus issues | Included through Yahoo's split adjustment |
| Rights issues, misdated or missing adjustments | Not reliably adjusted by Yahoo. Any one-day move beyond ±25 % inside the window (BIST daily limits are ±10 %) quarantines the row |
| Dates | Entry: close of the first trading day after C(T). Exit: close of the last trading day on or before C(T+1). Quotes older than 7 days at either end make the row unusable |
| Currency, inflation | Nominal TRY, not benchmark- or CPI-adjusted |
| Missing | Not imputed. A security without a quote at entry is not evaluated |

The two published targets are kept as evidence, not reused: the vendor's dated
calendar-year return (training target of the published experiment) and the
Yahoo year-end-to-year-end `adjclose` return (2026 pre-registration). They
agree in rank (ρ = 0.994) but differ by more than 10 points in 28 of 307 rows
([`alternative_targets_report.md`](../data/trusted_clean/alternative_targets_report.md)).
Neither can be re-windowed to start after publication, so PIT-v2 defines its
own target from daily prices.

## 6. Features

Every model feature has an entry in the machine-readable
[`feature_availability_registry.json`](../data/pit/feature_availability_registry.json)
recording source, observation period, availability rule, transformation,
adjustment basis and earliest usable prediction date.

| Class | Features | Availability |
| --- | ---: | --- |
| Statement levels, ratios, growth (FY T, growth also FY T−1) | 27 | statement `available_at` |
| PIT market value | `market_cap` | reference close |
| Valuation ratios | `pe_ratio`, `pb_ratio`, `enterprise_value`, `ev_ebitda` | later of statements and reference close |
| Price | 1- and 2-year momentum, 3-year drawdown, return vs XU100, listing age, data flag | reference close |
| Excluded | `price_adjclose_t` (level of a back-adjusted series), `benchmark_same_year_return_pct` (identical across a cross-section) | never |

### Market value and corporate actions

The published `market_cap` multiplied Yahoo's back-adjusted close by the
historical share count, two incompatible bases. PIT-v2 uses one basis:

```
market_cap(asof) = quoted close(asof) × shares(asof)
                 = Yahoo close(asof) × F(31 Dec T) × shares(31 Dec T)
```

where `F(d)` is the product of Yahoo split ratios dated after `d`. Undoing a
vendor's retroactive adjustment reconstructs the price as quoted; it adds no
later information. The identity holds only if every share change after
31 December is a split or bonus issue Yahoo recorded, so a row is **excluded**
(not repaired) when the year-end share record disagrees with Yahoo's split
ratios in year T or T+1 by more than 2 %, or the close series has an
unexplained one-day jump after 31 December T. P/E, P/B, EV and EV/EBITDA are
recomputed from the PIT market value where the published dataset had a value,
inheriting its rejection rules (positive denominators, absurd-value caps,
unverified 2024 balance sheets).

Accounting assumption: net income, equity, net debt and EBITDA are the
reported consolidated figures in the vendor files; minority interests are not
separated, so P/E and P/B mix group earnings with the parent's market value.

### Pre-listing rows

A company-year is evaluated only if the security had a Yahoo quote on or
before the prediction date. This removes, among others, the five pre-listing
rows whose published 2021 "return" is the same vendor placeholder
(56.947991 %).

## 7. Universe and survivorship (unresolved)

The universe is the published 81-company training universe (40 public + 41
training-only), assembled in 2026 from then-current listings. No
point-in-time index membership is applied, and no company that was delisted,
suspended or failed between 2020 and 2026 can appear. Survivorship bias is
**not solved**; its direction for a cross-sectional rank IC is not known, and
results are statements about these 81 surviving companies only.

## 8. Evaluation

Identical to the published harness except for the panel: within-cross-section
percentile ranks; the same nine models with the same hyperparameters and
seeds; expanding-window walk-forward with test fiscal years 2022, 2023 and
2024, training on all earlier fiscal years. Inference: equal-weighted mean of
within-year Spearman ICs; within-year permutation null (10,000, seed
20261004); bootstrap of tickers within year (10,000); Bonferroni over the six
ML models; analytic minimum detectable |IC| at 80 % power for the realised
design. The decision rules are fixed in the amendment.
