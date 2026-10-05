"""
routers/services.py — Эндпоинты для дерева SLA-услуг из Zabbix.
Синхронизирует сервисы из Zabbix с локальной БД для управления правами.
"""
import logging
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user, CurrentUser, get_accessible_services
from zabbix_client import zabbix_client
from models import Service, ServiceResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["services"])


@router.get("/services_tree")
def get_services_tree(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Получение дерева SLA-услуг из Zabbix.
    Синхронизирует сервисы с локальной БД.
    Фильтрует по доступным пользователю сервисам.
    """
    try:
        # Получаем данные из Zabbix
        tree_data = zabbix_client.get_services_tree()
        
        # Синхронизируем с локальной БД
        _sync_services_to_db(db, tree_data.get("nodes", []))
        
        # Если сервисов нет — возвращаем сообщение с инструкцией
        if not tree_data.get("nodes") or len(tree_data["nodes"]) == 0:
            return {
                "nodes": [],
                "edges": [],
                "empty": True,
                "message": "В Zabbix нет созданных SLA-услуг. Создайте их в интерфейсе Zabbix: Сервисы → Дерево сервисов → Создать сервис"
            }
        
        # Фильтруем по доступным пользователю сервисам
        accessible_ids = get_accessible_services(current_user, db)
        
        # Если пользователь — админ, он видит все
        if current_user.is_admin:
            filtered_nodes = tree_data["nodes"]
            filtered_edges = tree_data["edges"]
        else:
            # Фильтруем узлы
            filtered_nodes = [
                node for node in tree_data["nodes"]
                if node["id"] in accessible_ids
            ]
            
            # Фильтруем рёбра (только между доступными узлами)
            accessible_node_ids = {node["id"] for node in filtered_nodes}
            filtered_edges = [
                edge for edge in tree_data["edges"]
                if edge["from"] in accessible_node_ids and edge["to"] in accessible_node_ids
            ]
        
        # Если после фильтрации ничего не осталось
        if not filtered_nodes:
            return {
                "nodes": [],
                "edges": [],
                "empty": True,
                "message": "У вас нет доступа ни к одной SLA-услуге. Обратитесь к администратору для назначения прав."
            }
        
        return {
            "nodes": filtered_nodes,
            "edges": filtered_edges,
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


@router.get("/services/all", response_model=List[ServiceResponse])
def get_all_services(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Получение всех сервисов из локальной БД (для управления группами).
    Только для администраторов.
    """
    if not current_user.is_admin:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Только администраторы могут просматривать все сервисы")
    
    services = db.query(Service).order_by(Service.name).all()
    
    return [
        ServiceResponse(
            id=s.id,
            name=s.name,
            status=s.status,
            algorithm=s.algorithm,
            parent_id=s.parent_id,
        ) for s in services
    ]


@router.post("/services/sync")
def sync_services(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Принудительная синхронизация сервисов из Zabbix.
    Только для администраторов.
    """
    if not current_user.is_admin:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Только администраторы могут синхронизировать сервисы")
    
    try:
        tree_data = zabbix_client.get_services_tree()
        count = _sync_services_to_db(db, tree_data.get("nodes", []))
        
        return {
            "status": "ok",
            "synced": count,
            "message": f"Синхронизировано {count} сервисов"
        }
    except Exception as e:
        logger.error(f"Error syncing services: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Ошибка синхронизации: {str(e)}")


def _sync_services_to_db(db: Session, nodes: list) -> int:
    """
    Синхронизация сервисов из Zabbix с локальной БД.
    Возвращает количество синхронизированных сервисов.
    
    Синхронизирует:
    - Базовые данные сервиса (name, status, algorithm)
    - Правила расчёта (propagation_rule, weight, sortorder)
    - Метаданные (description)
    """
    from models import ServiceRule
    synced = 0
    
    for node in nodes:
        service_id = node.get("id")
        if not service_id:
            continue
        
        # Ищем существующий сервис
        existing = db.query(Service).filter(Service.id == service_id).first()
        
        if existing:
            # Обновляем существующий
            existing.name = node.get("name", existing.name)
            existing.status = node.get("status", existing.status)
            existing.algorithm = node.get("algorithm", existing.algorithm)
            existing.propagation_rule = node.get("propagation_rule", existing.propagation_rule)
            existing.sortorder = node.get("sortorder", existing.sortorder)
            existing.weight = node.get("weight", existing.weight)
            existing.description = node.get("description", existing.description)
            existing.parent_id = node.get("parent_id", existing.parent_id)
        else:
            # Создаём новый
            new_service = Service(
                id=service_id,
                name=node.get("name", ""),
                status=node.get("status", "ok"),
                algorithm=node.get("algorithm"),
                propagation_rule=node.get("propagation_rule"),
                sortorder=node.get("sortorder"),
                weight=node.get("weight"),
                description=node.get("description"),
                parent_id=node.get("parent_id"),
            )
            db.add(new_service)
        
        # Синхронизируем правила расчёта
        rule = db.query(ServiceRule).filter(ServiceRule.service_id == service_id).first()
        if rule:
            # Обновляем существующее правило
            rule.algorithm = node.get("algorithm", rule.algorithm)
            rule.propagation_rule = node.get("propagation_rule", rule.propagation_rule)
            rule.weight = node.get("weight", rule.weight)
        else:
            # Создаём новое правило
            new_rule = ServiceRule(
                service_id=service_id,
                algorithm=node.get("algorithm", "all"),
                propagation_rule=node.get("propagation_rule"),
                weight=node.get("weight"),
                source="zabbix",
            )
            db.add(new_rule)
        
        synced += 1
    
    db.commit()
    logger.info(f"Synced {synced} services from Zabbix")
    return synced
