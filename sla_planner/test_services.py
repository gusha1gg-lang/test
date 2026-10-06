"""
test_services.py — Unit-тесты для модуля выгрузки сервисов.
"""
import pytest
from unittest.mock import Mock, patch
from zabbix_client import ZabbixClient


class TestServiceGet:
    """Тесты запроса service.get с разными параметрами."""

    def test_service_get_fields(self):
        """Тест что запрашиваются все необходимые поля."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        mock_response = [
            {
                "serviceid": "1",
                "name": "Test Service",
                "algorithm": "1",
                "status": "0",
                "propagation_rule": "1",
                "sortorder": "0",
                "weight": "1",
                "description": "Test description",
                "parents": [],
                "children": [],
                "tags": [],
            }
        ]
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = mock_response
            result = client.get_services_tree()
            
            # Проверяем что запрос содержит все необходимые поля
            call_args = mock_request.call_args
            assert call_args[0][0] == "service.get"
            output_fields = call_args[0][1]["output"]
            
            assert "serviceid" in output_fields
            assert "name" in output_fields
            assert "algorithm" in output_fields
            assert "status" in output_fields
            assert "propagation_rule" in output_fields
            assert "sortorder" in output_fields
            assert "weight" in output_fields
            assert "description" in output_fields

    def test_algorithm_mapping(self):
        """Тест маппинга algorithm из Zabbix в понятный формат."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        # Тестируем все варианты algorithm
        test_cases = [
            ("1", "all"),
            ("2", "min_n"),
            ("3", "percent"),
            ("unknown", "all"),  # Дефолтное значение
        ]
        
        for zabbix_algo, expected in test_cases:
            mock_response = [{
                "serviceid": "1",
                "name": "Test",
                "algorithm": zabbix_algo,
                "status": "0",
                "propagation_rule": "1",
                "parents": [],
                "children": [],
                "tags": [],
            }]
            
            with patch.object(client, '_make_request') as mock_request:
                mock_request.return_value = mock_response
                result = client.get_services_tree()
                
                assert result["nodes"][0]["algorithm"] == expected

    def test_propagation_rule_mapping(self):
        """Тест маппинга propagation_rule."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        test_cases = [
            ("1", "as_problem"),
            ("2", "as_ok"),
            ("3", "ignore"),
        ]
        
        for zabbix_rule, expected in test_cases:
            mock_response = [{
                "serviceid": "1",
                "name": "Test",
                "algorithm": "1",
                "status": "0",
                "propagation_rule": zabbix_rule,
                "parents": [],
                "children": [],
                "tags": [],
            }]
            
            with patch.object(client, '_make_request') as mock_request:
                mock_request.return_value = mock_response
                result = client.get_services_tree()
                
                assert result["nodes"][0]["propagation_rule"] == expected


class TestEdgeCases:
    """Тесты граничных случаев."""

    def test_empty_tree(self):
        """Тест пустого дерева сервисов."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = []
            result = client.get_services_tree()
            
            assert result["nodes"] == []
            assert result["edges"] == []

    def test_service_without_triggers(self):
        """Тест сервиса без триггеров."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        mock_response = [{
            "serviceid": "1",
            "name": "Test",
            "algorithm": "1",
            "status": "0",
            "propagation_rule": "1",
            "parents": [],
            "children": [],
            "tags": [],  # Нет тегов
        }]
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = mock_response
            result = client.get_services_tree()
            
            assert len(result["nodes"]) == 1
            assert result["nodes"][0]["tags"] == []

    def test_service_without_parent(self):
        """Тест корневого сервиса (без родителя)."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        mock_response = [{
            "serviceid": "1",
            "name": "Root Service",
            "algorithm": "1",
            "status": "0",
            "propagation_rule": "1",
            "parents": [],  # Нет родителя
            "children": [{"serviceid": "2"}],
            "tags": [],
        }]
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = mock_response
            result = client.get_services_tree()
            
            assert result["nodes"][0]["parent_id"] is None

    def test_large_tree_1000_services(self):
        """Тест большого дерева (1000+ сервисов)."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        # Генерируем 1000 сервисов
        mock_response = [
            {
                "serviceid": str(i),
                "name": f"Service {i}",
                "algorithm": "1",
                "status": "0",
                "propagation_rule": "1",
                "parents": [{"serviceid": str(i-1)}] if i > 0 else [],
                "children": [{"serviceid": str(i+1)}] if i < 999 else [],
                "tags": [],
            }
            for i in range(1000)
        ]
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = mock_response
            result = client.get_services_tree()
            
            assert len(result["nodes"]) == 1000
            assert len(result["edges"]) == 999


class TestServiceTriggers:
    """Тесты получения триггеров для сервиса."""

    def test_get_service_triggers_success(self):
        """Тест успешного получения триггеров."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        # Мок ответа service.get
        service_response = [{
            "serviceid": "1",
            "name": "Test Service",
            "problem_tags": [
                {"tag": "service", "value": "test"},
                {"tag": "env", "value": "prod"},
            ],
        }]
        
        # Мок ответа trigger.get
        trigger_response = [
            {
                "triggerid": "100",
                "description": "CPU > 90%",
                "expression": "{host:cpu.usage.last()}>90",
                "priority": "4",
                "value": "1",
                "tags": [
                    {"tag": "service", "value": "test"},
                ],
            }
        ]
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.side_effect = [service_response, trigger_response]
            
            triggers = client.get_service_triggers("1")
            
            assert len(triggers) == 1
            assert triggers[0]["triggerid"] == "100"
            assert triggers[0]["description"] == "CPU > 90%"
            assert triggers[0]["expression"] == "{host:cpu.usage.last()}>90"

    def test_get_service_triggers_no_tags(self):
        """Тест сервиса без problem_tags."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        service_response = [{
            "serviceid": "1",
            "name": "Test Service",
            "problem_tags": [],  # Нет тегов
        }]
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = service_response
            
            triggers = client.get_service_triggers("1")
            
            assert triggers == []

    def test_get_service_triggers_service_not_found(self):
        """Тест когда сервис не найден."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = []
            
            triggers = client.get_service_triggers("999")
            
            assert triggers == []


class TestStatusMapping:
    """Тесты маппинга статусов."""

    def test_status_mapping(self):
        """Тест маппинга статусов из Zabbix."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        test_cases = [
            ("0", "ok"),
            ("1", "problem"),
            ("2", "warning"),
            ("unknown", "ok"),  # Дефолтное значение
        ]
        
        for zabbix_status, expected in test_cases:
            mock_response = [{
                "serviceid": "1",
                "name": "Test",
                "algorithm": "1",
                "status": zabbix_status,
                "propagation_rule": "1",
                "parents": [],
                "children": [],
                "tags": [],
            }]
            
            with patch.object(client, '_make_request') as mock_request:
                mock_request.return_value = mock_response
                result = client.get_services_tree()
                
                assert result["nodes"][0]["status"] == expected


class TestCyclicReferences:
    """Тесты циклических ссылок."""

    def test_cyclic_reference_handling(self):
        """Тест что циклические ссылки не ломают граф."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        # Циклическая ссылка: A -> B -> A
        mock_response = [
            {
                "serviceid": "1",
                "name": "Service A",
                "algorithm": "1",
                "status": "0",
                "propagation_rule": "1",
                "parents": [{"serviceid": "2"}],  # Родитель — B
                "children": [{"serviceid": "2"}],  # Ребёнок — B
                "tags": [],
            },
            {
                "serviceid": "2",
                "name": "Service B",
                "algorithm": "1",
                "status": "0",
                "propagation_rule": "1",
                "parents": [{"serviceid": "1"}],  # Родитель — A
                "children": [{"serviceid": "1"}],  # Ребёнок — A
                "tags": [],
            }
        ]
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = mock_response
            result = client.get_services_tree()
            
            # Должно обработать без ошибки
            assert len(result["nodes"]) == 2
            assert len(result["edges"]) == 4  # 2 родителя + 2 ребёнка


class TestTriggerExpression:
    """Тесты expression триггера."""

    def test_trigger_expression_retrieved(self):
        """Тест что expression триггера подтягивается корректно."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        service_response = [{
            "serviceid": "1",
            "name": "Test Service",
            "problem_tags": [{"tag": "service", "value": "test"}],
        }]
        
        trigger_response = [{
            "triggerid": "100",
            "description": "CPU > 90%",
            "expression": "{host:cpu.usage.last()}>90",  # Expression
            "priority": "4",
            "value": "1",
            "tags": [{"tag": "service", "value": "test"}],
        }]
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.side_effect = [service_response, trigger_response]
            
            triggers = client.get_service_triggers("1")
            
            assert len(triggers) == 1
            assert triggers[0]["expression"] == "{host:cpu.usage.last()}>90"
            assert triggers[0]["description"] == "CPU > 90%"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
