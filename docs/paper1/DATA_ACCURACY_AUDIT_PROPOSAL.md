# Paper 1 — Capstone v1 data-accuracy audit

**BEFORE RECORD · v1.0 · OWNER-APPROVED SPECIFICATION · 2026-11-03 · NOT SAMPLED / NOT EXECUTED.**
Research support only; not investment advice.

This freezes the owner-approved specification as a before record. It does not
establish source availability, rights, KER-13b completeness, or authorize a draw,
retrieval, source inspection, comparison, or protected-period access. This audit
describes the frozen Capstone v1 inputs only; it is not a predictive test, a
population-wide vendor assessment, or a correction to the frozen record. It does
not substitute the capstone cohort for the new research universe.

**Decision provenance:** explicit owner decision dated 2026-11-03 and recorded at
2026-11-03 21:24:35 Europe/Zurich. The specification is frozen as a BEFORE record;
unapproved implementation and source-evidence details below remain UNSET.

## Frozen scope and sample

- **Frame:** Capstone v1 firm-years with fiscal years 2020–2022.
- **Sample:** 30 observations, simple random sampling without replacement, seed
  `20261103`.
- Do not enumerate the frame or draw the sample until the date/access conflict below
  is prospectively resolved. No company-year has been selected and no audit source
  values have been read.
- The owner-approved design fixes SRSWOR and the seed, but not the stable frame
  serialization or RNG/runtime. These draw-implementation details remain **UNSET**;
  freeze them before any draw and do not select a sample from this record alone.
- Use the original, first-filed KAP annual consolidated statement for each fiscal
  year. Do not substitute a restated comparative, later filing, current summary
  screen, or inflation-rebased history.

The original proposal's publication/access boundary ended on 2022-12-31. A first
annual filing for FY2022 may have been published in 2023, while the Research Charter
places 2023–2025 in a protected holdout period. Fiscal-year labels do not establish
publication dates. This conflict is **UNSET** and blocks frame enumeration, the draw,
and access to affected source material. Do not read, inspect, or infer any 2023–2025
source or holdout fact under this record. Resolve the boundary prospectively under
the governing Charter and registered-access rules, with owner approval and any
required Charter amendment, before proceeding. Do not silently narrow the approved
frame to FY2020–2021 or reinterpret the publication boundary.

## Financial fields and original KAP comparison

Compare exactly these five fields from the proposal:

1. Annual revenue.
2. Annual profit attributable to owners of the parent.
3. Period-end total assets.
4. Period-end equity attributable to owners of the parent.
5. Net margin, defined as 100 × annual profit attributable to owners of the parent
   divided by annual revenue, in percentage points. Zero or missing revenue makes
   this field non-comparable.

The capstone values must come from the frozen Capstone v1 financial input stream.
The comparison value must come from the original first-filed annual consolidated
KAP statement for the same issuer and fiscal period. Retain the supporting evidence
locally: KAP disclosure identifier and publication time, document hash, page/table/
line, statement type, reporting unit, currency, sign, period basis, and the exact
mapping used. Do not place source values or identifiers in public issues, pull
requests, or remote-agent prompts.

**Tolerance.** After exact, evidence-backed conversion to a common currency and
scale, calculate relative difference as `abs(capstone_value - KAP_value) /
abs(KAP_value)` when `KAP_value != 0`. If the KAP value is zero, relative difference
is undefined and only the absolute rule applies. A pair matches when relative
difference is at most `0.005` **OR** the absolute difference is at most one unit at
the original KAP statement's reported scale, converted exactly to the comparison
currency. Do not round values before applying either rule. If exact unit/basis
normalization or field comparability cannot be evidenced, mark the pair
NOT-COMPARABLE; do not guess a mapping or transformation.

For the four directly reported monetary fields, the absolute unit is one unit at
the original KAP statement's displayed monetary scale. Net margin is a derived
percentage-point field; its corresponding KAP-reported ratio precision and thus
the one-unit absolute tolerance are **UNSET**. Do not transfer a monetary scale to
the ratio, infer display precision, or classify a net-margin pair until its
prospective, evidence-based precision rule is frozen. This does not change the
owner-approved relative-difference rule.

Aliases, KAP template and statement-line identifiers, consolidation/period mapping,
and correction-vintage adjudication remain **UNSET** until established from
authorized, rights-cleared evidence. An unknown vintage, basis, currency, scale, or
mapping is not backfilled. Missing values remain null; they are not imputed and do
not trigger row replacement.

## Conditional price checks

When legitimate LSEG/DataStore price values and the necessary source/right evidence
are available, conditionally check the two price fields in the original proposal:
raw year-end official close and nominal-TRY calendar-year total shareholder return
with gross cash dividends reinvested on ex-date and evidenced share/rights actions.
LSEG is the primary source, DataStore is the cross-check, and Yahoo is
development-only. This source-role choice does not establish access, a licensed
snapshot, comparator independence, or the semantics of the frozen legacy fields.

Before any price comparison, establish the frozen legacy field meaning, source
lineage and snapshot; trading-session calendar; endpoint, non-trading and delisting
treatment; corporate-action and reinvestment basis; exact price/return precision;
and applicable rights for each operation. These implementation and evidence details
remain **UNSET** where not already evidenced. Do not fetch data, use a wrapper over
the same upstream feed as independent evidence, carry values forward, or treat a
different adjustment basis as an error without evidence. No price checks run until
these gates and the protected-period boundary are resolved.

## Statuses, denominator, and release

For each field, record local statuses MATCH, MISMATCH, MISSING, or
NOT-COMPARABLE, with reasons. Missing and non-comparable pairs stay null and are
excluded from the comparable-pair denominator; no imputation or replacement is
allowed. The local match rate is matches divided by comparable, non-missing pairs.
If that denominator is zero, the match rate and interval are unavailable, not zero.

For any field with a nonzero denominator, calculate a two-sided 95% Wilson score
interval using `z = 1.959963984540054`. For match rate `p` and denominator `n`,
the Wilson centre is `(p + z²/(2n)) / (1 + z²/n)` and the half-width is
`z × sqrt(p(1-p)/n + z²/(4n²)) / (1 + z²/n)`; report centre ± half-width, bounded
to [0,1]. Retain row-level evidence, denominators, missing/non-comparable reasons,
and calculations locally. The only released numeric results are the per-field
match rates and corresponding Wilson 95% intervals; do not release row counts,
denominators, sample identities, observation values, differences, returns,
rankings, source excerpts, or microdata. Explain that rates are conditional on
comparable pairs and do not establish overall input accuracy.

## Access and execution gates

- The financial comparison waits for a rights- and procedure-cleared KER-13b Kernel
  snapshot containing the required original-first-filed values. The outcome-free
  request at [`kernel_request_data_accuracy_20261103.md`](kernel_request_data_accuracy_20261103.md)
  asks only for availability/scope status. It does not request a Kernel edit,
  acquisition, execution plan, sample values, or output transfer.
- Price comparisons wait for the conditional gates above and legitimate LSEG and
  DataStore access. All comparison work and evidence stay local.
- Preserve FO-0, the locked 2023–2025 holdout, immutable historical records, and the
  closed KAP/BIST-announcement/Product 3184 rights decisions. No holdout opening,
  return or performance access, model execution, FIQ-17/18 execution, or journal
  submission is authorized here.
- Record any later authorized attempt, failure, abandonment, or deviation in the
  applicable append-only records, with actual occurrence and recording times. Never
  backdate, reroll, replace a sampled observation, alter a field after seeing a
  result, or overwrite frozen evidence. A prospective amendment is required for a
  specification change.

This record contains no results. Until each applicable gate is separately met and
the comparison is lawfully and procedurally available, audit rates remain
**UNAVAILABLE** and the manuscript may state only the unquantified owner-reported
concern as a limitation.
