"""
zabbix_client.py — Обёртка над Zabbix 7.0 API.
Обрабатывает авторизацию, получение дерева сервисов, создание SLA исключений.

ВАЖНО для Zabbix 7.0:
- Авторизация: параметр "username" (не "user")
- SLA исключения: через sla.update с полным массивом excluded_downtimes
- Алгоритмы: 1=Все дочерние, 2=Минимум N, 3=Процент
"""
import requests
import logging
from typing import Optional, Dict, Any, List
from config import settings

logger = logging.getLogger(__name__)


class ZabbixClient:
    """Клиент для работы с Zabbix API 7.0."""

    def __init__(self):
        self.url = settings.ZABBIX_URL
        self.auth_token: Optional[str] = None
        self.request_id = 0

    def _make_request(self, method: str, params: dict) -> Any:
        """Выполнение JSON-RPC запроса к Zabbix API."""
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
                error_msg = result["error"].get("data", "Unknown error")
                logger.error(f"Zabbix API error: {result['error']}")
                raise Exception(f"Zabbix API: {error_msg}")

            return result.get("result", {})

        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Zabbix server")
            raise ConnectionError("Zabbix server unavailable")
        except requests.exceptions.Timeout:
            logger.error("Zabbix request timeout")
            raise TimeoutError("Zabbix request timeout")
        except requests.exceptions.RequestException as e:
            logger.error(f"Zabbix request failed: {e}")
            raise

    def login(self) -> bool:
        """
        Авторизация в Zabbix.
        В Zabbix 7.0 используется параметр 'username' (не 'user').
        """
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
        """Проверка доступности Zabbix сервера."""
        try:
            self._make_request("apiinfo.version", {})
            return True
        except Exception:
            return False

    def get_services_tree(self) -> Dict[str, Any]:
        """
        Получение дерева сервисов для vis-network.
        Возвращает nodes и edges для отображения графа.
        """
        services = self._make_request("service.get", {
            "output": ["serviceid", "name", "algorithm", "status"],
            "selectParents": ["serviceid"],
            "selectChildren": ["serviceid"],
            "selectTags": "extend",
        })

        nodes: List[Dict] = []
        edges: List[Dict] = []

        for svc in services:
            # Определяем статус сервиса
            status = "ok"
            if svc.get("status") == 1:
                status = "problem"
            elif svc.get("status") == 2:
                status = "warning"

            # Определяем алгоритм
            algorithm_map = {"1": "all", "2": "min_n", "3": "percent"}
            algorithm = algorithm_map.get(str(svc.get("algorithm", "1")), "all")

            parent_id = None
            if svc.get("parents") and len(svc["parents"]) > 0:
                parent_id = svc["parents"][0]["serviceid"]

            children = [c["serviceid"] for c in svc.get("children", [])]

            nodes.append({
                "id": svc["serviceid"],
                "name": svc["name"],
                "status": status,
                "algorithm": algorithm,
                "parent_id": parent_id,
                "children": children,
            })

            # Рёбра графа
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

        В Zabbix 7.0 НЕТ метода sla.createexclusion.
        Исключения добавляются через sla.update с ПОЛНЫМ массивом excluded_downtimes.
        """
        try:
            # 1. Получить текущий SLA с существующими исключениями
            slas = self._make_request("sla.get", {
                "filter": {"name": settings.ZABBIX_SLA_NAME},
                "selectExcludedDowntimes": "extend",
            })

            if not slas:
                logger.error(f"SLA '{settings.ZABBIX_SLA_NAME}' not found")
                return False

            sla = slas[0]
            slaid = sla["slaid"]

            # 2. Добавить новое исключение в массив
            existing = sla.get("excluded_downtimes", [])
            new_exclusion = {
                "name": f"ПР: {description} ({service_name})",
                "period_from": str(int(start_timestamp)),
                "period_to": str(int(end_timestamp)),
            }
            updated_exclusions = existing + [new_exclusion]

            # 3. Обновить SLA полным массивом
            self._make_request("sla.update", {
                "slaid": slaid,
                "excluded_downtimes": updated_exclusions,
            })

            logger.info(f"SLA exclusion created for '{service_name}': {description}")
            return True

        except Exception as e:
            logger.error(f"Failed to create SLA exclusion: {e}")
            return False

    def get_sla_report(self) -> Dict[str, Any]:
        """Получение отчёта по SLA."""
        try:
            slas = self._make_request("sla.get", {
                "filter": {"name": settings.ZABBIX_SLA_NAME},
                "selectExcludedDowntimes": "extend",
                "selectServiceTags": "extend",
            })
            if slas:
                return slas[0]
            return {}
        except Exception as e:
            logger.error(f"Failed to get SLA report: {e}")
            return {}


# Глобальный экземпляр клиента
zabbix_client = ZabbixClient()
