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
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from config import settings

logger = logging.getLogger(__name__)


class ZabbixAPIError(Exception):
    """Кастомное исключение для ошибок Zabbix API."""
    def __init__(self, code: int, message: str, data: str = ""):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"Zabbix API error {code}: {message} - {data}")


class ZabbixClient:
    """Клиент для работы с Zabbix API 7.0."""

    def __init__(self):
        self.url = settings.ZABBIX_URL
        self.auth_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.request_id = 0
        self.max_retries = 3
        self.retry_delay = 1  # секунды

    def _is_token_valid(self) -> bool:
        """Проверка валидности токена."""
        if not self.auth_token:
            return False
        if self.token_expires_at and datetime.now() >= self.token_expires_at:
            return False
        return True

    def _make_request(self, method: str, params: dict, retry_count: int = 0) -> Any:
        """
        Выполнение JSON-RPC запроса к Zabbix API с retry логикой.
        
        Args:
            method: Метод Zabbix API
            params: Параметры запроса
            retry_count: Текущая попытка (для retry)
        """
        # Проверка токена и перелогин если нужно
        if method != "user.login" and not self._is_token_valid():
            logger.info("Token expired or missing, re-authenticating...")
            self.login()

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
                timeout=30,  # Увеличен таймаут
                headers={"Content-Type": "application/json-rpc"},
            )
            
            # Retry на 5xx ошибки
            if response.status_code >= 500 and retry_count < self.max_retries:
                delay = self.retry_delay * (2 ** retry_count)  # Экспоненциальный backoff
                logger.warning(f"Zabbix returned {response.status_code}, retrying in {delay}s...")
                time.sleep(delay)
                return self._make_request(method, params, retry_count + 1)
            
            response.raise_for_status()
            result = response.json()

            if "error" in result:
                error = result["error"]
                code = error.get("code", -1)
                message = error.get("message", "Unknown error")
                data = error.get("data", "")
                
                # Перелогин при 401 (невалидный токен)
                if code == -32602 or "not authorized" in data.lower():
                    logger.warning("Token invalid, re-authenticating...")
                    self.login()
                    if retry_count < self.max_retries:
                        return self._make_request(method, params, retry_count + 1)
                
                logger.error(f"Zabbix API error: {message} - {data}")
                raise ZabbixAPIError(code, message, data)

            return result.get("result", {})

        except requests.exceptions.ConnectionError:
            if retry_count < self.max_retries:
                delay = self.retry_delay * (2 ** retry_count)
                logger.warning(f"Connection failed, retrying in {delay}s...")
                time.sleep(delay)
                return self._make_request(method, params, retry_count + 1)
            logger.error("Cannot connect to Zabbix server after retries")
            raise ConnectionError("Zabbix server unavailable")
        except requests.exceptions.Timeout:
            if retry_count < self.max_retries:
                delay = self.retry_delay * (2 ** retry_count)
                logger.warning(f"Request timeout, retrying in {delay}s...")
                time.sleep(delay)
                return self._make_request(method, params, retry_count + 1)
            logger.error("Zabbix request timeout after retries")
            raise TimeoutError("Zabbix request timeout")
        except ZabbixAPIError:
            raise  # Пробрасываем кастомное исключение
        except requests.exceptions.RequestException as e:
            logger.error(f"Zabbix request failed: {e}")
            raise

    def login(self) -> bool:
        """
        Авторизация в Zabbix.
        В Zabbix 7.0 используется параметр 'username' (не 'user').
        Токен действителен 4 часа (стандартное значение Zabbix).
        """
        try:
            result = self._make_request("user.login", {
                "username": settings.ZABBIX_USERNAME,
                "password": settings.ZABBIX_PASSWORD,
            })
            self.auth_token = result
            # Токен действителен 4 часа (стандарт Zabbix)
            self.token_expires_at = datetime.now() + timedelta(hours=4)
            logger.info("Successfully authenticated with Zabbix")
            return True
        except Exception as e:
            logger.error(f"Zabbix login failed: {e}")
            return False

    def ping(self) -> bool:
        """Проверка доступности Zabbix сервера."""
        try:
            # Zabbix 7.0 требует params даже для apiinfo.version
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
        
        Валидация:
        - start_timestamp < end_timestamp
        - Проверка на дубликаты
        - Проверка существования SLA
        """
        # Валидация входных данных
        if start_timestamp >= end_timestamp:
            logger.error(f"Invalid timestamps: start ({start_timestamp}) >= end ({end_timestamp})")
            raise ValueError("Start time must be before end time")
        
        if not service_name or not description:
            logger.error("Missing required parameters: service_name or description")
            raise ValueError("service_name and description are required")
        
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
            
            # Проверка на дубликаты
            new_period_from = str(int(start_timestamp))
            new_period_to = str(int(end_timestamp))
            
            for exclusion in existing:
                if (exclusion.get("period_from") == new_period_from and 
                    exclusion.get("period_to") == new_period_to):
                    logger.warning(f"Duplicate exclusion found: {new_period_from} - {new_period_to}")
                    return True  # Уже существует, считаем успехом
            
            new_exclusion = {
                "name": f"ПР: {description} ({service_name})",
                "period_from": new_period_from,
                "period_to": new_period_to,
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
