"""
routers/works.py — CRUD операции для плановых работ.
С проверкой прав доступа к сервисам.
"""
import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user, CurrentUser, check_service_access, get_accessible_services
from models import (
    PlannedWork, PlannedWorkCreate, PlannedWorkUpdate, PlannedWorkResponse
)
from zabbix_client import zabbix_client
from audit import log_work_action

logger = logging.getLogger(__name__)

router = APIRouter(tags=["works"])


@router.get("/works", response_model=List[PlannedWorkResponse])
def list_works(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Получение списка плановых работ.
    Обычные пользователи видят только свои работы.
    Администраторы видят все работы.
    """
    query = db.query(PlannedWork)
    
    # Фильтрация по статусу
    if status:
        query = query.filter(PlannedWork.status == status)
    
    # Фильтрация по доступу (не администраторы видят только свои работы)
    if not current_user.is_admin:
        # Получаем доступные сервисы
        accessible_ids = get_accessible_services(current_user, db)
        if accessible_ids:
            query = query.filter(
                (PlannedWork.service_id_zabbix.in_(accessible_ids)) |
                (PlannedWork.created_by == current_user.username)
            )
        else:
            query = query.filter(PlannedWork.created_by == current_user.username)
    
    return query.order_by(PlannedWork.start_time.desc()).all()


@router.get("/works/{work_id}", response_model=PlannedWorkResponse)
def get_work(
    work_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Получение конкретной плановой работы по ID."""
    db_work = db.query(PlannedWork).filter(PlannedWork.id == work_id).first()
    if not db_work:
        raise HTTPException(status_code=404, detail="Work not found")
    
    # Проверка доступа
    if not current_user.is_admin:
        accessible_ids = get_accessible_services(current_user, db)
        if db_work.service_id_zabbix not in accessible_ids and db_work.created_by != current_user.username:
            raise HTTPException(status_code=403, detail="Нет доступа к этой работе")
    
    return db_work


@router.post("/works", response_model=PlannedWorkResponse, status_code=201)
def create_work(
    work: PlannedWorkCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Создание новой плановой работы.
    Проверяет права доступа к сервису.
    """
    # Валидация: end > start
    if work.end_time <= work.start_time:
        raise HTTPException(
            status_code=400,
            detail="End time must be after start time"
        )
    
    # Проверка доступа к сервису
    if work.service_id_zabbix:
        has_access = check_service_access(current_user, work.service_id_zabbix, db)
        if not has_access:
            raise HTTPException(
                status_code=403,
                detail=f"У вас нет доступа к сервису '{work.service_name}'. Обратитесь к администратору."
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
        created_by=current_user.username,  # Сохраняем реального пользователя
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
        logger.error(f"Failed to create Zabbix exclusion: {e}")
        db_work.zabbix_exclusion_created = False
    
    db.add(db_work)
    db.commit()
    db.refresh(db_work)
    
    # Запись в аудит-лог
    log_work_action(
        db=db,
        username=current_user.username,
        action="create",
        work=db_work,
        request=request,
    )
    
    logger.info(f"Work '{db_work.work_title}' created by '{current_user.username}'")
    return db_work


@router.patch("/works/{work_id}", response_model=PlannedWorkResponse)
def update_work(
    work_id: int,
    update: PlannedWorkUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Обновление статуса плановой работы.
    Пользователь может изменять только свои работы (или все, если админ).
    """
    db_work = db.query(PlannedWork).filter(PlannedWork.id == work_id).first()
    if not db_work:
        raise HTTPException(status_code=404, detail="Work not found")
    
    # Проверка доступа
    if not current_user.is_admin:
        if db_work.created_by != current_user.username:
            raise HTTPException(
                status_code=403,
                detail="Вы можете изменять только свои работы"
            )
    
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
    
    # Запись в аудит-лог
    log_work_action(
        db=db,
        username=current_user.username,
        action="update",
        work=db_work,
        request=request,
    )
    
    logger.info(f"Work '{db_work.id}' updated by '{current_user.username}'")
    return db_work


@router.delete("/works/{work_id}", status_code=204)
def delete_work(
    work_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Удаление плановой работы.
    Пользователь может удалять только свои работы (или все, если админ).
    """
    db_work = db.query(PlannedWork).filter(PlannedWork.id == work_id).first()
    if not db_work:
        raise HTTPException(status_code=404, detail="Work not found")
    
    # Проверка доступа
    if not current_user.is_admin:
        if db_work.created_by != current_user.username:
            raise HTTPException(
                status_code=403,
                detail="Вы можете удалять только свои работы"
            )
    
    work_title = db_work.work_title
    
    # Запись в аудит-лог перед удалением
    log_work_action(
        db=db,
        username=current_user.username,
        action="delete",
        work=db_work,
        request=request,
    )
    
    db.delete(db_work)
    db.commit()
    
    logger.info(f"Work '{work_title}' deleted by '{current_user.username}'")
