# 🤖 Крипто-бот с ИИ-анализом

Telegram-бот для отслеживания криптовалют с ежедневными ИИ-отчетами и ценовыми алертами.

## 🚀 Возможности

- ✅ Управление списком избранных монет
- 📊 Получение детальных отчетов по монетам через ИИ
- 🔔 Ежедневная рассылка аналитики в 9:00 МСК
- 📈 Анализ трендов на основе исторических данных (последние 7 дней)
- 🎯 Ценовые алерты с автоматическими уведомлениями
- 🤖 Интеграция с OpenRouter API для генерации отчетов

## 📋 Требования

### Локальная разработка
- Python 3.10+
- SQLite (включен в Python)

### Docker (рекомендуется для продакшена)
- Docker 20.10+
- Docker Compose 2.0+

### API ключи
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))
- OpenRouter API ключ (получить на [openrouter.ai](https://openrouter.ai))
- CoinGecko API ключ (опционально, для бесплатного плана не требуется)

## ⚙️ Установка и запуск

### 🐳 Docker (рекомендуется)

Самый простой способ развернуть бота на VPS:

```bash
# 1. Клонировать репозиторий
git clone https://github.com/yourusername/coin_checker.git
cd coin_checker

# 2. Создать .env файл из примера
cp .env.example .env

# 3. Отредактировать .env файл с вашими ключами
nano .env

# 4. Запустить через Docker Compose
docker compose up -d

# 5. Проверить логи
docker compose logs -f
```

**Подробная инструкция по деплою на VPS:** [DEPLOY.md](DEPLOY.md)

### 💻 Локальная разработка

#### 1. Клонировать репозиторий

```bash
git clone https://github.com/yourusername/coin_checker.git
cd coin_checker
```

#### 2. Создать виртуальное окружение

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/MacOS:**
```bash
python -m venv .venv
source .venv/bin/activate
```

#### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

#### 4. Настроить переменные окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Заполните переменные в `.env`:

```env
TG_BOT_TOKEN=ваш_токен_телеграм_бота
BASE_URL=https://api.coingecko.com/api
API_KEY=ваш_api_ключ_coingecko
OPEN_ROUTER_API=ваш_ключ_openrouter
```

#### 5. Применить миграции базы данных

```bash
alembic upgrade head
```

#### 6. Запустить бота

```bash
python main.py
```

Бот запустится и будет готов к работе. В логах вы увидите:
```
Бот запущен и готов к работе!
Ежедневные отчёты будут отправляться в 9:00 МСК
Проверка ценовых алертов каждые 10 минут
```

## 📱 Команды бота

- `/start` - Начать работу с ботом
- `/fav` - Управление избранными монетами (добавить/удалить/посмотреть)
- `/alert <монета> <условие> <цена>` - Установить ценовой алерт (например: `/alert btc > 70000`)
- `/alert list` - Посмотреть активные алерты
- `/get_report` - Получить ИИ-отчет по избранным монетам
- `/help` - Справка по всем возможностям

## 🏗️ Структура проекта

```
coin_checker/
├── database/              # Модели БД и подключение
│   ├── __init__.py
│   ├── base.py
│   ├── engine.py
│   └── models.py
├── service/              # Бизнес-логика
│   ├── __init__.py
│   ├── ai_service.py                    # Интеграция с OpenRouter
│   ├── coingeko_service.py              # Работа с CoinGecko API
│   ├── report_service.py                # Управление снапшотами рынка
│   ├── user_service.py                  # Управление пользователями
│   └── user_favorite_coins_service.py   # Избранные монеты
├── tg_bot/               # Telegram bot handlers
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start_handler.py
│   │   ├── favorite_coin_handler.py
│   │   └── get_report.py
│   └── keyboards/
│       ├── __init__.py
│       └── favorite_keyboards.py
├── jobs/                 # Фоновые задачи
│   ├── __init__.py
│   └── daily_report_job.py
├── alembic/              # Миграции БД
├── .env                  # Переменные окружения
├── main.py              # Точка входа
└── requirements.txt     # Зависимости
```

## 🔧 Разработка

### Создание новой миграции

После изменения моделей в `database/models.py`:

```bash
alembic revision --autogenerate -m "Описание изменений"
alembic upgrade head
```

### Логирование

Логи выводятся в консоль с уровнем INFO. Для изменения уровня логирования отредактируйте `main.py`:

```python
logging.basicConfig(level=logging.DEBUG)  # Для более детальных логов
```

## 🐛 Устранение неполадок

### Ошибка: "TG_BOT_TOKEN не найден"
- Проверьте файл `.env` и убедитесь что токен указан корректно

### Ошибка при подключении к CoinGecko
- Проверьте BASE_URL в `.env`
- Убедитесь что API_KEY валиден (для бесплатного плана может не требоваться)

### Ошибка при генерации ИИ-отчетов
- Проверьте OPEN_ROUTER_API в `.env`
- Убедитесь что у вас есть кредиты на OpenRouter

## 📝 Лицензия

Проект создан в учебных целях.
