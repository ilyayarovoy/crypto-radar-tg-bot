from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def all_favorites_coins_keyboard(user_favorites_coins: list[str], page: int = 0, per_page: int = 3) -> InlineKeyboardMarkup:
    keyboard_buttons = []

    start_idx = page * per_page
    end_idx = start_idx + per_page
    current_slice = user_favorites_coins[start_idx:end_idx]

    for coin in current_slice:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"🪙 {coin.upper()}",
                callback_data=f"coin_info_{coin}",  # Посмотреть детально/удалить
            )
        ])

    nav_buttons = []
    total_pages = (len(user_favorites_coins) + per_page - 1) // per_page

    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"fav_page_{page - 1}")
        )

    if total_pages > 1:
        nav_buttons.append(
            InlineKeyboardButton(text=f"📄 {page + 1}/{total_pages}", callback_data="ignore")
        )

    if end_idx < len(user_favorites_coins):
        nav_buttons.append(
            InlineKeyboardButton(text="Вперед ➡️", callback_data=f"fav_page_{page + 1}")
        )

    if nav_buttons:
        keyboard_buttons.append(nav_buttons)

    # ВАЖНО: раньше эти две кнопки были внутри `if nav_buttons:`, из-за чего
    # при одной странице избранного (<= per_page монет) они вообще не показывались.
    # Теперь они всегда видны.
    keyboard_buttons.append([
        InlineKeyboardButton(text="➕ Добавить монету", callback_data="fav_add_prompt")
    ])
    keyboard_buttons.append([
        InlineKeyboardButton(text="❌ Удалить монету", callback_data="fav_delete_prompt")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def _toggle_selection_keyboard(
    items: list[str],
    selected: set[str],
    toggle_prefix: str,
    page_prefix: str,
    confirm_callback: str,
    confirm_text: str,
    page: int = 0,
    per_page: int = 5,
    show_manual_entry: bool = False,
    show_back: bool = False,
) -> InlineKeyboardMarkup:

    keyboard_buttons = []

    start_idx = page * per_page
    end_idx = start_idx + per_page
    current_slice = items[start_idx:end_idx]

    for item in current_slice:
        mark = "✅ " if item in selected else ""
        keyboard_buttons.append([
            InlineKeyboardButton(text=f"{mark}{item}", callback_data=f"{toggle_prefix}{item}")
        ])

    nav_buttons = []
    total_pages = (len(items) + per_page - 1) // per_page

    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{page_prefix}{page - 1}")
        )
    if total_pages > 1:
        nav_buttons.append(
            InlineKeyboardButton(text=f"📄 {page + 1}/{total_pages}", callback_data="ignore")
        )
    if end_idx < len(items):
        nav_buttons.append(
            InlineKeyboardButton(text="Вперед ➡️", callback_data=f"{page_prefix}{page + 1}")
        )
    if nav_buttons:
        keyboard_buttons.append(nav_buttons)

    if show_manual_entry:
        keyboard_buttons.append([
            InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="fav_add_custom")
        ])

    # Кнопку подтверждения показываем только если вообще есть из чего выбирать
    if items:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{confirm_text} ({len(selected)})", callback_data=confirm_callback
            )
        ])

    if show_back:
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Назад", callback_data="fav_back")
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def add_favorite_coins_keyboard(
    recommended_coin_list: list[str],
    selected_coins: set[str] | None = None,
    page: int = 0,
    per_page: int = 5,
    show_back: bool = False,
) -> InlineKeyboardMarkup:
    return _toggle_selection_keyboard(
        items=recommended_coin_list,
        selected=selected_coins or set(),
        toggle_prefix="toggle_coin_",
        page_prefix="rec_page_",
        confirm_callback="fav_confirm_add",
        confirm_text="➕ Добавить выбранные",
        page=page,
        per_page=per_page,
        show_manual_entry=True,
        show_back=show_back,
    )


def delete_favorite_coins_keyboard(
    user_favorite_coins: list[str],
    selected_coins: set[str] | None = None,
    page: int = 0,
    per_page: int = 5,
) -> InlineKeyboardMarkup:
    return _toggle_selection_keyboard(
        items=user_favorite_coins,
        selected=selected_coins or set(),
        toggle_prefix="toggle_delete_coin_",
        page_prefix="del_page_",
        confirm_callback="fav_confirm_delete",
        confirm_text="🗑 Удалить выбранные",
        page=page,
        per_page=per_page,
        show_manual_entry=False,
        show_back=True,
    )