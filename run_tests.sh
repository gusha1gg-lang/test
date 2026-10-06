#!/bin/bash
# Скрипт для запуска интеграционных тестов SLA Planner

set -e

echo "🚀 Запуск интеграционных тестов SLA Planner..."
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker не установлен. Установите Docker и попробуйте снова.${NC}"
    exit 1
fi

# Проверка Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose не установлен. Установите Docker Compose и попробуйте снова.${NC}"
    exit 1
fi

# Функция очистки
cleanup() {
    echo ""
    echo -e "${YELLOW}🧹 Остановка и удаление контейнеров...${NC}"
    docker-compose -f docker-compose.test.yml down -v
    echo -e "${GREEN}✅ Очистка завершена${NC}"
}

# Регистрация cleanup при выходе
trap cleanup EXIT

# Запуск тестов
echo -e "${YELLOW}📦 Запуск Docker Compose с тестами...${NC}"
docker-compose -f docker-compose.test.yml up --build

# Проверка результата
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Все тесты пройдены успешно!${NC}"
    echo ""
    echo "📊 Результаты тестов:"
    echo "   - HTML отчёт: test-results/report.html"
    echo "   - Покрытие кода: test-results/coverage/"
    echo ""
    echo "📋 Просмотр результатов:"
    echo "   docker-compose -f docker-compose.test.yml logs test-app"
    echo ""
    exit 0
else
    echo ""
    echo -e "${RED}❌ Некоторые тесты не пройдены${NC}"
    echo ""
    echo "🔍 Просмотр логов:"
    echo "   docker-compose -f docker-compose.test.yml logs test-app"
    echo ""
    exit 1
fi
