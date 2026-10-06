# 🚀 SLA Planner — Инструкция по развёртыванию (Windows + WSL)

## Архитектура

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────┐
│   Браузер       │────▶│  FastAPI (WSL)   │────▶│  Zabbix 7.0  │
│   React SPA     │/api │  :8000           │     │  :8080       │
│   (dist/)       │     │                  │     │              │
└─────────────────┘     └──────────────────┘     └──────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  SQLite/PG   │
                        │  (БД)        │
                        └──────────────┘
```

---

## 📁 Шаг 1: Куда кидать файлы на Windows

Все файлы проекта лежат в папке `sla_planner/` внутри этого проекта.

### Структура:
```
sla_planner/                    ← Python бэкенд (FastAPI)
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── config.py
├── main.py
├── database.py
├── models.py
├── zabbix_client.py
├── auth.py
├── routers/
│   ├── __init__.py
│   ├── works.py
│   ├── services.py
│   ├── calendar.py
│   └── settings.py
├── static/                     ← Сюда скопировать dist/ из React
│   ├── css/
│   └── js/
└── templates/
    └── index.html              ← Скопировать dist/index.html сюда
```

---

## 🐧 Шаг 2: Копирование в WSL

### 2.1. Открой WSL терминал:
```bash
wsl
```

### 2.2. Создай рабочую папку:
```bash
mkdir -p ~/sla_planner
cd ~/sla_planner
```

### 2.3. Скопируй файлы из Windows в WSL:

**Вариант A** — через проводник Windows (самый простой):
```
# В адресной строке проводника Windows набери:
\\wsl$\Ubuntu\home\ТВОЙ_ЛОГИН\sla_planner

# И скопируй туда все файлы из папки sla_planner/
```

**Вариант B** — через терминал:
```bash
# Из Windows PowerShell:
wsl cp -r /mnt/c/Путь/К/проекту/sla_planner/* ~/sla_planner/
```

---

## ⚙️ Шаг 3: Настройка .env

```bash
cd ~/sla_planner
cp .env.example .env
nano .env
```

Заполни реальные данные:
```env
ZABBIX_URL=http://zabbix.corp.local:8080/api_jsonrpc.php
ZABBIX_USERNAME=Admin
ZABBIX_PASSWORD=твой_пароль
ZABBIX_SLA_NAME=Название_SLA_в_Zabbix

DATABASE_URL=sqlite:///./sla_planner.db
AUTH_MODE=mock

APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
```

---

## 🐍 Шаг 4: Установка Python и зависимостей

### 4.1. Проверь Python:
```bash
python3 --version
# Должно быть 3.11+

# Если нет — установи:
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

### 4.2. Создай виртуальное окружение:
```bash
cd ~/sla_planner
python3 -m venv venv
source venv/bin/activate
```

### 4.3. Установи зависимости:
```bash
pip install -r requirements.txt
```

---

## 🏗️ Шаг 5: Сборка фронтенда

### 5.1. Скопируй собранный фронтенд в папку бэкенда:

```bash
# Фронтенд уже собран в dist/ — скопируем его в static/ бэкенда
cp -r dist/* ~/sla_planner/static/
cp dist/index.html ~/sla_planner/templates/index.html
```

### 5.2. Либо пересобери фронтенд (если менял код):
```bash
# Из папки React-проекта (в Windows или WSL):
npm run build

# Затем скопируй:
cp -r dist/* ~/sla_planner/static/
cp dist/index.html ~/sla_planner/templates/index.html
```

---

## 🚀 Шаг 6: Запуск

```bash
cd ~/sla_planner
source venv/bin/activate
python main.py
```

Откроется:
```
==================================================
  SLA Planner — запуск
==================================================
  Database : sqlite:///./sla_planner.db
  Zabbix   : http://zabbix.corp.local:8080/api_jsonrpc.php
  SLA Name : Название_SLA_в_Zabbix
  Auth     : mock
==================================================
✅ Database tables created
✅ Connected to Zabbix
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Открой в браузере:
```
http://localhost:8000
```

---

## 🔄 Шаг 7: Проверка работы

1. **Панель управления** — показывает статус подключения к Zabbix
2. **SLA-услуги из Zabbix** — интерактивный граф, загружается из Zabbix API
3. **Новая работа** — регистрация ПР, автоматически создаёт исключение в Zabbix SLA
4. **Список работ** — все зарегистрированные ПР
5. **Календарь** — визуальное представление
6. **SLA Отчёт** — данные из Zabbix + созданные исключения
7. **Настройки** — текущая конфигурация + проверка подключения

---

## 🐳 Альтернатива: Docker

```bash
cd ~/sla_planner
docker-compose up -d
```

---

## 🔧 Решение проблем

### «Zabbix unavailable»
- Проверь URL в .env — должен быть доступен из WSL
- Проверь логин/пароль
- В Zabbix 7.0 используется `username` (не `user`)

### «Cannot connect to server» на фронтенде
- Убедись что `python main.py` запущен
- Проверь что порт 8000 не занят: `sudo lsof -i :8000`

### Фронтенд не загружается
- Проверь что `dist/` скопирован в `templates/` и `static/`
- Файл `templates/index.html` должен существовать

### Смена SQLite → PostgreSQL
```env
# В .env:
DATABASE_URL=postgresql://user:password@localhost:5432/sla_planner
```
Таблицы создадутся автоматически при следующем запуске.

---

## 📝 Быстрый старт (одной командой)

```bash
# В WSL:
cd ~
git clone <repo> || mkdir sla_planner && cd sla_planner
cp .env.example .env && nano .env  # заполни данные
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py
# → http://localhost:8000
```
