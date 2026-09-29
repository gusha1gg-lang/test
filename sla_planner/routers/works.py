"""
routers/works.py — CRUD операции для плановых работ.
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user, User
from models import (
    PlannedWork, PlannedWorkCreate, PlannedWorkUpdate, PlannedWorkResponse
)
from zabbix_client import zabbix_client

router = APIRouter(tags=["works"])


@router.get("/works", response_model=list[PlannedWorkResponse])
def list_works(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Получение списка плановых работ с фильтрацией по статусу."""
    query = db.query(PlannedWork)
    if status:
        query = query.filter(PlannedWork.status == status)
    return query.order_by(PlannedWork.start_time.desc()).all()


@router.get("/works/{work_id}", response_model=PlannedWorkResponse)
def get_work(
    work_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Получение конкретной плановой работы по ID."""
    db_work = db.query(PlannedWork).filter(PlannedWork.id == work_id).first()
    if not db_work:
        raise HTTPException(status_code=404, detail="Work not found")
    return db_work


@router.post("/works", response_model=PlannedWorkResponse, status_code=201)
def create_work(
    work: PlannedWorkCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Создание новой плановой работы.
    Автоматически пытается создать исключение SLA в Zabbix.
    """
    # Валидация: end > start
    if work.end_time <= work.start_time:
        raise HTTPException(
            status_code=400,
            detail="End time must be after start time"
        )

    # Создание записи в БД
    db_work = PlannedWork(
        service_name=work.service_name,
        service_id_zabbix=work.service_id_zabbix,
        work_title=work.work_title,
        description=work.description,
        start_time=work.start_time,
        end_time=work.end_time,
        status="planned",
        created_by=user.username,
    )

    # Попытка создать исключение в Zabbix
    try:
        success = zabbix_client.create_sla_exclusion(
            service_name=work.service_name,
            start_timestamp=work.start_time.timestamp(),
            end_timestamp=work.end_time.timestamp(),
            description=work.work_title,
        )
        db_work.zabbix_exclusion_created = success
    except Exception as e:
        # Если Zabbix недоступен — просто сохраняем без исключения
        db_work.zabbix_exclusion_created = False

    db.add(db_work)
    db.commit()
    db.refresh(db_work)
    return db_work


@router.patch("/works/{work_id}", response_model=PlannedWorkResponse)
def update_work(
    work_id: int,
    update: PlannedWorkUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Обновление статуса плановой работы."""
    db_work = db.query(PlannedWork).filter(PlannedWork.id == work_id).first()
    if not db_work:
        raise HTTPException(status_code=404, detail="Work not found")

    if update.status is not None:
        valid_statuses = ["planned", "in_progress", "completed", "cancelled"]
        if update.status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {valid_statuses}"
            )
        db_work.status = update.status

    if update.zabbix_exclusion_created is not None:
        db_work.zabbix_exclusion_created = update.zabbix_exclusion_created

    db.commit()
    db.refresh(db_work)
    return db_work


@router.delete("/works/{work_id}", status_code=204)
def delete_work(
    work_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Удаление плановой работы."""
    db_work = db.query(PlannedWork).filter(PlannedWork.id == work_id).first()
    if not db_work:
        raise HTTPException(status_code=404, detail="Work not found")

    db.delete(db_work)
    db.commit()
