import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart


from database import session_maker
from service.user_service import UserService


router = Router()

logger = logging.getLogger(__name__)

@router.message(CommandStart())
async def start_handler(message: Message):
    user = message.from_user
    tg_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name

    start_text = (
        f"👋 **Привет, {first_name or 'криптоэнтузиаст'}!**\n\n"
        "Я — твой персональный **Крипто-бот**. 🤖📊\n\n"
        "⚙️ **Основные команды:**\n"
        "• `/start` — Начать работу с ботом\n"
        "• `/fav` — Управление избранными монетами\n"
        "• `/alert` — Установить ценовой алерт (например: `/alert btc > 70000`)\n"
        "• `/help` — Справка по всем возможностям\n\n"
        "🌟 **Что я умею:**\n"
        "1️⃣ Собирать данные по твоим монетам каждый день в 9:00 МСК\n"
        "2️⃣ Передавать историю в ИИ и присылать умный утренний отчет-аналитику\n"
        "3️⃣ Следить за ценами и присылать алерт при достижении цели _(скоро)_\n\n"
        "💡 Начни с команды `/fav`, чтобы добавить монеты для отслеживания!"
    )


    async with session_maker() as session:
        user_service = UserService(session)
        try:
            user = await user_service.get_user_by_tg_id(tg_id=tg_id)
            if user is None:
                await user_service.create_user(
                tg_id=tg_id,
                username=username,
                first_name=first_name,
                last_name=last_name
                )
                await message.answer(start_text)

            await message.answer(start_text)
        except Exception as e:
            logger.info(f"Ошибка {e}")



