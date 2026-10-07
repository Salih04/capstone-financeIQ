# PIT Kernel görevleri

Tarih: 2026-10-07 · Repo: `financeiq-pit-kernel` · FinanceIQ görevleri ayrı dosyada:
[`TASKS_FINANCEIQ_2026-10-07.md`](TASKS_FINANCEIQ_2026-10-07.md)

Bu dosya kernel'in bütün işlerini, tek tek başlatılabilecek kartlar halinde tutar. **Bilerek hiçbir
sonuç sayısı içermez**; kernel oturumlarında güvenle kullanılabilir. Prompt'lar İngilizce.

**Nasıl kullanılır**
- Ajan kartı: önce §3 kernel preamble'ı, sonra kartın prompt'u. Kernel oturumuna başka bir şey
  (FinanceIQ plan dosyası, sonuç dosyaları, FinanceIQ görev dosyası) verme.
- `KO-` kartları senin işin.

**Kernel'in yeni görevi (2026-10-07).** FinanceIQ'nun araştırma evreni artık sabit bir kohort değil:
çeyreklik BIST 100 üyeliğine göre kurala bağlı, hayatta kalanları ve endeksten çıkanları içeren bir
evren. Kernel bu evrenin **kanıtını** tutar: üyelik aralıkları, kimlikler, KAP bildirim zamanları,
tablo değerleri, fiyat barları, şirket eylemleri, makro seriler. Evren kuralına kernel karar vermez.
Kernel, FinanceIQ'nun kohort listelerinden (`data/config/*`) varlık **türetmez**; bu listelerin seçim
kuralı belgelenmemiş. Varlık listesi üyelik kanıtından gelir.

**Kernel v1 "bitti" tanımı.** Pencere boyunca şunlar as-of sorgulanabilir: üyelik aralıkları,
kimlikler, KAP bildirim zamanları, tablo değerleri, günlük fiyatlar, şirket eylemleri, makro seriler.
Her biri için kapsam raporu var, CI yeşil ve FinanceIQ'ya dosya tabanlı export çalışıyor.

---

## 1. Durum

| Konu | Durum |
|---|---|
| Remote | **Yok.** Tek kopya iCloud senkronlu Desktop'ta → KO-1 |
| Devam eden iş | `rights.py`, `postgres.py`, `source_rights.schema.json` ve fixture'da commit'lenmemiş değişiklikler var (2026-10-07). Başka bir oturumun işi; diğer kartlar bundan sonra → KER-00 |
| Bilinen hata | `select_fact()` yalnız entity ve field'a göre filtreliyor; TRY ve USD olguları yalnız tazeliğe göre yarışabiliyor → KER-01 |
| Üyelik kanıtı | FinanceIQ tarafında ön çalışma var: 2013–2026 Borsa İstanbul endeks duyuru arşivi, dönemsel değişiklik tabloları, KAP tetikleyici denetimi. Günlük üyelik 2017–2023 için kurulamıyor (dönem içi değişiklikler yayımlanmamış); çeyreklik üyelik açık tarihlerle yayımlanmış. Çeyreklik tam liste DataStore Product 3184'te: ücretsiz, ama hesap kaydı ve sözleşme onayı istiyor → KO-5 |

---

## 2. Başlatma sırası

Migration ekleyen kartlar (KER-01, 02, 03, 07, 08, 09) **sırayla** koşar. Migration'lar numaralı ve
append-only; paralel branch'ler aynı numarayı alıp çakışır.

| Dalga | Paralel başlatılabilir | Ön koşul |
|---|---|---|
| 1 | KO-1, KO-2, KO-3, KO-5 · KER-00 · KER-11 | — |
| 2 | KER-01 → KER-02 → KER-03 · KER-04 · KER-05 · KER-06 → KO-4 | KER-00 bitti; KER-04 için KO-1 |
| 3 | KER-07 → KER-08 → KER-09 · KER-12 · KER-15 | KER-07 için KER-03; KER-12 için KO-2; KER-15 için KER-01 |
| 4 | KER-10 → KER-13a, KER-13c, KER-13d, KER-13e → KER-13b → KER-13f | KER-10 için KER-09 ve KO-4; KER-13 için KO-4 ve KER-12; KER-13d için KO-3; KER-13e için KO-5 |
| 5 | KER-14 | KER-13a/b/c/e |

---

## 3. Kernel preamble (kör oturum)

```text
You are a coding agent working in the financeiq-pit-kernel repository
(/Users/salihcamci/Desktop/Projects/First_Priority_Projects/financeiq-pit-kernel).
Read AGENTS.md, README.md, docs/governance/SCOPE_AND_GATES.md and docs/architecture/*.md first.

The Kernel is an outcome-blind, bitemporal store of point-in-time evidence for research on Borsa
Istanbul equities: index membership, identities, KAP filings and statement values, prices,
corporate actions and macro series. Downstream research defines its universe from quarterly
BIST 100 membership; the Kernel stores the evidence and never decides the universe. Never seed
entities, coverage lists or universes from the FinanceIQ repository's cohort or universe lists
(data/config/*); entities come from membership evidence and source documents.

NO_NEW_OUTCOME_INSPECTION=true is binding. Do not open, search or summarize files of the main
FinanceIQ repository except paths this task names explicitly, and never anything containing
returns, rankings, IC values, model results or experiment outputs. No recursive searches outside
this repository. If an outcome figure appears, stop, do not use it, and append an entry to
docs/governance/INCIDENT_EVENTS.jsonl. You may store and integrity-check raw prices when a task
says so, but never compute or inspect returns.

No real data acquisition, external account use or scraping unless the task says so AND an
owner-approved rights decision exists for that exact source and operation. Never script requests
against Borsa Istanbul DataStore (manual download by the owner only). Licensed raw bytes never
enter git; they live in the PRIVATE_LOCAL_RAW vault outside the repository.

Migrations are append-only: add a new numbered file, never edit an applied one. A change to
temporal meaning or canonical hash bytes requires a new contract major version.

Git: start from a clean main; create a new branch; small commits; never rewrite history.
Verify: python3 -m unittest discover -s tests -v, plus the same with PIT_TEST_DSN pointing at a
disposable PostgreSQL 16+ database for the persistence tests.

Final report: 1) what changed, 2) verification commands and honest results,
3) not done / needs verification.
```

---

## 4. Sahip kartları (SEN)

| ID | İş | Neden | Bitti ölçütü | Dalga |
|---|---|---|---|---|
| KO-1 | Kernel için **özel** bir GitHub repo'su aç; devam eden iş (KER-00) commit'lendikten sonra push et | Remote yok; tek kopya | `git remote -v` bir remote gösteriyor; `main` push edilmiş | 1 |
| KO-2 | Vault kararı: şifreli APFS disk imajı ya da harici disk, artı ikinci kopya. Taşınacaklar: `~/FinanceIQ_backups/2026-10-07/` (SC5 KAP önbelleği), FinanceIQ'nun üyelik ham arşivi (`PRIVATE_LOCAL_RAW:bist-membership/`), ileride gelecek DataStore dosyaları | Ham veri iCloud'da ve tek diskte | Vault yolu belli; SHA-256 manifesti vault'ta doğrulanıyor | 1 |
| KO-3 | EVDS API anahtarı al (ücretsiz kayıt). Anahtarı yalnız env'de ya da Keychain'de tut | KER-13d için gerekli | Anahtar alındı; git'te yok | 1 |
| KO-4 | KER-06'daki rights karar taslaklarını onayla ya da düzelt | Gerçek veri ingest'inin kapısı | Her karar `APPROVED` ya da gerekçeli `DENIED` | 2 |
| KO-5 | **DataStore kararı.** Borsa İstanbul DataStore'da hesap aç, kayıt sözleşmesini oku. Sözleşme iç araştırma kullanımına izin veriyorsa kabul et ve Product 3184'ü ("Since 2000, companies in BIST 30/50/100") pencere boyunca bütün yıllar için **elle** indir; dosyaları vault'a koy. İzin vermiyorsa yazılı gerekçeyle reddet | Çeyreklik tam üyelik listesinin tek birinci taraf kaynağı. Dosyalar ücretsiz; engel yalnız kayıt ve sözleşme. Script'li istek WAF'a takılıp oturumu kapatıyor | Karar notu (sözleşme sürümü, tarih, ilgili madde); kabul edildiyse dosyalar vault'ta, manifest satırlarıyla. İndirilecek liste: KER-11 | 1 |

---

## 5. Ajan kartları

### 5.1 Çekirdek semantik

#### KER-00 · Devam eden rights işini bitir ve commit'le
Dalga 1 · Bu iş başka bir oturumda sürüyor

Bitti ölçütü: `git status` temiz; testler yeşil. Diğer KER kartları bundan sonra başlar.

#### KER-01 · Olgu boyut anahtarı + contract 2.0.0
Dalga 2 · Ön koşul: KER-00

```text
Task KER-01. Problem: select_fact() in src/financeiq_pit/temporal.py filters only by entity_id
and field, while snapshot_envelope() treats (entity, security, field, unit, currency) as the
dimension, and docs/architecture/STORAGE_DESIGN.md says units belong in the dimension key.
A fact for the same field in TRY and in USD can therefore be selected by recency alone.
1) Define one canonical dimension key used by both functions: entity_id, security_id,
   field, period_type, period_basis, currency, unit, scale, consolidation, accounting_basis.
   Add the new fields to schemas/structured_fact.schema.json (required, with an explicit
   NOT_APPLICABLE value where a field does not apply) and to a new migration.
2) select_fact takes the full key; candidates differing in any key field never compete.
   Add tests: TRY vs USD, consolidated vs solo, thousand vs unit scale.
3) Bump the exchange contract to 2.0.0 (request carries the full key; new hash-algorithm
   identifier if canonical bytes change). Keep the 1.0.0 fixtures as historical, add 2.0.0
   fixtures, update docs/architecture/INTEGRATION_CONTRACT.md, TEMPORAL_SEMANTICS.md and
   MIGRATIONS.md.
```

#### KER-02 · Muhasebe temeli ve UMS 29 semantiği
Dalga 2 · Ön koşul: KER-01

```text
Task KER-02. Under IAS 29 (hyperinflation), a prior-year figure is republished in a later report
restated in the measuring unit current at the later balance-sheet date. That is a change of
measurement basis, not an error correction. Model it with accounting_basis values such as
TFRS_HISTORICAL and IAS29_RESTATED, plus a measuring_unit_date. A restated comparative is a
new fact with its own basis; it must never supersede the originally published value. Tests:
for one synthetic entity and period, the original value and the restated comparative are both
selectable at an as_of after both publications, each by its own basis; an as_of before the
restated report sees only the original. Document the rule in TEMPORAL_SEMANTICS.md.
```

#### KER-03 · Dönem semantiği: birikimli ve dönemsel
Dalga 2 · Ön koşul: KER-02

```text
Task KER-03. Turkish interim income statements are published cumulative year-to-date (3M, 6M,
9M, 12M). Add period_type (FY, Q1–Q4, H1, M9 …) and period_basis (CUMULATIVE, DISCRETE).
Published values keep their published basis. A discrete quarter is a derivative (e.g. Q4 =
12M − 9M), recorded in the derivatives relation with lineage to both inputs, and available only
once both inputs are public (known_at_upper = max of inputs). If an input is restated, the
derivative is recomputed as a new version; the old one stays. Tests for availability timing,
restatement and a missing input (no derivative; never imputed).
```

#### KER-04 · CI + PostgreSQL + Python 3.12
Dalga 2 · Ön koşul: KO-1 (remote)

```text
Task KER-04. Add .github/workflows/verify.yml: Python 3.12, `pip install -e .[postgres]`, a
postgres:16 service container, PIT_TEST_DSN pointing at it, and
`python3 -m unittest discover -s tests -v`. All tests must run in CI (none skipped for a
missing DSN). Set requires-python to ">=3.12" in pyproject.toml and say so in README.md.
Add a secret-scan step that fails on committed keys or .env files. Add a check that fails if
two migration files share a number or if a file name contains " 2" (iCloud duplicate copies).
```

#### KER-05 · Sonuç körlüğünü makineyle zorla
Dalga 2

```text
Task KER-05. Turn NO_NEW_OUTCOME_INSPECTION into tests. 1) A schema/test denylist: no field name
in schemas or fixtures may match outcome patterns (return, ret_, excess, alpha, ic, rank,
target, label, prediction, pnl, performance). Allowlist exceptions explicitly in the test with
a reason. 2) A test that the package imports nothing from the main FinanceIQ repository and has
no code path that writes outside its own database or the configured vault. 3) A test that no
code or fixture reads a path matching the FinanceIQ universe lists (data/config/universe_*,
bist100_candidates). 4) Document all three in docs/governance/SCOPE_AND_GATES.md.
```

#### KER-06 · Kaynak hakları karar taslakları
Dalga 2 · Ön koşul: KER-00 · Çıktıyı KO-4 onaylar

```text
Task KER-06. Draft one rights-decision record per source using the current
schemas/source_rights.schema.json, all with status DRAFT_PENDING_OWNER (they grant nothing until
the owner approves). Policy basis for each: the owner's internal decision
FI-SOURCE-OWNER-AMENDMENT-01 — publicly disclosed, non-confidential financial facts may be
collected, transformed and retained in a private research archive; it does NOT cover public
redistribution of raw third-party data, publication of raw vendor files, credential sharing,
bypassing authentication, CAPTCHAs or rate limits, or using another person's entitlement. It
is not a third-party licence and not legal advice.
Sources and proposed capabilities:
- KAP public disclosures: automated access ALLOWED_WITH_CONDITIONS (3–8 s between requests;
  an empty response body is SEARCH_INCOMPLETE, never zero results; back off on 429); raw
  retention in vault; derived facts INTERNAL research; redistribution PROHIBITED.
- Borsa Istanbul public index announcements (website archive and attached PDFs): retrieval of
  individual public documents; raw retention in vault; redistribution PROHIBITED.
- Borsa Istanbul DataStore, Product 3184 and any later product: MANUAL_ONLY download by the
  owner under the owner's own account and registration agreement (automated requests are
  blocked by its WAF and log the owner out); conditions per the agreement the owner accepted
  (KO-5); raw retention in vault; redistribution PROHIBITED.
- TCMB EVDS: API with the owner's personal key (never committed); conditions per EVDS terms
  (owner to confirm); redistribution of raw series PROHIBITED unless terms allow.
- Yahoo chart endpoint: internal research only; raw retention in vault; redistribution
  PROHIBITED; status UNKNOWN on any operation the owner's terms review does not cover.
- Fintables exports: MANUAL_ONLY download under the owner's own subscription; raw retention in
  vault; redistribution PROHIBITED.
Put the drafts in a new directory and add a test that DRAFT records deny every operation.
```

### 5.2 Yeni veri aileleri

#### KER-07 · Şirket eylemleri, fiyat barları, işlem takvimi
Dalga 3 · Ön koşul: KER-03

```text
Task KER-07. Add append-only relations in new migrations: pit_corporate_actions (type: cash
dividend, bonus issue, rights issue, split, reverse split, merger; ratio/amount; ex-date,
record date, known_at bounds, source document), pit_price_bars (raw OHLCV per listing and
session, source hash; no adjusted prices stored as source data) and pit_trading_calendar
(venue, session date, open/closed, known_at). Adjusted prices and adjustment factors exist only
as derivatives computed from raw bars plus corporate actions, with lineage. Synthetic tests:
bonus issue, rights issue (theoretical ex-rights price), cash dividend, a holiday, and a
corporate action announced after its ex-date (late knowledge). Never compute returns.
```

#### KER-08 · Makro seri vintajları
Dalga 3 · Ön koşul: KER-07

```text
Task KER-08. Model macro time series (policy rate decisions, FX rates, CPI, weekly
non-resident securities flows) as facts with valid time (the period the value refers to),
release time (known_at, from the publisher's release calendar or announcement timestamp) and
vintage. Revisions append. A policy-rate decision is known at its announcement time, not at the
start of its effective date. Weekly flow statistics are known at their publication time, not at
week end. Synthetic tests for each case and for a revision.
```

#### KER-09 · Endeks üyeliği modeli
Dalga 3 · Ön koşul: KER-08

Bitti ölçütü: üyelik aralıkları kaynağıyla birlikte saklanıyor; kanıtı eksik ya da çelişkili bir
dönem için as-of sorgusu `UNKNOWN` döndürüyor, asla tahmin etmiyor.

```text
Task KER-09. Add an append-only relation for index membership in a new migration: index code,
listing/security id, index period (start and end dates as published), evidence kind
(QUARTERLY_STATE such as a DataStore Product 3184 cell; PERIODIC_CHANGE from a review
announcement; INTRA_PERIOD_CHANGE where published), effective date, known_at (announcement
time), source document id. Semantics:
1) membership_as_of(index, as_of) returns members, non-members and UNKNOWN; it returns UNKNOWN
   when evidence for that period is missing or the evidence kinds disagree. It never projects a
   later list backwards and never assumes continuity inside a period.
2) What a quarterly-state cell means (period start or period end) is stored with the source,
   not hard-coded; until a source documents it, cells are flagged CELL_SEMANTICS_UNKNOWN.
3) Before an index period's announcement is public, its membership is not known (known_at).
Synthetic tests: a clean quarter; a quarter with a missing announcement (UNKNOWN); a conflict
between a state cell and a change announcement (UNKNOWN); an intra-period exclusion; an as_of
before the announcement.
```

#### KER-10 · Kaynak belgelerden kimlik kayıtları
Dalga 4 · Ön koşul: KER-09, KO-4

```text
Task KER-10. Build entity, security, listing and identifier-assignment records for every
company that appears in the membership evidence for the window, including companies that later
left the index, were renamed, merged or delisted. Allowed inputs: membership evidence in the
vault, and from the FinanceIQ repository only these source lists (no outcomes):
docs/evidence/bist_membership_event_sources.csv, docs/evidence/bist_membership_source_manifest.csv,
docs/evidence/bist_membership_p3184_2020_q4_rows.csv. KAP company records may be used where an
approved KAP rights decision covers the operation. Never read FinanceIQ's data/config/ lists.
Record ticker changes, mergers and delistings only where a source document states them (cite
it; unknown stays unknown). Tests: resolving a ticker at two different times; a reused ticker;
an ambiguous symbol fails; a delisted company stays resolvable as of dates when it was listed.
Output a coverage list (entity, listing, first and last evidence date) for the ingestion cards.
```

#### KER-11 · Üyelik kanıtı eksik listesi (araştırma)
Dalga 1 · Kod yazmaz, veri indirmez

Bitti ölçütü: hangi belgelerin hâlâ gerektiğini ve KO-5'te elle neyin indirileceğini gösteren bir
memo.

```text
Task KER-11 (research memo; no code, no downloads). Read, in the FinanceIQ repository, only:
docs/UNIVERSE_HISTORY_SOURCING_SPIKE.md, docs/DATA_EXPANSION_MEMBERSHIP_SOURCING_REPORT.md,
docs/BIST_MEMBERSHIP_EVENT_COVERAGE_AUDIT.md, docs/BIST_MEMBERSHIP_KAP_TRIGGER_AUDIT.md,
docs/BIST_MEMBERSHIP_P3184_2020_RECONCILIATION.md, docs/BIST_MEMBERSHIP_2020_10_01_COLLISION_AUDIT.md
and docs/evidence/bist_membership_*.csv. These are membership-sourcing documents and contain no
outcomes. Write docs/sources/MEMBERSHIP_EVIDENCE_GAPS.md in the Kernel repository:
1) What exists per year (periodic announcements archived, Product 3184 objects acquired or not,
   intra-period announcements), from the documents only.
2) The earliest year from which quarter-boundary membership can be evidenced for BIST 100.
3) A manual download checklist for the owner: Product 3184 objects per year (catalogue ids if
   the documents give them), periodic announcements still missing, each with where to find it.
4) Open questions: quarterly-cell semantics, reserve-substitution order, identity collisions.
State every claim's source document and section.
```

#### KER-12 · Vault bağlantısı
Dalga 3 · Ön koşul: KO-2

```text
Task KER-12. Read the vault root from env (PIT_VAULT_ROOT); refuse to run if it is inside the
repository or inside an iCloud-synced directory. Every raw file has a manifest row (sha256,
size, source, rights decision id, acquired_at). Exports and snapshots never contain vault
paths. Tests use a temporary vault.
```

### 5.3 İngest

Her ingest kartı idempotent, hash'li ve onaylı rights kararına karşı kontrol edilir. Her biri
KER-10'un kapsam listesine karşı bir kapsam raporu yazar: hangi varlık ve dönem var, hangisi yok.
Eksik olan eksik kalır, doldurulmaz. Bir ingest kartı migration gerektiriyorsa onu tek başına çalıştır.

#### KER-13a · KAP bildirim zamanları
Dalga 4

```text
Task KER-13a. Input: the owner's SC5 KAP raw cache in the vault (path from vault config). Parse
disclosure metadata into source documents and filing-time facts for financial-statement
disclosures: publication timestamp with timezone, period, consolidation where stated. Report
coverage against the KER-10 coverage list (entity-periods with an exact filing time, without,
and not in the cache at all). Never treat an empty or unparsed response as "no filing".
```

#### KER-13b · KAP tablo değerleri
Dalga 4 · Ön koşul: KER-13a

```text
Task KER-13b. From the KAP financial-statement disclosures in the vault, load statement values
as structured facts with the full dimension key (KER-01): period_type and period_basis as
published (cumulative), accounting_basis (TFRS_HISTORICAL / IAS29_RESTATED with
measuring_unit_date), consolidation, currency, unit, scale. Comparatives restated in a later
report are new facts (KER-02). Discrete quarters only through the KER-03 derivatives. Map line
items to a documented field vocabulary; unmapped items are kept as source-labelled facts, never
dropped silently. Financial-sector templates (banks, insurers) map to their own vocabulary.
Coverage report against the KER-10 list.
```

#### KER-13c · Günlük fiyatlar
Dalga 4

```text
Task KER-13c. For every listing in the KER-10 coverage list, including index leavers and
delisted listings, load raw daily bars and dividend/split events from Yahoo chart JSON under the
approved Yahoo rights decision, with a provenance manifest (symbol, url, accessed time,
sha256). Raw files go to the vault. known_at = session close in Europe/Istanbul. Integrity
checks only (gaps, duplicates, non-positive prices). Report listings with no data or with
history that starts late or ends early; never fill them. Never compute returns.
```

#### KER-13d · EVDS makro serileri
Dalga 4 · Ön koşul: KO-3

```text
Task KER-13d. Fetch the macro series named in KER-08 with the owner's EVDS key from the
environment; store raw responses in the vault; load facts with release times and vintages.
Document each series code and its release-time source.
```

#### KER-13e · Üyelik kanıtının yüklenmesi
Dalga 4 · Ön koşul: KO-5

```text
Task KER-13e. Load membership evidence into the KER-09 relation: Product 3184 files the owner
downloaded into the vault (QUARTERLY_STATE), periodic review announcements (PERIODIC_CHANGE) and
published intra-period changes (INTRA_PERIOD_CHANGE), each with its source document id and
known_at. Cross-check state against change announcements quarter by quarter and write a
reconciliation report: agreeing quarters, conflicting quarters (left UNKNOWN), quarters with no
evidence. Never resolve a conflict by guessing.
```

#### KER-13f · KAP kapsam boşlukları için edinim adaptörü
Dalga 4 · Ön koşul: KER-13a, KER-13b, onaylı KAP rights kararı

```text
Task KER-13f. For entity-periods the KER-13a/13b coverage reports list as missing from the
cache, add a KAP acquisition adapter under the approved KAP rights decision: 3–8 s between
requests, back off on 429, an empty response body is SEARCH_INCOMPLETE (retry later, never
"no filing"), raw responses to the vault with manifest rows, then the same parsers as 13a/13b.
Resumable and idempotent. Run it only after the owner confirms the run in chat; report what was
fetched and what is still missing.
```

### 5.4 Doğrulama ve export

#### KER-14 · Gerçek veriyle "golden" testler
Dalga 5 · Ön koşul: KER-13a/b/c/e

```text
Task KER-14. Add a test module that runs only when PIT_VAULT_ROOT is set and is skipped (and
reported as skipped) otherwise. Golden cases from real data: a TRY vs USD field, a cumulative
quarter derivation, an IAS 29 restated comparative, a ticker change, a late filing, a bonus
issue, an index exit followed by continued listing, a quarter whose membership is UNKNOWN. Each
case cites its source document id. No raw values are committed; expected values live in the
vault next to the raw data.
```

#### KER-15 · FinanceIQ için snapshot export'u
Dalga 3 · Ön koşul: KER-01

```text
Task KER-15. Add a deterministic, file-based export of snapshot envelopes under contract 2.0.0
for a requested set of as_of times and entities: statement facts, filing times, membership
intervals, identities, price bars, corporate actions, macro facts, each with known_at bounds
and lineage ids. Same input, same bytes, same content hash. Exports never contain vault paths
or raw licensed bytes beyond what the rights decision allows for internal research. Write a
manifest per export (contract version, hash algorithm, record counts, content hashes). The
Kernel never reads anything back from the consumer.
```
