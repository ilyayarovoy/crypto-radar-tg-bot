import logging
import re
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import session_maker
from service.alert_service import AlertService
from service.coingeko_service import CoinGekoService

router = Router()
logger = logging.getLogger(__name__)


def parse_alert_command(text: str) -> dict | None:
    # Убираем команду /alert
    text = text.replace('/alert', '').strip()

    if not text:
        return None

    # Регулярка: название монеты + оператор (>, <, >=, <=) + число
    pattern = r'^(\w+)\s*(>=|<=|>|<)\s*([\d.]+)$'
    match = re.match(pattern, text, re.IGNORECASE)

    if not match:
        return None

    coin_name = match.group(1).lower()
    condition = match.group(2)

    try:
        price = float(match.group(3))
    except ValueError:
        return None

    return {
        'coin_name': coin_name,
        'condition': condition,
        'price': price
    }


@router.message(Command('alert'))
async def alert_handler(message: Message):

    text = message.text or ""

    # Команда /alert list - показать все активные алерты
    if 'list' in text.lower():
        await show_user_alerts(message)
        return

    # Парсим параметры алерта
    parsed = parse_alert_command(text)

    if not parsed:
        await message.answer(
            "📢 **Ценовые алерты**\n\n"
            "Получай уведомления при достижении целевой цены!\n\n"
            "**Формат команды:**\n"
            "`/alert <монета> <условие> <цена>`\n\n"
            "**Примеры:**\n"
            "• `/alert btc > 70000` — уведомить, когда Bitcoin выше $70,000\n"
            "• `/alert eth < 3000` — уведомить, когда Ethereum ниже $3,000\n"
            "• `/alert sol >= 150` — уведомить, когда Solana >= $150\n\n"
            "**Управление алертами:**\n"
            "• `/alert list` — посмотреть все активные алерты\n\n"
            "⏱️ Проверка цен происходит каждые 10 минут"
        )
        return

    # Создаем алерт
    coin_name = parsed['coin_name']
    condition = parsed['condition']
    price = parsed['price']

    # Используем CoinGecko API для поиска реального coin_id
    try:
        coin_ids = await CoinGekoService.get_coin_id_from_name([coin_name])

        if not coin_ids or len(coin_ids) == 0:
            await message.answer(
                f"❌ Монета `{coin_name}` не найдена в CoinGecko\n\n"
                f"Попробуй ввести полное название или популярный тикер, например:\n"
                f"• bitcoin или btc\n"
                f"• ethereum или eth\n"
                f"• solana или sol"
            )
            return

        coin_id = coin_ids[0]

    except Exception as e:
        logger.error(f"Ошибка при поиске монеты {coin_name}: {e}")
        await message.answer(
            f"❌ Не удалось найти монету `{coin_name}`\n\n"
            f"Проверь правильность названия и попробуй ещё раз"
        )
        return

    async with session_maker() as session:
        alert_service = AlertService(session)
        alert = await alert_service.create_alert(
            tg_id=message.from_user.id,
            coin_id=coin_id,
            condition=condition,
            target_price=price
        )

    if alert:
        await message.answer(
            f"✅ **Алерт создан!**\n\n"
            f"🪙 Монета: {coin_name.upper()} ({coin_id})\n"
            f"📊 Условие: цена {condition} ${price:,.2f}\n"
            f"🔔 Ты получишь уведомление, когда условие выполнится\n\n"
            f"ID алерта: `#{alert.id}`\n"
            f"Проверка цен каждые 10 минут ⏱️\n\n"
            f"Посмотреть все алерты: /alert list"
        )
        logger.info(f"User {message.from_user.id} created alert: {coin_name} ({coin_id}) {condition} {price}")
    else:
        await message.answer("❌ Ошибка при создании алерта. Попробуй позже.")


async def show_user_alerts(message: Message):
    async with session_maker() as session:
        alert_service = AlertService(session)
        alerts = await alert_service.get_user_active_alerts(tg_id=message.from_user.id)

    if not alerts:
        await message.answer(
            "📭 У тебя пока нет активных алертов\n\n"
            "Создай новый алерт командой:\n"
            "`/alert btc > 70000`"
        )
        return

    # Формируем список алертов с кнопками удаления
    text = f"🔔 **Твои активные алерты** ({len(alerts)}):\n\n"

    builder = InlineKeyboardBuilder()

    for alert in alerts:
        ticker = alert.coin_id.upper()
        condition = alert.condition
        price = alert.target_price
        alert_id = alert.id

        text += f"#{alert_id}: {ticker} {condition} ${price:,.2f}\n"
        builder.button(text=f"🗑 Удалить #{alert_id}", callback_data=f"delete_alert_{alert_id}")

    builder.adjust(1)  # По одной кнопке в ряд

    text += "\n💡 Нажми на кнопку, чтобы удалить алерт"

    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith('delete_alert_'))
async def delete_alert_callback(callback: CallbackQuery):
    """Обработчик удаления алерта по кнопке"""
    alert_id = int(callback.data.split('_')[-1])

    async with session_maker() as session:
        alert_service = AlertService(session)
        deleted = await alert_service.delete_alert(
            alert_id=alert_id,
            tg_id=callback.from_user.id
        )

    if deleted:
        await callback.answer(f"✅ Алерт #{alert_id} удален", show_alert=True)

        # Обновляем список алертов
        async with session_maker() as session:
            alert_service = AlertService(session)
            alerts = await alert_service.get_user_active_alerts(tg_id=callback.from_user.id)

        if not alerts:
            await callback.message.edit_text(
                "📭 У тебя больше нет активных алертов\n\n"
                "Создай новый алерт командой:\n"
                "`/alert btc > 70000`"
            )
        else:
            # Перестраиваем список
            text = f"🔔 **Твои активные алерты** ({len(alerts)}):\n\n"
            builder = InlineKeyboardBuilder()

            for alert in alerts:
                ticker = alert.coin_id.upper()
                condition = alert.condition
                price = alert.target_price
                aid = alert.id

                text += f"#{aid}: {ticker} {condition} ${price:,.2f}\n"
                builder.button(text=f"🗑 Удалить #{aid}", callback_data=f"delete_alert_{aid}")

            builder.adjust(1)
            text += "\n💡 Нажми на кнопку, чтобы удалить алерт"

            await callback.message.edit_text(text, reply_markup=builder.as_markup())
    else:
        await callback.answer("❌ Не удалось удалить алерт", show_alert=True)
