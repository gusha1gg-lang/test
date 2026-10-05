"""
test_zabbix_client.py — Unit-тесты для Zabbix клиента.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from zabbix_client import ZabbixClient, ZabbixAPIError
from config import settings


class TestZabbixClientAuth:
    """Тесты авторизации и управления токеном."""

    def test_login_success(self):
        """Тест успешной авторизации."""
        client = ZabbixClient()
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = "test_token_123"
            
            result = client.login()
            
            assert result is True
            assert client.auth_token == "test_token_123"
            assert client.token_expires_at is not None
            # Токен должен быть действителен ~4 часа
            expected_expiry = datetime.now() + timedelta(hours=4)
            assert abs((client.token_expires_at - expected_expiry).total_seconds()) < 1

    def test_login_failure(self):
        """Тест неудачной авторизации."""
        client = ZabbixClient()
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.side_effect = Exception("Invalid credentials")
            
            result = client.login()
            
            assert result is False
            assert client.auth_token is None

    def test_token_validity_check(self):
        """Тест проверки валидности токена."""
        client = ZabbixClient()
        
        # Нет токена
        assert client._is_token_valid() is False
        
        # Токен есть, но не истёк
        client.auth_token = "test_token"
        client.token_expires_at = datetime.now() + timedelta(hours=1)
        assert client._is_token_valid() is True
        
        # Токен истёк
        client.token_expires_at = datetime.now() - timedelta(hours=1)
        assert client._is_token_valid() is False


class TestZabbixClientRetry:
    """Тесты retry логики."""

    def test_retry_on_5xx_error(self):
        """Тест retry при 5xx ошибке."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {}
        
        with patch('requests.post') as mock_post:
            # Первый вызов — 500, второй — 200
            mock_response_success = Mock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {
                "jsonrpc": "2.0",
                "result": {"serviceid": "1", "name": "Test"},
                "id": 1
            }
            mock_post.side_effect = [mock_response, mock_response_success]
            
            with patch('time.sleep'):  # Пропускаем реальную задержку
                result = client._make_request("service.get", {})
                
                assert result == {"serviceid": "1", "name": "Test"}
                assert mock_post.call_count == 2

    def test_retry_max_attempts(self):
        """Тест максимального количества попыток."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        client.max_retries = 3
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {}
        
        with patch('requests.post') as mock_post:
            mock_post.return_value = mock_response
            
            with patch('time.sleep'):
                with pytest.raises(Exception):
                    client._make_request("service.get", {})
                
                # Должно быть 4 вызова: 1 начальный + 3 retry
                assert mock_post.call_count == 4

    def test_no_retry_on_4xx_error(self):
        """Тест отсутствия retry при 4xx ошибке."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "error": {"code": -32602, "message": "Invalid params", "data": ""},
            "id": 1
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.post') as mock_post:
            mock_post.return_value = mock_response
            
            with pytest.raises(ZabbixAPIError):
                client._make_request("service.get", {})
            
            # Должен быть только 1 вызов (без retry)
            assert mock_post.call_count == 1


class TestSLAExclusion:
    """Тесты создания SLA исключений."""

    def test_create_exclusion_success(self):
        """Тест успешного создания исключения."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        # Мок данных SLA
        mock_sla = {
            "slaid": "1",
            "name": "Test SLA",
            "excluded_downtimes": []
        }
        
        with patch.object(client, '_make_request') as mock_request:
            # Первый вызов — sla.get, второй — sla.update
            mock_request.side_effect = [
                [mock_sla],  # sla.get
                {}  # sla.update
            ]
            
            result = client.create_sla_exclusion(
                service_name="Test Service",
                start_timestamp=1700000000.0,
                end_timestamp=1700003600.0,
                description="Test maintenance"
            )
            
            assert result is True
            assert mock_request.call_count == 2
            
            # Проверяем что sla.update вызван с правильными параметрами
            call_args = mock_request.call_args_list[1]
            assert call_args[0][0] == "sla.update"
            assert call_args[0][1]["slaid"] == "1"
            assert len(call_args[0][1]["excluded_downtimes"]) == 1

    def test_create_exclusion_duplicate_check(self):
        """Тест проверки на дубликаты."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        # Мок данных SLA с существующим исключением
        mock_sla = {
            "slaid": "1",
            "name": "Test SLA",
            "excluded_downtimes": [
                {
                    "name": "ПР: Existing maintenance (Test Service)",
                    "period_from": "1700000000",
                    "period_to": "1700003600"
                }
            ]
        }
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = [mock_sla]
            
            # Пытаемся создать дубликат
            result = client.create_sla_exclusion(
                service_name="Test Service",
                start_timestamp=1700000000.0,
                end_timestamp=1700003600.0,
                description="Existing maintenance"
            )
            
            assert result is True  # Считаем успехом
            # sla.update НЕ должен вызываться
            assert mock_request.call_count == 1

    def test_create_exclusion_invalid_timestamps(self):
        """Тест валидации временных меток."""
        client = ZabbixClient()
        
        # start > end
        with pytest.raises(ValueError, match="Start time must be before end time"):
            client.create_sla_exclusion(
                service_name="Test Service",
                start_timestamp=1700003600.0,
                end_timestamp=1700000000.0,
                description="Test"
            )
        
        # start == end
        with pytest.raises(ValueError, match="Start time must be before end time"):
            client.create_sla_exclusion(
                service_name="Test Service",
                start_timestamp=1700000000.0,
                end_timestamp=1700000000.0,
                description="Test"
            )

    def test_create_exclusion_missing_params(self):
        """Тест валидации обязательных параметров."""
        client = ZabbixClient()
        
        # Пустое имя сервиса
        with pytest.raises(ValueError, match="service_name and description are required"):
            client.create_sla_exclusion(
                service_name="",
                start_timestamp=1700000000.0,
                end_timestamp=1700003600.0,
                description="Test"
            )
        
        # Пустое описание
        with pytest.raises(ValueError, match="service_name and description are required"):
            client.create_sla_exclusion(
                service_name="Test Service",
                start_timestamp=1700000000.0,
                end_timestamp=1700003600.0,
                description=""
            )

    def test_create_exclusion_sla_not_found(self):
        """Тест когда SLA не найден."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = []  # SLA не найден
            
            result = client.create_sla_exclusion(
                service_name="Test Service",
                start_timestamp=1700000000.0,
                end_timestamp=1700003600.0,
                description="Test"
            )
            
            assert result is False

    def test_create_exclusion_api_error(self):
        """Тест обработки ошибки API."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.side_effect = ZabbixAPIError(-32600, "Invalid request", "")
            
            result = client.create_sla_exclusion(
                service_name="Test Service",
                start_timestamp=1700000000.0,
                end_timestamp=1700003600.0,
                description="Test"
            )
            
            assert result is False


class TestTimezoneHandling:
    """Тесты обработки временных зон."""

    def test_timestamp_conversion(self):
        """Тест конвертации datetime в timestamp."""
        # Создаём datetime в UTC
        dt_utc = datetime(2024, 1, 1, 12, 0, 0)
        timestamp = dt_utc.timestamp()
        
        # Проверяем что это правильное Unix timestamp
        assert isinstance(timestamp, float)
        assert int(timestamp) == int(dt_utc.timestamp())

    def test_timestamp_precision(self):
        """Тест точности timestamp (до секунд)."""
        client = ZabbixClient()
        
        # Timestamp с миллисекундами
        timestamp_with_ms = 1700000000.123
        
        # При конвертации в str(int()) миллисекунды должны отброситься
        result = str(int(timestamp_with_ms))
        assert result == "1700000000"


class TestEdgeCases:
    """Тесты граничных случаев."""

    def test_overlapping_exclusions(self):
        """Тест пересечения исключений (должно предупреждать, но не блокировать)."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        # Существующее исключение: 10:00-12:00
        mock_sla = {
            "slaid": "1",
            "name": "Test SLA",
            "excluded_downtimes": [
                {
                    "name": "ПР: Existing (Service)",
                    "period_from": "1700000000",  # 10:00
                    "period_to": "1700007200"     # 12:00
                }
            ]
        }
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.side_effect = [
                [mock_sla],  # sla.get
                {}  # sla.update
            ]
            
            # Новое исключение: 11:00-13:00 (пересекается)
            result = client.create_sla_exclusion(
                service_name="Service",
                start_timestamp=1700003600.0,  # 11:00
                end_timestamp=1700010800.0,    # 13:00
                description="Overlapping"
            )
            
            # Должно создаться (Zabbix позволяет пересечения)
            assert result is True

    def test_past_window_warning(self):
        """Тест окна задним числом (должно предупреждать, но не блокировать)."""
        client = ZabbixClient()
        
        # Окно в прошлом
        past_timestamp = (datetime.now() - timedelta(days=1)).timestamp()
        
        # Не должно вызывать ошибку (Zabbix принимает прошлые окна)
        with patch.object(client, '_make_request') as mock_request:
            mock_request.side_effect = [
                [{"slaid": "1", "excluded_downtimes": []}],
                {}
            ]
            
            result = client.create_sla_exclusion(
                service_name="Service",
                start_timestamp=past_timestamp,
                end_timestamp=past_timestamp + 3600,
                description="Past window"
            )
            
            # Должно создаться
            assert result is True


class TestUpdateSLAExclusion:
    """Тесты обновления SLA исключений."""

    def test_update_exclusion_success(self):
        """Тест успешного обновления исключения."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        mock_sla = {
            "slaid": "1",
            "name": "Test SLA",
            "excluded_downtimes": [
                {
                    "name": "ПР: Old maintenance (Service)",
                    "period_from": "1700000000",
                    "period_to": "1700003600"
                }
            ]
        }
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.side_effect = [
                [mock_sla],  # sla.get
                {}  # sla.update
            ]
            
            result = client.update_sla_exclusion(
                old_start_timestamp=1700000000.0,
                old_end_timestamp=1700003600.0,
                new_start_timestamp=1700007200.0,  # Сдвиг на 2 часа
                new_end_timestamp=1700010800.0,
                service_name="Service",
                description="Updated maintenance"
            )
            
            assert result is True
            assert mock_request.call_count == 2

    def test_update_exclusion_not_found(self):
        """Тест обновления несуществующего исключения."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        mock_sla = {
            "slaid": "1",
            "name": "Test SLA",
            "excluded_downtimes": []  # Пусто
        }
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.side_effect = [
                [mock_sla],  # sla.get
                {}  # sla.update (всё равно вызывается)
            ]
            
            result = client.update_sla_exclusion(
                old_start_timestamp=1700000000.0,
                old_end_timestamp=1700003600.0,
                new_start_timestamp=1700007200.0,
                new_end_timestamp=1700010800.0,
                service_name="Service",
                description="New maintenance"
            )
            
            # Должно создаться новое исключение
            assert result is True


class TestDeleteSLAExclusion:
    """Тесты удаления SLA исключений."""

    def test_delete_exclusion_success(self):
        """Тест успешного удаления исключения."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        mock_sla = {
            "slaid": "1",
            "name": "Test SLA",
            "excluded_downtimes": [
                {
                    "name": "ПР: Maintenance (Service)",
                    "period_from": "1700000000",
                    "period_to": "1700003600"
                },
                {
                    "name": "ПР: Other (Service)",
                    "period_from": "1700010000",
                    "period_to": "1700013600"
                }
            ]
        }
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.side_effect = [
                [mock_sla],  # sla.get
                {}  # sla.update
            ]
            
            result = client.delete_sla_exclusion(
                start_timestamp=1700000000.0,
                end_timestamp=1700003600.0
            )
            
            assert result is True
            
            # Проверяем что sla.update вызван с правильным количеством исключений
            call_args = mock_request.call_args_list[1]
            assert len(call_args[0][1]["excluded_downtimes"]) == 1  # Осталось 1 исключение

    def test_delete_exclusion_not_found(self):
        """Тест удаления несуществующего исключения."""
        client = ZabbixClient()
        client.auth_token = "test_token"
        
        mock_sla = {
            "slaid": "1",
            "name": "Test SLA",
            "excluded_downtimes": [
                {
                    "name": "ПР: Other (Service)",
                    "period_from": "1700010000",
                    "period_to": "1700013600"
                }
            ]
        }
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = [mock_sla]
            
            result = client.delete_sla_exclusion(
                start_timestamp=1700000000.0,  # Не существует
                end_timestamp=1700003600.0
            )
            
            assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
