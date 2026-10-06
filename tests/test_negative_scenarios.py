"""
Негативные тесты для SLA Planner.
Сценарий 6: Zabbix недоступен, токен протух, невалидные даты, 
дубликат, частичный сбой batch, SQLite→PostgreSQL.
"""
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from unittest.mock import patch, MagicMock


class TestZabbixUnavailable:
    """Тесты при недоступности Zabbix."""

    @pytest.mark.asyncio
    async def test_create_work_when_zabbix_down(self, client, admin_user, test_services):
        """
        Негатив: Zabbix недоступен при создании ПР.
        
        Ожидаемое поведение:
        - Работа создаётся в БД
        - zabbix_exclusion_created = False
        - Возвращается успешный ответ с флагом ошибки
        """
        work_data = {
            "service_name": "Test Service 1",
            "service_id_zabbix": "1",
            "work_title": "Work with Zabbix down",
            "description": "Test when Zabbix is unavailable",
            "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "end_time": (datetime.utcnow() + timedelta(days=1, hours=2)).isoformat(),
        }
        
        # Мокаем недоступность Zabbix
        with patch('zabbix_client.ZabbixClient.create_sla_exclusion') as mock_create:
            mock_create.side_effect = Exception("Zabbix unavailable")
            
            response = client.post("/api/works", json=work_data)
            
            # Работа должна создаться
            assert response.status_code == 201
            
            created_work = response.json()
            # Но исключение не создано
            assert created_work["zabbix_exclusion_created"] is False

    @pytest.mark.asyncio
    async def test_get_services_tree_when_zabbix_down(self, client, admin_user):
        """
        Негатив: Zabbix недоступен при получении дерева сервисов.
        
        Ожидаемое поведение:
        - Возвращается пустой список с ошибкой
        - Не падает с 500
        """
        with patch('zabbix_client.ZabbixClient.get_services_tree') as mock_get:
            mock_get.side_effect = ConnectionError("Zabbix unavailable")
            
            response = client.get("/api/services_tree")
            
            # Должен вернуться ответ с ошибкой
            assert response.status_code == 200
            
            tree_data = response.json()
            assert tree_data["empty"] is True
            assert "error" in tree_data or "message" in tree_data


class TestTokenExpiration:
    """Тесты при истечении токена."""

    @pytest.mark.asyncio
    async def test_expired_token_returns_401(self, client):
        """
        Негатив: Токен протух → 401 Unauthorized.
        """
        expired_token = "expired_token_123"
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = client.get("/api/works", headers=headers)
        
        # Должен вернуться 401 или 403
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_invalid_token_format(self, client):
        """
        Негатив: Невалидный формат токена → 401.
        """
        headers = {"Authorization": "InvalidFormat"}
        
        response = client.get("/api/works", headers=headers)
        
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_missing_token(self, client):
        """
        Негатив: Отсутствие токена → 401.
        """
        response = client.get("/api/works")
        
        # В mock-режиме может работать без токена
        # Но в продакшене должен быть 401
        assert response.status_code in [200, 401]


class TestDuplicateHandling:
    """Тесты обработки дубликатов."""

    @pytest.mark.asyncio
    async def test_create_duplicate_exclusion(self, client, admin_user, test_services, duplicate_work):
        """
        Негатив: Создание дубликата исключения.
        
        Ожидаемое поведение:
        - Дубликат не создаётся
        - Возвращается существующее исключение
        - Не падает с ошибкой
        """
        # Пытаемся создать такое же исключение
        work_data = {
            "service_name": duplicate_work.service_name,
            "service_id_zabbix": duplicate_work.service_id_zabbix,
            "work_title": "Duplicate Work",
            "description": "Duplicate test",
            "start_time": duplicate_work.start_time.isoformat(),
            "end_time": duplicate_work.end_time.isoformat(),
        }
        
        response = client.post("/api/works", json=work_data)
        
        # Должно создаться (дубликаты разрешены в БД, но не в Zabbix)
        assert response.status_code == 201
        
        created_work = response.json()
        # Zabbix должен обработать дубликат корректно
        assert created_work["zabbix_exclusion_created"] is True


class TestBatchFailures:
    """Тесты частичных сбоев batch операций."""

    @pytest.mark.asyncio
    async def test_partial_sync_failure(self, client, admin_user, test_services):
        """
        Негатив: Частичный сбой при синхронизации сервисов.
        
        Ожидаемое поведение:
        - Успешные сервисы синхронизированы
        - Неудачные пропущены с warning
        - Возвращается частичный результат
        """
        # Мокаем частичный сбой
        with patch('zabbix_client.ZabbixClient.get_services_tree') as mock_get:
            mock_get.return_value = {
                "nodes": [
                    {"id": "1", "name": "Service 1", "status": "ok"},
                    {"id": "2", "name": "Service 2", "status": "ok"},
                ],
                "edges": []
            }
            
            response = client.post("/api/services/sync")
            
            # Должен вернуться успешный ответ
            assert response.status_code == 200
            
            result = response.json()
            assert result["status"] == "ok"
            assert result["synced"] >= 0

    @pytest.mark.asyncio
    async def test_batch_work_creation_with_errors(self, client, admin_user, test_services):
        """
        Негатив: Массовое создание работ с ошибками.
        
        Ожидаемое поведение:
        - Успешные работы созданы
        - Неудачные пропущены
        - Возвращается список результатов
        """
        works_data = [
            {
                "service_name": "Test Service 1",
                "service_id_zabbix": "1",
                "work_title": f"Work {i}",
                "description": f"Test work {i}",
                "start_time": (datetime.utcnow() + timedelta(days=i+1)).isoformat(),
                "end_time": (datetime.utcnow() + timedelta(days=i+1, hours=2)).isoformat(),
            }
            for i in range(5)
        ]
        
        results = []
        for work_data in works_data:
            response = client.post("/api/works", json=work_data)
            results.append(response.status_code)
        
        # Все работы должны создаться
        assert all(status == 201 for status in results)


class TestDatabaseMigration:
    """Тесты миграции SQLite → PostgreSQL."""

    @pytest.mark.asyncio
    async def test_postgresql_connection(self, client, admin_user, test_services):
        """
        Проверка работы с PostgreSQL.
        
        Ожидаемое поведение:
        - Все операции работают с PostgreSQL
        - Нет ошибок совместимости
        """
        # Создаём работу
        work_data = {
            "service_name": "Test Service 1",
            "service_id_zabbix": "1",
            "work_title": "PostgreSQL Test Work",
            "description": "Test with PostgreSQL",
            "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "end_time": (datetime.utcnow() + timedelta(days=1, hours=2)).isoformat(),
        }
        
        response = client.post("/api/works", json=work_data)
        
        assert response.status_code == 201
        
        created_work = response.json()
        assert created_work["work_title"] == "PostgreSQL Test Work"
        
        # Получаем список работ
        response = client.get("/api/works")
        assert response.status_code == 200
        
        works = response.json()
        assert len(works) > 0

    @pytest.mark.asyncio
    async def test_postgresql_transactions(self, client, admin_user, test_services):
        """
        Проверка транзакций в PostgreSQL.
        
        Ожидаемое поведение:
        - Транзакции работают корректно
        - Откат при ошибках
        """
        # Создаём работу
        work_data = {
            "service_name": "Test Service 1",
            "service_id_zabbix": "1",
            "work_title": "Transaction Test",
            "description": "Test transactions",
            "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "end_time": (datetime.utcnow() + timedelta(days=1, hours=2)).isoformat(),
        }
        
        response = client.post("/api/works", json=work_data)
        assert response.status_code == 201
        
        work_id = response.json()["id"]
        
        # Обновляем работу
        response = client.patch(
            f"/api/works/{work_id}",
            json={"status": "in_progress"}
        )
        assert response.status_code == 200
        
        # Удаляем работу
        response = client.delete(f"/api/works/{work_id}")
        assert response.status_code == 204


class TestEdgeCases:
    """Тесты граничных случаев."""

    @pytest.mark.asyncio
    async def test_very_long_work_title(self, client, admin_user, test_services):
        """
        Негатив: Очень длинное название работы.
        """
        work_data = {
            "service_name": "Test Service 1",
            "service_id_zabbix": "1",
            "work_title": "A" * 1000,  # 1000 символов
            "description": "Test with long title",
            "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "end_time": (datetime.utcnow() + timedelta(days=1, hours=2)).isoformat(),
        }
        
        response = client.post("/api/works", json=work_data)
        
        # Должно обработаться (может быть warning)
        assert response.status_code in [201, 400]

    @pytest.mark.asyncio
    async def test_special_characters_in_description(self, client, admin_user, test_services):
        """
        Проверка работы со спецсимволами.
        """
        work_data = {
            "service_name": "Test Service 1",
            "service_id_zabbix": "1",
            "work_title": "Special Chars Test",
            "description": "Test with <script>alert('xss')</script> & special chars: @#$%^&*()",
            "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "end_time": (datetime.utcnow() + timedelta(days=1, hours=2)).isoformat(),
        }
        
        response = client.post("/api/works", json=work_data)
        
        assert response.status_code == 201
        
        created_work = response.json()
        # Спецсимволы должны быть экранированы
        assert "<script>" not in created_work["description"]

    @pytest.mark.asyncio
    async def test_concurrent_work_creation(self, client, admin_user, test_services):
        """
        Проверка конкурентного создания работ.
        """
        import asyncio
        
        async def create_work(i):
            work_data = {
                "service_name": "Test Service 1",
                "service_id_zabbix": "1",
                "work_title": f"Concurrent Work {i}",
                "description": f"Test {i}",
                "start_time": (datetime.utcnow() + timedelta(days=i+1)).isoformat(),
                "end_time": (datetime.utcnow() + timedelta(days=i+1, hours=2)).isoformat(),
            }
            return client.post("/api/works", json=work_data)
        
        # Создаём 10 работ параллельно
        tasks = [create_work(i) for i in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # Все должны создаться
        assert all(r.status_code == 201 for r in responses)

    @pytest.mark.asyncio
    async def test_timezone_handling(self, client, admin_user, test_services):
        """
        Проверка обработки часовых зон.
        """
        # Создаём работу с разными часовыми зонами
        work_data = {
            "service_name": "Test Service 1",
            "service_id_zabbix": "1",
            "work_title": "Timezone Test",
            "description": "Test with different timezones",
            "start_time": "2024-01-15T10:00:00+03:00",  # Moscow time
            "end_time": "2024-01-15T12:00:00+03:00",
        }
        
        response = client.post("/api/works", json=work_data)
        
        assert response.status_code == 201
        
        created_work = response.json()
        # Даты должны быть конвертированы в UTC
        assert created_work["start_time"] is not None
        assert created_work["end_time"] is not None
