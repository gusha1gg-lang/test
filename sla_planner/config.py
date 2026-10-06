"""
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
    # Для теста: sqlite:///./sla_planner.db
    # Для прода: postgresql://user:password@localhost:5432/sla_planner
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


# Глобальный экземпляр настроек
settings = Settings()
