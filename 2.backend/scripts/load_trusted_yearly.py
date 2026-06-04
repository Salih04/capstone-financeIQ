"""Single, deterministic loader for the trusted yearly dataset.

Pipeline:
    3.Datasets/*stocks.xlsx  --convert-->  data/trusted/stocks_2020_2025.csv
                             --load------>  Postgres: yearly_stocks + companies

This is the ONLY sanctioned way trusted financial data enters the database.
There is no seeder, no synthetic generator, no scraper, and no external API in
this path. It is idempotent (upsert on ticker+year) and strict (aborts on any
validation error rather than committing partial/incorrect data).

Usage (inside the backend container or a venv with DATABASE_URL set):

    python -m scripts.load_trusted_yearly             # convert if needed + load
    python -m scripts.load_trusted_yearly --reconvert # force XLSX->CSV first
    python -m scripts.load_trusted_yearly --summary    # DB summary only, no write
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import func

from app.database import Base, SessionLocal, engine
from app.models.company import Company
from app.models.trusted import YearlyStock
from app.trusted_data import OUTPUT_COLUMNS, summarize_frame, validate_frame

REPO_ROOT = Path(__file__).resolve().parents[2]
# Env override keeps this correct in Docker, where /app == 2.backend.
COMBINED_CSV = Path(
    os.environ.get(
        "TRUSTED_COMBINED_CSV",
        str(REPO_ROOT / "data" / "trusted" / "stocks_2020_2025.csv"),
    )
)

# Columns persisted to yearly_stocks (everything the contract defines + year).
_PERSIST_COLUMNS = ("ticker", "year") + tuple(
    c for c in OUTPUT_COLUMNS if c not in ("ticker", "year")
) + ("source_file",)


def _ensure_combined_csv(reconvert: bool) -> Path:
    if reconvert or not COMBINED_CSV.is_file():
        from scripts.convert_trusted_xlsx import main as convert_main

        print("Combined trusted CSV missing or --reconvert set; converting XLSX...")
        rc = convert_main()
        if rc != 0:
            raise SystemExit("XLSX->CSV conversion failed; aborting load.")
    return COMBINED_CSV


def _row_payload(row: pd.Series) -> dict:
    payload = {}
    for col in _PERSIST_COLUMNS:
        if col not in row:
            continue
        val = row[col]
        if col == "ticker":
            payload[col] = str(val).strip().upper()
        elif col in ("year",):
            payload[col] = int(val)
        elif col in ("indices", "source_file"):
            payload[col] = None if pd.isna(val) else str(val)
        else:
            payload[col] = None if pd.isna(val) else float(val)
    return payload


def _load(db) -> tuple[int, int]:
    df = pd.read_csv(COMBINED_CSV)
    errors = validate_frame(df, COMBINED_CSV.name)
    if errors:
        raise SystemExit("Refusing to load; trusted CSV invalid:\n  " + "\n  ".join(errors))

    created = updated = 0
    for _, row in df.iterrows():
        payload = _row_payload(row)
        existing = (
            db.query(YearlyStock)
            .filter(YearlyStock.ticker == payload["ticker"], YearlyStock.year == payload["year"])
            .first()
        )
        if existing:
            for k, v in payload.items():
                setattr(existing, k, v)
            updated += 1
        else:
            db.add(YearlyStock(**payload))
            created += 1
    db.commit()
    return created, updated


def _sync_companies(db) -> int:
    """Company universe derived from the trusted data only.

    Trusted XLSX has no sector column, so sector stays NULL (we do not invent
    one). Ticker is used as the display name until a real name source exists.
    """
    tickers = [t[0] for t in db.query(YearlyStock.ticker).distinct().all()]
    touched = 0
    for ticker in tickers:
        existing = db.query(Company).filter(Company.ticker == ticker).first()
        if existing:
            existing.is_active = True
        else:
            db.add(Company(ticker=ticker, company_name=ticker, is_active=True))
        touched += 1
    db.commit()
    return touched


def _summary(db) -> None:
    total = db.query(func.count(YearlyStock.id)).scalar()
    years = [y[0] for y in db.query(YearlyStock.year).distinct().order_by(YearlyStock.year).all()]
    companies = db.query(func.count(Company.id)).scalar()
    print(f"  yearly_stocks rows : {total}")
    print(f"  years              : {years}")
    print(f"  companies          : {companies}")
    for y in years:
        n = db.query(func.count(YearlyStock.id)).filter(YearlyStock.year == y).scalar()
        print(f"    {y}: {n} stocks")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reconvert", action="store_true", help="force XLSX->CSV before loading")
    ap.add_argument("--summary", action="store_true", help="print DB summary only")
    args = ap.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if args.summary:
            print("Current trusted yearly state:")
            _summary(db)
            return 0

        csv_path = _ensure_combined_csv(args.reconvert)
        print(f"Loading trusted yearly data: {csv_path}")
        created, updated = _load(db)
        companies = _sync_companies(db)
        print(f"Loaded: {created} created, {updated} updated, {companies} companies synced.")
        print("Summary:")
        _summary(db)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
