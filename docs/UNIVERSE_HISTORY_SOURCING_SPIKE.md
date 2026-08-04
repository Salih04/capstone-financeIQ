# Point-in-time BIST 100 universe history sourcing spike

## 1. Task identity

**Task identity:** R3-SPIKE-01 (Phase 3, Wave 3C) — "Point-in-time universe history sourcing spike (memo only)".
**Research access date for every source in this memo:** 2026-08-04.
**Memo type:** feasibility research. No dataset, script, configuration, or generated artifact was created or changed by this task.
**Repository state at authoring:** branch `local/universe-history-sourcing-spike-000a22`, HEAD `e7c2089044b661929ffcc4ab4eb9a2cb96cbf677`, identical to `origin/main`, clean worktree.

---

## 2. Executive verdict

**`FEASIBLE_WITH_DOCUMENTED_GAPS`**

Free, first-party, effective-dated evidence for BIST 100 membership **change events** demonstrably exists and is publicly reachable without credentials, for periods inside the required window. Borsa İstanbul publishes quarterly periodic constituent-change tables (ticker + issuer name, "to be included" / "to be excluded" / "substitute"), and the same decisions are disclosed on KAP with attached first-party PDFs. The rulebook governing review timing and extraordinary changes is also free and dated.

However, **no required period reaches `CONFIRMED`**, because three things were *not* established in this spike:

1. **No free official historical full-constituent snapshot was found for any past date.** Both Borsa İstanbul's index page and KAP's index page publish *current* membership only. A reconstruction would therefore have to anchor on a present-day snapshot and roll the event stream **backwards** — which fails closed the moment the event stream has a hole.
2. **The non-periodic (extraordinary) change stream was not shown to be completely enumerable.** The rules make intra-quarter exclusions routine (permanent trading halt, suspension beyond 5 consecutive trading days, transfer to the Watchlist Market — each effective on the date of the event, not at a quarter boundary). Individual such disclosures exist on KAP, but this spike did not find a free, complete, filterable index of *all* BIST 100 non-periodic changes for 2020–2025.
3. **Three required quarterly announcements were not located at all** in this spike (Q3 2024, Q4 2024, Q1 2025 effective periods). Their absence from the enumeration is itself a finding: the announcement archive is UI-paginated and the default listing response does not return the complete set.

The verdict is set by the weakest required period, per the task's rule. Every period in §8 classifies as `PARTIAL` or `NOT FOUND`; none classifies as `CONFIRMED`. Reconstruction is a **substantial, mostly manual, evidence-archival project**, not a scripted download.

**Immediate next recommendation:** authorize only the smaller evidence-completion spike **R3-SPIKE-01a** first. Its purpose is to decide whether the missing historical anchor, quarterly gaps, and extraordinary-event coverage can be closed. Only after that decision should a separately authorized collection/reconstruction task be considered, and only with a fail-closed design in which any period with an unresolved event hole is marked unknown rather than filled. **No-go** for any attempt to retrofit point-in-time membership onto existing FinanceIQ artifacts.

---

## 3. Scope and non-goals

**In scope:** whether an auditable, effective-dated, point-in-time BIST 100 membership history can be sourced for the periods FinanceIQ's research protocol needs — feature years 2020–2024, target/evaluation years 2023–2025, plus whatever earlier effective periods are required to establish membership in force at each feature-year cutoff.

**Explicitly not in scope / not done:**

- No membership dataset, CSV, JSON, manifest, cache, or source archive was created.
- No scraper, downloader, parser, script, test, or configuration was written or committed.
- No repository data, model, experiment result, or generated artifact was read into, changed, or regenerated.
- No current universe membership was altered.
- No paid data product was purchased or accessed. No credentials, authenticated sessions, or paywalled material were used.
- No robots directive, rate limit, access control, or CAPTCHA was bypassed.
- No legal conclusion is offered. §12 records observable access and licensing facts only and defers to owner/legal review.
- **No membership list is asserted from recollection.** Where a ticker appears below, it is because it was read out of a first-party document retrieved on 2026-08-04, and the document is cited.

---

## 4. Current repository limitation

`docs/universe_audit.md` (audit date 2026-07-12) is the controlling internal statement and this memo does not weaken it:

- The repository verifies membership in the **FinanceIQ configured universes**, not point-in-time BIST 100 membership.
- The public cohort is defined by `data/config/universe_public_40.csv`, which carries no stated selection criterion and no effective date. The training cohort is `data/config/universe_training_bist100.csv`.
- Both configuration files first appear in git **after** the 2020–2025 study window, so the cohort is retrospectively fixed.
- `scripts/data_collection/pipeline.py` sets `is_bist100` by testing whether an undated `indices` text field contains `XU100`; there is no membership-effective date anywhere in the pipeline.
- `data/config/bist100_candidates.csv` self-describes as a static, manually curated list against a "2024-2025 reference" — a current/recent proxy, not history.

The concrete consequence, restated: a ticker-year row in `data/trusted_clean/modeling_dataset_public_2020_2025.csv` or `data/trusted_clean/modeling_dataset_training_2020_2025.csv` does **not** establish that the security was an index constituent — or even listed — in that year.

This spike found first-party evidence that directly illustrates the problem rather than merely asserting it. Borsa İstanbul's Q3 2025 periodic announcement lists `DSTKF` and `KUYAS` among the stocks **to be included** in the BIST 100 effective 2025-07-01.<sup>[S3]</sup> Both tickers are present in the repository's public cohort for the whole 2020–2025 window, and `docs/universe_audit.md` separately records that `DSTKF` has no committed year-end price observation for 2020–2024. A retrospective cohort therefore contains at least one name that first-party evidence places outside the BIST 100 for most of the study window.

---

## 5. Point-in-time membership standard

A membership record is point-in-time only if it can answer "which securities were in index X on date D, using only information published on or before D" without back-filling from a later state. The conceptual schema below is what such a record would have to carry. **This is a conceptual schema only — nothing was built, and no file with these columns exists or should be created under this task.**

| Field | Purpose |
|---|---|
| `index_name` | e.g. BIST 100 |
| `index_rulebook_version` | which rulebook/methodology version governed the event (see §9 — the article numbering changed inside the study window) |
| `security_id` | stable identifier (ISIN preferred; see §10 for why ticker is not sufficient) |
| `ticker_at_time` | ticker as printed in the source document |
| `ticker_current` | current ticker or successor, where a mapping is evidenced |
| `issuer_name_at_time` | issuer name as printed in the source document |
| `announcement_date` | date the decision was published |
| `effective_from` | first date the membership state is in force |
| `effective_to` | last date in force, or null while open |
| `superseded_by_event_id` | the event that closed this interval |
| `event_type` | `scheduled_inclusion`, `scheduled_exclusion`, `extraordinary_inclusion`, `extraordinary_exclusion`, `ticker_change`, `name_change`, `merger_succession`, `delisting`, `substitute_activation` |
| `source_url` / `source_document_id` | direct official URL or KAP disclosure id |
| `source_title` | document title as published |
| `publication_date` | source's own publication timestamp |
| `retrieved_at` | retrieval date |
| `source_checksum` / `archive_id` | integrity anchor, **only if** a later task is authorized to archive locally |
| `evidence_confidence` | first-party / first-party-via-archive / corroborating-secondary |
| `unresolved_ambiguity` | free text; non-empty means the interval must be treated as unknown |

A record missing `effective_from`, or carrying only an announcement date, is not point-in-time.

---

## 6. Official source inventory

All rows accessed **2026-08-04**. "First-party" means published by Borsa İstanbul A.Ş. or by KAP (Kamuyu Aydınlatma Platformu / Public Disclosure Platform, operated by MKK).

| # | Source owner | Title / type | Party | Covered dates | Ann. date | Eff. date | Snapshot or change | Machine-readable | Free/public | Stable ID/URL | Historical archive quality | Usefulness | Limitations |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | Borsa İstanbul | Index Announcements listing (`/en/indices/index-announcements`) | First-party | Listing surfaced items dated 2013–2026 | n/a | n/a | Index of documents | Partly (HTML, filterable) | Yes | Section URL stable; per-item URLs contain a numeric id **and** a required slug | Mixed — the default response did not return all known quarterly items | Discovery entry point | Numeric-id-only URLs 404 without the slug; default listing is incomplete; enumeration requires manual paging of the date/type filters |
| S2 | Borsa İstanbul | Quarterly "constituent changes to the BIST Stock Indices" announcements (HTML) | First-party | Individually verified: Q1 2020, Q2 2021, Q3 2025 | Yes | Yes | **Change events only** | Yes — real `<table>` with ticker + issuer name columns | Yes | Slugged URL per quarter | Good where located | **Primary evidence** | Never a full constituent list; included/excluded/substitute sit in adjacent columns of one table, so naive text extraction interleaves them (§10) |
| S3 | Borsa İstanbul | Q3 2025 announcement, id 15121 | First-party | Eff. 2025-07-01 → 2025-09-30 | 2025-06-20 | Yes | Change events | Yes | Yes | Yes | Good | Verified example | As S2 |
| S4 | Borsa İstanbul | Q1 2020 announcement, id 13577 | First-party | Eff. 2020-01-01 → 2020-03-31 | 2019-12-17 | Yes | Change events | Yes | Yes | Yes | Good | Earliest verified in-window quarter | As S2 |
| S5 | Borsa İstanbul | Q2 2021 announcement, id 14147 | First-party | Eff. 2021-04-01 → 2021-06-30 | 2021-03-15 | Yes | Change events | Yes | Yes | Yes | Good | Verified mid-window quarter | As S2 |
| S6 | Borsa İstanbul | *BIST Stock Indices Ground Rules*, April 2020 (PDF) | First-party | Rulebook in force during part of the window | Doc-dated | n/a | Rules | Text-extractable PDF | Yes | **Version-agnostic filename** — same URL, changing content | Poor as an archive: no version in the path | **Decisive for §9 mechanics** | The URL does not pin a version; a local archived copy + checksum is required for any citation to stay reproducible |
| S7 | Borsa İstanbul | *BIST Market Cap Weighted Stock Indices Methodology* (successor rulebook, incl. a 2026-01 draft PDF) | First-party | Later window | Doc-dated | n/a | Rules | PDF | Yes | Dated filename on the draft | Better than S6 | Confirms the rulebook was renamed and renumbered mid-window | Draft status must not be cited as the rule in force |
| S8 | KAP | Disclosure 875734 — Q4 2020 periodic index changes, by BORSA İSTANBUL A.Ş. | First-party | Eff. 2020-10-01 → 2020-12-31 | Submitted 2020-09-18 18:22:50 | In prose + attachment | Change events | Attachments are PDF; body is prose | Yes | Numeric disclosure id | Good | **Independent corroboration path for the 2020 quarters** | 2020-era taxonomy has **no structured effective-date field**; the tables live only in the attached PDFs |
| S9 | KAP | Disclosure 1302173 — periodic index changes, by BORSA İSTANBUL A.Ş. (participation indices) | First-party | Eff. 2024-07-01 → 2024-11-30 | Submitted 2024-06-26 18:13:11 | **Structured field** | Change events | Taxonomy-tagged (`oda_ChangeInConstituentsOfBISTIndices…`) + PDF | Yes | Numeric disclosure id | Good | Shows the **later** taxonomy carries per-row `Geçerlilik Tarihi / Efective Date` [sic] | The example is a participation-index disclosure; equivalent structure for BIST 100 in every year was not verified |
| S10 | KAP | Disclosure attachment endpoint `/tr/api/file/download/<opaque-id>` | First-party | Per disclosure | n/a | n/a | Attachment | PDF | Yes | Opaque, apparently stable id | Good | Attachments are directly retrievable and checksummable | PDF layout carries letter-spacing artifacts that corrupt naive text extraction |
| S11 | KAP | `/tr/Endeksler?indice=…` current index constituents | First-party | **Current state only** | n/a | n/a | Snapshot | HTML | Yes | Query URL | None (no history) | Candidate **anchor snapshot** for backward rolling | Publishes today's membership; carries no historical validity whatsoever |
| S12 | Borsa İstanbul | `/en/index/xu100` index detail page | First-party | Current state | n/a | n/a | Metadata + current constituents | HTML | Yes | Yes | None | Candidate anchor snapshot | Page states the constituent count "shows the number of constituents in previous day"; no historical constituent download was found |
| S13 | Borsa İstanbul | `robots.txt` | First-party | n/a | n/a | n/a | n/a | Text | Yes | Yes | n/a | Access-policy evidence | Contents observed: `User-agent: *` / `Allow: /`. This is a crawler directive only and does **not** substitute for the site's copyright/terms (§12) |
| S14 | KAP | `robots.txt` | First-party | n/a | n/a | n/a | n/a | — | **Not served** | n/a | n/a | Access-policy evidence | The request returned a KAP error page rather than a robots file; absence of a directive is **not** permission |
| S15 | Borsa İstanbul | DataStore (`datastore.borsaistanbul.com`) | First-party | Unknown | — | — | Unknown | Unknown | **Not established as free** | Yes | Unknown | Possible paid historical route | The landing response was a JavaScript application shell; product scope, pricing, and licensing were **not** established in this spike and must not be assumed |
| S16 | Internet Archive Wayback | Archived copies of the announcements listing | Secondary/recovery | — | — | — | — | — | Yes | — | **Not established** | Would-be recovery route | The Availability API returned a closest capture dated **2025-10-06** (timestamp `20251006022039`) for the announcements listing when queried at the 2020 timestamp; it did not return a 2020-era capture for that timestamp probe. That returned 2025 listing-page capture does not establish historical coverage for the required 2020–2024 window. The CDX endpoint could not be accessed from this environment to enumerate all available captures, so web-archive fallback for the required historical window remains unproven. This does not establish that no 2020-era captures or relevant archive records exist. Archived copies are not first-party publication and carry chain-of-custody limits |
| S17 | Financial media (Bloomberg HT, Ekonomist, Midas, doviz.com, Mondovisione) | Index-change news reports | **Secondary — discovery lead only** | Various | Yes | Sometimes | Change events | No | Yes | Weak | Weak | Found candidate announcement titles/quarters | **Must never be the sole basis for a membership claim.** Used here only to locate first-party URLs |

---

## 7. Source-by-source findings

### 7.1 Borsa İstanbul quarterly periodic-change announcements — the primary evidence

Verified by direct retrieval on 2026-08-04. The Q1 2020 announcement (`/en/announcement/13577/…-first-quarter-2020`) publishes on-page date **12/17/2019**, states that changes are made "In accordance with the article 8.2 of BIST Equity Indices Ground Rules … for the first quarter of 2020 (January 1, 2020 - March 31, 2020)", and carries a heading **"PERIODIC INDEX CHANGES FOR THE PERIOD JANUARY 1, 2020 – MARCH 31, 2020"** followed by a section headed **"BIST 100 INDEX"**.<sup>[S4]</sup>

The payload is a genuine HTML `<table>`. Its header row is `STOCKS TO BE INCLUDED | STOCKS TO BE EXCLUDED | SUBSTITUTE STOCKS`, and each body row carries an ordinal, a ticker, and an issuer name for each of the three columns — e.g. the first body row reads `1 · ADANA · ADANA CIMENTO (A)` (included), `1 · AFYON · AFYON CIMENTO` (excluded), `1 · BOLUC · BOLU CIMENTO` (substitute).<sup>[S4]</sup> This is the single most encouraging finding in the spike: the evidence is structured, carries both ticker and contemporaneous issuer name, and is free.

The Q3 2025 announcement follows the identical pattern with an explicit application sentence: changes "will be applied after the close of business on Monday, June 30, 2025 and will be effective on Tuesday, July 1, 2025", for the period 2025-07-01 → 2025-09-30, announced 2025-06-20.<sup>[S3]</sup> The Q2 2021 announcement likewise: announced 2021-03-15, "applied after the close of business on Wednesday, March 31, 2021 and … effective on Thursday, April 1, 2021", period 2021-04-01 → 2021-06-30.<sup>[S5]</sup>

**Announcement date and effective date are therefore distinct, both published, and both machine-readable from these pages.** That satisfies the effective-date requirement for the periodic stream.

**But every one of these documents is a change list, not a snapshot.** No page examined contained a full 100-name constituent list.

### 7.2 The announcement listing is not a complete index

Retrieving the Index Announcements listing returned a large HTML document containing on the order of three hundred distinct announcement links. From it, quarterly BIST-stock-index constituent-change announcements were enumerated for the following effective periods: Q1–Q4 2020, Q1–Q4 2021 (Q1 2021 id 14132, Q2 14147, Q3 12664, Q4 14213), Q1–Q4 2022 (12771, 14347, 14401, 12960), Q1–Q4 2023 (14476, 14516, 14545, 13125), Q1 and Q2 2024 (14627, 14654), and Q3 2025 (15121). Web search additionally surfaced Q2 2025 (14784), Q4 2025 (15220), Q1 2026 (15293) and Q2 2026 (15392).

**Not located in this spike: the announcements for effective periods Q3 2024, Q4 2024, and Q1 2025.** This is not evidence that they do not exist — the listing exposes date-range and type filters plus a per-page selector, and the default response is evidently partial. It *is* evidence that complete enumeration is a manual, filter-driven task rather than a single fetch, and that the reconstruction cannot be declared complete until those periods are retrieved and read.

Two further access facts: the numeric announcement id alone does not resolve (nine probed id-only URLs all returned the site's "Sayfa Bulunamadı" page — the slug is mandatory), and the legacy `/en/duyuru/<id>/…` URL form surfaced by search for a 2020 announcement did not respond at all (the connection closed with an empty reply on two attempts, once via the fetch tool and once directly). Older URL forms should be assumed unreliable.

### 7.3 KAP disclosures — independent corroboration, with a taxonomy break

KAP carries the same Borsa İstanbul decisions as formal disclosures under the title "Endeks Şirketlerinde Değişiklik" / "Change In Constituents of BIST Indices".

Disclosure **875734** (submitted **2020-09-18 18:22:50**) states, in both Turkish and English, that under "article 8.2 of BIST Market Cap Weighted Equity Indices Ground Rules" the BIST 100, BIST 50, BIST 30, BIST Liquid Banks and BIST Liquid 10 Ex Banks indices "will have attached constituent changes for the fourth quarter of 2020 (October 1, 2020 - December 31, 2020)". Its two attachments are `2020_4_dönemsel_değişiklikler.pdf` and `2020_4_periodic_changes.pdf`.<sup>[S8]</sup> The English attachment was retrieved directly from `https://www.kap.org.tr/tr/api/file/download/4028328d745d13ff0174a1cbcc893a35` (171 116 bytes, SHA-256 `6938f6c80087d3b91b8e82f830403b735052443a5f3d6e586a926e38cd291310` as retrieved 2026-08-04) and contains the "PERIODIC INDEX CHANGES FOR THE PERIOD OCTOBER 1, 2020 – DECEMBER 31, 2020" tables, with a `BIST 100 INDEX` block listing six inclusions, six exclusions and three substitutes with tickers and issuer names.<sup>[S10]</sup>

So the 2020 quarters are corroborable from **two** first-party publishers. That materially strengthens 2020 relative to years where only one route was checked.

**The taxonomy break matters.** The 2020 disclosure's tagged fields are limited to an explanation text block — there is **no** structured effective-date element; the dates exist only in prose and inside the PDF. The 2024 disclosure **1302173** (submitted 2024-06-26 18:13:11) does carry a row-level structured table with the columns `Pay Adı / Related Stock`, `Kapsamına Dahil Edildiği Endeks / Index In Which Included`, `Kapsamından Çıkarıldığı Endeks / Index From Which Excluded`, and `Geçerlilik Tarihi / Efective Date` [spelling as published].<sup>[S9]</sup> A future ingestion therefore faces **two different extraction problems in the same window**: PDF table parsing for the early years, structured-field reading for the later ones.

### 7.4 No free official historical snapshot was found

KAP publishes current index constituents at `/tr/Endeksler?indice=…`, and Borsa İstanbul publishes an index detail page at `/en/index/xu100`. Both are current-state. The `xu100` page's own footnote states the constituent count "shows the number of constituents in previous day", and no historical constituent file (PDF/XLS/CSV) was found linked from it. Neither can be treated as historically valid for any earlier date.

This forces an **anchor-and-roll-back** design: take a dated present-day snapshot as the anchor, then invert the full event stream backwards to each target cutoff. That design is only as sound as the completeness of the event stream — which is exactly the gap in §7.2 and §7.5.

### 7.5 Non-periodic changes are frequent by rule, and were not enumerated

The April 2020 Ground Rules devote §7 to "NON-PERIODIC CHANGES ON CONSTITUENT STOCKS". §7.1 provides that stocks whose trading is halted permanently, stocks suspended for more than 5 consecutive trading days (other than for additional public offering), and stocks transferred to the Watchlist Market "are excluded from all the indices under which they are covered, to be effective on the date of halt, suspension or transfer", and that exclusions from BIST 30/50/100, BIST Liquid 10 Ex Banks and BIST Dividend 25 "are replaced with substitute stocks". §7.2 handles other market transfers "effective from the date the transfer takes place". §7.3 provides that re-admitted stocks rejoin the relevant indices **except** BIST 30/50/100 and BIST Liquid 10 Ex Banks during the same index period. §7.4/§7.5 govern newly traded stocks, with fast-entry to BIST 100 possible from the 5th business day of trading for sufficiently large offerings.<sup>[S6]</sup>

Two consequences: **(a)** BIST 100 membership genuinely changes intra-quarter, so a quarterly event stream alone is insufficient; **(b)** the substitute list is not decorative — it is the mechanism by which mid-period replacements occur, so substitutes must be captured, not discarded.

Individual non-periodic KAP disclosures plainly exist (many single-company "…shares will be included in …" announcements were visible in the Borsa İstanbul listing). What was **not** established is a free, complete, filterable enumeration of every BIST 100 non-periodic change for 2020–2025. Until that exists, no period can be called complete.

---

## 8. Historical coverage matrix

Columns: **Baseline** = official baseline constituent snapshot found for that period; **Events** = official change events found; **Eff. dates** = explicit effective dates; **Extraord.** = extraordinary/non-periodic changes covered; **Identity** = identity reconciliation possible from the evidence found; **Confidence** = completeness confidence; **Gap** = principal unresolved gap.

| Effective period | Baseline | Events | Eff. dates | Extraord. | Identity | Confidence | Unresolved gap | Classification |
|---|---|---|---|---|---|---|---|---|
| Pre-2020 anchor (a full snapshot at any date before 2020-01-01) | NOT FOUND | n/a | n/a | n/a | n/a | none | No free official historical snapshot located at any past date | `NOT FOUND` |
| 2020 Q1 (2020-01-01→03-31) | NOT FOUND | CONFIRMED (id 13577, verified) | CONFIRMED | NOT FOUND | PARTIAL (ticker+issuer name, no ISIN) | low-medium | Non-periodic stream not enumerated | `PARTIAL` |
| 2020 Q2 (04-01→06-30) | NOT FOUND | PARTIAL (id 13353 resolves; content not read) | PARTIAL | NOT FOUND | PARTIAL | low | Content unread; non-periodic stream | `PARTIAL` |
| 2020 Q3 (07-01→09-30) | NOT FOUND | PARTIAL (id 14106 resolves; content not read) | PARTIAL | NOT FOUND | PARTIAL | low | Content unread; non-periodic stream | `PARTIAL` |
| 2020 Q4 (10-01→12-31) | NOT FOUND | CONFIRMED (id 14118 resolves; KAP 875734 + attachment verified) | CONFIRMED | NOT FOUND | PARTIAL | medium | Non-periodic stream not enumerated | `PARTIAL` |
| 2021 Q1 | NOT FOUND | PARTIAL (id 14132 listed) | PARTIAL | NOT FOUND | PARTIAL | low | Content unread; non-periodic stream | `PARTIAL` |
| 2021 Q2 | NOT FOUND | CONFIRMED (id 14147, verified) | CONFIRMED | NOT FOUND | PARTIAL | low-medium | Non-periodic stream not enumerated | `PARTIAL` |
| 2021 Q3 / Q4 | NOT FOUND | PARTIAL (ids 12664, 14213 listed) | PARTIAL | NOT FOUND | PARTIAL | low | Content unread; non-periodic stream | `PARTIAL` |
| 2022 Q1–Q4 | NOT FOUND | PARTIAL (ids 12771, 14347, 14401, 12960 listed) | PARTIAL | NOT FOUND | PARTIAL | low | Content unread; non-periodic stream | `PARTIAL` |
| 2023 Q1–Q4 | NOT FOUND | PARTIAL (ids 14476, 14516, 14545, 13125 listed) | PARTIAL | NOT FOUND | PARTIAL | low | Content unread; non-periodic stream | `PARTIAL` |
| 2024 Q1–Q2 | NOT FOUND | PARTIAL (ids 14627, 14654 listed) | PARTIAL | NOT FOUND | PARTIAL | low | Content unread; non-periodic stream | `PARTIAL` |
| **2024 Q3–Q4** | NOT FOUND | **NOT FOUND** | NOT FOUND | NOT FOUND | NOT FOUND | none | **Quarterly announcements not located in this spike** | `NOT FOUND` |
| **2025 Q1** | NOT FOUND | **NOT FOUND** | NOT FOUND | NOT FOUND | NOT FOUND | none | **Quarterly announcement not located in this spike** | `NOT FOUND` |
| 2025 Q2 | NOT FOUND | PARTIAL (id 14784, via secondary lead) | PARTIAL | NOT FOUND | PARTIAL | low | Content unread; non-periodic stream | `PARTIAL` |
| 2025 Q3 | NOT FOUND | CONFIRMED (id 15121, verified) | CONFIRMED | NOT FOUND | PARTIAL | low-medium | Non-periodic stream not enumerated | `PARTIAL` |
| 2025 Q4 | NOT FOUND | PARTIAL (id 15220, via secondary lead) | PARTIAL | NOT FOUND | PARTIAL | low | Content unread; non-periodic stream | `PARTIAL` |
| 2026 Q1 (needed only to close the 2025 target year) | NOT FOUND | PARTIAL (id 15293, via secondary lead) | PARTIAL | NOT FOUND | PARTIAL | low | Content unread | `PARTIAL` |

**Yearly roll-up:** 2020 `PARTIAL` · 2021 `PARTIAL` · 2022 `PARTIAL` · 2023 `PARTIAL` · **2024 `NOT FOUND` for half the year** · **2025 `NOT FOUND` for Q1**.

No period is `CONFIRMED`, because `CONFIRMED` was reserved for evidence supporting a **complete** effective-dated membership reconstruction, and the missing baseline snapshot plus the unenumerated non-periodic stream prevent that everywhere. No period is `CONFLICTING`: no two first-party sources were observed to disagree in this spike.

---

## 9. Effective-date and rebalance mechanics

**Calendar-year membership is not sufficient.** The April 2020 Ground Rules are explicit:

- §2.14 "Review Day": for BIST 30, BIST 50 and BIST 100 the Review Day is "The last trading day of November, February, May and August", using Number of Shares and Free Float Ratio.<sup>[S6]</sup>
- §2.15 "Index Period": "There are 4 index periods for BIST 30, BIST 50, BIST 100, BIST Liquid Banks and BIST Liquid 10 Ex Banks indices, namely, January-March, April-June, July-September and October-December."<sup>[S6]</sup>
- §8.2: at periodic reviews the stocks to be included and the substitute lists are determined by the Index Department subject to management approval.<sup>[S6]</sup>

So the BIST 100 rebalances **quarterly**, on a Review Day roughly one month before the period start, with the decision announced in the interval between. The announcements confirm this in practice: Q1 2020 announced 2019-12-17 for a 2020-01-01 effective date; Q2 2021 announced 2021-03-15 for 2021-04-01; Q3 2025 announced 2025-06-20 for 2025-07-01.<sup>[S3][S4][S5]</sup>

Any FinanceIQ feature-year cutoff at a calendar year end therefore falls inside a **Q4 index period** whose membership was fixed by the preceding August Review Day and then modified by any intervening non-periodic events. A "membership in year Y" field is not well-defined; only "membership on date D" is.

**Rulebook versioning inside the window.** The 2020 KAP disclosure cites "article 8.2" of the "BIST Piyasa Değeri Ağırlıklı Pay Endeksleri **Temel Kuralları**" (Ground Rules); the 2024 disclosure cites "article 10.3" of the "BIST Piyasa Değeri Ağırlıklı Pay Endeksleri **Kural Seti**" (Methodology).<sup>[S8][S9]</sup> Search results also surfaced Borsa İstanbul announcements that the Ground Rules were updated and that the document was later reissued as a Methodology. Consequently a point-in-time record must pin **which rulebook version governed each event**, and cannot cite "the rulebook" generically. The generic URL `bist-stock-indices-ground-rules.pdf` currently serves the **April 2020** edition (585 885 bytes, SHA-256 `892a37c4c74a1721eb815781fbb35a190d14124d5c7c1c9f6affed7ba96d0c3d` as retrieved 2026-08-04) — but the path contains no version, so that mapping can silently change.

**What the sources give and do not give:**

| Question | Answer from the evidence found |
|---|---|
| Explicit effective dates? | **Yes**, for the periodic stream — stated as an explicit period and as an application sentence naming the exact business day. |
| Only announcement dates? | No — both are published, and they are distinct. |
| Period labels without exact dates? | No for the periodic stream; the exact date is given alongside the label. |
| Current-state lists with no historical validity? | Yes — S11 and S12 are exactly this, and must be labelled as such. |
| Changes but not complete snapshots? | **Yes — this is the central structural limitation.** |

**Can an event stream become snapshots?** Yes in principle, no without a starting baseline. Because BIST 100 has a fixed constituent count, a complete, correctly ordered, sign-consistent event stream can be inverted from a dated anchor snapshot back to any earlier date. The required starting baseline is therefore **one** dated full constituent list — and the only free official ones found are *today's* (S11/S12), which forces backward rolling. Every hole in the stream (an unlocated quarter, a missed non-periodic exclusion, an unrecorded substitute activation) propagates to **all earlier dates**, not just the period containing it. A reconstruction must therefore be validated by a hard invariant — the rolled-back constituent count must equal 100 at every date — and must fail closed when it does not.

---

## 10. Identity and ticker-reconciliation risks

**Ticker alone is not safe.** Verified reasons, from the documents retrieved:

1. **No stable identifier in the documents.** The announcement tables and the KAP attachment carry ticker + issuer name only. No ISIN and no CRA/MKK security identifier appeared in any BIST 100 change table examined.<sup>[S4][S10]</sup> The repository configs likewise carry ticker only (`data/config/universe_public_40.csv` columns: `ticker,is_public_universe,is_training_universe,notes`). Joining history to the repository would be a **ticker-to-ticker join with no identifier on either side** — the weakest possible key.
2. **Succession events are visible but unexplained.** The Q4 2020 BIST 100 exclusion list retrieved from KAP contains `ANACM`, `SODA` and `TRKCM` in the same event.<sup>[S10]</sup> Three tickers of one corporate group leaving simultaneously is the signature of a corporate reorganization, but the change table itself gives **no** successor mapping. Whether these were merged into a surviving listed entity — and if so which — was **not verified in this spike** and would require separate first-party issuer/KAP disclosures. Until such a disclosure is read, the successor link must stay `unresolved_ambiguity`, not be inferred.
3. **Renames without ticker change, and ticker changes without rename, are both invisible in a ticker-only stream.** The tables print the issuer name as it stood at the time (e.g. `ADANA CIMENTO (A)`, `ALCATEL LUCENT TELETAS`), so name drift is observable — but only if the name column is captured, which a ticker-only ingestion would discard.
4. **Share classes.** `ADANA CIMENTO (A)` in the Q1 2020 table<sup>[S4]</sup> demonstrates class suffixes appearing in the issuer-name field rather than in the ticker. Class-level membership cannot be assumed from a company-level ticker.
5. **Turkish orthography and transliteration.** The English-language documents transliterate (`CIMSA`, `ISDMR`, `BESIKTAS FUTBOL YAT.`) while Turkish-language originals use `Ç/Ğ/İ/Ö/Ş/Ü`. Matching across the TR and EN attachments of the same disclosure requires a normalization policy, and dotted/dotless `I` casing is a classic silent-corruption source.
6. **Delisted companies leave the current-state sources entirely.** A name that exited before today appears in **no** current constituent list, so it can only ever be recovered from the event stream — precisely the stream with known holes.
7. **Extraction fidelity is itself a risk.** Two concrete instances observed on 2026-08-04: automated summarization of the Q1 2020 page reported "23 total" inclusions while emitting a list interleaving inclusions and exclusions from adjacent table columns; and the KAP attachment PDF renders headings with inter-character spacing (`PE RI O D IC I ND E X CH AN G E S`) that defeats naive text extraction. Both argue for parsing the HTML `<table>` structurally rather than the rendered text, and for human verification of every parsed period.

---

## 11. Repository compatibility assessment

Conceptual only. **Nothing below was implemented, and no repository artifact was changed.**

**Fields that could be matched.** Only `ticker`, from `data/config/universe_public_40.csv` and `data/config/universe_training_bist100.csv` (both `ticker,is_public_universe,is_training_universe,notes`), against the `ticker_at_time` column of a reconstructed record. `scripts/data_collection/pipeline.py`'s `is_bist100` flag is derived from an undated text field and is not a joinable membership key. There is no date-qualified membership field anywhere in the repository to match against.

**Tickers likely to need historical aliases.** Any name whose repository row-coverage is discontinuous is a candidate. `docs/universe_audit.md` records missing committed year-end price observations for `ASTOR` (2020–2022), `CANTE` (2020), `DSTKF` (2020–2024), `MIATK` (2020) and `PASEU` (2020–2023). Those gaps are consistent with late listing — and for `DSTKF` and `KUYAS` the Q3 2025 announcement independently shows a **2025-07-01** BIST 100 inclusion.<sup>[S3]</sup> The audit is explicit that missing price coverage does not by itself prove why an observation is missing, so these are candidates for alias/status work, not conclusions.

**Can the current cohort be interpreted point-in-time?** **No.** The public cohort is a single undated set applied uniformly across 2020–2025, and at least one member is first-party-evidenced as a 2025 index entrant. There is no honest reading under which the existing configuration is a point-in-time universe.

**Would missing historical constituents require new collection?** **Yes, extensively.** A true point-in-time BIST 100 universe contains 100 names per date, with turnover every quarter — the Q1 2020 table alone shows a large simultaneous in/out swap.<sup>[S4]</sup> The repository's public cohort is far smaller than 100 and its training cohort, while larger, is documented as limited to names with validated statements. Reconstructed history would name many companies for which FinanceIQ holds **no** financial-statement or price data at all, and the project's standing rules forbid fabricating or imputing those values. Missing stays null; a null-heavy point-in-time panel is a legitimate outcome and must not be back-filled.

**Would current target/prediction panels shrink or change?** Almost certainly **change**, and plausibly shrink for any given date: names would drop out where evidence shows non-membership at that date, and names would be added for which no features exist and therefore cannot be scored. Both directions alter the evaluated population.

**Correction or successor experiment?** **Successor experiment, unambiguously.** A point-in-time analysis would evaluate a different population under a different construction rule. Silently editing existing artifacts or metrics to reflect it would destroy comparability and would contradict the project's honesty contract. Any such work must land as a new, separately registered experiment alongside — never in place of — the existing retrospective result, following the manual-CSV sidecar pattern already used in `data/trusted_raw/macro/` (e.g. `macro_context_yearly.csv` with its per-value `*_effective_date` and `*_source_id` columns, and the `.md` provenance sidecars beside it).

---

## 12. Legal, access, and operational constraints

**No legal conclusion is offered here.** These are observable facts as of 2026-08-04; licensing and terms interpretation is for the owner and, where warranted, legal review.

- **Public access.** Every first-party document cited in §7 was reached over plain HTTPS with no login, no API key, no payment and no session. No access control, rate limit, paywall or CAPTCHA was encountered or circumvented.
- **Crawler directives.** `borsaistanbul.com/robots.txt` serves `User-agent: *` / `Allow: /`.<sup>[S13]</sup> `kap.org.tr/robots.txt` did **not** serve a robots file; the request returned a KAP error page.<sup>[S14]</sup> A permissive robots file is a crawler directive, not a licence; a missing one is not permission. Both sites publish their own copyright/terms pages, which the owner should read before any bulk retrieval. (An attempt to retrieve the Borsa İstanbul copyright/disclaimer page during this spike failed with an empty server reply, so its text is **not** reported here — this is a `Needs verification` item, see §16.)
- **Site fragility.** Concrete instances observed the same day: the legacy `/en/duyuru/<id>/…` announcement URL form returned an empty reply on repeated attempts; numeric announcement ids without their slug return a not-found page; and one embedded resource on the `xu100` page rendered as "File not found!". First-party URLs on these hosts should be treated as breakable.
- **Automation posture.** Given the fragility above, the paginated filter UI, the PDF attachments, and the two-era extraction problem, a **manual, human-in-the-loop retrieval** — the pattern the repository already uses for macro sidecars — is the appropriate approach, not an automated crawler. This is also the posture the project's own rules require (no scrapers).
- **Stable URLs.** Slugged announcement URLs and numeric KAP disclosure ids appear stable. The rulebook PDF path is **not** version-pinned and its content changes across editions (§9) — the single worst archival risk found.
- **Local archival copies and checksums.** Required, if and only if a later task is authorized. Nothing was archived into this repository by this task.
- **Expected manual reconciliation burden.** For the required window: on the order of **24+ quarterly documents** to retrieve, parse and human-verify; an unknown but non-trivial number of non-periodic disclosures to enumerate and read; an alias/succession table to build by hand from issuer disclosures; plus dual-language reconciliation. Realistically a multi-day effort by someone who reads Turkish, not an afternoon.

---

## 13. Proposed future evidence schema

Design proposal only. **Do not create these files under this task.** Paths are marked *(proposed)*.

Two manual CSV sidecars, following the existing `data/trusted_raw/macro/` convention of a `.csv` plus a `.md` provenance note:

**A. Membership event log** *(proposed)* — one row per index-membership event, columns per §5: `index_name, index_rulebook_version, security_id, ticker_at_time, ticker_current, issuer_name_at_time, announcement_date, effective_from, effective_to, superseded_by_event_id, event_type, source_url, source_document_id, source_title, publication_date, retrieved_at, source_checksum, evidence_confidence, unresolved_ambiguity`.

**B. Identity alias table** *(proposed)* — one row per identity assertion: `security_id, ticker_at_time, valid_from, valid_to, successor_security_id, relation_type (rename | ticker_change | merger | demerger | share_class | delisting), source_url, retrieved_at, evidence_confidence`.

A derived **membership snapshot** view (date → constituent set) would be *computed* from A and B, never hand-maintained, and would refuse to emit a snapshot for any date whose interval carries a non-empty `unresolved_ambiguity` or whose rolled constituent count is not 100.

---

## 14. Proposed source precedence and conflict policy

1. Borsa İstanbul first-party announcement (HTML table) — highest.
2. KAP first-party disclosure by Borsa İstanbul A.Ş., including its attached PDFs — equal authority; used as the independent cross-check.
3. Borsa İstanbul rulebook/methodology of the version in force — authoritative for *mechanics* (what an event means, when it takes effect), never for membership itself.
4. Issuer KAP disclosures — admissible **only** to corroborate an identity or succession event, never to originate a membership claim.
5. Web-archive copies — admissible only as recovery evidence when the first-party document is unreachable, always labelled as archived-not-first-party, with the capture timestamp recorded and reduced `evidence_confidence`.
6. Secondary media — discovery leads only. **Never** written into the event log as a source.

**Conflict policy:** where two same-tier first-party sources disagree, do **not** pick a winner. Record both, mark the interval `CONFLICTING`, and treat membership over that interval as unknown. Where a lower tier contradicts a higher tier, the higher tier stands and the discrepancy is logged. Where a required document cannot be located at all, the affected interval is unknown — **and, because reconstruction rolls backwards from a present-day anchor, every earlier interval is also unknown** until the hole is closed.

---

## 15. Reproducibility and archival requirements

A later authorized implementation would need, at minimum:

- **Source manifest** — every document: URL/id, title, publisher, publication date, retrieval date, byte size, checksum.
- **Immutable local evidence archive** — the retrieved HTML and PDF bytes, stored verbatim, never re-fetched in place. Essential given the un-versioned rulebook path (§9).
- **Checksums** — SHA-256 per archived file, recorded at retrieval and re-verified on every use.
- **Parsing version** — a pinned parser version stamped into every derived row, since the two-era extraction problem (§7.3) guarantees parser changes.
- **Event normalization** — one canonical vocabulary for `event_type`, with substitute activations modelled explicitly rather than dropped.
- **Alias table** — schema B in §13, maintained by hand from first-party succession evidence.
- **Conflict-resolution policy and source precedence** — as §14, encoded, not left to reviewer judgment.
- **Audit log** — append-only: what was retrieved when, what was parsed, what a human corrected and on what evidence.
- **Fail-closed treatment** — unresolved membership emits `null`/unknown and blocks snapshot generation for affected dates. It must never fall back to the current cohort, to a candidate list, or to a "most recent known" set.
- **Tests** — invariants first: constituent count equals 100 at every reconstructed date; no overlapping intervals for one `security_id`; every row carries a resolvable `source_url` and a `retrieved_at`; every checksum matches; no row sourced from a secondary publisher.
- **Artifact-registry ownership** — the outputs registered as owned, versioned evidence under the project's existing provenance/registry conventions, not dropped loose into `data/`.

Recommendation only. Nothing here was implemented.

---

## 16. Unresolved gaps

1. **No free official historical full-constituent snapshot found at any past date.** Reconstruction must roll backwards from a present-day anchor; this is the single biggest structural weakness.
2. **Quarterly announcements for effective periods Q3 2024, Q4 2024 and Q1 2025 were not located.** Existence is likely; retrieval is unproven. `Needs verification`.
3. **The non-periodic/extraordinary change stream was not enumerated.** No free, complete, filterable index of all BIST 100 §7 events for 2020–2025 was found. This alone blocks any `CONFIRMED` classification.
4. **Only four quarterly documents were read end-to-end** (Q1 2020, Q4 2020 via KAP, Q2 2021, Q3 2025). All other periods rest on URL resolution or listing presence, not content.
5. **Succession semantics unverified.** The simultaneous Q4 2020 exclusion of `ANACM`, `SODA`, `TRKCM` has no successor mapping in the source. `Needs verification` from first-party issuer disclosures.
6. **No stable security identifier in any BIST 100 change document examined.** Whether ISIN-level history is obtainable free was not established.
7. **KAP archive depth and its bulk-query surface were not characterized.** A 2020 disclosure was reachable by direct id; whether the detailed-query interface exposes a complete, free, date-ranged listing of all Borsa İstanbul index disclosures back to 2020 was **not** tested.
8. **Web-archive fallback unproven.** The Availability API returned a closest capture dated **2025-10-06** (timestamp `20251006022039`) for the announcements listing when queried at `20200101`; it did not return a 2020-era capture for the timestamp probed. The returned 2025 listing-page capture does not establish historical coverage for the required 2020–2024 window. The CDX endpoint could not be accessed from this environment to enumerate all available captures. This does not establish that no 2020-era captures or relevant archive records exist.
9. **Borsa İstanbul DataStore not characterized.** Scope, pricing and licensing unknown; must not be assumed free, and must not be assumed to contain point-in-time constituent history.
10. **Borsa İstanbul copyright/disclaimer text not retrieved** (empty server reply). Terms review remains outstanding.
11. **Whether the BIST 100 structured effective-date KAP field exists for every year** was not verified; the structured example inspected was a participation-index disclosure.

---

## 17. Recommended next step

**Do not** open a collection task yet. Recommended sequence, each separately authorized:

1. **R3-SPIKE-01a (memo/verification, small):** close gaps 2, 7 and 10 — locate the three missing quarterly announcements via the listing's date filters, characterize KAP's detailed-query surface for Borsa İstanbul index disclosures across 2020–2025, and retrieve the two sites' terms/copyright text. Cheap, and it decides whether the rest is viable.
2. **Owner/legal review** of the terms surfaced in step 1, plus an explicit decision on manual-only retrieval.
3. **R3/R4 collection task (only if 1 and 2 clear):** manual retrieval and archival of the periodic stream and the enumerated non-periodic stream, producing schema A and B (§13) with checksums, an audit log, and the invariant tests in §15 — fail-closed.
4. **Successor experiment (separate again):** a point-in-time-universe analysis registered as a *new* experiment beside the existing retrospective one.

If step 1 cannot close gap 3 (complete non-periodic enumeration), this memo's verdict should be **downgraded** and the dependent frontier ideas gated permanently, with that outcome recorded in `docs/universe_audit.md` by a follow-up documentation task — as the R3-SPIKE-01 packet anticipates.

---

## 18. Claim-safety boundary

Stated explicitly and without qualification:

- **The current FinanceIQ cohort remains retrospective.** `docs/universe_audit.md` stands unchanged and uncontradicted by this memo.
- **This spike does not make any existing FinanceIQ analysis point-in-time valid.** Nothing here retro-validates a single existing number.
- **Source discovery is not completed data collection.** Locating documents is not retrieving, parsing, verifying or archiving them.
- **A future membership reconstruction would require separate authorization, implementation, tests, provenance and independent review.** It is not authorized by this memo.
- **Historical membership evidence establishes nothing about predictive edge, alpha, profitability, investment value, tradability, or future performance.** Fixing a universe-construction bias changes what is measured; it does not create a signal. The project's walk-forward finding of no reliable predictive edge is untouched by this memo.
- **No current generated artifact, dataset, model, experiment result or reported metric is changed by this memo.** The only file this task writes is this document.
- Nothing in this memo is investment advice.

---

## 19. Sources and access dates

All accessed **2026-08-04**. Tags match the `[Sn]` references above.

**First-party — Borsa İstanbul A.Ş.**

- **[S1]** Index Announcements — https://www.borsaistanbul.com/en/indices/index-announcements
- **[S4]** *Borsa İstanbul announces the constituent changes to the BIST Stock Indices for the first quarter of 2020* — https://www.borsaistanbul.com/en/announcement/13577/borsa-istanbul-announces-constituent-changes-bist-stock-indices-first-quarter-2020 (page-dated 12/17/2019; effective 2020-01-01 → 2020-03-31)
- **[S5]** *… second quarter of 2021* — https://www.borsaistanbul.com/en/announcement/14147/borsa-istanbul-announces-constituent-changes-bist-stock-indices-second-quarter-2021 (published 2021-03-15; effective 2021-04-01 → 2021-06-30)
- **[S3]** *… third quarter of 2025* — https://www.borsaistanbul.com/en/announcement/15121/borsa-istanbul-announces-constituent-changes-bist-stock-indices-third-quarter-2025 (published 2025-06-20; effective 2025-07-01 → 2025-09-30)
- **[S2]** Additional quarterly announcements resolved but **not read** in this spike: ids 13353 (2020 Q2), 14106 (2020 Q3), 14118 (2020 Q4); and listed but not fetched: 14132, 12664, 14213, 12771, 14347, 14401, 12960, 14476, 14516, 14545, 13125, 14627, 14654 — all under `https://www.borsaistanbul.com/en/announcement/<id>/borsa-istanbul-announces-constituent-changes-bist-stock-indices-<quarter>-<year>`
- **[S6]** *BIST Stock Indices Ground Rules*, April 2020 edition — https://www.borsaistanbul.com/files/bist-stock-indices-ground-rules.pdf (585 885 bytes; SHA-256 `892a37c4c74a1721eb815781fbb35a190d14124d5c7c1c9f6affed7ba96d0c3d` as retrieved; §2.14, §2.15, §7, §8.2 cited). **URL is not version-pinned.**
- **[S7]** *BIST Market Cap Weighted Stock Indices Methodology* (2026-01 draft) — https://borsaistanbul.com/files/bist-mcw-equity-indices-m-eng-2026-01-draft.pdf — retrieved as PDF; text not extracted in this spike. Draft; **do not cite as the rule in force**.
- **[S12]** BIST 100 index page — https://www.borsaistanbul.com/en/index/xu100 (current state only)
- **[S13]** https://www.borsaistanbul.com/robots.txt — served `User-agent: *` / `Allow: /`
- **[S15]** Borsa İstanbul DataStore — https://datastore.borsaistanbul.com/ — responded with a JavaScript application shell; scope/pricing/licensing **not established**

**First-party — KAP (Public Disclosure Platform, MKK)**

- **[S8]** Disclosure 875734, BORSA İSTANBUL A.Ş., "Endeks Şirketlerinde Değişiklik" — https://www.kap.org.tr/tr/Bildirim/875734 (submitted 2020-09-18 18:22:50; period 2020-10-01 → 2020-12-31; attachments `2020_4_dönemsel_değişiklikler.pdf`, `2020_4_periodic_changes.pdf`)
- **[S10]** Attachment (English) — https://www.kap.org.tr/tr/api/file/download/4028328d745d13ff0174a1cbcc893a35 (171 116 bytes; SHA-256 `6938f6c80087d3b91b8e82f830403b735052443a5f3d6e586a926e38cd291310` as retrieved)
- **[S9]** Disclosure 1302173, BORSA İSTANBUL A.Ş. — https://www.kap.org.tr/tr/Bildirim/1302173 (submitted 2024-06-26 18:13:11; structured `Geçerlilik Tarihi / Efective Date` column observed)
- **[S11]** Current index constituents — https://www.kap.org.tr/tr/Endeksler (current state only)
- **[S14]** https://www.kap.org.tr/robots.txt — no robots file served; the request returned a KAP error page

**Recovery evidence (not first-party)**

- **[S16]** Internet Archive availability API — http://archive.org/wayback/available — returned a closest capture dated **2025-10-06** (timestamp `20251006022039`) for the Borsa İstanbul announcements listing when queried at the 2020 timestamp; it did not return a 2020-era capture for that timestamp probe. The returned 2025 listing-page capture does not establish historical coverage for the required 2020–2024 window. The CDX endpoint could not be accessed from this environment to enumerate all available captures, so web-archive fallback for the required historical window remains unproven. This does not establish that no 2020-era captures or relevant archive records exist.

**Secondary — discovery leads only, never cited as membership evidence**

- **[S17]** Bloomberg HT, Ekonomist, Midas, haber.doviz.com and Mondovisione index-change reports surfaced in search were used solely to locate candidate first-party announcement titles and quarters. No membership fact in this memo rests on them, and no search-result snippet is cited as evidence.

**Repository sources**

- `docs/universe_audit.md` (audit date 2026-07-12)
- `data/config/universe_public_40.csv`, `data/config/universe_training_bist100.csv`, `data/config/bist100_candidates.csv`
- `scripts/data_collection/pipeline.py`
- `data/trusted_raw/macro/macro_context_yearly.csv` and its sidecar convention
- `FINANCEIQ_PHASE3_4_FRONTIER_PLAN.md` §C-18
