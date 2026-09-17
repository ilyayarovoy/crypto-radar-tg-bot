import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command('help'))
async def help_handler(message: Message):


    help_text = (
        "🤖 **Справка по командам бота**\n\n"
        "**Основные команды:**\n\n"
        "🏠 `/start` — Начать работу с ботом\n"
        "Запустить бота и зарегистрироваться в системе\n\n"

        "⭐ `/fav` — Управление избранными монетами\n"
        "Добавляй, удаляй и просматривай свой список отслеживаемых криптовалют\n\n"

        "🔔 `/alert` — Установить ценовое уведомление\n"
        "Получай уведомления при достижении целевой цены\n"
        "Примеры:\n"
        "  • `/alert btc > 70000`\n"
        "  • `/alert eth < 3000`\n"
        "  • `/alert sol > 150`\n"
        "_(в разработке)_\n\n"

        "📊 `/get_report` — Получить отчет по избранным монетам\n"
        "Запросить аналитический отчет с ИИ-анализом по твоим монетам\n\n"

        "❓ `/help` — Показать эту справку\n\n"

        "**Автоматические функции:**\n\n"
        "📬 **Ежедневные отчеты** — каждый день в 9:00 МСК\n"
        "Бот автоматически собирает данные по твоим избранным монетам и отправляет "
        "аналитический отчет с использованием ИИ\n\n"

        "💡 **Подсказка:**\n"
        "Начни с команды `/fav`, чтобы добавить монеты для отслеживания!"
    )

    await message.answer(help_text)
    logger.info(f"Help command used by user {message.from_user.id}")
