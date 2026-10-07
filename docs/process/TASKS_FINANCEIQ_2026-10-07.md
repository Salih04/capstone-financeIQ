# FinanceIQ görevleri

Tarih: 2026-10-07 · Kapsam: [`RESEARCH_CHARTER.md`](RESEARCH_CHARTER.md) · Kernel görevleri ayrı
dosyada: [`TASKS_PIT_KERNEL_2026-10-07.md`](TASKS_PIT_KERNEL_2026-10-07.md)

Bu dosya FinanceIQ'nun bütün işlerini, tek tek başlatılabilecek kartlar halinde tutar. Her kartta
dalga, ön koşul, bitti ölçütü ve (ajan işleri için) yapıştırılmaya hazır bir prompt var. Prompt'lar
İngilizce, çünkü repo dokümanları ve kod İngilizce.

**Nasıl kullanılır**
- Ajan kartı: önce §3.1 FinanceIQ preamble'ı, sonra kartın prompt'u.
- Web araştırması kartı: §3.2 araştırma preamble'ı, sonra prompt.
- `FO-` kartları senin işin.
- `KER-` ile başlayan ön koşullar kernel dosyasındaki kartlardır.
- Bu dosyayı ve `GAP_CLOSURE_PLAN_2026-10-07.md`'yi **kernel oturumlarına verme**. FinanceIQ
  sonuçlarına atıf yapıyorlar; kernel sonuç görmemeli.

---

## 1. Durum

| İş | Durum | Kanıt |
|---|---|---|
| SC5 commit'lerini kurtar (A1) | Yapıldı (yerel) | Branch `archive/sc5-kap-batch1-2026-10-03`; bundle `~/FinanceIQ_backups/2026-10-07/`. Push kararı: FO-2 |
| SC5 ham önbelleğini yedekle (A2) | Yapıldı | Aynı klasör, 127 MB, 2.144 dosya, SHA-256 doğrulandı. Kalıcı vault: KO-2 (kernel dosyası) |
| Audit öncesi yüzeyleri etiketle (A5) | Yapıldı | Commit `547cffb5`: `X-Evidence-Status: withdrawn_pre_pit` + `PreAuditNotice` |
| 2026 ön kayıt yüzey kontrolü (A6) | Yapıldı, değişiklik gerekmedi | Dondurulmuş sıralamayı okuyan yüzey yok |
| **Kapsam değişikliği** | **Yapıldı (bu tur)** | `RESEARCH_CHARTER.md` yürürlükte; `AGENTS.md`/`CLAUDE.md` rolü ve kuralları, `PRD.md` ve `README.md` durum notu güncellendi |
| Ham vendor dosyaları (A3) | Kart: FIQ-09 | Veri erişim düzeni yeniden tasarlanmalı |

Charter'ın özü: capstone (40 şirket, yıllık T→T+1) **Capstone v1** olarak donduruldu. Evren, model,
hedef, özellik, eğitim şeması ve filtre artık serbest. Bu serbestliği bilimsel olarak savunulabilir
kılan disiplin şu: point-in-time veri, her denemenin deftere yazılması, kilitli holdout ve
doğrulayıcı analizden önce ön kayıt. 40 şirketlik kohort yeni araştırmada kullanılmaz; yerine
kurala bağlı U1 evreni geliyor (charter §4).

Eski karttan yeni karta geçiş: O-11→FO-1 · O-2→FO-2 · O-8→FO-3 · O-4→FO-4 · O-6→FO-5 ·
O-7→FO-6 · O-10→FO-7 · FIQ-3→FIQ-01 · FIQ-2→FIQ-02 · FIQ-4→FIQ-03 · FIQ-7→FIQ-08 ·
FIQ-1→FIQ-09 · FIQ-9→FIQ-13 · FIQ-10→FIQ-14 · FIQ-5→FIQ-15 · FIQ-8→FIQ-16 · FIQ-6→FIQ-18 ·
P2-A/B/C/E→FIQ-19/20/21/22. Geri kalanlar yeni.

---

## 2. Başlatma sırası

| Dalga | Paralel başlatılabilir | Ön koşul |
|---|---|---|
| 1 | FO-0, FO-1, FO-2, FO-3, FO-4, FO-6 · FIQ-01, FIQ-02, FIQ-03, FIQ-04, FIQ-05 · FIQ-13, FIQ-14 (web) | — |
| 2 | FIQ-06, FIQ-11 · FIQ-09 · FIQ-15 · FIQ-16 · FIQ-19 | FIQ-06/11 için FO-0; FIQ-09 için FO-4; FIQ-15 için FIQ-13 başlamış; FIQ-16 için FO-1 |
| 3 | FIQ-12 · FIQ-08 · FO-5 | FIQ-12 için FIQ-11; FIQ-08 için KER-01 ve KER-15; FO-5 için FIQ-15 taslağı |
| 4 | FIQ-07 · FIQ-10 · FIQ-18 | FIQ-07 için FIQ-06, FIQ-08, KER-09, KER-10, KER-13e; FIQ-10 için FIQ-08, KER-07, KER-08, KER-13a/b/c; FIQ-18 için FIQ-08, KER-13a |
| 5 | FIQ-17 · FIQ-20, FIQ-21 · FIQ-23 | FIQ-17 ve FIQ-23 için FIQ-07, FIQ-10, FIQ-12; FIQ-20/21 için FIQ-19, FIQ-07, KER-07, KER-13a, KER-13c |
| 6 | FO-7 → FIQ-22 · FIQ-24 → FO-7 → FIQ-25 | Ön kayıtlar OSF'de |

Aynı dosyalara dokunan kartlar paralel koşmaz. FIQ-01 ile FIQ-04 ikisi de süreç dokümanlarına
dokunuyor; sırayla çalıştır.

---

## 3. Preamble'lar

### 3.1 FinanceIQ preamble

```text
You are a coding agent working in the FinanceIQ repository (github.com/Salih04/capstone-financeIQ).
Read AGENTS.md first (rules live in docs/process/AGENTS.md), then docs/process/RESEARCH_CHARTER.md
(current scope; it wins over older documents), then docs/process/TASKS_FINANCEIQ_2026-10-07.md.
Do only the task below.

FinanceIQ is an open research program. The original capstone (40-company cohort, annual T->T+1)
is frozen as the Capstone v1 record. Models, targets, features, training schemes and filters are
open, under this discipline: never fabricate data and never impute stored data (missing stays
null); every feature must have been public at its use time; log every evaluated configuration in
the experiment ledger once it exists (FIQ-12); never evaluate on the locked holdout without a
registered confirmatory study; never use the capstone cohort lists in data/config/ as a research
universe. Never hand-edit data/trusted/ or data/trusted_clean/. Keep every "research support,
not investment advice" caveat and the withdrawn-result labels. No paid data, no secrets in git,
no acquisition code in this repository (it belongs in the PIT Kernel).

Git: create a new branch from main; small commits; never push to main; open a PR only if I ask.

Verify: PYTHONPATH=. python -m pytest tests/ -q (compare the *collected* count with
docs/VERIFICATION_BASELINE.md — fewer collected tests means tests were lost);
cd backend && python -m pytest tests/ -q; make data-validate; make claims-lint docs-lint.
The root suite needs a clean worktree: commit before running it.

Final report: 1) what changed (file + one-line reason), 2) exact verification commands and
honest results, 3) not done / needs verification.
```

### 3.2 Araştırma / yazım preamble'ı (ChatGPT, web erişimli)

```text
You are helping with academic papers from FinanceIQ, an open research program on Borsa Istanbul
equities. Paper 1 is a point-in-time audit of the program's own original study (publication-lag
and cohort-selection look-ahead). Paper 2 is a pre-registered event study of financial-statement
disclosures. Accuracy beats fluency: cite only sources you have verified, give DOIs or stable
URLs, and mark anything unverified as [UNVERIFIED]. Never invent numbers; use only figures I
paste from the repository. The work is research support, not investment advice.
```

---

## 4. Sahip kartları (SEN)

| ID | İş | Neden | Bitti ölçütü | Dalga |
|---|---|---|---|---|
| FO-0 | Charter'ı oku. İki kararı onayla ya da değiştir: **U1 evreni** (çeyreklik BIST 100 üyeliği, hayatta kalanları ve çıkanları içeren, boşlukta kapalı kalan) ve **holdout sınırları** (geliştirme ≤ 2022-12-31; kilitli holdout 2023–2025; ileri holdout = OSF kaydından sonra yayımlanan veri) | Bu iki karar, ilk U1 modeli değerlendirilmeden önce kesinleşmeli. Sonra değiştirmek forking-paths sayılır | Charter'da "Adopted" satırının altına onay notu; değişiklik varsa ilgili § güncel | 1 |
| FO-1 | 40 şirketlik kohortun **nasıl seçildiğini** yaz: `data/raw/yearly_xlsx/` dosyaları ("winner cohort") hangi üründen, hangi ekrandan, hangi filtreyle indirildi? Liste getiriye göre mi sıralanmıştı? | Paper 1'in seçim yanlılığı bölümü buna dayanıyor. Hakemin ilk sorusu olur | Kısa beyan: kaynak, tarih, filtre, sıralama ölçütü. Hatırlanmayan kısım "bilinmiyor" diye yazılır. FIQ-16'nın girdisi | 1 |
| FO-2 | SC5 arşiv branch'i: public repo'ya **push etme**. Özel bir arşiv repo'su aç (ör. `financeiq-private-archive`) ve `archive/sc5-kap-batch1-2026-10-03`'ü oraya push et | Repo public; SC5 bir KAP edinim aracı | Branch özel bir remote'ta | 1 |
| FO-3 | Bu branch'i (`local/financeiq-data-correlation-3c159d`) PR ile main'e al | Charter ve etiketler main'e girsin; ajanlar main'den branch açıyor | PR merge edildi; CI yeşil | 1 |
| FO-4 | Fintables ve Yahoo kullanım koşullarını oku. Her biri için kaynak, URL, okuma tarihi, yeniden dağıtım izni (var/yok) ve ilgili madde | FIQ-09'un girdisi | Kısa not, ör. `docs/SOURCE_TERMS_REVIEW_2026-10.md` (proposed) | 1 |
| FO-5 | Danışman: Uni Basel'de 2–3 aday hoca (Data Science veya finans/ekonometri). Charter, Paper 1 taslağı ve Paper 2 tasarımıyla kısa bir e-posta | Paper'ın kabul şansı için en büyük kaldıraç | İlk görüşme ayarlandı | 3 |
| FO-6 | İki repoyu da iCloud senkronlu Desktop dışına taşı; ardından her repoda `git worktree repair` | "x 2" kopyaları glob'ları bozuyor; kernel migration'larını iki kez çalıştırabilir | Repolar ör. `~/Projects/` altında; iki repoda da testler yeşil | 1 (bütün branch'ler push edildikten sonra) |
| FO-7 | OSF hesabı aç. Ön kayıtları gönder: Paper 2 (FIQ-19/20/21 sonrası), Study 3 doğrulayıcı analiz (FIQ-24 sonrası) | Zaman damgalı, public ön kayıt | OSF kaydı ve DOI | 6 |

---

## 5. Ajan kartları

### 5.1 Yönetişim ve Capstone v1 kaydı

#### FIQ-01 · Çalışma kaydı şablonu ve defterlerin dondurulması
Dalga 1

Bitti ölçütü: şablon var; iki eski defterin başında işaret satırı var; hiçbir geçmiş kayıt silinmedi.

```text
Task FIQ-01. Implement charter §5 rule 9 without deleting any history.
1) Add docs/process/STUDY_RECORD_TEMPLATE.md with two one-page parts. Before: question,
   estimand, universe rule version, data snapshot and cutoffs, development/holdout boundaries,
   analysis plan, multiplicity plan (how the experiment-ledger trial count enters it), stopping
   rule, what result would count as null, what would change the conclusion. After: registered
   versus post-hoc analyses, results, deviations, limitations, ledger trial count.
2) Add a one-line pointer at the top of TASK_STATE.md and FINANCEIQ_AGENT_TASK_QUEUE.md:
   frozen ledger as of 2026-10-07, new work is recorded with the template, see
   docs/process/RESEARCH_CHARTER.md. Do not change any existing entry.
Some tests read these files by path (TASK_STATE.md: Stage 3 registration test;
FINANCEIQ_AGENT_TASK_QUEUE.md: memo citation service); run the root suite and the backend suite.
```

#### FIQ-02 · Branch ve worktree hijyeni
Dalga 1 (yalnız rapor) · Uygulama yalnız onaydan sonra

Bitti ölçütü: rapor var. Onaydan sonra yalnız merge edilmiş ve temiz olanlar silinmiş; detached
ya da merge edilmemiş hiçbir iş kaybolmamış.

```text
Task FIQ-02. Phase 1 — read-only report. List every worktree (`git worktree list --porcelain`)
with: path, HEAD, branch or detached, clean/dirty (`git -C <path> status --porcelain`),
whether HEAD is contained in any branch, whether it is merged into main, and last commit date.
List local branches merged into main, branches not merged, and any commit reachable only from
a detached worktree HEAD. Write the report to docs/process/REPO_HYGIENE_REPORT.md with a
proposed action per row. Change nothing. Stop and wait for approval.
Phase 2 — after approval only: `git worktree prune`; remove approved clean worktrees of merged
branches; delete approved merged local branches with `git branch -d` (never -D). Never touch
dirty worktrees, unmerged branches, archive/* branches, or a worktree an active session uses.
```

#### FIQ-03 · Panel v2 ön kaydını "yerini U1 aldı" diye kapat
Dalga 1

Bitti ölçütü: `docs/PANEL_V2_STATUS.md` (proposed) durumu, gerekçeyi ve yeniden kullanılabilecek
parçaları kaydediyor; ön kaydın kendisi değişmemiş.

```text
Task FIQ-03. Read docs/PREREGISTERED_PANEL_V2_PIT.md and docs/panel_v2/* in full on branch
local/panel-v2-pit-prereg-6084b45f (commit e3d7012b; also on origin). Do not merge or modify it.
On your branch from main, write docs/PANEL_V2_STATUS.md: status SUPERSEDED as of 2026-10-07 by
docs/process/RESEARCH_CHARTER.md (it is an annual panel on the capstone universe; the charter
replaces both with the rule-based quarterly U1 universe). List the artefacts later work can
reuse (source-manifest schema, PIT cell-evidence schema, applicability rules) with file paths,
and cite branch and commit SHA. If the pre-registration contains a commitment that closing it
would break (e.g. a dated obligation), report it instead of closing.
```

#### FIQ-04 · Doğrulama tabanını yenile
Dalga 1 · Doğrulama gerçeğinin sahibi olan görev

Bitti ölçütü: `docs/VERIFICATION_BASELINE.md` bugünkü sayıları, commit'i ve ortamı kaydediyor;
`make docs-lint` yeşil.

```text
Task FIQ-04. This task owns verification truth. From a clean checkout of main, run exactly the
commands in docs/VERIFICATION_BASELINE.md (root suite, backend suite both invocations,
make data-validate, make claims-lint, make docs-lint) and record collected and passed counts,
the git SHA and the environment table. The last baseline is dated 2026-08-11; counts have grown
since (the 2026-10-07 branch added 27 backend tests). Explain every count change by commit
range; if any count went down, stop and report instead of recording it. Keep the CI deselect
list section accurate. Run make docs-lint last: other documents that cite the old counts must be
updated or listed in TRUTH_DRIFT_EXCLUSIONS with a reason.
```

#### FIQ-05 · Capstone v1 kaydı
Dalga 1

Bitti ölçütü: tek sayfalık kayıt dokümanı ve önerilen git etiketi; etiketi sen push edersin.

```text
Task FIQ-05. Write docs/CAPSTONE_V1_RECORD.md (one page): what Capstone v1 was (cohort,
period, design, models), where its code, data and results live, how to reproduce it (Makefile
targets), its known limitations (publication-lag look-ahead found by the 2026-10-04 audit;
undocumented cohort selection per docs/universe_audit.md; survivorship; low power), the
withdrawn_pre_pit labels on the app, and that new research follows
docs/process/RESEARCH_CHARTER.md. Link, do not copy, RESULTS.md and the audit. Propose an
annotated tag name and message (e.g. capstone-v1-final on the main commit that contains the
charter) but do not create or push it.
```

### 5.2 Evren

#### FIQ-06 · U1/U2 evren kuralı tasarımı
Dalga 2 · Ön koşul: FO-0 · Sonuç hesaplamaz

Bitti ölçütü: `docs/research/UNIVERSE_RULE.md` (proposed) sürüm numaralı, sonuçtan bağımsız ve
kernel verisinin nasıl kullanılacağını adım adım tanımlıyor.

```text
Task FIQ-06. Specify the research universe of charter §4 precisely enough that two people
implementing it get the same table. Compute no outcome of any kind.
Write docs/research/UNIVERSE_RULE.md (version 1.0.0):
1) Formation dates: BIST index period starts (quarterly reviews), with the source of each date.
2) U1 membership per formation date from Borsa Istanbul DataStore Product 3184 cross-checked with
   the periodic review announcements (docs/evidence/bist_membership_event_sources.csv). Read
   docs/BIST_MEMBERSHIP_EVENT_COVERAGE_AUDIT.md, docs/BIST_MEMBERSHIP_P3184_2020_RECONCILIATION.md
   and docs/BIST_MEMBERSHIP_KAP_TRIGGER_AUDIT.md first. Define what a Product 3184 quarter cell
   means (start or end of period — currently UNKNOWN; state how the cross-check resolves it) and
   what happens when the two sources disagree (fail closed).
3) Survivor inclusion: a firm in a formation sample is followed through the holding or event
   window after index exit, suspension, merger or delisting; how a delisting is recorded.
4) Intra-quarter entries join at the next review; intra-quarter exits stay in the sample.
5) Strata: non-financial primary; banks, insurers, leasing, factoring, brokerage as a separate
   stratum (rule based on statement template or official sector code, never on performance);
   holding companies flagged.
6) U2 robustness universe: all listed equities with KAP filings and prices at formation, with a
   liquidity screen computed only from data before formation (define it).
7) Window: the earliest and latest formation dates for which membership, KAP statements and
   prices all exist; give the feasibility count per year (members with evidence, members missing
   evidence) using only membership evidence — no prices or returns.
8) Versioning: any change after the first U1 model evaluation needs a new major version and is
   reported as a deviation.
```

#### FIQ-07 · Evren oluşturucu
Dalga 4 · Ön koşul: FIQ-06, FIQ-08, KER-09, KER-10, KER-13e · Sonuç hesaplamaz

Bitti ölçütü: her oluşum tarihi için evren tablosu + kapsam raporu; dışlanan tarih ve firmalar
sayılmış; testler kuralı sentetik vakalarla doğruluyor.

```text
Task FIQ-07. Implement docs/research/UNIVERSE_RULE.md v1.0.0 on Kernel snapshots read through
experiments/pit/kernel_snapshot.py. Put the builder in experiments/universe/ (new). Output: one
row per (formation_date, entity_id, security_id) with stratum, membership source document ids
and inclusion reason, plus a coverage report (formation dates excluded and why, firms without
identity, firms without any statement or price coverage). Record the universe rule version and
snapshot content hashes in the output. Tests with synthetic snapshots: a firm that exits
mid-quarter stays; a firm that enters mid-quarter joins at the next review; a quarter with
conflicting sources fails closed; a delisted firm keeps its rows. Compute no returns.
```

### 5.3 Veri

#### FIQ-08 · Kernel snapshot adaptörü
Dalga 3 · Ön koşul: KER-01 (contract 2.0.0), KER-15 (export)

Bitti ölçütü: FinanceIQ Kernel snapshot'larını dosyadan okuyor, contract major sürümünü ve hash'i
doğruluyor; FinanceIQ'dan Kernel'e yazma yolu yok; snapshot yapılandırılmadığında eski davranış
byte-byte aynı.

```text
Task FIQ-08. Add a one-way, file-based reader for PIT Kernel snapshot exports (contract 2.0.0)
in experiments/pit/kernel_snapshot.py. It reads export directories given by config or env,
rejects unknown contract major versions and hash algorithms, recomputes and checks every
content hash, and exposes facts by the full dimension key: statement facts, filing times,
membership intervals, identities, price bars, corporate actions and macro facts, each with
known_at bounds. Copy only the Kernel's synthetic contract fixtures into tests/fixtures/kernel/.
Wire the existing PIT guard so that, when a snapshot directory is configured, filing times come
from it instead of data/pit/reporting_deadlines.csv and filing_dates_sample.csv; with no
snapshot configured, behaviour stays byte-identical (prove it with a test). FinanceIQ never
writes to the Kernel.
```

#### FIQ-09 · Public veri erişim yeniden tasarımı (A3)
Dalga 2 · Ön koşul: FO-4, KO-2 (vault) · İki aşamalı

Bitti ölçütü: public HEAD'de üçüncü taraf ham ya da ham eşdeğeri dosya yok; manifest ve edinme
talimatları var; CI yeşil; kök suite'in toplanan test sayısı sahibin onaylamadığı biçimde düşmüyor.

```text
Task FIQ-09 (two phases). Phase 1 — design only, change no tracked data files.
1) Inventory every tracked file that is third-party raw data or a near-verbatim conversion of it:
   data/raw/** (Fintables XLSX), data/trusted/20XXstocks.csv and stocks_2020_2025.csv,
   data/trusted_raw/**/yahoo_chart_raw/*.json, and anything else you find. For each, list
   every script, test, Makefile target and backend module that reads it.
2) The owner's rule FI-SOURCE-OWNER-AMENDMENT-01 (docs/SOURCE_USE_OWNER_AMENDMENT.md §1.2)
   forbids public redistribution of third-party raw datasets. The owner's terms review is in
   docs/SOURCE_TERMS_REVIEW_2026-10.md (if missing, stop and ask).
3) Write docs/DATA_AVAILABILITY_DESIGN.md: which files leave the public tree, what replaces
   them (manifest: path, sha256, source, retrieval date, obtain instructions), how
   `make data-validate`, the root suite and CI keep working (options: a derived-only CI fixture
   the terms allow; machine-of-record-only tests with an owner-approved deselect list — never
   silently drop tests), and how other checkouts avoid losing local copies when the removal is
   pulled (back up to the vault first). Capstone v1 must stay reproducible on the owner's
   machine. Stop and wait for owner approval.
Phase 2 — only after I approve the design: implement it with `git rm --cached` plus
.gitignore so local copies stay; add the manifests; update docs/VERIFICATION_BASELINE.md only
if the owner approved a count change. Do not rewrite git history (separate owner decision).
```

#### FIQ-10 · Point-in-time özellik deposu
Dalga 4 · Ön koşul: FIQ-08, KER-07, KER-08, KER-13a, KER-13b, KER-13c

Bitti ölçütü: her özellik değerinin bir `known_at` zamanı var; geleceği sızdıran özellik enjekte
eden testler kırılıyor; hedef ya da getiri hesaplanmıyor.

```text
Task FIQ-10. Build a point-in-time feature store from Kernel snapshots in experiments/features/
(new). Compute no targets and no returns; this task builds inputs only.
1) Fundamentals: discrete quarters and trailing-twelve-month values derived from published
   cumulative figures (use the Kernel's derivatives, never re-derive differently), ratios and
   growth rates. Every value carries known_at = the latest known_at of its inputs.
2) IAS 29: keep the accounting basis in the key; provide unit-invariant variants (ratios,
   within-report comparisons) and document which features are comparable across the 2023
   basis change (charter §5 rule 7).
3) Market features from raw price bars plus corporate actions (adjustment factors from the
   Kernel's derivatives): size, liquidity, past-window volatility and momentum computed only
   from bars before the as-of time.
4) Macro features with their release times (policy rate, FX, CPI, weekly non-resident flows).
5) API: features_as_of(entity_ids, as_of) returning only values with known_at <= as_of.
6) Tests: inject a fact published one day after as_of and assert it is invisible; a restated
   comparative does not overwrite the original; a missing input yields null, never a fill.
Record feature definitions with a version in docs/research/FEATURES.md.
```

### 5.4 Araştırma altyapısı

#### FIQ-11 · Araştırma protokolü
Dalga 2 · Ön koşul: FO-0

Bitti ölçütü: `docs/research/PROTOCOL.md` (proposed) bütün çalışmaların uyacağı ortak kuralları
tanımlıyor; FIQ-12 bunu koda döküyor.

```text
Task FIQ-11. Write docs/research/PROTOCOL.md implementing charter §5 rules 6–8 for every study:
1) Time boundaries: development window, locked holdout, forward holdout (dates from the charter
   as approved in FO-0); what "touching the holdout" means operationally (any metric, plot or
   summary computed from outcomes dated in it).
2) Validation inside the development window: purged and embargoed cross-validation or
   expanding windows; embargo length tied to target horizon; nested tuning.
3) Multiplicity: every evaluated configuration counts; how the trial count enters the
   adjustment (Holm or Benjamini–Hochberg for families of hypotheses; White's reality check or
   Hansen's SPA for model selection; deflated performance metrics). Cite the methods.
4) Confirmatory analysis: at most a few pre-registered hypotheses, one run on the holdout,
   reported whatever the result; how semi-clean 2023–2025 is disclosed.
5) IAS 29: how models trained before 2023 are evaluated after the basis change.
6) LLM-derived features: model pin, prompt hash, training-cutoff check (rule 8).
7) Reporting: registered vs post-hoc, trial count, null results reported.
Use docs/process/STUDY_RECORD_TEMPLATE.md if it exists.
```

#### FIQ-12 · Deney defteri ve holdout kilidi
Dalga 3 · Ön koşul: FIQ-11

Bitti ölçütü: her değerlendirme deftere ekleniyor; kayıtlı bir çalışma kimliği olmadan holdout
tarihli sonuç üzerinde metrik hesaplanamıyor; testler ikisini de zorluyor.

```text
Task FIQ-12. Implement docs/research/PROTOCOL.md in code under experiments/research_core/ (new).
1) Experiment ledger: append-only JSONL (path from config; outside git if it would grow large).
   One record per evaluated configuration: timestamp, git SHA, universe rule version, Kernel
   snapshot hashes, feature set version, target, model and hyperparameters, seed, evaluation
   window, metrics, study id or "exploratory". Records are never edited; a hash chain makes
   tampering detectable.
2) Holdout lock: the only function that joins outcomes to predictions refuses any outcome dated
   inside the locked or forward holdout unless it receives a study id that resolves to a
   registered study record containing an OSF URL and a git commit, and the current commit
   descends from it. Each registered study may open the holdout once; a second attempt fails.
3) A trial-count report per study and overall.
4) Tests: an exploratory run cannot read holdout outcomes; a registered study can, once;
   editing a ledger line breaks the hash chain; every evaluation path goes through the ledger.
```

### 5.5 Paper 1 — audit (zamanlama + seçim)

#### FIQ-13 · Atıf doğrulama
Dalga 1 · Araştırma preamble'ı ile ChatGPT (web)

Bitti ölçütü: `docs/paper1/references.bib` (proposed) + doğrulama tablosu (yazar, yıl, başlık,
dergi, DOI, durum).

```text
Task FIQ-13. Verify each reference in §13 of docs/process/GAP_CLOSURE_PLAN_2026-10-07.md (I
will paste the list). For each: exact authors, year, title, venue, volume/pages, DOI; mark
VERIFIED or WRONG (with the correction). Then find 3–5 peer-reviewed works since 2015 on
look-ahead bias, publication-lag handling, survivorship or sample-selection bias, or data
leakage in machine learning for asset pricing, with one sentence on what each contributes.
Add the multiple-testing references the protocol needs (White 2000 reality check; Hansen 2005
SPA; Harvey, Liu and Zhu 2016; Bailey and López de Prado on the deflated Sharpe ratio).
Output BibTeX plus a verification table.
```

#### FIQ-14 · Hedef dergi kısa listesi
Dalga 1 · Araştırma preamble'ı ile ChatGPT (web)

```text
Task FIQ-14. For Borsa Istanbul Review, Finance Research Letters, The Journal of Financial Data
Science, and ICAIF / NeurIPS finance workshops (plus two venues you think fit better): scope
fit for a methodological audit paper with a negative result, article type and length limits,
open-access fee, typical time to first decision, and whether negative or replication results
are explicitly welcome. Give sources and a ranked recommendation.
```

#### FIQ-15 · Paper 1 taslağı
Dalga 2 · Ön koşul: FIQ-13 başlamış olmalı

Bitti ölçütü: `docs/paper1/draft.md` (proposed) 8–12 sayfa; bütün sayılar RESULTS.md ve PIT-v2
raporuyla birebir aynı; seçim yanlılığı bölümü FIQ-16/17 için yer tutucu; yeni analiz yok.

```text
Task FIQ-15. Draft Paper 1 in docs/paper1/draft.md (8–12 pages). Run no new analysis; every
number must match RESULTS.md and experiments/results_pit_v2/REPORT.md verbatim.
Thesis: two look-aheads inflate an ML-for-finance evaluation in an emerging market —
publication timing (measured by the point-in-time audit) and cohort selection (to be measured
by FIQ-17; leave a clearly marked placeholder section and do not guess its size).
Structure: abstract; introduction; related work; data; original design; the audit (publication
lag, mixed adjustment bases, pre-listing rows); point-in-time protocol and guard; corrected
results; cohort selection (placeholder; what is known from docs/universe_audit.md and the
owner's statement once FIQ-16 exists); power and controls; limitations; reproducibility;
conclusion. Positioning: the publication-lag rule is known in empirical finance (Fama–French
use a lag of at least six months for annual accounting data); the contribution is measuring how
much violating it — and selecting the sample — inflates an evaluation, plus a machine-checked
PIT guard with tests that inject future-available features. Framing: target trial emulation and
immortal-time bias as the clinical analogue; leakage taxonomy; multiple testing. State what was
registered and what was post-hoc (docs/PREREGISTRATION_AMENDMENT_2026-10-04.md). Mark every
citation not verified in docs/paper1/references.bib as [UNVERIFIED].
```

#### FIQ-16 · Kohort seçimi ve hayatta kalma sınırı
Dalga 2 · Ön koşul: FO-1

Bitti ölçütü: Paper 1'e girecek paragraf + tablo; kanıtı olmayan hiçbir şey sayılmamış; seçim
kuralı (ya da bilinmediği) açıkça yazılmış.

```text
Task FIQ-16. First, record how the public 40-company cohort was selected, using only the
owner's statement (FO-1) and repository evidence (docs/universe_audit.md; data/raw/README.md
calls the yearly files a "winner cohort"). If the cohort was ranked or filtered on returns,
say so plainly as an outcome-selection limitation distinct from survivorship; if unknown, say
unknown. Then, using only evidenced membership sources (docs/evidence/bist_membership_*.csv and
the BIST membership audit documents in docs/), count for each year 2020–2025: index members
with evidence, how many are in the 81-company universe (data/config/), how many are not, and
how many of those are delisted or merged where evidenced. Unknown stays unknown (separate
column; never infer). Write docs/paper1/survivorship_bound.md with the table, one paragraph
for the paper, and the source of every number.
```

#### FIQ-17 · Seçim etkisinin ölçümü (Capstone tasarımı U1 üzerinde)
Dalga 5 · Ön koşul: FIQ-07, FIQ-10, FIQ-12 · Önce şartname commit'lenir, sonra çalıştırılır

Bitti ölçütü: şartname çalıştırmadan önce commit'lenmiş; sonuç kaynak etkisi ve seçim etkisi
olarak ayrı ayrı raporlanmış; deftere yazılmış.

```text
Task FIQ-17. Step 1 — before any run, write and commit docs/paper1/SELECTION_REPLICATION_SPEC.md:
re-run the frozen Capstone v1 design (same features as far as Kernel data allows, same target
definition, same models and hyperparameters, same walk-forward folds, point-in-time mode) on
U1 for the years that overlap the capstone. Two contrasts, both fixed in advance:
(a) source effect — the capstone cohort with Kernel (KAP) data versus the same cohort with the
original vendor data; (b) selection effect — U1 versus the capstone cohort, both with Kernel
data. List every feature that cannot be rebuilt from Kernel data and how it is handled
(dropped, never imputed). State the metrics, tests and how results enter Paper 1.
Step 2 — run from the spec commit through the experiment ledger (study id
paper1-selection-replication). Step 3 — write the results with the ledger trial count; report
them whatever they show. These years overlap the capstone evaluation, which is why this is a
replication of a frozen design, not a new model search.
```

#### FIQ-18 · Kesin bildirim zamanı duyarlılığı
Dalga 4 · Ön koşul: FIQ-08, KER-13a

Bitti ölçütü: amendment çalıştırmadan **önce** commit'lenmiş; çalıştırma o commit'ten yapılmış;
sonuç post-hoc duyarlılık analizi olarak raporlanmış.

```text
Task FIQ-18. Step 1 — before any run, write and commit an amendment
docs/PIT_EXACT_FILING_AMENDMENT.md: exact-filing-timestamp mode replaces statutory deadlines
where a Kernel snapshot gives a filing time; the rule for company-years without one (state it
in advance: excluded, not imputed, not deadline-filled — or justify another pre-specified rule);
outputs; how it will be reported (post-hoc sensitivity, never replacing the registered primary
result). Record the commit SHA. Step 2 — run experiments/pit_v2_evaluation.py in that mode
from the amendment commit, with Kernel snapshots pinned by content hash. Step 3 — append the
result to the PIT-v2 report as a sensitivity, with coverage (how many company-years had exact
times) and the amendment SHA.
```

### 5.6 Paper 2 — bildirim olay çalışması ve etki ayrıştırma

Finans uzmanının sorusu burada: bir firmanın fiyat hareketinin ne kadarı piyasa, faiz, kur ve fon
akışından, ne kadarı firmanın kendi bilanço haberinden geliyor? Ön kayıt gönderilene kadar hiçbir
oturum gerçek bildirim tarihlerinde olağandışı getiri hesaplamaz ya da onu sürprizle ilişkilendirmez.

#### FIQ-19 · Tasarım dokümanı ve OSF ön kayıt taslağı
Dalga 2

```text
Task FIQ-19. Write docs/paper2/DESIGN.md and docs/paper2/OSF_PREREGISTRATION_DRAFT.md for an
event study of KAP financial-statement disclosures on the U1 universe
(docs/research/UNIVERSE_RULE.md). Compute no outcome. Cover: questions (1: abnormal return
around disclosures versus a pre-specified earnings surprise; 2: attribution — how much of the
event-window move is explained by market, interest-rate, FX and non-resident-flow factors
versus the firm-specific component, with the factor model and its PIT inputs fixed in advance;
3: whether the IAS 29 transition changed the surprise–reaction relation); event time from the
KAP timestamp (after-close disclosures move to the next session); surprise (seasonal random-walk
SUE on discrete quarterly earnings; earnings-announcement return as alternative; no analyst
consensus exists); expected-return model and an estimation window ending before the event;
inference robust to event-date clustering (Kolari–Pynnönen adjustment, calendar-time
portfolios, clustered standard errors); placebo events and negative controls; the holdout per
docs/research/PROTOCOL.md; exclusions; multiplicity; stopping rule; what counts as null.
Use docs/process/STUDY_RECORD_TEMPLATE.md if it exists.
```

#### FIQ-20 · Pilot: belge, zaman damgası ve fiyat eşleşmesi
Dalga 5 · Ön koşul: FIQ-19, FIQ-07, KER-07, KER-13a, KER-13c

```text
Task FIQ-20. For 3–5 companies, check that each KAP financial-statement disclosure maps to the
right trading session (timezone, after-close rule, holidays) and that prices exist around it.
Report mismatches and their causes. Allowed: timestamps, calendars, price availability.
Forbidden: computing abnormal returns at the true disclosure dates or relating anything to
surprise.
```

#### FIQ-21 · Kümelenmeyi koruyan güç simülasyonu
Dalga 5 · Ön koşul: FIQ-19, FIQ-07, KER-07, KER-13c

```text
Task FIQ-21. Estimate power with the Brown–Warner approach: draw placebo event dates that keep
the real calendar clustering of disclosure dates (never use the true dates), inject abnormal
returns of chosen sizes, and apply the inference planned in FIQ-19. Report detection rates by
effect size and false-positive rates with no injection. Seeded, reproducible, logged in the
experiment ledger as study paper2-power.
```

#### FIQ-22 · Ana analiz
Dalga 6 · Ön koşul: FO-7 (OSF kaydı)

Ön kayda birebir uyarak, deney defteri üzerinden çalıştır. Sapmalar ayrı bir bölümde raporlanır.

### 5.7 Study 3 — açık modelleme

Burada model ailesi, hedef, özellik ve filtre serbest. Tek şart: keşif geliştirme penceresinde
kalır, her deneme deftere girer, holdout'a yalnız ön kayıtlı doğrulayıcı analiz dokunur.

#### FIQ-23 · Keşif: geliştirme penceresinde serbest modelleme
Dalga 5 · Ön koşul: FIQ-07, FIQ-10, FIQ-12

Bitti ölçütü: keşif raporu deneme sayısıyla birlikte; holdout'a hiç dokunulmamış (defter bunu
gösteriyor); doğrulayıcı aşamaya taşınacak en fazla birkaç hipotez gerekçesiyle seçilmiş.

```text
Task FIQ-23. Exploratory modeling on the U1 point-in-time panel inside the development window
only (docs/research/PROTOCOL.md). Any target, model family, feature set, training scheme and
filter is allowed if declared in the run config before it is evaluated. Every evaluated
configuration goes through the experiment ledger as "exploratory". Suggested breadth: linear
and regularised baselines, gradient-boosted trees, a neural model, a panel model; targets at
more than one horizon; purged and embargoed validation. Write docs/study3/EXPLORATION_REPORT.md:
what was tried (from the ledger, with the total trial count), what was learned, and at most
three candidate hypotheses for confirmation, each with the exact configuration that would be
frozen. Report the multiplicity-adjusted view, not only the best run. Never read holdout
outcomes; the lock should refuse it.
```

#### FIQ-24 · Doğrulayıcı ön kayıt
Dalga 6 · Ön koşul: FIQ-23 · Çıktıyı FO-7 OSF'ye gönderir

```text
Task FIQ-24. Turn the candidate hypotheses of docs/study3/EXPLORATION_REPORT.md into
docs/study3/OSF_PREREGISTRATION_DRAFT.md using the study record template: frozen
configurations (code commit, feature version, universe version, snapshot hashes), the single
holdout evaluation, metrics and tests, multiplicity across the registered hypotheses and the
exploration trial count, the semi-clean disclosure for 2023–2025, the forward-holdout plan, and
what result counts as null. Run nothing on the holdout.
```

#### FIQ-25 · Doğrulayıcı çalıştırma
Ön koşul: FO-7 (OSF kaydı)

Kayıtlı çalışma kimliğiyle holdout bir kez açılır. Sonuç ne olursa olsun raporlanır; sapmalar ayrı
bölümde.

---

## 6. Sonraya bırakılanlar

Paper 2 pilotundan sonra değerlendirilir; şimdilik kart yok: fon akışı çalışması, sponsor veya
banka verisi talep şartnamesi, hukuki çerçeve, CDS ve kredi spread'i için ücretsiz kaynak.
Ayrıntılar: `GAP_CLOSURE_PLAN_2026-10-07.md` §7.
