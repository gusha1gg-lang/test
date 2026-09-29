"""
routers/services.py — Эндпоинты для дерева SLA-услуг из Zabbix.
Возвращает ТОЛЬКО реальные данные из Zabbix. Если Zabbix недоступен — пустой список.
"""
import logging
from fastapi import APIRouter, Depends
from auth import get_current_user, User
from zabbix_client import zabbix_client
from models import ServicesTreeResponse, ServiceNode

logger = logging.getLogger(__name__)

router = APIRouter(tags=["services"])


@router.get("/services_tree", response_model=ServicesTreeResponse)
def get_services_tree(user: User = Depends(get_current_user)):
    """
    Получение дерева SLA-услуг из Zabbix.
    Если Zabbix недоступен — возвращает пустой список.
    """
    try:
        tree_data = zabbix_client.get_services_tree()
        return ServicesTreeResponse(**tree_data)
    except Exception as e:
        logger.warning(f"Cannot get services from Zabbix: {e}")
        # Возвращаем пустой список — фронтенд покажет сообщение
        return ServicesTreeResponse(nodes=[], edges=[])
