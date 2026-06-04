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
from scripts.import_datasets import main as import_datasets

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

# ── Schema migrations: add new columns to existing tables ────────────────────
_NEW_COMPUTED_METRIC_COLS = [
    "gross_profit_margin", "ebitda_margin", "roic",
    "revenue_growth", "ebitda_growth", "net_income_growth",
    "pe_ratio", "pb_ratio", "ev_ebitda", "ev_sales", "peg_ratio", "working_capital",
]

with engine.begin() as _conn:
    for _col in _NEW_COMPUTED_METRIC_COLS:
        _conn.execute(text(
            f"ALTER TABLE computed_metrics ADD COLUMN IF NOT EXISTS {_col} FLOAT"
        ))
    # stock_returns is created by create_all above (new table), so no ALTER needed

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
    # ── Additional companies from 3.Datasets ────────────────────────────────
    {"ticker": "ASTOR",  "company_name": "Astor Enerji A.Ş.",                                    "sector": "Enerji",                  "sector_code": "ENERJI"},
    {"ticker": "BRSAN",  "company_name": "Borçelik Çelik Sanayii T.A.Ş.",                       "sector": "Demir-Çelik",             "sector_code": "DEMIR_CELIK"},
    {"ticker": "BTCIM",  "company_name": "Batıçim Batı Anadolu Çimento Sanayii A.Ş.",           "sector": "Çimento",                 "sector_code": "CIMENTO"},
    {"ticker": "CANTE",  "company_name": "Cante Yazılım ve Bilgi Teknolojileri A.Ş.",           "sector": "Teknoloji",               "sector_code": "TEKNOLOJI"},
    {"ticker": "CCOLA",  "company_name": "Coca-Cola İçecek A.Ş.",                                "sector": "Gıda & İçecek",           "sector_code": "GIDA"},
    {"ticker": "CIMSA",  "company_name": "Çimsa Çimento Sanayi ve Ticaret A.Ş.",               "sector": "Çimento",                 "sector_code": "CIMENTO"},
    {"ticker": "DSTKF",  "company_name": "Doğuş Teknoloji ve Finansman A.Ş.",                   "sector": "Finans",                  "sector_code": "FINANS"},
    {"ticker": "GUBRF",  "company_name": "Gübre Fabrikaları T.A.Ş.",                             "sector": "Kimya",                   "sector_code": "KIMYA"},
    {"ticker": "HEKTS",  "company_name": "Hektaş Ticaret T.A.Ş.",                               "sector": "Kimya",                   "sector_code": "KIMYA"},
    {"ticker": "KONTR",  "company_name": "Kontrolmatik Teknoloji A.Ş.",                          "sector": "Teknoloji",               "sector_code": "TEKNOLOJI"},
    {"ticker": "KUYAS",  "company_name": "Kuyaş Yatırım ve Gayrimenkul A.Ş.",                   "sector": "Gayrimenkul",             "sector_code": "GAYRIMENKUL"},
    {"ticker": "MAVI",   "company_name": "Mavi Giyim Sanayi ve Ticaret A.Ş.",                   "sector": "Tekstil & Perakende",     "sector_code": "TEKSTIL"},
    {"ticker": "MIATK",  "company_name": "MİA Teknoloji A.Ş.",                                   "sector": "Teknoloji",               "sector_code": "TEKNOLOJI"},
    {"ticker": "OYAKC",  "company_name": "Oyak Çimento Fabrikaları A.Ş.",                       "sector": "Çimento",                 "sector_code": "CIMENTO"},
    {"ticker": "PASEU",  "company_name": "Paşabahçe Cam Sanayi ve Ticaret A.Ş.",               "sector": "Cam",                     "sector_code": "CAM"},
    {"ticker": "TRALT",  "company_name": "Trakya Alüminyum Sanayi A.Ş.",                         "sector": "Metal",                   "sector_code": "METAL"},
    {"ticker": "TRMET",  "company_name": "Trakya Metal Sanayi A.Ş.",                             "sector": "Metal",                   "sector_code": "METAL"},
    {"ticker": "TSKB",   "company_name": "Türkiye Sınai Kalkınma Bankası A.Ş.",                 "sector": "Bankacılık",              "sector_code": "BANKACILIK"},
    {"ticker": "TURSG",  "company_name": "Türkiye Sigorta A.Ş.",                                 "sector": "Sigorta",                 "sector_code": "SIGORTA"},
]

FLOAT_COLS = [
    "revenue", "net_income", "total_assets", "total_equity", "total_liabilities",
    "current_assets", "current_liabilities", "cash", "operating_cash_flow",
    "operating_income", "gross_profit", "inventory",
]

# Synthetic financial parameters are disabled. The app relies solely on
# uploaded datasets in 3.Datasets.
SYNTHETIC_DATA = []

def _syn_financial_rows(ticker, rev4, ni_pct, assets4, eq_pct, ca_pct, cl_pct,
                         cash_pct, ocf_pct, op_pct, gp_pct, inv_pct):
    """Deprecated: synthetic seed data disabled by default."""
    return []

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

        # ── Financial data from 3.Datasets xlsx ────────────────────────────
        print("[seed] Importing datasets from 3.Datasets…")
        import_datasets()

        # Collect all company IDs and periods for post-processing
        from app.models.financial import ComputedMetric as CM
        _metrics = db.query(CM.company_id, CM.period).distinct().all()
        affected_companies: set[int] = {r[0] for r in _metrics}
        affected_periods: set[str] = {r[1] for r in _metrics}

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
