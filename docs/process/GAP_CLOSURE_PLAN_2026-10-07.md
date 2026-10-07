# FinanceIQ + PIT Kernel — Eksik Kapatma ve Araştırma Planı

Tarih: 2026-10-07 · Durum: taslak, sahibin onayına açık · Kapsam: `Salih04/capstone-financeIQ`
(FinanceIQ) ve `financeiq-pit-kernel`

Girdiler: iki reponun incelenmesi, finans uzmanı görüşü, Codex incelemesi. Hedef: Uni Basel
Data Science yüksek lisansı süresince savunulabilir bir araştırma ve paper. Ürün hedef değil.

Bu bir araştırma planıdır; yatırım tavsiyesi değildir.

> **Kapsam değişikliği (2026-10-07, aynı gün):** FinanceIQ artık açık bir araştırma programı;
> kapsam `docs/process/RESEARCH_CHARTER.md`'de ve bu planla çeliştiği yerde o geçerli. Geçersiz
> kalan kararlar: K1, K4, K6, K8, K15 (charter §8). Görev kartları iki dosyada:
> `docs/process/TASKS_FINANCEIQ_2026-10-07.md` ve `docs/process/TASKS_PIT_KERNEL_2026-10-07.md`.
> A1, A2, A5, A6 yapıldı; A3 FIQ-09 kartına taşındı.
>
> **Kernel oturumlarına bu dosyayı verme:** sonuç sayıları içeriyor. Kernel'e yalnızca kernel
> görev dosyasındaki preamble ve kart prompt'ları gider.

---

## 0. Özet

FinanceIQ'nun bugünkü değeri tahmin değil, kendi yayın gecikmesi hatasını yakalayıp düzelten
denetim kaydı: eşit ağırlıklı IC +0,150 (p = 0,017) → PIT düzeltmesiyle +0,031 (p = 0,63).
Yıllık kesitsel tasarım gerçekçi büyüklükteki etkileri göremiyor (80 % güçte tespit edilebilir en
küçük |IC| ≈ 0,19). Daha fazla model veya özellik bunu değiştirmez.

Plan dört adımdır:

1. Önce veri/kod kaybı ve dürüstlük risklerini kapat (Bölüm A).
2. FinanceIQ'yu ürün olarak dondur; araştırma hattı devam etsin.
3. Kernel'i Paper 2'nin ihtiyacı kadar gerçek veriyle kur ve FinanceIQ'ya erken, tek yönlü bağla.
4. Paper 1 (audit) → Paper 2 (bilanço açıklaması olay çalışması, UMS 29) → Paper 3 (fon
   akışları / sponsor verisi).

---

## 1. Kararlar (seçildi)

Her satırda seçilen seçenek, reddedilen alternatif ve gerekçe var. Değiştirmek istediğin karar
olursa sonraki bölümler ona göre güncellenir.

| # | Konu | Seçilen | Reddedilen | Gerekçe |
|---|---|---|---|---|
| K1 | FinanceIQ'nun rolü | Ürün olarak dondur; araştırma hattı devam | Tamamen durdurmak; uygulamayı PIT verisine yeniden bağlamak | Audit kaydı Paper 1'in malzemesi. Uygulamayı yeniden bağlamanın bilimsel getirisi yok |
| K2 | Repo yapısı | İki repo ayrı kalır | Kernel'i FinanceIQ'ya gömmek | Kernel sonuç görmez. Bu, klinik denemelerdeki körlemenin karşılığı ve yöntem bölümünde yapısal bir savunma |
| K3 | Entegrasyon zamanı | Erken, tek yönlü, dosya tabanlı snapshot (kernel → FinanceIQ) | "Kernel tamamen bitince" tek seferde entegrasyon | Gerçek veri şemayı kırar. Kullanıcısı olmayan altyapının bitiş çizgisi olmaz |
| K4 | Kernel v1 "bitti" tanımı | Paper 2 diliminin gerçek veriyle as-of sorgulanabilmesi | Side-project registry'deki 9 yeteneğin tamamı | Geri kalanı yıllar alır; ihtiyaç doğdukça eklenir |
| K5 | Legacy uygulama yüzeyleri | Görünür "geri çekildi (PIT öncesi)" etiketi + API'de `evidence_status` bayrağı; yeniden bağlama yok | Kapatmak; yeniden bağlamak | Kapatmak backend ve e2e testlerini kırar. Etiket ucuz ve dürüst, audit hikâyesini de gösterir |
| K6 | Paper sırası | P1 audit (taslak şimdi, sayılar dilim 1 sonrası) → P2 → P3 | Önce büyük veri altyapısı | P1'in malzemesi hazır; danışmana somut bir şeyle gidilir |
| K7 | Paper 2 sorusu | Bilanço açıklaması sonrası fiyat tepkisi × önceden tanımlı sürpriz; UMS 29 geçişi ikincil soru | Fon akışı ayrıştırması | Fon verisi ağır. Olay çalışması dar ve gücü yüksek |
| K8 | Panel v2 PIT ön kaydı (yıllık genişletilmiş panel; branch `local/panel-v2-pit-prereg-6084b45f`) | PARK: origin'de tarihsel kayıt olarak kalır | Şimdi uygulamak | Aynı yıllık soru, düşük güç. Kernel dilimi aynı KAP/tablo tabanını kurduğu için sonra ucuz canlanır |
| K9 | KAP edinimi | SC5 kodu FinanceIQ'da donmuş halde kalır (önce kurtarılır); çıktısı kernel'e ingest edilir; yeni edinim kodu kernel'de yazılır | SC5'i kernel'e taşımak | Yaklaşık 18 bin satırı taşımak pahalı. Kayıt sistemi kernel olur |
| K10 | Kaynak hakları | Kernel'in kaynak başına rights kaydı korunur; `FI-SOURCE-OWNER-AMENDMENT-01` politika dayanağı olarak doldurulur | Kernel kapısını gevşetmek; her kaynak için dış izin aramak | İki repo'nun governance'ı çelişiyor (kernel: kaynak başına karar; FinanceIQ: genel owner kararı). Bu ikisini uzlaştırır |
| K11 | Public repo'daki ham vendor dosyaları | HEAD'den kaldır; hash + fetch script + manifest bırak. Geçmiş temizliği ayrı karar (koşullar okunduktan sonra) | Olduğu gibi bırakmak | Kendi amendment'ın ham vendor dosyalarının yayımlanmasını yasaklıyor. Hakem de sponsor da görür |
| K12 | Kernel contract sürümü | 2.0.0'a geç: istek tam boyut anahtarını taşır | 1.x'e opsiyonel alan eklemek | Anlam değişikliği major sürüm demek. Henüz tüketici olmadığı için en ucuz an şimdi |
| K13 | UMS 29 karşılaştırmalı yeniden ifade | Yeni ölçüm temeli (yeni boyut) olarak modelle; supersession değil | Düzeltme gibi supersede etmek | Bu bir hata düzeltmesi değil, birim değişikliği. Supersede edilirse eski değer as-of sorgularında yanlışlıkla kaybolur |
| K14 | Ön kayıt yeri | Paper 2 için OSF (zaman damgalı, public); repo içi ön kayıtlar tarihsel kayıt olarak kalır | Yalnız repo içi | Hakemler OSF/AsPredicted'ı tanır |
| K15 | Hayatta kalma yanlılığı | P1'de "çözülmedi" + nicel sınır. P2'de kısa pencereli olay çalışması + dışlanan firmaların sayılması | Önce tam evren rekonstrüksiyonu | Evren rekonstrüksiyonu büyük ölçüde manuel arşiv işi (`docs/UNIVERSE_HISTORY_SOURCING_SPIKE.md`) |
| K16 | Süreç | Çalışma başına 1 ön kayıt + 1 sonuç dokümanı; bağımsız inceleme yalnız paper'a giren analizlerde; yeni R3/R4 ID'si açılmaz | Mevcut yoğun governance | Yaklaşık 41 bin satır Markdown; asıl hız darboğazı bu |
| K17 | Makro veri | Yıllık makro kesitsel modele girmez. Günlük/haftalık EVDS serileri yayın zamanlarıyla kernel'e | Yıllık makroyu özellik yapmak | Aynı yıl içinde bütün şirketler için sabit; sıralamaya sıfır bilgi ekler |
| K18 | Python sürümü | İki repoda da 3.12 | Kernel'de 3.9 tabanı | Backend Docker 3.12; tek ortam |

---

## 2. Bölüm A — Acil (bu hafta): kayıp ve dürüstlük riskleri

| ID | İş | Neden | Bitti ölçütü | Sahibi |
|---|---|---|---|---|
| A1 | SC5 commit'lerini bir branch'e bağla ve push et | SC5 KAP edinim işi (yaklaşık 18 bin satır; `2958abe9` → `2a031896`) hiçbir branch'te değil. Yalnızca detached HEAD duran `sc5-batch1-cap-exhaustion-guard-20260930` worktree'sinde. Worktree temizlenirse commit'ler erişilemez olur | `git for-each-ref --contains 2a031896` bir branch gösterir ve branch origin'de | Ajan (onayınla) |
| A2 | SC5 ham önbelleğini ikinci konuma yedekle | `~/Desktop/Backups/FinanceIQ_Docs/batches/` tek kopya ve iCloud senkronlu Desktop altında | İkinci konumda kopya; SHA-256 manifesti eşleşiyor | Sen |
| A3 | Ham vendor dosyalarını public HEAD'den kaldır | 15 Fintables XLSX (`data/raw/`) ve 246 Yahoo ham JSON public repoda takip ediliyor. `FI-SOURCE-OWNER-AMENDMENT-01` §1.2 bunu yasaklıyor | `git ls-files data/raw` yalnız README döner. Manifest + hash + fetch script kalır. Testler ve `make data-validate` yeşil | Sen (koşulları oku) + Ajan |
| A4 | Git geçmişi temizliği kararı | HEAD'den silmek dosyayı geçmişten silmez | Fintables/Yahoo koşullarına göre yazılı karar (temizle / bırak, gerekçesiyle). Geçmiş yeniden yazımı geri alınamaz, ayrı onay ister | Sen |
| A5 | Legacy yüzeylere "geri çekildi" etiketi | PIT öncesi veriyi okuyanlar: `backend/app/services/research/data.py` (eski `stocks_2020_2025.csv`, kendi yorumu "UNRELIABLE" diyor), `forecasting_csv_service.py`, `research_agent.py`, `skeptic_service.py`, `yearly_stocks` tablosu | İlgili her yanıtta `evidence_status: "withdrawn_pre_pit"`; UI'da banner; bunu doğrulayan backend testi | Ajan |
| A6 | 2026 ileriye dönük ön kaydı UI ve dokümanda kontrol et | Donmuş sıralama PIT öncesi production servisiyle üretildi | Hiçbir yüzey onu PIT kanıtı gibi sunmuyor | Ajan |

---

## 3. Bölüm F — FinanceIQ veri eksikleri

| ID | İş | Neden | Bitti ölçütü | Bağımlılık |
|---|---|---|---|---|
| F1 | Kesin bildirim zamanları: 323 şirket-yıl (şu an 6) | Yasal son tarih kaba bir yaklaşım. P1 duyarlılık analizi ve P2 için şart | Kernel snapshot'ı 323 şirket-yılın kapsamını raporlar; eksikler null kalır | A1, K-09a |
| F2 | Elle tutulan `data/pit/*.csv` tablolarını kernel snapshot'ıyla değiştir | Çift kaynak riski | PIT guard kernel snapshot'ından okur; contract major + hash pinli | K-15 |
| F3 | Pay sayısı geçmişi (şu an 323 satırın 164'ü tek temelde geçerli) | Piyasa değeri, F/K, PD/DD buna bağlı | KAP sermaye değişikliği bildirimlerinden, kernel'de sürümlü | K-05 |
| F4 | Şirket eylemleri: bedelli, bedelsiz, temettü, bölünme | Yahoo `adjclose` bedelli sermaye artırımını güvenilir işlemiyor | Ham kapanış + olay kayıtlarından repo içinde türetilmiş ayarlama; Yahoo `adjclose` ile fark raporu | K-05, K-06 |
| F5 | Hayatta kalma / tarihsel evren | 81 şirket 2026'da, o günkü listelerden seçildi | P1: nicel limit cümlesi. P2: kural tabanlı evren + dışlanan şirket sayısı | Stage-A sınırının doğrulanması |
| F6 | BIST işlem takvimi | "İlk işlem günü" kuralları buna dayanıyor | Tatil takvimi kernel'de, testli | K-07 |
| F7 | EVDS günlük/haftalık makro seriler | P2'nin kontrol faktörleri | Politika faizi (karar duyuru zamanıyla), USD/TRY, gösterge tahvil faizi (varlığı doğrulanacak), haftalık yerleşik olmayanların hisse alım-satımı (yayın gecikmesiyle) | K-08, K-10 |
| F8 | Günlük gösterge ve sektör endeksleri | Olay çalışmasında piyasa ve sektör modeli | XU100 + sektör endeksleri günlük; kaynak ve rights kaydı var | K-06 |
| F9 | Çeyreklik finansal tablolar: birikimli → dönemsel | P2'nin sürpriz ölçüsü (SUE). KAP çeyrekleri birikimli yayımlanıyor (3A, 6A, 9A, 12A) | Q4 = 12A − 9A türetimi testli; birikimli bayrağı kernel'de | K-04 |

---

## 4. Bölüm K — PIT Kernel eksikleri

| ID | İş | Neden | Bitti ölçütü |
|---|---|---|---|
| K-01 | Olgu boyut anahtarı: entity, security, field, period_type, period_basis (birikimli/dönemsel), currency, unit, scale, consolidation (konsolide/solo), accounting_basis (TFRS / UMS 29 + ölçüm birimi tarihi) | `select_fact` (`src/financeiq_pit/temporal.py:90`) yalnız entity + field ile filtreliyor. `snapshot_envelope` ise unit + currency'yi de boyut sayıyor. `STORAGE_DESIGN.md` "units belong in the dimension key" diyor ama bu uygulanmamış | İki fonksiyon tek bir anahtar fonksiyonunu kullanır; TRY/USD testi doğru kaydı seçer ya da belirsizlik hatası verir; migration `0002` |
| K-02 | Contract 2.0.0 (K12) | İstek boyut anahtarını taşımalı | Şema, fixture'lar ve hash algoritması kimliği güncel; 1.0.0 fixture'ları tarihsel kayıt olarak kalır |
| K-03 | UMS 29 modellemesi (K13) | FY2022 değeri, FY2023 raporunda farklı ölçüm birimiyle yeniden yayımlanır | Testte iki değer de as-of sorgusunda kendi temeliyle seçilir |
| K-04 | Dönem semantiği | KAP çeyrekleri birikimli | `period_type` + `period_basis` alanları; türetilmiş dönemsel değer lineage ile derivative olarak tutulur |
| K-05 | Şirket eylemleri tablosu | Migration'da yok | `pit_corporate_actions`: tip, oran, hak kullanım tarihi, kayıt tarihi, known_at, kaynak |
| K-06 | Fiyat depolama | 82 sembol × yaklaşık 2.400 işlem günü; fact tablosu bunun için verimsiz | Ayrı append-only `pit_price_bars` (ham OHLCV + kaynak hash). Ayarlanmış fiyat yalnız türetilmiş olarak var |
| K-07 | İşlem takvimi tablosu | Takvim kurallarının tek kaynağı olmalı | Tablo + testler |
| K-08 | Makro seri vintajları | EVDS serileri revize edilebilir | Yayın zamanı + vintage; revizyonlar append edilir |
| K-09 | İngest adaptörleri: (a) KAP ← SC5 önbelleği, (b) Yahoo günlük ← mevcut ham JSON + `data/pit/yahoo_daily_provenance.csv`, (c) EVDS, (d) BIST üyelik kanıt CSV'leri (`docs/evidence/`) | Kernel'de gerçek veri yok | Her adaptör idempotent, hash'li, rights kontrollü ve kapsam raporu üretiyor |
| K-10 | Rights kayıtları (K10): KAP, EVDS, Yahoo, Fintables, BIST DataStore | Kapı `UNKNOWN` durumunda reddediyor | 5 karar dosyası. DataStore `MANUAL_ONLY`. KAP otomatik erişimi koşullu (istekler arası 3–8 sn; boş gövde = `SEARCH_INCOMPLETE`, asla sıfır sonuç değil). Bütün kaynaklarda redistribution `PROHIBITED` |
| K-11 | `PRIVATE_LOCAL_RAW` vault konumu | Ham bayt git'e giremez | iCloud dışında, şifreli disk + yedek; konum repo dışındaki bir config'te |
| K-12 | Kimlik: önce 81 şirket, sonra genişletilmiş evren için entity/security/listing; ticker değişimleri, birleşmeler | Ticker birincil anahtar olamaz | Gerçek vakalarla sembol çözümleme testleri |
| K-13 | PostgreSQL testleri CI'da | 3 test DSN yokken atlanıyor | GitHub Actions'ta `postgres:16` servisiyle bütün testler koşuyor |
| K-14 | Kernel CI + Python 3.12 pin (K18) | Kernel'de CI yok | Verify workflow yeşil |
| K-15 | FinanceIQ adapter (tüketici taraf) | Entegrasyon yok | FinanceIQ `experiments/` snapshot'ı dosyadan okur, contract major + `content_hash` pinler, bilinmeyen major sürümü reddeder |
| K-16 | Sonuç körlüğünü makineyle zorla | Kural şu an yalnız metin | Kernel şemasında getiri/IC/hedef alan adları için denylist testi. FinanceIQ'dan kernel'e yazma yolu olmadığını gösteren test |
| K-17 | Gerçek veri "golden" testleri | Sentetik fixture'lar gerçek tuzakları yakalamaz | Vault'a bağlı, CI dışı, işaretli test seti: TRY/USD, birikimli çeyrek, UMS 29, ticker değişimi, geç bildirim |

---

## 5. Bölüm P1 — Paper 1 (audit)

| ID | İş | Not |
|---|---|---|
| P1-1 | Danışman / ortak yazar bul | Uni Basel'de Data Science veya finans/ekonometri tarafı. Paper 1 taslağı ve Paper 2 önerisiyle git |
| P1-2 | Konumlama | Fama–French (1992) yıllık muhasebe verisini en az 6 ay gecikmeyle kullanır; kural ampirik finansta biliniyor. Katkı "yeni bir hata keşfettik" değil: ML-for-finance çalışmalarında bu ihlalin gelişmekte olan bir piyasadaki büyüklüğünü ölçmek ve makineyle kontrol edilen bir PIT guard sunmak |
| P1-3 | Çerçeve | Target trial emulation ve immortal-time bias analojisi (Hernán & Robins 2016); sızıntı sınıflaması (Kapoor & Narayanan 2023); çoklu test (Harvey, Liu & Zhu 2016) |
| P1-4 | Kesin zaman damgası duyarlılığı | Çalıştırmadan **önce** amendment olarak kaydet; sonucu post-hoc duyarlılık analizi olarak raporla |
| P1-5 | Güç tablosu ve negatif/pozitif kontroller | Mevcut; paper formatına taşınır |
| P1-6 | Limitler | Hayatta kalma, 3 test yılı, tek enflasyon rejimi, kesin bildirim zamanlarının kapsamı |
| P1-7 | Replikasyon paketi | Kod + lisans içindeki türetilmiş veri + Zenodo DOI. A3'ten sonra |
| P1-8 | Hedef kısa listesi (kapsam, ücret ve süre doğrulanacak) | Borsa Istanbul Review; Finance Research Letters; Journal of Financial Data Science; ICAIF / NeurIPS workshop'ları |
| P1-9 | Taslak | 8–12 sayfa |

---

## 6. Bölüm P2 — Paper 2 (bilanço açıklaması olay çalışması)

| ID | İş | Not |
|---|---|---|
| P2-1 | Soruyu sabitle | "KAP finansal tablo bildirimleri sonrası olağandışı getiri, önceden tanımlı sürprizle nasıl ilişkili? UMS 29 geçişi bu ilişkiyi değiştirdi mi?" |
| P2-2 | Olay zamanı | KAP bildirim saati esas alınır; seans sonrası gelen bildirimde olay günü t+1 |
| P2-3 | Sürpriz ölçüsü | Mevsimsel rastgele yürüyüş SUE (dönemsel çeyreklik kâr). Alternatif: açıklama günü getirisi (EAR). Analist konsensüsü ücretsiz değil, kullanılmaz |
| P2-4 | Beklenen getiri modeli | Piyasa / faktör modeli; olay öncesi tahmin penceresiyle PIT beta; EVDS makro kontrolleri |
| P2-5 | Çıkarım | Bildirimler yasal son tarihlere yığıldığı için olay günleri kümelenir. Kolari–Pynnönen düzeltmesi + takvim-zamanı portföyü; şirket ve tarihe göre kümelenmiş standart hatalar |
| P2-6 | Pilot (sonuçlara bakmadan) | 3–5 şirkette belge, zaman damgası ve fiyat eşleşmesinin doğrulanması |
| P2-7 | Güç simülasyonu | Kümelenme yapısı korunarak enjekte edilmiş CAR ile |
| P2-8 | OSF ön kaydı | Hiçbir sonuç hesaplanmadan |
| P2-9 | Plasebo olaylar ve negatif kontroller | Ampirik p-değeri kalibrasyonu (Schuemie vd. 2018'deki fikir) |
| P2-10 | Ayrı tutulmuş test dönemi | Ön kayıtta tanımlanır |
| P2-11 | Evren | Pilot: 81 şirket. Ana analiz: Stage-A sınırı ("351 üye"; tam tanımı doğrulanacak). Kapanmış şirketlerin fiyat kapsamı ölçülür ve raporlanır |
| P2-12 | Yöntem bölümünde körleme | Kernel sonuçları hiç görmedi; veri katmanı sonuçtan bağımsız kuruldu |

---

## 7. Bölüm S — Paper 3 / sponsor (sonra)

Zamanlama: Paper 2 pilotundan sonra.

| ID | İş | Not |
|---|---|---|
| S1 | Fon akışı çalışması | Coval & Stafford (2007) çerçevesi. TEFAS ve KAP fon portföy raporları yayın gecikmeleriyle kullanılır (dönem sonu ≠ yayın tarihi) |
| S2 | Sponsor veri talebi spesifikasyonu | Alanlar, frekans, dönem, anonimleştirme |
| S3 | Hukuki çerçeve | KVKK, 5411 sayılı Bankacılık Kanunu md. 73 (sır saklama), NDA, yayın hakkı maddesi, veri ortamı (kernel vault veya bankanın kendi altyapısı) |
| S4 | CDS ve kredi spread'i | Ücretsiz ve meşru bir günlük kaynak yok; sponsor kaynağı (Bloomberg/Refinitiv) gerekir |

---

## 8. Bölüm H — Süreç ve hijyen

| ID | İş | Not |
|---|---|---|
| H1 | Governance sadeleştirme (K16) | `TASK_STATE.md` dondurulur; yeni çalışmalar için kısa kayıt formatı |
| H2 | Branch ve worktree temizliği | 289 branch, 81 worktree (7'si prunable). Önce detached HEAD'deki işler branch'e bağlanır (A1), sonra temizlik |
| H3 | Repoları iCloud senkronlu Desktop dışına taşı | Senkron "x 2" kopyaları üretip glob'ları bozuyor |
| H4 | Oturum ayrımı | Kernel oturumları FinanceIQ sonuç dosyalarını okumaz (bkz. kernel `docs/governance/INCIDENT_EVENTS.jsonl`) |
| H5 | Doğrulama tabanı | `docs/VERIFICATION_BASELINE.md` güncel tutulur |
| H6 | Haftalık zaman bütçesi | Ders yüküne göre sabit bir çalışma bloğu |

---

## 9. Sıralama

| Faz | Zaman | İşler |
|---|---|---|
| 0 | Bu hafta | A1, A2, A5, K-10 taslağı; A1'den sonra H2 |
| 1 | Ekim–Kasım | A3, A4, A6; K-01 → K-04; K-13, K-14; P1-1, P1-2, P1-3; P1-9 taslağı; H1, H3 |
| 2 | Kasım–Ocak | K-05 → K-12, K-15 → K-17; F1 → F9; P1-4, P1-7 |
| 3 | Şubat | P2-1 → P2-8; P1 gönderimi |
| 4 | Bahar | P2 ana analiz; S1–S4 değerlendirmesi |

Kritik bağımlılık zincirleri:

- A1 → K-09a → F1 → P1-4
- K-01 → K-02 → K-15 → F2
- F4, F8, F9, K-07 → P2-6 → P2-7 → P2-8

---

## 10. Bilinçli olarak yapılmayacaklar

- Derin öğrenme (örneklem küçük).
- Alfa veya getiri tahmini iddiası.
- CDS ya da fiyat için kazıma (investing.com vb.).
- Uygulamanın yeniden inşası; kernel için public API.
- Paper 2 pilotundan önce banka verisi.
- Kernel registry'sindeki bütün yetenekleri ilk dilimde yapmak.
- Yıllık makroyu kesitsel özellik yapmak.
- BIST DataStore otomasyonu (WAF engelliyor; dosyalar manuel indirilir).

---

## 11. Doğrulanması gerekenler

- 40 şirketlik public kohortun seçim kuralı. `data/raw/README.md` yıllık dosyaları "winner
  cohort" diye tanımlıyor; kohort getiriye göre seçildiyse bu, hayatta kalmadan ayrı ve daha
  ağır bir seçim yanlılığı (görev kartı FO-1, FIQ-16).
- Fintables ve Yahoo kullanım koşulları (A3, A4).
- Stage-A "351 üye" sınırının tam tanımı.
- EVDS'de gösterge tahvil faizi serisinin varlığı.
- KAP bildirim saatinin bütün dönemlerde mevcut olup olmadığı.
- Kapanmış şirketler için ücretsiz günlük fiyat kaynağı (Yahoo 404 döndürüyor).
- Hedef dergilerin kapsam, ücret ve süreleri.
- Aşağıdaki atıfların tamamı (hafızadan yazıldı; gönderimden önce kontrol edilmeli).
- Panel v2 ön kaydı tamamen okunmadı; K8'deki PARK kararı başlık ve durum tablosuna dayanıyor.

---

## 12. Bu planın dayandığı kanıtlar

- FinanceIQ: `README.md`, `RESULTS.md`, `docs/process/PRD.md`, `docs/limitations_register.md`,
  `docs/SOURCE_USE_OWNER_AMENDMENT.md`, `docs/PREREGISTERED_DATA_EXPANSION_STAGE_A.md`,
  `docs/thesis/DATA_FEASIBILITY.md`, `docs/side_projects/SIDE_PROJECT_REGISTRY.md`,
  `data/trusted_raw/macro/`, `data/pit/`, backend servisleri (A5'te listelenenler),
  `experiments/pit/panel.py`, `.github/workflows/verify.yml`.
- Git: `git for-each-ref --contains 2a031896` (boş), `git worktree list`,
  `git ls-files data/raw`, `gh repo view` (visibility: PUBLIC).
- Kernel: `README.md`, `AGENTS.md`, `docs/architecture/*`, `docs/governance/*`,
  `src/financeiq_pit/temporal.py`, `schemas/structured_fact.schema.json`,
  `migrations/0001_pit_core.sql`.
- Codex'in bu turdaki test çalıştırmaları (Codex'in raporu; burada yeniden çalıştırılmadı):
  backend 552 geçti, kernel 17 geçti / 3 atlandı, `make data-validate`, `claims-lint`,
  `docs-lint` geçti.

---

## 13. Kaynaklar (hafızadan; doğrulanacak)

- Brandt, Kishore, Santa-Clara & Venkatachalam (2008). Earnings announcements are full of surprises.
- Chen, Roll & Ross (1986). Economic forces and the stock market. *Journal of Business*.
- Coval & Stafford (2007). Asset fire sales (and purchases) in equity markets. *JFE*.
- Fama & French (1992). The cross-section of expected stock returns. *Journal of Finance*.
- Harvey, Liu & Zhu (2016). … and the cross-section of expected returns. *RFS*.
- Hernán & Robins (2016). Using big data to emulate a target trial when a randomized trial is not
  available. *American Journal of Epidemiology*.
- Kapoor & Narayanan (2023). Leakage and the reproducibility crisis in machine-learning-based
  science. *Patterns*.
- Kolari & Pynnönen (2010). Event study testing with cross-sectional correlation of abnormal
  returns. *RFS*.
- MacKinlay (1997). Event studies in economics and finance. *Journal of Economic Literature*.
- Morck, Yeung & Yu (2000). The information content of stock markets: why do emerging markets have
  synchronous stock price movements? *JFE*.
- Schuemie, Hripcsak, Ryan, Madigan & Suchard (2018). Empirical confidence interval calibration for
  population-level effect estimation studies in observational healthcare data. *PNAS*.
- Vuolteenaho (2002). What drives firm-level stock returns? *Journal of Finance*.
- Codex'in önerdikleri (ilgili çalışma olarak): Miotto vd. 2016 (Deep Patient), Argelaguet vd. 2020
  (MOFA+), Chernozhukov vd. (Double/Debiased ML), Brodersen vd. 2015 (CausalImpact), Melnychuk vd.
  2022 (Causal Transformer).
