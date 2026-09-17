import logging
import aiohttp
import os
from aiogram import Bot

from database import session_maker
from service.alert_service import AlertService

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")


async def check_price_alerts(bot: Bot) -> None:
    """
    Фоновая задача для проверки ценовых алертов.
    Вызывается каждые 10 минут через APScheduler.

    Алгоритм:
    1. Получить все активные алерты из БД
    2. Собрать уникальные coin_id для оптимизации запросов
    3. Сделать один пакетный запрос на CoinGecko API для всех монет
    4. Проверить условия для каждого алерта
    5. Отправить уведомления пользователям, у которых сработали алерты
    6. Деактивировать сработавшие алерты
    """

    async with session_maker() as session:
        alert_service = AlertService(session)

        # Получаем все активные алерты
        active_alerts = await alert_service.get_all_active_alerts()

        if not active_alerts:
            logger.info("Нет активных алертов для проверки")
            return

        # Собираем уникальные coin_id для пакетного запроса
        unique_coin_ids = await alert_service.get_unique_coin_ids()

        if not unique_coin_ids:
            return

        logger.info(f"Проверка {len(active_alerts)} алертов для {len(unique_coin_ids)} монет")

        # Запрашиваем текущие цены для всех монет одним запросом
        try:
            current_prices = await fetch_current_prices(unique_coin_ids)
        except Exception as e:
            logger.error(f"Ошибка при получении цен с CoinGecko: {e}")
            return

        # Проверяем каждый алерт
        triggered_alerts = []

        for alert in active_alerts:
            coin_id = alert.coin_id
            current_price = current_prices.get(coin_id)

            if current_price is None:
                logger.warning(f"Цена для {coin_id} не найдена, пропускаем алерт #{alert.id}")
                continue

            # Проверяем условие
            condition_met = check_condition(
                current_price=current_price,
                condition=alert.condition,
                target_price=alert.target_price
            )

            if condition_met:
                triggered_alerts.append({
                    'alert': alert,
                    'current_price': current_price
                })

        # Отправляем уведомления и деактивируем алерты
        for item in triggered_alerts:
            alert = item['alert']
            current_price = item['current_price']

            try:
                # Отправляем уведомление пользователю
                await send_alert_notification(
                    bot=bot,
                    user_id=alert.user_id,
                    coin_id=alert.coin_id,
                    condition=alert.condition,
                    target_price=alert.target_price,
                    current_price=current_price
                )

                # Деактивируем алерт
                await alert_service.deactivate_alert(alert.id)

                logger.info(f"Алерт #{alert.id} сработал: {alert.coin_id} {alert.condition} ${alert.target_price}")

            except Exception as e:
                logger.error(f"Ошибка при обработке алерта #{alert.id}: {e}")

        if triggered_alerts:
            logger.info(f"Сработало {len(triggered_alerts)} алертов")
        else:
            logger.info("Ни один алерт не сработал")


async def fetch_current_prices(coin_ids: list[str]) -> dict[str, float]:
    """
    Получить текущие цены для списка монет через CoinGecko API.
    Возвращает словарь {coin_id: price}
    """
    headers = {"X-CMC_PRO_API_KEY": API_KEY}

    # CoinGecko позволяет запросить до 250 монет за раз
    coin_ids_str = ",".join(coin_ids[:250])

    url = f"{BASE_URL}/v3/coins/markets?vs_currency=usd&ids={coin_ids_str}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"CoinGecko API error: {response.status}")

            data = await response.json()

            # Формируем словарь {coin_id: current_price}
            prices = {}
            for coin in data:
                coin_id = coin.get('id')
                current_price = coin.get('current_price')

                if coin_id and current_price is not None:
                    prices[coin_id] = float(current_price)

            return prices


def check_condition(current_price: float, condition: str, target_price: float) -> bool:
    """
    Проверить выполнение условия алерта.
    """
    if condition == '>':
        return current_price > target_price
    elif condition == '<':
        return current_price < target_price
    elif condition == '>=':
        return current_price >= target_price
    elif condition == '<=':
        return current_price <= target_price
    else:
        logger.warning(f"Неизвестное условие: {condition}")
        return False


async def send_alert_notification(
    bot: Bot,
    user_id: int,
    coin_id: str,
    condition: str,
    target_price: float,
    current_price: float
) -> None:
    """
    Отправить уведомление пользователю о срабатывании алерта.
    """
    from service.user_service import UserService

    # Получаем tg_id пользователя по user_id
    async with session_maker() as session:
        user_service = UserService(session)
        # Нужно найти пользователя по внутреннему user_id
        # Для этого модифицируем запрос
        from sqlalchemy import select
        from database.models import UserModel

        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            logger.error(f"Пользователь с id={user_id} не найден")
            return

        tg_id = user.tg_id

    # Формируем сообщение
    price_change = ((current_price - target_price) / target_price) * 100

    message = (
        f"🔔 **АЛЕРТ СРАБОТАЛ!**\n\n"
        f"🪙 Монета: {coin_id.upper()}\n"
        f"📊 Условие: цена {condition} ${target_price:,.2f}\n"
        f"💰 Текущая цена: ${current_price:,.2f}\n"
        f"📈 Изменение: {price_change:+.2f}%\n\n"
        f"⏰ Алерт деактивирован автоматически.\n"
        f"Создай новый алерт: `/alert {coin_id} {condition} {target_price}`"
    )

    try:
        await bot.send_message(tg_id, message, parse_mode="Markdown")
        logger.info(f"Уведомление об алерте отправлено пользователю tg_id={tg_id}")
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление пользователю tg_id={tg_id}: {e}")
