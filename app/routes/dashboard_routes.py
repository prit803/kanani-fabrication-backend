from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("")
def get_dashboard(
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
):
    return DashboardService.get_dashboard(
        db=db,
        from_date=from_date,
        to_date=to_date,
    )
