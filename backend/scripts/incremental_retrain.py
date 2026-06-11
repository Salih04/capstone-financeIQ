from __future__ import annotations

from app.database import SessionLocal
from app.models.forecasting import ForecastRun, WinnerCohortRow
from app.services.forecasting_service import run_forecast_for_sector, train_sector_success_model


def main() -> None:
    db = SessionLocal()
    try:
        latest_run_year = db.query(ForecastRun.year).order_by(ForecastRun.year.desc()).first()
        latest_data_year = db.query(WinnerCohortRow.year).order_by(WinnerCohortRow.year.desc()).first()

        if not latest_data_year:
            print("No winner cohort data available.")
            return

        data_year = int(latest_data_year[0])
        prev_year = int(latest_run_year[0]) if latest_run_year else None

        if prev_year is not None and data_year <= prev_year:
            print(f"No new data year detected (latest data year={data_year}, latest run year={prev_year}).")
            return

        sectors = sorted({r[0] for r in db.query(WinnerCohortRow.sector).filter(WinnerCohortRow.year == data_year).distinct().all()})
        print(f"New data detected for year={data_year}. Incremental retrain for {len(sectors)} sectors.")

        for s in sectors:
            train_sector_success_model(db, year=data_year, sector=s, top_n_parameters=8)
            res = run_forecast_for_sector(
                db,
                year=data_year,
                sector=s,
                created_by_user_id=None,
                user_type="incremental",
                risk_level="medium",
                model_type="scoring",
            )
            print(f"- {s}: run_id={res['run_id']} stocks={len(res['items'])}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
