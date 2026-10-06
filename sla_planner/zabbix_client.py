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
        
        Запрашиваемые поля:
        - serviceid, name, algorithm, status (базовые)
        - propagation_rule, sortorder, weight (правила расчёта)
        - description, created_at (метаданные)
        - parents, children (иерархия)
        - tags (теги)
        """
        services = self._make_request("service.get", {
            "output": [
                "serviceid", "name", "algorithm", "status",
                "propagation_rule", "sortorder", "weight",
                "description", "created_at",
            ],
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
            
            # Propagation rule (как статус распространяется на родителей)
            propagation_rule = svc.get("propagation_rule", "1")
            propagation_map = {
                "1": "as_problem",  # как проблема
                "2": "as_ok",       # как OK
                "3": "ignore",      # игнорировать
            }
            propagation = propagation_map.get(str(propagation_rule), "as_problem")

            parent_id = None
            if svc.get("parents") and len(svc["parents"]) > 0:
                parent_id = svc["parents"][0]["serviceid"]

            children = [c["serviceid"] for c in svc.get("children", [])]
            
            # Теги
            tags = [tag.get("tag", "") for tag in svc.get("tags", [])]

            nodes.append({
                "id": svc["serviceid"],
                "name": svc["name"],
                "status": status,
                "algorithm": algorithm,
                "propagation_rule": propagation,
                "sortorder": svc.get("sortorder", "0"),
                "weight": svc.get("weight", "1"),
                "description": svc.get("description", ""),
                "parent_id": parent_id,
                "children": children,
                "tags": tags,
            })

            # Рёбра графа
            for parent in svc.get("parents", []):
                edges.append({
                    "from": parent["serviceid"],
                    "to": svc["serviceid"],
                })

        return {"nodes": nodes, "edges": edges}
    
    def get_service_triggers(self, service_id: str) -> List[Dict]:
        """
        Получение триггеров, связанных с сервисом.
        Использует problem_tags для поиска триггеров.
        """
        try:
            # Получаем сервис с тегами проблем
            services = self._make_request("service.get", {
                "serviceids": [service_id],
                "selectProblemTags": "extend",
            })
            
            if not services:
                return []
            
            service = services[0]
            problem_tags = service.get("problem_tags", [])
            
            if not problem_tags:
                return []
            
            # Ищем триггеры по тегам
            triggers = self._make_request("trigger.get", {
                "output": ["triggerid", "description", "expression", "priority", "value"],
                "selectTags": "extend",
                "tags": problem_tags,
                "evaltype": "0",  # AND
            })
            
            return triggers
            
        except Exception as e:
            logger.error(f"Failed to get triggers for service {service_id}: {e}")
            return []

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
        - Проверка пересечения интервалов (warning)
        
        Args:
            service_name: Название сервиса
            start_timestamp: Unix timestamp начала (UTC)
            end_timestamp: Unix timestamp окончания (UTC)
            description: Описание плановой работы
            
        Returns:
            bool: True если исключение создано или уже существует
        """
        # Валидация входных данных
        if start_timestamp >= end_timestamp:
            logger.error(f"Invalid timestamps: start ({start_timestamp}) >= end ({end_timestamp})")
            raise ValueError("Start time must be before end time")
        
        if not service_name or not description:
            logger.error("Missing required parameters: service_name or description")
            raise ValueError("service_name and description are required")
        
        # Проверка на окно задним числом (warning, но не ошибка)
        current_time = datetime.now().timestamp()
        if start_timestamp < current_time:
            logger.warning(f"Creating exclusion in the past: {start_timestamp} < {current_time}")
        
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
            
            # Конвертация в строки (Zabbix требует строки)
            new_period_from = str(int(start_timestamp))
            new_period_to = str(int(end_timestamp))
            
            # Проверка на дубликаты (точное совпадение)
            for exclusion in existing:
                if (exclusion.get("period_from") == new_period_from and 
                    exclusion.get("period_to") == new_period_to):
                    logger.warning(f"Duplicate exclusion found: {new_period_from} - {new_period_to}")
                    return True  # Уже существует, считаем успехом
            
            # Проверка пересечения интервалов (warning, но не блокируем)
            for exclusion in existing:
                existing_from = int(exclusion.get("period_from", 0))
                existing_to = int(exclusion.get("period_to", 0))
                new_from = int(new_period_from)
                new_to = int(new_period_to)
                
                # Проверка пересечения: (start1 < end2) and (end1 > start2)
                if new_from < existing_to and new_to > existing_from:
                    logger.warning(
                        f"Overlapping exclusion detected: "
                        f"new [{new_from}-{new_to}] overlaps with existing [{existing_from}-{existing_to}]"
                    )
            
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

    def update_sla_exclusion(
        self,
        old_start_timestamp: float,
        old_end_timestamp: float,
        new_start_timestamp: float,
        new_end_timestamp: float,
        service_name: str,
        description: str,
    ) -> bool:
        """
        Обновление существующего исключения SLA.
        
        Args:
            old_start_timestamp: Старый Unix timestamp начала (UTC)
            old_end_timestamp: Старый Unix timestamp окончания (UTC)
            new_start_timestamp: Новый Unix timestamp начала (UTC)
            new_end_timestamp: Новый Unix timestamp окончания (UTC)
            service_name: Название сервиса
            description: Описание плановой работы
            
        Returns:
            bool: True если исключение обновлено
        """
        # Валидация
        if new_start_timestamp >= new_end_timestamp:
            raise ValueError("New start time must be before new end time")
        
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
            existing = sla.get("excluded_downtimes", [])
            
            # 2. Найти и удалить старое исключение
            old_period_from = str(int(old_start_timestamp))
            old_period_to = str(int(old_end_timestamp))
            
            updated_exclusions = [
                excl for excl in existing
                if not (excl.get("period_from") == old_period_from and 
                       excl.get("period_to") == old_period_to)
            ]
            
            if len(updated_exclusions) == len(existing):
                logger.warning(f"Old exclusion not found: {old_period_from} - {old_period_to}")
                # Всё равно создаём новое
            
            # 3. Добавить новое исключение
            new_period_from = str(int(new_start_timestamp))
            new_period_to = str(int(new_end_timestamp))
            
            new_exclusion = {
                "name": f"ПР: {description} ({service_name})",
                "period_from": new_period_from,
                "period_to": new_period_to,
            }
            updated_exclusions.append(new_exclusion)

            # 4. Обновить SLA
            self._make_request("sla.update", {
                "slaid": slaid,
                "excluded_downtimes": updated_exclusions,
            })
            
            logger.info(f"SLA exclusion updated for '{service_name}': {description}")
            return True

        except Exception as e:
            logger.error(f"Failed to update SLA exclusion: {e}")
            return False

    def delete_sla_exclusion(
        self,
        start_timestamp: float,
        end_timestamp: float,
    ) -> bool:
        """
        Удаление исключения SLA.
        
        Args:
            start_timestamp: Unix timestamp начала (UTC)
            end_timestamp: Unix timestamp окончания (UTC)
            
        Returns:
            bool: True если исключение удалено
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
            existing = sla.get("excluded_downtimes", [])
            
            # 2. Найти и удалить исключение
            period_from = str(int(start_timestamp))
            period_to = str(int(end_timestamp))
            
            updated_exclusions = [
                excl for excl in existing
                if not (excl.get("period_from") == period_from and 
                       excl.get("period_to") == period_to)
            ]
            
            if len(updated_exclusions) == len(existing):
                logger.warning(f"Exclusion not found: {period_from} - {period_to}")
                return False
            
            # 3. Обновить SLA
            self._make_request("sla.update", {
                "slaid": slaid,
                "excluded_downtimes": updated_exclusions,
            })
            
            logger.info(f"SLA exclusion deleted: {period_from} - {period_to}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete SLA exclusion: {e}")
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

    def calculate_sla_availability(
        self,
        service_id: str,
        period_from: datetime,
        period_to: datetime,
    ) -> Dict[str, Any]:
        """
        Расчёт доступности сервиса за период с учётом исключений.
        
        Формула SLA:
        SLA % = (Total Period Time - Downtime + Excluded Downtime) / Total Period Time × 100
        
        Args:
            service_id: ID сервиса в Zabbix
            period_from: Начало периода (UTC)
            period_to: Конец периода (UTC)
            
        Returns:
            Dict с метриками:
            - sla_percentage: SLA %
            - total_time: Общее время периода (сек)
            - downtime: Время простоя (сек)
            - excluded_downtime: Исключённое время (сек)
            - effective_downtime: Эффективное время простоя (сек)
        """
        try:
            # Получаем SLA с исключениями
            sla_data = self.get_sla_report()
            if not sla_data:
                return {"error": "SLA not found"}
            
            excluded_downtimes = sla_data.get("excluded_downtimes", [])
            
            # Общее время периода (в секундах)
            total_seconds = (period_to - period_from).total_seconds()
            
            if total_seconds <= 0:
                return {"error": "Invalid period"}
            
            # Получаем события простоя для сервиса из Zabbix
            # Используем event.get для получения проблем
            events = self._make_request("event.get", {
                "objectids": [service_id],
                "source": "0",  # Trigger events
                "value": "1",   # Problem state
                "time_from": int(period_from.timestamp()),
                "time_till": int(period_to.timestamp()),
                "selectTags": "extend",
                "sortfield": ["clock"],
                "sortorder": "ASC",
            })
            
            # Рассчитываем время простоя
            downtime_seconds = 0
            for event in events:
                event_start = int(event.get("clock", 0))
                event_end = int(event.get("r_clock", period_to.timestamp()))
                
                # Ограничиваем рамками периода
                event_start = max(event_start, int(period_from.timestamp()))
                event_end = min(event_end, int(period_to.timestamp()))
                
                if event_end > event_start:
                    downtime_seconds += (event_end - event_start)
            
            # Рассчитываем исключённое время простоя
            excluded_seconds = 0
            period_from_ts = int(period_from.timestamp())
            period_to_ts = int(period_to.timestamp())
            
            for exclusion in excluded_downtimes:
                excl_from = int(exclusion.get("period_from", 0))
                excl_to = int(exclusion.get("period_to", 0))
                
                # Проверяем пересечение с периодом
                if excl_to > period_from_ts and excl_from < period_to_ts:
                    # Ограничиваем рамками периода
                    effective_from = max(excl_from, period_from_ts)
                    effective_to = min(excl_to, period_to_ts)
                    
                    if effective_to > effective_from:
                        excluded_seconds += (effective_to - effective_from)
            
            # Эффективное время простоя (за вычетом исключений)
            effective_downtime = max(0, downtime_seconds - excluded_seconds)
            
            # Расчёт SLA %
            availability_time = total_seconds - effective_downtime
            sla_percentage = (availability_time / total_seconds) * 100 if total_seconds > 0 else 0
            
            return {
                "service_id": service_id,
                "period_from": period_from.isoformat(),
                "period_to": period_to.isoformat(),
                "sla_percentage": round(sla_percentage, 4),
                "total_time_seconds": total_seconds,
                "downtime_seconds": downtime_seconds,
                "excluded_downtime_seconds": excluded_seconds,
                "effective_downtime_seconds": effective_downtime,
                "availability_seconds": availability_time,
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate SLA availability: {e}")
            return {"error": str(e)}


# Глобальный экземпляр клиента
zabbix_client = ZabbixClient()
