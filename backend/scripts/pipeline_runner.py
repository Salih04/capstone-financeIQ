from __future__ import annotations

from app.database import SessionLocal
from app.services.forecasting_service import get_available_filters, run_time_cv_evaluation
from scripts.incremental_retrain import main as incremental_main


def main() -> None:
    incremental_main()

    db = SessionLocal()
    try:
      filters = get_available_filters(db)
      sectors = filters.get("sectors", [])
      for s in sectors:
          try:
              res = run_time_cv_evaluation(db, sector=s, model_type="scoring", window_size=2)
              print(f"[EVAL] {s}: folds={res['total_folds']} mean_stability={res['mean_rank_stability']}")
          except Exception as exc:
              print(f"[EVAL] {s}: skipped ({exc})")
    finally:
      db.close()


if __name__ == "__main__":
    main()
