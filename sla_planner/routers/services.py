"""
routers/services.py — Эндпоинты для дерева сервисов Zabbix.
Если Zabbix недоступен — возвращает демо-данные.
"""
from fastapi import APIRouter, Depends
from auth import get_current_user, User
from zabbix_client import zabbix_client
from models import ServicesTreeResponse, ServiceNode

router = APIRouter(tags=["services"])

# Демо-данные (используются если Zabbix недоступен)
DEMO_TREE = ServicesTreeResponse(
    nodes=[
        ServiceNode(id="1", name="IT Инфраструктура", status="ok", algorithm="all", parent_id=None),
        ServiceNode(id="2", name="Почтовый сервер", status="ok", parent_id="1"),
        ServiceNode(id="3", name="CRM Система", status="ok", algorithm="all", parent_id="1"),
        ServiceNode(id="4", name="БД PostgreSQL", status="ok", parent_id="3"),
        ServiceNode(id="5", name="ERP Система", status="warning", algorithm="min_n", parent_id="1"),
        ServiceNode(id="6", name="БД Oracle", status="ok", parent_id="5"),
        ServiceNode(id="7", name="1С Бухгалтерия", status="problem", parent_id="5"),
        ServiceNode(id="8", name="Портал клиентов", status="ok", parent_id="1"),
        ServiceNode(id="9", name="Веб-сервер Nginx", status="ok", parent_id="8"),
        ServiceNode(id="10", name="Файловый сервер", status="ok", parent_id="1"),
    ],
    edges=[
        {"from": "1", "to": "2"},
        {"from": "1", "to": "3"},
        {"from": "1", "to": "5"},
        {"from": "1", "to": "8"},
        {"from": "1", "to": "10"},
        {"from": "3", "to": "4"},
        {"from": "5", "to": "6"},
        {"from": "5", "to": "7"},
        {"from": "8", "to": "9"},
    ],
)


@router.get("/services_tree", response_model=ServicesTreeResponse)
def get_services_tree(user: User = Depends(get_current_user)):
    """
    Получение дерева сервисов для vis-network.
    Если Zabbix доступен — берёт реальные данные.
    Если нет — возвращает демо-данные.
    """
    try:
        tree_data = zabbix_client.get_services_tree()
        return ServicesTreeResponse(**tree_data)
    except Exception:
        # Zabbix недоступен — возвращаем демо-данные
        return DEMO_TREE
