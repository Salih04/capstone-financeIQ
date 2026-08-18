# Pre-registered Stage-A data-expansion sourcing protocol (FI-DATA-EXPAND-03)

> Stage A freezes **how historical data may be sourced and which ticker-years may
> ever become eligible**, before any new historical data is acquired. It does not
> freeze a realized panel, does not authorize any particular year, and does not
> predict that expansion will produce a detectable signal. The repository's
> standing scientific position is unchanged: **no reliable predictive edge has
> been established**.

Protocol identifier: **`FI-DATA-EXPAND-STAGE-A-v1`**.

| Field | Value |
| --- | --- |
| Task | FI-DATA-EXPAND-03 |
| Prior adjudication | `FI_DATA_EXPAND_02_METHOD_CHANGES_REQUIRED` |
| Authored at repository HEAD | `6fde2084767a20b3fa906e9ac029bcb8bd9a22ed` (branch `main`, clean worktree) |
| Protected boundary at authoring | 351 members, digest `98195607983a35d3ffc8996934be9ac1b808250a659fea126a1a9636e800cee5` (unchanged by this task) |
| Stage | **A only** — sourcing, provenance, eligibility and integrity rules |
| Stage B | **Not created by this task** |
| Data acquired by this task | **None.** No external source was contacted; no dataset, target, benchmark, model, or result was regenerated or changed |

## 1. Stage A versus Stage B

The two freezes are deliberately separated because they can only be honest at
different times.

| | Stage A (this document) | Stage B (future, separate task) |
| --- | --- | --- |
| Written | **before** any acquisition | **after** acquisition, **before** any fitting |
| Freezes | source admissibility, point-in-time membership rules, identity rules, comparability rule, missingness gate, target hierarchy, feature authority, metric, inference, multiplicity, stopping rule, interpretation | the **realized** eligible year list, the realized ticker-year universe, source manifest hashes, the realized feature vector and its hash, cohort assignment, fold schedule, realized n per year |
| Must not contain | any realized year list, ticker count, or n chosen after seeing data | any outcome value for a newly acquired year |
| Consequence of violation | the study is descriptive only | the study is descriptive only |

Nothing in Stage A authorizes acquisition by itself. A separate authorization is
required for each acquisition activity it describes.

## 2. Expansion direction: `TEMPORAL_REGIME_FIRST`

The declared expansion direction is **temporal/regime coverage first, ticker
breadth second**.

Reasoning, stated without overclaim:

- The current confirmatory walk-forward evaluation has only **three** evaluation
  years (`SPLITS` in [`experiments/run_experiments.py`](../experiments/run_experiments.py): `test_2023`,
  `test_2024`, `test_2025`).
- The governed macro table [`data/trusted_raw/macro/macro_context_yearly.csv`](../data/trusted_raw/macro/macro_context_yearly.csv)
  carries exactly **one** `regime_id` (`observed_2020_2025_macro_period`) for the
  entire 2020–2025 window.
- Adding tickers to the same years cannot add temporal or regime variation. It
  changes cross-sectional width only.
- Any tau-based (between-year heterogeneity) variance decomposition is
  **sensitivity-only** and is not an authority for this decision. Nothing in this
  repository establishes that tau > 0.
- Ticker breadth may still be worth pursuing **after** temporal integrity is
  solved; this document does not close that option, it orders it second.

## 3. Historical search window

**`2017` is frozen as the `CANDIDATE_SEARCH_FLOOR`.**

This is the earliest year that may be *searched*. It authorizes **no** year for
analysis — not 2017, not any other pre-2020 year.

A candidate year becomes Stage-B eligible only if **all six** gates pass for it:

| Gate | Requirement |
| --- | --- |
| G-1 point-in-time membership | effective-dated universe membership evidence for the year (§5) |
| G-2 identity | issuer/security identity and succession resolved (§6) |
| G-3 fundamentals | acceptable feature-year evidence under the fundamentals rule (§11) |
| G-4 benchmark | benchmark return for the year available under the governed acquisition rule (§10) |
| G-5 data quality | the concept-group missingness gate is decidable and satisfied for at least the confirmatory cohort definition (§9) |
| G-6 provenance | source identity, retrieval record and checksums complete (§10, §11) |

Failure of any gate classifies the year `INSUFFICIENT_DATA`.

There is **no substitution, no proxy year, and no back-filling from a later
membership state**. An `INSUFFICIENT_DATA` year is simply not in the study, and
saying so is a legitimate and expected outcome of this protocol. Given the
verdict already recorded in [`docs/UNIVERSE_HISTORY_SOURCING_SPIKE.md`](UNIVERSE_HISTORY_SOURCING_SPIKE.md)
— `FEASIBLE_WITH_DOCUMENTED_GAPS`, with **no** required period reaching
`CONFIRMED` even inside 2020–2025 — the realistic prior is that many candidate
years will classify `INSUFFICIENT_DATA`.

## 4. Universe rule

The universe is defined by rules, not by a target size.

> **Frozen rule.** Include **every** ticker-year that satisfies the Stage-A
> point-in-time membership rule (§5), the identity rule (§6), the comparability
> rule (§7), and the data-quality/missingness gate (§9). Include nothing else.

Explicitly **not** frozen and explicitly **forbidden** as inputs:

- a desired ticker count;
- the previously discussed 60–80 ticker target;
- a minimum N derived from a power calculation;
- any count chosen after collection begins.

**The realized ticker count is an output of the rules, not an input to them.**

## 5. Point-in-time membership rule

The standard is the one already established by the sourcing spike
[`docs/UNIVERSE_HISTORY_SOURCING_SPIKE.md`](UNIVERSE_HISTORY_SOURCING_SPIKE.md) §5, §10 and §15. Frozen here at
minimum:

1. **First-party, effective-dated evidence is preferred** and is the only class
   admissible to *originate* a membership claim (index operator announcements and
   the first-party disclosure attachments of those announcements).
2. **`effective_from` / `effective_to` semantics are mandatory.** `effective_from`
   is the first date the membership state is in force; `effective_to` is the last
   date in force or null while open. A record carrying only an announcement date
   is **not** point-in-time evidence.
3. **Fail closed on unresolved gaps.** Any interval whose membership state cannot
   be established from evidence remains `UNKNOWN` and is **excluded** from the
   confirmatory panel. `UNKNOWN` is never resolved by inference, interpolation,
   or convenience.
4. **No present-day membership may be projected backward.** A current constituent
   list is not evidence of past membership. The repository's own cohort files
   [`data/config/universe_public_40.csv`](../data/config/universe_public_40.csv) and
   [`data/config/universe_training_bist100.csv`](../data/config/universe_training_bist100.csv) are retrospective and
   carry no effective date; they are **not** membership evidence for any year.
5. **Extraordinary/non-periodic events must be accounted for**, not only quarterly
   periodic changes. A reconstruction that enumerates periodic changes alone is
   incomplete by construction, and incompleteness propagates to every earlier
   date when an event stream is rolled backward.
6. **A ticker symbol alone is not identity authority** wherever succession,
   merger, rename, or delisting is involved.
7. **Stable identity should use ISIN or another evidenced stable identifier where
   available.** Where no stable identifier appears in the source documents, that
   fact must be recorded on the record rather than papered over with a
   ticker-to-ticker join.
8. Membership evidence must record source URL/document identity, publication
   date, retrieval timestamp, and a document checksum.

**No sourcing, retrieval, or reconstruction is performed by this task.**

## 6. Identity and corporate-event rules

Predeclared handling, decided before any acquisition:

| Case | Rule |
| --- | --- |
| Ticker change | requires an evidenced identity assertion linking old and new ticker for the same security; otherwise both intervals stay `UNKNOWN` |
| Issuer rename without ticker change | must be captured (issuer name at time is recorded on every membership record) |
| Merger | requires evidenced succession; the successor does not inherit the predecessor's history unless the succession evidence states it |
| Successor entities | same as merger; a successor relation is asserted only from first-party succession evidence |
| Delisting | closes the interval at the evidenced effective date; later years are not carried forward |
| IPO | membership and feature-year eligibility begin no earlier than the evidenced first trading date |
| Listing after the feature-year cutoff | the ticker-year is ineligible for that feature year; it is not admitted with a shortened history |
| Split, demerger, share-class or restructuring cases with ambiguous continuity | if continuity is ambiguous, the identity is **not** resolved and the affected intervals stay `UNKNOWN` |

> **Frozen rule.** No identity resolution may be inferred merely because two
> tickers, names, or issuer descriptions look related. Unresolved identity **fails
> closed**.

## 7. Comparability rule for banks and financial firms — **Option A**

**Decision: A — issuers whose reported financial statements do not carry the
governed non-financial accounting concepts are excluded from the confirmatory
cohort.** They are not admitted under an improvised feature contract.

This is decided from existing repository evidence and schema semantics, before
acquisition, and it is not permitted to be revisited on the basis of predictive
results.

Repository evidence:

- [`DATA_PIPELINE.md`](../DATA_PIPELINE.md) records that bank candidates are flagged `is_bank=true` and
  that for them "revenue = net interest income and EBITDA is undefined".
- [`data/config/bist100_candidates.csv`](../data/config/bist100_candidates.csv) carries the same statement in its own
  header comment and flags nine bank candidates.
- [`data/trusted_clean/bist100_expansion_report.md`](../data/trusted_clean/bist100_expansion_report.md) §6 states that banks
  "should be handled as a separate sector", marks them "no gross profit/EBITDA",
  and recommends excluding banks "unless the model is restructured to support
  bank-specific features".
- The governed 40-feature vector (§8) contains at least nine concepts that are
  undefined or non-comparable under bank/insurance reporting: `gross_profit`,
  `gross_margin`, `ebitda`, `ebitda_margin`, `ev_ebitda`, `net_debt_to_ebitda`,
  `current_assets`, `current_ratio`, `working_capital`.
- **No comparable bank/financial feature contract exists anywhere in this
  repository.** Option B would require declaring one; declaring one is a separate
  scientific task and is not attempted here.

Identification procedure — evidence-based, never inferred:

1. The `sector` column is **unpopulated** in the trusted modeling path, and
   [`data/trusted_clean/feature_passports.json`](../data/trusted_clean/feature_passports.json) states it "must not be
   inferred". Sector labels are therefore **not** an admissible classifier.
2. A ticker-year is classified `FINANCIAL_STATEMENT_FORMAT_NON_COMPARABLE` when
   the evidenced source statements for that issuer-year do **not** report a
   cost-of-sales-based gross profit and an EBITDA-compatible operating structure,
   or when the issuer is evidenced to report under a banking or insurance
   supervisory statement format.
3. Classification evidence (source document, as-of date) is recorded per
   ticker-year in the Stage-B manifest.
4. Where the statement format cannot be evidenced, the ticker-year **fails
   closed** and is confirmatory-ineligible.

Scope and disclosure:

- The rule applies uniformly to **every** ticker-year entering a Stage-B
  expansion panel, including re-used 2020–2025 rows. It does not restate, revise,
  or reinterpret any committed result; existing artifacts are untouched.
- **Disclosure:** the current 40-ticker public cohort contains at least two
  financial issuers (`TSKB`, a development/investment bank, and `TURSG`, an
  insurer). Their rows carry populated `gross_profit` and `ebitda` values, but a
  populated cell is not evidence of concept comparability. Their confirmatory
  eligibility under this rule must be adjudicated from statement-format evidence
  at Stage B, not assumed in either direction.
- A future Option B (financial issuers admitted under a separately declared
  comparable feature contract) may be introduced **only** through separate prior
  governance, and never after expanded outcomes have been inspected.

## 8. Frozen target hierarchy

The existing repository contract is preserved unchanged.

| Class | Target | Basis |
| --- | --- | --- |
| **Confirmatory (primary)** | `next_year_return_pct` | nominal TRY |
| Exploratory robustness | `next_year_excess_return_vs_bist100` | benchmark-relative |
| Exploratory robustness | `next_year_real_return_pct` | real TRY |
| Exploratory robustness | `next_year_usd_return_pct` | USD |

Frozen statements:

- The R3-TGT-01 authority is **preserved**: nominal TRY is the sole confirmatory
  basis, and the excess basis remains exploratory.
- The excess target is **not** promoted to confirmatory by this task.
- Switching the primary target requires **separate prior governance**, completed
  before Stage B.
- **No target basis may be selected after seeing expanded outcomes.**
- No cross-basis multiplicity control is newly claimed (§17).

## 9. Frozen feature authority — the governed 40-feature vector

The governed feature vector is whatever
[`experiments/run_experiments.py`](../experiments/run_experiments.py)`::_feature_cols` returns for the modeling
dataset in force. Resolved at this document's HEAD against
[`data/trusted_clean/modeling_dataset_training_2020_2025.csv`](../data/trusted_clean/modeling_dataset_training_2020_2025.csv), it is exactly
**40** columns, in this order:

```
benchmark_same_year_return_pct
current_assets
current_ratio
ebitda
ebitda_growth_pct
ebitda_margin
enterprise_value
equity
ev_ebitda
financial_debt_ratio
gross_margin
gross_profit
gross_profit_growth_pct
leverage_ratio
long_term_liabilities
market_cap
net_debt
net_debt_to_ebitda
net_income
net_income_growth_pct
net_margin
non_current_assets
operating_income
operating_income_growth_pct
pb_ratio
pe_ratio
price_adjclose_t
price_data_available
price_drawdown_from_3y_high_pct
price_history_years_available
price_momentum_1y_pct
price_momentum_2y_pct
price_vs_bist100_1y_pct
revenue
revenue_growth_pct
roa
roe
short_term_liabilities
total_assets
working_capital
```

Deterministic hash of that list representation:

| Representation | SHA-256 |
| --- | --- |
| the 40 names joined by `\n`, no trailing newline, UTF-8 | `041566fc685b043c8618af859c268aa736fa5ae87b0d2679a2b35df779659575` |
| the same 40 names as a compact JSON array (`json.dumps(cols, separators=(',',':'))`) | `f8064f43ca5a446e21b2357fdafa4a9f6a1b7dfcbe7e79b8bc0835125c452543` |

Reproduction:

```bash
PYTHONPATH=. python -c "import hashlib,pandas as pd,experiments.run_experiments as r;c=r._feature_cols(pd.read_csv(r._modeling_csv()));print(len(c),hashlib.sha256('\n'.join(c).encode()).hexdigest())"
```

Frozen statements:

- The earlier "51-column exploratory" count is **incorrect** and is not used
  anywhere in this protocol.
- **No feature may be added or removed after expanded outcomes are inspected.**
- `_feature_cols` is a column filter, not a hard-coded list, so a schema change
  silently changes the vector. Stage B must therefore **re-resolve the realized
  vector, re-declare it in full, and re-declare its hash before any fitting**, and
  must state explicitly whether it equals the hash above.

## 10. Missingness gate — concept groups with exact minima

The previously proposed "at least 26 of 40 non-null" rule is **rejected** and is
not used.

### 10.1 Why a raw count is unsafe

Already-established pre-expansion facts (no expanded data was inspected to state
them):

| Cohort | Rows | Non-null count out of the governed 40 |
| --- | ---: | --- |
| public cohort | 240 | min 27 / median 39 / max 40 |
| training-only cohort | 163 | min 15 / median 25 / max 26 |

Fourteen governed features are structurally null across the **whole**
training-only cohort: `current_ratio`, `ebitda_growth_pct`, `enterprise_value`,
`ev_ebitda`, `financial_debt_ratio`, `gross_profit_growth_pct`,
`leverage_ratio`, `market_cap`, `net_debt_to_ebitda`, `net_income_growth_pct`,
`operating_income_growth_pct`, `pb_ratio`, `pe_ratio`, `revenue_growth_pct`.

A raw count therefore separates rows by **source class**, not by economic
concept: a 26-of-40 threshold would admit or reject an entire acquisition channel
wholesale while saying nothing about whether the row's valuation, growth, or
price concepts were ever observed. That is the defect, and it is the only use
this section makes of these figures. **The rule below was not designed to
preserve or exclude any cohort size**, and no cohort size was computed under it.

### 10.2 The standard the minimum is derived from

The minimum is **not** a chosen number. It is forced by two committed facts:

1. The project's core contract forbids fabricated, imputed, or synthesized
   values — missing stays null ([`CLAUDE.md`](../CLAUDE.md), [`AGENTS.md`](../AGENTS.md)).
2. At fit time the governed pipeline does **not** honour nulls: `_fit_sklearn` in
   [`experiments/run_experiments.py`](../experiments/run_experiments.py) applies `np.nan_to_num(X, nan=0.5)` — every
   null feature enters every model as the **median rank**, a fabricated neutral
   value.

Consequently, for a **confirmatory** ticker-year the only defensible minimum is
"every feature whose concept is defined for that ticker-year is actually
evidenced". Any partial count below that would be an invented parameter admitting
a declared quantity of fabricated neutral cells, which is exactly what the
rejected 26-of-40 rule did.

### 10.3 Concept groups, exact members, exact minima

Every one of the 40 governed features belongs to exactly one group.

| Group | Members | Exact minimum non-null | Individually mandatory |
| --- | --- | --- | --- |
| G1 `SIZE_SCALE` (7) | `revenue`, `total_assets`, `equity`, `current_assets`, `non_current_assets`, `market_cap`, `enterprise_value` | **all applicable members** | every applicable member |
| G2 `PROFITABILITY` (9) | `gross_profit`, `operating_income`, `ebitda`, `net_income`, `gross_margin`, `ebitda_margin`, `net_margin`, `roa`, `roe` | **all applicable members** | every applicable member |
| G3 `VALUATION` (3) | `pe_ratio`, `pb_ratio`, `ev_ebitda` | **all applicable members** | every applicable member |
| G4 `GROWTH` (5) | `revenue_growth_pct`, `gross_profit_growth_pct`, `ebitda_growth_pct`, `operating_income_growth_pct`, `net_income_growth_pct` | **all applicable members** | every applicable member |
| G5 `LEVERAGE_LIQUIDITY` (8) | `short_term_liabilities`, `long_term_liabilities`, `net_debt`, `net_debt_to_ebitda`, `leverage_ratio`, `financial_debt_ratio`, `current_ratio`, `working_capital` | **all applicable members** | every applicable member |
| G6 `PRICE_MOMENTUM` (8) | `price_adjclose_t`, `price_data_available`, `price_history_years_available`, `price_momentum_1y_pct`, `price_momentum_2y_pct`, `price_drawdown_from_3y_high_pct`, `price_vs_bist100_1y_pct`, `benchmark_same_year_return_pct` | **all applicable members** | every applicable member |

> **Frozen rule.** A ticker-year is **confirmatory-eligible** if and only if, in
> every one of G1–G6, every *applicable* member is non-null. A group whose
> applicable set is empty is **never** vacuously satisfied — it makes the
> ticker-year confirmatory-ineligible. The minimum has zero free parameters and
> may not be relaxed, tightened, or re-parameterized at Stage B.

### 10.4 Structurally-not-applicable concepts (exact conditions)

A member is *not applicable* to a ticker-year only under the conditions below.
Each follows a committed definition in [`scripts/data_collection/build_all.py`](../scripts/data_collection/build_all.py)
or [`scripts/data_collection/build_free_valuation_history.py`](../scripts/data_collection/build_free_valuation_history.py).

| Member | Not applicable when | Basis |
| --- | --- | --- |
| `pe_ratio` | `net_income` <= 0 | definition: `market_cap / net_income` where net income is positive |
| `pb_ratio` | `equity` <= 0 | definition: `market_cap / equity` where equity is positive and validated |
| `ev_ebitda` | `ebitda` <= 0 | definition: `enterprise_value / ebitda` where EBITDA is positive (`reject if ebitda <= 0`) |
| `net_debt_to_ebitda` | `ebitda` <= 0 | same accounting guard as `ev_ebitda`, applied consistently; declared here, not inferred from data |
| all five G4 growth members | the issuer-year is the **earliest evidenced feature year** for that security identity in the acquired panel, so no evidenced T-1 base period exists | a growth rate cannot be evidenced without an evidenced base period |
| `price_momentum_1y_pct`, `price_vs_bist100_1y_pct` | first-party evidence shows the security was **not trading** at the T-1 year end | the concept does not exist before listing |
| `price_momentum_2y_pct`, `price_drawdown_from_3y_high_pct` | first-party evidence shows the security was not trading for the full T-2 through T window | same |
| `price_adjclose_t`, `price_data_available`, `price_history_years_available`, `benchmark_same_year_return_pct` | **never** — always applicable | required anchors of the price/benchmark concept |

Not-applicable is a statement about the **concept**, evidenced from listing or
accounting facts. It is never a description of what a source happened to supply.

### 10.5 Source-class structural missingness

> **Frozen rule.** When a source class cannot supply a concept that *is* defined
> for the issuer-year — for example no evidenced shares-outstanding input, so
> `market_cap`, `enterprise_value` and the whole G3 valuation group are absent —
> that is **missing data, not non-applicability**. The ticker-year is
> **confirmatory-ineligible** and may enter only prespecified exploratory
> analyses, labelled as such.

This is the rule that makes the source-class defect in §10.1 explicit instead of
silent.

### 10.6 Imputation disclosure and the complete-case robustness cohort

Because not-applicable cells are still imputed to the neutral rank 0.5 at fit
time (§10.2), Stage B must:

1. record, for every confirmatory row, the exact count and identity of
   not-applicable cells that the fit imputes;
2. report those counts per year and per model before any inference is read; and
3. run one **prespecified** robustness analysis restricted to the subset of
   confirmatory rows with **zero** imputed cells.

The complete-case subset is named here, in advance, so that it can never be
chosen after outcomes are seen.

### 10.7 Prohibited

- Changing any group membership, applicability condition, or minimum after
  expanded outcomes are inspected.
- Selecting any part of this rule using IC, returns, p-values, significance, or
  model performance.
- Using this rule to reach a desired cohort size.

## 11. Benchmark acquisition rule

Only the governance principle is frozen here. **No benchmark data is fetched by
this task.**

> Any pre-2020 benchmark acquisition is a **new scientific-data acquisition**, not
> a refresh, and requires its own authorization.

Stage A requires, before any benchmark acquisition:

1. the exact year window is declared **before** acquisition;
2. the source identity (provider, instrument, calendar convention) is recorded;
3. the raw acquisition is preserved wherever repository policy permits;
4. the exact annual-return derivation is fixed **before** any value is used;
5. **no silent refresh** of the existing 2020–2025 observations
   (`27.38 / 24.23 / 185.94 / 31.96 / 28.94 / 12.64`, currently in
   [`data/trusted_raw/bist100_benchmark_returns.csv`](../data/trusted_raw/bist100_benchmark_returns.csv));
6. overlap years old-versus-new are compared **exactly**;
7. any overlap revision is adjudicated explicitly and recorded, never absorbed;
8. a benchmark source/provenance manifest accompanies the acquisition;
9. the generated benchmark report is **never** hand-edited.

Known, deliberately unrepaired: the committed
[`data/trusted_clean/bist100_benchmark_report.json`](../data/trusted_clean/bist100_benchmark_report.json) still carries a stale
absolute `output` path leaf. The producer
[`scripts/data_collection/collect_bist100_benchmark.py`](../scripts/data_collection/collect_bist100_benchmark.py) was already fixed
forward under FI-DATA-PATH-02D; the stale leaf must resolve naturally through the
next governed regeneration. **It is not repaired here** and is not a Stage-A
gate.

## 12. Fundamentals acquisition rule

Frozen evidence requirements for any historical fundamentals acquisition. **No
files are acquired by this task.**

1. Every feature-year T value must have been **information available as of the
   declared cutoff** for year T.
2. **No later frozen snapshot may be used as a historical fact.** A single
   point-in-time vendor snapshot repeated across periods is not history — see
   [`data/trusted_clean/frozen_column_evidence.md`](../data/trusted_clean/frozen_column_evidence.md), where whole columns
   were rejected precisely because per ticker the value was identical across all
   periods.
3. **No quarter or period file whose values are known frozen or repeated across
   periods** may be admitted.
4. Source identity and effective/as-of date are recorded per value.
5. Owner/manual exports are admissible **only** under the documented ingestion
   contract ([`MANUAL_FINANCIALS.md`](../MANUAL_FINANCIALS.md), [`DATA_REQUIREMENTS.md`](../DATA_REQUIREMENTS.md)).
6. **No fabricated missing values.** Missing stays null.
7. **No retrospective value substitution** from a later fiscal period.
8. Derived features are recomputed from evidenced inputs; a derived value whose
   inputs are absent stays null.

Observed pre-expansion caution (existing committed data, recorded as motivation
only and **not adjudicated or repaired by this task**): within the current public
cohort, 4 of 40 tickers carry a single `revenue` value across all six years, and
two different tickers (`TSKB`, `TURSG`) carry an identical `revenue`,
`gross_profit` and `ebitda` value. Whatever its cause, it demonstrates that
frozen/repeated-value screening must be a gate on acquisition rather than an
afterthought.

## 13. Power language

> The power model is **`DESCRIPTIVE / SENSITIVITY ONLY`**. It is not a design
> authority, not a stopping rule, and not evidence about any effect.

- `tau = 0.093` is **not** frozen as truth. Nothing in this repository establishes
  a between-year IC standard deviation. (The numeral coincides with an observed
  pooled ridge IC in [`experiments/results/significance_report.md`](../experiments/results/significance_report.md); that is a
  coincidence of magnitude, not an estimate of tau.)
- Sensitivity grid over tau: `0`, `0.05`, `0.093`, `0.15`, `0.25`.
- Neutral hypothetical absolute-IC grid: `0.02`, `0.05`, `0.075`, `0.10`, `0.15`,
  `0.20`. These are **hypothetical values**, not claims about attainable or
  typical IC. No literature claim about "typical" IC ranges is used anywhere in
  this protocol.
- "Effective N" is **not** a governance headline and may not be reported as one.
- Every MDE figure is **conditional** on its assumptions and on the realized
  Stage-B design. The realized sensitivity table is a Stage-B deliverable and is
  not populated here.

## 14. Regime treatment

> Frozen: **`DESCRIPTIVE_ONLY`**.

- The governed macro table carries a single `regime_id`
  (`observed_2020_2025_macro_period`) for 2020–2025. There is currently **no**
  regime contrast to test.
- No confirmatory regime label — crisis, COVID, inflation, high-rate, low-rate —
  may be defined from narrative description.
- A deterministic regime rule may be introduced **only** through separate
  governance, and only **before** expanded equity outcomes are inspected.
- If ever defined, it must use **non-equity macro variables only**
  (`cpi_december_yoy_pct`, `policy_rate_year_end_pct`,
  `usdtry_year_end_try_per_usd` are available; each carries its own source id and
  effective date).
- **`bist100_return_pct` must never be used to define a regime that is later
  evaluated on equity performance.**

## 15. Primary metric and uncertainty

| Item | Frozen value |
| --- | --- |
| Primary metric | equal-year-weighted mean of within-year Spearman IC |
| Primary inference | within-year permutation of realized outcomes |
| Draws | 10,000 (`DEFAULT_PERMUTATIONS` in [`experiments/significance.py`](../experiments/significance.py)) |
| Seed | 42 (`DEFAULT_SEED`, same module) |
| Tail rule | two-sided absolute tail |
| Monte Carlo correction | `(#{|null| >= |observed|} + 1) / (draws + 1)` |

This is the repository's current R3-TGT-01 convention, read directly from
[`experiments/significance.py`](../experiments/significance.py); no different fixed value is asserted.

Prespecified robustness, all **descriptive**:

- ticker-cluster bootstrap — descriptive interval only, never a confirmatory test;
- leave-one-year-out pooled IC stability;
- random-effects tau estimate with interval — descriptive only.

> Year-cluster bootstrap and cluster-robust standard errors **must not** be made
> primary at a likely Y = 6–9 evaluation years. With that few clusters their
> nominal coverage is not credible, and presenting them as primary would overstate
> precision.

## 16. Model family and hyperparameters

Frozen confirmatory family — exactly the six existing ML models, with their
committed hyperparameters and seeds from [`experiments/run_experiments.py`](../experiments/run_experiments.py):

| Model | Committed configuration |
| --- | --- |
| `linear_regression` | `LinearRegression()` defaults |
| `ridge` | `Ridge(alpha=1.0)` |
| `lasso` | `Lasso(alpha=0.1, max_iter=5000)` |
| `elasticnet` | `ElasticNet(alpha=0.1, max_iter=5000)` |
| `random_forest` | `RandomForestRegressor(n_estimators=200, max_depth=4, random_state=42)` |
| `gradient_boosting` | `GradientBoostingRegressor(random_state=42, max_depth=2, n_estimators=120)` |

- **No tuning. No hyperparameter search. No new model after data acquisition.**
- The rank-percentile feature transform and the `nan_to_num(..., 0.5)` fit-time
  handling stay exactly as committed (see §10.6 for the required disclosure).
- Baselines (`baseline_equal_weight`, `baseline_rank_score`,
  `robust_rank_aggregation`) stay **outside** the confirmatory family, exactly as
  today.

## 17. Multiplicity

> **Confirmatory family = 6 ML models x 1 primary target (`next_year_return_pct`,
> nominal TRY) x 1 primary metric.**
> Correction: **Bonferroni**, FWER **alpha = 0.05**, family size **6**.

Secondary, prespecified, and clearly labelled as such:

- the excess target `next_year_excess_return_vs_bist100`;
- the real TRY target `next_year_real_return_pct`;
- the USD target `next_year_usd_return_pct`;
- the exploratory missingness cohort (§10.5);
- leave-one-year-out robustness.

No cross-basis multiplicity control is newly claimed. Any analysis **not named
before Stage B** is `DESCRIPTIVE_ONLY` and may not support a predictive-edge
claim.

## 18. No-peeking boundary

This boundary is operational, not aspirational.

**Stage B MAY inspect, for newly acquired years:**

- source availability and source identifiers;
- document hashes;
- membership effective dates;
- provenance completeness;
- coverage counts;
- missingness and data-quality gate outcomes;
- eligible/ineligible ticker-year identities;
- schema integrity.

**Stage B MUST NOT inspect, for newly acquired years:**

- `next_year_*` values of any basis;
- realized returns;
- benchmark-relative outcome values;
- ICs;
- model predictions;
- model scores;
- p-values;
- effect signs;
- rankings;
- significance summaries.

> **Operational test.** The Stage-B author must be able to complete the entire
> Stage-B freeze **without loading a `next_year_*` column for any newly acquired
> year.** If completing the freeze requires such a column, the freeze is invalid.

## 19. Stopping rule

> **Frozen.** Collection ends when the Stage-A search window has been exhausted
> and every candidate year has been classified by the sourcing and data-quality
> gates (§3). Predictive results are never an input to stopping.

Explicitly forbidden:

- adding another year because a p-value was close;
- adding tickers because IC looked promising;
- dropping a year because the sign was unfavorable;
- changing the missingness rule after seeing outcomes;
- switching target basis after seeing results;
- enlarging the model family after seeing results.

Future calendar years enter **only** through a separately declared prospective
protocol — as [`docs/PREREGISTERED_2026_EVALUATION.md`](PREREGISTERED_2026_EVALUATION.md) does — and never by
extending this study after observing its result.

## 20. Interpretation of a null result (pre-written)

A null result means: **failure to reject the declared within-year null under the
realized Stage-B design.**

It may exclude effects above the achieved, assumption-conditional MDE band.

It does **not** establish:

- that there is no true effect;
- that the true IC is zero;
- that no economically interesting small effect exists;
- that the finding generalizes across unobserved regimes, markets, or periods.

## 21. Positive-result escalation (pre-written)

If any confirmatory result survives the declared correction, the following
sequence is **mandatory and ordered** before any claim-class change:

1. contamination and leakage audit;
2. point-in-time re-verification of **every** contributing ticker-year;
3. full declared multiplicity confirmation;
4. leave-one-year-out and per-model survival review;
5. an independent, untouched forward year evaluated under freeze-once governance;
6. separate Model Confidence Contract / governance review.

> Until **all six** are satisfied, the repository's position remains: **no
> reliable predictive edge established.**

## 22. Stage-B contract stub (non-binding, unpopulated)

Stage B must eventually freeze the following, and none of it can be known now.
These fields are **intentionally empty**.

| Field | Status |
| --- | --- |
| exact eligible year list | not yet knowable |
| exact ticker-year universe | not yet knowable |
| source and manifest hashes | not yet knowable |
| exact realized feature-vector hash | not yet knowable (must be re-resolved per §9) |
| confirmatory/exploratory cohort assignment | not yet knowable |
| exact walk-forward fold schedule | not yet knowable |
| realized n per year | not yet knowable |
| realized sensitivity/MDE table | not yet knowable |
| final immutable interpretation grid | not yet knowable |

Populating any of these from assumption rather than realized evidence
invalidates the Stage-B freeze.

## 23. What this document does not do

- It does not fetch, download, or access any external data source.
- It does not collect membership records, fundamentals, or benchmark values.
- It does not regenerate any dataset, model, experiment, or report.
- It does not change current modeling data, current target values, or any
  committed scientific result.
- It does not re-pin the protected boundary.
- It does not create Stage B.
- It does not authorize any specific year.
- It does not claim, imply, or anticipate a predictive edge. **No reliable
  predictive edge has been established.**

Research and educational use only. Not investment advice.
