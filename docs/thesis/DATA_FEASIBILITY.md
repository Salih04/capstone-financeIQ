# Week 1 data feasibility probes

Scope: the minimum evidence needed to make two Week 1 decisions — whether a
monthly panel is buildable from the existing free data path, and whether the
empty `sector` field can be populated honestly. **No panel was built and no
dataset was committed.** Probes were read-only and their output went to a
scratch directory.

Probe date: 2026-08-27. Probed symbols: `AEFES.IS`, `THYAO.IS`, `ASTOR.IS`,
`KUYAS.IS`, plus one deliberately invalid symbol.

---

## 1. Monthly prices — VERDICT: FEASIBLE

The existing acquisition path already talks to an endpoint that serves monthly
history. No new data source, no scraper, and no paid API is required.

### Current fetcher

`scripts/fetch_yahoo_chart_prices.py` calls
`https://query1.finance.yahoo.com/v8/finance/chart/{TICKER}.IS` with
`interval=1d` and a **hardcoded three-week window** (`period1` = 20 December of
the target year, `period2` = 10 January of the next). `find_year_end_price`
then collapses that window to a single year-end observation. The fetcher is
year-end-shaped by construction, not by limitation of the source.

### What the source actually supports

Confirmed live against the endpoint:

| Property | Observed |
|---|---|
| `validRanges` | `1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max` |
| `interval=1mo` | Works. `dataGranularity` echoes back `1mo`. |
| Span, `AEFES.IS` / `THYAO.IS`, request 2015-01-01 → 2025-12-31 | 132 monthly bars, 2014-12-31 → 2025-11-30 |
| Nulls in that span | 0 in `close`, 0 in `adjclose` |
| `firstTradeDate` | Exposed per symbol (both probed majors: 2000-05-10) |
| Events | `events=div,split` returns explicit `dividends` and `splits` records |
| Currency | `TRY` |

### Required code changes

Four small, contained changes — no redesign:

1. Parameterise `period1` / `period2`; they are currently hardcoded to the
   year-end window.
2. Parameterise `interval` (`1d` / `1mo`); the request already builds a params
   dict, so this is one key.
3. Replace `find_year_end_price` (single-point extractor) with a full-series
   extractor emitting a long-format `ticker × date` frame. Leave
   `find_year_end_price` in place — the year-end path is governed and in use.
4. Write the monthly raw JSON to a **separate cache namespace**. The existing
   `data/trusted_raw/prices/yahoo_chart_raw/{SYMBOL}_{year}.json` files are
   governed artifacts of the year-end path and must not be collided with.

### Adjustment convention

`close` is the raw close; `adjclose` is back-adjusted for dividends and splits.
They genuinely differ (e.g. `AEFES.IS` 2023-12-20: close 12.880000, adjclose
12.523424).

The reproducibility hazard is that `adjclose` is defined *relative to
subsequent corporate actions*, so a dividend or split occurring after a fetch
retroactively restates every earlier `adjclose`.

**Observed:** re-fetching the exact window backing the committed
`AEFES.IS_2023.json` cache produced **0 of 14 dates differing**, in both `close`
and `adjclose`. So no drift was observed on this probe. That is a single
negative observation, not proof the mechanism is absent — `AEFES` simply had no
restating corporate action in the interval.

**Mitigation, regardless:** pin raw `close` plus the explicit `div`/`split`
event records and derive the adjustment in-repo, rather than pinning Yahoo's
`adjclose`. Hash the raw JSON per fetch. That makes the adjustment
deterministic and auditable instead of dependent on a vendor's current view of
history.

### Delisting and symbol risk

An invalid or delisted symbol returns **HTTP 404**, which the existing
`_NON_RETRYABLE` set already classifies correctly: the fetcher records an error
row with null prices and moves on. It never yields a silent zero or an empty
success — the same failure mode that has bitten this project on the KAP
disclosure API.

Residual risk is ticker *reuse and renaming* on BIST: a symbol that changes
hands between issuers is indistinguishable at the endpoint. This must be
handled by the universe/membership layer, not by the price fetcher.

### Missing-month behaviour

Absent months are **omitted from the series, not null-padded**. `ASTOR.IS`
(`firstTradeDate` 2023-01-18) returns 36 bars for the same 132-month window
that returns 132 bars for a long-listed name.

Consequence for the panel builder: reindex onto an explicit full month grid and
leave genuine gaps **null**. Never forward-fill, and never treat a short series
as a complete one. This is the project's standing contract — missing stays null.

### Rate-limit risk — materially *lower* than today

Monthly history for a ticker is **one request for the whole span**, versus the
current **one request per ticker-year**. The full 40-ticker training universe
costs ~40 requests instead of ~240. Observed latency was ~0.4 s per request; at
the existing 0.5 s politeness sleep the whole universe fetches in well under a
minute. The existing exponential backoff (1/2/4/8/16 s on 429 and 5xx) carries
over unchanged.

### Reproducibility implications

- Cache and hash the raw JSON per ticker; treat it as the provenance unit.
- Pin raw `close` + event records, not `adjclose` (see above).
- Record `firstTradeDate` per symbol so short series are explained by data, not
  assumed to be errors.
- Series end at the last **completed** month, so any re-fetch at a later date
  extends the panel. The end date must be pinned explicitly in the manifest,
  or two runs will disagree by construction.

### Why it is worth doing: power

Computed with the repository's own `experiments.significance.minimum_detectable_ic`
(verified to reproduce the committed baseline values 0.182271, 0.259819,
0.308847 exactly):

| Design | Cross-sections | MDE \|IC\| at 80% power |
|---|---|---|
| Committed baseline (n=80, 3 annual) | 3 | 0.182271 |
| Monthly, n=40, 3 years | 36 | 0.076612 |
| Monthly, n=40, 6 years | 72 | 0.054226 |
| Monthly, n=40, 11 years | 132 | 0.040067 |

Monthly cross-sectional ICs are **not independent** — annual fundamentals
repeat across the months of a year, and returns autocorrelate. The idealised
row above is therefore a lower bound on MDE. Discounting 11 years of monthly
data for dependence:

| Effective independence | k_eff | MDE \|IC\| |
|---|---|---|
| Independent monthly (idealised) | 132 | 0.040067 |
| Quarterly-effective | 44 | 0.069323 |
| Semiannual-effective | 22 | 0.097881 |
| Annual-effective (most conservative) | 11 | 0.137983 |

Even the most conservative discount — assuming monthly data buys no more
independent information than one observation per year — lands at 0.138, below
the committed 0.182. The monthly redesign improves detectable effect size under
every dependence assumption tested. This is a statement about **measurement
resolution only**; it says nothing about whether any effect exists to detect.

---

## 2. Sector data — VERDICT: CANNOT BE POPULATED HONESTLY

### Is there an existing trustworthy source?

No. Every candidate in the repository was checked:

| Candidate | Finding |
|---|---|
| `sector` in the three `data/trusted_clean/modeling_dataset_*.csv` | Column present, **0 of 403 rows populated** |
| `data/trusted_raw/company_universe.csv` | Has a `sector` column, **0 of 40 rows populated** |
| `backend/templates/quarterly_fundamentals_template.csv` | A blank manual-entry template, not a source |
| `backend/app/services/sector_service.py` | A **consumer**, not a source. Computes sector z-scores from `Company.sector_code` in Postgres and requires a classification it does not supply. |

No tracked source carries a sector classification for any ticker.

### Could the `indices` column serve as a proxy?

It should not. `indices` is populated for 240 of 403 rows and holds BIST index
membership strings. Two problems:

1. **It is not a sector classification.** Of 14 distinct index codes, only two
   are sector indices — `XUSIN` (industrials, 120 ticker-years) and `XUMAL`
   (financials, 30). The rest are size, governance, dividend, sustainability
   and participation indices. Coverage would be partial and the taxonomy
   two-valued.
2. **It is not point-in-time.** The membership string is **identical across all
   years for every one of the 40 tickers** (0 of 40 vary). It is a single
   retrospective snapshot back-projected onto history. Using it as a sector
   label would import exactly the look-ahead the pipeline's guards exist to
   prevent, and it compounds the already-recorded limitation that the cohort is
   a retrospectively fixed universe rather than verified point-in-time
   membership.

### Would a static mapping create point-in-time problems?

Yes — two distinct ones:

- **Reclassification.** A company's sector is not constant. A static
  present-day mapping assigns today's classification to 2020 observations,
  which is look-ahead whenever a reclassification occurred in between.
- **Survivorship, again.** A mapping built from a current listing covers only
  currently-listed names, silently dropping anything delisted during the
  window.

A static mapping is defensible **only** as an explicitly-labelled, clearly
caveated robustness cut — never as a modelling feature and never as a
point-in-time control.

### Recommendation

Leave `sector` null. Fabricating or back-projecting it would violate the
project's core contract. If sector control becomes necessary for a thesis
experiment, it requires a genuine point-in-time classification source with
effective dates, acquired under the existing no-paid-API / no-scraper policy —
and that acquisition is itself a scoped task with an owner decision, not a
side-effect of an experiment.

Until then, the honest position stands: **no sector-controlled or
sector-neutral analysis is possible on this dataset**, and that limitation is
recorded in the frozen baseline.
