from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    score_run_id: Mapped[int | None] = mapped_column(ForeignKey("score_runs.id"), nullable=True)
    report_type: Mapped[str] = mapped_column(String(10), nullable=False)  # pdf | csv | json
    file_path: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="reports")
    score_run: Mapped["ScoreRun | None"] = relationship("ScoreRun", back_populates="reports")
