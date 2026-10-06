"""
routers/settings.py — Настройки подключения к Zabbix.
"""
from fastapi import APIRouter, Depends
from auth import get_current_user, User
from zabbix_client import zabbix_client
from config import settings

router = APIRouter(tags=["settings"])


@router.get("/settings")
def get_settings(user: User = Depends(get_current_user)):
    """
    Получение текущих настроек.
    Пароль Zabbix НЕ возвращается в ответе.
    """
    return {
        "zabbix_url": settings.ZABBIX_URL,
        "zabbix_username": settings.ZABBIX_USERNAME,
        "zabbix_sla_name": settings.ZABBIX_SLA_NAME,
        "database_url": settings.DATABASE_URL,
        "auth_mode": settings.AUTH_MODE,
        "app_host": settings.APP_HOST,
        "app_port": settings.APP_PORT,
        "debug": settings.DEBUG,
    }


@router.post("/settings/test")
def test_zabbix_connection(user: User = Depends(get_current_user)):
    """
    Проверка подключения к Zabbix серверу.
    Возвращает статус подключения и версию API.
    """
    connected = zabbix_client.login()
    return {
        "connected": connected,
        "url": settings.ZABBIX_URL,
        "message": "Подключение успешно" if connected else "Не удалось подключиться к Zabbix",
    }


@router.get("/health")
def health_check(user: User = Depends(get_current_user)):
    """
    Health check — общая проверка состояния системы.
    """
    zabbix_ok = zabbix_client.ping()
    return {
        "status": "ok",
        "zabbix_connected": zabbix_ok,
        "mode": "production" if zabbix_ok else "demo",
        "user": user.username,
    }
