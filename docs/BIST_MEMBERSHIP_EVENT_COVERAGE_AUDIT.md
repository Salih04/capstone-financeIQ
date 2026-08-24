# First-party BIST/KAP index-event coverage and effective-date audit (FI-DATA-EXPAND-04B-EVENT-01)

> Outcome-blind membership/effective-date sourcing audit. This task read
> **first-party index-announcement evidence only**. It ran no model, opened no
> modeling dataset, target, benchmark or result artifact, integrated nothing into
> any scientific dataset, and authored no Stage-B contract. The repository's
> standing scientific position is unchanged: **no reliable predictive edge has
> been established**.

| Field | Value |
| --- | --- |
| Task | `FI-DATA-EXPAND-04B-EVENT-01` |
| Authored at repository HEAD | `cca5dc319a8837ea58f132735d7d5f0b8a7c9152` (branch `main` == `origin/main`, worktree clean including untracked) |
| Protected boundary at authoring | 351 members, digest `98195607983a35d3ffc8996934be9ac1b808250a659fea126a1a9636e800cee5` (unchanged by this task) |
| Governing protocols | [`docs/PREREGISTERED_DATA_EXPANSION_STAGE_A.md`](PREREGISTERED_DATA_EXPANSION_STAGE_A.md) (`FI-DATA-EXPAND-STAGE-A-v1`), [`docs/SOURCE_USE_OWNER_AMENDMENT.md`](SOURCE_USE_OWNER_AMENDMENT.md) (`FI-SOURCE-OWNER-AMENDMENT-01`) |
| Prior sourcing evidence extended, not revised | [`docs/DATA_EXPANSION_MEMBERSHIP_SOURCING_REPORT.md`](DATA_EXPANSION_MEMBERSHIP_SOURCING_REPORT.md) §6 scoped this audit and left the event route `NOT_ASSESSED` |
| Event manifest | [`docs/evidence/bist_membership_event_sources.csv`](evidence/bist_membership_event_sources.csv) — 610 rows |
| Private raw archive | `PRIVATE_LOCAL_RAW` — 29 objects, outside the repository, never committed |
| Decision | **`FI_DATA_EXPAND_04B_EVENT_STREAM_PARTIAL`** |
| No new outcome inspection | `NO_NEW_OUTCOME_INSPECTION=true` |

## 1. Summary

Borsa İstanbul publishes index-membership changes through a **dedicated,
first-party, taxonomy-classified archive** that this task located, censused and
archived. Three findings determine the outcome, and they are independent.

1. **The scheduled/periodic event stream is complete and explicitly
   effective-dated for the whole candidate window.** All sixteen quarterly
   *BIST Pay Endeksleri* review announcements covering `2017Q1` through `2020Q4`
   exist, are reachable by stable id, and each one states its index period as an
   explicit date range and itemises additions and removals **per ticker per
   index** for BIST 100, BIST 50 and BIST 30. 190 additions and 190 removals were
   transcribed across the twenty announcements archived (four adjacent boundary
   quarters included); 198 of those rows are `XU100` rows inside 2017–2020.

2. **The extraordinary/intra-period event stream does not exist for the
   candidate window, and this is an evidenced negative result, not an
   assumption.** The official archive's own announcement-type taxonomy contains
   the category *Endeks İçeriklerinde Yapılan Dönem İçi Değişiklikler*
   (intra-period constituent changes). Across 585 archive rows spanning
   2013-06-21 to 2026-08-20 that category has **zero rows before 2021-12-07**,
   and its earliest row tagged to the benchmark group *BIST Pay
   Endeksleri | Gösterge Endeksler* (XU030/XU050/XU100) is **2023-09-28**.

3. **The rule that governs extraordinary changes is documented and
   deterministic, but the events it applies to are not published.** The
   period-correct rulebook (`BIST Pay Endeksleri Temel Kuralları`, Ekim 2019)
   §7 defines non-periodic membership changes exhaustively — market closure,
   Yakın İzleme transfer, market migration, IPO fast entry, mergers, transfers,
   demergers — each with an explicit effective-date rule keyed to a **KAP
   disclosure**. Reconstructing 2017–2020 extraordinary changes would therefore
   require deriving them from KAP company disclosures and market actions and
   then selecting among published reserve shares, which the rulebook does not
   order. That is derivation, not first-party event evidence.

The consequence for the candidate window is bounded and stated plainly: the
quarter-boundary chronology of BIST 100 for 2017–2020 is **source-supported with
explicit effective dates**; intra-quarter membership for the same years is
**not**. Under Stage-A fail-closed semantics that makes every candidate year
`INSUFFICIENT_DATA` for point-in-time reconstruction, and Stage B remains
unauthorised.

## 2. The official event mechanism

Two distinct first-party streams were discovered from the sites' own links. No
third-party page was used as evidence, and none was needed.

### 2.1 General announcement archive — `borsaistanbul.com/duyurular`

| Property | Observed value |
| --- | --- |
| Archive URL | `https://www.borsaistanbul.com/duyurular` |
| Item URL form | `/duyuru/<numeric-node-id>/<slug>` — stable numeric id; the slug is required (id alone returns HTTP 404) |
| Pagination | Drupal pager, `?page=0` … `?page=83`, 25 items per page |
| Census | 2098 unique items, 2012-01-02 … 2026-08-21 |
| Filters | Free-text search only. No category filter, no date filter |
| Completeness | **NOT the complete regulatory stream.** Borsa İstanbul also issues a numbered circular series (`YYYY/NN`). This archive carries only 12 items referencing that series for 2021, while the series itself had reached at least `2021/76` by 2021-11-09 |

### 2.2 Index announcement archive — `borsaistanbul.com/endeksler/endeks-duyurulari`

This is the authoritative, purpose-built stream and the one this audit relies on.

| Property | Observed value |
| --- | --- |
| Archive URL | `https://www.borsaistanbul.com/endeksler/endeks-duyurulari` |
| Delivery | The full row set is embedded in the page and filtered client-side; no server-side query parameters were used or needed |
| Census | 585 rows, 2013-06-21 … 2026-08-20 |
| Date filter | `Başlangıç Tarihi` / `Bitiş Tarihi` |
| Page size | 10 / 20 / 50 / 100 |
| Announcement-type filter | `announcementType` = 1…5 |
| Index-group filter | `indexGroup` = `<group>;<subgroup>;-1`; the benchmark subgroup is *BIST Pay Endeksleri &#124; Gösterge Endeksler* |
| Target linkage | Rows link either to a `/duyuru/<id>/<slug>` node or, from 2023-09-27 onward, to a **KAP disclosure** `kap.org.tr/tr/Bildirim/<id>` |

**Announcement-type taxonomy, as published by the source:**

| Type | Turkish label | Meaning | Archive rows |
| --- | --- | --- | --- |
| 1 | Kural Seti Değişiklikleri | rule-set changes, new indices | 69 |
| 2 | Endeks İçeriklerinde Yapılan Dönemsel Değişiklikler | **periodic** constituent changes | 287 |
| 3 | Endeks İçeriklerinde Yapılan Dönem İçi Değişiklikler | **intra-period / extraordinary** constituent changes | 202 |
| 4 | Endekslere ve Referans Oranlara İlişkin Diğer Duyurular | other index/reference-rate announcements | 20 |
| 5 | İşlem Gören Şirketlere Yönelik Endeks Duyuruları | issuer-directed index announcements | 7 |

The taxonomy is the decisive artefact: it means the distinction between
scheduled and extraordinary changes is **made by the source itself**, not
imposed by this audit.

### 2.3 KAP / MKK

KAP is the **trigger** authority for extraordinary changes under rulebook §7,
but it is **not** a source of index-composition announcements for the candidate
window. The earliest archive row whose target is a KAP disclosure is
**2023-09-27**; every row dated 2013–2022 targets a `borsaistanbul.com` node.
`kap.org.tr` was reachable and its disclosure-query surface was inspected; no
2017–2020 Borsa İstanbul index-composition disclosure was found or claimed, and
none was inferred. MKK was not required by any question this audit resolved.

## 3. Years inspected

Primary: **2017, 2018, 2019, 2020**. Continuity, taxonomy and mechanism were
then checked across **2013–2026** because the whole archive is one page; the
adjacent quarters `2016Q2`–`2016Q4` and `2021Q1` were archived as boundary
evidence.

## 4. Scheduled (periodic) review coverage

Every quarterly *BIST Pay Endeksleri* review announcement in the window exists.
Publication precedes the index period, consistent with rulebook §2.16 (periodic
changes announced at least 10 calendar days before the period starts).

| Index period | Stated effective window (verbatim from the document) | Published | Node id |
| --- | --- | --- | --- |
| 2017Q1 | 02/01/2017 – 31/03/2017 | 2016-12-14 | `11511` |
| 2017Q2 | 03/04/2017 – 30/06/2017 | 2017-03-20 | `11492` |
| 2017Q3 | 03/07/2017 – 30/09/2017 | 2017-06-22 | `11503` |
| 2017Q4 | 02/10/2017 – 29/12/2017 | 2017-09-20 | `11473` |
| 2018Q1 | 02/01/2018 – 30/03/2018 | 2017-12-18 | `11466` |
| 2018Q2 | 02/04/2018 – 29/06/2018 | 2018-03-22 | `11443` |
| 2018Q3 | 02/07/2018 – 30/09/2018 | 2018-06-19 | `12512` |
| 2018Q4 | 01/10/2018 – 31/12/2018 | 2018-09-19 | `12465` |
| 2019Q1 | 02/01/2019 – 29/03/2019 | 2018-12-21 | `12304` |
| 2019Q2 | 01/04/2019 – 28/06/2019 | 2019-03-18 | `12070` |
| 2019Q3 | 01/07/2019 – 30/09/2019 | 2019-06-21 | `11867` |
| 2019Q4 | 01/10/2019 – 31/12/2019 | 2019-09-20 | `11632` |
| 2020Q1 | 01/01/2020 – 31/03/2020 | 2019-12-17 | `11428` |
| 2020Q2 | 01/04/2020 – 30/06/2020 | 2020-03-19 | `12557` |
| 2020Q3 | 01/07/2020 – 30/09/2020 | 2020-06-19 | `12559` |
| 2020Q4 | 01/10/2020 – 31/12/2020 | 2020-09-18 | `14118` |

Each document itemises, per index, three columns: **ALINACAK PAYLAR**
(to be added), **ÇIKARILACAK PAYLAR** (to be removed) and **YEDEK PAYLAR**
(reserve). Additions and removals are equal in number in **every** transcribed
table, matching rulebook §6(c)/(d), which requires the counts to be equalised.
Reserve-list size is 5 per index through `2019Q4` and 3 from `2020Q1` onward,
which is exactly the change announced on 2019-10-28 (node `11419`, circular
`2019/68`). These are independent internal corroborations of the transcription,
not assumptions imposed on it.

## 5. Extraordinary (intra-period) event coverage

| Year | Periodic | **Intra-period** | Rule-set | Other | Issuer |
| --- | --- | --- | --- | --- | --- |
| 2017 | 24 | **0** | 3 | 0 | 0 |
| 2018 | 16 | **0** | 5 | 0 | 0 |
| 2019 | 15 | **0** | 2 | 3 | 0 |
| 2020 | 17 | **0** | 4 | 2 | 0 |
| 2021 | 14 | **4** | 5 | 3 | 2 |
| 2022 | 18 | **21** | 6 | 3 | 2 |
| 2023 | 30 | **43** | 11 | 5 | 1 |
| 2024 | 45 | **46** | 8 | 1 | 1 |
| 2025 | 50 | **42** | 11 | 0 | 0 |

Onsets, stated as evidence rather than inference:

- First intra-period row anywhere in the archive: **2021-12-07** (BIST Katılım
  indices).
- First intra-period row tagged to the benchmark group **Gösterge Endeksler**
  (XU030/XU050/XU100): **2023-09-28**. Rows so tagged: 2023: 19, 2024: 38,
  2025: 22, 2026: 38.

**What this does and does not establish.** It establishes that no first-party
intra-period benchmark-index change announcement exists in this archive for
2017–2020. It does **not** establish that no such change occurred. Whether none
occurred, or whether they occurred and were never entered into this archive, is
not determined by the source and is not assumed here in either direction.
Rulebook §7 makes the second reading the more likely one — the rule was in force
throughout — but "more likely" is not evidence, and the audit records `UNKNOWN`.

## 6. Effective-date evidence quality

| Question | Answer | Basis |
| --- | --- | --- |
| Does a periodic announcement state an explicit effective date? | **Yes** | Each document states its index period as a literal date range, e.g. "2017 yılı birinci üç aylık dönemi (02/01/2017 - 31/03/2017)" |
| Is `publication_date` ever equated with `effective_date`? | **No** | They differ in every row; publication precedes the period start by roughly 10–20 days |
| Is the period start a calendar-quarter start? | **No, and it must not be assumed to be** | The stated starts are trading days: `2017Q1` starts 02/01/2017, `2017Q2` 03/04/2017, `2017Q3` 03/07/2017, `2017Q4` 02/10/2017 |
| Is there a documented deterministic rule behind the dates? | **Yes** | Rulebook §2.15 (four index periods), §2.16 (announced ≥10 calendar days before period start) |
| Are extraordinary effective dates deterministic *given the trigger*? | **Yes** | Rulebook §7: a KAP disclosure must be published by 16:30 on the business day before the event date (12:00 on a half day); otherwise it counts as published the next business day and the change takes effect on the **second business day following** KAP publication. §7.1 removes definitively closed shares, shares closed for more than 5 consecutive business days, and shares moved to Yakın İzleme Pazarı effective **on the day of the closure or transfer** |
| Are the extraordinary triggers themselves available for 2017–2020? | **No** | §5 |

## 7. Per-year event-stream completeness

Classified per §8 of the task contract. `EVENT_STREAM_COMPLETE` requires a
defensible first-party basis for **both** scheduled and extraordinary classes;
finding quarterly reviews alone is explicitly not sufficient.

| Year | Classification | Basis |
| --- | --- | --- |
| 2017 | `PERIODIC_REVIEWS_FOUND_BUT_EXTRAORDINARY_COMPLETENESS_UNKNOWN` | 4/4 periodic reviews, explicitly effective-dated; 0 intra-period rows |
| 2018 | `PERIODIC_REVIEWS_FOUND_BUT_EXTRAORDINARY_COMPLETENESS_UNKNOWN` | 4/4 periodic reviews; 0 intra-period rows |
| 2019 | `PERIODIC_REVIEWS_FOUND_BUT_EXTRAORDINARY_COMPLETENESS_UNKNOWN` | 4/4 periodic reviews; 0 intra-period rows |
| 2020 | `PERIODIC_REVIEWS_FOUND_BUT_EXTRAORDINARY_COMPLETENESS_UNKNOWN` | 4/4 periodic reviews; 0 intra-period rows |
| 2021 | `PERIODIC_REVIEWS_FOUND_BUT_EXTRAORDINARY_COMPLETENESS_UNKNOWN` | intra-period category opens 2021-12-07 but carries no benchmark-group row |
| 2022 | `PERIODIC_REVIEWS_FOUND_BUT_EXTRAORDINARY_COMPLETENESS_UNKNOWN` | 21 intra-period rows, none tagged to the benchmark group |
| 2023 | `PARTIAL_EVENT_COVERAGE` | benchmark-group intra-period coverage begins **within the year**, on 2023-09-28 |
| 2024 | `PERIODIC_REVIEWS_FOUND_BUT_EXTRAORDINARY_COMPLETENESS_UNKNOWN` | both classes present all year; no first-party statement of archive completeness or retention policy was found, so exhaustiveness is not defensible |
| 2025 | `PERIODIC_REVIEWS_FOUND_BUT_EXTRAORDINARY_COMPLETENESS_UNKNOWN` | as 2024 |

No year is classified `EVENT_STREAM_COMPLETE`.

## 8. Per-year point-in-time reconstructibility

Classified per §9. The question is whether Product 3184 quarterly state plus the
first-party event stream can deterministically produce `effective_from`,
`effective_to`, security identity and BIST 100 inclusion state **without**
interpolation, backward projection, present-day substitution, outcome data,
guessed effective dates or assumed continuity.

| Year | Classification | Binding constraint |
| --- | --- | --- |
| 2017 | `INSUFFICIENT_DATA` | intra-quarter membership unestablished; §5 |
| 2018 | `INSUFFICIENT_DATA` | as 2017 |
| 2019 | `INSUFFICIENT_DATA` | as 2017 |
| 2020 | `INSUFFICIENT_DATA` | as 2017; 2020 additionally carries the largest single periodic change in the window (23 in / 23 out at `2020Q1`) |
| 2021 | `INSUFFICIENT_DATA` | no benchmark-group intra-period rows |
| 2022 | `INSUFFICIENT_DATA` | no benchmark-group intra-period rows |
| 2023 | `INSUFFICIENT_DATA` | benchmark-group intra-period coverage starts mid-year |
| 2024 | `UNKNOWN` | both event classes present with explicit effective dates, but no Product 3184 row has been acquired and extraordinary exhaustiveness is unevidenced, so the test cannot be run |
| 2025 | `UNKNOWN` | as 2024 |

Assuming continuity across a quarter — that is, treating the quarter-boundary
state as valid for every day inside the quarter — would produce a universe that
looks complete and is silently wrong on any day an extraordinary change was in
force. Stage-A fail-closed semantics forbid that substitution, so the honest
classification is `INSUFFICIENT_DATA` and the honest consequence is that Stage B
stays unauthorised for this window.

## 9. Identity and succession

Only cases encountered in the event stream were investigated, per §11. The
stream carries **ticker and bulletin name only — no ISIN and no stable security
identifier**, which is the same structural gap already recorded for Product
3184.

| Case encountered | Classification | Evidence |
| --- | --- | --- |
| `A.V.O.D` / `AVOD` | `INSUFFICIENT_IDENTITY_EVIDENCE` | Node `11867` (`2019Q3`) prints the ticker as `A.V.O.D`; other documents of the same series print `AVOD`. Both are recorded verbatim in the manifest. Normalisation is **not** asserted from name similarity |
| Ticker in both `ÇIKARILACAK` and `YEDEK` of the same table | Not an identity case — a **semantics** finding | 7 tickers (14 manifest rows) across the twenty announcements in the transcribed BIST 100/50/30 tables: `ALCTL` in node `11511` (XU100, `2017Q1`), `ECZYT` and `SARKY` in node `12559` (XU100, `2020Q3`), `PETUN` in node `14132` (XU100, `2021Q1`). A share removed at a period boundary can simultaneously be listed as an eligible substitute for that same index during that period. A reserve entry is therefore **not** a membership state |
| Every ticker row in the manifest | `INSUFFICIENT_IDENTITY_EVIDENCE` | No ISIN or stable id is published in any document of this series |
| Merger / succession cases | **None resolved, none encountered as an event** | The 2017–2020 stream contains no merger, rename, code-change, delisting or relisting event, because the intra-period category that would carry them is empty for those years (§5). Rulebook §7.10–§7.16 define how such events *would* be handled |

No continuity was inferred from similar names anywhere in this audit.

## 10. The deterministic reconstruction algorithm (specified, not built)

Per §12 the canonical universe dataset was **not** built. The algorithm that
would be used, if and only if the evidence were adequate, is specified here so
that the evidence gap is auditable against a concrete procedure.

1. **Seed state.** Take the Product 3184 quarterly membership table for the
   year. Its cells are positional (`1.–4. Çeyrek`), carry no date, and its
   quarter semantics are `UNKNOWN` — that ambiguity must be resolved from
   evidence before this step is admissible.
2. **Nested-index expansion.** Expand before anything else: `XU030 ⟹ XU050 ⟹
   XU100`. The product writes only the narrowest index of membership, so a
   literal read of the BIST 100 column silently drops every BIST 30 and BIST 50
   constituent.
3. **Anchor the period calendar.** For each quarter take `effective_from` and
   `effective_to` from the **stated period range in the periodic announcement**,
   never from the publication date and never from the calendar quarter.
4. **Apply periodic deltas at the period boundary.** At `effective_from`, apply
   `REMOVE` then `ADD` for that index. Discard `RESERVE` rows: they are
   eligibility, not membership.
5. **Apply extraordinary events in effective-date order.** For each event, take
   the effective date from rulebook §7 — second business day after KAP
   publication for the general case; day of closure or transfer for §7.1; day
   share distribution begins for §7.10/§7.11/§7.15. *This step has no input for
   2017–2020.*
6. **Same-day ordering.** Within one effective date apply, in order: removals
   forced by §7.1 closure/transfer, then merger and demerger resolutions
   (§7.10–§7.15), then reserve substitutions, then periodic deltas if the date
   coincides with a period start. **This ordering is a construction of this
   audit, not a published rule**, and any dataset built on it must record it as
   such.
7. **Reserve substitution.** §7.1/§7.10/§7.11 require a removed share to be
   replaced "from the reserves". The reserve list is published in rank order,
   but **no first-party rule states that substitution consumes it in rank
   order**. Any implementation that assumes rank order must flag the assumption;
   fail-closed treatment is `INSUFFICIENT_DATA`.
8. **Identity resolution.** Carry the ticker verbatim. Apply `RENAME` /
   `CODE_CHANGE` / `MERGER_SUCCESSION` only against an evidenced first-party
   identity assertion. Unresolved identity fails closed to `UNKNOWN`; it is never
   resolved by name similarity.
9. **Quarter-boundary reconciliation.** Independently reconcile the Product 3184
   state at each quarter boundary against the state produced by applying the
   event stream to the previous quarter. Agreement is the acceptance test.
10. **Fail-closed on mismatch.** Any unreconciled difference between the Product
    3184 state and the event-derived state marks that security-period
    `INSUFFICIENT_DATA`. It is never repaired by preferring one source, by
    interpolation, or by present-day substitution.

## 11. Private raw archive and repository boundary

29 objects were archived, all outside the repository, none committed:

| Group | Count | Class |
| --- | --- | --- |
| Quarterly periodic review announcements (`2016Q2`–`2021Q1`) | 20 | `PRIVATE_LOCAL_RAW` |
| Rule-set update announcements (nodes `11419`, `12305`, `12574`, `12592`) | 4 | `PRIVATE_LOCAL_RAW` |
| `BIST Pay Endeksleri Temel Kuralları` PDFs (Ekim 2019, 20 Aralık 2018) | 2 | `PRIVATE_LOCAL_RAW` |
| Index-announcement archive page snapshot | 1 | `PRIVATE_LOCAL_RAW` |
| General announcement listing snapshots (first and last pager page) | 2 | `PRIVATE_LOCAL_RAW` |

Every object is SHA-256 hashed with its byte size and access date in the
manifest, and referenced only by the symbolic form
`PRIVATE_LOCAL_RAW:bist-membership/{events,raw}/<name>`. No absolute archive
path appears in any tracked file. **No HTML, PDF, XLSX or ZIP source byte is
tracked in Git.** Consistent with `FI-SOURCE-OWNER-AMENDMENT-01` this is
`INTERNAL_OWNER_AUTHORIZED` internal research use, **not** an external licence
grant; public redistribution of third-party raw data remains prohibited.

Nothing was written under `data/provenance/`, which is reserved by existing
exact-content invariants.

## 12. Manifest

[`docs/evidence/bist_membership_event_sources.csv`](evidence/bist_membership_event_sources.csv)
— **610 rows**.

| Row class | Count |
| --- | --- |
| `ADD` (per ticker, per index, effective-dated) | 190 |
| `REMOVE` (per ticker, per index, effective-dated) | 190 |
| `OTHER_MEMBERSHIP_RELEVANT` — reserve-list entries | 195 |
| `OTHER_MEMBERSHIP_RELEVANT` — archive mechanism, rulebooks, rule-set updates | 9 |
| `OTHER_MEMBERSHIP_RELEVANT` — evidenced negative result, intra-period class, 2017–2022 | 6 |
| `REVIEW_SCHEDULE` — one document-level row per announcement | 20 |

`ADD`/`REMOVE` rows by index: `XU100` 224, `XU050` 126, `XU030` 30. Restricted
to coverage years 2017–2020, `XU100` contributes 198 rows.

**NA convention**, unchanged from the 04B manifest: `NA` means the field does
not apply to that record type; `UNKNOWN` means it applies but is not established
by evidence. Neither is ever a placeholder for a fabricated value, and **no cell is blank** — 10 rows where the source prints the bulletin name identically to the share code (`AYGAZ`, `BRISA`, `CIMSA`, `TUKAS`, `YATAS`) carry that repeated value verbatim and say so in their note. `BIST Likit
Banka` and `BIST Banka Dışı Likit 10` tables appear in the later announcements
and were deliberately **not** transcribed, because no first-party index code was
established for them; each affected `REVIEW_SCHEDULE` row says so.

## 13. Unresolved gaps

1. **Extraordinary events for 2017–2020.** No first-party record. Deriving them
   from KAP company disclosures plus market actions is a different task with a
   different admissibility argument, and it would still leave the reserve
   selection order (§10 step 7) unresolved.
2. **Reserve consumption order.** Published in rank order, not stated to be
   consumed in rank order.
3. **Same-day event ordering.** No published rule; §10 step 6 is this audit's
   construction.
4. **Security identity.** No ISIN in any document of this series; the
   `A.V.O.D`/`AVOD` case is unresolved.
5. **Archive retention policy.** No first-party statement was found on whether
   the index-announcement archive is exhaustive or subject to retention limits.
   The pre-2021 intra-period vacuum is consistent with either reading.
6. **Product 3184 rows.** Still unacquired — that gate is unchanged and is an
   owner decision, per the 04B report §10.
7. **Implicit index label.** Node `11632` (`2019Q4`) has no printed heading on
   its first table; BIST 100 was assigned by document order under an intro
   naming BIST 100, BIST 50 and BIST 30. Flagged in every affected manifest row
   as inference, not a printed label.

## 14. Scientific and no-peeking boundary

| Control | State |
| --- | --- |
| Outcome inspection | `NO_NEW_OUTCOME_INSPECTION=true` — no return, benchmark-relative outcome, model score, prediction, IC or p-value was opened, loaded or inspected |
| Modeling artifacts | Untouched — no `data/trusted_clean/modeling_dataset*` and no `experiments/results_*` file was read |
| Models run | **None** — `make data`, `make benchmark`, `make research`, `make research-excess` NOT RUN |
| Scientific-data integration | **None** — no event row was written into any modeling, feature, target, benchmark or universe file |
| Stage A | Unchanged, byte-identical |
| Owner amendment | Unchanged, byte-identical |
| 04B report and manifest | Unchanged, byte-identical |
| Stage B | **Not authored** |
| Protected boundary | 351 → 351, digest unchanged, no re-pin |
| Governed provenance namespace | `data/provenance/` untouched |

**Interpretation limits.** Finding a complete periodic announcement series does
not make a historical universe valid; more covered years do not improve any
estimate; event reconstruction does not establish model validity; and sourcing
success does not imply predictive edge. This task determined only whether
membership chronology is source-supported. **No reliable predictive edge has
been established.**

## 15. Recommendation for the next task

1. **Owner decision on DataStore registration remains the top gate**, unchanged
   from the 04B report §10. Nothing in this audit relaxes it.
2. **Do not author Stage B for 2017–2020.** The candidate window classifies
   `INSUFFICIENT_DATA` for point-in-time reconstruction, and saying so is the
   protocol working, not failing.
3. **The next bounded task, if the owner wants the window reopened, is a KAP
   trigger-event feasibility audit**: can KAP's disclosure archive be queried
   first-party for 2017–2020 market-closure, Yakın İzleme transfer, merger and
   delisting disclosures for BIST 100 constituents, and can rulebook §7 be
   applied to them deterministically? That audit must also resolve the reserve
   consumption order, or record that it cannot be resolved. If it fails, the
   honest outcome is that 2017–2020 stays `INSUFFICIENT_DATA`.
4. **A separate, much cheaper option exists**: restrict any future candidate
   window to years where **both** event classes are published for the benchmark
   group — that is, 2024 onward. Those years classify `UNKNOWN` here only
   because Product 3184 is unacquired, not because the event stream is missing.
   Whether so short a window is scientifically worth building is a Stage-A
   question, not a sourcing question, and is not decided here.

Benchmark acquisition (Products 3180/3181, XU100 series, Yahoo) and fundamentals
acquisition remain separate, untouched source streams.

---

`NO_NEW_OUTCOME_INSPECTION=true`
`NO_RELIABLE_PREDICTIVE_EDGE_ESTABLISHED=true`
`FINANCEIQ_DATA_EXPAND_04B_EVENT: FI_DATA_EXPAND_04B_EVENT_STREAM_PARTIAL`
