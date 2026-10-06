# SLA Planner

Портал управления плановыми работами с интеграцией Zabbix 7.0.

## Что делает

- **Загружает SLA-услуги** из Zabbix через API (дерево сервисов с статусами)
- **Создаёт плановые работы** — автоматически добавляет исключения простоя в Zabbix SLA
- **Управляет пользователями и группами** — права доступа к конкретным ИС
- **Ведёт аудит-лог** — кто, когда, что сделал

## Архитектура

```
┌──────────────┐      ┌──────────────────┐      ┌──────────────┐
│   Браузер    │─────▶│  FastAPI (WSL)   │─────▶│  Zabbix 7.0  │
│   React SPA  │/api  │  :8000           │ API  │  :8080       │
└──────────────┘      └──────────────────┘      └──────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │  SQLite/PG   │
                       │  (БД)        │
                       └──────────────┘
```

## Структура

```
├── src/                    ← React фронтенд
│   ├── pages/              ← Страницы (Dashboard, ServiceGraph, Calendar и т.д.)
│   ├── api/client.ts       ← API клиент
│   └── components/         ← Sidebar, Header
├── sla_planner/            ← Python бэкенд
│   ├── main.py             ← FastAPI приложение
│   ├── zabbix_client.py    ← Zabbix API клиент
│   ├── routers/            ← API роуты
│   └── models.py           ← SQLAlchemy модели
├── package.json
└── vite.config.js
```

## Быстрый старт (WSL + домашний Zabbix)

### 1. Сборка фронтенда (Windows PowerShell)

```powershell
npm install
npm run build
```

### 2. Копирование в WSL

```bash
# Создай папку
sudo mkdir -p /opt/sla_planner
sudo chown $USER:$USER /opt/sla_planner

# Скопируй через WinSCP или:
cp -r sla_planner/* /opt/sla_planner/
cp -r dist /opt/sla_planner/
```

### 3. Настройка в WSL

```bash
cd /opt/sla_planner

# Создай .env
cat > .env << 'EOF'
ZABBIX_URL=http://localhost:8080/api_jsonrpc.php
ZABBIX_USERNAME=Admin
ZABBIX_PASSWORD=Zabbix
ZABBIX_SLA_NAME=Test SLA
DATABASE_URL=sqlite:///./sla_planner.db
AUTH_MODE=mock
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
EOF

# Создай venv и установи зависимости
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Скопируй фронтенд
mkdir -p static/assets templates
cp -r dist/assets/* static/assets/
cp dist/index.html templates/
```

### 4. Запуск

```bash
cd sla_planner
python main.py
```

Открой: **http://localhost:8000**

## Настройка Zabbix

1. **Создай SLA:** Сервисы → SLA → Создать SLA (имя как в `ZABBIX_SLA_NAME`)
2. **Создай услуги:** Сервисы → Дерево сервисов → Создать сервис
3. **Проверь API:**
   ```bash
   curl -s http://localhost:8080/api_jsonrpc.php \
     -X POST -H "Content-Type: application/json-rpc" \
     -d '{"jsonrpc":"2.0","method":"apiinfo.version","params":{},"id":1}'
   ```

## API эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/health` | Статус системы |
| GET | `/api/services_tree` | Дерево SLA-услуг из Zabbix |
| GET | `/api/works` | Список плановых работ |
| POST | `/api/works` | Создать работу + исключение в Zabbix |
| PATCH | `/api/works/{id}` | Обновить статус |
| GET | `/api/calendar` | Работы для календаря |
| GET | `/api/users` | Список пользователей |
| POST | `/api/users` | Создать пользователя |
| GET | `/api/groups` | Список групп |
| POST | `/api/groups` | Создать группу |
| GET | `/api/audit` | Аудит-лог |
| POST | `/api/services/sync` | Синхронизация услуг из Zabbix |

## Безопасность

- Приложение работает **только** через Zabbix API
- **Не имеет** прямого доступа к БД Zabbix
- Создаёт исключения SLA через `sla.update` (штатный метод)
- Не изменяет конфигурацию Zabbix (хосты, триггеры, алерты)

## Переменные окружения

| Переменная | Описание | Пример |
|-----------|----------|--------|
| `ZABBIX_URL` | URL API Zabbix | `http://localhost:8080/api_jsonrpc.php` |
| `ZABBIX_USERNAME` | Логин Zabbix | `Admin` |
| `ZABBIX_PASSWORD` | Пароль Zabbix | `Zabbix` |
| `ZABBIX_SLA_NAME` | Имя SLA для исключений | `Test SLA` |
| `DATABASE_URL` | Строка подключения к БД | `sqlite:///./sla_planner.db` |
| `AUTH_MODE` | Режим авторизации | `mock` / `adfs` |
