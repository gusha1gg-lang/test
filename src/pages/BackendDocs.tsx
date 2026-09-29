import React, { useState } from 'react';

const BackendDocs: React.FC = () => {
  const [activeTab, setActiveTab] = useState('structure');

  const tabs = [
    { id: 'structure', label: '📁 Структура' },
    { id: 'env', label: '📄 .env.example' },
    { id: 'config', label: '⚙️ config.py' },
    { id: 'database', label: '🗄️ database.py' },
    { id: 'models', label: '📋 models.py' },
    { id: 'zabbix', label: '🔌 zabbix_client.py' },
    { id: 'auth', label: '🔐 auth.py' },
    { id: 'main', label: '🚀 main.py' },
    { id: 'routers', label: '🛤️ routers/' },
    { id: 'docker', label: '🐳 Docker' },
    { id: 'run', label: '▶️ Запуск' },
  ];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-800">🐍 Backend код (Python/FastAPI)</h2>
        <p className="text-sm text-gray-500 mt-1">
          Полный код бэкенда для развёртывания. Готов к миграции на прод.
        </p>
      </div>

      <div className="flex gap-6">
        {/* Табы */}
        <div className="w-48 flex-shrink-0">
          <nav className="space-y-1 sticky top-6">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-100 text-blue-700 font-medium'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Контент */}
        <div className="flex-1 min-w-0">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="bg-gray-800 px-4 py-2 flex items-center justify-between">
              <span className="text-xs text-gray-400 font-mono">
                {activeTab === 'structure' && 'project/'}
                {activeTab === 'env' && '.env.example'}
                {activeTab === 'config' && 'config.py'}
                {activeTab === 'database' && 'database.py'}
                {activeTab === 'models' && 'models.py'}
                {activeTab === 'zabbix' && 'zabbix_client.py'}
                {activeTab === 'auth' && 'auth.py'}
                {activeTab === 'main' && 'main.py'}
                {activeTab === 'routers' && 'routers/*.py'}
                {activeTab === 'docker' && 'Dockerfile / docker-compose.yml'}
                {activeTab === 'run' && 'Инструкция по запуску'}
              </span>
              <button
                onClick={() => {
                  const el = document.getElementById('code-content');
                  if (el) navigator.clipboard.writeText(el.textContent || '');
                }}
                className="text-xs text-gray-400 hover:text-white px-2 py-1 rounded hover:bg-gray-700"
              >
                📋 Копировать
              </button>
            </div>
            <div className="p-4 overflow-x-auto max-h-[600px] overflow-y-auto">
              <pre id="code-content" className="text-xs text-gray-300 font-mono whitespace-pre leading-relaxed">
                {getContent(activeTab)}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

function getContent(tab: string): string {
  const contents: Record<string, string> = {
    structure: `sla_planner/
├── .env.example          # Пример файла конфигурации
├── .gitignore
├── requirements.txt
├── docker-compose.yml    # Для будущего прода
├── Dockerfile
├── config.py             # Чтение переменных окружения
├── main.py               # FastAPI приложение, роуты
├── database.py           # SQLAlchemy engine, session, Base
├── models.py             # Pydantic схемы + SQLAlchemy модели
├── zabbix_client.py      # Обёртка над Zabbix API
├── auth.py               # Заглушка авторизации (потом ADFS/OAuth2)
├── routers/
│   ├── __init__.py
│   ├── works.py          # CRUD для плановых работ
│   ├── services.py       # Эндпоинты для дерева сервисов
│   ├── calendar.py       # Эндпоинты для календаря
│   └── settings.py       # Настройки подключения к Zabbix
├── static/
│   ├── css/style.css
│   └── js/
│       ├── app.js
│       ├── graph.js
│       ├── calendar.js
│       └── form.js
└── templates/
    └── index.html`,

    env: `# Zabbix подключение
ZABBIX_URL=http://localhost:8080/api_jsonrpc.php
ZABBIX_USERNAME=Admin
ZABBIX_PASSWORD=zabbix
ZABBIX_SLA_NAME=Test SLA

# База данных
# Для теста: sqlite:///./sla_planner.db
# Для прода: postgresql://user:password@localhost:5432/sla_planner
DATABASE_URL=sqlite:///./sla_planner.db

# Авторизация (заготовка под ADFS)
AUTH_MODE=mock
# AUTH_MODE=adfs
# ADFS_CLIENT_ID=your-client-id
# ADFS_CLIENT_SECRET=your-client-secret
# ADFS_TENANT_ID=your-tenant-id
# ADFS_AUTH_URL=https://adfs.corp.local/adfs/oauth2/authorize
# ADFS_TOKEN_URL=https://adfs.corp.local/adfs/oauth2/token

# Приложение
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true`,

    config: `"""
config.py — Конфигурация приложения через переменные окружения.
Следует принципам 12-Factor App.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка .env файла
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    """Централизованное хранилище настроек приложения."""

    # Zabbix
    ZABBIX_URL: str = os.getenv("ZABBIX_URL", "http://localhost:8080/api_jsonrpc.php")
    ZABBIX_USERNAME: str = os.getenv("ZABBIX_USERNAME", "Admin")
    ZABBIX_PASSWORD: str = os.getenv("ZABBIX_PASSWORD", "zabbix")
    ZABBIX_SLA_NAME: str = os.getenv("ZABBIX_SLA_NAME", "Test SLA")

    # База данных
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sla_planner.db")

    # Авторизация
    AUTH_MODE: str = os.getenv("AUTH_MODE", "mock")
    ADFS_CLIENT_ID: str = os.getenv("ADFS_CLIENT_ID", "")
    ADFS_CLIENT_SECRET: str = os.getenv("ADFS_CLIENT_SECRET", "")
    ADFS_TENANT_ID: str = os.getenv("ADFS_TENANT_ID", "")
    ADFS_AUTH_URL: str = os.getenv("ADFS_AUTH_URL", "")
    ADFS_TOKEN_URL: str = os.getenv("ADFS_TOKEN_URL", "")

    # Приложение
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"


settings = Settings()`,

    database: `"""
database.py — Настройка SQLAlchemy engine и сессии.
Для смены БД достаточно изменить DATABASE_URL в .env файле.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import settings


# Создание engine — работает и с SQLite, и с PostgreSQL
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM моделей."""
    pass


def get_db():
    """Dependency для FastAPI — предоставляет сессию БД."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Создание таблиц в БД."""
    Base.metadata.create_all(bind=engine)`,

    models: `"""
models.py — SQLAlchemy модели и Pydantic схемы.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from database import Base
from pydantic import BaseModel
from typing import Optional


# === SQLAlchemy модели ===

class PlannedWork(Base):
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
    created_by = Column(String, default="Admin")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# === Pydantic схемы ===

class PlannedWorkCreate(BaseModel):
    service_name: str
    service_id_zabbix: Optional[str] = None
    work_title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime

class PlannedWorkUpdate(BaseModel):
    status: Optional[str] = None
    zabbix_exclusion_created: Optional[bool] = None

class PlannedWorkResponse(BaseModel):
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
    id: str
    name: str
    status: str  # ok, warning, problem
    algorithm: Optional[str] = None
    parent_id: Optional[str] = None
    children: list[str] = []

class ServicesTreeResponse(BaseModel):
    nodes: list[ServiceNode]
    edges: list[dict]

class HealthResponse(BaseModel):
    status: str
    zabbix_connected: bool
    mode: str  # demo / production
    services_count: int
    works_count: int`,

    zabbix: `"""
zabbix_client.py — Обёртка над Zabbix 7.0 API.
Обрабатывает авторизацию, получение дерева сервисов, создание SLA исключений.
"""
import requests
import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)


class ZabbixClient:
    """Клиент для работы с Zabbix API 7.0."""

    def __init__(self):
        self.url = settings.ZABBIX_URL
        self.auth_token: Optional[str] = None
        self.request_id = 0

    def _make_request(self, method: str, params: dict) -> dict:
        """Выполнение JSON-RPC запроса к Zabbix."""
        self.request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.request_id,
        }
        if self.auth_token:
            payload["auth"] = self.auth_token

        try:
            response = requests.post(
                self.url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json-rpc"},
            )
            response.raise_for_status()
            result = response.json()

            if "error" in result:
                logger.error(f"Zabbix API error: {result['error']}")
                raise Exception(f"Zabbix API: {result['error'].get('data', 'Unknown error')}")

            return result.get("result", {})
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Zabbix")
            raise ConnectionError("Zabbix server unavailable")
        except requests.exceptions.Timeout:
            logger.error("Zabbix request timeout")
            raise TimeoutError("Zabbix request timeout")

    def login(self) -> bool:
        """Авторизация в Zabbix. В 7.0 используется 'username' вместо 'user'."""
        try:
            result = self._make_request("user.login", {
                "username": settings.ZABBIX_USERNAME,
                "password": settings.ZABBIX_PASSWORD,
            })
            self.auth_token = result
            logger.info("Successfully authenticated with Zabbix")
            return True
        except Exception as e:
            logger.error(f"Zabbix login failed: {e}")
            return False

    def ping(self) -> bool:
        """Проверка доступности Zabbix."""
        try:
            self._make_request("apiinfo.version", {})
            return True
        except Exception:
            return False

    def get_services_tree(self) -> dict:
        """Получение дерева сервисов для vis-network."""
        services = self._make_request("service.get", {
            "output": ["serviceid", "name", "algorithm", "status"],
            "selectParents": ["serviceid"],
            "selectChildren": ["serviceid"],
            "selectTags": "extend",
        })

        nodes = []
        edges = []

        for svc in services:
            # Определяем статус
            status = "ok"
            if svc.get("status") == 1:
                status = "problem"
            elif svc.get("status") == 2:
                status = "warning"

            nodes.append({
                "id": svc["serviceid"],
                "name": svc["name"],
                "status": status,
                "algorithm": str(svc.get("algorithm", "1")),
                "parent_id": svc["parents"][0]["serviceid"] if svc.get("parents") else None,
                "children": [c["serviceid"] for c in svc.get("children", [])],
            })

            for parent in svc.get("parents", []):
                edges.append({
                    "from": parent["serviceid"],
                    "to": svc["serviceid"],
                })

        return {"nodes": nodes, "edges": edges}

    def create_sla_exclusion(
        self,
        service_name: str,
        start_timestamp: float,
        end_timestamp: float,
        description: str,
    ) -> bool:
        """
        Создание исключения SLA (плановые работы).
        В Zabbix 7.0 используется sla.update с полным массивом excluded_downtimes.
        """
        try:
            # 1. Получить текущий SLA
            slas = self._make_request("sla.get", {
                "filter": {"name": settings.ZABBIX_SLA_NAME},
                "selectExcludedDowntimes": "extend",
            })

            if not slas:
                logger.error(f"SLA '{settings.ZABBIX_SLA_NAME}' not found")
                return False

            sla = slas[0]
            slaid = sla["slaid"]

            # 2. Добавить новое исключение
            existing = sla.get("excluded_downtimes", [])
            new_exclusion = {
                "name": f"ПР: {description} ({service_name})",
                "period_from": str(int(start_timestamp)),
                "period_to": str(int(end_timestamp)),
            }
            updated_exclusions = existing + [new_exclusion]

            # 3. Обновить SLA
            self._make_request("sla.update", {
                "slaid": slaid,
                "excluded_downtimes": updated_exclusions,
            })

            logger.info(f"SLA exclusion created for '{service_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to create SLA exclusion: {e}")
            return False


# Глобальный экземпляр клиента
zabbix_client = ZabbixClient()`,

    auth: `"""
auth.py — Модуль авторизации.
Сейчас используется MockAuthProvider (заглушка).
При переносе в прод — заменить на ADFSAuthProvider.
"""
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
from fastapi import Request
from config import settings


@dataclass
class User:
    """Модель пользователя."""
    username: str
    full_name: str
    email: str


class AuthProvider(ABC):
    """Абстрактный провайдер авторизации."""

    @abstractmethod
    def get_current_user(self, request: Request) -> User:
        """Получение текущего пользователя из запроса."""
        pass


class MockAuthProvider(AuthProvider):
    """Заглушка для тестов — всегда возвращает Admin."""

    def get_current_user(self, request: Request) -> User:
        return User(
            username="Admin",
            full_name="Администратор",
            email="admin@corp.local",
        )


class ADFSAuthProvider(AuthProvider):
    """
    Провайдер авторизации через ADFS/OAuth2.
    Реализуется при переносе в корпоративную среду.

    TODO при миграции на прод:
    1. Redirect на ADFS_AUTH_URL для получения authorization code
    2. Обмен code на access_token через ADFS_TOKEN_URL
    3. Валидация JWT токена (python-jose)
    4. Извлечение username, email, groups из claims
    5. Проверка членства в нужной AD группе
    """

    def get_current_user(self, request: Request) -> User:
        # Получаем токен из заголовка Authorization
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise Exception("No valid token provided")

        token = auth_header[7:]

        # TODO: Раскодировать JWT и извлечь данные пользователя
        # from jose import jwt
        # claims = jwt.decode(token, key, algorithms=["RS256"])
        # return User(
        #     username=claims["preferred_username"],
        #     full_name=claims["name"],
        #     email=claims["email"],
        # )

        raise NotImplementedError("ADFS auth not yet implemented")


def get_auth_provider() -> AuthProvider:
    """Фабрика провайдеров авторизации."""
    if settings.AUTH_MODE == "adfs":
        return ADFSAuthProvider()
    return MockAuthProvider()


# Dependency для FastAPI
def get_current_user(request: Request) -> User:
    """FastAPI dependency — возвращает текущего пользователя."""
    provider = get_auth_provider()
    return provider.get_current_user(request)`,

    main: `"""
main.py — FastAPI приложение. Точка входа.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from config import settings
from database import init_db, get_db
from auth import get_current_user, User
from routers import works, services, calendar, settings as settings_router
from zabbix_client import zabbix_client

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация при запуске."""
    logger.info("Starting SLA Planner...")
    init_db()

    # Попытка подключения к Zabbix
    if zabbix_client.login():
        logger.info("✅ Connected to Zabbix")
    else:
        logger.warning("⚠️ Zabbix unavailable — running in demo mode")

    yield
    logger.info("Shutting down SLA Planner...")


app = FastAPI(
    title="SLA Planner",
    description="Портал управления плановыми работами с интеграцией Zabbix 7.0",
    version="1.0.0",
    lifespan=lifespan,
)

# Статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключение роутеров
app.include_router(works.router, prefix="/api")
app.include_router(services.router, prefix="/api")
app.include_router(calendar.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")


@app.get("/")
async def root():
    """Главная страница — SPA."""
    return FileResponse("templates/index.html")


@app.get("/api/health")
async def health_check(user: User = Depends(get_current_user)):
    """Проверка состояния системы."""
    zabbix_ok = zabbix_client.ping()
    return {
        "status": "ok",
        "zabbix_connected": zabbix_ok,
        "mode": "production" if zabbix_ok else "demo",
        "user": user.username,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
    )`,

    routers: `"""
routers/works.py — CRUD операции для плановых работ.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

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
    """Получение списка плановых работ с фильтрацией."""
    query = db.query(PlannedWork)
    if status:
        query = query.filter(PlannedWork.status == status)
    return query.order_by(PlannedWork.start_time.desc()).all()


@router.post("/works", response_model=PlannedWorkResponse)
def create_work(
    work: PlannedWorkCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Создание новой плановой работы."""
    # Валидация: end > start
    if work.end_time <= work.start_time:
        raise HTTPException(400, "End time must be after start time")

    # Создание записи в БД
    db_work = PlannedWork(
        service_name=work.service_name,
        service_id_zabbix=work.service_id_zabbix,
        work_title=work.work_title,
        description=work.description,
        start_time=work.start_time,
        end_time=work.end_time,
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
    except Exception:
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
        raise HTTPException(404, "Work not found")

    if update.status is not None:
        db_work.status = update.status
    if update.zabbix_exclusion_created is not None:
        db_work.zabbix_exclusion_created = update.zabbix_exclusion_created

    db.commit()
    db.refresh(db_work)
    return db_work


# === routers/services.py ===
"""
routers/services.py — Эндпоинты для дерева сервисов.
"""
from fastapi import APIRouter, Depends
from auth import get_current_user, User
from zabbix_client import zabbix_client
from models import ServicesTreeResponse

router = APIRouter(tags=["services"])

# Демо-данные (используются если Zabbix недоступен)
DEMO_TREE = {
    "nodes": [
        {"id": "1", "name": "IT Инфраструктура", "status": "ok", "algorithm": "all", "parent_id": None},
        {"id": "2", "name": "Почтовый сервер", "status": "ok", "parent_id": "1"},
        {"id": "3", "name": "CRM Система", "status": "ok", "algorithm": "all", "parent_id": "1"},
        {"id": "4", "name": "БД PostgreSQL", "status": "ok", "parent_id": "3"},
        {"id": "5", "name": "ERP Система", "status": "warning", "algorithm": "min_n", "parent_id": "1"},
        {"id": "6", "name": "БД Oracle", "status": "ok", "parent_id": "5"},
        {"id": "7", "name": "1С Бухгалтерия", "status": "problem", "parent_id": "5"},
        {"id": "8", "name": "Портал клиентов", "status": "ok", "parent_id": "1"},
        {"id": "9", "name": "Веб-сервер Nginx", "status": "ok", "parent_id": "8"},
        {"id": "10", "name": "Файловый сервер", "status": "ok", "parent_id": "1"},
    ],
    "edges": [
        {"from": "1", "to": "2"}, {"from": "1", "to": "3"}, {"from": "1", "to": "5"},
        {"from": "1", "to": "8"}, {"from": "1", "to": "10"}, {"from": "3", "to": "4"},
        {"from": "5", "to": "6"}, {"from": "5", "to": "7"}, {"from": "8", "to": "9"},
    ],
}


@router.get("/services_tree", response_model=ServicesTreeResponse)
def get_services_tree(user: User = Depends(get_current_user)):
    """Получение дерева сервисов (из Zabbix или демо)."""
    try:
        return zabbix_client.get_services_tree()
    except Exception:
        return DEMO_TREE


# === routers/calendar.py ===
"""
routers/calendar.py — Эндпоинты для календаря.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user, User
from models import PlannedWork, PlannedWorkResponse

router = APIRouter(tags=["calendar"])


@router.get("/calendar", response_model=list[PlannedWorkResponse])
def get_calendar_works(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Получение работ для календаря за указанный месяц."""
    from sqlalchemy import extract
    return db.query(PlannedWork).filter(
        extract('year', PlannedWork.start_time) == year,
        extract('month', PlannedWork.start_time) == month,
    ).all()


# === routers/settings.py ===
"""
routers/settings.py — Настройки подключения.
"""
from fastapi import APIRouter, Depends
from auth import get_current_user, User
from zabbix_client import zabbix_client
from config import settings

router = APIRouter(tags=["settings"])


@router.get("/settings")
def get_settings(user: User = Depends(get_current_user)):
    """Получение текущих настроек (без пароля)."""
    return {
        "zabbix_url": settings.ZABBIX_URL,
        "zabbix_username": settings.ZABBIX_USERNAME,
        "zabbix_sla_name": settings.ZABBIX_SLA_NAME,
        "database_url": settings.DATABASE_URL,
        "auth_mode": settings.AUTH_MODE,
    }


@router.post("/settings/test")
def test_zabbix_connection(user: User = Depends(get_current_user)):
    """Проверка подключения к Zabbix."""
    connected = zabbix_client.login()
    return {"connected": connected}`,

    docker: `# === Dockerfile ===
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


# === docker-compose.yml ===
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: \${DB_USER:-sla_user}
      POSTGRES_PASSWORD: \${DB_PASSWORD:-sla_pass}
      POSTGRES_DB: \${DB_NAME:-sla_planner}
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - app
    restart: unless-stopped

volumes:
  pgdata:


# === requirements.txt ===
fastapi==0.115.0
uvicorn==0.30.6
sqlalchemy==2.0.35
requests==2.32.3
pydantic==2.9.2
pydantic-settings==2.5.2
python-dotenv==1.0.1
python-jose==3.3.0
passlib==1.7.4
psycopg2-binary==2.9.9  # Для PostgreSQL в проде`,

    run: `# === ИНСТРУКЦИЯ ПО ЗАПУСКУ ===

# 1. Клонировать проект и перейти в папку
cd sla_planner

# 2. Скопировать .env.example в .env и заполнить
cp .env.example .env
# Отредактировать .env — указать реальные параметры Zabbix

# 3. Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\\Scripts\\activate  # Windows

# 4. Установить зависимости
pip install -r requirements.txt

# 5. Запустить приложение
python main.py

# 6. Открыть в браузере
# http://localhost:8000

# === ЗАПУСК В DOCKER (для прода) ===
docker-compose up -d

# === ПЕРЕКЛЮЧЕНИЕ SQLite → PostgreSQL ===
# 1. В .env изменить:
#    DATABASE_URL=postgresql://user:pass@db:5432/sla_planner
# 2. Перезапустить приложение
# 3. Таблицы создадутся автоматически через SQLAlchemy

# === ПЕРЕКЛЮЧЕНИЕ Mock → ADFS авторизация ===
# 1. В .env изменить:
#    AUTH_MODE=adfs
#    ADFS_CLIENT_ID=...
#    ADFS_AUTH_URL=...
# 2. Реализовать ADFSAuthProvider в auth.py
# 3. Перезапустить приложение`,
  };

  return contents[tab] || 'Содержимое не найдено';
}

export default BackendDocs;
