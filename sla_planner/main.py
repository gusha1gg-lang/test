"""
main.py — FastAPI приложение. Точка входа.
Запуск: python main.py
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from config import settings
from database import init_db, get_db
from auth import get_current_user, User
from routers import works, services, calendar, settings as settings_router
from zabbix_client import zabbix_client

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация при запуске приложения."""
    logger.info("=" * 50)
    logger.info("  SLA Planner — запуск")
    logger.info("=" * 50)
    logger.info(f"  Database : {settings.DATABASE_URL}")
    logger.info(f"  Zabbix   : {settings.ZABBIX_URL}")
    logger.info(f"  SLA Name : {settings.ZABBIX_SLA_NAME}")
    logger.info(f"  Auth     : {settings.AUTH_MODE}")
    logger.info("=" * 50)

    # Создание таблиц БД
    init_db()
    logger.info("✅ Database tables created")

    # Попытка подключения к Zabbix
    if zabbix_client.login():
        logger.info("✅ Connected to Zabbix")
    else:
        logger.warning("⚠️  Zabbix unavailable — services will be empty until connected")

    yield

    logger.info("Shutting down SLA Planner...")


# Создание FastAPI приложения
app = FastAPI(
    title="SLA Planner",
    description="Портал управления плановыми работами с интеграцией Zabbix 7.0",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — разрешаем запросы с фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В проде заменить на конкретный домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров API
app.include_router(works.router, prefix="/api")
app.include_router(services.router, prefix="/api")
app.include_router(calendar.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")


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


# Статические файлы (для раздачи фронтенда из dist/)
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# Точка входа при запуске через python main.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
    )
