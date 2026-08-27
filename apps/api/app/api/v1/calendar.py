from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.calendar import CalendarResponse
from app.services.calendar import CalendarService

router = APIRouter(prefix="/calendar", tags=["Calendar"])


@router.get("", response_model=CalendarResponse)
def get_calendar(
    month: Optional[str] = Query(None, json_schema_extra={"example": "2026-08"}, description="Target month in format YYYY-MM"),
    db: Session = Depends(get_db)
):
    try:
        if month is None:
            month = date.today().strftime("%Y-%m")
        service = CalendarService(db)
        return service.get_monthly_calendar(month)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
