"""
Интеграционные тесты для графа SLA и отчётов.
Сценарии 4-5: Граф SLA == Zabbix UI, SLA-отчёт == ручной расчёт.
"""
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient


class TestSLAGraphConsistency:
    """Тесты соответствия графа SLA с Zabbix UI."""

    @pytest.mark.asyncio
    async def test_services_tree_matches_zabbix(self, client, admin_user, zabbix_client):
        """
        Сценарий 4: Граф SLA == Zabbix UI.
        
        Шаги:
        1. GET /api/services_tree
        2. Получить данные напрямую из Zabbix через service.get
        3. Сравнить количество сервисов
        4. Сравнить имена, статусы, алгоритмы
        """
        response = client.get("/api/services_tree")
        
        assert response.status_code == 200, f"Failed to get services tree: {response.json()}"
        
        tree_data = response.json()
        
        # Получаем данные напрямую из Zabbix
        zabbix_services = zabbix_client.get_services_tree()
        
        # Сравнение количества
        assert len(tree_data["nodes"]) == len(zabbix_services["nodes"]), \
            f"Node count mismatch: {len(tree_data['nodes'])} vs {len(zabbix_services['nodes'])}"
        
        # Сравнение данных каждого узла
        for api_node in tree_data["nodes"]:
            zabbix_node = next(
                (n for n in zabbix_services["nodes"] if n["id"] == api_node["id"]),
                None
            )
            assert zabbix_node is not None, f"Node {api_node['id']} not found in Zabbix"
            
            assert api_node["name"] == zabbix_node["name"], \
                f"Name mismatch for node {api_node['id']}"
            assert api_node["status"] == zabbix_node["status"], \
                f"Status mismatch for node {api_node['id']}"
            assert api_node["algorithm"] == zabbix_node["algorithm"], \
                f"Algorithm mismatch for node {api_node['id']}"

    @pytest.mark.asyncio
    async def test_services_tree_edges_match_zabbix(self, client, admin_user, zabbix_client):
        """
        Проверка что рёбра графа совпадают с Zabbix.
        """
        response = client.get("/api/services_tree")
        tree_data = response.json()
        
        zabbix_services = zabbix_client.get_services_tree()
        
        # Сравнение количества рёбер
        assert len(tree_data["edges"]) == len(zabbix_services["edges"]), \
            f"Edge count mismatch: {len(tree_data['edges'])} vs {len(zabbix_services['edges'])}"
        
        # Сравнение каждого ребра
        for api_edge in tree_data["edges"]:
            zabbix_edge = next(
                (e for e in zabbix_services["edges"] 
                 if e["from"] == api_edge["from"] and e["to"] == api_edge["to"]),
                None
            )
            assert zabbix_edge is not None, \
                f"Edge {api_edge['from']} -> {api_edge['to']} not found in Zabbix"

    @pytest.mark.asyncio
    async def test_service_propagation_rules(self, client, admin_user, zabbix_client):
        """
        Проверка что propagation_rule корректно передаётся.
        """
        response = client.get("/api/services_tree")
        tree_data = response.json()
        
        zabbix_services = zabbix_client.get_services_tree()
        
        for api_node in tree_data["nodes"]:
            zabbix_node = next(
                (n for n in zabbix_services["nodes"] if n["id"] == api_node["id"]),
                None
            )
            
            if zabbix_node and "propagation_rule" in zabbix_node:
                assert api_node.get("propagation_rule") == zabbix_node["propagation_rule"], \
                    f"Propagation rule mismatch for node {api_node['id']}"


class TestSLAReportAccuracy:
    """Тесты точности SLA-отчётов."""

    @pytest.mark.asyncio
    async def test_sla_calculation_matches_manual(self, client, admin_user, test_services, test_period):
        """
        Сценарий 5: SLA-отчёт == ручной расчёт.
        
        Шаги:
        1. POST /api/sla/calculate с периодом
        2. Рассчитать SLA вручную по формуле
        3. Сравнить результаты
        """
        request_data = {
            "period_from": test_period["period_from"].isoformat(),
            "period_to": test_period["period_to"].isoformat(),
            "service_ids": ["1"],
        }
        
        response = client.post("/api/sla/calculate", json=request_data)
        
        assert response.status_code == 200, f"Failed to calculate SLA: {response.json()}"
        
        sla_report = response.json()
        
        # Проверка структуры ответа
        assert "services" in sla_report
        assert "summary" in sla_report
        assert len(sla_report["services"]) > 0
        
        service_sla = sla_report["services"][0]
        
        # Проверка что все метрики присутствуют
        assert "sla_percentage" in service_sla
        assert "total_time_seconds" in service_sla
        assert "downtime_seconds" in service_sla
        assert "excluded_downtime_seconds" in service_sla
        assert "effective_downtime_seconds" in service_sla
        assert "availability_seconds" in service_sla
        
        # Проверка формулы: SLA% = (Total - Effective Downtime) / Total * 100
        total_time = service_sla["total_time_seconds"]
        effective_downtime = service_sla["effective_downtime_seconds"]
        expected_sla = ((total_time - effective_downtime) / total_time) * 100 if total_time > 0 else 0
        
        assert abs(service_sla["sla_percentage"] - expected_sla) < 0.01, \
            f"SLA calculation mismatch: {service_sla['sla_percentage']} vs {expected_sla}"

    @pytest.mark.asyncio
    async def test_sla_report_with_exclusions(self, client, admin_user, test_services, sample_work):
        """
        Проверка что SLA-отчёт учитывает исключения простоя.
        """
        # Создаём работу с исключением
        request_data = {
            "period_from": (datetime.utcnow() - timedelta(days=30)).isoformat(),
            "period_to": datetime.utcnow().isoformat(),
            "service_ids": ["1"],
        }
        
        response = client.post("/api/sla/calculate", json=request_data)
        sla_report = response.json()
        
        service_sla = sla_report["services"][0]
        
        # Проверка что excluded_downtime_seconds >= 0
        assert service_sla["excluded_downtime_seconds"] >= 0
        
        # Проверка что effective_downtime <= downtime
        assert service_sla["effective_downtime_seconds"] <= service_sla["downtime_seconds"]

    @pytest.mark.asyncio
    async def test_sla_summary_endpoint(self, client, admin_user, test_services):
        """
        Проверка эндпоинта /api/sla/summary.
        """
        response = client.get("/api/sla/summary?period=month")
        
        assert response.status_code == 200, f"Failed to get SLA summary: {response.json()}"
        
        summary = response.json()
        
        assert "period" in summary
        assert "total_services" in summary
        assert "services" in summary
        assert summary["period"] == "month"

    @pytest.mark.asyncio
    async def test_sla_service_endpoint(self, client, admin_user, test_services):
        """
        Проверка эндпоинта /api/sla/service/{service_id}.
        """
        response = client.get("/api/sla/service/1?period=month")
        
        assert response.status_code == 200, f"Failed to get service SLA: {response.json()}"
        
        service_sla = response.json()
        
        assert "service_id" in service_sla
        assert "service_name" in service_sla
        assert "sla_percentage" in service_sla
        assert service_sla["service_id"] == "1"
        assert service_sla["period"] == "month"

    @pytest.mark.asyncio
    async def test_sla_calculation_with_invalid_period(self, client, admin_user, test_services):
        """
        Негатив: Невалидный период (end < start) → 400.
        """
        request_data = {
            "period_from": datetime.utcnow().isoformat(),
            "period_to": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "service_ids": ["1"],
        }
        
        response = client.post("/api/sla/calculate", json=request_data)
        
        assert response.status_code == 400
        assert "period_to must be after period_from" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_sla_calculation_with_too_long_period(self, client, admin_user, test_services):
        """
        Негатив: Период больше 1 года → 400.
        """
        request_data = {
            "period_from": (datetime.utcnow() - timedelta(days=400)).isoformat(),
            "period_to": datetime.utcnow().isoformat(),
            "service_ids": ["1"],
        }
        
        response = client.post("/api/sla/calculate", json=request_data)
        
        assert response.status_code == 400
        assert "Period cannot exceed 1 year" in response.json()["detail"]
