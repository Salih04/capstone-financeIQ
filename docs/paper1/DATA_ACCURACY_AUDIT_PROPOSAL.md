# Paper 1 — Capstone v1 data-accuracy sample audit

**NEW PROPOSED CARD · v0.1 · 2026-11-02 · NOT APPROVED / NOT EXECUTED.**
Research support only; not investment advice.

Authority to draft: the owner's explicit 2026-11-02 continuation of
[FINANCEIQ](https://chatgpt.com/c/6ae096dd-14f4-83ed-85fe-8cacbd3639a2).
This is an additional Paper 1 measurement-quality proposal, separate from FO-4,
FIQ-09 migration and FIQ-17 source/selection-effect replication. It grants no
sampling, retrieval, comparison, outcome access or experiment authorization.

## Question and proposed boundary

How often do specified legacy annual fields agree with independently sourced,
definition-compatible observations? This is a descriptive audit of the frozen
Capstone inputs, not a predictive test, population-wide vendor assessment, or
correction to the frozen record. The capstone frame is used only to audit that
historical artifact; it is never substituted for U1 in new research.

Propose **30 company-years**, without replacement, fixed seed **20261102**.
All observation dates, return endpoints and original source availability dates
must be **on or before 2022-12-31**. A fiscal-year label ≤2022 alone is insufficient:
FY2022 statements first published in 2023 are outside this proposal's access scope.
The owner must approve the resulting precise eligible-year/frame definition before
sampling; do not silently move the boundary to retain FY2022. No frame has been
enumerated, company-year selected, availability checked or observation retrieved.

## Definitions proposed for approval before execution

1. **Frame and immutable inputs.** Pin the frozen annual original and corrected-input
   versions separately, hashes and parser commit. Identify which stream each field
   actually entered; do not pool duplicate company-years or original/corrected values.
   Propose non-financial capstone company-years with consolidated annual statements,
   subject to the date boundary above; any stratum restriction and its generalisation
   cost require approval. Define issuer/security mapping, fiscal-period end and share
   class before reading values. Missing fields do not remove a sampled row.
2. **Deterministic draw.** Freeze an outcome-free eligible frame sorted by stable
   issuer ID and fiscal-period end, UTF-8 LF serialization and SHA-256. Proposed
   algorithm: pin Python version, then `random.Random(20261102).sample(frame, 30)`.
   Require at least 30 eligible unique rows; otherwise stop for a prospective amendment.
   No replacement of missing, mismatching, suspended or delisted observations; no
   outcome-dependent choice of sample, fields, tolerance or source. Do not run this now.
3. **Five proposed financial fields.** Annual revenue; annual profit attributable to
   owners of the parent; period-end total assets; period-end equity attributable to
   owners of the parent; net margin = 100 × that profit / that revenue (percentage
   points; zero/missing revenue means not comparable). Approve exact legacy column
   aliases and KAP taxonomy/statement-line IDs, sign, currency, scale, consolidation,
   annual cumulative period and ratio convention. If a legacy ratio uses a different
   numerator, it is not comparable under this definition; do not reinterpret it after
   seeing agreement. These candidate mappings have not been verified against payloads.
4. **Original-period KAP evidence.** Use the actual original filing and attachments
   for that fiscal period, with disclosure ID/time, document hash, page/table/line and
   unit. Do not use today's summary screen, a later report's comparative column,
   subsequent restatement or inflation-rebased history as the original. Define how
   corrected original-period filings and vendor extraction dates are adjudicated
   before execution; unknown vintage/basis stays non-comparable, never backfilled.
5. **Prices and returns.** Propose two separate comparison fields: raw year-end
   official close on the last scheduled BIST session of year y, and nominal-TRY
   calendar-year total shareholder return from the last session of y−1 to that of y,
   with gross cash dividends reinvested on the ex-date and evidenced share/rights
   actions. Approve actual legacy field semantics, trading calendar, non-trading and
   delisting treatment, action timing, reinvestment/rights assumptions and formula
   before access. No carry-forward substitution. A differently adjusted vendor field
   is non-comparable until its basis is evidenced, not automatically wrong. Every
   required endpoint/action must satisfy the ≤2022 date boundary.
6. **Independent price comparator.** Name and approve a second source with documented
   upstream lineage independent of the field under audit. Another wrapper over the
   same Yahoo/Fintables feed is not independent evidence. KAP statements are not a
   daily-price source. No comparator has been selected; the new-research
   [price-source owner choice](../research/DAILY_PRICE_SOURCE_OWNER_OPTIONS.md) is
   separate and remains unresolved. Do not fetch prices or corporate actions now.
7. **Matching and missingness.** Propose monetary agreement after exact unit/sign
   normalization within half the coarser published reporting unit; prices within half
   the coarser evidenced tick/quoted precision; ratios/returns within half the coarser
   displayed percentage-point precision. Approve precision extraction, ties and
   rounding rules in advance; no percentage-of-value tolerance selected post hoc.
   Retain local statuses MATCH, MISMATCH, MISSING and NOT-COMPARABLE, with reasons.
   Nulls stay null. MISMATCH alone does not identify which source is erroneous.
8. **Denominator and disclosure.** Proposed per-field match rate = matches / comparable
   non-missing pairs; zero denominator yields null. Publish **only those per-field
   match rates**, plus methodological/limitations prose; no company/year rows, values,
   differences, returns, rankings, source snippets, sample identities or microdata.
   Keep denominators, missing/non-comparable counts and adjudication local. Because
   this disclosure restriction hides coverage, the paragraph must explicitly say the
   rates are conditional on comparability and cannot certify overall accuracy.
   Approve the exact aggregate-release schema/precision before execution. No confidence
   interval, hypothesis test or vendor ranking is proposed; any addition needs a
   prospective specification and multiplicity decision.

## Mandatory gates and stopping rule

- Obtain explicit owner approval of the exact version, frame, fields, source lineage,
  dates, formulae, tolerances, denominators, sample size and release schema. Complete
  and commit a BEFORE record using the [study template](../process/STUDY_RECORD_TEMPLATE.md)
  before the draw or data access. Record actual timestamps; never backdate registration.
- Document prior exposure, including the existing capstone/audit findings and this
  outcome-bearing project context. Apply Charter and adopted
  [owner addendum](../research/OWNER_DECISION_ADDENDUM.md) access/exposure rules.
  No protected 2023–2025 observations, price coverage, joins or later information;
  no holdout opening, model evaluation, new performance metric or FIQ-17 execution.
- Preserve the already closed KAP, BIST announcement and Product 3184 rights decisions.
  Reference their exact applicable records when execution is considered; do not reopen
  them. Separately establish that the intended legacy-file/comparator operations and
  aggregate output are covered by applicable evidence. FO-4 is terms review only;
  Fintables raw public redistribution is NO. An internal owner authorization is not an
  external licence; see the [source-use amendment](../SOURCE_USE_OWNER_AMENDMENT.md).
- Comparisons and evidence stay **LOCAL ONLY** in the authorized private archive.
  No raw files or observation-bearing prompts/uploads to remote agents/services.
  New acquisition, if separately authorized, remains Kernel-owned and outcome-blind;
  pass no audit results, match rates, returns or model information to Kernel. This
  card sets no Kernel execution sequence and authorizes no Kernel task or write.
- Register every attempt, failure, abandonment and deviation in append-only study/
  trial/exposure records, including occurrence and recording times. Never erase an
  unsuccessful draw or redefine a field after seeing its agreement. Stop at the
  approved 30 rows; unresolved source, rights, date, mapping or access prerequisites
  stop the affected work. Changes require a prospective amendment, not a reroll.
- Independent methodological and disclosure review is required before using findings
  in Paper 1. Write the AFTER record, reconcile local statuses and release only the
  approved aggregate fields. Preserve every frozen source/result byte; no repair or
  rerun is authorized by this audit.

## Intended deliverable — no results yet

A Paper 1 **“Data accuracy” limitations paragraph** reporting only approved per-field
match rates and explaining conditional comparability, missingness, small selected
historical scope, original-vintage limitations and prior exposure. It must distinguish
owner suspicion, demonstrated mismatches and unresolved causes; agreement on these
fields cannot validate all ratios, prices, research results or an investment edge.
Until execution is separately authorized and completed, retain the owner-reported
concern as an unquantified limitation; leave all numerical results unfilled.
