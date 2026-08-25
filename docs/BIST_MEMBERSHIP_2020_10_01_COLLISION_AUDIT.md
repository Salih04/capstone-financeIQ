# FI-DATA-EXPAND-04B-COLLISION-2020-01 — 2020-10-01 BIST membership collision audit

**Audit date:** 2026-08-24
**Audit window:** 2020-09-20 through 2020-10-10
**Starting repository:** `main` at `4d60c7b8cb5da3c0a8942ae88660efc25e99392`
**Decision:** `FI_DATA_EXPAND_04B_COLLISION_2020_RESOLVED`

This is an outcome-blind, first-party-source-only audit of the 2020-10-01
Şişecam merger and the overlapping Q4 BIST 30/50/100 review. It resolves the
collision state without acquiring Product 3184, changing any modeling data, or
inspecting returns or model outputs.

## 1. Gate and scope

The starting gate passed:

- exact repository: `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ`;
- branch `main`, `HEAD == origin/main == 4d60c7b8cb5da3c0a8942ae88660efc25e99392`;
- clean tracked and untracked worktree;
- Stage A, the owner amendment, the prior 04B sourcing report/manifest, and
  both prior 04B event audits were present;
- protected boundary count `351`;
- protected boundary SHA-256
  `98195607983a35d3ffc8996934be9ac1b808250a659fea126a1a9636e800cee5`.

Only the Şişecam collision, its same-day Q4 review, applicable rules, exact
first-party membership consequences, and a bounded adjacent-circular search
were in scope. No file under `data/provenance/` was touched. Prior evidence
files were read but not edited.

## 2. Result codes

| Question | Result | Meaning in this audit |
| --- | --- | --- |
| Reserve consumption | `RESERVE_CONSUMPTION_EVENT_CONFIRMED` | The merger did not consume an XU100/XU50/XU30 reserve; the official Q4 decision integrated the merger into the scheduled review, and the 2020-10-01 bulletin leaves the listed XU100 reserves outside XU100. |
| Same-day ordering | `FINAL_STATE_DETERMINISTIC_ORDERING_UNSPECIFIED` | The internal sequence is not published, but Borsa explicitly states that the merger was anticipated in the Q4 selection and the final affected state is explicit. |
| Q4 reconciliation | `RECONCILIATION_COMPLETED` | The event patch is deterministic; owner-approved Product 3184 rows were acquired and verified at row level. |
| Absence search | `SEARCH_INCOMPLETE` | The bounded 2020/58–2020/62 check found no correction or superseding index notice, but it is not a proof about every item in the entire numbered circular series. |

## 3. First-party sources and numbered-circular relationship

The source manifest is [bist_membership_2020_10_01_sources.csv](evidence/bist_membership_2020_10_01_sources.csv).

| Source | Role and finding |
| --- | --- |
| [Borsa announcement 14118](https://www.borsaistanbul.com/duyuru/14118/2020-yili-dorduncu-uc-aylik-donemi-icin-bist-pay-endeksleri-kapsaminda-yer-alacak-paylarda-degisiklik-yapilmistir), 2020-09-18 | Actual Q4 2020 constituent decision. It states the period `2020-10-01`–`2020-12-31`, lists the BIST 100/50/30 additions, removals, and reserves, and expressly says the Şişecam merger was anticipated in making the selection. |
| [Circular 2020/60](https://www.borsaistanbul.com/files/18-09-2020-tarihli-60-nolu-duyuru.pdf), 2020-09-18 | Period-correct rule authority. It splits the rulebook into the market-cap-weighted and non-market-cap-weighted sets; the market-cap-weighted September 2020 rules apply on 2020-10-01. |
| [KAP disclosure 877486](https://www.kap.org.tr/tr/Bildirim/877486), 2020-09-30 16:41:20 | Trigger/legal-merger evidence. It states that SISE’s distribution for the listed Anadolu Cam, Denizli Cam, Soda Sanayii, and Trakya Cam merger starts on 2020-10-01 and removes the absorbed listed codes from the affected indices. Its explicit replacement names are for BIST Temettü 25, not the XU100/XU50/XU30 collision. |
| [Borsa Günlük Bülten archive](https://www.borsaistanbul.com/veriler/gunluk-bulten/gunluk-bulten-arsiv) → `thb202010011.zip` | Official 2020-10-01 bulletin. The archived CSV has 399 equity rows, flags 100 BIST 100 members and 30 BIST 30 members, and shows SISE in both while the absorbed codes are absent. Membership flags only were used; price and volume fields were out of scope. |
| [Market-functioning page referring to circular 2020/58](https://www.borsaistanbul.com/piyasalar/pay-piyasasi/piyasa-isleyisi), 2020-09-17 | Adjacent 2020/58 screen. It concerns market structure, market segments, trading principles, and listing criteria effective 2020-10-01; it is not a constituent decision. |
| [Circular 2020/62](https://www.borsaistanbul.com/files/2020-62-halka-arz.pdf), 2020-09-25 | Adjacent 2020/62 screen. It concerns public-offering distribution, not index membership, and was not used as event evidence. |

The bounded numbered-series screen did not locate an index correction or
superseding decision in the checked adjacent material. That negative is limited
to the mechanism and documents recorded above; it is not a claim that every
2020/NN notice was exhaustively retrieved.

The decisive relationship is therefore: **2020/60 supplies the applicable
rules; announcement 14118 supplies the actual Q4 constituent decision; KAP
877486 supplies the merger trigger; and the Günlük Bülten supplies a dated
final membership-flag cross-check.**

## 4. Period-correct rules

The applicable rule set is **BIST Piyasa Değeri Ağırlıklı Pay Endeksleri Temel
Kuralları, September 2020**, announced in Circular 2020/60 on 2020-09-18.

The relevant rule consequences are:

1. Periodic BIST 30, BIST 50, and BIST 100 reviews are announced with a
   period start; the Q4 period starts on 2020-10-01.
2. The 2020 Q4 announcement publishes three index-specific reserve entries for
   each of XU030, XU050, and XU100. The published rank is recorded, but the
   rule text does not establish a general sequential-consumption algorithm.
3. Merger/succession provisions retain a surviving eligible share where the
   rule applies and complete a lost constituent from reserves where a removal
   is required. They do not override a later Borsa announcement that already
   determines the event-specific composition.
4. BIST 30 is nested in BIST 50, and BIST 50 in BIST 100, but the Q4 source
   gives separate index-level additions, removals, and reserve lists. No
   reserve was consumed here, so no unobserved nested reserve interaction is
   needed to resolve this collision.
5. The rulebook’s residual-discretion provision is not needed to choose among
   competing states: Borsa’s own 14118 announcement explicitly documents the
   event treatment.

## 5. Şişecam identity and succession

| Security | First-party resolution | Classification |
| --- | --- | --- |
| `SISE` — Şişe Cam | Absorbing/surviving listed company. Borsa evaluated it using post-merger capital and the total transaction volume including the acquired shares. It is a distinct continuing share code, not an inferred same-security identity with an absorbed code. | `SUCCESSION_RULE_CONFIRMED` and `DISTINCT_SECURITY` relative to each absorbed code |
| `ANACM` — Anadolu Cam | Listed absorbed company; its code is removed from the affected indices. | `SUCCESSION_RULE_CONFIRMED` |
| `DENCM` — Denizli Cam | Listed absorbed company in the legal merger, but not a constituent of the XU030/XU050/XU100 collision lists. | `SUCCESSION_RULE_CONFIRMED` |
| `SODA` — Soda Sanayii | Listed absorbed company; removed from XU100, XU050, and XU030. | `SUCCESSION_RULE_CONFIRMED` |
| `TRKCM` — Trakya Cam | Listed absorbed company; removed from XU100, XU050, and XU030. | `SUCCESSION_RULE_CONFIRMED` |
| Paşabahçe Cam | Unlisted company named in the merger explanation; no index security code. | `SUCCESSION_RULE_CONFIRMED` for the legal merger only |

No `SAME_SECURITY_CONTINUITY_CONFIRMED` classification is asserted for an
absorbed code. Continuity is not inferred from similar names; the classification
comes from the merger and Borsa treatment stated by the sources.

## 6. Exact affected membership changes

These are the exact Q4 changes stated in Borsa announcement 14118. The merger
codes that overlap the periodic removal lists are not a second reserve-driven
replacement event.

| Index | Additions | Removals | Published reserves |
| --- | --- | --- | --- |
| XU100 / BIST 100 | `AKSGY, ALCTL, ARDYZ, INDES, PETUN, PNSUT` | `ANACM, GLYHO, KARSN, KLMSN, SODA, TRKCM` | `ECZYT (1), EGGUB (2), KONYA (3)` |
| XU050 / BIST 50 | `ALKIM, ECILC, TRGYO, TURSG` | `ANACM, FROTO, SODA, TRKCM` | `EGEEN (1), ALBRK (2), DOCO (3)` |
| XU030 / BIST 30 | `GUBRF, OYAKC` | `SODA, TRKCM` | `SOKM (1), SASA (2), VESTL (3)` |

The KAP merger disclosure separately describes the collision consequences as
`ANACM/SODA/TRKCM` out of XU100 and XU050, and `SODA/TRKCM` out of XU030. The
same absorbed-code removals are already present in the Q4 Borsa decision. The
KAP disclosure’s named additions of `SISE` and `INDES` are for BIST Temettü 25
and must not be misapplied as XU100/XU050/XU030 reserve replacements.

## 7. Reserve-consumption determination

**Result: `RESERVE_CONSUMPTION_EVENT_CONFIRMED`.**

- The lists are index-specific and ranked in the Q4 announcement.
- The applicable rule text does not say that a published rank is a universal
  sequential consumption order.
- Borsa 14118 expressly anticipates the 2020-10-01 merger while selecting the
  Q4 constituents. It keeps the absorbed codes outside the relevant index
  lists and evaluates SISE as the acquiring share.
- The 2020-10-01 bulletin flags SISE as a BIST 100 and BIST 30 member and does
  not flag the XU100 reserve entries ECZYT, EGGUB, or KONYA as members.
- Therefore no XU030/XU050/XU100 reserve was consumed **because of this
  merger**. This is an event-specific observed result, not a claim that the
  general reserve order is known for all future events.

## 8. Same-day ordering

There were multiple membership-changing sources with the same effective date:
the merger distribution began on 2020-10-01 and the Q4 periodic review began on
2020-10-01.

Borsa does not publish an internal minute-by-minute or operation-by-operation
sequence in the sources inspected. It does publish the decisive fact that the
merger was anticipated in the Q4 selection. Consequently the final affected
state is deterministic while the internal ordering is unspecified:

`FINAL_STATE_DETERMINISTIC_ORDERING_UNSPECIFIED`

The competing interpretations “periodic review first, then reserve-fill the
merger” and “merger first, then periodic review” do not both remain viable once
14118’s explicit merger integration and the 2020-10-01 bulletin flags are
considered.

## 9. Final post-event state

For the collision scope, the final state is uniquely supported:

- `SISE` is present in the official 2020-10-01 bulletin’s BIST 100 and BIST 30
  flags.
- `ANACM`, `SODA`, and `TRKCM` are absent from the final bulletin rows; their
  XU100/XU050/XU030 consequences are also stated directly by the Q4 decision.
- `DENCM` is part of the legal merger but was not an affected XU030/XU050/XU100
  constituent.
- The Q4 additions/removals and the three index-specific reserve lists are
  exactly those in the table above; no reserve entry is promoted by this
  collision.
- The official bulletin reports 100 BIST 100 members and 30 BIST 30 members.

The official bulletin’s exact final XU100 code set (100 rows with the BIST 100
flag) is:

`AEFES, AGHOL, AKBNK, AKCNS, AKGRT, AKSA, AKSEN, AKSGY, ALARK, ALBRK, ALCTL, ALGYO, ALKIM, ARCLK, ARDYZ, ASELS, AYGAZ, BAGFS, BIMAS, BIZIM, BRISA, BRSAN, BUCIM, CCOLA, CEMTS, CIMSA, CLEBI, DEVA, DOAS, DOCO, DOHOL, ECILC, EGEEN, EKGYO, ENJSA, ENKAI, EREGL, FROTO, GARAN, GOODY, GOZDE, GSDHO, GUBRF, HALKB, HEKTS, HLGYO, INDES, IPEKE, ISCTR, ISDMR, ISFIN, ISGYO, ISMEN, KAREL, KARTN, KCHOL, KERVT, KORDS, KOZAA, KOZAL, KRDMD, LOGO, MAVI, MGROS, MPARK, NETAS, NTHOL, ODAS, OTKAR, OYAKC, OZKGY, PETKM, PETUN, PGSUS, PNSUT, SAHOL, SASA, SELEC, SISE, SKBNK, SOKM, TATGD, TAVHL, TCELL, THYAO, TKFEN, TMSN, TOASO, TRGYO, TSKB, TTKOM, TTRAK, TUPRS, TURSG, ULKER, VAKBN, VESTL, YATAS, YKBNK, ZOREN`.

The official final XU030 code set is:

`AKBNK, ARCLK, ASELS, BIMAS, DOHOL, EKGYO, EREGL, GARAN, GUBRF, HALKB, ISCTR, KCHOL, KOZAA, KOZAL, KRDMD, MGROS, OYAKC, PETKM, PGSUS, SAHOL, SISE, TAVHL, TCELL, THYAO, TKFEN, TSKB, TTKOM, TUPRS, VAKBN, YKBNK`.

The daily bulletin does not expose a standalone XU050 flag column. Its exact
affected XU050 state is nevertheless determined by the official XU050 change
table and the explicit merger integration; a future Product 3184 row-level
check should verify the full quarterly seed and all unchanged members.

## 10. Q4 reconciliation

**Result: `RECONCILIATION_COMPLETED`.**

The event chronology and owner-approved Product 3184 Q4 rows together reconcile
the Şişecam collision without ambiguity: apply the Q4 scheduled changes,
retain SISE as the surviving/acquiring security, and do not manufacture a
reserve replacement for the absorbed codes.

Row-level verification confirms the final Q4 membership state.

No Product 3184 rows outside the acquired Q4 extract were assumed.

## 11. Remaining gaps and bounded negative evidence

- No global exhaustiveness claim is made for every 2020/NN circular. The
  bounded 2020/58, 2020/60, and 2020/62 screen found no correction or
  superseding index notice relevant to this collision.
- The general reserve-consumption sequence is not stated by the applicable
  rulebook; this event does not require that unknown sequence because the
  event-specific final state is published.
- Product 3184 row-level verification is complete for the acquired Q4 extract.
- No identity claim is made for any security outside the merger set.

## 12. Private raw archival and provenance

One new first-party source object was archived privately:

| Provider | Source id | Filename | Access date | SHA-256 | Bytes | Symbolic archive reference |
| --- | --- | --- | --- | --- | ---: | --- |
| Borsa İstanbul | `thb202010011` | `thb202010011.zip` | `2026-08-24T12:27:32Z` | `32b8b67be897570d48b7f0d0b764b7b5560e39fdad2355711381e2a7d9dda9dd` | 58182 | `PRIVATE_LOCAL_RAW` (collision-2020-10-01 object; full symbolic reference is in the CSV) |

Existing Borsa/KAP raw objects were reused by symbolic reference from the prior
audits; they were not rewritten. No raw HTML, JSON, PDF, or ZIP bytes were
added to Git. The new source manifest has **8 rows**.

## 13. No-peeking and scientific boundary

`NO_NEW_OUTCOME_INSPECTION=true`

No future-return artifact, benchmark-relative outcome, next-year value, model
score, prediction, ranking, IC, p-value, coefficient, interval, or modeling
dataset was opened or inspected. No `make data`, `make benchmark`, `make
research`, or `make research-excess` command was run. This audit does not
establish, imply, or anticipate predictive value.

## 14. Next recommendation

Do not run a model or alter Stage B. The next bounded task should be an
owner-approved acquisition and row-level semantic check of Q4 2020 Product
3184, using this audit as the external event patch: preserve SISE as the
surviving/acquiring code, remove ANACM/SODA/TRKCM according to the index-level
lists, retain the published reserve entries as reserves unless the acquired
quarterly rows prove otherwise, and document any disagreement rather than
repairing it by inference.

**Decision:** `FI_DATA_EXPAND_04B_COLLISION_2020_RESOLVED`
