"""
Конфигурация pytest для интеграционных тестов.
Содержит фикстуры для тестового окружения.
"""
import pytest
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sla_planner'))

from database import Base, get_db
from main import app
from models import User, UserGroup, Service, PlannedWork, AuditLog
from zabbix_client import ZabbixClient
from config import settings


# ============================================
# Фикстуры базы данных
# ============================================

@pytest.fixture(scope="session")
def test_db_engine():
    """Создание тестового движка БД."""
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db_engine) -> Session:
    """Создание сессии БД для теста."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    """Создание тестового клиента FastAPI."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ============================================
# Фикстуры пользователей
# ============================================

@pytest.fixture
def admin_user(db_session):
    """Создание тестового администратора."""
    user = User(
        username="test_admin",
        email="admin@test.com",
        full_name="Test Admin",
        is_admin=True,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    yield user
    db_session.delete(user)
    db_session.commit()


@pytest.fixture
def regular_user(db_session):
    """Создание тестового обычного пользователя."""
    user = User(
        username="test_user",
        email="user@test.com",
        full_name="Test User",
        is_admin=False,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    yield user
    db_session.delete(user)
    db_session.commit()


# ============================================
# Фикстуры групп
# ============================================

@pytest.fixture
def test_group(db_session):
    """Создание тестовой группы."""
    group = UserGroup(
        name="Test Group",
        description="Group for integration tests",
    )
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    yield group
    db_session.delete(group)
    db_session.commit()


# ============================================
# Фикстуры сервисов
# ============================================

@pytest.fixture
def test_services(db_session):
    """Создание тестовых сервисов."""
    services = [
        Service(
            id="1",
            name="Test Service 1",
            status="ok",
            algorithm="all",
            propagation_rule="as_problem",
            parent_id=None,
        ),
        Service(
            id="2",
            name="Test Service 2",
            status="warning",
            algorithm="min_n",
            propagation_rule="as_ok",
            parent_id="1",
        ),
    ]
    for service in services:
        db_session.add(service)
    db_session.commit()
    for service in services:
        db_session.refresh(service)
    yield services
    for service in services:
        db_session.delete(service)
    db_session.commit()


# ============================================
# Фикстуры плановых работ
# ============================================

@pytest.fixture
def sample_work(db_session, test_services):
    """Создание тестовой плановой работы."""
    work = PlannedWork(
        service_name="Test Service 1",
        service_id_zabbix="1",
        work_title="Test Maintenance",
        description="Test maintenance window",
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=1, hours=2),
        status="planned",
        zabbix_exclusion_created=False,
        created_by="test_admin",
    )
    db_session.add(work)
    db_session.commit()
    db_session.refresh(work)
    yield work
    db_session.delete(work)
    db_session.commit()


# ============================================
# Фикстуры Zabbix клиента
# ============================================

@pytest.fixture
def zabbix_client():
    """Создание клиента Zabbix для тестов."""
    client = ZabbixClient()
    client.login()
    yield client


# ============================================
# Фикстуры временных периодов
# ============================================

@pytest.fixture
def test_period():
    """Тестовый период для SLA расчётов."""
    period_from = datetime(2024, 1, 1, 0, 0, 0)
    period_to = datetime(2024, 1, 31, 23, 59, 59)
    return {
        "period_from": period_from,
        "period_to": period_to,
        "total_seconds": (period_to - period_from).total_seconds(),
    }


# ============================================
# Фикстуры для негативных тестов
# ============================================

@pytest.fixture
def invalid_dates():
    """Невалидные даты для тестов."""
    return {
        "start_time": datetime.utcnow() + timedelta(days=2),
        "end_time": datetime.utcnow() + timedelta(days=1),  # end < start
    }


@pytest.fixture
def duplicate_work(db_session, test_services):
    """Дубликат плановой работы."""
    work = PlannedWork(
        service_name="Test Service 1",
        service_id_zabbix="1",
        work_title="Duplicate Maintenance",
        description="Duplicate test",
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=1, hours=2),
        status="planned",
        zabbix_exclusion_created=False,
        created_by="test_admin",
    )
    db_session.add(work)
    db_session.commit()
    db_session.refresh(work)
    yield work
    db_session.delete(work)
    db_session.commit()


# ============================================
# Утилиты для тестов
# ============================================

@pytest.fixture
def auth_headers(admin_user):
    """Заголовки авторизации для тестов."""
    return {"Authorization": f"Bearer test_token"}


def create_test_work_data(service_id: str = "1", service_name: str = "Test Service 1"):
    """Создание тестовых данных для плановой работы."""
    return {
        "service_name": service_name,
        "service_id_zabbix": service_id,
        "work_title": "Test Maintenance",
        "description": "Test maintenance window",
        "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "end_time": (datetime.utcnow() + timedelta(days=1, hours=2)).isoformat(),
    }
