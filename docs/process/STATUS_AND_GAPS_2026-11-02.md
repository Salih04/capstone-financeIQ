# Durum ve eksikler — 2026-11-02

Kesit: FinanceIQ `main` `a8f19049`, PIT Kernel `main` `33f5d31`. Kaynak: iki reponun git
geçmişi ve `main` üzerindeki dokümanlar. Research support only; not investment advice.
Bu dosya FinanceIQ planıdır; kernel oturumlarına verilmez.

## Kritik yol

1. **Paper 1** gönderime en yakın iş: taslak var, eksikler owner kararları ve birleştirme.
2. **Veri omurgası** (Kernel): kod büyük ölçüde hazır, ama henüz hiçbir gerçek veri yüklenmedi.
   Paper 2, Study 3 ve olası banka çalışması buna bağlı.
3. **Paper 2**: kayıt öncesinde 20 kapı var (`docs/paper2/REGISTRATION_READINESS_AUDIT.md`
   G01–G20); kapıların çoğu owner kararı.

## A. Paper 1 (FIQ-13/14/15/16)

| Eksik | Durum | Kapatan |
|---|---|---|
| Taslak (`4b6c8823`, ~4.000 kelime) ve FIQ-13/14/16 kanıtı (`7b444a35`) yalnız yerel branch'lerde; remote'ta da `main`'de de yok | Tek kopya riski | Push + PR + merge |
| Dergi seçimi, YZ kullanım beyanı, çıkar çatışması / biyografi | UNSET | Owner (`docs/paper1/readiness/submission_readiness.md` §2) |
| FO-1 seçim beyanı (40/81 kohortu nasıl seçildi) | Yok; seçim bölümü "unknown" diyor | Owner, 15 dk |
| Veri erişilebilirlik beyanı | FO-4 ve FIQ-09'a bağlı | FO-4 notu + FIQ-09 Faz 1 |
| Veri doğruluğu örneklem denetimi | Öneri var (`docs/paper1/DATA_ACCURACY_AUDIT_PROPOSAL.md`), çalıştırılmadı | FinanceIQ |
| Çift kör hakemlik için anonimleştirme | Taslak FinanceIQ adını, repo yollarını, SHA'ları içeriyor | FinanceIQ, dergi seçiminden sonra |
| BIST'e özgü literatür | Hiç atıf yok | FIQ-13 ek turu |

## B. Veri omurgası (PIT Kernel)

| Aile | Kod | Gerçek veri | Eksik |
|---|---|---|---|
| Üyelik (3184, KER-09/10/13e) | Var; layout v1 `#21` | Yok | 2025 Q1 pilotunu çalıştır; sonra 2017–2024 dosyaları (KO-5) |
| KAP bildirim zamanları ve tablo değerleri (KER-13a/b) | **Yok** | Yok | En büyük boşluk; SC5 KAP ham önbelleği owner yedeğinde. Paper 2'nin olay zamanları ve kazançları buna bağlı |
| Günlük fiyatlar (KER-13c) | KER-07 şeması var, adaptör yok | Yok | Kaynak kararı verildi: LSEG birincil, DataStore çapraz kontrol (KO-6/KO-7) |
| Makro seriler, EVDS (KER-13d) | KER-08 şeması var, adaptör yok | Yok | KO-3 EVDS anahtarı (durumu doğrulanmadı) |
| CDS ve tahvil faizleri (KER-13h, yeni) | KER-08 şeması | Yok | KO-6 |
| Endeks seviyeleri (KER-16) | Var | Yok | Ürünün ücretsiz olup olmadığı doğrulanmadı |
| Snapshot dışa aktarımı (KER-15) | Sentetik | — | Gerçek veriyle ilk snapshot |
| Golden testler (KER-14) | Yok | — | İlk gerçek aileden sonra |

Süreç notu: tek bir dosya (3184) için sekiz mimari doküman yazıldı. Yeni kaynaklar
"önce profil, sonra layout sözleşmesi, sonra sentetik ikiz" yolunu izler; süreç bu kadar
uzamaz.

## C. Paper 2 (FIQ-19 → 25)

- Kayıt öncesi 20 kapının çoğu owner kararı: G01, G04, G06, G07, G10, G12, G13, G14, G16,
  G17 UNSET. Bunlar **tek oturumda** karara bağlanabilir: varsayılanlar yazılır, owner
  tek seferde onaylar.
- Veri kapıları (G02, G03, G05, G19) veri omurgasını bekliyor: U1, KAP zamanları, fiyatlar.
- G20 (kaynak hakları) KAP, BIST duyuruları ve 3184 için kapalı. LSEG için lisans kaydı
  KO-6 ile gelir.

## D. FinanceIQ altyapısı

- FIQ-06 `UNIVERSE_RULE.md` ve FIQ-11 `PROTOCOL.md`: `main`'de yalnız kapsamlı owner
  kararları var (`docs/research/OWNER_DECISION_ADDENDUM.md`). Tam metinler yerel
  branch'lerde; işlevsel U1 sürümü (G02) BLOCKED. Yerelde ~10 FIQ-06/11 düzeltme branch'i
  birikmiş.
- FIQ-07 (evren oluşturucu): 3184 gerçek verisini bekliyor.
- FIQ-09 Faz 1 (ham veri envanteri ve tasarım): başlamadı; bloklayan bir şey yok.
- FIQ-10 (PIT özellik deposu): başlamadı. FIQ-12: yalnız inert çekirdek var.

## E. Yeni yön: paralel veri

- Faiz, CDS, kur, enflasyon ve haftalık yabancı akımları KER-08/13d/13h ile gelir.
- Fon akımları (TEFAS) yeni bir kaynak; Paper 3 adayı: fon akımı kaynaklı fiyat baskısı
  ile temel haber etkisinin ayrıştırılması. Tasarım kartı daha sonra.
- Makro faktör bloğunun Paper 2 RQ2'ye eklenmesi bir owner kararıdır ve OSF kaydından
  önce verilmelidir.

## Owner işleri (toplam ~1,5 saat)

| # | İş | Süre |
|---|---|---|
| 1 | KO-6: UB Basel'e LSEG lisans e-postası | 10 dk |
| 2 | KO-7: DataStore akademik fiyat dilekçesi | 15 dk |
| 3 | KO-5: 3184 dosyalarını 2017–2024 için indir, intake'e koy | 20 dk |
| 4 | KO-3: EVDS anahtarı (yoksa) | 5 dk |
| 5 | FO-1: kohort seçim beyanı | 15 dk |
| 6 | FO-4: Fintables ve Yahoo koşul notu | 20 dk |
| 7 | Paper 1 ve 13/14/16 branch'lerinin push edilmesi | 2 dk |
