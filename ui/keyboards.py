from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Осмотреться", callback_data="look")],
        [InlineKeyboardButton(text="🗺 Карта", callback_data="locations")],
        [InlineKeyboardButton(text="⚔️ Бой", callback_data="fight_menu")],
        [InlineKeyboardButton(text="📜 Квесты", callback_data="quests")],
        [InlineKeyboardButton(text="💚 Исцелиться", callback_data="heal")],
        [InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inventory")],
        [InlineKeyboardButton(text="🛒 Магазин", callback_data="shop")],
        [InlineKeyboardButton(text="⚒️ Крафт", callback_data="crafting_menu")],
        [InlineKeyboardButton(text="🤝 Трейдинг", callback_data="trade_menu")],
        [InlineKeyboardButton(text="🏰 Гильдия", callback_data="guild_menu")],
        [InlineKeyboardButton(text="🛡️ Снаряжение", callback_data="equipment_menu")],
        [InlineKeyboardButton(text="👤 Статус", callback_data="status")],
        [InlineKeyboardButton(text="🔮 Шёпот тумана", callback_data="whisper")],
        [InlineKeyboardButton(text="🏆 Энциклопедия", callback_data="legends")],
        [InlineKeyboardButton(text="⚔️ PvP Арена", callback_data="pvp_menu")],
        [InlineKeyboardButton(text="🤖 Команды", callback_data="commands")],
    ])


def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])


def confirm_kb(action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm:{action}"),
            InlineKeyboardButton(text="❌ Нет", callback_data="main_menu"),
        ]
    ])


def post_action_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Осмотреться", callback_data="look")],
        [InlineKeyboardButton(text="🗺 Карта", callback_data="locations")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])


def list_kb(items: list, callback_prefix: str) -> InlineKeyboardMarkup:
    buttons = []
    for item in items:
        buttons.append([InlineKeyboardButton(
            text=item.get("label", item.get("name", "?")),
            callback_data=f"{callback_prefix}:{item.get('id', item.get('key', ''))}",
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def paginated_kb(items: list, page: int, per_page: int, callback_prefix: str) -> InlineKeyboardMarkup:
    total_pages = max(1, (len(items) + per_page - 1) // per_page)
    start = page * per_page
    end = start + per_page
    page_items = items[start:end]

    buttons = []
    for item in page_items:
        buttons.append([InlineKeyboardButton(
            text=item.get("label", item.get("name", "?")),
            callback_data=f"{callback_prefix}:{item.get('id', item.get('key', ''))}",
        )])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"{callback_prefix}:page:{page - 1}"))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"{callback_prefix}:page:{page + 1}"))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
