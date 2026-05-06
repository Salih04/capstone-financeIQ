from app.database import SessionLocal
from app.models.company import Company

COMPANIES = [
    ("AEFES", "Anadolu Efes Biracılık ve Malt Sanayii A.Ş.", "Food & Beverage", "FOOD"),
    ("ARCLK", "Arçelik A.Ş.", "Consumer Durables", "DURABLES"),
    ("ASELS", "Aselsan Elektronik Sanayi ve Ticaret A.Ş.", "Defense", "DEFENSE"),
    ("ASTOR", "Astor Enerji A.Ş.", "Energy", "ENERGY"),
    ("BIMAS", "BİM Birleşik Mağazalar A.Ş.", "Retail", "RETAIL"),
    ("BRSAN", "Borusan Birleşik Boru Fabrikaları Sanayi ve Ticaret A.Ş.", "Steel & Iron", "STEEL"),
    ("BTCIM", "Batıçim Batı Anadolu Çimento Sanayii A.Ş.", "Cement", "CEMENT"),
    ("CANTE", "Çan2 Termik A.Ş.", "Energy", "ENERGY"),
    ("CCOLA", "Coca-Cola İçecek A.Ş.", "Food & Beverage", "FOOD"),
    ("CIMSA", "Çimsa Çimento Sanayi ve Ticaret A.Ş.", "Cement", "CEMENT"),
    ("DOAS", "Doğuş Otomotiv Servis ve Ticaret A.Ş.", "Automotive", "AUTO"),
    ("DSTKF", "Destek Finans Faktoring A.Ş.", "Financial Services", "FINANCE"),
    ("ENKAI", "Enka İnşaat ve Sanayi A.Ş.", "Construction", "CONSTRUCTION"),
    ("EREGL", "Ereğli Demir ve Çelik Fabrikaları T.A.Ş.", "Steel & Iron", "STEEL"),
    ("FROTO", "Ford Otomotiv Sanayi A.Ş.", "Automotive", "AUTO"),
    ("GUBRF", "Gübre Fabrikaları T.A.Ş.", "Chemicals", "CHEMICAL"),
    ("HEKTS", "Hektaş Ticaret T.A.Ş.", "Chemicals", "CHEMICAL"),
    ("KONTR", "Kontrolmatik Teknoloji Enerji ve Mühendislik A.Ş.", "Technology", "TECH"),
    ("KRDMD", "Kardemir Karabük Demir Çelik Sanayi ve Ticaret A.Ş.", "Steel & Iron", "STEEL"),
    ("KUYAS", "Kuyas Yatırım A.Ş.", "Real Estate", "REAL_ESTATE"),
    ("MAVI", "Mavi Giyim Sanayi ve Ticaret A.Ş.", "Retail", "RETAIL"),
    ("MGROS", "Migros Ticaret A.Ş.", "Retail", "RETAIL"),
    ("MIATK", "Mia Teknoloji A.Ş.", "Technology", "TECH"),
    ("OYAKC", "Oyak Çimento Fabrikaları A.Ş.", "Cement", "CEMENT"),
    ("PASEU", "Pasifik Eurasia Lojistik Dış Ticaret A.Ş.", "Logistics", "LOGISTICS"),
    ("PETKM", "Petkim Petrokimya Holding A.Ş.", "Petrochemicals", "PETROCHEM"),
    ("PGSUS", "Pegasus Hava Taşımacılığı A.Ş.", "Aviation", "AVIATION"),
    ("SASA", "Sasa Polyester Sanayi A.Ş.", "Chemicals", "CHEMICAL"),
    ("SISE", "Türkiye Şişe ve Cam Fabrikaları A.Ş.", "Glass", "GLASS"),
    ("TAVHL", "TAV Havalimanları Holding A.Ş.", "Aviation", "AVIATION"),
    ("TCELL", "Turkcell İletişim Hizmetleri A.Ş.", "Telecom", "TELECOM"),
    ("THYAO", "Türk Hava Yolları A.O.", "Aviation", "AVIATION"),
    ("TOASO", "Tofaş Türk Otomobil Fabrikası A.Ş.", "Automotive", "AUTO"),
    ("TRALT", "Trabzon Liman İşletmeciliği A.Ş.", "Transportation", "TRANSPORT"),
    ("TRMET", "Türkiye Metal Sanayi A.Ş.", "Metal", "METAL"),
    ("TSKB", "Türkiye Sınai Kalkınma Bankası A.Ş.", "Banking", "BANKING"),
    ("TTKOM", "Türk Telekomünikasyon A.Ş.", "Telecom", "TELECOM"),
    ("TUPRS", "Türkiye Petrol Rafinerileri A.Ş.", "Energy", "ENERGY"),
    ("TURSG", "Türkiye Sigorta A.Ş.", "Insurance", "INSURANCE"),
    ("ULKER", "Ülker Bisküvi Sanayi A.Ş.", "Food & Beverage", "FOOD"),
]


def main():
    db = SessionLocal()
    try:
        valid_tickers = {ticker for ticker, _, _, _ in COMPANIES}

        for ticker, name, sector, sector_code in COMPANIES:
            c = db.query(Company).filter(Company.ticker == ticker).first()

            if not c:
                c = Company(ticker=ticker)
                db.add(c)

            c.company_name = name
            c.sector = sector
            c.sector_code = sector_code
            c.is_active = True

        db.query(Company).filter(~Company.ticker.in_(valid_tickers)).update(
            {Company.is_active: False},
            synchronize_session=False,
        )

        db.commit()
        print(f"Seeded/updated {len(COMPANIES)} companies.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()