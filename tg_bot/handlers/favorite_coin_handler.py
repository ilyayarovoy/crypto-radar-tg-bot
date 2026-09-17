import logging
from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from database import session_maker

from tg_bot.keyboards.favorite_keyboards import (
    all_favorites_coins_keyboard,
    add_favorite_coins_keyboard,
    delete_favorite_coins_keyboard,
)
from service.user_favorite_coins_service import UserFavoriteCoinsService
from service.coingeko_service import CoinGekoService
import aiohttp
import os

router = Router()
logger = logging.getLogger(__name__)

BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")

RECOMMENDED_COINS = ['bitcoin', 'ethereum', 'binancecoin', 'ripple', 'solana', 'tron', 'hyperliquid', 'dogecoin', 'near', 'sui']

FAV_PAGE_SIZE = 3


class FavoriteCoinsStates(StatesGroup):
    entering_custom_coin = State()


# вспомогательные функции ----------

async def _get_user_favorites(tg_id: int) -> list[str]:
    async with session_maker() as session:
        service = UserFavoriteCoinsService(session)
        return await service.get_favorite_coins_by_user(tg_id=tg_id)


async def _fetch_coin_prices(coin_ids: list[str]) -> dict[str, float]:
    """
    Получить текущие цены для списка монет.
    Возвращает словарь {coin_id: price}
    """
    if not coin_ids:
        return {}

    headers = {"X-CMC_PRO_API_KEY": API_KEY}
    coin_ids_str = ",".join(coin_ids[:250])
    url = f"{BASE_URL}/v3/coins/markets?vs_currency=usd&ids={coin_ids_str}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Ошибка CoinGecko API: {response.status}")
                    return {}

                data = await response.json()

                prices = {}
                for coin in data:
                    coin_id = coin.get('id')
                    current_price = coin.get('current_price')
                    price_change_24h = coin.get('price_change_percentage_24h')

                    if coin_id and current_price is not None:
                        prices[coin_id] = {
                            'price': float(current_price),
                            'change_24h': float(price_change_24h) if price_change_24h else 0.0
                        }

                return prices
    except Exception as e:
        logger.error(f"Ошибка при получении цен: {e}")
        return {}


async def _show_favorites(target, tg_id: int, state: FSMContext, page: int = 0, edit: bool = False) -> None:
    await state.clear()
    favorites = await _get_user_favorites(tg_id)

    if favorites:
        # Получаем текущие цены для всех избранных монет
        prices = await _fetch_coin_prices(favorites)

        text = f'⭐ **Твои избранные монеты** (Страница {page + 1}):\n\n'

        for coin in favorites:
            coin_upper = coin.upper()
            price_data = prices.get(coin)

            if price_data:
                price = price_data['price']
                change_24h = price_data['change_24h']

                # Эмодзи для изменения цены
                if change_24h > 0:
                    change_emoji = "📈"
                    change_sign = "+"
                elif change_24h < 0:
                    change_emoji = "📉"
                    change_sign = ""
                else:
                    change_emoji = "➡️"
                    change_sign = ""

                text += f"🪙 **{coin_upper}**: ${price:,.2f} {change_emoji} {change_sign}{change_24h:.2f}%\n"
            else:
                # Если цену не удалось получить
                text += f"🪙 **{coin_upper}**: _цена недоступна_\n"

        keyboard = all_favorites_coins_keyboard(
            user_favorites_coins=favorites, page=page, per_page=FAV_PAGE_SIZE
        )
    else:
        text = "У тебя пока нет избранных монет\nВыбери из рекомендаций:"
        keyboard = add_favorite_coins_keyboard(recommended_coin_list=RECOMMENDED_COINS, selected_coins=set())
        await state.update_data(available_coins=RECOMMENDED_COINS, selected_coins=[])

    if edit:
        await target.message.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)
    else:
        await target.answer(text, parse_mode='Markdown', reply_markup=keyboard)


# ---------- команда /fav ----------

@router.message(Command('fav'))
async def favorite_coin_handler(message: Message, state: FSMContext):
    await _show_favorites(message, tg_id=message.from_user.id, state=state)


@router.callback_query(F.data.startswith('fav_page_'))
async def fav_pagination_handler(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split('_')[-1])
    await _show_favorites(callback, tg_id=callback.from_user.id, state=state, page=page, edit=True)
    await callback.answer()


@router.callback_query(F.data == 'ignore')
async def ignore_handler(callback: CallbackQuery):
    # Клик по индикатору страницы "📄 1/2" — ничего не делаем, просто убираем "часики"
    await callback.answer()


@router.callback_query(F.data == 'fav_back')
async def fav_back_handler(callback: CallbackQuery, state: FSMContext):
    await _show_favorites(callback, tg_id=callback.from_user.id, state=state, edit=True)
    await callback.answer()


# ---------- добавление монет ----------

@router.callback_query(F.data == 'fav_add_prompt')
async def fav_add_prompt_handler(callback: CallbackQuery, state: FSMContext):
    favorites = set(await _get_user_favorites(callback.from_user.id))
    # Не предлагаем то, что уже в избранном
    available = [c for c in RECOMMENDED_COINS if c not in favorites]

    await state.update_data(available_coins=available, selected_coins=[])

    if available:
        text = "Выбери монеты из списка (можно несколько) или введи тикер вручную:"
    else:
        text = "Все рекомендованные монеты уже у тебя в избранном.\nВведи тикер вручную:"

    keyboard = add_favorite_coins_keyboard(
        recommended_coin_list=available, selected_coins=set(), show_back=True
    )
    await callback.message.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith('toggle_coin_'))
async def toggle_coin_handler(callback: CallbackQuery, state: FSMContext):
    coin = callback.data.removeprefix('toggle_coin_')

    data = await state.get_data()
    available = data.get('available_coins', RECOMMENDED_COINS)
    selected = set(data.get('selected_coins', []))

    if coin in selected:
        selected.remove(coin)
    else:
        selected.add(coin)

    await state.update_data(selected_coins=list(selected))

    keyboard = add_favorite_coins_keyboard(
        recommended_coin_list=available,
        selected_coins=selected,
        show_back=True,
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except Exception:
        # Telegram кидает ошибку, если разметка не изменилась (повторный клик подряд)
        pass
    await callback.answer()


@router.callback_query(F.data.startswith('rec_page_'))
async def rec_pagination_handler(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split('_')[-1])
    data = await state.get_data()
    available = data.get('available_coins', RECOMMENDED_COINS)
    selected = set(data.get('selected_coins', []))

    keyboard = add_favorite_coins_keyboard(
        recommended_coin_list=available, selected_coins=selected, page=page, show_back=True
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == 'fav_confirm_add')
async def fav_confirm_add_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get('selected_coins', [])

    if not selected:
        await callback.answer("Сначала выбери хотя бы одну монету ☝️", show_alert=True)
        return

    tg_id = callback.from_user.id
    async with session_maker() as session:
        service = UserFavoriteCoinsService(session)
        for coin in selected:
            await service.add_favorite_coin(tg_id=tg_id, coin=coin)

    await callback.answer(f"Добавлено: {', '.join(selected)}")
    await _show_favorites(callback, tg_id=tg_id, state=state, edit=True)


@router.callback_query(F.data == 'fav_add_custom')
async def fav_add_custom_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FavoriteCoinsStates.entering_custom_coin)
    await callback.message.edit_text(
        "Напиши тикер монеты, которую хочешь добавить (например: BTC).\n"
        "Можно указать сразу несколько через запятую или пробел."
    )
    await callback.answer()


@router.message(StateFilter(FavoriteCoinsStates.entering_custom_coin))
async def custom_coin_entered_handler(message: Message, state: FSMContext):
    raw = message.text or ""
    # Разбиваем по запятым/пробелам и приводим к нижнему регистру
    coins_input = [c.strip().lower() for c in raw.replace(',', ' ').split() if c.strip()]

    # Простая валидация тикера: только буквы/цифры и разумная длина
    valid_input = [c for c in coins_input if c.isalnum() and 1 <= len(c) <= 10]

    if not valid_input:
        await message.answer(
            "Не удалось распознать тикер. Введи ещё раз, например: BTC или BTC, ETH"
        )
        return

    # Преобразуем введенные названия в правильные coin_id через CoinGecko API
    try:
        coin_ids = await CoinGekoService.get_coin_id_from_name(valid_input)
    except Exception as e:
        logger.error(f"Ошибка при поиске монет: {e}")
        await message.answer(
            "❌ Ошибка при поиске монет в CoinGecko. Попробуй позже."
        )
        return

    # Разделяем найденные и не найденные монеты
    found_coins = coin_ids
    not_found = [coin for i, coin in enumerate(valid_input) if i >= len(coin_ids)]

    if not found_coins:
        await message.answer(
            f"❌ Монеты не найдены: {', '.join(valid_input)}\n\n"
            f"Попробуй ввести полное название или популярный тикер, например:\n"
            f"• bitcoin или btc\n"
            f"• ethereum или eth\n"
            f"• ripple или xrp"
        )
        return

    # Добавляем найденные coin_id в избранное
    tg_id = message.from_user.id
    async with session_maker() as session:
        service = UserFavoriteCoinsService(session)
        for coin_id in found_coins:
            await service.add_favorite_coin(tg_id=tg_id, coin=coin_id)

    reply = f"✅ Добавлено: {', '.join([c.upper() for c in found_coins])}"
    if not_found:
        reply += f"\n⚠️ Не найдено: {', '.join(not_found)}"
    await message.answer(reply)

    await _show_favorites(message, tg_id=tg_id, state=state)


# ---------- удаление монет ----------

@router.callback_query(F.data == 'fav_delete_prompt')
async def fav_delete_prompt_handler(callback: CallbackQuery, state: FSMContext):
    favorites = await _get_user_favorites(callback.from_user.id)

    if not favorites:
        await callback.answer("У тебя нет монет для удаления", show_alert=True)
        return

    await state.update_data(favorite_coins=favorites, selected_delete_coins=[])

    text = "Выбери монеты, которые хочешь удалить из избранного:"
    keyboard = delete_favorite_coins_keyboard(user_favorite_coins=favorites, selected_coins=set())
    await callback.message.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith('toggle_delete_coin_'))
async def toggle_delete_coin_handler(callback: CallbackQuery, state: FSMContext):
    coin = callback.data.removeprefix('toggle_delete_coin_')

    data = await state.get_data()
    favorites = data.get('favorite_coins', [])
    selected = set(data.get('selected_delete_coins', []))

    if coin in selected:
        selected.remove(coin)
    else:
        selected.add(coin)

    await state.update_data(selected_delete_coins=list(selected))

    keyboard = delete_favorite_coins_keyboard(user_favorite_coins=favorites, selected_coins=selected)
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith('del_page_'))
async def del_pagination_handler(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split('_')[-1])
    data = await state.get_data()
    favorites = data.get('favorite_coins', [])
    selected = set(data.get('selected_delete_coins', []))

    keyboard = delete_favorite_coins_keyboard(
        user_favorite_coins=favorites, selected_coins=selected, page=page
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == 'fav_confirm_delete')
async def fav_confirm_delete_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get('selected_delete_coins', [])

    if not selected:
        await callback.answer("Сначала выбери хотя бы одну монету ☝️", show_alert=True)
        return

    tg_id = callback.from_user.id
    async with session_maker() as session:
        service = UserFavoriteCoinsService(session)
        for coin in selected:
            await service.remove_favorite_coin(tg_id=tg_id, coin=coin)

    await callback.answer(f"Удалено: {', '.join(selected)}")
    await _show_favorites(callback, tg_id=tg_id, state=state, edit=True)