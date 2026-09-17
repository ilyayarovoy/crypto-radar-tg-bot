#!/bin/bash
set -e

echo "Starting Crypto Bot..."
echo "Applying database migrations..."

# Применяем миграции
alembic upgrade head

echo "Migrations applied successfully!"
echo "Starting bot application..."

# Запускаем бота
exec python main.py
