# 🚀 Деплой на VPS через Docker

Инструкция по развертыванию Crypto Bot на VPS с использованием Docker.

## 📋 Требования

- VPS с Ubuntu 20.04+ / Debian 11+
- Docker 20.10+
- Docker Compose 2.0+
- Минимум 512 MB RAM
- 1 GB свободного места на диске

## 🔧 Подготовка VPS

### 1. Установка Docker

```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавляем текущего пользователя в группу docker
sudo usermod -aG docker $USER

# Перелогиниваемся для применения изменений
newgrp docker

# Проверяем установку
docker --version
docker compose version
```

### 2. Клонирование проекта

```bash
# Переходим в домашнюю директорию
cd ~

# Клонируем репозиторий (замените URL на ваш)
git clone https://github.com/yourusername/coin_checker.git
cd coin_checker
```

## ⚙️ Настройка

### 1. Создание .env файла

```bash
# Копируем пример конфигурации
cp .env.example .env

# Редактируем файл с вашими ключами
nano .env
```

Заполните следующие переменные:

```env
# Telegram Bot Token (получить у @BotFather)
TG_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# CoinGecko API
BASE_URL=https://api.coingecko.com/api
API_KEY=your_coingecko_api_key

# OpenRouter API (получить на openrouter.ai)
OPEN_ROUTER_API=sk-or-v1-your-key-here
```

### 2. Создание директории для базы данных

```bash
# Создаем директорию для персистентных данных
mkdir -p data
```

## 🚀 Запуск

### Первый запуск

```bash
# Собираем и запускаем контейнер
docker compose up -d

# Проверяем логи
docker compose logs -f
```

Вы должны увидеть:
```
Бот запущен и готов к работе!
Ежедневные отчёты будут отправляться в 9:00 МСК
Проверка ценовых алертов каждые 10 минут
```

### Управление контейнером

```bash
# Остановить бота
docker compose down

# Перезапустить бота
docker compose restart

# Посмотреть логи
docker compose logs -f

# Посмотреть статус
docker compose ps

# Пересобрать и запустить (после изменений кода)
docker compose up -d --build
```

## 🔄 Обновление бота

```bash
# Останавливаем контейнер
docker compose down

# Получаем обновления
git pull

# Пересобираем и запускаем
docker compose up -d --build

# Проверяем логи
docker compose logs -f
```

## 🗄️ Работа с базой данных

### Создание миграций

```bash
# Войти в контейнер
docker compose exec crypto_bot bash

# Создать миграцию
alembic revision --autogenerate -m "Description"

# Применить миграцию
alembic upgrade head

# Выйти из контейнера
exit
```

### Бэкап базы данных

```bash
# Создать бэкап
docker compose exec crypto_bot cp /app/database.db /app/data/backup_$(date +%Y%m%d_%H%M%S).db

# Или скопировать на хост
docker compose cp crypto_bot:/app/database.db ./backup_$(date +%Y%m%d_%H%M%S).db
```

### Восстановление из бэкапа

```bash
# Остановить бота
docker compose down

# Восстановить базу
cp backup_YYYYMMDD_HHMMSS.db database.db

# Запустить бота
docker compose up -d
```

## 🔍 Мониторинг

### Просмотр логов в реальном времени

```bash
# Все логи
docker compose logs -f

# Последние 100 строк
docker compose logs --tail=100

# Логи за последний час
docker compose logs --since 1h
```

### Проверка ресурсов

```bash
# Использование ресурсов контейнером
docker stats crypto_bot

# Размер контейнера
docker compose ps --size
```

## 🛠️ Устранение неполадок

### Бот не запускается

```bash
# Проверяем логи
docker compose logs

# Проверяем, что .env файл существует и заполнен
cat .env

# Проверяем статус контейнера
docker compose ps
```

### Ошибки миграций

```bash
# Войти в контейнер
docker compose exec crypto_bot bash

# Проверить текущую версию БД
alembic current

# Применить миграции вручную
alembic upgrade head
```

### Очистка Docker

```bash
# Удалить остановленные контейнеры
docker container prune

# Удалить неиспользуемые образы
docker image prune

# Полная очистка (осторожно!)
docker system prune -a
```

## 🔒 Безопасность

### Рекомендации

1. **Никогда не коммитьте .env файл в git**
2. **Используйте сильные токены и ключи**
3. **Регулярно обновляйте систему**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

4. **Настройте firewall**:
   ```bash
   sudo ufw allow 22/tcp  # SSH
   sudo ufw enable
   ```

5. **Настройте автоматические бэкапы** (cron):
   ```bash
   crontab -e
   # Добавьте строку для ежедневного бэкапа в 3:00
   0 3 * * * cd ~/coin_checker && docker compose exec crypto_bot cp /app/database.db /app/data/backup_$(date +\%Y\%m\%d).db
   ```

## 📊 Автозапуск при перезагрузке

Docker Compose автоматически настроен на перезапуск контейнера (`restart: unless-stopped`).

Проверка:
```bash
# Перезагрузите VPS
sudo reboot

# После перезагрузки проверьте статус
docker compose ps
```

## 🆘 Поддержка

При проблемах:
1. Проверьте логи: `docker compose logs -f`
2. Проверьте статус: `docker compose ps`
3. Проверьте конфигурацию: `cat .env`

## 📝 Полезные команды

```bash
# Быстрый рестарт
docker compose restart

# Обновление с пересборкой
git pull && docker compose up -d --build

# Просмотр последних 50 строк логов
docker compose logs --tail=50

# Войти в shell контейнера
docker compose exec crypto_bot bash

# Проверить версию Python в контейнере
docker compose exec crypto_bot python --version
```
