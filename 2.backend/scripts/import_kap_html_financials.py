import re
import unicodedata
from pathlib import Path
import pandas as pd

from app.database import SessionLocal
from app.models.company import Company
from app.models.financial import FinancialStatement


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "docs" / "DATA_Financial"


# ✅ 44 HİSSE — SOURCE OF TRUTH
FULL_TICKERS = {
    "AEFES","AKSA","AKSEN","ASELS","BIMAS","BRSAN","BSOKE","BTCIM",
    "CCOLA","CIMSA","CLEBI","DOAS","ECILC","EGEEN","ENJSA","EREGL",
    "FROTO","GENIL","GRSEL","GUBRF","KCAER","KRDMD","MAGEN","MAVI",
    "MGROS","MIATK","MPARK","OTKAR","OYAKC","PGSUS","SOKM","TAVHL",
    "TCELL","THYAO","TOASO","TRALT","TRENJ","TRMET","TTKOM","TTRAK",
    "TUPRS","TUREX","ULKER","YEOTK"
}


# 🔥 TÜM DOSYA ADI → TICKER MAP
TICKER_NAME_HINTS = {
    "ANADOLU EFES": "AEFES",
    "AKSA AKRILIK": "AKSA",
    "AKSA ENERJI": "AKSEN",
    "ASELSAN": "ASELS",
    "BIM BIRLESIK": "BIMAS",
    "BORUSAN": "BRSAN",
    "BATISOKE": "BSOKE",
    "SOKE CIMENTO": "BSOKE",
    "BATI ANADOLU CIMENTO": "BTCIM",
    "COCA COLA": "CCOLA",
    "CIMSA": "CIMSA",
    "CELEBI": "CLEBI",
    "DOGUS OTOMOTIV": "DOAS",
    "ECZACIBASI": "ECILC",
    "EGE ENDUSTRI": "EGEEN",
    "ENERJISA": "ENJSA",
    "EREGLI": "EREGL",
    "FORD OTOMOTIV": "FROTO",
    "GEN ILAC": "GENIL",
    "GURSEL": "GRSEL",
    "GUBRE": "GUBRF",
    "KOCAER": "KCAER",
    "KARDEMIR": "KRDMD",
    "MARGUN": "MAGEN",
    "MAVI": "MAVI",
    "MIGROS": "MGROS",
    "MIA TEKNOLOJI": "MIATK",
    "MLP SAGLIK": "MPARK",
    "OTOKAR": "OTKAR",
    "OYAK CIMENTO": "OYAKC",
    "PEGASUS": "PGSUS",
    "SOK MARKETLER": "SOKM",
    "TAV": "TAVHL",
    "TURKCELL": "TCELL",
    "TURK HAVA": "THYAO",
    "TOFAS": "TOASO",
    "TRABZON LIMAN": "TRALT",
    "TRENJ": "TRENJ",
    "TURKIYE SISE": "TRMET",
    "TURK TELEKOM": "TTKOM",
    "TURK TRAKTOR": "TTRAK",
    "TUPRAS": "TUPRS",
    "TUREX": "TUREX",
    "ULKER": "ULKER",
    "YEO": "YEOTK",
}


ROW_MAP = {
    "Hasılat": "revenue",
    "Net Dönem Karı (Zararı)": "net_income",
    "Toplam Varlıklar": "total_assets",
    "Toplam Özkaynaklar": "total_equity",
    "Dönen Varlıklar": "current_assets",
    "Kısa Vadeli Yükümlülükler": "current_liabilities",
}


def normalize(text):
    text = str(text).upper()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text


def detect_ticker(filename):
    name = normalize(filename)

    # 1. direkt ticker var mı?
    for t in FULL_TICKERS:
        if t in name:
            return t

    # 2. isimden eşleş
    for hint, ticker in TICKER_NAME_HINTS.items():
        if normalize(hint) in name:
            return ticker

    return None


def parse_number(x):
    if pd.isna(x):
        return None
    s = str(x).replace(".", "").replace(",", ".")
    try:
        return float(s)
    except:
        return None


def detect_multiplier(df):
    text = normalize(" ".join(df.astype(str).values.flatten()))
    if "BIN TL" in text or "1000 TL" in text:
        return 1000
    return 1


def find_periods(df):
    return [c for c in df.columns if re.match(r"\d{4}/\d{2}", str(c))]


def upsert_company(db, ticker):
    c = db.query(Company).filter_by(ticker=ticker).first()
    if not c:
        c = Company(ticker=ticker, company_name=ticker, is_active=True)
        db.add(c)
        db.flush()
    return c


def upsert_fs(db, cid, period, values):
    fs = db.query(FinancialStatement).filter_by(company_id=cid, period=period).first()
    if not fs:
        fs = FinancialStatement(company_id=cid, period=period)
        db.add(fs)

    for k, v in values.items():
        if hasattr(fs, k):
            setattr(fs, k, v)


def parse_file(path):
    ticker = detect_ticker(path.name)

    if not ticker:
        print("❌ SKIP:", path.name)
        return None, {}

    tables = pd.read_html(path)
    result = {}

    for df in tables:
        if df.shape[1] < 2:
            continue

        mult = detect_multiplier(df)
        periods = find_periods(df)

        if not periods:
            continue

        key_col = df.columns[0]

        for _, row in df.iterrows():
            label = str(row[key_col]).strip()

            if label not in ROW_MAP:
                continue

            field = ROW_MAP[label]

            for p in periods:
                if p not in result:
                    result[p] = {}

                val = parse_number(row[p])
                if val is not None:
                    result[p][field] = val * mult

    return ticker, result


def main():
    db = SessionLocal()

    try:
        files = list(DATA_DIR.glob("*.xls"))

        print(f"{len(files)} files found")

        imported = set()

        for f in files:
            ticker, data = parse_file(f)
            if not ticker:
                continue

            company = upsert_company(db, ticker)

            for period, values in data.items():
                upsert_fs(db, company.id, period, values)

            imported.add(ticker)
            print("✔", ticker, len(data), "periods")

        missing = FULL_TICKERS - imported

        db.commit()

        print("\nDONE")
        print("Imported:", len(imported))
        print("Missing:", missing)

    except Exception as e:
        db.rollback()
        print("ERROR:", e)
    finally:
        db.close()


if __name__ == "__main__":
    main()