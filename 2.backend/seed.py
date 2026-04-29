"""
Seed script – populates companies table and imports financial data.
Run: python -m backend.seed  (from workspace root)
Or inside Docker: python seed.py
"""
import sys
import os
import time

# ensure app is importable
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from app.database import SessionLocal, engine, Base
from app.models import *  # noqa
from app.models.company import Company
from app.models.financial import FinancialStatement, ComputedMetric
from app.models.scoring_model import ScoringModel, ScoringModelMetric
from app.models.governance import LabelDefinition
from app.services.ratio_service import compute_ratios, upsert_computed_metrics
from app.services.transition_service import compute_transitions_for_company
from app.services.sector_service import recompute_sector_benchmarks, recompute_sector_normalized

# Wait for Postgres to be ready before doing anything
MAX_RETRIES = 20
for _attempt in range(1, MAX_RETRIES + 1):
    try:
        with engine.connect() as _conn:
            _conn.execute(text("SELECT 1"))
        print(f"[seed] Database ready (attempt {_attempt})")
        break
    except OperationalError as _e:
        print(f"[seed] Waiting for DB… attempt {_attempt}/{MAX_RETRIES}: {_e}")
        time.sleep(3)
else:
    print("[seed] ❌ Could not connect to database. Exiting.")
    sys.exit(1)

Base.metadata.create_all(bind=engine)

COMPANIES = [
    {"ticker": "ASELS", "company_name": "Aselsan Elektronik Sanayi ve Ticaret A.Ş.", "sector": "Savunma & Havacılık", "sector_code": "SAVUNMA"},
    {"ticker": "THYAO", "company_name": "Türk Hava Yolları A.O.", "sector": "Havacılık & Ulaşım", "sector_code": "HAVACILIK"},
    {"ticker": "EREGL", "company_name": "Ereğli Demir ve Çelik Fabrikaları T.A.Ş.", "sector": "Demir-Çelik", "sector_code": "DEMIR_CELIK"},
    {"ticker": "BIMAS", "company_name": "BİM Birleşik Mağazalar A.Ş.", "sector": "Perakende", "sector_code": "PERAKENDE"},
    {"ticker": "KCHOL", "company_name": "Koç Holding A.Ş.", "sector": "Holdingler", "sector_code": "HOLDING"},
    {"ticker": "SISE",  "company_name": "Türkiye Şişe ve Cam Fabrikaları A.Ş.", "sector": "Cam & Ambalaj", "sector_code": "CAM"},
    {"ticker": "GARAN", "company_name": "Türkiye Garanti Bankası A.Ş.", "sector": "Bankacılık", "sector_code": "BANKACILIK"},
    {"ticker": "FROTO", "company_name": "Ford Otomotiv Sanayi A.Ş.", "sector": "Otomotiv", "sector_code": "OTOMOTIV"},
    {"ticker": "AKBNK",  "company_name": "Akbank T.A.Ş.",                                          "sector": "Bankacılık",              "sector_code": "BANKACILIK"},
    # ── Non-financial BIST companies ─────────────────────────────────────────
    {"ticker": "TTKOM",  "company_name": "Türk Telekomünikasyon A.Ş.",                           "sector": "Telekomünikasyon",        "sector_code": "TELEKOM"},
    {"ticker": "TCELL",  "company_name": "Turkcell İletişim Hizmetleri A.Ş.",                    "sector": "Telekomünikasyon",        "sector_code": "TELEKOM"},
    {"ticker": "NETAS",  "company_name": "Netaş Telekomünikasyon A.Ş.",                          "sector": "Telekomünikasyon",        "sector_code": "TELEKOM"},
    {"ticker": "LOGO",   "company_name": "Logo Yazılım Sanayi ve Ticaret A.Ş.",                  "sector": "Yazılım",                 "sector_code": "YAZILIM"},
    {"ticker": "INDES",  "company_name": "İndeks Bilgisayar Sistemleri A.Ş.",                    "sector": "Teknoloji",               "sector_code": "TEKNOLOJI"},
    {"ticker": "ARENA",  "company_name": "Arena Bilgisayar Sanayi ve Ticaret A.Ş.",              "sector": "Teknoloji",               "sector_code": "TEKNOLOJI"},
    {"ticker": "TUPRS",  "company_name": "Tüpraş Türkiye Petrol Rafinerileri A.Ş.",              "sector": "Enerji",                  "sector_code": "ENERJI"},
    {"ticker": "PETKM",  "company_name": "Petkim Petrokimya Holding A.Ş.",                       "sector": "Petrokimya",              "sector_code": "PETROKIMYA"},
    {"ticker": "AYGAZ",  "company_name": "Aygaz A.Ş.",                                           "sector": "Enerji",                  "sector_code": "ENERJI"},
    {"ticker": "AKSEN",  "company_name": "Aksa Enerji Üretim A.Ş.",                              "sector": "Enerji",                  "sector_code": "ENERJI"},
    {"ticker": "AKENR",  "company_name": "Akenerji Elektrik Üretim A.Ş.",                        "sector": "Enerji",                  "sector_code": "ENERJI"},
    {"ticker": "MGROS",  "company_name": "Migros Ticaret A.Ş.",                                  "sector": "Perakende",               "sector_code": "PERAKENDE"},
    {"ticker": "SOKM",   "company_name": "Şok Marketler Ticaret A.Ş.",                           "sector": "Perakende",               "sector_code": "PERAKENDE"},
    {"ticker": "ADESE",  "company_name": "Adese Alışveriş Merkezleri T.A.Ş.",                    "sector": "Perakende",               "sector_code": "PERAKENDE"},
    {"ticker": "HEPSI",  "company_name": "D-Market Elektronik Hizmetler ve Ticaret A.Ş.",        "sector": "E-Ticaret",               "sector_code": "ETICARET"},
    {"ticker": "KRDMD",  "company_name": "Kardemir Karabük Demir Çelik Sanayi ve Ticaret A.Ş.", "sector": "Demir-Çelik",             "sector_code": "DEMIR_CELIK"},
    {"ticker": "ANACM",  "company_name": "Anadolu Cam Sanayii A.Ş.",                             "sector": "Cam",                     "sector_code": "CAM"},
    {"ticker": "TRKCM",  "company_name": "Trakya Cam Sanayii A.Ş.",                              "sector": "Cam",                     "sector_code": "CAM"},
    {"ticker": "CEMTS",  "company_name": "Çimsa Çimento Sanayi ve Ticaret A.Ş.",                "sector": "Çimento",                 "sector_code": "CIMENTO"},
    {"ticker": "ENKAI",  "company_name": "Enka İnşaat ve Sanayi A.Ş.",                           "sector": "İnşaat",                  "sector_code": "INSAAT"},
    {"ticker": "TEKFEN", "company_name": "Tekfen Holding A.Ş.",                                  "sector": "Holdingler",              "sector_code": "HOLDING"},
    {"ticker": "AKCNS",  "company_name": "Akçansa Çimento Sanayi ve Ticaret A.Ş.",              "sector": "Çimento",                 "sector_code": "CIMENTO"},
    {"ticker": "BUCIM",  "company_name": "Bursa Çimento Fabrikası A.Ş.",                         "sector": "Çimento",                 "sector_code": "CIMENTO"},
    {"ticker": "TOASO",  "company_name": "Tofaş Türk Otomobil Fabrikası A.Ş.",                  "sector": "Otomotiv",                "sector_code": "OTOMOTIV"},
    {"ticker": "DOAS",   "company_name": "Doğuş Otomotiv Servis ve Ticaret A.Ş.",               "sector": "Otomotiv",                "sector_code": "OTOMOTIV"},
    {"ticker": "OTKAR",  "company_name": "Otokar Otomotiv ve Savunma Sanayi A.Ş.",              "sector": "Otomotiv",                "sector_code": "OTOMOTIV"},
    {"ticker": "ULKER",  "company_name": "Ülker Bisküvi Sanayi A.Ş.",                            "sector": "Gıda",                    "sector_code": "GIDA"},
    {"ticker": "AEFES",  "company_name": "Anadolu Efes Biracılık ve Malt Sanayii A.Ş.",         "sector": "Gıda & İçecek",           "sector_code": "GIDA"},
    {"ticker": "TATGD",  "company_name": "Tat Gıda Sanayi A.Ş.",                                 "sector": "Gıda",                    "sector_code": "GIDA"},
    {"ticker": "BANVT",  "company_name": "Banvit Bandırma Vitaminli Yem Sanayii A.Ş.",          "sector": "Gıda",                    "sector_code": "GIDA"},
    {"ticker": "KERVT",  "company_name": "Kerevitaş Gıda Sanayi ve Ticaret A.Ş.",              "sector": "Gıda",                    "sector_code": "GIDA"},
    {"ticker": "PGSUS",  "company_name": "Pegasus Hava Taşımacılığı A.Ş.",                      "sector": "Havacılık",               "sector_code": "HAVACILIK"},
    {"ticker": "ECILC",  "company_name": "Eczacıbaşı İlaç Sanayi ve Ticaret A.Ş.",             "sector": "İlaç & Sağlık",          "sector_code": "ILAC"},
    {"ticker": "DEVA",   "company_name": "Deva Holding A.Ş.",                                    "sector": "İlaç",                   "sector_code": "ILAC"},
    {"ticker": "HURGZ",  "company_name": "Hürriyet Gazetecilik ve Matbaacılık A.Ş.",            "sector": "Medya",                   "sector_code": "MEDYA"},
    {"ticker": "RYSAS",  "company_name": "Reysaş Taşımacılık ve Lojistik Ticaret A.Ş.",        "sector": "Lojistik",                "sector_code": "LOJISTIK"},
    {"ticker": "SASA",   "company_name": "Sasa Polyester Sanayi A.Ş.",                           "sector": "Kimya & Tekstil",         "sector_code": "TEKSTIL"},
    {"ticker": "VESBE",  "company_name": "Vestel Beyaz Eşya Sanayi ve Ticaret A.Ş.",            "sector": "Dayanıklı Tüketim",       "sector_code": "TUKETIM"},
    {"ticker": "VESTL",  "company_name": "Vestel Elektronik Sanayi ve Ticaret A.Ş.",            "sector": "Elektronik",              "sector_code": "ELEKTRONIK"},
    {"ticker": "ARCLK",  "company_name": "Arçelik A.Ş.",                                         "sector": "Dayanıklı Tüketim",       "sector_code": "TUKETIM"},
    {"ticker": "TAVHL",  "company_name": "TAV Havalimanları Holding A.Ş.",                       "sector": "Havacılık & Ulaşım",      "sector_code": "HAVACILIK"},
]

FLOAT_COLS = [
    "revenue", "net_income", "total_assets", "total_equity", "total_liabilities",
    "current_assets", "current_liabilities", "cash", "operating_cash_flow",
    "operating_income", "gross_profit", "inventory",
]

# Synthetic financial parameters for new non-financial companies.
# fmt: (ticker, rev_q4, ni_pct, assets_q4, eq_pct, ca_pct, cl_pct,
#        cash_pct_of_assets, ocf_pct, op_pct, gp_pct, inv_pct_of_rev)
SYNTHETIC_DATA = [
    ("TTKOM",   62_000_000_000, 0.18, 130_000_000_000, 0.38, 0.25, 0.22, 0.08, 0.25, 0.28, 0.38, 0.00),
    ("TCELL",   78_000_000_000, 0.15, 148_000_000_000, 0.35, 0.22, 0.20, 0.07, 0.22, 0.25, 0.35, 0.00),
    ("NETAS",    2_500_000_000, 0.08,   6_000_000_000, 0.45, 0.50, 0.35, 0.12, 0.10, 0.12, 0.25, 0.15),
    ("LOGO",     3_500_000_000, 0.22,  10_000_000_000, 0.55, 0.45, 0.25, 0.15, 0.25, 0.27, 0.62, 0.00),
    ("INDES",   14_000_000_000, 0.03,  10_000_000_000, 0.30, 0.70, 0.55, 0.08, 0.04, 0.04, 0.08, 0.25),
    ("ARENA",   11_000_000_000, 0.03,   8_000_000_000, 0.28, 0.72, 0.57, 0.06, 0.04, 0.04, 0.07, 0.22),
    ("TUPRS",  280_000_000_000, 0.05, 190_000_000_000, 0.30, 0.35, 0.28, 0.06, 0.06, 0.08, 0.12, 0.15),
    ("PETKM",   48_000_000_000, 0.08,  65_000_000_000, 0.42, 0.30, 0.22, 0.08, 0.10, 0.12, 0.20, 0.18),
    ("AYGAZ",   28_000_000_000, 0.08,  22_000_000_000, 0.50, 0.40, 0.28, 0.10, 0.10, 0.12, 0.20, 0.10),
    ("AKSEN",   14_000_000_000, 0.06,  32_000_000_000, 0.38, 0.20, 0.18, 0.05, 0.15, 0.18, 0.35, 0.02),
    ("AKENR",    9_000_000_000, 0.05,  22_000_000_000, 0.35, 0.18, 0.16, 0.05, 0.14, 0.17, 0.32, 0.02),
    ("MGROS",   62_000_000_000, 0.03,  32_000_000_000, 0.35, 0.55, 0.48, 0.05, 0.05, 0.06, 0.20, 0.20),
    ("SOKM",    48_000_000_000, 0.02,  20_000_000_000, 0.30, 0.55, 0.50, 0.04, 0.04, 0.05, 0.18, 0.22),
    ("ADESE",   10_000_000_000, 0.02,   6_000_000_000, 0.35, 0.50, 0.45, 0.04, 0.04, 0.05, 0.18, 0.20),
    ("HEPSI",   13_000_000_000,-0.02,  10_000_000_000, 0.35, 0.60, 0.50, 0.10, 0.02, 0.01, 0.35, 0.10),
    ("KRDMD",   22_000_000_000, 0.10,  35_000_000_000, 0.45, 0.40, 0.28, 0.08, 0.14, 0.17, 0.28, 0.22),
    ("ANACM",    9_000_000_000, 0.12,  16_000_000_000, 0.52, 0.35, 0.22, 0.09, 0.15, 0.18, 0.30, 0.15),
    ("TRKCM",   26_000_000_000, 0.13,  38_000_000_000, 0.50, 0.32, 0.20, 0.08, 0.16, 0.19, 0.32, 0.14),
    ("CEMTS",   14_000_000_000, 0.12,  18_000_000_000, 0.55, 0.28, 0.18, 0.08, 0.16, 0.18, 0.35, 0.08),
    ("ENKAI",   55_000_000_000, 0.15, 110_000_000_000, 0.50, 0.30, 0.18, 0.08, 0.18, 0.20, 0.35, 0.05),
    ("TEKFEN",  42_000_000_000, 0.12,  55_000_000_000, 0.45, 0.45, 0.33, 0.10, 0.15, 0.18, 0.28, 0.05),
    ("AKCNS",   15_000_000_000, 0.18,  19_000_000_000, 0.58, 0.30, 0.18, 0.08, 0.20, 0.22, 0.38, 0.07),
    ("BUCIM",    6_000_000_000, 0.16,   9_000_000_000, 0.55, 0.30, 0.18, 0.07, 0.18, 0.20, 0.36, 0.07),
    ("TOASO",   72_000_000_000, 0.09,  65_000_000_000, 0.42, 0.38, 0.28, 0.07, 0.11, 0.12, 0.20, 0.18),
    ("DOAS",    42_000_000_000, 0.04,  25_000_000_000, 0.35, 0.55, 0.45, 0.06, 0.05, 0.06, 0.12, 0.25),
    ("OTKAR",   12_000_000_000, 0.14,  18_000_000_000, 0.45, 0.45, 0.35, 0.10, 0.16, 0.18, 0.30, 0.20),
    ("ULKER",   48_000_000_000, 0.08,  38_000_000_000, 0.45, 0.35, 0.25, 0.06, 0.10, 0.12, 0.32, 0.15),
    ("AEFES",   38_000_000_000, 0.09,  58_000_000_000, 0.42, 0.30, 0.22, 0.07, 0.12, 0.14, 0.45, 0.12),
    ("TATGD",    6_000_000_000, 0.06,   7_000_000_000, 0.45, 0.40, 0.30, 0.06, 0.08, 0.10, 0.25, 0.18),
    ("BANVT",    9_000_000_000, 0.05,   8_000_000_000, 0.42, 0.38, 0.30, 0.05, 0.07, 0.08, 0.22, 0.20),
    ("KERVT",    7_000_000_000, 0.05,   7_000_000_000, 0.42, 0.40, 0.32, 0.05, 0.07, 0.09, 0.22, 0.20),
    ("PGSUS",   45_000_000_000, 0.10,  72_000_000_000, 0.38, 0.28, 0.22, 0.08, 0.14, 0.15, 0.30, 0.02),
    ("ECILC",    9_000_000_000, 0.10,  14_000_000_000, 0.48, 0.42, 0.28, 0.08, 0.12, 0.13, 0.35, 0.18),
    ("DEVA",     8_000_000_000, 0.08,  13_000_000_000, 0.46, 0.40, 0.28, 0.07, 0.10, 0.12, 0.33, 0.20),
    ("HURGZ",    4_000_000_000, 0.05,   7_000_000_000, 0.45, 0.45, 0.32, 0.10, 0.08, 0.10, 0.40, 0.00),
    ("RYSAS",    4_000_000_000, 0.15,  14_000_000_000, 0.55, 0.25, 0.15, 0.06, 0.20, 0.22, 0.45, 0.00),
    ("SASA",    32_000_000_000, 0.08,  45_000_000_000, 0.38, 0.30, 0.22, 0.05, 0.10, 0.12, 0.20, 0.20),
    ("VESBE",   35_000_000_000, 0.07,  28_000_000_000, 0.38, 0.45, 0.38, 0.06, 0.09, 0.10, 0.28, 0.20),
    ("VESTL",   45_000_000_000, 0.07,  40_000_000_000, 0.35, 0.50, 0.40, 0.05, 0.08, 0.10, 0.25, 0.22),
    ("ARCLK",  112_000_000_000, 0.08, 145_000_000_000, 0.35, 0.42, 0.32, 0.06, 0.10, 0.12, 0.32, 0.18),
    ("TAVHL",   32_000_000_000, 0.12,  82_000_000_000, 0.40, 0.25, 0.18, 0.07, 0.16, 0.18, 0.55, 0.00),
]


def _syn_financial_rows(ticker, rev4, ni_pct, assets4, eq_pct, ca_pct, cl_pct,
                         cash_pct, ocf_pct, op_pct, gp_pct, inv_pct):
    """Return 4 quarterly financial-data dicts for seed insertion (2023Q1–Q4)."""
    rev_factors   = [0.70, 0.80, 0.90, 1.00]
    asset_factors = [0.90, 0.93, 0.96, 1.00]
    rows = []
    for i, period in enumerate(["2023Q1", "2023Q2", "2023Q3", "2023Q4"]):
        rev   = int(rev4   * rev_factors[i])
        ta    = int(assets4 * asset_factors[i])
        eq    = int(ta * eq_pct)
        rows.append({
            "ticker": ticker, "period": period,
            "revenue":            rev,
            "net_income":         int(rev * ni_pct),
            "total_assets":       ta,
            "total_equity":       eq,
            "total_liabilities":  ta - eq,
            "current_assets":     int(ta  * ca_pct),
            "current_liabilities":int(ta  * cl_pct),
            "cash":               int(ta  * cash_pct),
            "operating_cash_flow":int(rev * ocf_pct),
            "operating_income":   int(rev * op_pct),
            "gross_profit":       int(rev * gp_pct),
            "inventory":          int(rev * inv_pct),
        })
    return rows

# Default rule-based scoring model seeded on first run
DEFAULT_MODEL = {
    "model_name": "rule_based_v2",
    "model_type": "rule_based",
    "version": "2.0",
    "metrics": [
        {"feature_name": "roa",              "weight": 10, "direction": "higher_better"},
        {"feature_name": "roe",              "weight": 10, "direction": "higher_better"},
        {"feature_name": "operating_margin", "weight": 8,  "direction": "higher_better"},
        {"feature_name": "net_margin",       "weight": 8,  "direction": "higher_better"},
        {"feature_name": "current_ratio",    "weight": 8,  "direction": "higher_better"},
        {"feature_name": "quick_ratio",      "weight": 7,  "direction": "higher_better"},
        {"feature_name": "cash_ratio",       "weight": 7,  "direction": "higher_better"},
        {"feature_name": "debt_to_equity",   "weight": 10, "direction": "lower_better"},
        {"feature_name": "debt_to_assets",   "weight": 8,  "direction": "lower_better"},
        {"feature_name": "ocf_to_debt",      "weight": 10, "direction": "higher_better"},
        {"feature_name": "ocf_to_assets",    "weight": 7,  "direction": "higher_better"},
        {"feature_name": "cash_flow_margin", "weight": 7,  "direction": "higher_better"},
    ],
}


def seed():
    import csv, os

    db = SessionLocal()
    try:
        # ── Companies ───────────────────────────────────────────────────────
        for c in COMPANIES:
            existing = db.query(Company).filter(Company.ticker == c["ticker"]).first()
            if not existing:
                db.add(Company(**c))
            else:
                # Back-fill sector_code if missing
                if not existing.sector_code:
                    existing.sector_code = c["sector_code"]
        db.commit()
        print(f"[seed] {len(COMPANIES)} companies upserted.")

        # ── Financial data ──────────────────────────────────────────────────
        csv_path = os.path.join(os.path.dirname(__file__), "seed_data", "financial_data.csv")
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            affected_companies: set[int] = set()
            affected_periods: set[str] = set()
            for row in reader:
                ticker = row["ticker"].strip().upper()
                period = row["period"].strip()
                company = db.query(Company).filter(Company.ticker == ticker).first()
                if not company:
                    continue

                existing = (
                    db.query(FinancialStatement)
                    .filter(
                        FinancialStatement.company_id == company.id,
                        FinancialStatement.period == period,
                    )
                    .first()
                )
                data = {col: (float(row[col]) if row.get(col) else None) for col in FLOAT_COLS}

                if existing:
                    for k, v in data.items():
                        setattr(existing, k, v)
                    db.commit()
                    db.refresh(existing)
                    stmt = existing
                else:
                    stmt = FinancialStatement(
                        company_id=company.id,
                        period=period,
                        source_name="seed",
                        **data,
                    )
                    db.add(stmt)
                    db.commit()
                    db.refresh(stmt)

                ratios = compute_ratios(stmt)
                upsert_computed_metrics(db, company.id, period, ratios)

                affected_companies.add(company.id)
                affected_periods.add(period)
                count += 1
            print(f"[seed] {count} financial records imported.")

        # ── Synthetic financial data for new non-financial companies ────────
        print("[seed] Inserting synthetic financial data for new companies…")
        syn_count = 0
        for params in SYNTHETIC_DATA:
            for row in _syn_financial_rows(*params):
                ticker = row["ticker"]
                period = row["period"]
                company = db.query(Company).filter(Company.ticker == ticker).first()
                if not company:
                    continue
                existing = (
                    db.query(FinancialStatement)
                    .filter(
                        FinancialStatement.company_id == company.id,
                        FinancialStatement.period == period,
                    )
                    .first()
                )
                data = {col: row.get(col) for col in FLOAT_COLS}
                if existing:
                    for k, v in data.items():
                        setattr(existing, k, v)
                    db.commit()
                    db.refresh(existing)
                    stmt = existing
                else:
                    stmt = FinancialStatement(
                        company_id=company.id,
                        period=period,
                        source_name="synthetic",
                        **data,
                    )
                    db.add(stmt)
                    db.commit()
                    db.refresh(stmt)
                ratios = compute_ratios(stmt)
                upsert_computed_metrics(db, company.id, period, ratios)
                affected_companies.add(company.id)
                affected_periods.add(period)
                syn_count += 1
        print(f"[seed] {syn_count} synthetic financial records inserted.")

        # ── V2 post-processing ──────────────────────────────────────────────
        print("[seed] Computing transitions…")
        for cid in affected_companies:
            compute_transitions_for_company(db, cid)

        print("[seed] Computing sector benchmarks…")
        for period in affected_periods:
            recompute_sector_benchmarks(db, period)

        print("[seed] Computing sector-normalized scores…")
        for cid in affected_companies:
            for period in affected_periods:
                recompute_sector_normalized(db, cid, period)

        # ── Default scoring model ───────────────────────────────────────────
        existing_model = (
            db.query(ScoringModel)
            .filter(ScoringModel.model_name == DEFAULT_MODEL["model_name"])
            .first()
        )
        if not existing_model:
            model = ScoringModel(
                model_name=DEFAULT_MODEL["model_name"],
                model_type=DEFAULT_MODEL["model_type"],
                version=DEFAULT_MODEL["version"],
                is_active=True,
                status="active",
                feature_set_version="v3_12metrics",
                label_strategy="sector_median_12m",
                evaluation_horizon="12m",
            )
            db.add(model)
            db.flush()
            for m in DEFAULT_MODEL["metrics"]:
                db.add(ScoringModelMetric(
                    scoring_model_id=model.id,
                    feature_name=m["feature_name"],
                    weight=m["weight"],
                    direction=m["direction"],
                ))
            db.commit()
            print("[seed] Default scoring model 'rule_based_v2' created.")
        else:
            # Ensure V3 fields are populated
            if not existing_model.status:
                existing_model.status = "active"
                existing_model.feature_set_version = "v3_12metrics"
                existing_model.label_strategy = "sector_median_12m"
                existing_model.evaluation_horizon = "12m"
                db.commit()
            print("[seed] Default scoring model already exists, skipping.")

        # ── Default label definition (V3) ───────────────────────────────────
        existing_label = db.query(LabelDefinition).filter(LabelDefinition.is_active == True).first()
        if not existing_label:
            ld = LabelDefinition(
                name="Sector Median (12m)",
                description="Success if rule-based score >= sector median. Horizon: 12 months.",
                sector_benchmark_type="sector_median",
                horizon_months=12,
                threshold_rule="score >= sector_median",
                sector_adjustment_mode="z_score",
                success_threshold=0.55,
                is_active=True,
            )
            db.add(ld)
            db.commit()
            print("[seed] Default label definition created.")
        else:
            print("[seed] Active label definition already exists, skipping.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
    print("[seed] Done.")

