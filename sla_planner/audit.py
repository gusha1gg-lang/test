"""
audit.py — Модуль аудита для записи действий пользователей.
"""
import json
import logging
from typing import Optional, Any
from datetime import datetime
from fastapi import Request
from sqlalchemy.orm import Session

from models import AuditLog

logger = logging.getLogger(__name__)


def log_action(
    db: Session,
    username: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    resource_name: Optional[str] = None,
    details: Optional[dict] = None,
    request: Optional[Request] = None,
):
    """
    Запись действия в аудит-лог.
    
    Args:
        db: Сессия БД
        username: Имя пользователя
        action: Тип действия (create, update, delete, login, logout)
        resource_type: Тип ресурса (work, user, group, service)
        resource_id: ID ресурса
        resource_name: Название ресурса
        details: Дополнительные данные (dict)
        request: HTTP запрос (для извлечения IP и User-Agent)
    """
    try:
        # Извлекаем IP и User-Agent из запроса
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
        
        # Сериализуем details в JSON
        details_json = None
        if details:
            try:
                details_json = json.dumps(details, ensure_ascii=False, default=str)
            except Exception as e:
                logger.warning(f"Failed to serialize audit details: {e}")
                details_json = str(details)
        
        # Создаём запись
        log_entry = AuditLog(
            timestamp=datetime.utcnow(),
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            resource_name=resource_name,
            details=details_json,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        db.add(log_entry)
        db.commit()
        
        logger.info(f"Audit: {username} {action} {resource_type} {resource_id or resource_name}")
        
    except Exception as e:
        # Не прерываем работу приложения при ошибке логирования
        logger.error(f"Failed to write audit log: {e}")
        # Откатываем транзакцию, если она была
        try:
            db.rollback()
        except:
            pass


def log_work_action(
    db: Session,
    username: str,
    action: str,
    work: Any,
    request: Optional[Request] = None,
):
    """Удобный хелпер для логирования действий с плановыми работами."""
    log_action(
        db=db,
        username=username,
        action=action,
        resource_type="work",
        resource_id=work.id,
        resource_name=work.work_title,
        details={
            "service_name": work.service_name,
            "service_id": work.service_id_zabbix,
            "start_time": str(work.start_time),
            "end_time": str(work.end_time),
            "status": work.status,
        },
        request=request,
    )


def log_user_action(
    db: Session,
    username: str,
    action: str,
    user: Any,
    request: Optional[Request] = None,
):
    """Удобный хелпер для логирования действий с пользователями."""
    log_action(
        db=db,
        username=username,
        action=action,
        resource_type="user",
        resource_id=user.id,
        resource_name=user.username,
        details={
            "email": user.email,
            "full_name": user.full_name,
            "is_admin": user.is_admin,
        },
        request=request,
    )


def log_group_action(
    db: Session,
    username: str,
    action: str,
    group: Any,
    request: Optional[Request] = None,
):
    """Удобный хелпер для логирования действий с группами."""
    log_action(
        db=db,
        username=username,
        action=action,
        resource_type="group",
        resource_id=group.id,
        resource_name=group.name,
        details={
            "description": group.description,
            "services_count": len(group.services) if hasattr(group, 'services') else 0,
        },
        request=request,
    )
