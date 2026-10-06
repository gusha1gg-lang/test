"""
Мок Zabbix API сервер для интеграционных тестов.
Имитирует поведение Zabbix 7.0 API.
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
from typing import Dict, List, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Хранилище данных мока
mock_data = {
    "auth_token": "test_token_123",
    "services": [
        {
            "serviceid": "1",
            "name": "Test Service 1",
            "algorithm": "1",
            "status": "0",
            "propagation_rule": "1",
            "sortorder": "0",
            "weight": "1",
            "description": "Test service for integration tests",
            "parents": [],
            "children": [{"serviceid": "2"}],
            "tags": [{"tag": "env", "value": "test"}],
        },
        {
            "serviceid": "2",
            "name": "Test Service 2",
            "algorithm": "2",
            "status": "1",
            "propagation_rule": "2",
            "sortorder": "1",
            "weight": "2",
            "description": "Child service",
            "parents": [{"serviceid": "1"}],
            "children": [],
            "tags": [{"tag": "env", "value": "test"}],
        },
    ],
    "sla": {
        "slaid": "1",
        "name": "Test SLA",
        "period": "1",
        "period_from": "1704067200",
        "period_to": "1735689599",
        "sla": "99.9",
        "excluded_downtimes": [],
        "service_tags": [],
    },
    "triggers": [
        {
            "triggerid": "100",
            "description": "CPU > 90%",
            "expression": "{host:cpu.usage.last()}>90",
            "priority": "4",
            "value": "1",
            "tags": [{"tag": "env", "value": "test"}],
        }
    ],
    "events": [
        {
            "eventid": "1",
            "objectid": "1",
            "clock": "1700000000",
            "r_clock": "1700003600",
            "value": "1",
            "tags": [{"tag": "env", "value": "test"}],
        }
    ],
}


class ZabbixMockHandler(BaseHTTPRequestHandler):
    """Обработчик HTTP запросов для мока Zabbix API."""

    def do_POST(self):
        """Обработка POST запросов (JSON-RPC)."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            request = json.loads(body.decode("utf-8"))
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id", 1)

            logger.info(f"Received request: {method}")

            # Обработка различных методов Zabbix API
            if method == "apiinfo.version":
                result = "7.0.0"
            elif method == "user.login":
                username = params.get("username")
                password = params.get("password")
                if username == "Admin" and password == "zabbix":
                    result = mock_data["auth_token"]
                else:
                    result = {"error": {"code": -32602, "message": "Login credentials are incorrect"}}
            elif method == "service.get":
                result = self._handle_service_get(params)
            elif method == "sla.get":
                result = self._handle_sla_get(params)
            elif method == "sla.update":
                result = self._handle_sla_update(params)
            elif method == "trigger.get":
                result = self._handle_trigger_get(params)
            elif method == "event.get":
                result = self._handle_event_get(params)
            else:
                result = {"error": {"code": -32601, "message": f"Method {method} not found"}}

            # Формирование ответа
            if isinstance(result, dict) and "error" in result:
                response = {
                    "jsonrpc": "2.0",
                    "error": result["error"],
                    "id": request_id,
                }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": request_id,
                }

            self.send_response(200)
            self.send_header("Content-Type", "application/json-rpc")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            self.send_response(500)
            self.end_headers()

    def _handle_service_get(self, params: Dict) -> List[Dict]:
        """Обработка service.get."""
        services = mock_data["services"]

        # Фильтрация по serviceids
        if "serviceids" in params:
            service_ids = params["serviceids"]
            services = [s for s in services if s["serviceid"] in service_ids]

        # Фильтрация по output
        if "output" in params:
            output_fields = params["output"]
            services = [{k: s.get(k) for k in output_fields if k in s} for s in services]

        return services

    def _handle_sla_get(self, params: Dict) -> List[Dict]:
        """Обработка sla.get."""
        sla = mock_data["sla"]

        # Фильтрация по имени
        if "filter" in params and "name" in params["filter"]:
            if sla["name"] != params["filter"]["name"]:
                return []

        result = [sla.copy()]

        # Добавление excluded_downtimes
        if params.get("selectExcludedDowntimes") == "extend":
            result[0]["excluded_downtimes"] = sla["excluded_downtimes"]

        # Добавление service_tags
        if params.get("selectServiceTags") == "extend":
            result[0]["service_tags"] = sla["service_tags"]

        return result

    def _handle_sla_update(self, params: Dict) -> Dict:
        """Обработка sla.update."""
        slaid = params.get("slaid")
        excluded_downtimes = params.get("excluded_downtimes", [])

        if slaid == mock_data["sla"]["slaid"]:
            mock_data["sla"]["excluded_downtimes"] = excluded_downtimes
            return {"slaid": slaid}
        else:
            return {"error": {"code": -32602, "message": "SLA not found"}}

    def _handle_trigger_get(self, params: Dict) -> List[Dict]:
        """Обработка trigger.get."""
        triggers = mock_data["triggers"]

        # Фильтрация по тегам
        if "tags" in params:
            tags = params["tags"]
            # Упрощённая фильтрация
            triggers = [t for t in triggers if any(tag in t.get("tags", []) for tag in tags)]

        return triggers

    def _handle_event_get(self, params: Dict) -> List[Dict]:
        """Обработка event.get."""
        events = mock_data["events"]

        # Фильтрация по времени
        if "time_from" in params:
            time_from = int(params["time_from"])
            events = [e for e in events if int(e.get("clock", 0)) >= time_from]

        if "time_till" in params:
            time_till = int(params["time_till"])
            events = [e for e in events if int(e.get("clock", 0)) <= time_till]

        return events


def run_server(port: int = 8080):
    """Запуск мок сервера."""
    server = HTTPServer(("0.0.0.0", port), ZabbixMockHandler)
    logger.info(f"Starting Zabbix mock server on port {port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
