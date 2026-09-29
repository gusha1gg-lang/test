"""
models.py — SQLAlchemy модели и Pydantic схемы.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from database import Base
from pydantic import BaseModel


# ============================================
# SQLAlchemy модели (таблицы БД)
# ============================================

class PlannedWork(Base):
    """Модель плановой работы."""
    __tablename__ = "planned_works"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_name = Column(String, nullable=False, index=True)
    service_id_zabbix = Column(String, nullable=True)
    work_title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="planned")  # planned/in_progress/completed/cancelled
    zabbix_exclusion_created = Column(Boolean, default=False)
    created_by = Column(String, default="Admin")  # Потом — из ADFS токена
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================
# Pydantic схемы (валидация запросов/ответов)
# ============================================

class PlannedWorkCreate(BaseModel):
    """Схема для создания новой плановой работы."""
    service_name: str
    service_id_zabbix: Optional[str] = None
    work_title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime


class PlannedWorkUpdate(BaseModel):
    """Схема для обновления статуса работы."""
    status: Optional[str] = None
    zabbix_exclusion_created: Optional[bool] = None


class PlannedWorkResponse(BaseModel):
    """Схема ответа с данными работы."""
    id: int
    service_name: str
    service_id_zabbix: Optional[str]
    work_title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    status: str
    zabbix_exclusion_created: bool
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ServiceNode(BaseModel):
    """Узел дерева сервисов."""
    id: str
    name: str
    status: str  # ok, warning, problem
    algorithm: Optional[str] = None
    parent_id: Optional[str] = None
    children: List[str] = []


class ServicesTreeResponse(BaseModel):
    """Ответ с деревом сервисов для vis-network."""
    nodes: List[ServiceNode]
    edges: List[dict]


class HealthResponse(BaseModel):
    """Ответ health-check."""
    status: str
    zabbix_connected: bool
    mode: str  # demo / production
    services_count: int
    works_count: int


class CalendarWork(BaseModel):
    """Работа для календаря."""
    id: int
    service_name: str
    work_title: str
    start_time: datetime
    end_time: datetime
    status: str
