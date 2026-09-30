from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.location_service import LocationService

router = APIRouter(prefix="/coverage", tags=["coverage"])


@router.get("")
def get_source_coverage(db: Session = Depends(get_db)):
    """Return geographic source coverage metrics."""
    service = LocationService(db)
    return service.get_source_coverage()

