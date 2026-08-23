# Historical BIST membership sourcing evidence (FI-DATA-EXPAND-04B / R3-SPIKE-01a)

> Outcome-blind membership/identity/provenance spike. This task acquired and
> documented **source evidence about index membership only**. It ran no model,
> touched no modeling dataset, target, benchmark, or result, and authored no
> Stage-B contract. The repository's standing scientific position is unchanged:
> **no reliable predictive edge has been established**.

| Field | Value |
| --- | --- |
| Task | FI-DATA-EXPAND-04B / R3-SPIKE-01a |
| Authored at repository HEAD | `7bd1dfad16eb750481603f18eca916e4ab09cfc4` (branch `main` == `origin/main`, worktree clean including untracked) |
| Protected boundary at authoring | 351 members, digest `98195607983a35d3ffc8996934be9ac1b808250a659fea126a1a9636e800cee5` (unchanged by this task) |
| Governing protocols | [`docs/PREREGISTERED_DATA_EXPANSION_STAGE_A.md`](PREREGISTERED_DATA_EXPANSION_STAGE_A.md) (`FI-DATA-EXPAND-STAGE-A-v1`), [`docs/SOURCE_USE_OWNER_AMENDMENT.md`](SOURCE_USE_OWNER_AMENDMENT.md) (`FI-SOURCE-OWNER-AMENDMENT-01`) |
| Prior source verdict superseded in part | [`docs/UNIVERSE_HISTORY_SOURCING_SPIKE.md`](UNIVERSE_HISTORY_SOURCING_SPIKE.md) S15 — DataStore was previously recorded as uncharacterized |
| Provenance manifest | [`data/provenance/bist_membership_source_manifest.csv`](../data/provenance/bist_membership_source_manifest.csv) — 73 rows |
| Private raw archive | `PRIVATE_LOCAL_RAW` — 6 objects, outside the repository, never committed |
| Decision | **`FI_DATA_EXPAND_04B_OWNER_PURCHASE_DECISION_REQUIRED`** |
| No new outcome inspection | `NO_NEW_OUTCOME_INSPECTION=true` |

## 1. Summary

Borsa İstanbul DataStore **Product 3184** ("2000 Yılından İtibaren Endekslerde
Bulunan Şirketler (BIST 30, BIST 50 ve BIST 100 için)") was located, its full
catalogue enumerated, and its official file-format specification acquired and
read. Two findings determine the outcome, and they are independent of each other.

1. **Acquisition is blocked by an entitlement gate, not by price.** All 66
   catalogue objects are listed at **0.00 TRY** with `accessType` `G`, but the
   only acquisition control the product page exposes is *Sepete Ekle* (add to
   basket). Completing that route requires an account, and the login/registration
   dialog requires accepting a **Kullanıcı Kayıt Sözleşmesi** (User Registration
   Agreement) plus a KVKK personal-data notice. The owner has **no existing
   logged-in DataStore session** — both the isolated browser and the owner's own
   Chrome profile presented the logged-out state with an empty basket. Creating
   an account and accepting a registration agreement is a new entitlement and a
   contract acceptance, which this task's rules and the agent's standing rules
   both reserve for a fresh, explicit owner decision. **Zero `exsrk` files were
   downloaded.**

2. **Even once downloaded, Product 3184 alone cannot satisfy the Stage-A
   point-in-time membership rule.** The official specification (§2.1.29) defines
   the file as one row per share with **four quarter columns** and **no date
   field of any kind**. Stage-A §5.2 makes `effective_from` / `effective_to`
   semantics mandatory and states that a record without them is not
   point-in-time evidence. Product 3184 therefore can never reach
   `POINT_IN_TIME_CONFIRMED` on its own, for any year, regardless of acquisition.

The candidate window is not closed by this result. The source exists, is
complete back to 2000, is free of charge, and is one owner decision away from
acquisition. What it cannot do alone is establish effective dates.

## 2. Coverage audit — Product 3184

Enumerated by paginating the product page's own *Daha fazla yükle* control
through all four catalogue pages (20 + 20 + 20 + 6 = **66 objects**; the fourth
page returned fewer than the page size, which ends the listing). Raw catalogue
responses are archived under `PRIVATE_LOCAL_RAW` and hashed in the manifest.

**The product title's "since 2000" claim is corroborated by the catalogue**: every
year 2000–2026 is represented. This was not assumed from the title; it was read
from the enumerated listing.

| Year | Objects visible | Visibility | Downloadable | Status |
| --- | --- | --- | --- | --- |
| 2000–2015 | 1 each (16 objects) | VISIBLE | No | `ACCESS_RESTRICTED` |
| 2016 | 2 | VISIBLE | No | `ACCESS_RESTRICTED` |
| 2017 | 5 | VISIBLE | No | `ACCESS_RESTRICTED` |
| 2018 | 8 | VISIBLE | No | `ACCESS_RESTRICTED` |
| 2019 | 4 | VISIBLE | No | `ACCESS_RESTRICTED` |
| 2020 | 7 | VISIBLE | No | `ACCESS_RESTRICTED` |
| 2021 | 5 | VISIBLE | No | `ACCESS_RESTRICTED` |
| 2022–2025 | 4 each (16 objects) | VISIBLE | No | `ACCESS_RESTRICTED` |
| 2026 | 3 | VISIBLE | No | `ACCESS_RESTRICTED` |

- **Earliest year visible:** 2000. **Latest year visible:** 2026.
- **Earliest downloadable year:** none. **Latest downloadable year:** none.
- **`NOT_VISIBLE` / `NOT_FOUND`:** no year in 2000–2026.
- **`ACCESS_RESTRICTED`:** every year, uniformly, for the same entitlement reason.

**2017–2020 are visible.** This directly answers the pre-2020 question: the
files are not absent, and the §16 prohibition on substitution, backward
extrapolation, interpolation, Wikipedia, screeners, or price-inferred membership
was never approached, because no year needed reconstructing from a missing file.
2017–2020 are in fact the **densest** part of the catalogue (5, 8, 4 and 7
objects respectively), which is consistent with off-cycle republication during
that period.

### 2.1 Whether entitlement changes visibility

**`UNKNOWN`.** The catalogue was enumerated anonymously and every object was
already visible with a listed price of 0.00 TRY and `inLibrary: false`. Whether
an authenticated account reveals additional objects, additional years, or
different pricing was **not** established and must not be assumed.

## 3. Access route and the blocking gate

| Step | Observed |
| --- | --- |
| Product page | Public, anonymous, no login required to browse or read metadata |
| Format documentation | Public static asset, direct link, no login — **acquired** |
| Per-object detail panel | Shows `Dosya Adı`, `Tarih`, `Boyut` and a single action: *Sepete Ekle* |
| Direct download link | **None exposed** at any point in the anonymous flow |
| Basket | Reachable and empty; checkout not attempted |
| Login/registration | Single combined *Giriş/Kayıt* dialog requiring a KVKK notice acknowledgement and acceptance of the **Kullanıcı Kayıt Sözleşmesi** |

Per this task's access rules and the agent's standing rules, the following were
**not** performed: creating an account, entering credentials, adding to basket,
submitting an order, accepting any agreement or consent banner, or any
authentication/rate-limit/access-control circumvention. No guessed download URL
was probed; §6 makes clear that a guessed URL returning bytes would not be
adequate provenance, and probing one would also be an access-control bypass.

Everything read came from first-party published objects: the product page itself,
the catalogue listing endpoint that page invokes to render its own product list,
and the format-specification PDF linked from the page body.

> **`OWNER_PURCHASE_OR_CONTRACT_DECISION_REQUIRED`.** The obligation is not
> monetary — the files are free. It is an account registration plus acceptance
> of a user agreement. That is an owner decision, and this task stopped at it.

## 4. Format and semantics audit

Source: official DataStore file-format specification, §2.1.29 "2000 Yılından
İtibaren Endekslerde Bulunan Şirketler", document version **1.4 dated
15.06.2016**, SHA-256 `ab76e970…f00cc` (manifest row `BM-001`).

### 4.1 Documented structure

| Element | Documented value |
| --- | --- |
| Container | `exsrk[YYYY].zip` → `exsrk[YYYY].xls` (one workbook per year) |
| Field 1 | `Pay Kodu` — share code (alphabetic, 32) |
| Field 2 | `Pay Adı` — share bulletin name (alphabetic, 32) |
| Fields 3–6 | `1.Çeyrek`, `2.Çeyrek`, `3.Çeyrek`, `4.Çeyrek` — one column per quarter (alphanumeric, 5) |
| Delimiter | Semicolon, per the documented sample row |
| Date field | **None** |
| Effective-date field | **None** |
| ISIN or other stable identifier | **None** |

The documented sample row is `ADEL;ADEL KALEMCİLİK;;XU100;XU100;XU100` — an
empty quarter cell denotes non-membership in that quarter, and an index code
denotes membership.

### 4.2 Time granularity

The specification describes the file as showing, for the relevant years, the list
of companies in BIST 100, BIST 50 and BIST 30 **in each quarter**. Granularity is
therefore **quarterly, encoded positionally as four columns**, not as dated
records.

**What the specification does not state, and what must therefore not be
invented:** whether a quarter cell means membership at quarter *start*, at
quarter *end*, throughout the *whole* quarter, or at *any point during* the
quarter. This is `UNKNOWN`. It matters directly, because a share that entered or
left mid-quarter has exactly one cell to be described by, and the resolution rule
is undocumented.

### 4.3 Nested-index semantics — documented and decisive

The specification states, for each quarter column, that the indices successively
contain one another and that only the narrowest index the share belongs to is
written: "Endeksler sırasıyla diğerini kapsamaktadır, sadece yer aldığı en az
payı içeren endeks belirtilmektedir" (Borsa İstanbul, DataStore file-format
specification v1.4, §2.1.29).

Consequently the documented hierarchy **BIST 30 ⊂ BIST 50 ⊂ BIST 100** is
authoritative, and expansion is **required, not optional**:

| Cell value | Implied membership that quarter |
| --- | --- |
| `XU030` | BIST 30 **and** BIST 50 **and** BIST 100 |
| `XU050` | BIST 50 **and** BIST 100 |
| `XU100` | BIST 100 only |
| empty | none of the three |

**Answering §8 directly:** yes — `XU030` must be expanded to `XU050` and
`XU100`, and `XU050` must be expanded to `XU100`. A reconstruction that read the
BIST 100 column literally, without expansion, would silently drop every BIST 30
and BIST 50 constituent from the BIST 100 universe. This is the single most
consequential parsing rule in the product and it is explicitly documented.

### 4.4 Extraordinary intra-quarter changes and exact effective dates

**Not represented in the file.** There is no date column, no event column, and no
mechanism for more than one membership state per quarter. Both §8 questions
resolve negatively:

- Are extraordinary intra-quarter changes represented? **No.**
- Are exact effective dates represented? **No.**

The catalogue does carry a *publication* date per object (`createDate`), and the
off-cycle republication pattern is suggestive — 2017 has an object dated
20-10-2017 after its 02-10-2017 quarterly object; 2018 has four off-cycle objects
(16-02, 22-02, 05-06, 04-09); 2020 has 27-04, 22-05 and 28-07; 2021 has 17-06.
But a publication date **bounds** when a change was reflected; it is not an
`effective_from`. Treating it as one would violate Stage-A §5.2. It is recorded
in the manifest as publication metadata and nothing more.

### 4.5 Documentation currency — an open gap

The specification is **v1.4, dated 15.06.2016**. Every 2017–2026 object postdates
it, and the product page itself warns that field names may vary over time because
of the systems that produced the data. Two byte-size discontinuities in the
catalogue are consistent with a format change after the documented version:

| Boundary | Declared size before → after |
| --- | --- |
| 2019 Q3 → Q4 objects | 26,930 → 58,640 bytes |
| 2026 Q1 → Q2 objects | 67,319 → 156,759 bytes |

Within a single year the declared sizes otherwise grow monotonically across the
quarterly republications (2025: 65,793 → 67,819 → 68,340 → 69,096), which is
consistent with quarter columns being populated progressively through the year —
but that is corroboration by file size, not proof, and no file was opened.

**Therefore the applicability of the v1.4 field layout to the 2017–2026 objects
is `UNKNOWN` and must be verified against an acquired file before any parser is
written.**

### 4.6 Legacy-object date-field anomaly

For `exsrk2000.zip` through `exsrk2015.zip` the provider's `date` field is
`31-12-(YYYY-1)` — for example `exsrk2015.zip` carries `31-12-2014` and
`exsrk2000.zip` carries `31-12-1999` — while the 2016+ objects carry
`30-12-YYYY` matching their filename year. All sixteen legacy objects share a
single upload date of 08-06-2015, indicating a bulk historical load. **Whether
the legacy filename year or the legacy `date` field identifies the covered year
is not established.** This is recorded per row in the manifest and is outside the
2017 candidate floor, but it would become decisive if the window were ever
extended earlier.

### 4.7 Duplicate same-day objects in 2020

Two pairs of distinct catalogue objects share a filename and a publication date
but differ in declared size:

| Object id | File | Publication date | Declared bytes |
| --- | --- | --- | --- |
| 982925 | `exsrk2020.zip` | 27-04-2020 | 56,407 |
| 982927 | `exsrk2020.zip` | 27-04-2020 | 55,195 |
| 1132519 | `exsrk2020.zip` | 01-10-2020 | 58,823 |
| 1132521 | `exsrk2020.zip` | 01-10-2020 | 58,631 |

Which member of each pair is authoritative is **`UNKNOWN`**. Under Stage-A
fail-closed this is an unresolved ambiguity specific to 2020 and must be settled
from evidence, never by choosing the larger file or the higher id.

## 5. Point-in-time adequacy against Stage A

Stage-A §5.2: `effective_from` / `effective_to` semantics are mandatory, and a
record carrying only an announcement or publication date is not point-in-time
evidence. Stage-A §5.5: periodic changes alone are incomplete by construction.

Product 3184 supplies neither effective dates nor extraordinary-event coverage.
**`POINT_IN_TIME_CONFIRMED` is unreachable for every year from this product
alone.** The per-year classification is therefore:

| Years | Documented ceiling from the specification | Realized status this task |
| --- | --- | --- |
| 2000–2016 | `QUARTERLY_ONLY_REQUIRES_EVENT_AUGMENTATION` | `UNKNOWN` — not acquired |
| 2017–2026 | `UNKNOWN` — v1.4 predates these objects (§4.5) | `UNKNOWN` — not acquired |

No year is classified `INSUFFICIENT_DATA`. That classification is reserved for a
year whose evidence has been examined and found inadequate; here the evidence
exists and has not yet been obtainable, which is a different state and is
recorded as such.

Answering §9's four questions:

| Question | Answer |
| --- | --- |
| Can exact membership at an annual as-of date be established? | **Not from Product 3184 alone.** A quarter column has no as-of date; an annual as-of date falling mid-quarter cannot be resolved against it without an undocumented assumption. |
| Can entry/exit effective dates be established? | **No.** No date field exists. |
| Can extraordinary intra-quarter changes alter the annual state? | **Yes, and they are invisible in this product.** The off-cycle republications in 2017, 2018, 2020 and 2021 are direct evidence that such changes occurred within the candidate window. |
| Are identity/succession cases deterministically resolvable? | **No.** The product carries share code and bulletin name only, with no ISIN or other stable identifier (§4.1), which Stage-A §5.7 requires be recorded rather than papered over with a ticker-to-ticker join. |

**Stage A was not weakened to fit this source.** No rule was relaxed, reworded,
or reinterpreted, and the Stage-A document is byte-identical.

## 6. Event augmentation — required, and not yet assessed

Event augmentation is **required**, established from the specification rather
than assumed: the only route to `effective_from` / `effective_to` is first-party
index-review and extraordinary-change announcements carrying effective dates.

This task did **not** build that evidence base. §10 scopes event sourcing to what
is needed to evaluate gaps in Product 3184, and the gap is now established
without it. One bounded, read-only check was performed: `borsaistanbul.com`
responded, and a `/duyurular` announcements route was discovered from links in
the site's own homepage response rather than guessed.

**What remains `UNKNOWN` and must not be assumed:** whether that route publishes
effective-dated index-composition changes, whether its archive reaches back to
2017, whether additions and removals are itemised per ticker, and whether
extraordinary changes are distinguishable from periodic reviews. A guessed KAP
index path returned HTTP 404 and is recorded as a failed guess, not as evidence
of absence. This is manifest row `BM-073`, `provenance_status=NOT_ASSESSED`.

## 7. Identity and succession

**No identity or succession case was resolved, and none was attempted.**
Resolution requires the membership rows themselves, which were not acquired. Every
`CATALOG_ENTRY` row carries `identity_status=NOT_ASSESSED`, and no row carries a
ticker or company name.

The structural gap is already known from §4.1: the product carries no ISIN or
other stable identifier. Under Stage-A §6 every rename, merger, successor,
delisting and ambiguous-continuity case will require an evidenced identity
assertion from a separate source, and unresolved identity fails closed to
`UNKNOWN`. Classification of individual cases is future work.

## 8. Private raw archive and repository boundary

The private archive holds **6 objects**, all outside the repository, none
committed:

| Object | Class |
| --- | --- |
| `DataStore_Veri_Bildirim_ve_Kabul_Formatlari.pdf` | `PRIVATE_LOCAL_RAW` |
| `api_product-type_3184.json` | `PRIVATE_LOCAL_RAW` |
| `api_product-type_3184_products_page1.json` … `page4.json` (4 files) | `PRIVATE_LOCAL_RAW` |

Every object is SHA-256 hashed in the manifest and referenced only by the
symbolic form `PRIVATE_LOCAL_RAW:bist-membership/raw/<name>`. No absolute
archive path appears in any tracked file. No ZIP, XLSX, PDF or HTML source byte
is tracked in Git. Consistent with `FI-SOURCE-OWNER-AMENDMENT-01`, this is
`INTERNAL_OWNER_AUTHORIZED` internal research use, **not** an external licence
grant, and public redistribution of third-party raw data remains prohibited.

The manifest carries **no membership data**: `ticker_or_share_code` and
`company_name` are `NA` on all 73 rows, because no membership file was opened.

**NA convention:** `NA` means the field does not apply to that record type;
`UNKNOWN` means it applies but is not established by evidence. Neither is ever a
placeholder for a fabricated value.

## 9. Scientific and no-peeking boundary

| Control | State |
| --- | --- |
| Outcome inspection | `NO_NEW_OUTCOME_INSPECTION=true` — no return, benchmark-relative outcome, model score, prediction, IC or p-value was opened, loaded or inspected |
| Modeling artifacts | Untouched — no `data/trusted_clean/modeling_dataset*`, no `experiments/results_*` file was read |
| Models run | **None** — `make data`, `make benchmark`, `make research`, `make research-excess` NOT RUN |
| Universe / features / targets / benchmark | Unchanged — the cohort files [`data/config/universe_public_40.csv`](../data/config/universe_public_40.csv), [`data/config/universe_training_bist100.csv`](../data/config/universe_training_bist100.csv) and [`data/config/bist100_candidates.csv`](../data/config/bist100_candidates.csv), and all modeling, feature, target and benchmark data, untouched |
| Stage A | Unchanged, byte-identical |
| Stage B | **Not authored** |
| Protected boundary | 351 → 351, digest unchanged, no re-pin |
| Benchmark acquisition (Products 3180/3181, XU100 series, Yahoo) | **Not performed** — noted as existing, separate task |
| Fundamentals acquisition | **Not performed** — separate source stream |

## 10. Recommendation for the next task

**One owner decision unblocks everything else.** In priority order:

1. **Owner decision on DataStore registration.** The owner registers a DataStore
   account and accepts the Kullanıcı Kayıt Sözleşmesi themselves, or declines.
   The files are free; the decision is about the agreement and the account, not
   money. This is not an agent action under any framing.
2. **On approval, acquire and audit a single probe year first** — 2017, the
   candidate floor — verify the v1.4 field layout still holds (§4.5), confirm the
   nested-index encoding empirically, and only then acquire the remaining
   candidate window. Resolve the 2020 duplicate-object ambiguity (§4.7) from
   evidence at that point.
3. **Assess the first-party event-evidence route** (§6) as a parallel task: does
   Borsa İstanbul publish effective-dated index-composition changes back to 2017,
   itemised per ticker, distinguishing extraordinary from periodic changes? This
   determines whether `QUARTERLY_ONLY_REQUIRES_EVENT_AUGMENTATION` can ever be
   lifted to a Stage-B-admissible universe, and it is the true gating question —
   Product 3184 by itself cannot answer it no matter how much of it is acquired.
4. **Do not author Stage B** until (2) and (3) both return. If (3) fails, the
   honest outcome is that the candidate window classifies `INSUFFICIENT_DATA`
   under Stage-A fail-closed, and saying so is an expected result of the
   protocol, not a failure of it.

Benchmark acquisition and fundamentals acquisition remain separate, untouched
source streams.

---

`NO_NEW_OUTCOME_INSPECTION=true`
`NO_RELIABLE_PREDICTIVE_EDGE_ESTABLISHED=true`
`FINANCEIQ_DATA_EXPAND_04B: FI_DATA_EXPAND_04B_OWNER_PURCHASE_DECISION_REQUIRED`
