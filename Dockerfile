# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем директорию для базы данных
RUN mkdir -p /app/data

# Применяем миграции при старте (через entrypoint скрипт)
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Порт не нужен, т.к. это Telegram бот, но можем оставить для будущего
EXPOSE 8000

# Запускаем через entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]
