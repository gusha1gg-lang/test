"""
routers/calendar.py — Эндпоинты для календаря плановых работ.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import extract, and_

from database import get_db
from auth import get_current_user, User
from models import PlannedWork, PlannedWorkResponse

router = APIRouter(tags=["calendar"])


@router.get("/calendar", response_model=list[PlannedWorkResponse])
def get_calendar_works(
    year: int = Query(..., description="Год"),
    month: int = Query(..., ge=1, le=12, description="Месяц (1-12)"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Получение работ для календаря за указанный месяц.
    Возвращает все работы, которые пересекаются с данным месяцем.
    """
    works = db.query(PlannedWork).filter(
        and_(
            extract('year', PlannedWork.start_time) == year,
            extract('month', PlannedWork.start_time) == month,
        )
    ).order_by(PlannedWork.start_time.asc()).all()

    return works
