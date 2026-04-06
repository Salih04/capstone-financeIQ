from __future__ import annotations

from app.database import SessionLocal
from app.services.forecasting_service import (
    get_available_filters,
    run_forecast_for_sector,
    train_sector_success_model,
)


def main() -> None:
    db = SessionLocal()
    try:
        filters = get_available_filters(db)
        years = filters.get("years", [])
        sectors = filters.get("sectors", [])

        if not years or not sectors:
            print("No forecasting data found. Import winner files first.")
            return

        latest_year = max(years)
        print(f"Retraining forecasting models for year={latest_year} across {len(sectors)} sectors")

        for sector in sectors:
            train_sector_success_model(db, year=latest_year, sector=sector, top_n_parameters=8)
            result = run_forecast_for_sector(
                db,
                year=latest_year,
                sector=sector,
                created_by_user_id=None,
                user_type="scheduled",
                risk_level="medium",
                investment_scope=None,
            )
            print(f"- {sector}: run_id={result['run_id']} stocks={len(result['items'])}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
