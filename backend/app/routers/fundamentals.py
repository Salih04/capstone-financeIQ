from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.forecasting import FundamentalsUploadResponse
from app.services.fundamentals_service import upload_quarterly_fundamentals_csv

router = APIRouter(tags=["fundamentals"])


@router.post("/fundamentals/upload-csv", response_model=FundamentalsUploadResponse)
async def upload_fundamentals_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="Please upload a CSV file.")
    content = await file.read()
    try:
        return upload_quarterly_fundamentals_csv(db, content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
