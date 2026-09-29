"""
models.py — SQLAlchemy модели и Pydantic схемы.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from pydantic import BaseModel


# ============================================
# SQLAlchemy модели (таблицы БД)
# ============================================

# Таблица связи пользователей и групп (многие-ко-многим)
user_group_association = Table(
    'user_group_association',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('group_id', Integer, ForeignKey('user_groups.id'))
)

# Таблица связи групп и сервисов (многие-ко-многим)
group_service_association = Table(
    'group_service_association',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('user_groups.id')),
    Column('service_id', String, ForeignKey('services.id'))
)


class User(Base):
    """Модель пользователя."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=True)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связь с группами
    groups = relationship("UserGroup", secondary=user_group_association, back_populates="users")


class UserGroup(Base):
    """Модель группы пользователей."""
    __tablename__ = "user_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связь с пользователями
    users = relationship("User", secondary=user_group_association, back_populates="groups")
    # Связь с сервисами
    services = relationship("Service", secondary=group_service_association, back_populates="groups")


class Service(Base):
    """Модель сервиса (ИС) из Zabbix."""
    __tablename__ = "services"

    id = Column(String, primary_key=True)  # ID из Zabbix
    name = Column(String, nullable=False)
    status = Column(String, default="ok")
    algorithm = Column(String, nullable=True)
    parent_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связь с группами
    groups = relationship("UserGroup", secondary=group_service_association, back_populates="services")


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
    created_by = Column(String, nullable=False)  # username пользователя
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    """Модель аудита — запись всех действий пользователей."""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    username = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False)  # create, update, delete, login, logout
    resource_type = Column(String, nullable=False)  # work, user, group, service
    resource_id = Column(String, nullable=True)  # ID объекта
    resource_name = Column(String, nullable=True)  # Название объекта для удобства
    details = Column(Text, nullable=True)  # JSON с деталями изменения
    ip_address = Column(String, nullable=True)  # IP адрес пользователя
    user_agent = Column(String, nullable=True)  # Браузер/клиент


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


# ============================================
# Pydantic схемы для пользователей и групп
# ============================================

class UserCreate(BaseModel):
    """Схема создания пользователя."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_admin: bool = False
    group_ids: List[int] = []


class UserUpdate(BaseModel):
    """Схема обновления пользователя."""
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    group_ids: Optional[List[int]] = None


class UserResponse(BaseModel):
    """Схема ответа с данными пользователя."""
    id: int
    username: str
    email: Optional[str]
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime
    groups: List["GroupResponse"] = []

    class Config:
        from_attributes = True


class GroupCreate(BaseModel):
    """Схема создания группы."""
    name: str
    description: Optional[str] = None
    service_ids: List[str] = []


class GroupUpdate(BaseModel):
    """Схема обновления группы."""
    name: Optional[str] = None
    description: Optional[str] = None
    service_ids: Optional[List[str]] = None


class GroupResponse(BaseModel):
    """Схема ответа с данными группы."""
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    users_count: int = 0
    services_count: int = 0
    services: List["ServiceResponse"] = []

    class Config:
        from_attributes = True


class ServiceResponse(BaseModel):
    """Схема ответа с данными сервиса."""
    id: str
    name: str
    status: str
    algorithm: Optional[str]
    parent_id: Optional[str]

    class Config:
        from_attributes = True


class UserAccessCheck(BaseModel):
    """Проверка доступа пользователя к сервису."""
    username: str
    service_id: str
    has_access: bool
    reason: str


class AuditLogResponse(BaseModel):
    """Схема ответа с данными аудита."""
    id: int
    timestamp: datetime
    username: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    resource_name: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]

    class Config:
        from_attributes = True


# Обновляем forward references
UserResponse.model_rebuild()
GroupResponse.model_rebuild()
