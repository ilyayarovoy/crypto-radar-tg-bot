import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from database import session_maker
from service.user_favorite_coins_service import UserFavoriteCoinsService
from service.report_service import ReporteService
from service.coingeko_service import CoinGekoService
from service.ai_service import AIService

from tg_bot.keyboards.favorite_keyboards import add_favorite_coins_keyboard


router = Router()

logger = logging.getLogger(__name__)

RECOMMENDED_COINS = ['bitcoin', 'ethereum', 'binancecoin', 'ripple', 'solana', 'tron', 'hyperliquid', 'dogecoin', 'near', 'sui']


@router.message(Command("get_report"))
async def get_report(message: Message):
    tg_id = message.from_user.id

    async with session_maker() as session:
        user_favorite_coins_service = UserFavoriteCoinsService(session)
        favorite_coins_user_list = await user_favorite_coins_service.get_favorite_coins_by_user(tg_id=tg_id)

    if not favorite_coins_user_list:
        await message.answer(
            "Гост мод — сначала добавь монеты в избранное:",
            reply_markup=add_favorite_coins_keyboard(recommended_coin_list=RECOMMENDED_COINS),
        )
        return

    await message.answer("Получаем отчёт от ИИ, секунду... ⏳")

    # Обновляем снапшот именно по монетам этого юзера (пишет новую запись в market_snapshots)
    try:
        await CoinGekoService.market_data_for_coin(coins_list=favorite_coins_user_list)
    except Exception:
        logger.exception("Не удалось обновить данные с CoinGecko для tg_id=%s", tg_id)
        await message.answer("Не получилось обновить рыночные данные, попробуй позже 🙏")
        return

    # Берём историю (до 7 последних снапшотов на монету), чтобы ИИ видел динамику
    async with session_maker() as session:
        report_service = ReporteService(session)
        snapshots = await report_service.get_market_snapshots(
            coin_list=favorite_coins_user_list, limit_per_coin=7
        )

    report_text = await AIService.generate_market_report(snapshots)
    await message.answer(report_text, parse_mode="Markdown")