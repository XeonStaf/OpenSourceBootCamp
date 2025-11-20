#!/bin/bash

# Скрипт для запуска backend локально (вне Docker)

set -e

echo "🚀 Запуск backend локально..."

# Проверка наличия .env файла
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден!"
    echo "📝 Создайте файл .env в директории backend/ со следующими переменными:"
    echo "   LLM_NAME=..."
    echo "   LLM_HOST=..."
    echo "   API_KEY=..."
    echo "   TAVILY_API_KEY=..."
    echo "   TAVILY_MAX_RESULTS=..."
    exit 1
fi

# Проверка наличия poetry
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry не установлен!"
    echo "📦 Установите Poetry: https://python-poetry.org/docs/#installation"
    exit 1
fi

# Проверка виртуального окружения
if [ ! -d ".venv" ]; then
    echo "📦 Создание виртуального окружения..."
    poetry install
fi

# Активация окружения и запуск
echo "✅ Запуск приложения на http://localhost:8000"
echo "📊 Логи будут отображаться в консоли"
echo ""

poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

