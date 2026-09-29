"""
routers/audit.py — Эндпоинты для просмотра аудит-лога.
"""
import logging
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from auth import get_current_user, CurrentUser
from models import AuditLog, AuditLogResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["audit"])


@router.get("/audit", response_model=List[AuditLogResponse])
def get_audit_logs(
    limit: int = Query(100, ge=1, le=1000, description="Максимум записей"),
    offset: int = Query(0, ge=0, description="Смещение"),
    username: Optional[str] = Query(None, description="Фильтр по пользователю"),
    action: Optional[str] = Query(None, description="Фильтр по действию"),
    resource_type: Optional[str] = Query(None, description="Фильтр по типу ресурса"),
    date_from: Optional[datetime] = Query(None, description="Начальная дата"),
    date_to: Optional[datetime] = Query(None, description="Конечная дата"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Получение аудит-лога.
    Только для администраторов.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Только администраторы могут просматривать аудит-лог"
        )
    
    # Базовый запрос
    query = db.query(AuditLog)
    
    # Фильтры
    if username:
        query = query.filter(AuditLog.username == username)
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    
    if date_from:
        query = query.filter(AuditLog.timestamp >= date_from)
    
    if date_to:
        query = query.filter(AuditLog.timestamp <= date_to)
    
    # Сортировка и пагинация
    logs = query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit).all()
    
    return logs


@router.get("/audit/stats")
def get_audit_stats(
    days: int = Query(7, ge=1, le=365, description="Период в днях"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Статистика по аудит-логу за период.
    Только для администраторов.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Только администраторы могут просматривать статистику аудита"
        )
    
    date_from = datetime.utcnow() - timedelta(days=days)
    
    # Общее количество действий
    total_actions = db.query(AuditLog).filter(
        AuditLog.timestamp >= date_from
    ).count()
    
    # Действия по типам
    actions_by_type = db.query(
        AuditLog.action,
        db.query.func.count(AuditLog.id)
    ).filter(
        AuditLog.timestamp >= date_from
    ).group_by(AuditLog.action).all()
    
    # Действия по пользователям
    actions_by_user = db.query(
        AuditLog.username,
        db.query.func.count(AuditLog.id)
    ).filter(
        AuditLog.timestamp >= date_from
    ).group_by(AuditLog.username).all()
    
    # Действия по типам ресурсов
    actions_by_resource = db.query(
        AuditLog.resource_type,
        db.query.func.count(AuditLog.id)
    ).filter(
        AuditLog.timestamp >= date_from
    ).group_by(AuditLog.resource_type).all()
    
    return {
        "period_days": days,
        "total_actions": total_actions,
        "actions_by_type": dict(actions_by_type),
        "actions_by_user": dict(actions_by_user),
        "actions_by_resource": dict(actions_by_resource),
    }


@router.get("/audit/users")
def get_audit_users(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Список пользователей из аудит-лога (для фильтра).
    Только для администраторов.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Только администраторы могут просматривать аудит-лог"
        )
    
    users = db.query(AuditLog.username).distinct().all()
    return [u[0] for u in users]
