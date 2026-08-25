# FI-DATA-EXPAND-04B-P3184-2020-01 — Product 3184 2020 acquisition, revision and Q4 reconciliation

**Task date:** 2026-08-24
**Starting repository:** `main` at `c719982fd7eae31dc57c4e4d769d7122d63e3d3e`
**Decision:** `FI_DATA_EXPAND_04B_P3184_2020_LOGIN_REQUIRED`

This is an outcome-blind task. It inspected Borsa İstanbul DataStore **Product
3184** first-party catalogue metadata for 2020, established the complete 2020
object inventory, and stopped at the documented owner-decision gate before any
account registration or agreement acceptance. **As of that task (2026-08-24), no
Product 3184 data file had been downloaded, opened, parsed, or reconstructed by
it.** That statement describes §§1–15 only and is superseded for the 01-10-2020
publication by the §16 addendum and for the acquisition boundary of all seven
2020 objects by the §17 provenance correction; it must not be read as a
present-tense claim about the evidence state. No modeling dataset, benchmark,
model, return, or outcome was touched or inspected.

Research support only; not investment advice. The repository's scientific
position is unchanged: **no reliable predictive edge has been established**, and
nothing in this document bears on that question.

## 1. Gate

The starting gate passed:

- exact repository `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ`;
- branch `main`, `HEAD == origin/main == c719982fd7eae31dc57c4e4d769d7122d63e3d3e`;
- clean worktree including untracked files;
- all prior governance and 04B evidence present —
  [Stage A](PREREGISTERED_DATA_EXPANSION_STAGE_A.md),
  [owner amendment](SOURCE_USE_OWNER_AMENDMENT.md),
  [sourcing report](DATA_EXPANSION_MEMBERSHIP_SOURCING_REPORT.md),
  [event-coverage audit](BIST_MEMBERSHIP_EVENT_COVERAGE_AUDIT.md),
  [KAP trigger audit](BIST_MEMBERSHIP_KAP_TRIGGER_AUDIT.md),
  [2020-10-01 collision audit](BIST_MEMBERSHIP_2020_10_01_COLLISION_AUDIT.md),
  and their four evidence manifests;
- protected boundary `351` members;
- protected boundary SHA-256
  `98195607983a35d3ffc8996934be9ac1b808250a659fea126a1a9636e800cee5`,
  recomputed live from the `experiments/run_excess_basis.py` frozen-boundary
  authority and matching the expected digest exactly.

## 2. Result codes

| Question | Result |
| --- | --- |
| DataStore access | `NO_EXISTING_OWNER_SESSION` — the product page renders the anonymous *Giriş* control, every catalogue object reports `inLibrary: false`, and no authenticated session exists |
| Continuation requirement | `REGISTRATION_AND_AGREEMENT_ACCEPTANCE_REQUIRED` — the combined *Giriş/Kayıt* dialog requires acknowledging the KVKK notice and accepting the **Kullanıcı Kayıt Sözleşmesi** |
| 2020 object inventory | `COMPLETE` — 7 catalogue objects, fully enumerated below |
| Revision semantics | `REVISION_SEMANTICS_UNRESOLVED` |
| Raw acquisition | ~~`NONE` — no `exsrk2020.zip` object acquired~~ → superseded 2026-08-25: archive material for all seven 2020 objects exists in the private evidence archive; two are at `ACQUIRED_OBJECT_BINDING_BY_DECLARED_SIZE` and five at `ARCHIVE_PRESENT_NOT_OBJECT_BOUND` (see §17) |
| Format verification | ~~`NOT_VERIFIED_NO_FILE_ACQUIRED`~~ → superseded 2026-08-25 for the 01-10-2020 publication (§16.2); the §6 documentation-currency discrepancy still stands as written |
| Q4 row extraction | ~~`0 rows`~~ → `100 rows` (2026-08-25, see §16.3) |
| Nested-count reconciliation | ~~Not evaluable — neither `NESTED_COUNTS_RECONCILED` nor `NESTED_COUNTS_MISMATCH` can be issued without rows~~ → superseded 2026-08-25: `NESTED_COUNTS_RECONCILED` for XU030 and XU100 against the official 2020-10-01 Günlük Bülten; XU050 nested-expanded count (50) is now observable but unreconciled against an independent first-party source — `XU050_SEED_STATE_UNRESOLVED` stands (see §16.3) |
| 2020-10-01 collision reconciliation | `NOT_PERFORMED` — the prior audit stands unchanged and unreinterpreted |
| XU050 seed state | `XU050_SEED_STATE_UNRESOLVED` |
| Revision canonicalization | ~~`REVISION_CANONICALIZATION_UNRESOLVED`~~ → `REVISION_CANONICALIZATION_RESOLVED` (2026-08-25, see §16) |
| Q4 state | ~~`Q4_STATE_UNRESOLVED`~~ → `Q4_STATE_RESOLVED` (2026-08-25, see §16) |

## 3. DataStore access result

The Product 3184 page and its catalogue API were reached anonymously, exactly as
in the prior sourcing task. The header renders **Giriş** (log in), the basket
shows `0` items at `0.00`, and every catalogue object carries `inLibrary: false`
— there is no authenticated owner library and therefore **no pre-existing
legitimate owner session to use**.

Opening the *Giriş* control renders a single combined login/registration dialog
whose gate text is:

- `Kişisel Verilerin Korunması Aydınlatma Metni'ni okudum ve anladım`
- `Kullanıcı Kayıt Sözleşmesini okudum, kabul ediyorum`
- `Giriş/Kayıt`

Continuing past that dialog requires **creating an account and accepting a user
registration agreement**. Under `FI-SOURCE-OWNER-AMENDMENT-01` that is a new
contractual entitlement, and autonomous acceptance of a new agreement on the
owner's behalf is explicitly outside owner authorization. The task therefore
stopped there.

Nothing was typed into the dialog, no checkbox was ticked, no credential was
entered, no basket item was added, no checkout was started, no download URL was
guessed, and no authentication, rate limit, or access control was probed or
circumvented. The gate is **contractual, not monetary** — the 2020 files are
priced at `0.0 TRY`.

## 4. Complete 2020 catalogue inventory

Seven Product 3184 objects exist for 2020, at catalogue positions 25–31 of 66.
All seven share the displayed filename `exsrk2020.zip`, data-definition id `173`,
`period = Q`, `accessType = G`, `dateFormat = yyyy`, `price = 0.0 TRY`,
`inLibrary = false`, and provider `date` field `30-12-2020`.

| Order | Object id | Publication (`createDate`) | Declared size (bytes) | Prior manifest row |
| --- | --- | --- | --- | --- |
| 25 | `3184#1132521` | 01-10-2020 | 58,631 | `BM-031` |
| 26 | `3184#1132519` | 01-10-2020 | 58,823 | `BM-032` |
| 27 | `3184#1068011` | 28-07-2020 | 59,259 | `BM-033` |
| 28 | `3184#1006269` | 22-05-2020 | 57,733 | `BM-034` |
| 29 | `3184#982927` | 27-04-2020 | 55,195 | `BM-035` |
| 30 | `3184#982925` | 27-04-2020 | 56,407 | `BM-036` |
| 31 | `3184#872590` | 02-01-2020 | 55,016 | `BM-037` |

The per-object manifest is
[bist_membership_p3184_2020_sources.csv](evidence/bist_membership_p3184_2020_sources.csv).

The four catalogue-listing pages backing this table were re-fetched on
2026-08-24 and archived privately. Their SHA-256 digests are **byte-identical**
to the 2026-08-23 snapshots already recorded in
[bist_membership_source_manifest.csv](evidence/bist_membership_source_manifest.csv)
(rows `BM-003`–`BM-006`), so the Product 3184 catalogue did not drift between
the two access dates and the seven-object 2020 inventory is stable across
independent accesses.

### 4.1 What the catalogue does not contain

Checked field by field against the raw catalogue records, **none** of the
following exists anywhere in a Product 3184 object record:

- a revision, version, or edition indicator;
- a `supersedes` / `superseded_by` / `replaces` relationship;
- a language or variant marker;
- an effective, as-of, or valid-from date;
- any free-text note explaining why a year carries multiple objects.

The provider `date` field is `30-12-2020` for **all seven** objects. It is
therefore a nominal year label, not a discriminator and not an effective date.

## 5. Revision semantics — `REVISION_SEMANTICS_UNRESOLVED`

None of the five permitted classifications can be asserted from catalogue
metadata alone, and three specific facts block the naive resolutions:

1. **Two objects share each of two publication dates.** `3184#1132521` and
   `3184#1132519` were both published 01-10-2020 at 58,631 and 58,823 declared
   bytes; `3184#982927` and `3184#982925` were both published 27-04-2020 at
   55,195 and 56,407 declared bytes. The catalogue supplies nothing that
   distinguishes either pair, so "latest publication date" does not even select
   a unique object.

2. **Declared size is not monotonic across 2020.** Ordered by publication —
   55,016 (02-01) → 55,195 and 56,407 (27-04) → 57,733 (22-05) → 59,259 (28-07)
   → 58,631 and 58,823 (01-10) — the **newest** 2020 objects are *smaller* than
   the 28-07-2020 object. The
   [sourcing report §4.5](DATA_EXPANSION_MEMBERSHIP_SOURCING_REPORT.md) recorded
   monotonic within-year growth for 2025 as weak corroboration that quarter
   columns are populated progressively. **2020 breaks that pattern.** Whatever
   the explanation, "newest is the superset" is not supported for 2020.

3. **No supersession relation is published.** Absent a revision field, a later
   object may be a correction, a re-cut, a partial re-upload, a variant, or an
   unrelated regeneration. The catalogue does not say, and inventing an
   interpretation would violate Stage A.

Per §4 of the task specification, one object was therefore **not** silently
chosen as canonical.

### 5.1 The material 2020 hazard this exposes

The last 2020 object was published **2020-10-01** — the exact date on which the
Şişecam merger took effect and the Q4 BIST 30/50/100 review period began, as
established by the
[2020-10-01 collision audit](BIST_MEMBERSHIP_2020_10_01_COLLISION_AUDIT.md).
No 2020 object was published after that date. Two open branches follow, and the
catalogue cannot decide between them:

- if a quarter column is populated at quarter **start**, the 01-10-2020 objects
  may record the Q4 column before or after the same-day merger took effect, and
  no later 2020 republication exists to correct it;
- if a quarter column is populated at quarter **end**, the Q4 column of every
  2020 object may be unpopulated, in which case the exsrk2020 series would not
  carry 2020 Q4 membership at all.

The declared-size non-monotonicity in §5 item 2 is consistent with either branch and
proves neither. **This is resolvable only from acquired bytes**, and it is the
single most consequential unknown for 2020.

## 6. Format verification — `NOT_VERIFIED_NO_FILE_ACQUIRED`

No file was acquired, so no sheet name, column set, row count, encoding, blank
convention, duplicate-ticker handling, or index-code vocabulary could be
observed.

One discrepancy is flagged for the future acquisition task. The Product 3184
page's own **Alan Adları** (field names) block currently reads:

> `PAY KODU, PAY ADI, BULUNDUĞU ENDEKS`

— three fields. The DataStore file-format specification v1.4 (15.06.2016),
recorded as manifest row `BM-001` and summarised in
[sourcing report §4.1](DATA_EXPANSION_MEMBERSHIP_SOURCING_REPORT.md), documents
**six**: `Pay Kodu`, `Pay Adı`, `1.Çeyrek`, `2.Çeyrek`, `3.Çeyrek`, `4.Çeyrek`.
The product page also warns that field names may vary over time because of the
systems that produced the data.

Which layout an acquired `exsrk2020.zip` actually carries is `UNKNOWN`. The
four-quarter layout must be **verified against the acquired file** before any
parser is written; the three-field product-page description must not be assumed
to supersede the specification, and the specification must not be assumed to
survive the product-page description.

## 7. Q4 row extraction — ~~0 rows~~ → superseded 2026-08-25, see §16.3

**Historical (2026-08-24):**
[bist_membership_p3184_2020_q4_rows.csv](evidence/bist_membership_p3184_2020_q4_rows.csv)
carried the pre-registered task-specification Q4-row schema and **zero data
rows** at that time. No ticker, company name, index value, or membership flag
had been derived, estimated, or inferred. Literal index-code counts and
nested-expanded XU030/XU050/XU100 counts were consequently **unavailable**,
not zero.

**Current (2026-08-25):** the same file now carries **100** Q4 (2020-10-01)
membership rows. See §16.3 for the extraction and §17 for the provenance
correction to the acquisition boundary underlying it.

## 8. Nested-index semantics — rule restated, not applied

The documented rule is unchanged and remains the decisive parsing rule for the
future acquisition task. Per the DataStore file-format specification, the
indices successively contain one another and only the narrowest index a share
belongs to is written:

| Cell value | Implied membership that quarter |
| --- | --- |
| `XU030` | BIST 30 **and** BIST 50 **and** BIST 100 |
| `XU050` | BIST 50 **and** BIST 100 |
| `XU100` | BIST 100 only |
| empty | none of the three |

With zero rows there is nothing to expand and nothing to count, so neither
`NESTED_COUNTS_RECONCILED` nor `NESTED_COUNTS_MISMATCH` is issued. Reading only
literal `XU100` cells as the BIST 100 universe remains prohibited.

## 9. 2020-10-01 collision reconciliation — not performed

The [collision audit](BIST_MEMBERSHIP_2020_10_01_COLLISION_AUDIT.md) and its
result `FI_DATA_EXPAND_04B_COLLISION_2020_RESOLVED` are treated as authoritative
prior evidence. **Neither the audit nor its manifest was edited, reinterpreted,
or weakened by this task.**

Row-level reconciliation requires Q4 rows, of which there are none. Its
prerequisite therefore remains exactly what the prior audit recorded:
`RECONCILIATION_REQUIRES_PRODUCT_3184_ROWS`.

The checks that remain outstanding, restated so the future task inherits them
unchanged, are: SISE present in Q4 XU030/XU050/XU100 as the surviving code;
ANACM, DENCM, SODA and TRKCM absent from the Q4 state as absorbed codes;
Paşabahçe treated only as legal-succession context and never as an index
identity; the published Q4 additions and removals reflected; reserves treated as
published eligibility lists rather than memberships; and the nested-expanded Q4
counts checked against expected index sizes. Every row-level classification in
task §11 is unassigned because no row exists to classify.

## 10. XU050 seed state — `XU050_SEED_STATE_UNRESOLVED`

The prior audit left XU050 seed-state reconciliation open specifically because
the official 2020-10-01 Günlük Bülten flags BIST 100 and BIST 30 membership but
does not flag BIST 50. Product 3184 is the source that would close it, because
its narrowest-index encoding makes XU050 directly observable. Without acquired
rows the gap is unchanged.

## 11. Revision canonicalization — `REVISION_CANONICALIZATION_UNRESOLVED`

No 2020 raw object was acquired, so no mechanical comparison of identical,
changed, added, or removed rows was possible, and no supersession claim is made.
File modification timestamps were not used as authority, in line with task §13.

## 12. 2020 year-level interpretation — `Q4_STATE_UNRESOLVED`

Product 3184 Q4 evidence for 2020 is **not** confirmed. This task closes neither
the Product 3184 Q4 source state nor the 2020-10-01 row-level reconciliation.

2020 is **not** promoted toward Stage-B eligibility, and this document must not
be cited as partial progress toward that promotion. A separate year-level
closure adjudication remains required for the rest of the 2020 extraordinary-
stream and identity requirements, and it cannot begin while the Q4 source state
is unresolved.

## 13. No-peeking compliance

`NO_NEW_OUTCOME_INSPECTION=true`.

No modeling dataset, `experiments/results_*` artifact, `next_year_*` column,
future-return artifact, benchmark-relative outcome, IC report, p-value, model
score, or model ranking was opened or inspected. `make data`, `make benchmark`,
`make research`, and `make research-excess` were not run. The only Python
executed against the repository was the frozen-boundary digest recomputation
required by the starting gate, which reads file hashes and no data values.

## 14. Private raw archive

Four objects were archived under
`~/Documents/FinanceIQ-private-source-archive/bist-membership/raw/p3184-2020/`,
verified to be outside the repository before writing. All four are Product 3184
**catalogue-metadata JSON pages**: they contain object ids, filenames,
publication dates, declared sizes, prices and access types, and **no membership
row, ticker, company name, or index code**. Their digests are recorded in the
source manifest and their bytes are `PRIVATE_LOCAL_RAW`.

No raw third-party ZIP, XLS, XLSX, PDF or HTML bytes were added to Git. No file
under `data/` or `data/provenance/` was created or modified.

## 15. What the owner must decide next

This task is blocked on a decision only the owner can make, and it is a decision
about an agreement, not about money:

1. **Register a DataStore account and accept the Kullanıcı Kayıt Sözleşmesi
   personally, or decline.** The 2020 files are free. If the owner registers and
   signs in, the acquisition task becomes runnable under an existing legitimate
   session with no further contractual gate.
2. **If the owner registers**, the minimum acquisition set for 2020 is the four
   objects needed to bound the revision question — both 01-10-2020 objects
   (`3184#1132521`, `3184#1132519`), the 28-07-2020 object (`3184#1068011`) to
   test the size non-monotonicity, and one earlier object as a baseline. That is
   the minimal set that can distinguish the two branches in §5.1; a bulk
   2000–2026 download remains prohibited.
3. **If the owner declines**, 2020 Q4 membership stays unsourced from Product
   3184, and any 2020 point-in-time reconstruction claim stays unavailable.

Neither outcome changes the scientific position. Sourcing progress is not
evidence of predictive value, and no reliable predictive edge has been
established.

## 16. Addendum (2026-08-25) — FI-DATA-EXPAND-04B-P3184-Q4-RESOLUTION

**This addendum is documentation and evidence reconciliation only.** It
followed the owner's out-of-band decision to supply an already-downloaded
private evidence archive rather than register a DataStore account; the
gate described in §3 and §15 was not re-attempted, no DataStore session was
established, and no browser automation or authentication was performed
against DataStore. All bytes referenced below came from
`~/Documents/FinanceIQ-private-source-archive/P3184_2020/exsrk2020_all/`,
a location outside this repository.

### 16.1 Acquired evidence reference

**Corrected 2026-08-25 — see §17.** The object↔file attribution originally
printed in this table was inverted. The table below is re-derived from actual
on-disk file identity (SHA-256 of each archive file, plus a ZIP-member CRC-32
check binding each archive file to its extracted workbook).

| File | SHA-256 | Size on disk | Catalogue object (declared size match only) |
| --- | --- | --- | --- |
| `exsrk2020 (1).zip` (candidate A) | `ed59e80e386c9b54058215996ef186849aa3bca144e0cc7f59227f92a889d73c` | 58,631 bytes | `3184#1132521` (declared 58,631) |
| `exsrk2020.zip` (candidate B) | `5ad33b895bea97647ed6809f45609f2fc0782fa9f887117aa59c26ae1cf145a8` | 58,823 bytes | `3184#1132519` (declared 58,823) |
| Extracted `exsrk2020.xls` from candidate A | `de44aa20b70d2021d8301a726a157e3d92525a7a91690ed1ebfece06259ceb34` | 420,864 bytes | — |
| Extracted `exsrk2020.xls` from candidate B | `45963bdbb706eee8105fa70967ffc02ba7d029649ca53c19a18547101bac3ac2` | 421,888 bytes | — |
| Converted CSV export, **both** candidates (byte-identical) | `4385ae8e6e7b7335add4a1072ad455c6cee317f75b9d2dc5000f7c61ed008892` | 436 lines × 7 columns | — |

The archive-file identities in column 2 are confirmed by digest. The catalogue
column is weaker: **private archive file identity confirmed; catalogue object
assignment based on declared size match only.** No provider-side digest,
per-object download URL, or other independent identifier was available to bind
an archive file to a catalogue object id, so the fourth column rests on the
seven 2020 declared sizes being pairwise distinct and matching the seven
archive files one-to-one. It is not proof of object identity.

Both extracted workbooks and both source ZIPs remain `PRIVATE_LOCAL_RAW`. No
ZIP or XLS bytes were added to this repository. The full acquisition-row
detail is recorded as source_ids `P3184-2020-12`, `P3184-2020-13`, and
`P3184-2020-Q4-EVIDENCE` in
[bist_membership_p3184_2020_sources.csv](evidence/bist_membership_p3184_2020_sources.csv).

### 16.2 Revision canonicalization — `REVISION_CANONICALIZATION_RESOLVED`

Both 01-10-2020 catalogue candidates identified in §5 item 1 were extracted
and their workbooks converted to CSV. Result: **436 lines × 7 columns** in
both converted exports, and a full-file comparison found **zero differing
cells** — the two exports are in fact byte-identical, SHA-256
`4385ae8e6e7b7335add4a1072ad455c6cee317f75b9d2dc5000f7c61ed008892`.

The two extracted workbook files carry different SHA-256 digests.
**Converted CSV exports were cell-identical. Binary workbook files differed,
but the exact binary-level cause was not fully attributed.** No claim is made
here about which regions of the binary differ or why.

Conclusion: the two catalogue candidates for the 01-10-2020 publication have
**byte-identical converted CSV projections** (SHA-256
`4385ae8e6e7b7335add4a1072ad455c6cee317f75b9d2dc5000f7c61ed008892`). The two
extracted binary workbook files themselves differ (§17.1), and full workbook
semantics — formulas, hidden sheets, formatting, or binary-level equivalence —
were **not** established for either file. The equivalence claim is scoped to
the extracted-and-converted CSV output only, not to the source workbooks. The
§5 item 1 observation that the catalogue cannot distinguish the pair by
metadata alone still stands as a description of catalogue-metadata limits; it
is no longer a live ambiguity for the converted row content, because both
candidates' conversions resolve to the same rows.

This does not resolve the size non-monotonicity noted in §5 item 2 (the
28-07-2020 object remains larger by declared size than either 01-10-2020
object) and does not, by itself, characterize the other five 2020 objects,
which were not part of this evidence set.

### 16.3 Q4 membership extraction — `Q4_STATE_RESOLVED`

The workbook's `2020-10-01` column (Q4) was extracted: **100 rows**, no
blank or malformed cells, matching the pre-registered schema. Because the two
candidates' converted exports are byte-identical (§16.2), this extraction is
supported identically by either candidate and is **not** bound to a single
catalogue object id. Row-level values are recorded in
[bist_membership_p3184_2020_q4_rows.csv](evidence/bist_membership_p3184_2020_q4_rows.csv)
(100 data rows; source_id `P3184-2020-Q4-01`).

Nested-expanded nested-index counts (per the §8 rule):

| Index | Literal cell count | Nested-expanded membership |
| --- | --- | --- |
| XU030 | 30 | 30 (also counted in XU050 and XU100) |
| XU050 | 20 | 50 (20 + 30, also counted in XU100) |
| XU100 | 50 | 100 (50 + 20 + 30) |

The nested-expanded XU100 count of 100 matches the official 2020-10-01
Günlük Bülten's reported 100-member BIST 100, corroborating both the
nested-index reading rule and the extraction. `NESTED_COUNTS_RECONCILED`
against that external reference for XU100. XU030 (30) also matches the
official bulletin's reported 30-member BIST 30. XU050 has no independent
official count on record for this date (§10, `XU050_SEED_STATE_UNRESOLVED`
in the source task), so `XU050_SEED_STATE_UNRESOLVED` for the 50-count is
**not** newly closed by this addendum — it is now directly *observable*
from Product 3184 (50 members), but no independent first-party figure
exists yet to reconcile it against.

### 16.4 Glass group reconciliation evidence — snapshot only, not full reconciliation

Within the 100 Q4 rows, the tracked predecessor/successor group from the
[collision audit](BIST_MEMBERSHIP_2020_10_01_COLLISION_AUDIT.md) resolves
as:

| Code | Q4 2020 state |
| --- | --- |
| `SISE` | present, `XU030` |
| `ANACM` | absent |
| `DENCM` | absent |
| `SODA` | absent |
| `TRKCM` | absent |

This is consistent with the collision audit's `SISE` surviving-code finding
and `ANACM`/`DENCM`/`SODA`/`TRKCM` absorbed-code finding, and corroborates
those with a first-party Product 3184 membership row rather than the daily
bulletin alone. **No merger mechanics are inferred beyond this membership
snapshot** — this addendum observes presence/absence only.

The row-level reconciliation checklist restated in §9 (index additions and
removals, reserve treatment, nested-expanded counts checked against
expected sizes) is **not fully closed** by this addendum. Only the
surviving/absorbed-code presence check and the XU030/XU100 nested-expanded
counts (§16.3) were verified. Full row-level reconciliation against every
item in §9's checklist — in particular the exact ADD/REMOVE sets and
reserve-consumption cross-check — remains open and is not claimed here.

### 16.5 Status changes

| Item | Previous | New | Basis |
| --- | --- | --- | --- |
| Revision canonicalization | `REVISION_CANONICALIZATION_UNRESOLVED` | `REVISION_CANONICALIZATION_RESOLVED` | §16.2 — both 01-10-2020 candidates extracted, content-equivalent, 0 differing cells |
| Q4 state | `Q4_STATE_UNRESOLVED` | `Q4_STATE_RESOLVED` | §16.3 — 100 Q4 rows extracted, nested counts reconcile against official XU030/XU100 bulletin figures |

### 16.6 What remains unresolved

- Full 2020-10-01 row-level reconciliation per §9's checklist (exact
  ADD/REMOVE sets, reserve consumption) beyond the surviving/absorbed-code
  presence check in §16.4.
- `XU050_SEED_STATE_UNRESOLVED` for an independent first-party 50-count to
  reconcile against (the count is now observable from Product 3184, 20
  literal / 50 nested-expanded, but unreconciled against a second source).
- The other five 2020 catalogue objects (02-01, 27-04 ×2, 22-05, 28-07) were
  not reconciled by this addendum. **Corrected 2026-08-25 (§17):** archive
  material for them *does* exist and is now recorded, at status
  `ARCHIVE_PRESENT_NOT_OBJECT_BOUND`. §5's revision semantics for the full
  2020 series (in particular the 27-04-2020 pair and the size
  non-monotonicity in §5 item 2) are unaffected — no row-level comparison,
  ADD/REMOVE determination, or canonical-revision conclusion was made for
  any of the five.
- 2020 is **not** promoted to Stage-B eligibility by this addendum alone.
  This is a Q4 2020 membership and revision-candidate resolution only, not
  a full 2020 year-level closure adjudication (§12).
- This addendum does not claim complete historical BIST membership
  reconstruction for 2020 or any other year.

## 17. Provenance correction (2026-08-25) — FI-DATA-EXPAND-04B-P3184-2020-PROVENANCE-REPAIR

**This section is a provenance and wording repair only.** It expands no
conclusion, promotes no status, and derives no new membership fact. It corrects
three defects found by the final audit of the §16 addendum: an inverted
object↔file attribution, an over-attributed binary-difference claim, and a false
acquisition boundary for five catalogue objects. No ZIP, XLS, Q4 evidence CSV,
trusted data file, or model file was modified; only this document,
[bist_membership_p3184_2020_sources.csv](evidence/bist_membership_p3184_2020_sources.csv),
and `TASK_STATE.md` were edited.

### 17.1 Correction A — binary-difference wording withdrawn

The §16.2 sentence that attributed the two extracted workbooks' byte differences
to a specific container-metadata region, named specific metadata fields, cited
specific byte offsets, and declared the difference to lie outside the sheet data
**is withdrawn** in this document, in the sources manifest, and in
`TASK_STATE.md`. It asserted a binary-level cause that the recorded evidence
does not establish. The withdrawn wording is not reproduced here; the prior text
is recoverable from this file's Git history if it is ever needed.

What is retained is exactly what was measured:

> Converted CSV exports were cell-identical. Binary workbook files differed, but
> the exact binary-level cause was not fully attributed.

The cell-equality result is unchanged and is now stated in its strongest
verifiable form: the two converted CSV exports are byte-identical, SHA-256
`4385ae8e6e7b7335add4a1072ad455c6cee317f75b9d2dc5000f7c61ed008892`, 436 lines ×
7 columns each. `REVISION_CANONICALIZATION_RESOLVED` rests on that equality
alone; it never rested on the binary claim, and it is unchanged.

The §16.2 phrase "436 data rows" is also corrected to "436 lines", the measured
quantity: the converted export's 436 lines include a header line and quarter
banner lines, so 436 is not a count of membership rows.

### 17.2 Correction B — object↔archive-file attribution rebound

The §16.1 table and manifest rows `P3184-2020-12` / `P3184-2020-13` paired each
catalogue object with the *other* archive file's name and digest, and with a
byte count belonging to neither pairing consistently. Re-derived from disk:

| Archive file | Size on disk | SHA-256 | Extracted `exsrk2020.xls` | XLS size |
| --- | --- | --- | --- | --- |
| `exsrk2020 (1).zip` | 58,631 | `ed59e80e…a889d73c` | `de44aa20…06259ceb34` | 420,864 |
| `exsrk2020.zip` | 58,823 | `5ad33b89…1cf145a8` | `45963bdb…101bac3ac2` | 421,888 |

Each archive file is bound to its extracted workbook by a ZIP-member CRC-32
check, not by directory naming. Catalogue objects then attach by declared size:
`3184#1132521` declares 58,631 and `3184#1132519` declares 58,823 (§4).

The limit of that attachment is stated explicitly and is not to be strengthened
without new evidence:

> **private archive file identity confirmed; catalogue object assignment based
> on declared size match only.**

No provider-side digest, per-object download URL, or other independent
identifier exists in the catalogue record (§4.1), so declared size is the only
available link. The seven 2020 declared sizes are pairwise distinct and match
the seven archive files one-to-one, which makes the assignment consistent — it
does not make it proven.

### 17.3 Correction C — acquisition boundary for `P3184-2020-07`…`-11`

Manifest rows `P3184-2020-07` through `-11` (objects `3184#1068011`,
`3184#1006269`, `3184#982927`, `3184#982925`, `3184#872590`) previously recorded
`raw_sha256 = NA`, `raw_bytes = NA`, `raw_storage_class = NOT_ACQUIRED`, and the
note "unverified because the object was not downloaded". That boundary was
false: the private evidence archive holds a corresponding ZIP for each, and each
ZIP's extracted workbook material exists on disk.

Each row now records the archive file's actual name, SHA-256, and byte count,
plus the extracted workbook's SHA-256 and size, with the ZIP-member CRC-32 check
binding the two. Declared-size match to the catalogue object follows the same
size-only limit as §17.2.

What was **not** done for these five, and is not claimed anywhere:

- no row-level reconciliation;
- no ADD/REMOVE determination;
- no canonical-revision or supersession conclusion;
- no membership value read, derived, or recorded.

The extractions were inspected structurally only — file presence, digest, size,
and archive-member binding. §5 (`REVISION_SEMANTICS_UNRESOLVED`) and §5 item 2
(declared-size non-monotonicity) are untouched by this correction.

### 17.4 Provenance status vocabulary

Every provenance status token used in
[bist_membership_p3184_2020_sources.csv](evidence/bist_membership_p3184_2020_sources.csv),
including the two introduced by this correction:

| `provenance_status` | Meaning |
| --- | --- |
| `ACQUIRED` | The named file was obtained and its bytes are identified by the recorded SHA-256. Used for the catalogue-metadata JSON snapshots, whose identity needs no further binding because the request URL is itself the identifier. |
| `VISIBLE_NOT_ACQUIRED` | The catalogue object was observed in the provider's catalogue, but no bytes for it were held at the time the row was written. Rows `P3184-2020-05` and `-06` retain this status: they are pure catalogue-observation rows, and the archive evidence for the same two objects is carried by rows `-12` and `-13`. |
| `ARCHIVE_PRESENT_NOT_OBJECT_BOUND` | **New (2026-08-25).** A file in the private evidence archive is present and its own identity is confirmed by SHA-256, but its binding to *this* catalogue object id is not proven — it rests on declared-size match alone — and no content-level reconciliation has been performed. Applied to `P3184-2020-07`…`-11`. |
| `ACQUIRED_OBJECT_BINDING_BY_DECLARED_SIZE` | **New (2026-08-25).** As `ACQUIRED` for the file's own identity, and the file's content *has* been converted and compared, but the catalogue-object assignment still rests on declared-size match alone. Applied to `P3184-2020-12` and `-13`. |
| `DERIVED` | The row records an extraction computed from already-recorded evidence rather than a file obtained from the provider. Applied to `P3184-2020-Q4-EVIDENCE`. |

`ARCHIVE_PRESENT_NOT_OBJECT_BOUND` and
`ACQUIRED_OBJECT_BINDING_BY_DECLARED_SIZE` differ only in whether content was
compared. Neither asserts a proven object identity. Promoting either to a
stronger status requires a provider-side digest, a per-object download record,
or another independent identifier — not a further inference from size.

**Scope note (Q4 rows provenance token).** The table above describes
`provenance_status` tokens used in the source manifest
([bist_membership_p3184_2020_sources.csv](evidence/bist_membership_p3184_2020_sources.csv)).
The Q4 rows file
([bist_membership_p3184_2020_q4_rows.csv](evidence/bist_membership_p3184_2020_q4_rows.csv))
uses a separate token, `ACQUIRED_PRIVATE_LOCAL_VERIFIED`, in its own
`provenance_status` column, for derived row-level provenance — that a given
Q4 membership row was obtained from the private local archive and its
extraction verified. This token is not defined in the table above because it
is not a source-manifest state, and it does **not** imply full §9 row-level
collision reconciliation or Stage-B approval; those remain open exactly as
§16.4, §16.6, and §17.5 state.

### 17.5 What this correction does not change

- No status is promoted. `REVISION_CANONICALIZATION_RESOLVED` (§16.2) and
  `Q4_STATE_RESOLVED` (§16.3) stand on the unchanged cell-equality and
  row-extraction evidence; `REVISION_SEMANTICS_UNRESOLVED` (§5) and
  `XU050_SEED_STATE_UNRESOLVED` (§10) remain open.
- The §9 row-level reconciliation checklist remains open exactly as §16.4 left
  it. The five newly bounded objects do not close any part of it.
- 2020 is **not** promoted toward Stage-B eligibility, and §12's requirement for
  a separate year-level closure adjudication is unchanged.
- The [collision audit](BIST_MEMBERSHIP_2020_10_01_COLLISION_AUDIT.md) and its
  manifest were not edited, reinterpreted, or weakened.
- No modeling dataset, benchmark, return, model output, IC, or p-value was
  opened or inspected. `NO_NEW_OUTCOME_INSPECTION=true` still holds.
- Research support only; not investment advice. Correcting provenance records is
  not evidence of predictive value, and **no reliable predictive edge has been
  established**.
