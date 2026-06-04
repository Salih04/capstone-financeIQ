"""Single source of truth loader.

Loads quarterly_fundamentals_2025.csv -- the ONLY trusted data source -- into
Postgres. It is the one and only sanctioned way fundamentals and company rows
enter the database. Every other importer/seeder has been retired to
``unnecessary/`` because it pulled data from xlsx files, synthetic generators,
or scraped HTML, which produced the jumbled/incorrect data we are replacing.

Rules enforced here:
  * No fabricated values. Anything not in the CSV stays NULL.
  * Strict parsing. If any row fails validation the whole load aborts; we do
    not commit a half-correct dataset.
  * Idempotent. Re-running upserts on (stock_code, period) and ticker.

Usage (inside the backend container or a venv with DATABASE_URL set):

    python -m scripts.load_trusted_fundamentals            # load + summary
    python -m scripts.load_trusted_fundamentals --summary  # summary only, no write

CSV location resolution order:
    1. --csv <path>
    2. $TRUSTED_FUNDAMENTALS_CSV
    3. ./quarterly_fundamentals_2025.csv (cwd)
    4. repo-root/quarterly_fundamentals_2025.csv
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from sqlalchemy import func

from app.database import Base, SessionLocal, engine
from app.models.company import Company
from app.models.forecasting import QuarterlyFundamental
from app.services.fundamentals_service import upload_quarterly_fundamentals_csv

CSV_NAME = "quarterly_fundamentals_2025.csv"


def _resolve_csv(explicit: str | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    env = os.environ.get("TRUSTED_FUNDAMENTALS_CSV")
    if env:
        candidates.append(Path(env))
    candidates.append(Path.cwd() / CSV_NAME)
    # scripts/ -> 2.backend -> repo root
    candidates.append(Path(__file__).resolve().parents[2] / CSV_NAME)

    for c in candidates:
        if c.is_file():
            return c

    tried = "\n  ".join(str(c) for c in candidates)
    raise FileNotFoundError(
        f"Trusted data source '{CSV_NAME}' not found. Looked in:\n  {tried}\n"
        "Set TRUSTED_FUNDAMENTALS_CSV or pass --csv. This file is the only "
        "accepted data source and must be present."
    )


def _sync_companies(db) -> int:
    """Create/refresh Company rows from the fundamentals already loaded.

    The trusted CSV is the sole source for the company universe too. We do not
    invent company names -- the ticker is used as the display name until a real
    name source exists.
    """
    pairs = (
        db.query(QuarterlyFundamental.stock_code, QuarterlyFundamental.sector)
        .distinct()
        .all()
    )
    touched = 0
    for ticker, sector in pairs:
        existing = db.query(Company).filter(Company.ticker == ticker).first()
        if existing:
            existing.sector = sector
            existing.is_active = True
        else:
            db.add(
                Company(
                    ticker=ticker,
                    company_name=ticker,
                    sector=sector,
                    is_active=True,
                )
            )
        touched += 1
    db.commit()
    return touched


def _print_summary(db) -> None:
    total = db.query(func.count(QuarterlyFundamental.id)).scalar()
    periods = [
        p[0]
        for p in db.query(QuarterlyFundamental.period)
        .distinct()
        .order_by(QuarterlyFundamental.period)
        .all()
    ]
    companies = db.query(func.count(Company.id)).scalar()
    print(f"  fundamentals rows : {total}")
    print(f"  distinct periods  : {periods}")
    print(f"  companies         : {companies}")
    for period in periods:
        n = (
            db.query(func.count(QuarterlyFundamental.id))
            .filter(QuarterlyFundamental.period == period)
            .scalar()
        )
        print(f"    {period}: {n} stocks")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", help="explicit path to the trusted CSV")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="print DB summary only, do not load",
    )
    args = parser.parse_args()

    # create_all is a safety net for fresh databases; Alembic owns real schema.
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if args.summary:
            print("Current trusted-fundamentals state:")
            _print_summary(db)
            return 0

        csv_path = _resolve_csv(args.csv)
        print(f"Loading trusted source: {csv_path}")
        content = csv_path.read_bytes()

        result = upload_quarterly_fundamentals_csv(db, content)
        if result["errors"]:
            # Strict: a trusted source must parse cleanly. Roll back so we never
            # leave a partially-correct dataset behind.
            db.rollback()
            joined = "\n  ".join(result["errors"])
            raise SystemExit(
                f"Refusing to load: {result['skipped']} row(s) failed validation:\n  {joined}"
            )

        companies = _sync_companies(db)
        print(
            f"Loaded: {result['created']} created, {result['updated']} updated, "
            f"{companies} companies synced."
        )
        print("Summary:")
        _print_summary(db)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
