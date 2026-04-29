from app.database import SessionLocal
from app.models.company import Company

COMPANIES = [
    ("AEFES", "Anadolu Efes Biracılık ve Malt Sanayii A.Ş.", "Food & Beverage", "FOOD"),
    ("AKSA", "Aksa Akrilik Kimya Sanayii A.Ş.", "Chemicals", "CHEMICAL"),
    ("AKSEN", "Aksa Enerji Üretim A.Ş.", "Energy", "ENERGY"),
    ("ASELS", "Aselsan Elektronik Sanayi ve Ticaret A.Ş.", "Defense", "DEFENSE"),
    ("BIMAS", "BİM Birleşik Mağazalar A.Ş.", "Retail", "RETAIL"),
    ("BRSAN", "Borusan Birleşik Boru Fabrikaları Sanayi ve Ticaret A.Ş.", "Steel & Iron", "STEEL"),
    ("BSOKE", "Batısöke Söke Çimento Sanayii T.A.Ş.", "Cement", "CEMENT"),
    ("BTCIM", "Batıçim Batı Anadolu Çimento Sanayii A.Ş.", "Cement", "CEMENT"),
    ("CCOLA", "Coca-Cola İçecek A.Ş.", "Food & Beverage", "FOOD"),
    ("CIMSA", "Çimsa Çimento Sanayi ve Ticaret A.Ş.", "Cement", "CEMENT"),
    ("CLEBI", "Çelebi Hava Servisi A.Ş.", "Aviation", "AVIATION"),
    ("DOAS", "Doğuş Otomotiv Servis ve Ticaret A.Ş.", "Automotive", "AUTO"),
    ("ECILC", "Eczacıbaşı İlaç Sanayi ve Ticaret A.Ş.", "Pharmaceuticals", "PHARMA"),
    ("EGEEN", "Ege Endüstri ve Ticaret A.Ş.", "Automotive", "AUTO"),
    ("ENJSA", "Enerjisa Enerji A.Ş.", "Energy", "ENERGY"),
    ("EREGL", "Ereğli Demir ve Çelik Fabrikaları T.A.Ş.", "Steel & Iron", "STEEL"),
    ("FROTO", "Ford Otomotiv Sanayi A.Ş.", "Automotive", "AUTO"),
    ("GENIL", "Gen İlaç ve Sağlık Ürünleri Sanayi ve Ticaret A.Ş.", "Pharmaceuticals", "PHARMA"),
    ("GRSEL", "Gür-Sel Turizm Taşımacılık ve Servis Ticaret A.Ş.", "Transportation", "TRANSPORT"),
    ("GUBRF", "Gübre Fabrikaları T.A.Ş.", "Chemicals", "CHEMICAL"),
    ("KCAER", "Kocaer Çelik Sanayi ve Ticaret A.Ş.", "Steel & Iron", "STEEL"),
    ("KRDMD", "Kardemir Karabük Demir Çelik Sanayi ve Ticaret A.Ş.", "Steel & Iron", "STEEL"),
    ("MAGEN", "Margün Enerji Üretim Sanayi ve Ticaret A.Ş.", "Energy", "ENERGY"),
    ("MAVI", "Mavi Giyim Sanayi ve Ticaret A.Ş.", "Retail", "RETAIL"),
    ("MGROS", "Migros Ticaret A.Ş.", "Retail", "RETAIL"),
    ("MIATK", "Mia Teknoloji A.Ş.", "Technology", "TECH"),
    ("MPARK", "MLP Sağlık Hizmetleri A.Ş.", "Healthcare", "HEALTH"),
    ("OTKAR", "Otokar Otomotiv ve Savunma Sanayi A.Ş.", "Automotive", "AUTO"),
    ("OYAKC", "Oyak Çimento Fabrikaları A.Ş.", "Cement", "CEMENT"),
    ("PGSUS", "Pegasus Hava Taşımacılığı A.Ş.", "Aviation", "AVIATION"),
    ("SOKM", "Şok Marketler Ticaret A.Ş.", "Retail", "RETAIL"),
    ("TAVHL", "TAV Havalimanları Holding A.Ş.", "Aviation", "AVIATION"),
    ("TCELL", "Turkcell İletişim Hizmetleri A.Ş.", "Telecom", "TELECOM"),
    ("THYAO", "Türk Hava Yolları A.O.", "Aviation", "AVIATION"),
    ("TOASO", "Tofaş Türk Otomobil Fabrikası A.Ş.", "Automotive", "AUTO"),
    ("TRALT", "Trabzon Liman İşletmeciliği A.Ş.", "Transportation", "TRANSPORT"),
    ("TRENJ", "Europower Enerji ve Otomasyon Teknolojileri Sanayi Ticaret A.Ş.", "Energy", "ENERGY"),
    ("TRMET", "Türkiye Şişe ve Cam Fabrikaları A.Ş.", "Glass", "GLASS"),
    ("TTKOM", "Türk Telekomünikasyon A.Ş.", "Telecom", "TELECOM"),
    ("TTRAK", "Türk Traktör ve Ziraat Makineleri A.Ş.", "Automotive", "AUTO"),
    ("TUPRS", "Türkiye Petrol Rafinerileri A.Ş.", "Energy", "ENERGY"),
    ("TUREX", "Tureks Turizm Taşımacılık A.Ş.", "Transportation", "TRANSPORT"),
    ("ULKER", "Ülker Bisküvi Sanayi A.Ş.", "Food & Beverage", "FOOD"),
    ("YEOTK", "Yeo Teknoloji Enerji ve Endüstri A.Ş.", "Technology", "TECH"),
]

def main():
    db = SessionLocal()
    try:
        for ticker, name, sector, sector_code in COMPANIES:
            c = db.query(Company).filter(Company.ticker == ticker).first()

            if not c:
                c = Company(ticker=ticker)
                db.add(c)

            c.company_name = name
            c.sector = sector
            c.sector_code = sector_code
            c.is_active = True

        db.commit()
        print("Seeded/updated 44 companies.")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    main()