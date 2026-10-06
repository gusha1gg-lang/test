"""
test_zabbix_integration.py — Интеграционные тесты для проверки соответствия с Zabbix UI.
"""
import pytest
from unittest.mock import patch
from zabbix_client import ZabbixClient


class TestZabbixUIConsistency:
    """Тесты соответствия с Zabbix UI."""

    def test_algorithm_matches_zabbix_ui(self):
        """Проверка что algorithm маппится правильно как в Zabbix UI."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        # Данные из Zabbix UI для сервиса с algorithm=1
        # В Zabbix UI: algorithm=1 означает "All children must be OK"
        zabbix_response = [{
            "serviceid": "1",
            "name": "Test Service",
            "algorithm": "1",  # В Zabbix UI: "All children must be OK"
            "status": "0",
            "propagation_rule": "1",
            "parents": [],
            "children": [],
            "tags": [],
        }]
        
        with patch.object(client, '_make_request', return_value=zabbix_response):
            result = client.get_services_tree()
            
            # В нашем UI должно отображаться как "all"
            assert result["nodes"][0]["algorithm"] == "all"

    def test_propagation_rule_matches_zabbix_ui(self):
        """Проверка что propagation_rule маппится правильно как в Zabbix UI."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        # propagation_rule=1 в Zabbix UI: "As problem"
        zabbix_response = [{
            "serviceid": "1",
            "name": "Test",
            "algorithm": "1",
            "status": "0",
            "propagation_rule": "1",  # В Zabbix UI: "As problem"
            "parents": [],
            "children": [],
            "tags": [],
        }]
        
        with patch.object(client, '_make_request', return_value=zabbix_response):
            result = client.get_services_tree()
            assert result["nodes"][0]["propagation_rule"] == "as_problem"

    def test_algorithm_min_n_matches_zabbix_ui(self):
        """Проверка algorithm=2 (Minimum N children)."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        zabbix_response = [{
            "serviceid": "1",
            "name": "Test",
            "algorithm": "2",  # В Zabbix UI: "Minimum N children must be OK"
            "status": "0",
            "propagation_rule": "1",
            "parents": [],
            "children": [],
            "tags": [],
        }]
        
        with patch.object(client, '_make_request', return_value=zabbix_response):
            result = client.get_services_tree()
            assert result["nodes"][0]["algorithm"] == "min_n"

    def test_algorithm_percent_matches_zabbix_ui(self):
        """Проверка algorithm=3 (Percentage)."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        zabbix_response = [{
            "serviceid": "1",
            "name": "Test",
            "algorithm": "3",  # В Zabbix UI: "Percentage of children must be OK"
            "status": "0",
            "propagation_rule": "1",
            "parents": [],
            "children": [],
            "tags": [],
        }]
        
        with patch.object(client, '_make_request', return_value=zabbix_response):
            result = client.get_services_tree()
            assert result["nodes"][0]["algorithm"] == "percent"

    def test_propagation_as_ok_matches_zabbix_ui(self):
        """Проверка propagation_rule=2 (As OK)."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        zabbix_response = [{
            "serviceid": "1",
            "name": "Test",
            "algorithm": "1",
            "status": "0",
            "propagation_rule": "2",  # В Zabbix UI: "As OK"
            "parents": [],
            "children": [],
            "tags": [],
        }]
        
        with patch.object(client, '_make_request', return_value=zabbix_response):
            result = client.get_services_tree()
            assert result["nodes"][0]["propagation_rule"] == "as_ok"

    def test_propagation_ignore_matches_zabbix_ui(self):
        """Проверка propagation_rule=3 (Ignore)."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        zabbix_response = [{
            "serviceid": "1",
            "name": "Test",
            "algorithm": "1",
            "status": "0",
            "propagation_rule": "3",  # В Zabbix UI: "Ignore"
            "parents": [],
            "children": [],
            "tags": [],
        }]
        
        with patch.object(client, '_make_request', return_value=zabbix_response):
            result = client.get_services_tree()
            assert result["nodes"][0]["propagation_rule"] == "ignore"

    def test_status_mapping_matches_zabbix_ui(self):
        """Проверка что статусы маппятся правильно как в Zabbix UI."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        # В Zabbix UI: status=0 means OK, 1 means Problem, 2 means Warning
        test_cases = [
            ("0", "ok"),       # OK в Zabbix UI
            ("1", "problem"),  # Problem в Zabbix UI
            ("2", "warning"),  # Warning в Zabbix UI
        ]
        
        for zabbix_status, expected in test_cases:
            zabbix_response = [{
                "serviceid": "1",
                "name": "Test",
                "algorithm": "1",
                "status": zabbix_status,
                "propagation_rule": "1",
                "parents": [],
                "children": [],
                "tags": [],
            }]
            
            with patch.object(client, '_make_request', return_value=zabbix_response):
                result = client.get_services_tree()
                assert result["nodes"][0]["status"] == expected


class TestCacheBehavior:
    """Тесты поведения кэша."""

    def test_cache_invalidation_on_sync(self):
        """Тест что кэш инвалидируется при синхронизации."""
        from routers.services import _invalidate_services_cache, _get_cached_services_tree, _set_cached_services_tree
        
        # Устанавливаем кэш
        _set_cached_services_tree({"nodes": [], "edges": []})
        
        # Проверяем что кэш установлен
        assert _get_cached_services_tree() is not None
        
        # Инвалидируем кэш
        _invalidate_services_cache()
        
        # Проверяем что кэш пуст
        assert _get_cached_services_tree() is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
