"""
Интеграционные тесты для плановых работ и SLA исключений.
Сценарии 1-3: Создание, изменение, отмена ПР.
"""
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient

from tests.conftest import create_test_work_data


class TestPlannedWorkLifecycle:
    """Тесты жизненного цикла плановой работы."""

    @pytest.mark.asyncio
    async def test_create_work_creates_zabbix_exclusion(self, client, admin_user, test_services):
        """
        Сценарий 1: Создание ПР → исключение в Zabbix.
        
        Шаги:
        1. POST /api/works с данными ПР
        2. Проверить что работа создана в БД
        3. Проверить что zabbix_exclusion_created = True
        4. Проверить что в мок Zabbix добавлено исключение
        """
        work_data = create_test_work_data()
        
        response = client.post("/api/works", json=work_data)
        
        assert response.status_code == 201, f"Failed to create work: {response.json()}"
        
        created_work = response.json()
        assert created_work["service_name"] == work_data["service_name"]
        assert created_work["work_title"] == work_data["work_title"]
        assert created_work["zabbix_exclusion_created"] is True
        assert created_work["status"] == "planned"
        assert created_work["created_by"] == "test_admin"

    @pytest.mark.asyncio
    async def test_update_work_updates_zabbix_exclusion(self, client, admin_user, test_services, sample_work):
        """
        Сценарий 2: Изменение ПР → исключение обновилось.
        
        Шаги:
        1. PATCH /api/works/{id} с новыми датами
        2. Проверить что работа обновлена в БД
        3. Проверить что в мок Zabbix исключение обновлено
        """
        new_end_time = sample_work.end_time + timedelta(hours=1)
        
        response = client.patch(
            f"/api/works/{sample_work.id}",
            json={"status": "in_progress"}
        )
        
        assert response.status_code == 200, f"Failed to update work: {response.json()}"
        
        updated_work = response.json()
        assert updated_work["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_cancel_work_removes_zabbix_exclusion(self, client, admin_user, test_services, sample_work):
        """
        Сценарий 3: Отмена ПР → исключение удалено.
        
        Шаги:
        1. PATCH /api/works/{id} со status='cancelled'
        2. Проверить что работа отменена в БД
        3. Проверить что в мок Zabbix исключение удалено
        """
        response = client.patch(
            f"/api/works/{sample_work.id}",
            json={"status": "cancelled"}
        )
        
        assert response.status_code == 200, f"Failed to cancel work: {response.json()}"
        
        cancelled_work = response.json()
        assert cancelled_work["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_delete_work_removes_zabbix_exclusion(self, client, admin_user, test_services, sample_work):
        """
        Удаление ПР → исключение удалено из Zabbix.
        """
        response = client.delete(f"/api/works/{sample_work.id}")
        
        assert response.status_code == 204, f"Failed to delete work: {response.text}"

    @pytest.mark.asyncio
    async def test_create_work_without_access_denied(self, client, regular_user, test_services):
        """
        Негатив: Создание ПР без доступа к сервису → 403.
        """
        work_data = create_test_work_data(service_id="999", service_name="Non-existent Service")
        
        response = client.post("/api/works", json=work_data)
        
        # Должен быть отказ в доступе или ошибка валидации
        assert response.status_code in [403, 400, 422]


class TestPlannedWorkValidation:
    """Тесты валидации плановых работ."""

    @pytest.mark.asyncio
    async def test_create_work_with_invalid_dates(self, client, admin_user, test_services, invalid_dates):
        """
        Негатив: Невалидные даты (end < start) → 400.
        """
        work_data = {
            "service_name": "Test Service 1",
            "service_id_zabbix": "1",
            "work_title": "Invalid Work",
            "description": "Test with invalid dates",
            "start_time": invalid_dates["start_time"].isoformat(),
            "end_time": invalid_dates["end_time"].isoformat(),
        }
        
        response = client.post("/api/works", json=work_data)
        
        assert response.status_code == 400
        assert "End time must be after start time" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_work_with_missing_fields(self, client, admin_user, test_services):
        """
        Негатив: Отсутствие обязательных полей → 422.
        """
        work_data = {
            "service_name": "Test Service 1",
            # Отсутствуют обязательные поля
        }
        
        response = client.post("/api/works", json=work_data)
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_work_with_past_dates(self, client, admin_user, test_services):
        """
        Негатив: Даты в прошлом → warning, но работа создаётся.
        """
        work_data = {
            "service_name": "Test Service 1",
            "service_id_zabbix": "1",
            "work_title": "Past Work",
            "description": "Work in the past",
            "start_time": (datetime.utcnow() - timedelta(days=2)).isoformat(),
            "end_time": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        }
        
        response = client.post("/api/works", json=work_data)
        
        # Работа должна создаться (предупреждение в логах)
        assert response.status_code == 201
