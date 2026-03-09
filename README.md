# FinanceIQ – BIST Financial Analysis Platform

> BIST'te işlem gören şirketlerin finansal tablolarını analiz eden, puanlayan ve karşılaştıran bir yatırım analiz platformu.

## Hızlı Başlangıç

### Gereksinimler
- Docker & Docker Compose
- (Yerel geliştirme için) Python 3.12, Node.js 20

### Docker ile Çalıştırma

```bash
cd Capstone_Code
docker compose up --build
```

| Servis   | Adres                        |
|----------|------------------------------|
| Frontend | http://localhost:3000        |
| Backend  | http://localhost:8000        |
| API Docs | http://localhost:8000/docs   |

Backend ilk açılışta otomatik olarak:
1. Veritabanı tablolarını oluşturur
2. **50 BIST şirketi** kaydeder (9 gerçek finansal veri + 41 sentetik veri)
3. 4'er çeyrek (2023Q1–Q4) finansal veri ve oran hesaplamalarını yapar
4. Kural tabanlı skorlama modeli (`rule_based_v2`) oluşturur

### Demo Giriş Bilgileri
Kayıt ekranından yeni hesap oluşturun (`/login` → "Kayıt Ol")

---

## Yerel Geliştirme

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# .env dosyası oluştur
echo "DATABASE_URL=postgresql://postgres:postgres@localhost:5432/capstone_db" > .env

# PostgreSQL çalışıyorsa seed'i çalıştır
python seed.py
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

---

## Sayfalar

| Sayfa | Yol | Açıklama |
|-------|-----|----------|
| Giriş | `/login` | Kayıt / JWT ile giriş |
| Arama | `/search` | Ticker veya şirket adıyla arama |
| Şirket Profili | `/company/:id` | Finansal tablo, oranlar, skor geçmişi |
| Skor Sonucu | `/score/:id` | Toplam skor, metrik breakdown, olasılık |
| Karşılaştırma | `/compare` | 2–8 şirket aynı modelle karşılaştırma |
| Veri Sağlığı | `/data-health` | Veri doğrulama ve boşluk analizi |
| Etiketleme Lab | `/labeling` | Makine öğrenmesi etiketi yönetimi |
| Doğrulama Lab | `/validation` | Model doğrulama ve sonuçlar |
| Admin | `/admin` | Kullanıcı ve model yönetimi (admin) |

---

## Proje Yapısı

```
Capstone_Code/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI uygulaması
│   │   ├── config.py            # Ortam değişkenleri
│   │   ├── database.py          # SQLAlchemy engine
│   │   ├── models/              # ORM modelleri (company, financial, scoring…)
│   │   ├── schemas/             # Pydantic şemaları
│   │   ├── routers/             # API endpoint'leri
│   │   └── services/
│   │       ├── ratio_service.py      # 12 finansal oran hesaplama
│   │       ├── scoring_service.py    # Kural tabanlı & lojistik skor motoru
│   │       ├── comparison_service.py # Çoklu şirket karşılaştırması
│   │       ├── sector_service.py     # Sektör benchmark hesaplama
│   │       └── validation_service.py # Model doğrulama
│   ├── seed_data/
│   │   └── financial_data.csv   # 9 şirket × 4 dönem (gerçek veriler)
│   ├── seed.py                  # Veritabanı seed scripti (50 şirket)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/               # 9 sayfa bileşeni
│   │   ├── components/
│   │   │   ├── layout/          # Sidebar, Topbar
│   │   │   └── ui.jsx           # Ortak UI bileşenleri
│   │   ├── context/AuthContext.jsx
│   │   └── api/client.js        # Axios istemcisi (JWT interceptor)
│   ├── vite.config.js
│   ├── nginx.conf
│   └── Dockerfile
└── docker-compose.yml
```

---

## API Özeti

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/auth/register` | Kullanıcı kaydı |
| POST | `/auth/login` | JWT token alımı |
| GET  | `/auth/me` | Mevcut kullanıcı bilgisi |
| GET  | `/companies?q=&limit=` | Şirket arama (max 500) |
| GET  | `/companies/{id}` | Şirket detayı |
| GET  | `/companies/{id}/financials` | Finansal tablolar |
| GET  | `/companies/{id}/metrics` | Hesaplanan 12 oran |
| POST | `/scoring/run` | Şirket skor çalıştır |
| POST | `/scoring/compare` | Çoklu şirket karşılaştır |
| GET  | `/reports/` | Rapor listesi |
| GET  | `/validation/runs` | Model doğrulama geçmişi |
| POST | `/ingestion/upload-csv` | CSV ile veri yükleme |

---

## Skor Motoru (Rule-Based v2)

| Metrik | Ağırlık |
|--------|---------|
| ROA | 10 |
| ROE | 10 |
| Operating Margin | 8 |
| Net Margin | 8 |
| Current Ratio | 8 |
| Quick Ratio | 7 |
| Cash Ratio | 7 |
| Debt/Equity | 10 |
| Debt/Assets | 8 |
| OCF/Debt | 10 |
| OCF/Assets | 7 |
| Cash Flow Margin | 7 |

- **Toplam Skor**: 0–100
- Logistik regresyon modeli de desteklenmektedir

---

## Seed Şirketleri (50 Şirket)

| Sektör | Şirketler |
|--------|-----------|
| Savunma | ASELS |
| Havacılık | THYAO, PGSUS, TAVHL |
| Bankacılık | GARAN, AKBNK |
| Holdingler | KCHOL, TEKFEN |
| Demir-Çelik | EREGL, KRDMD |
| Cam | SISE, ANACM, TRKCM |
| Perakende | BIMAS, MGROS, SOKM, ADESE |
| Otomotiv | FROTO, TOASO, DOAS, OTKAR |
| Telekomünikasyon | TTKOM, TCELL, NETAS |
| Yazılım/Teknoloji | LOGO, INDES, ARENA |
| Enerji | TUPRS, PETKM, AYGAZ, AKSEN, AKENR |
| Çimento/İnşaat | CEMTS, ENKAI, AKCNS, BUCIM |
| Gıda | ULKER, AEFES, TATGD, BANVT, KERVT |
| Diğer | HEPSI (E-Ticaret), ECILC, DEVA (İlaç), HURGZ (Medya), RYSAS (Lojistik), SASA (Kimya), VESBE, VESTL, ARCLK (Tüketim) |

