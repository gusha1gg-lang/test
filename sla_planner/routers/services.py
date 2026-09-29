# --- ФАЙЛ: sla_planner/routers/services.py ---
"""
Эндпоинты для дерева SLA-услуг из Zabbix.
Возвращает ТОЛЬКО реальные данные из Zabbix. Если сервисов нет — возвращает понятное сообщение.
"""
import logging
from fastapi import APIRouter, Depends
from auth import get_current_user, User
from zabbix_client import zabbix_client
from models import ServicesTreeResponse, ServiceNode
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(tags=["services"])


@router.get("/services_tree")
def get_services_tree(user: User = Depends(get_current_user)):
    """
    Получение дерева SLA-услуг из Zabbix.
    Если Zabbix недоступен или сервисов нет — возвращает понятное сообщение.
    """
    try:
        tree_data = zabbix_client.get_services_tree()
        
        # Если сервисов нет — возвращаем сообщение с инструкцией
        if not tree_data.get("nodes") or len(tree_data["nodes"]) == 0:
            return {
                "nodes": [],
                "edges": [],
                "empty": True,
                "message": "В Zabbix нет созданных SLA-услуг. Создайте их в интерфейсе Zabbix: Сервисы → Дерево сервисов → Создать сервис"
            }
        
        return {
            "nodes": tree_data["nodes"],
            "edges": tree_data["edges"],
            "empty": False
        }
        
    except ConnectionError as e:
        logger.error(f"Cannot connect to Zabbix: {e}")
        return {
            "nodes": [],
            "edges": [],
            "empty": True,
            "error": True,
            "message": f"Не удалось подключиться к Zabbix: {str(e)}. Проверьте настройки подключения."
        }
    except Exception as e:
        logger.error(f"Error getting services tree: {e}")
        return {
            "nodes": [],
            "edges": [],
            "empty": True,
            "error": True,
            "message": f"Ошибка получения данных из Zabbix: {str(e)}"
        }
