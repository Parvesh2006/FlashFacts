from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.analytics import PerformanceAnalyticsResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/performance", response_model=PerformanceAnalyticsResponse)
def get_performance_analytics(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve personal performance analytics calculated exclusively from
    the authenticated student's real stored test attempts and mistake records.
    """
    service = AnalyticsService(db)
    return service.get_user_analytics(user_id=user.id)
