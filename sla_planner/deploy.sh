#!/bin/bash
# --- ФАЙЛ: sla_planner/deploy.sh ---
# Скрипт автоматического развертывания SLA Planner в WSL

set -e  # Остановка при ошибке

echo "🚀 Начало развертывания SLA Planner..."
echo ""

# 1. Проверка Python
echo "📋 Проверка Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен!"
    echo "Установите: sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $PYTHON_VERSION"

# 2. Создание виртуального окружения
echo ""
echo "📦 Создание виртуального окружения..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Виртуальное окружение создано"
else
    echo "✅ Виртуальное окружение уже существует"
fi

# Активация
source venv/bin/activate

# 3. Установка зависимостей
echo ""
echo "📥 Установка зависимостей..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "✅ Зависимости установлены"

# 4. Копирование фронтенда
echo ""
echo "🎨 Копирование фронтенда..."
mkdir -p static templates

if [ -d "dist" ]; then
    # Копируем assets в static
    if [ -d "dist/assets" ]; then
        mkdir -p static/assets
        cp -r dist/assets/* static/assets/ 2>/dev/null || true
    fi
    
    # Копируем index.html в templates
    if [ -f "dist/index.html" ]; then
        cp dist/index.html templates/index.html
        echo "✅ Фронтенд скопирован"
    else
        echo "⚠️  dist/index.html не найден"
    fi
else
    echo "⚠️  Папка dist/ не найдена."
    echo "   Сначала выполните 'npm run build' в Windows и скопируйте dist/ сюда"
fi

# 5. Создание .env если нет
echo ""
echo "⚙️  Проверка конфигурации..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Создан .env из .env.example"
        echo "⚠️  ВАЖНО: Отредактируйте .env и укажите параметры Zabbix!"
        echo "   nano .env"
    else
        echo "⚠️  .env.example не найден. Создайте .env вручную"
    fi
else
    echo "✅ .env уже существует"
fi

# 6. Создание папок для БД
echo ""
echo "🗄️  Подготовка базы данных..."
if [[ "$DATABASE_URL" == sqlite* ]] || grep -q "sqlite" .env 2>/dev/null; then
    echo "✅ SQLite база данных будет создана автоматически"
fi

# 7. Проверка структуры
echo ""
echo "🔍 Проверка структуры проекта..."
MISSING_FILES=()
[ ! -f "main.py" ] && MISSING_FILES+=("main.py")
[ ! -f "config.py" ] && MISSING_FILES+=("config.py")
[ ! -f "database.py" ] && MISSING_FILES+=("database.py")
[ ! -f "models.py" ] && MISSING_FILES+=("models.py")
[ ! -f "zabbix_client.py" ] && MISSING_FILES+=("zabbix_client.py")
[ ! -f "auth.py" ] && MISSING_FILES+=("auth.py")
[ ! -d "routers" ] && MISSING_FILES+=("routers/")

if [ ${#MISSING_FILES[@]} -ne 0 ]; then
    echo "❌ Отсутствуют файлы: ${MISSING_FILES[*]}"
    echo "   Убедитесь что все файлы скопированы из Windows"
    exit 1
fi

echo "✅ Структура проекта корректна"

# 8. Готово
echo ""
echo "═══════════════════════════════════════════════════"
echo "✅ Развертывание завершено успешно!"
echo "═══════════════════════════════════════════════════"
echo ""
echo "📌 Следующие шаги:"
echo "   1. Отредактируйте .env: nano .env"
echo "   2. Запустите сервер: python main.py"
echo "   3. Откройте: http://localhost:8000"
echo ""
echo "🔧 Если Zabbix не подключается:"
echo "   - Проверьте URL в .env"
echo "   - Убедитесь что Zabbix доступен из WSL"
echo "   - Проверьте логин/пароль"
echo ""
echo "🚀 Запуск..."
echo ""

# Запуск сервера
python main.py
