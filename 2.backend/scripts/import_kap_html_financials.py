import re
import unicodedata
from pathlib import Path
import pandas as pd

from app.database import SessionLocal
from app.models.company import Company
from app.models.financial import FinancialStatement


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "docs" / "DATA_Financial"


# ✅ 40 HİSSE — SOURCE OF TRUTH
FULL_TICKERS = {
    "AEFES", "ARCLK", "ASELS", "ASTOR", "BIMAS", "BRSAN", "BTCIM", "CANTE",
    "CCOLA", "CIMSA", "DOAS", "DSTKF", "ENKAI", "EREGL", "FROTO", "GUBRF",
    "HEKTS", "KONTR", "KRDMD", "KUYAS", "MAVI", "MGROS", "MIATK", "OYAKC",
    "PASEU", "PETKM", "PGSUS", "SASA", "SISE", "TAVHL", "TCELL", "THYAO",
    "TOASO", "TRALT", "TRMET", "TSKB", "TTKOM", "TUPRS", "TURSG", "ULKER"
}


# Dosya adı / şirket adı → ticker map
TICKER_NAME_HINTS = {
    "ANADOLU EFES": "AEFES",
    "ARCELIK": "ARCLK",
    "ARCLK": "ARCLK",
    "ASELSAN": "ASELS",
    "ASTOR": "ASTOR",
    "BIM BIRLESIK": "BIMAS",
    "BIM": "BIMAS",
    "BORUSAN": "BRSAN",
    "BATI ANADOLU CIMENTO": "BTCIM",
    "BATI CIMENTO": "BTCIM",
    "BTCIM": "BTCIM",
    "CAN2 TERMIK": "CANTE",
    "CAN 2 TERMIK": "CANTE",
    "CANTE": "CANTE",
    "COCA COLA": "CCOLA",
    "COCA-COLA": "CCOLA",
    "CIMSA": "CIMSA",
    "DOGUS OTOMOTIV": "DOAS",
    "DESTEK FINANS": "DSTKF",
    "DSTKF": "DSTKF",
    "ENKA": "ENKAI",
    "EREGLI": "EREGL",
    "FORD OTOMOTIV": "FROTO",
    "GUBRE": "GUBRF",
    "HEKTAS": "HEKTS",
    "KONTROLMATIK": "KONTR",
    "KARDEMIR": "KRDMD",
    "KUYAS": "KUYAS",
    "MAVI": "MAVI",
    "MIGROS": "MGROS",
    "MIA TEKNOLOJI": "MIATK",
    "OYAK CIMENTO": "OYAKC",
    "PASIFIK EURASIA": "PASEU",
    "PASEU": "PASEU",
    "PETKIM": "PETKM",
    "PEGASUS": "PGSUS",
    "SASA": "SASA",
    "SISE": "SISE",
    "TURKIYE SISE": "SISE",
    "TAV": "TAVHL",
    "TURKCELL": "TCELL",
    "TURK HAVA": "THYAO",
    "TOFAS": "TOASO",
    "TRABZON LIMAN": "TRALT",
    "TRMET": "TRMET",
    "TURKIYE SINAI KALKINMA": "TSKB",
    "TSKB": "TSKB",
    "TURK TELEKOM": "TTKOM",
    "TUPRAS": "TUPRS",
    "TURKIYE SIGORTA": "TURSG",
    "TURSG": "TURSG",
    "ULKER": "ULKER",
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

    for ticker in FULL_TICKERS:
        if ticker in name:
            return ticker

    for hint, ticker in TICKER_NAME_HINTS.items():
        if ticker in FULL_TICKERS and normalize(hint) in name:
            return ticker

    return None


def parse_number(x):
    if pd.isna(x):
        return None

    s = str(x).replace(".", "").replace(",", ".")

    try:
        return float(s)
    except Exception:
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

    c.is_active = ticker in FULL_TICKERS

    return c


def upsert_fs(db, company_id, period, values):
    fs = (
        db.query(FinancialStatement)
        .filter_by(company_id=company_id, period=period)
        .first()
    )

    if not fs:
        fs = FinancialStatement(company_id=company_id, period=period)
        db.add(fs)

    for field, value in values.items():
        if hasattr(fs, field):
            setattr(fs, field, value)


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

        multiplier = detect_multiplier(df)
        periods = find_periods(df)

        if not periods:
            continue

        key_col = df.columns[0]

        for _, row in df.iterrows():
            label = str(row[key_col]).strip()

            if label not in ROW_MAP:
                continue

            field = ROW_MAP[label]

            for period in periods:
                if period not in result:
                    result[period] = {}

                value = parse_number(row[period])

                if value is not None:
                    result[period][field] = value * multiplier

    return ticker, result


def main():
    db = SessionLocal()

    try:
        files = list(DATA_DIR.glob("*.xls"))

        print(f"{len(files)} files found")

        imported = set()

        for file in files:
            ticker, data = parse_file(file)

            if not ticker:
                continue

            company = upsert_company(db, ticker)

            for period, values in data.items():
                upsert_fs(db, company.id, period, values)

            imported.add(ticker)
            print("✔", ticker, len(data), "periods")

        db.query(Company).filter(~Company.ticker.in_(FULL_TICKERS)).update(
            {Company.is_active: False},
            synchronize_session=False,
        )

        missing = FULL_TICKERS - imported

        db.commit()

        print("\nDONE")
        print("Expected:", len(FULL_TICKERS))
        print("Imported:", len(imported))
        print("Missing:", sorted(missing))

    except Exception as e:
        db.rollback()
        print("ERROR:", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()