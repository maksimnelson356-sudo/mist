from aiogram import Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from services.container import services

router = Router()


async def _loc_name(loc_id: str) -> str:
    loc = await services.movement.get_location(loc_id)
    return loc["name"] if loc else loc_id


def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Осмотреться", callback_data="look")],
        [InlineKeyboardButton(text="🗺 Карта", callback_data="locations")],
        [InlineKeyboardButton(text="⚔️ Бой", callback_data="fight_menu")],
        [InlineKeyboardButton(text="📜 Квесты", callback_data="quests")],
        [InlineKeyboardButton(text="💚 Исцелиться", callback_data="heal")],
        [InlineKeyboardButton(text="🍖 Поесть", callback_data="eat_food")],
        [InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inventory")],
        [InlineKeyboardButton(text="🛒 Магазин", callback_data="shop")],
        [InlineKeyboardButton(text="📊 Рынок", callback_data="market_menu")],
        [InlineKeyboardButton(text="⚒️ Крафт", callback_data="crafting_menu")],
        [InlineKeyboardButton(text="🤝 Трейдинг", callback_data="trade_menu")],
        [InlineKeyboardButton(text="🏰 Гильдия", callback_data="guild_menu")],
        [InlineKeyboardButton(text="🛡️ Снаряжение", callback_data="equipment_menu")],
        [InlineKeyboardButton(text="🏠 Дом", callback_data="home_menu")],
        [InlineKeyboardButton(text="🏺 Артефакты", callback_data="artifact_menu")],
        [InlineKeyboardButton(text="💀 Боссы", callback_data="boss_menu")],
        [InlineKeyboardButton(text="🐉 Рейды", callback_data="raid_menu")],
        [InlineKeyboardButton(text="🎭 События", callback_data="event_menu")],
        [InlineKeyboardButton(text="⚔️ Войны", callback_data="war_menu")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance_menu")],
        [InlineKeyboardButton(text="📖 Каталог", callback_data="catalog_menu")],
        [InlineKeyboardButton(text="📜 Хроника", callback_data="world_chronicle")],
        [InlineKeyboardButton(text="📅 Награды дня", callback_data="daily_menu")],
        [InlineKeyboardButton(text="⚔️ Класс", callback_data="class_menu")],
        [InlineKeyboardButton(text="🏴 Фракции", callback_data="faction_menu")],
        [InlineKeyboardButton(text="🔮 Шёпот тумана", callback_data="whisper")],
        [InlineKeyboardButton(text="🏆 Энциклопедия", callback_data="legends")],
        [InlineKeyboardButton(text="📊 Лидерборды", callback_data="leaderboard_menu")],
        [InlineKeyboardButton(text="⚔️ PvP Арена", callback_data="pvp_menu")],
        [InlineKeyboardButton(text="🤖 Команды", callback_data="commands")],
    ])


def back_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")]
    ])


def post_action_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Осмотреться", callback_data="look")],
        [InlineKeyboardButton(text="🗺 Карта", callback_data="locations")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])


async def nav_kb(connections: list) -> InlineKeyboardMarkup:
    buttons = []
    for loc_id in connections:
        name = await _loc_name(loc_id)
        buttons.append([InlineKeyboardButton(
            text=f"🚶 {name}",
            callback_data=f"move:{loc_id}"
        )])
    buttons.append([InlineKeyboardButton(text="🔍 Осмотреться", callback_data="look")])
    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def combat_kb(creatures: list) -> InlineKeyboardMarkup:
    buttons = []
    for c in creatures:
        buttons.append([InlineKeyboardButton(
            text=f"⚔️ {c['name']} (HP:{c['hp']})",
            callback_data=f"attack:{c['creature_id']}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def creature_action_kb(creatures: list) -> InlineKeyboardMarkup:
    buttons = []
    for c in creatures:
        icon = {"hostile": "⚔️", "neutral": "🗣", "friendly": "💚"}.get(c["disposition"], "❓")
        buttons.append([InlineKeyboardButton(
            text=f"{icon} {c['name']}",
            callback_data=f"creature_action:{c['creature_id']}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def ground_items_kb(items: list) -> InlineKeyboardMarkup:
    buttons = []
    for item in items:
        name = item.get("name") or item["item_id"]
        buttons.append([InlineKeyboardButton(
            text=f"🤲 {name} x{item['quantity']}",
            callback_data=f"pickup:{item['item_id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
