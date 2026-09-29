# 🚀 SLA Planner — Полная инструкция по развертыванию

## 📋 Содержание
1. [Архитектура](#архитектура)
2. [Требования](#требования)
3. [Сборка фронтенда (Windows)](#сборка-фронтенда-windows)
4. [Копирование в WSL](#копирование-в-wsl)
5. [Развертывание в WSL](#развертывание-в-wsl)
6. [Настройка Zabbix](#настройка-zabbix)
7. [Запуск и проверка](#запуск-и-проверка)
8. [Решение проблем](#решение-проблем)

---

## 🏗️ Архитектура

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

## ✅ Требования

### Windows:
- Node.js 18+ (для сборки фронтенда)
- npm (устанавливается вместе с Node.js)

### WSL (Ubuntu):
- Python 3.11+ (рекомендуется 3.12 или 3.13)
- pip
- venv
- Доступ к Zabbix серверу по сети

---

## 📦 Сборка фронтенда (Windows)

### Шаг 1: Откройте PowerShell в папке проекта

```powershell
cd C:\path\to\your\project
```

### Шаг 2: Установите зависимости (если ещё не установлены)

```powershell
npm install
```

### Шаг 3: Соберите фронтенд

```powershell
npm run build
```

Результат: создастся папка `dist/` со следующими файлами:
```
dist/
├── index.html
└── assets/
    ├── index-XXXXX.css
    └── index-XXXXX.js
```

---

## 📂 Копирование в WSL

### Вариант A: Через проводник Windows (самый простой)

1. Откройте проводник Windows
2. В адресной строке введите:
   ```
   \\wsl$\Ubuntu\home\ВАШ_ЛОГИН\
   ```
3. Создайте папку `sla_planner`
4. Скопируйте **всё содержимое** папки `sla_planner/` из проекта
5. Скопируйте папку `dist/` в `sla_planner/dist/`

### Вариант B: Через терминал WSL

```bash
# Из PowerShell:
wsl

# В WSL:
cd ~
mkdir -p sla_planner
cd sla_planner

# Копирование из Windows (замените путь)
cp -r /mnt/c/path/to/project/sla_planner/* .
cp -r /mnt/c/path/to/project/dist .
```

### Вариант C: Через git (если проект в репозитории)

```bash
cd ~
git clone <your-repo-url> sla_planner
cd sla_planner
# Скопируйте dist/ из Windows в эту папку
```

---

## 🚀 Развертывание в WSL

### Автоматическое развертывание (рекомендуется)

```bash
cd ~/sla_planner
chmod +x deploy.sh
./deploy.sh
```

Скрипт автоматически:
- ✅ Проверит Python
- ✅ Создаст виртуальное окружение
- ✅ Установит зависимости
- ✅ Скопирует фронтенд из `dist/` в `static/` и `templates/`
- ✅ Создаст `.env` из примера
- ✅ Проверит структуру проекта
- ✅ Запустит сервер

### Ручное развертывание

Если скрипт не работает, выполните вручную:

```bash
cd ~/sla_planner

# 1. Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# 2. Установите зависимости
pip install --upgrade pip
pip install -r requirements.txt

# 3. Скопируйте фронтенд
mkdir -p static/assets templates
cp -r dist/assets/* static/assets/
cp dist/index.html templates/index.html

# 4. Создайте .env
cp .env.example .env
nano .env  # Отредактируйте параметры

# 5. Запустите сервер
python main.py
```

---

## ⚙️ Настройка .env

Откройте файл `.env` и заполните реальные данные:

```env
# Zabbix подключение
ZABBIX_URL=http://zabbix.corp.local:8080/api_jsonrpc.php
ZABBIX_USERNAME=Admin
ZABBIX_PASSWORD=ваш_пароль
ZABBIX_SLA_NAME=Название_SLA_в_Zabbix

# База данных
DATABASE_URL=sqlite:///./sla_planner.db

# Авторизация
AUTH_MODE=mock

# Приложение
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
```

### Важные параметры:

| Параметр | Описание | Пример |
|----------|----------|--------|
| `ZABBIX_URL` | URL API Zabbix | `http://zabbix:8080/api_jsonrpc.php` |
| `ZABBIX_USERNAME` | Логин Zabbix | `Admin` |
| `ZABBIX_PASSWORD` | Пароль Zabbix | `zabbix` |
| `ZABBIX_SLA_NAME` | Имя SLA для исключений | `Production SLA` |
| `DATABASE_URL` | Строка подключения к БД | `sqlite:///./sla_planner.db` |

---

## 🔧 Настройка Zabbix

### Создание SLA-услуг

1. Откройте Zabbix веб-интерфейс
2. Перейдите: **Сервисы → Дерево сервисов**
3. Нажмите **«Создать сервис»**
4. Создайте иерархию услуг вашей ИС:
   ```
   IT Инфраструктура (корневая)
   ├── Почтовый сервер
   ├── CRM Система
   │   └── БД PostgreSQL
   ├── ERP Система
   │   ├── БД Oracle
   │   └── 1С Бухгалтерия
   └── Портал клиентов
       └── Веб-сервер Nginx
   ```

5. Для каждой услуги укажите:
   - **Имя** — название сервиса
   - **Алгоритм** — как рассчитывается статус (обычно "Все дочерние")
   - **Родитель** — родительская услуга (для иерархии)

### Создание SLA

1. Перейдите: **Сервисы → SLA**
2. Нажмите **«Создать SLA»**
3. Укажите:
   - **Имя** — должно совпадать с `ZABBIX_SLA_NAME` в `.env`
   - **Период** — месяц/квартал/год
   - **Целевой SLA** — например, 99.9%

---

## 🎯 Запуск и проверка

### Запуск сервера

```bash
cd ~/sla_planner
source venv/bin/activate
python main.py
```

Вы увидите:
```
==================================================
  SLA Planner — запуск
==================================================
  Database : sqlite:///./sla_planner.db
  Zabbix   : http://zabbix.corp.local:8080/api_jsonrpc.php
  SLA Name : Production SLA
  Auth     : mock
==================================================
✅ Database tables created
✅ Connected to Zabbix
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Открыть в браузере

```
http://localhost:8000
```

### Проверка работы

1. **Панель управления** — показывает статус подключения к Zabbix
2. **SLA-услуги из Zabbix** — интерактивный граф (должен загрузиться из Zabbix)
3. **Новая работа** — регистрация ПР (выпадающий список услуг из Zabbix)
4. **Список работ** — все зарегистрированные ПР
5. **Календарь** — визуальное представление
6. **SLA Отчёт** — данные из Zabbix + созданные исключения
7. **Настройки** — текущая конфигурация + проверка подключения

---

## 🐛 Решение проблем

### Проблема: «Zabbix не подключён»

**Причины:**
- Неверный URL в `.env`
- Zabbix недоступен из WSL
- Неверный логин/пароль

**Решение:**
```bash
# Проверьте доступность Zabbix из WSL:
curl http://zabbix.corp.local:8080/api_jsonrpc.php

# Проверьте .env:
cat .env | grep ZABBIX

# Перезапустите сервер:
python main.py
```

### Проблема: «В Zabbix нет созданных SLA-услуг»

**Решение:**
1. Откройте Zabbix веб-интерфейс
2. Создайте услуги: **Сервисы → Дерево сервисов → Создать сервис**
3. Обновите страницу портала

### Проблема: «Файл templates/index.html не найден»

**Решение:**
```bash
# Скопируйте фронтенд:
cp dist/index.html templates/index.html
cp -r dist/assets/* static/assets/
```

### Проблема: «npm run build не работает»

**Решение:**
```powershell
# В Windows PowerShell:
npm install
npm run build
```

### Проблема: CORS ошибки при разработке

**Решение:**
В `.env` установите:
```env
DEBUG=true
```

Это разрешит все CORS запросы.

### Проблема: Порт 8000 занят

**Решение:**
```bash
# Найдите процесс:
sudo lsof -i :8000

# Убейте процесс:
sudo kill -9 <PID>

# Или измените порт в .env:
APP_PORT=8001
```

---

## 🔄 Обновление проекта

### Обновление фронтенда

```powershell
# В Windows:
cd C:\path\to\project
npm run build

# Скопируйте dist/ в WSL
```

### Обновление бэкенда

```bash
# В WSL:
cd ~/sla_planner
source venv/bin/activate
pip install -r requirements.txt --upgrade
python main.py
```

---

## 🐳 Развертывание через Docker (альтернатива)

```bash
cd ~/sla_planner
docker-compose up -d
```

---

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи: `python main.py` (вывод в консоль)
2. Проверьте `.env` — все ли параметры заполнены
3. Убедитесь что Zabbix доступен из WSL
4. Проверьте что фронтенд скопирован в `templates/` и `static/`

---

## ✅ Чек-лист перед запуском

- [ ] Node.js установлен в Windows
- [ ] `npm run build` выполнен успешно
- [ ] Папка `dist/` скопирована в WSL
- [ ] Python 3.11+ установлен в WSL
- [ ] Файлы `sla_planner/` скопированы в WSL
- [ ] `.env` создан и заполнен
- [ ] Zabbix доступен из WSL
- [ ] SLA-услуги созданы в Zabbix
- [ ] SLA создан в Zabbix (имя совпадает с `ZABBIX_SLA_NAME`)
- [ ] `deploy.sh` выполнен или ручное развертывание
- [ ] Сервер запущен: `python main.py`
- [ ] Браузер открыт: `http://localhost:8000`

---

**Готово!** 🎉 Теперь портал показывает только реальные данные из Zabbix.
