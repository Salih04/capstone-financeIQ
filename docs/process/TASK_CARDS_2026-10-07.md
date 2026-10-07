# Görev kartları — FinanceIQ + PIT Kernel

Tarih: 2026-10-07 · Kaynak plan: `docs/process/GAP_CLOSURE_PLAN_2026-10-07.md`

Bu dosya plandaki işlerin, sırayla tek tek başlatılabilecek görev kartlarına bölünmüş halidir.
Her kartta oturum türü, dalga, bağımlılık, bitti ölçütü ve (ajan işleri için) yapıştırılmaya
hazır bir prompt var. Prompt'lar İngilizce, çünkü repo dokümanları ve kod İngilizce.

> **Kernel kuralı.** Kernel oturumlarına plan dosyasını ya da FinanceIQ sonuç dosyalarını
> verme; plan sonuç sayıları içeriyor. Kernel oturumuna yalnızca **Kernel preamble'ı + o kartın
> prompt'unu** yapıştır. Bu dosyanın kendisi bilerek sonuç sayısı içermiyor.

---

## 1. Durum: bu oturumda yapılanlar (2026-10-07)

| Plan ID | İş | Durum | Kanıt |
|---|---|---|---|
| A1 | SC5 commit'lerini branch'e bağla | **Yapıldı (yerel)** | Branch `archive/sc5-kap-batch1-2026-10-03` → `2a031896`. Bundle: `~/FinanceIQ_backups/2026-10-07/sc5-kap-batch1.bundle` (`git bundle verify` OK). Push edilmedi: repo public ve SC5 bir KAP edinim aracı; karar sende (O-2) |
| A2 | SC5 ham önbelleğini yedekle | **Yapıldı** | `~/FinanceIQ_backups/2026-10-07/batches/` (127 MB, iCloud dışı); 2.144 dosya `batches_SHA256SUMS.txt` ile doğrulandı. Kalıcı vault kararı: O-3 |
| A3 | Ham vendor dosyalarını public HEAD'den kaldır | **Yeniden kapsamlandı → FIQ-1** | Ham XLSX'lere `make data-validate` (CI), `build_all`, backend `trusted_data.py` / `dataset_service.py` bağlı. `data/trusted/20XXstocks.csv` de vendor dosyasının CSV karşılığı. Bu tek commit'lik bir silme değil, veri erişim mimarisi değişikliği |
| A4 | Git geçmişi temizliği kararı | Bekliyor → O-4 sonrası | — |
| A5 | Legacy yüzeylere "geri çekildi" etiketi | **Yapıldı** | Commit `547cffb5`: `backend/app/core/evidence_status.py` + middleware → `X-Evidence-Status: withdrawn_pre_pit`. Bütün route'ların sınıflandırılmasını zorlayan test: `backend/tests/test_evidence_status.py` (27 test). `frontend/src/components/PreAuditNotice.jsx` AppShell'de; tarayıcıda /forecasting, /research-agent'ta göründüğü, /dashboard ve /data-quality'de görünmediği doğrulandı |
| A6 | 2026 ileriye dönük ön kayıt yüzey kontrolü | **Yapıldı, değişiklik gerekmedi** | Dondurulmuş sıralamayı (`experiments/results_forward_2026/`) okuyan frontend/backend kodu yok. Canlı tahmin sayfası artık A5 bandının altında |

Bu turdaki yeni bulgular:
- **Kernel repo'nun remote'u yok.** Tek kopya iCloud senkronlu Desktop'ta → O-1.
- **Kernel'de devam eden iş var.** `rights.py`, `postgres.py`, `source_rights.schema.json` ve
  fixture'da commit'lenmemiş değişiklikler var (2026-10-07 18:08). Başka bir oturumun işi;
  KER kartları bu iş commit'lendikten sonra başlamalı → KER-0.

---

## 2. Önerilen başlatma sırası

Aynı repoda aynı dosyalara dokunan kartlar paralel koşmaz. KER-1 → KER-2 → KER-3 sırayla
koşar, çünkü üçü de `temporal.py` ve şemalara dokunuyor.

| Dalga | Paralel başlatılabilir | Ön koşul |
|---|---|---|
| 1 | O-1, O-2, O-3, O-4, O-5, O-8 · FIQ-2 (yalnız rapor), FIQ-3, FIQ-4, FIQ-9, FIQ-10 · KER-0 | — |
| 2 | KER-1 → KER-2 → KER-3 · KER-5 · KER-4 · KER-6 → O-9 · FIQ-1 · FIQ-5 · FIQ-8 | KER-0 bitti; KER-4 için O-1; FIQ-1 için O-4 |
| 3 | KER-7, KER-8, KER-11 · KER-9 · FIQ-7 · O-6 · O-7 | KER-9 için O-9; FIQ-7 için KER-1; O-6 için FIQ-5 taslağı; O-7 için bütün branch'ler push edilmiş |
| 4 | KER-10a–d · KER-12 · FIQ-6 · P2-A | KER-10 için O-9, O-5, KER-11; FIQ-6 için KER-10a |
| 5 | P2-B, P2-C → O-10 (OSF) → P2-E | P2-B/C için KER-10b ve KER-7 |

---

## 3. Preamble'lar (her kartın prompt'undan önce yapıştır)

### 3.1 FinanceIQ preamble

```text
You are a coding agent working in the FinanceIQ repository (github.com/Salih04/capstone-financeIQ).
Read AGENTS.md first (rules live in docs/process/AGENTS.md), then
docs/process/GAP_CLOSURE_PLAN_2026-10-07.md (plan and decisions K1–K18) and
docs/process/TASK_CARDS_2026-10-07.md. Do only the task below.

Rules: never fabricate or impute data; missing stays null. Never hand-edit data/trusted/ or
data/trusted_clean/. Keep every "research support, not investment advice" caveat and the
weak-signal / withdrawn-result framing. No paid APIs, no secrets in git, no new scrapers.

Git: create a new branch from main; small commits; never push to main; open a PR only if I ask.

Verify: PYTHONPATH=. python -m pytest tests/ -q (compare the *collected* count with
docs/VERIFICATION_BASELINE.md — fewer collected tests means tests were lost);
cd backend && python -m pytest tests/ -q; make data-validate; make claims-lint docs-lint.
The root suite needs a clean worktree: commit before running it.

Final report: 1) what changed (file + one-line reason), 2) exact verification commands and
honest results, 3) not done / needs verification.
```

### 3.2 Kernel preamble (kör oturum)

```text
You are a coding agent working in the financeiq-pit-kernel repository
(/Users/salihcamci/Desktop/Projects/First_Priority_Projects/financeiq-pit-kernel).
Read AGENTS.md, README.md, docs/governance/SCOPE_AND_GATES.md and docs/architecture/*.md first.

NO_NEW_OUTCOME_INSPECTION=true is binding. Do not open, search or summarize files of the main
FinanceIQ repository except paths this task names explicitly, and never anything containing
returns, rankings, IC values, model results or experiment outputs. No recursive searches outside
this repository. If an outcome figure appears, stop, do not use it, and append an entry to
docs/governance/INCIDENT_EVENTS.jsonl. You may store and integrity-check raw prices when a task
says so, but never compute or inspect returns.

No real data acquisition, external account use or scraping unless the task says so AND an
owner-approved rights decision exists for that exact source and operation. Licensed raw bytes
never enter git; they live in the PRIVATE_LOCAL_RAW vault outside the repository.

Migrations are append-only: add a new numbered file, never edit an applied one. A change to
temporal meaning or canonical hash bytes requires a new contract major version.

Git: start from a clean main; create a new branch; small commits; never rewrite history.
Verify: python3 -m unittest discover -s tests -v, plus the same with PIT_TEST_DSN pointing at a
disposable PostgreSQL 16+ database for the persistence tests.

Final report: 1) what changed, 2) verification commands and honest results,
3) not done / needs verification.
```

### 3.3 Araştırma / yazım preamble (ChatGPT, web erişimli)

```text
You are helping with an academic paper derived from the FinanceIQ project, a point-in-time
audit of a financial machine-learning study on Borsa Istanbul equities. Accuracy beats fluency:
cite only sources you have verified, give DOIs or stable URLs, and mark anything unverified as
[UNVERIFIED]. Never invent numbers; use only figures I paste from the repository's RESULTS.md.
The work is research support, not investment advice.
```

---

## 4. Sahip kartları (SEN)

| ID | İş | Neden | Bitti ölçütü | Dalga |
|---|---|---|---|---|
| O-1 | Kernel için **özel** bir GitHub repo'su aç; devam eden iş (KER-0) commit'lendikten sonra push et | Kernel'in remote'u yok; tek kopya | `git remote -v` bir remote gösteriyor; `main` push edilmiş | 1 |
| O-2 | SC5 arşiv branch'inin push kararı. Öneri: public repo'ya **push etme**; özel bir arşiv repo'su aç (ör. `financeiq-private-archive`) ve `archive/sc5-kap-batch1-2026-10-03`'ü oraya push et | Repo public; SC5 bir KAP edinim aracı | Branch özel bir remote'ta | 1 |
| O-3 | Vault kararı (K-11): şifreli APFS disk imajı ya da harici disk + ikinci kopya. `~/FinanceIQ_backups/2026-10-07/` içeriğini oraya taşı | Ham veri iCloud'da ve tek diskte | Vault yolu belirli; SHA-256 manifesti vault'ta doğrulanıyor | 1 |
| O-4 | Fintables ve Yahoo kullanım koşullarını oku; her biri için kaynak, URL, okuma tarihi, yeniden dağıtım izni (var/yok) ve ilgili madde | FIQ-1 ve A4'ün girdisi | Kısa karar notu (ör. `docs/SOURCE_TERMS_REVIEW_2026-10.md`) | 1 |
| O-5 | EVDS API anahtarı al (ücretsiz kayıt). Anahtarı yalnız env veya Keychain'de tut | KER-10c için gerekli | Anahtar alındı; git'te yok | 1 |
| O-6 | Danışman: Uni Basel'de 2–3 aday hoca (Data Science veya finans/ekonometri). Paper 1 taslağı ve Paper 2 önerisiyle kısa bir e-posta | Paper'ın kabul şansı için en büyük kaldıraç | İlk görüşme ayarlandı | 3 |
| O-7 | Repoları iCloud senkronlu Desktop dışına taşı; ardından her repoda `git worktree repair` | "x 2" kopyaları glob'ları bozuyor | Repolar örn. `~/Projects/` altında; testler yeşil | 3 |
| O-8 | Bu branch'i (`local/financeiq-data-correlation-3c159d`) PR ile main'e al | A5 ve plan dokümanları main'e girsin | PR merge edildi; CI yeşil | 1 |
| O-9 | KER-6'daki rights karar taslaklarını onayla ya da düzelt | Gerçek veri ingest'inin kapısı | Beş karar `APPROVED` ya da gerekçeli `DENIED` | 2 |
| O-10 | OSF hesabı aç; Paper 2 ön kaydını gönder (P2-A/B/C bittikten sonra) | Zaman damgalı, public ön kayıt | OSF kaydı ve DOI | 5 |

---

## 5. FinanceIQ kartları (FIQ)

### FIQ-1 · Public veri erişim yeniden tasarımı (A3)
Dalga 2 · Ön koşul: O-4, O-3 · İki aşamalı: önce tasarım, sonra uygulama

Bitti ölçütü: public HEAD'de üçüncü taraf ham veya ham eşdeğeri dosya yok; manifest + fetch
talimatları var; CI yeşil; kök suite'in toplanan test sayısı sahibin onaylamadığı biçimde
düşmüyor.

```text
Task FIQ-1 (two phases). Phase 1 — design only, change no tracked data files.
1) Inventory every tracked file that is third-party raw data or a near-verbatim conversion of it:
   data/raw/** (Fintables XLSX), data/trusted/20XXstocks.csv and stocks_2020_2025.csv,
   data/trusted_raw/**/yahoo_chart_raw/*.json, and anything else you find. For each, list
   every script, test, Makefile target and backend module that reads it.
2) The owner's rule FI-SOURCE-OWNER-AMENDMENT-01 (docs/SOURCE_USE_OWNER_AMENDMENT.md §1.2)
   forbids public redistribution of third-party raw datasets. The owner's terms review is in
   docs/SOURCE_TERMS_REVIEW_2026-10.md (if missing, stop and ask).
3) Write docs/DATA_AVAILABILITY_DESIGN.md: which files leave the public tree, what replaces
   them (manifest: path, sha256, source, retrieval date, fetch/obtain instructions), how
   `make data-validate`, the root suite and CI keep working (options: a derived-only CI
   fixture the terms allow; machine-of-record-only tests with an owner-approved deselect list
   — never silently drop tests), and how other checkouts avoid losing local copies when the
   removal is pulled (back up to the vault first). Stop and wait for owner approval.
Phase 2 — only after I approve the design: implement it with `git rm --cached` plus
.gitignore so local copies stay; add the manifests; update docs/VERIFICATION_BASELINE.md only
if the owner approved a count change. Do not rewrite git history (separate owner decision A4).
```

### FIQ-2 · Branch ve worktree hijyeni (H2)
Dalga 1 (rapor) · Uygulama yalnız onaydan sonra

Bitti ölçütü: rapor var. Onaydan sonra yalnız merge edilmiş ve temiz olanlar silinmiş; detached
ya da merge edilmemiş hiçbir iş kaybolmamış.

```text
Task FIQ-2. Phase 1 — read-only report. List every worktree (`git worktree list --porcelain`)
with: path, HEAD, branch or detached, clean/dirty (`git -C <path> status --porcelain`),
whether HEAD is contained in any branch, whether it is merged into main, and last commit date.
List local branches merged into main, branches not merged, and any commit reachable only from
a detached worktree HEAD. Write the report to docs/process/REPO_HYGIENE_REPORT.md with a
proposed action per row. Change nothing. Stop and wait for approval.
Phase 2 — after approval only: `git worktree prune`; remove approved clean worktrees of merged
branches; delete approved merged local branches with `git branch -d` (never -D). Never touch
dirty worktrees, unmerged branches, archive/* branches, or a worktree an active session uses.
```

### FIQ-3 · Governance sadeleştirme (H1, K16)
Dalga 1

Bitti ölçütü: yeni çalışma kayıt şablonu var; süreç kuralı `docs/process/AGENTS.md` ve
`CLAUDE.md`'de birebir aynı; eski defterler silinmeden dondurulmuş.

```text
Task FIQ-3. Implement decision K16 of the plan without deleting any history.
1) Add docs/process/STUDY_RECORD_TEMPLATE.md: a one-page pre-registration template
   (question, estimand, data and cutoffs, analysis plan, multiplicity, stopping rule, what
   would change the conclusion) and a one-page results template (registered vs post-hoc,
   results, deviations, limitations).
2) Add a short section "Process after 2026-10-07" to docs/process/AGENTS.md and
   docs/process/CLAUDE.md (they must stay byte-identical): one pre-registration plus one
   results document per study; independent review only for analyses that enter a paper; no
   new R3/R4 task IDs; TASK_STATE.md and FINANCEIQ_AGENT_TASK_QUEUE.md are frozen ledgers
   (existing entries stay; new work is recorded with the template).
3) Add a one-line pointer at the top of TASK_STATE.md and FINANCEIQ_AGENT_TASK_QUEUE.md.
Run make docs-lint and the root suite (some tests check these files).
```

### FIQ-4 · Panel v2 ön kaydını park et (K8)
Dalga 1

Bitti ölçütü: `docs/PANEL_V2_STATUS.md` durumu, gerekçeyi ve Kernel'in yeniden kullanabileceği
parçaları kaydediyor; ön kaydın kendisi değişmemiş.

```text
Task FIQ-4. Read docs/PREREGISTERED_PANEL_V2_PIT.md and docs/panel_v2/* in full on branch
local/panel-v2-pit-prereg-6084b45f (commit e3d7012b; also on origin). Do not merge or modify it.
Write docs/PANEL_V2_STATUS.md on your branch from main: status PARKED as of 2026-10-07 per
plan decision K8; the reason (same annual cross-sectional question at low power; the Kernel
slice builds the shared KAP/statement base); which artefacts the Kernel slice can reuse
(source-manifest schema, PIT cell-evidence schema, applicability rules) and what would revive
it. Cite branch and commit SHA. If the prereg contains a commitment that parking would break
(e.g. a dated obligation), report it instead of parking.
```

### FIQ-5 · Paper 1 taslağı (P1-2, P1-3, P1-5, P1-6, P1-9)
Dalga 2 · Ön koşul: FIQ-9 başlamış olmalı (atıflar)

Bitti ölçütü: `docs/paper1/draft.md` 8–12 sayfa; bütün sayılar RESULTS.md ve PIT-v2 raporuyla
birebir aynı; yeni analiz yok; doğrulanmamış atıflar işaretli.

```text
Task FIQ-5. Draft Paper 1 in docs/paper1/draft.md (8–12 pages). Run no new analysis; every
number must match RESULTS.md and experiments/results_pit_v2/REPORT.md verbatim.
Structure: abstract; introduction; related work; data; original design; the audit
(publication lag, mixed adjustment bases, pre-listing rows); point-in-time protocol and guard;
corrected results; power and controls; limitations; reproducibility; conclusion.
Positioning (plan P1-2): the publication-lag rule is known in empirical finance (Fama–French
use a lag of at least six months for annual accounting data); the contribution is measuring how
much violating it inflates an ML-for-finance evaluation in an emerging market, plus a
machine-checked PIT guard with tests that inject future-available features. Framing (P1-3):
target trial emulation and immortal-time bias as the clinical analogue; leakage taxonomy;
multiple testing. State clearly what was registered and what was post-hoc
(docs/PREREGISTRATION_AMENDMENT_2026-10-04.md). Mark every citation not yet verified in
docs/paper1/references.bib as [UNVERIFIED].
```

### FIQ-6 · Kesin bildirim zamanı duyarlılığı (P1-4)
Dalga 4 · Ön koşul: KER-10a, FIQ-7

Bitti ölçütü: amendment, çalıştırmadan **önce** commit'lenmiş; çalıştırma o commit'ten yapılmış;
sonuç post-hoc duyarlılık analizi olarak raporlanmış.

```text
Task FIQ-6. Step 1 — before any run, write and commit an amendment
docs/PIT_EXACT_FILING_AMENDMENT.md: exact-filing-timestamp mode replaces statutory deadlines
where a Kernel snapshot gives a filing time; the rule for company-years without one (state it
in advance: excluded, not imputed, not deadline-filled — or justify another pre-specified rule);
outputs; how it will be reported (post-hoc sensitivity, never replacing the registered primary
result). Record the commit SHA. Step 2 — run experiments/pit_v2_evaluation.py in that mode
from the amendment commit, with Kernel snapshots pinned by content hash. Step 3 — append the
result to the PIT-v2 report as a sensitivity, with coverage (how many company-years had exact
times) and the amendment SHA.
```

### FIQ-7 · Kernel snapshot adaptörü (K-15, F2)
Dalga 3 · Ön koşul: KER-1 (contract 2.0.0)

Bitti ölçütü: FinanceIQ Kernel snapshot'larını dosyadan okuyor, contract major sürümünü ve
hash'i doğruluyor; FinanceIQ'dan Kernel'e yazma yolu yok.

```text
Task FIQ-7. Add a one-way, file-based reader for PIT Kernel snapshot envelopes (contract
2.0.0). Put it in experiments/pit/kernel_snapshot.py. It reads envelope JSON files from a
directory given by config or env, rejects unknown contract major versions and hash algorithms,
recomputes and checks content_hash, and exposes selected facts keyed by the full dimension key.
Copy only the Kernel's portable contract fixtures (synthetic) into tests/fixtures/kernel/ for
tests. Wire the PIT guard so that, when a snapshot directory is configured, filing times come
from it instead of data/pit/reporting_deadlines.csv and filing_dates_sample.csv; with no
snapshot configured, behaviour must stay byte-identical (prove it with a test). FinanceIQ never
writes to the Kernel.
```

### FIQ-8 · Hayatta kalma yanlılığını nicelleştir (F5, K15)
Dalga 2

Bitti ölçütü: Paper 1 limitler bölümüne girecek bir paragraf + tablo; kanıtı olmayan hiçbir
şey sayılmamış.

```text
Task FIQ-8. Using only evidenced membership sources in docs/evidence/bist_membership_*.csv and
the BIST membership audit documents in docs/, count for each year 2020–2025: index members with
evidence, how many are in the 81-company universe (data/config/), how many are not, and how many
of those are delisted or merged where evidenced. Unknown stays unknown (report it as a separate
column; never infer). Write docs/paper1/survivorship_bound.md with the table, one paragraph
for the paper, and the sources per number.
```

### FIQ-9 · Atıf doğrulama (P1-3, plan §13)
Dalga 1 · Araştırma preamble'ı ile ChatGPT (web)

Bitti ölçütü: `docs/paper1/references.bib` + doğrulama tablosu (yazar, yıl, başlık, dergi, DOI,
durum).

```text
Task FIQ-9. Verify each reference in §13 of docs/process/GAP_CLOSURE_PLAN_2026-10-07.md
(paste the list). For each: exact authors, year, title, venue, volume/pages, DOI; mark
VERIFIED or WRONG (with the correction). Then find 3–5 peer-reviewed works since 2015 on
look-ahead bias, publication-lag handling or data leakage in machine learning for asset
pricing, with one sentence on what each contributes. Output BibTeX plus a verification table.
```

### FIQ-10 · Hedef dergi kısa listesi (P1-8)
Dalga 1 · Araştırma preamble'ı ile ChatGPT (web)

```text
Task FIQ-10. For Borsa Istanbul Review, Finance Research Letters, The Journal of Financial Data
Science, and ICAIF / NeurIPS finance workshops (plus two venues you think fit better): scope
fit for a methodological audit paper with a negative result, article type and length limits,
open-access fee, typical time to first decision, and whether negative or replication results
are explicitly welcome. Give sources and a ranked recommendation.
```

---

## 6. Kernel kartları (KER) — kör oturum

### KER-0 · Devam eden rights işini bitir ve commit'le
Dalga 1 · Bu iş zaten başka bir oturumda sürüyor

Bitti ölçütü: `git status` temiz; testler yeşil. Diğer KER kartları bundan sonra başlar.

### KER-1 · Olgu boyut anahtarı + contract 2.0.0 (K-01, K-02, K12)
Dalga 2 · Ön koşul: KER-0

```text
Task KER-1. Problem: select_fact() in src/financeiq_pit/temporal.py filters only by entity_id
and field, while snapshot_envelope() treats (entity, security, field, unit, currency) as the
dimension, and docs/architecture/STORAGE_DESIGN.md says units belong in the dimension key.
A fact for the same field in TRY and in USD can therefore be selected by recency alone.
1) Define one canonical dimension key used by both functions: entity_id, security_id,
   field, period_type, period_basis, currency, unit, scale, consolidation, accounting_basis.
   Add the new fields to schemas/structured_fact.schema.json (required, with an explicit
   NOT_APPLICABLE value where a field does not apply) and to a new migration 0002.
2) select_fact takes the full key; candidates differing in any key field never compete.
   Add tests: TRY vs USD, consolidated vs solo, thousand vs unit scale.
3) Bump the exchange contract to 2.0.0 (request carries the full key; new hash-algorithm
   identifier if canonical bytes change). Keep the 1.0.0 fixtures as historical, add 2.0.0
   fixtures, update docs/architecture/INTEGRATION_CONTRACT.md, TEMPORAL_SEMANTICS.md and
   MIGRATIONS.md.
```

### KER-2 · Muhasebe temeli ve UMS 29 semantiği (K-03, K13)
Dalga 2 · Ön koşul: KER-1

```text
Task KER-2. Under IAS 29 (hyperinflation), a prior-year figure is republished in a later report
restated in the measuring unit current at the later balance-sheet date. That is a change of
measurement basis, not an error correction. Model it with accounting_basis values such as
TFRS_HISTORICAL and IAS29_RESTATED, plus a measuring_unit_date. A restated comparative is a
new fact with its own basis; it must never supersede the originally published value. Tests:
for one synthetic entity and period, the original value and the restated comparative are both
selectable at an as_of after both publications, each by its own basis; an as_of before the
restated report sees only the original. Document the rule in TEMPORAL_SEMANTICS.md.
```

### KER-3 · Dönem semantiği: birikimli ve dönemsel (K-04)
Dalga 2 · Ön koşul: KER-2

```text
Task KER-3. Turkish interim income statements are published cumulative year-to-date (3M, 6M,
9M, 12M). Add period_type (FY, Q1–Q4, H1, M9 …) and period_basis (CUMULATIVE, DISCRETE).
Published values keep their published basis. A discrete quarter is a derivative (e.g. Q4 =
12M − 9M), recorded in the derivatives relation with lineage to both inputs, and available only
once both inputs are public (known_at_upper = max of inputs). If an input is restated, the
derivative is recomputed as a new version; the old one stays. Tests for availability timing,
restatement and a missing input (no derivative; never imputed).
```

### KER-4 · CI + PostgreSQL + Python 3.12 (K-13, K-14, K18)
Dalga 2 · Ön koşul: O-1 (remote)

```text
Task KER-4. Add .github/workflows/verify.yml: Python 3.12, `pip install -e .[postgres]`, a
postgres:16 service container, PIT_TEST_DSN pointing at it, and
`python3 -m unittest discover -s tests -v`. All tests must run in CI (none skipped for a
missing DSN). Set requires-python to ">=3.12" in pyproject.toml and say so in README.md.
Add a secret-scan step that fails on committed keys or .env files.
```

### KER-5 · Sonuç körlüğünü makineyle zorla (K-16)
Dalga 2

```text
Task KER-5. Turn NO_NEW_OUTCOME_INSPECTION into tests. 1) A schema/test denylist: no field name
in schemas or fixtures may match outcome patterns (return, ret_, excess, alpha, ic, rank,
target, label, prediction, pnl, performance). Allowlist exceptions explicitly in the test with
a reason. 2) A test that the package imports nothing from the main FinanceIQ repository and has
no code path that writes outside its own database or the configured vault. 3) Document both
in docs/governance/SCOPE_AND_GATES.md.
```

### KER-6 · Kaynak hakları karar taslakları (K-10)
Dalga 2 · Ön koşul: KER-0 (rights şeması onunla genişliyor) · Çıktıyı O-9 onaylar

```text
Task KER-6. Draft one rights-decision record per source using the current
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
- TCMB EVDS: API with the owner's personal key (never committed); conditions per EVDS terms
  (owner to confirm); redistribution of raw series PROHIBITED unless terms allow.
- Yahoo chart endpoint: internal research only; raw retention in vault; redistribution
  PROHIBITED; status UNKNOWN on any operation the owner's terms review (O-4) does not cover.
- Fintables exports: MANUAL_ONLY download under the owner's own subscription; raw retention in
  vault; redistribution PROHIBITED.
- Borsa Istanbul DataStore: MANUAL_ONLY (automated requests are blocked by its WAF and log the
  owner out); raw retention in vault; redistribution PROHIBITED.
Put the drafts in a new directory and add a test that DRAFT records deny every operation.
```

### KER-7 · Şirket eylemleri, fiyat barları, işlem takvimi (K-05, K-06, K-07)
Dalga 3 · Ön koşul: KER-3

```text
Task KER-7. Add append-only relations in new migrations: pit_corporate_actions (type: cash
dividend, bonus issue, rights issue, split, reverse split, merger; ratio/amount; ex-date,
record date, known_at bounds, source document), pit_price_bars (raw OHLCV per listing and
session, source hash; no adjusted prices stored as source data) and pit_trading_calendar
(venue, session date, open/closed, known_at). Adjusted prices and adjustment factors exist only
as derivatives computed from raw bars plus corporate actions, with lineage. Synthetic tests:
bonus issue, rights issue (theoretical ex-rights price), cash dividend, a holiday, and a
corporate action announced after its ex-date (late knowledge). Never compute returns.
```

### KER-8 · Makro seri vintajları (K-08)
Dalga 3

```text
Task KER-8. Model macro time series (policy rate decisions, FX rates, CPI, weekly
non-resident securities flows) as facts with valid time (the period the value refers to),
release time (known_at, from the publisher's release calendar or announcement timestamp) and
vintage. Revisions append. A policy-rate decision is known at its announcement time, not at the
start of its effective date. Weekly flow statistics are known at their publication time, not at
week end. Synthetic tests for each case and for a revision.
```

### KER-9 · Gerçek evren için kimlik kayıtları (K-12)
Dalga 3 · Ön koşul: O-9 onayları

```text
Task KER-9. Allowed inputs from the main repository (lists only, no outcomes):
data/config/universe_public_40.csv, data/config/universe_training_bist100.csv,
data/config/bist100_candidates.csv. Build entity, security, listing and identifier-assignment
records for these companies, with ticker changes, mergers and delistings where a source
documents them (cite the source document; unknown stays unknown). Tests: resolving a ticker at
two different times; a reused ticker; an ambiguous symbol fails.
```

### KER-10 · İngest adaptörleri (K-09)
Dalga 4 · Ön koşul: O-9 (rights onayı), KER-11 (vault). KER-10c için O-5

Dört ayrı kart olarak başlat: 10a, 10b, 10c, 10d.

```text
Task KER-10a (KAP filing times). Input: the owner's SC5 KAP raw cache, copied into the vault
(path from the vault config). Parse disclosure metadata into source documents and filing-time
facts for financial-statement disclosures: publication timestamp with timezone, period, and
consolidation where stated. Idempotent, hashed, rights-checked against the approved KAP
decision; write a coverage report (company-years with an exact filing time vs without). Never
treat an empty or unparsed response as "no filing".

Task KER-10b (Yahoo daily prices). Input: raw chart JSON plus the provenance manifest
(symbol, url, accessed time, sha256). Load raw bars and dividend/split events into
pit_price_bars and pit_corporate_actions, known_at = session close in Europe/Istanbul. Integrity
checks only (gaps, duplicates, non-positive prices). Never compute returns.

Task KER-10c (EVDS). Fetch the macro series named in KER-8 with the owner's key from the
environment; store raw responses in the vault; load facts with release times.

Task KER-10d (BIST membership evidence). Load evidenced index-membership intervals from the
owner-provided evidence CSVs into listing/membership records with source lineage.
```

### KER-11 · Vault bağlantısı (K-11)
Dalga 3 · Ön koşul: O-3

```text
Task KER-11. Read the vault root from env (PIT_VAULT_ROOT); refuse to run if it is inside the
repository or inside an iCloud-synced directory. Every raw file has a manifest row (sha256,
size, source, rights decision id, acquired_at). Exports and snapshots never contain vault
paths. Tests use a temporary vault.
```

### KER-12 · Gerçek veriyle "golden" testler (K-17)
Dalga 4 · Ön koşul: KER-10a/b

```text
Task KER-12. Add a test module that runs only when PIT_VAULT_ROOT is set and is skipped (and
reported as skipped) otherwise. Golden cases from real data: a TRY vs USD field, a cumulative
quarter derivation, an IAS 29 restated comparative, a ticker change, a late filing, a bonus
issue. Each case cites its source document id. No raw values are committed; expected values
live in the vault next to the raw data.
```

---

## 7. Paper 2 kartları (P2) — ön kayıt modu

Ön kayıt gönderilene kadar hiçbir P2 oturumu gerçek açıklama tarihlerinde olağandışı getiri
hesaplamaz ya da onu sürprizle ilişkilendirmez.

### P2-A · Tasarım dokümanı ve OSF ön kayıt taslağı
Dalga 4 · FinanceIQ preamble'ı

```text
Task P2-A. Write docs/paper2/DESIGN.md and docs/paper2/OSF_PREREGISTRATION_DRAFT.md for an
event study of KAP financial-statement disclosures in Borsa Istanbul. Do not compute any
outcome. Cover: question (abnormal return around disclosures vs a pre-specified earnings
surprise; whether the IAS 29 transition changed that relation); event time from the KAP
timestamp (after-close disclosures move to the next session); surprise (seasonal random-walk
SUE on discrete quarterly earnings; earnings-announcement return as alternative; no analyst
consensus); expected-return model and estimation window ending before the event; inference
robust to event-date clustering (Kolari–Pynnönen adjustment, calendar-time portfolios,
clustered standard errors); placebo events and negative controls; a held-out period;
universe and exclusions; multiplicity; stopping rule; what result would count as null.
Use docs/process/STUDY_RECORD_TEMPLATE.md if it exists.
```

### P2-B · Pilot: belge, zaman damgası ve fiyat eşleşmesi
Dalga 5 · Ön koşul: KER-10a, KER-10b

```text
Task P2-B. For 3–5 companies, check that each KAP financial-statement disclosure maps to the
right trading session (timezone, after-close rule, holidays) and that prices exist around it.
Report mismatches and their causes. Allowed: timestamps, calendars, price availability.
Forbidden: computing abnormal returns at the true disclosure dates or relating anything to
surprise.
```

### P2-C · Kümelenmeyi koruyan güç simülasyonu
Dalga 5 · Ön koşul: P2-A, KER-10b, KER-7

```text
Task P2-C. Estimate power with the Brown–Warner approach: draw placebo event dates that keep
the real calendar clustering of disclosure dates (never use the true dates), inject abnormal
returns of chosen sizes, and apply the inference planned in P2-A. Report detection rates by
effect size and false-positive rates with no injection. Seeded and reproducible.
```

### P2-E · Ana analiz
Ön koşul: O-10 (OSF kaydı)

Ön kayda birebir uyarak çalıştır. Sapmalar ayrı bir bölümde raporlanır.

---

## 8. Sonraya bırakılanlar (S)

Paper 2 pilotundan sonra değerlendirilir; şimdilik kart yok: fon akışı çalışması (S1), sponsor
veri talebi spesifikasyonu (S2), hukuki çerçeve (S3), CDS ve kredi spread'i kaynağı (S4).
Ayrıntılar: plan §7.
