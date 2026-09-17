import logging

from aiogram import Bot

from database import session_maker
from service.user_service import UserService
from service.user_favorite_coins_service import UserFavoriteCoinsService
from service.report_service import ReporteService
from service.coingeko_service import CoinGekoService
from service.ai_service import AIService

logger = logging.getLogger(__name__)


async def send_daily_reports(bot: Bot) -> None:
    async with session_maker() as session:
        fav_service = UserFavoriteCoinsService(session)
        all_coins = await fav_service.get_all_distinct_favorite_coins()

    if not all_coins:
        logger.info("Ни у кого нет избранных монет — рассылку пропускаем")
        return

    # 1. Обновляем снапшот рынка (пишет новую запись в market_snapshots на каждую монету)
    try:
        await CoinGekoService.market_data_for_coin(coins_list=all_coins)
    except Exception:
        logger.exception("Не удалось обновить снапшот рынка, отчёты сегодня не шлём")
        return

    # 2. Последние 7 снапшотов на монету — одним запросом на все монеты сразу
    async with session_maker() as session:
        report_service = ReporteService(session)
        snapshots = await report_service.get_market_snapshots(coin_list=all_coins, limit_per_coin=7)

    snapshots_by_coin: dict[str, list] = {}
    for snapshot in snapshots:
        snapshots_by_coin.setdefault(snapshot.coin_id, []).append(snapshot)

    # 3. Персональный отчёт на каждого юзера из уже готовых данных
    async with session_maker() as session:
        user_service = UserService(session)
        fav_service = UserFavoriteCoinsService(session)
        users = await user_service.get_all_users()

        for user in users:
            user_coins = await fav_service.get_favorite_coins_by_user(tg_id=user.tg_id)
            if not user_coins:
                continue

            user_snapshots = [
                snap for coin in user_coins for snap in snapshots_by_coin.get(coin, [])
            ]
            if not user_snapshots:
                continue

            try:
                report_text = await AIService.generate_market_report(user_snapshots)
                await bot.send_message(user.tg_id, report_text, parse_mode="Markdown")
            except Exception:
                logger.exception("Не удалось отправить отчёт юзеру tg_id=%s", user.tg_id)