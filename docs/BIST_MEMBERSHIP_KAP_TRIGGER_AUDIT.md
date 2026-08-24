# First-party KAP trigger-event and reserve-consumption feasibility audit (FI-DATA-EXPAND-04B-KAP-TRIGGER-01)

> Outcome-blind sourcing audit. This task read **first-party KAP and Borsa
> İstanbul evidence only**. It ran no model, opened no modeling dataset, target,
> benchmark or result artifact, integrated nothing into any scientific dataset,
> and authored no Stage-B contract. The repository's standing scientific position
> is unchanged: **no reliable predictive edge has been established.**

| Field | Value |
| --- | --- |
| Task | `FI-DATA-EXPAND-04B-KAP-TRIGGER-01` |
| Authored at repository HEAD | `dae9d364406bcfef1b3a540236078f78ad9c79d4` (branch `main` == `origin/main`, worktree clean including untracked) |
| Protected boundary at authoring | 351 members, digest `98195607983a35d3ffc8996934be9ac1b808250a659fea126a1a9636e800cee5` (unchanged by this task) |
| Governing protocols | [`docs/PREREGISTERED_DATA_EXPANSION_STAGE_A.md`](PREREGISTERED_DATA_EXPANSION_STAGE_A.md) (`FI-DATA-EXPAND-STAGE-A-v1`), [`docs/SOURCE_USE_OWNER_AMENDMENT.md`](SOURCE_USE_OWNER_AMENDMENT.md) (`FI-SOURCE-OWNER-AMENDMENT-01`) |
| Prior evidence extended, not revised | [`docs/DATA_EXPANSION_MEMBERSHIP_SOURCING_REPORT.md`](DATA_EXPANSION_MEMBERSHIP_SOURCING_REPORT.md), [`docs/BIST_MEMBERSHIP_EVENT_COVERAGE_AUDIT.md`](BIST_MEMBERSHIP_EVENT_COVERAGE_AUDIT.md) §15.3 scoped this audit |
| Trigger manifest | [`docs/evidence/bist_membership_kap_trigger_sources.csv`](evidence/bist_membership_kap_trigger_sources.csv) — 191 rows |
| Private raw archive | `PRIVATE_LOCAL_RAW` — 141 objects added, outside the repository, never committed |
| Decision | **`FI_DATA_EXPAND_04B_KAP_TRIGGER_PARTIAL`** |
| No new outcome inspection | `NO_NEW_OUTCOME_INSPECTION=true` |

## 1. Summary

The 2017–2020 extraordinary-event gap is **substantially, but not completely,
closed**, and one prior finding is corrected by first-party evidence.

1. **The intra-period index-change stream for 2017–2020 exists on KAP.** Borsa
   İstanbul publishes membership changes as `Endeks Şirketlerinde Değişiklik`
   disclosures under KAP's regulator-disclosure class. The candidate window
   carries **107** of them: 23 in 2017, 27 in 2018, 26 in 2019, 31 in 2020. Each
   one names the affected share, the index it is added to, the index it is
   removed from, and — decisively — an **explicit effective date printed by the
   source** (`Geçerlilik Tarihi`). All 107 were fetched and read in full.

2. **This corrects, on first-party evidence, a finding of the prior audit.**
   `FI-DATA-EXPAND-04B-EVENT-01` §2.3 recorded that KAP "is **not** a source of
   index-composition announcements for the candidate window" and that no
   2017–2020 Borsa index-composition disclosure "was found, claimed or
   inferred". That negative was correct about the
   `borsaistanbul.com/endeksler/endeks-duyurulari` archive — its intra-period
   category genuinely has no row before 2021-12-07 — but wrong to extend to KAP.
   The prior report and manifest are **not edited** by this task; the correction
   is recorded here and in the manifest.

3. **Eight BIST 100 membership-changing intra-period events were found**, none of
   which was available to the prior audit: 2 in 2017, 4 in 2018, **0 in 2019**,
   2 in 2020. Four are IPO fast entries under rulebook art. 7.5/7.6; four are
   mergers. Every one carries a printed effective date, so no business-day
   arithmetic and no Borsa holiday calendar were needed.

4. **Reserve consumption is resolved by announcement, not by rule.** No rulebook
   version in force during 2017–2020 states the order in which reserves are
   consumed. What Borsa does instead is **name the replacement in the
   disclosure**, and in the 2020-05-20 case it names it *by rank*: Sarkuysan is
   described verbatim as the share "determined as the **1st reserve** for the
   BIST 100 index for the second three-month period of 2020". That makes
   consumption deterministic **when the disclosure resolves it** — and the
   2020-09-30 Şişecam merger shows it does not always do so.

5. **One event breaks reconstruction and is the binding constraint on 2020.** On
   2020-09-30 Borsa removed **three** BIST 100 constituents (`ANACM`, `SODA`,
   `TRKCM`) effective 01/10/2020 and named **no** BIST 100 replacement. That
   effective date is also the first day of the 2020Q4 index period. Removals and
   the periodic review therefore share an effective date, and no first-party rule
   was found that orders same-day changes. BIST 100 membership on 2020-10-01 is
   not deterministically reconstructible, and this audit fails closed rather than
   choosing an ordering.

6. **Exhaustiveness is not certified, and there is a demonstrated reason not to
   certify it.** The 2017Q2 periodic review that Borsa published on its own site
   on 2017-03-20 is **absent from KAP entirely**. If a scheduled announcement can
   be missing from this channel inside the window, an intra-period one can be
   too. No first-party statement of KAP archive completeness or retention was
   found either. No year is therefore classified
   `TRIGGER_STREAM_COMPLETE_WITH_ZERO_EVENTS`.

The consequence: the extraordinary-event path is now **evidenced and largely
deterministic** where the prior audit had nothing at all, but at least one
required path — same-day ordering with unreplaced removals — remains open, and
exhaustiveness remains unevidenced. All four candidate years stay
`INSUFFICIENT_DATA` for point-in-time reconstruction, and Stage B stays
unauthorised.

## 2. KAP first-party disclosure mechanism

| Property | Observed value |
| --- | --- |
| Official archive route | `https://www.kap.org.tr/tr/bildirim-sorgu` (*Detaylı Sorgulama*) |
| Query transport | `POST https://www.kap.org.tr/tr/api/disclosure/members/byCriteria`, JSON body |
| Query fields | `fromDate`, `toDate`, `memberType`, `mkkMemberOidList`, `inactiveMkkMemberOidList`, `disclosureClass`, `subjectList`, `mainSector`, `sector`, `marketOid`, `index`, `year`, `term`, `period` |
| Date filter | Inclusive `YYYY-MM-DD` range |
| Company filter | `mkkMemberOidList` (active members) and `inactiveMkkMemberOidList` (former KAP members, listed separately in the UI as *Eski KAP Üyesi Şirketler*) |
| Disclosure-class filter | `ALL`, `FR` (financial reports), `ODA` (material-event disclosures), `DUY` (regulator disclosures), `DG` (other) |
| Disclosure-category filter | `subjectList`, taking stable `subjectOid` values from a published 202-entry taxonomy |
| Index filter | `index` accepts an `indicesOid`; **present-day** index membership, so it was **not** used for a historical question |
| Result limit | Stated by the source: *"Arama sonuçları 2000 bildirim ile sınırlıdır"* — 2000 rows. Every query used here returned far fewer, so the cap never bound |
| Stable ids | Numeric `disclosureIndex` (`/tr/Bildirim/<id>`), plus an internal `disclosureId` GUID. Rendered PDF at `/tr/api/BildirimPdf/<id>`; structured body at `/tr/api/notification/attachment-detail/<id>` |
| Publication timing | Date **and time to the second** (e.g. `20.05.2020 17:01:47`), which is exactly what rulebook art. 7's 16:30 cut-off needs |
| Attachments | Enumerated per disclosure with stable `objId`, downloadable from `/tr/api/file/download/<objId>` |

### 2.1 Trigger-relevant categories in the published taxonomy

| Class | Subject (`subjectOid`) | Role |
| --- | --- | --- |
| `DUY` | `Endeks Şirketlerinde Değişiklik` (`8aca490d4fda2d58014fda4e141f0112`) | **the membership-change channel** |
| `DUY` | `BIST Pay Endeksleri` (`8aca490d50286f620150287a60580089`) | periodic reviews and rule-set news |
| `DUY` | `Pazar Değişikliği` (`8aca490d50666e6d0150669b6de101c4`) | art. 7.1/7.2 trigger fact |
| `DUY` | `Kottan Çıkarma/İşlem Görmekten Men Etme` (`8aca490d504b7afa01504bbef9be02d1`) | art. 7.1 trigger fact |
| `DUY` | `Pay İşlem Sırası Kapatma / Açma` (`4028328c5fc60da7016007a0bd395db0`) | art. 7.1 trigger fact |
| `ODA` | `Birleşme` (`4028328d5988e2630159d5ff460b200c`), `Bölünme` (`4028328d5988e2630159d5e90bc21e73`) | issuer-side merger/demerger trigger |
| `DUY` | `ABCD Grubu Listeleri` (`8aca490d504b7afa01504bb52a42022b`) | art. 7.3 trigger fact, relevant only until the Ekim 2019 rule change |

### 2.2 A method finding that changes what a "zero result" means

Under throttling the query endpoint answers with an **empty body**, which a naive
client parses as zero results. **An empty body is not evidence of zero
disclosures.** Several first-pass counts in this audit were empty-body artefacts
and were discarded. Every count reported here was produced by a client that
accepts a result only when the body parses as a JSON array and otherwise retries
up to six times with increasing backoff; a query that never returns an array is
recorded `SEARCH_INCOMPLETE` and is never converted into a negative.

## 3. Period-correct rule authority

The prior audit had two rulebook versions. That is not enough: **eight**
`BIST Pay Endeksleri Temel Kuralları` revisions were announced between
2015-11-27 and 2020-09-18, and the rules that matter for BIST 100 changed inside
the window. Five further versions were located through the versioned PDF links
carried by their own rule-set announcements and archived.

| Version | Announced | Node | Retrieved | In force for |
| --- | --- | --- | --- | --- |
| Kasım 2015 | 2015-11-27 | `11703` | **yes (new)** | all of 2017, to 2018-06-08 |
| Mayıs 2018 | 2018-06-08 | `12514` | **yes (new)** | 2018-06-08 → 2018-07-05 |
| Haziran 2018 | 2018-07-05 | `12485` | **yes (new)** | 2018-07-05 → 2018-12-10 |
| Aralık 2018 (10.12) | 2018-12-10 | `12289` | **yes (new)** | 2018-12-10 → 2018-12-20 |
| Aralık 2018 (20.12) | 2018-12-20 | `12305` | reused from prior audit | 2018-12-20 → 2019-10-28 |
| Ekim 2019 | 2019-10-28 | `11419` | reused from prior audit | 2019-10-28 → 2020-01-20 |
| Ocak 2020 | 2020-01-20 | `12574` | **NOT RETRIEVABLE** | 2020-01-20 → 2020-04-06 |
| Nisan 2020 | 2020-04-06 | `12553` | **yes (new)** | 2020-04-06 → 2020-09-18 |
| 2020/60 split rule set | 2020-09-18 | `12592` | **yes (new)** | from 2020-09-18 |

The Ocak 2020 version is a genuine gap: node `12574` links the **unversioned**
path `/files/bist-pay-endeksleri-temel-kurallari.pdf`, which today serves the
Aralık 2018 text. No substitution was made; the gap is recorded.

### 3.1 Trigger rules that can change BIST 100 membership

| Article (Kasım 2015 numbering) | Trigger condition | Membership consequence | Effective-date rule | Reserve rule |
| --- | --- | --- | --- | --- |
| 7 chapeau | any KAP-disclosure-driven change | — | disclosure must be on KAP by 16:30 on the business day before the event date (12:00 on a half day); otherwise the change takes effect on the **second business day after** KAP publication | — |
| 7.1 | permanent market closure; closure for more than 5 consecutive business days (except additional-offering closures); transfer to Yakın İzleme Pazarı | removed from **every** index it is in | **day of the closure or transfer** | BIST 30/50/100 and Temettü 25 vacancies filled "from reserves" |
| 7.2 | transfer to any market other than Yakın İzleme | removed from the old market index, added to the new one | day of transfer | reserves fill BIST 30/50/100 — **this sentence is deleted in Ekim 2019** |
| 7.3 | A/B/C/D group-list transition | index change under the out-of-scope-shares article | day of transition | reserves fill | 
| 7.4 | — | a share removed under 7.1–7.3 is **not** re-admitted before the period ends | — | — |
| 7.6 (7.5 in Ekim 2019) | IPO whose offered market value exceeds the stated threshold | enters BIST 30/50/100 in place of the **smallest free-float market-cap constituent** | **5th trading day** | not a reserve substitution |
| 7.11–7.12 (Aralık 2018) / 7.10–7.11 (Ekim 2019) | merger or transfer of an index constituent | surviving company stays if its market is index-eligible; vacated slots "completed from reserves" | **day share distribution begins** | reserves fill |
| 7.16 (Aralık 2018) / 7.15 (Ekim 2019) | demerger | largest free-float constituent stays to period end | day share distribution begins | — |
| **8.3** | **any matter not regulated by these Rules** | **determined and announced by the Borsa İstanbul General Directorate** | — | — |

### 3.2 What changed inside the window

- **Reserve count.** Kasım 2015 → Haziran 2018 and Aralık 2018: BIST 30 = 2,
  BIST 50 = 3, BIST 100 = 5, Temettü 25 = 5. Ekim 2019 onward: **3 each**. This
  matches the reserve-list sizes independently transcribed by the prior audit
  (5 through 2019Q4, 3 from 2020Q1).
- **BIST 100 periodic thresholds.** Ranks 90/110 through Aralık 2018; **95/105**
  from Ekim 2019.
- **Trigger classes removed.** Ekim 2019 deletes the A/B/C/D list-transition
  trigger (old art. 7.3) and deletes the reserve-replacement sentence from
  art. 7.2. A 2017 reconstruction that applied the Ekim 2019 rules would
  therefore miss two trigger classes that were live in 2017 — which is exactly
  why the Kasım 2015 version had to be retrieved rather than assumed.
- **Art. 7 chapeau.** Ekim 2019 adds the deeming rule that a late disclosure
  counts as published on the following business day. The second-business-day
  consequence is the same in all versions.
- **Art. 8.3 is unchanged across every version in the window.**

## 4. Search-space definition

Two search populations were used, and the distinction matters.

**(a) Issuer-side, population-free.** The primary search queried the
`Endeks Şirketlerinde Değişiklik` subject for each candidate year with **no
company filter**. It therefore captures every index-membership change Borsa
İstanbul announced on KAP in the period, for any security, without needing to
know who the BIST 100 constituents were. This is the search that produced the
event list in §5.

**(b) Membership-derived, for cross-checking only.** A ticker universe was
derived from the already-established periodic evidence — every `XU100` `ADD`,
`REMOVE` and reserve row in
[`docs/evidence/bist_membership_event_sources.csv`](evidence/bist_membership_event_sources.csv)
for the candidate years:

| Year | Tickers |
| --- | --- |
| 2017 | 38 |
| 2018 | 52 |
| 2019 | 44 |
| 2020 | 68 |
| union | 119 |

**This is not the constituent list.** It contains only shares that entered, left
or were reserves at a period boundary — roughly a third of the index. The full
point-in-time constituent set for 2017–2020 is still unacquired (Product 3184
remains an owner decision), so a per-security exhaustive search over all ~100
constituents per quarter **cannot be defined**, and none is claimed. Separately,
19 of the 119 tickers do not resolve to a current KAP member because their
issuers later merged or delisted; resolving those needs the inactive-member list.
No model-ready data was loaded to obtain any ticker.

## 5. Trigger events found

Eight BIST 100 membership-changing intra-period events, all first-party, all with
a printed effective date.

| # | Published (KAP) | Effective | Trigger | BIST 100 out | BIST 100 in | Also |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2017-06-14 18:35:25 | 2017-06-21 | IPO fast entry (arts. 5.6.b, 7.5, 7.6 cited) | `AYEN` | `MAVI` | `MAVI` into XU050/XU030; `GOODY` out of XU050; `DOHOL` out of XU030 |
| 2 | 2017-10-19 18:05:38 | 2017-10-20 | merger — Net Holding absorbs Net Turizm | `NTTUR` | `HURGZ` | — |
| 3 | 2018-02-07 17:22:34 | 2018-02-14 | IPO fast entry (arts. 7.5, 7.6) | `CRFSA` | `ENJSA` | `ENJSA` into XU050/XU030; `GOLTS` out of XU050; `SKBNK` out of XU030 |
| 4 | 2018-02-12 18:20:47 | 2018-02-19 | IPO fast entry (arts. 7.5, 7.6) | `KLGYO` | `MPARK` | `MPARK` into XU050/XU030; `IHLAS` out of XU050; `ECILC` out of XU030 |
| 5 | 2018-05-17 18:12:28 | 2018-05-24 | IPO fast entry (arts. 7.5, 7.6) | `DGATE` | `SOKM` | `SOKM` into XU050/XU030; `NETAS` out of XU050; `OTKAR` out of XU030 |
| 6 | 2018-08-31 18:51:40 | 2018-09-03 | merger — Migros absorbs Kipa | `KIPA` | `ITTFH` | — |
| 7 | 2020-05-20 17:01:47 | 2020-05-21 | merger — Oyak Çimento absorbs four cement issuers (art. 7.11 cited) | `ADANA` | `SARKY` | `MRDIN` into XSANK/XTM25 under the new bulletin name OYAK ÇİMENTO |
| 8 | 2020-09-30 16:41:20 | 2020-10-01 | merger — Şişe Cam absorbs four glass issuers (art. 7.16 cited, for Temettü 25 only) | `ANACM`, `SODA`, `TRKCM` | **none named** | `SODA`/`TRKCM` out of XU050 and XU030; `ANACM` out of XU050 |

**2019 has none.** All 26 of that year's index-change disclosures were read; none
touches XU100, XU050 or XU030. The largest, the 2019-11-01 new-market-structure
reclassification effective 04/11/2019, moves 120 shares between `BIST YILDIZ` and
`BIST ANA` and leaves the benchmark indices alone.

Events 1–7 are **balanced** — additions equal removals in every affected index.
Event 8 is not: three out, none in.

### 5.1 Cross-check against the independent trigger streams

The `Pazar Değişikliği` and `Kottan Çıkarma` subjects carry the art. 7.1/7.2
trigger *facts*, published independently of the index consequence. In 2017–2020
there are **30** of them (26 market transfers, 4 delistings). **29 of the 30**
pair with an `Endeks Şirketlerinde Değişiklik` disclosure published within 45 days
that shares a share code. The single exception, `EMNIS` on 2018-09-26, is recorded
`AMBIGUOUS` in the manifest rather than explained away; `EMNIS` is not in the
BIST 100 membership-derived universe for any candidate year.

The `Birleşme` subject was also queried: 443 disclosures in the window, 261 of
which name a universe ticker. These are process filings — board resolutions, SPK
applications, registration steps — and most never reach an index consequence.
They were **not** used to derive events. The point of the KAP route is precisely
that derivation is unnecessary: Borsa publishes the consequence itself, with its
own effective date.

## 6. Negative-evidence assessment

Per §8 of the task contract, "keyword search returned nothing" is not a negative.
What this audit can and cannot support:

**Supported.** A first-party archive with a published category taxonomy, stable
document ids, an inclusive date filter and a stated result cap that never bound;
a deterministic per-year, per-subject query whose exact parameters are recorded
in the manifest; full retrieval and full reading of all 107 returned documents
plus 17 attachments; fail-closed handling of empty responses; and an independent
corroborating stream that pairs 29/30.

**Not supported.** Exhaustiveness. Two facts block it:

1. **A demonstrated omission.** The 2017Q2 periodic review published by Borsa on
   2017-03-20 (node `11492`) is not on KAP. Queried `BIST Pay Endeksleri` for
   2017 (6 rows), `Endeks Şirketlerinde Değişiklik` for 2017 (23 rows), and then
   the entire `DUY` class for 2017-03-17 … 2017-03-25 (170 rows) — none carries
   it. The other three 2017 reviews and all twelve 2018–2020 reviews are on KAP.
2. **No completeness or retention statement.** None was located. The
   `Endeks Şirketlerinde Değişiklik` subject returns zero rows for every year
   2009–2015 and 11 for 2016, so the category itself begins in 2016 and cannot
   reach earlier years — consistent with a taxonomy introduction, but the source
   does not say so.

Per-security/year classification is therefore:

| Class | Count | What it covers |
| --- | --- | --- |
| `TRIGGER_EVENT_FOUND` | 8 disclosures (38 manifest event rows) | §5 |
| `NO_TRIGGER_EVENT_EVIDENCED` | 99 index-change disclosures + 30 trigger-fact disclosures | read in full, no benchmark-index effect |
| `SEARCH_INCOMPLETE` | 3 | the empty-body behaviour, the 2017-03-20 omission, the absent retention statement |
| `AMBIGUOUS` | 1 | `EMNIS` 2018-09-26 |

## 7. Effective-date derivation

**Quality: high, and better than the task contract anticipated.** §9 of the
contract provides for deriving a date from "second business day after KAP
publication" using a Borsa trading calendar. That derivation was **not needed**:
every one of the 107 disclosures prints `Geçerlilik Tarihi` per row, and the
printed date is the effective date. No business-day arithmetic was performed, no
weekday approximation was used, and no Borsa holiday calendar was consulted or
required.

Publication date **and time** are recorded for every event, so the art. 7 chapeau
16:30 cut-off is checkable rather than assumed. Every event in §5 was published
after 16:30 (earliest 16:41:20), consistent with an effective date on a later
business day in every case.

No `EFFECTIVE_DATE_UNRESOLVED` row arises from date derivation. The unresolved
case in §9 is an **ordering** problem, not a dating problem.

## 8. Reserve consumption

**Return value: `RESERVE_CONSUMPTION_REQUIRES_EVENT_CONFIRMATION`.**

| Question | Answer | Basis |
| --- | --- | --- |
| Is the reserve list ranked? | **Yes** | Borsa's own 2020-05-20 disclosure calls Sarkuysan the share "determined as the 1st reserve for the BIST 100 index" for 2020Q2. This is the first located first-party statement that the published order carries a rank |
| Does any rulebook state a consumption order? | **No** | Every version from Kasım 2015 to the 2020-09 split says only *"yerlerine yedek paylar alınır"* / *"yedeklerden tamamlanır"* — reserves are taken, with no ordering |
| Is the printed order self-evidently a rank? | **Not from the document** | In the 2016–2019 announcements the ADD and REMOVE columns are not alphabetical, and neither is the reserve column. From 2020Q1 the ADD and REMOVE columns **are** alphabetical while the reserve column is not. The reserve column carries a row number, but the source never labels what the number means |
| Are reserves index-specific? | **Yes** | Reserves are chosen per index (art. 6(e)); the 2020-05-20 disclosure names the BIST 100 reserve specifically |
| Does Borsa announce the replacement? | **Usually, and by name** | Events 2, 6 and 7 name the incoming share explicitly |
| Always? | **No** | Event 8 removes three BIST 100 constituents and names no BIST 100 replacement |
| Are already-consumed reserves skipped? | **UNKNOWN** | No first-party statement; not observable, since no window event consumed two reserves for the same index in the same period |
| Do simultaneous XU30/XU50 changes affect the XU100 replacement? | **UNKNOWN** | In events 1, 3, 4 and 5 the entering share joins all three indices and each index loses a different constituent, so the three are resolved independently — but no rule says they must be |
| Is there committee discretion? | **Yes, residually** | Art. 8.3, unchanged across every version: any matter not regulated by the Rules is determined **and announced** by the General Directorate. Reserve consumption order is such a matter |

The honest reading: consumption is deterministic **conditional on the
disclosure**, because art. 8.3 routes the unregulated part to a General
Directorate determination that is announced. It is **not** deterministic from the
rules alone, and event 8 proves the announcement does not always supply it.

## 9. Same-day and multi-event ordering

One case in the window forces the question, and it is not resolved.

Event 8 takes effect **01/10/2020**. That is also the first day of the 2020Q4
index period (01/10/2020 – 31/12/2020), announced on 2020-09-18. So on the same
date: the periodic review applies its own additions and removals, and a merger
removes three constituents with no named replacement.

Three readings are possible — the periodic review already anticipated the
removals; the removals apply after the review and are filled from the 2020Q4
reserve list (`ECZYT`, `EGGUB`, `KONYA`); or the index ran below 100 members. **No
first-party rule was located that orders same-day changes**, and no announcement
resolves it. Choosing any reading would be a construction of this audit
presented as a fact.

**Reconstruction is therefore marked fail-closed at 2020-10-01.** The prior
audit's §10 step 6 same-day ordering — explicitly flagged there as that audit's
construction, not a published rule — remains unsupported by first-party evidence.

## 10. Identity and succession

| Case | Classification | Evidence |
| --- | --- | --- |
| `NTTUR` → removed, `HURGZ` → added (2017) | `SUCCESSION_RULE_CONFIRMED` for the removal; `DISTINCT_SECURITY` for the entry | Borsa states the removal is caused by the Net Holding/Net Turizm share exchange and that Hürriyet Gzt. is taken in "because Net Turizm is removed from the BIST 100" |
| `KIPA` → removed, `ITTFH` → added (2018) | as above | same construction, Migros/Kipa |
| `ADANA` → removed, `SARKY` → added (2020) | as above, with art. 7.11 cited | the disclosure cites the article and the reserve rank |
| Mardin Çimento → OYAK ÇİMENTO (2020) | `SAME_SECURITY_CONTINUITY_CONFIRMED` | the merger attachment lists the surviving entity under the **pre-existing share code `MRDIN`** with the bulletin name changed to `OYAK CIMENTO`. Continuity is asserted by the source's own code, not by name similarity |
| `ANACM`/`SODA`/`TRKCM` → Şişe Cam (2020) | `SUCCESSION_RULE_CONFIRMED` for the removals; `INSUFFICIENT_IDENTITY_EVIDENCE` for any BIST 100 replacement | the disclosure resolves succession only for BIST Temettü 25 |
| Every ticker row | no ISIN | KAP publishes share code, bulletin name and a company GUID (`mkkMemberOid`), but no ISIN in this disclosure type. The GUID is a **KAP member** identifier, not a security identifier |

No continuity was inferred from names anywhere. The `A.V.O.D`/`AVOD` case
recorded by the prior audit is untouched by this one and remains unresolved.

## 11. Per-year trigger-stream completeness

| Year | Classification | Basis |
| --- | --- | --- |
| 2017 | `TRIGGER_STREAM_PARTIAL` | 23 index-change disclosures read in full, 2 BIST 100 events found with printed effective dates; but a scheduled announcement from the same year is demonstrably missing from this channel (§6.1) |
| 2018 | `TRIGGER_STREAM_PARTIAL` | 27 disclosures read, 4 BIST 100 events; 9 of 10 art. 7.1/7.2 trigger facts paired, the tenth being the `EMNIS` case recorded `AMBIGUOUS`; exhaustiveness unevidenced |
| 2019 | `TRIGGER_STREAM_PARTIAL` | 26 disclosures read, 0 BIST 100 events; 3 of 3 art. 7.1/7.2 trigger facts paired. Not `TRIGGER_STREAM_COMPLETE_WITH_ZERO_EVENTS`: §8 requires the complete applicable search population, and the constituent list needed to define a per-security population is unacquired |
| 2020 | `TRIGGER_STREAM_PARTIAL` | 31 disclosures read, 2 BIST 100 events, one of which (event 8) is unbalanced and unresolved |

No year is classified `TRIGGER_STREAM_COMPLETE` or
`TRIGGER_STREAM_COMPLETE_WITH_ZERO_EVENTS`.

## 12. Per-year point-in-time adequacy

| Year | Classification | Binding constraint |
| --- | --- | --- |
| 2017 | `INSUFFICIENT_DATA` | trigger-stream exhaustiveness unevidenced with a demonstrated same-year omission; seed constituent state unacquired |
| 2018 | `INSUFFICIENT_DATA` | trigger-stream exhaustiveness unevidenced; seed constituent state unacquired |
| 2019 | `INSUFFICIENT_DATA` | as 2018 |
| 2020 | `INSUFFICIENT_DATA` | additionally the 2020-10-01 same-day collision with three unreplaced BIST 100 removals (§9) |

No year is `POINT_IN_TIME_RECONSTRUCTIBLE`. The distance to it has changed
substantially, though, and it is worth being precise about what is now in hand
versus what is not:

**Now evidenced and deterministic:** the extraordinary-event stream itself; the
per-event index-level consequence; the effective date, printed rather than
derived; publication timestamps precise enough to test the art. 7 cut-off; the
period-correct rule text for every part of the window except 2020-01-20 →
2020-04-06; and reserve consumption in three of the four merger cases.

**Still missing:** a point-in-time seed constituent list (Product 3184, an owner
decision); a first-party basis for asserting the KAP stream is exhaustive; a
same-day ordering rule; and the resolution of event 8.

## 13. Private raw archive and repository boundary

141 objects were added, all outside the repository, none committed:

| Group | Count | Class |
| --- | --- | --- |
| KAP disclosure bodies, structured JSON, one per index-change disclosure 2017–2020 | 107 | `PRIVATE_LOCAL_RAW` |
| KAP disclosure attachments (PDF) | 17 | `PRIVATE_LOCAL_RAW` |
| KAP query result sets (index changes, other topics, mergers, taxonomy, verification counts) | 5 | `PRIVATE_LOCAL_RAW` |
| KAP query-surface page snapshot | 1 | `PRIVATE_LOCAL_RAW` |
| Period-correct rulebook PDFs newly retrieved (Kasım 2015, Mayıs 2018, Haziran 2018, Aralık 2018/10.12, Nisan 2020) | 5 | `PRIVATE_LOCAL_RAW` |
| Circular 2020/60 PDF | 1 | `PRIVATE_LOCAL_RAW` |
| Rule-set change announcement snapshots (nodes `11703`, `12289`, `12485`, `12514`, `12553`) | 5 | `PRIVATE_LOCAL_RAW` |

Each object is SHA-256 hashed with its byte size and access date, and referenced
only by the symbolic form
`PRIVATE_LOCAL_RAW:bist-membership/{raw,kap-triggers}/<name>`. No absolute
archive path appears in any tracked file. **No HTML, JSON, PDF or XLSX source
byte is tracked in Git.** Consistent with `FI-SOURCE-OWNER-AMENDMENT-01` this is
`INTERNAL_OWNER_AUTHORIZED` internal research use, **not** an external licence
grant; public redistribution of third-party raw data remains prohibited.

Nothing was written under `data/provenance/`.

## 14. Manifest

[`docs/evidence/bist_membership_kap_trigger_sources.csv`](evidence/bist_membership_kap_trigger_sources.csv)
— **191 rows**.

| Row class | Count |
| --- | --- |
| Benchmark-index membership events, per ticker per index | 38 |
| Index-change disclosures reviewed with no benchmark effect | 99 |
| Art. 7.1/7.2 trigger facts used as a cross-check | 30 |
| Period-correct rule authority (rulebooks, circular, rule-set nodes) | 13 |
| Per-year search scope and negative-evidence records | 4 |
| KAP search mechanism and taxonomy | 3 |
| Archive-completeness findings | 2 |
| Correction of the prior finding | 1 |
| `AMBIGUOUS` (`EMNIS`) | 1 |

**NA convention**, unchanged from the 04B manifests: `NA` means the field does not
apply to that record type; `UNKNOWN` means it applies but is not established by
evidence. Neither is ever a placeholder for a fabricated value, and **no cell is
blank**. Turkish characters are transliterated to ASCII for consistency with the
sibling manifests; share codes and stable ids are unaffected.

## 15. Scientific and no-peeking boundary

| Control | State |
| --- | --- |
| Outcome inspection | `NO_NEW_OUTCOME_INSPECTION=true` — no return, benchmark-relative outcome, model score, prediction, IC or p-value was opened, loaded or inspected |
| Modeling artifacts | Untouched — no `data/trusted_clean/modeling_dataset*` and no `experiments/results_*` file was read for its values |
| Models run | **None** — `make data`, `make benchmark`, `make research`, `make research-excess` NOT RUN |
| Scientific-data integration | **None** — no event row was written into any modeling, feature, target, benchmark or universe file |
| Stage A | Unchanged, byte-identical |
| Owner amendment | Unchanged, byte-identical |
| 04B report/manifest and event audit/manifest | Unchanged, byte-identical |
| Stage B | **Not authored** |
| Protected boundary | 351 → 351, digest unchanged, no re-pin |
| Governed provenance namespace | `data/provenance/` untouched |

**Interpretation limits.** Finding the extraordinary-event stream does not make a
historical universe valid; more covered years do not improve any estimate; event
reconstruction does not establish model validity; and sourcing success does not
imply predictive edge. This task determined only whether the extraordinary
membership-change path is source-supported. **No reliable predictive edge has
been established.**

## 16. Recommendation for the next task

1. **Owner decision on DataStore registration is now the single largest gate.**
   The event side of the problem is largely solved; the seed constituent state is
   not. Product 3184 remains an owner decision, unchanged.
2. **Resolve event 8 before anything is built.** One bounded question decides
   whether 2020 is reconstructible: what BIST 100 membership was on 2020-10-01.
   The cheapest first-party routes are the Borsa daily bulletin
   (*Günlük Bülten*) constituent listing for 01.10.2020 and the numbered circular
   series around 2020/60. If neither resolves it, 2020 stays `INSUFFICIENT_DATA`
   and saying so is the protocol working.
3. **If a shorter window is acceptable, 2018–2019 is now the strongest
   candidate.** Both years have a fully read, effective-dated event stream, all
   trigger facts paired, balanced additions and removals in every event, and no
   same-day collision. They remain `INSUFFICIENT_DATA` only because
   exhaustiveness is unevidenced and the seed state is unacquired — both
   addressable, unlike event 8.
4. **Do not author Stage B.** No candidate year is
   `POINT_IN_TIME_RECONSTRUCTIBLE`.

Benchmark acquisition (Products 3180/3181, XU100 series, Yahoo) and fundamentals
acquisition remain separate, untouched source streams.

---

`NO_NEW_OUTCOME_INSPECTION=true`
`NO_RELIABLE_PREDICTIVE_EDGE_ESTABLISHED=true`
`FINANCEIQ_DATA_EXPAND_04B_KAP_TRIGGER: FI_DATA_EXPAND_04B_KAP_TRIGGER_PARTIAL`
