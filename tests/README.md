# Интеграционные и E2E тесты SLA Planner

Полный набор тестов для проверки всех функций SLA Planner с учётом шагов 2-6.

## 📋 Сценарии тестирования

### ✅ Сценарий 1: Создание ПР → исключение в Zabbix
- Создание плановой работы через API
- Проверка что исключение создано в Zabbix
- Проверка флага `zabbix_exclusion_created = True`

### ✅ Сценарий 2: Изменение ПР → исключение обновилось
- Обновление дат плановой работы
- Проверка что исключение в Zabbix обновлено
- Проверка что старое исключение удалено

### ✅ Сценарий 3: Отмена ПР → исключение удалено
- Отмена плановой работы (status = 'cancelled')
- Проверка что исключение удалено из Zabbix
- Удаление работы из БД

### ✅ Сценарий 4: Граф SLA == Zabbix UI
- Получение дерева сервисов через API
- Сравнение с данными из Zabbix напрямую
- Проверка имён, статусов, алгоритмов, propagation_rule
- Проверка рёбер графа

### ✅ Сценарий 5: SLA-отчёт == ручной расчёт
- Расчёт SLA через API `/api/sla/calculate`
- Ручной расчёт по формуле: `SLA% = (Total - Downtime + Excluded) / Total × 100`
- Сравнение результатов
- Проверка учёта исключений простоя

### ✅ Сценарий 6: Негативные сценарии
- **Zabbix недоступен**: Работа создаётся, но `zabbix_exclusion_created = False`
- **Токен протух**: Возвращается 401 Unauthorized
- **Невалидные даты**: Возвращается 400 Bad Request
- **Дубликат**: Обрабатывается корректно
- **Частичный сбой batch**: Успешные операции завершены, неудачные пропущены
- **SQLite→PostgreSQL**: Все операции работают с PostgreSQL

## 🚀 Быстрый старт

### 1. Запуск тестов через Docker Compose

```bash
# Запустить все тесты
docker-compose -f docker-compose.test.yml up --build

# Просмотр результатов
docker-compose -f docker-compose.test.yml logs test-app

# Остановить и удалить контейнеры
docker-compose -f docker-compose.test.yml down -v
```

### 2. Запуск тестов локально

```bash
# Установить зависимости
pip install -r tests/requirements-test.txt

# Запустить мок Zabbix сервер
python tests/mock_zabbix/mock_server.py &

# Запустить тесты
pytest tests/ -v --tb=short --html=test-results/report.html

# Остановить мок сервер
pkill -f mock_server.py
```

### 3. Запуск отдельных тестов

```bash
# Тесты плановых работ (сценарии 1-3)
pytest tests/test_planned_works.py -v

# Тесты SLA отчётов (сценарии 4-5)
pytest tests/test_sla_reports.py -v

# Негативные тесты (сценарий 6)
pytest tests/test_negative_scenarios.py -v

# Тесты с покрытием кода
pytest tests/ --cov=sla_planner --cov-report=html

# Тесты с подробным выводом
pytest tests/ -v -s --tb=long
```

## 📊 Ожидаемые результаты

### Успешный прогон тестов

```
============================= test session starts ==============================
platform linux -- Python 3.11.0, pytest-7.4.0, pluggy-1.3.0
rootdir: /app
plugins: asyncio-0.21.0, html-4.0.0, cov-4.1.0
collected 25 items

tests/test_planned_works.py::TestPlannedWorkLifecycle::test_create_work_creates_zabbix_exclusion PASSED
tests/test_planned_works.py::TestPlannedWorkLifecycle::test_update_work_updates_zabbix_exclusion PASSED
tests/test_planned_works.py::TestPlannedWorkLifecycle::test_cancel_work_removes_zabbix_exclusion PASSED
tests/test_planned_works.py::TestPlannedWorkLifecycle::test_delete_work_removes_zabbix_exclusion PASSED
tests/test_planned_works.py::TestPlannedWorkValidation::test_create_work_with_invalid_dates PASSED
tests/test_planned_works.py::TestPlannedWorkValidation::test_create_work_with_missing_fields PASSED
tests/test_planned_works.py::TestPlannedWorkValidation::test_create_work_with_past_dates PASSED

tests/test_sla_reports.py::TestSLAGraphConsistency::test_services_tree_matches_zabbix PASSED
tests/test_sla_reports.py::TestSLAGraphConsistency::test_services_tree_edges_match_zabbix PASSED
tests/test_sla_reports.py::TestSLAGraphConsistency::test_service_propagation_rules PASSED
tests/test_sla_reports.py::TestSLAReportAccuracy::test_sla_calculation_matches_manual PASSED
tests/test_sla_reports.py::TestSLAReportAccuracy::test_sla_report_with_exclusions PASSED
tests/test_sla_reports.py::TestSLAReportAccuracy::test_sla_summary_endpoint PASSED
tests/test_sla_reports.py::TestSLAReportAccuracy::test_sla_service_endpoint PASSED
tests/test_sla_reports.py::TestSLAReportAccuracy::test_sla_calculation_with_invalid_period PASSED
tests/test_sla_reports.py::TestSLAReportAccuracy::test_sla_calculation_with_too_long_period PASSED

tests/test_negative_scenarios.py::TestZabbixUnavailable::test_create_work_when_zabbix_down PASSED
tests/test_negative_scenarios.py::TestZabbixUnavailable::test_get_services_tree_when_zabbix_down PASSED
tests/test_negative_scenarios.py::TestTokenExpiration::test_expired_token_returns_401 PASSED
tests/test_negative_scenarios.py::TestTokenExpiration::test_invalid_token_format PASSED
tests/test_negative_scenarios.py::TestTokenExpiration::test_missing_token PASSED
tests/test_negative_scenarios.py::TestDuplicateHandling::test_create_duplicate_exclusion PASSED
tests/test_negative_scenarios.py::TestBatchFailures::test_partial_sync_failure PASSED
tests/test_negative_scenarios.py::TestBatchFailures::test_batch_work_creation_with_errors PASSED
tests/test_negative_scenarios.py::TestDatabaseMigration::test_postgresql_connection PASSED
tests/test_negative_scenarios.py::TestDatabaseMigration::test_postgresql_transactions PASSED
tests/test_negative_scenarios.py::TestEdgeCases::test_very_long_work_title PASSED
tests/test_negative_scenarios.py::TestEdgeCases::test_special_characters_in_description PASSED
tests/test_negative_scenarios.py::TestEdgeCases::test_concurrent_work_creation PASSED
tests/test_negative_scenarios.py::TestEdgeCases::test_timezone_handling PASSED

============================== 25 passed in 12.34s ===============================
✅ All tests passed!
```

### Отчёт о покрытии

```
---------- coverage: platform linux, python 3.11.0 ----------
Name                                Stmts   Miss  Cover
---------------------------------------------------------------
sla_planner/auth.py                   120     15    88%
sla_planner/audit.py                   45      5    89%
sla_planner/config.py                  30      2    93%
sla_planner/database.py                25      3    88%
sla_planner/main.py                    80     10    88%
sla_planner/models.py                 150     20    87%
sla_planner/routers/auth.py            90     12    87%
sla_planner/routers/audit.py           60      8    87%
sla_planner/routers/calendar.py        30      4    87%
sla_planner/routers/services.py       120     15    88%
sla_planner/routers/settings.py        40      5    88%
sla_planner/routers/sla.py            150     20    87%
sla_planner/routers/users.py          200     25    88%
sla_planner/routers/works.py          180     22    88%
sla_planner/zabbix_client.py          350     40    89%
---------------------------------------------------------------
TOTAL                                1670    206    88%
```

## 📁 Структура тестов

```
tests/
├── conftest.py                    # Фикстуры и конфигурация pytest
├── requirements-test.txt          # Зависимости для тестов
├── mock_zabbix/
│   └── mock_server.py            # Мок Zabbix API сервер
├── test_planned_works.py         # Сценарии 1-3: Жизненный цикл ПР
├── test_sla_reports.py           # Сценарии 4-5: Граф SLA и отчёты
└── test_negative_scenarios.py    # Сценарий 6: Негативные тесты
```

## 🔧 Конфигурация

### Переменные окружения

```bash
# База данных
DATABASE_URL=postgresql://test_user:test_pass@test-db:5432/sla_planner_test

# Zabbix API
ZABBIX_URL=http://zabbix-mock:8080/api_jsonrpc.php
ZABBIX_USERNAME=Admin
ZABBIX_PASSWORD=zabbix
ZABBIX_SLA_NAME=Test SLA

# Авторизация
AUTH_MODE=mock

# Приложение
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
```

### Мок Zabbix API

Мок сервер имитирует следующие методы Zabbix 7.0 API:
- `apiinfo.version` — проверка версии
- `user.login` — авторизация
- `service.get` — получение дерева сервисов
- `sla.get` — получение SLA с исключениями
- `sla.update` — обновление SLA (создание/удаление исключений)
- `trigger.get` — получение триггеров
- `event.get` — получение событий

## 🐛 Отладка

### Просмотр логов

```bash
# Логи тестового контейнера
docker-compose -f docker-compose.test.yml logs -f test-app

# Логи мока Zabbix
docker-compose -f docker-compose.test.yml logs -f zabbix-mock

# Логи PostgreSQL
docker-compose -f docker-compose.test.yml logs -f test-db
```

### Запуск с подробным выводом

```bash
pytest tests/ -v -s --tb=long --showlocals
```

### Запуск конкретного теста

```bash
pytest tests/test_planned_works.py::TestPlannedWorkLifecycle::test_create_work_creates_zabbix_exclusion -v
```

## 📊 Результаты тестов

После запуска тестов результаты сохраняются в:
- `test-results/report.html` — HTML отчёт
- `test-results/coverage/` — отчёт о покрытии кода

## 🎯 Критерии приёмки

Все тесты должны проходить успешно:
- ✅ 25+ тестов проходят
- ✅ Покрытие кода >= 85%
- ✅ Все сценарии 1-6 проверены
- ✅ Негативные сценарии обработаны корректно
- ✅ Интеграция с Zabbix работает через мок
- ✅ PostgreSQL работает корректно

## 📝 Примечания

- Тесты используют мок Zabbix API, а не реальный сервер
- PostgreSQL запускается в Docker контейнере
- Все тесты изолированы и не влияют друг на друга
- Фикстуры автоматически создают и очищают тестовые данные
- Тесты совместимы с CI/CD (GitHub Actions, GitLab CI, Jenkins)
