import json
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from services.container import services
from services.achievement_service import ACHIEVEMENT_DEFS, CATEGORY_ICONS, CATEGORY_NAMES
from handlers.whisper import _get_whisper_for_user

router = Router()

COMMANDS_INFO = {
    "help": "Показать список команд",
    "news": "Новости мира за сегодня",
    "quests": "Посмотреть доступные квесты",
    "shop": "Открыть магазин",
    "inventory": "Посмотреть инвентарь",
    "locations": "Показать карту локаций",
    "go": "Показать куда можно идти",
    "status": "Показать статус персонажа",
    "whisper": "Слушать шёпот тумана",
    "achievements": "Просмотреть достижения",
}

COMMANDS_DESC = {
    "help": "Список всех доступных команд.",
    "news": "Ежедневная газета мира: что произошло, пока тебя не было.",
    "quests": "Посмотреть активные квесты и доступные задания.",
    "shop": "Купить или продать предметы в магазине.",
    "inventory": "Переглянути свій інвентар і предмети.",
    "locations": "Показати карту локацій і шляхи.",
    "go": "Показати доступні напрямки для переходу.",
    "status": "Показати статистику персонажа, рівень, нагромадження.",
    "whisper": "Слухати таємничі шепоти туману.",
    "achievements": "Переглянути інформацію про досягнення.",
}

COMMANDS_EXAMPLES = {
    "help": "<code>/help</code> - показать все команды",
    "news": "<code>/news</code> - показать новости мира",
    "quests": "<code>/quests</code> - показать квесты",
    "shop": "<code>/shop</code> - открыть магазин",
    "inventory": "<code>/inventory</code> - показать инвентарь",
    "locations": "<code>/locations</code> - показать карту",
    "go": "<code>/go</code> - куда можно идти",
    "status": "<code>/status</code> - показать статус",
    "whisper": "<code>/whisper</code> - послушать шёпот",
    "achievements": "<code>/achievements</code> - показать достижения",
}

LOC_NAMES = {
    "dark_forest": "Тёмный лес", "riverbank": "Берег реки",
    "ancient_ruins": "Древние руины", "fishing_village": "Рыбацкая деревня",
    "wolf_den": "Логово волков", "temple_of_shadows": "Храм теней",
    "crystal_cave": "Хрустальная пещера", "white_forest": "Белый лес",
    "library_of_echoes": "Библиотека эхов", "obsidian_tower": "Обсидиановая башня",
    "tower_summit": "Вершина башни", "blood_meadow": "Кровавый луг",
    "shadow_market": "Теневой рынок", "heart_of_mist": "Сердце MIST",
    "witch_swamp": "Топи ведьмы", "forgotten_graveyard": "Забытое кладбище",
    "dark_harbour": "Тёмная гавань", "ash_fields": "Пепельные поля",
    "abandoned_mine": "Заброшенная шахта", "enchanted_grove": "Зачарованная роща",
    "abandoned_camp": "Покинутый лагерь", "portal_nexus": "Узел порталов",
}


def _format_achievement(ach: dict, user_data) -> str:
    if user_data and user_data.get("unlocked_at"):
        reward = ""
        if ach.get("reward_xp"):
            reward += f" +{ach['reward_xp']} XP"
        if ach.get("reward_gold"):
            reward += f" +{ach['reward_gold']} Gold"
        return f"✅ {ach['icon']} {ach['name']} — {ach['description']}{reward}"
    else:
        if ach.get("is_secret"):
            return "⬜ ❓ ??? (Секрет)"
        else:
            return f"⬜ {ach['icon']} {ach['name']} — {ach['description']}"


@router.message(Command("help"))
async def cmd_help(message: Message):
    if message.chat.type != "private":
        return

    text = "🤖 <b>Команды MIST</b>\n\n"

    text += "<b>Основные команды:</b>\n"
    for cmd, desc in COMMANDS_INFO.items():
        text += f"  • <code>/{cmd}</code> — {desc}\n"

    text += "\n<b>Примеры использования:</b>\n"
    for cmd, example in COMMANDS_EXAMPLES.items():
        text += f"  {example}\n"

    text += "\n<b>Дополнительные возможности:</b>\n"
    text += "  • Нажимайте кнопки в меню для быстрого доступа\n"
    text += "  • Следите за шёпотами тумана (кнопка 🔮 Шёпот тумана)\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")]
    ])
    await message.answer(text, reply_markup=kb)


@router.message(Command("quests"))
async def cmd_quests(message: Message):
    if message.chat.type != "private":
        return

    user = await services.player.get_or_create(message.from_user.id)
    active_quests = await services.quest.get_user_quests(message.from_user.id)
    available_here = await services.quest.get_available(message.from_user.id, user["current_location"])
    all_available_quests = await services.quest.get_available(message.from_user.id)

    active_ids = {q["quest_id"] for q in active_quests if q["status"] == "active"}
    available_quest_ids = {q["quest_id"] for q in (available_here or [])}

    text = "📜 <b>Квесты</b>\n\n"

    if active_quests:
        active_list = [q for q in active_quests if q["status"] == "active"]
        if active_list:
            text += "<b>Активные:</b>\n"
            for q in active_list:
                progress = q.get("progress", {})
                objectives = q.get("objectives", [])
                loc_name = LOC_NAMES.get(q.get("location", ""), q.get("location", ""))
                text += f"\n📋 <b>{q['name']}</b>\n"
                text += f"  📍 {loc_name}\n"
                for obj in objectives:
                    p = progress.get(obj["id"], {"current": 0, "target": obj["target"]})
                    done = "✅" if p["current"] >= p["target"] else "⬜"
                    text += f"  {done} {obj['description']}: {p['current']}/{p['target']}\n"

    if available_here:
        text += "\n<b>📜 Доступны здесь:</b>\n"
        for q in available_here:
            text += f"  → {q['name']}\n"

    remote = [q for q in all_available_quests if q["quest_id"] not in active_ids and q["quest_id"] not in available_quest_ids]
    if remote:
        text += "\n<b>Другие квесты:</b>\n"
        for q in remote:
            loc_name = LOC_NAMES.get(q["location"], q["location"])
            text += f"  • {q['name']} <i>({loc_name})</i>\n"

    if not active_quests and not available_here and not remote:
        text += "Пока ничего. Иди исследуй мир — квесты найдутся."

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Квесты", callback_data="quests")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])
    await message.answer(text, reply_markup=kb)


@router.message(Command("shop"))
async def cmd_shop(message: Message):
    if message.chat.type != "private":
        return

    user = await services.player.get_or_create(message.from_user.id)
    loc = user["current_location"]

    from services.shop_service import ShopService
    SHOP_LOCATIONS = ShopService.SHOP_LOCATIONS

    available_shops = []
    for shop_id in SHOP_LOCATIONS:
        if loc == shop_id or await services.shop.is_nearby(loc, shop_id):
            available_shops.append(shop_id)

    if not available_shops:
        text = "🛒 <b>Здесь нет магазинов.</b>\n\nПопробуй Торговую площадь или Теневой рынок."
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")]
        ])
        await message.answer(text, reply_markup=kb)
        return

    text = f"🛒 <b>Магазин</b>\n\n💰 Золото: {user['gold']} 🪙\n\n"
    text += "Доступны магазины:\n"
    for shop_id in available_shops:
        text += f"  • {SHOP_LOCATIONS[shop_id]}\n"

    buttons = []
    for shop_id in available_shops:
        buttons.append([InlineKeyboardButton(
            text=f"🏪 {SHOP_LOCATIONS[shop_id]}",
            callback_data=f"shop_open:{shop_id}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])

    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.message(Command("inventory"))
async def cmd_inventory(message: Message):
    if message.chat.type != "private":
        return

    items = await services.inventory.get(message.from_user.id)

    if not items:
        text = "🎒 <b>Инвентарь пуст</b>\n\nТы ничего не несёшь. Пока."
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")]
        ])
        await message.answer(text, reply_markup=kb)
        return

    text = "🎒 <b>Твой инвентарь:</b>\n\n"
    buttons = []
    for item in items:
        magic = " ✨" if item["is_magic"] else ""
        rarity_map = {"common": "", "rare": "🔵", "epic": "🟣", "legendary": "🟡"}
        rarity = rarity_map.get(item.get("rarity", ""), "")
        name = item.get("name") or item["item_id"]
        text += f"• {rarity} {name} x{item['quantity']}{magic}\n"

        if item.get("is_usable"):
            buttons.append([InlineKeyboardButton(
                text=f"🧪 Использовать: {name}",
                callback_data=f"use_item:{item['item_id']}"
            )])

    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(text, reply_markup=kb)


@router.message(Command("locations"))
async def cmd_locations(message: Message):
    if message.chat.type != "private":
        return

    user = await services.player.get_or_create(message.from_user.id)
    loc = await services.movement.get_location(user["current_location"])
    connections = loc.get("connections", [])

    text = f"🗺 <b>Выходы из «{loc['name']}»:</b>\n\n"
    for loc_id in connections:
        target = await services.movement.get_location(loc_id)
        if target:
            icon = "✅" if target["discovered"] else "❓"
            text += f"{icon} {target['name']}\n"

    from handlers.game import nav_kb
    kb = await nav_kb(connections)
    await message.answer(text, reply_markup=kb)


@router.message(Command("go"))
async def cmd_go(message: Message):
    if message.chat.type != "private":
        return

    user = await services.player.get_or_create(message.from_user.id)
    loc = await services.movement.get_location(user["current_location"])
    connections = loc.get("connections", []) if loc else []

    loc_name = loc["name"] if loc else user["current_location"]
    text = f"🧭 <b>Куда идти из «{loc_name}»?</b>\n\n"

    if not connections:
        text += "Нет доступных выходов. Осмотрись — возможно, путь откроется.\n"
    else:
        for loc_id in connections:
            target = await services.movement.get_location(loc_id)
            if target:
                icon = "✅" if target["discovered"] else "❓"
                text += f"{icon} {target['name']}\n"

    kb = await nav_kb(connections)
    await message.answer(text, reply_markup=kb)


@router.message(Command("status"))
async def cmd_status(message: Message):
    if message.chat.type != "private":
        return

    user = await services.player.get_or_create(message.from_user.id)
    days = user.get("days_in_mist", 0)
    xp_needed = user["level"] * 100

    loc_name = await services.movement.get_location_name(user["current_location"])
    text = (
        f"👤 <b>{user['display_name']}</b>\n\n"
        f"📍 Локация: {loc_name}\n"
        f"⏰ Дней в MIST: {days}\n\n"
        f"❤️ HP: {user['hp']}/{user['max_hp']}\n"
        f"🗡 Атака: {user['attack']}\n"
        f"🛡 Защита: {user['defense']}\n"
        f"⭐ Уровень: {user['level']} (XP: {user['xp']}/{xp_needed})\n"
        f"🪙 Золото: {user['gold']}\n\n"
        f"🎒 Воспоминаний: {user['memories']}\n"
        f"⚖️ Карма: {user['karma']}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")]
    ])
    await message.answer(text, reply_markup=kb)


@router.message(Command("whisper"))
async def cmd_whisper(message: Message):
    if message.chat.type != "private":
        return

    whisper_text = await _get_whisper_for_user(message.from_user.id)

    text = (
        f"🌫 <i>{whisper_text}</i>\n\n"
        "<i>Туман отвечает не всегда. Но когда отвечает — запоминаешь.</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔮 Ещё шёпот", callback_data="whisper")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])
    await message.answer(text, reply_markup=kb)


@router.message(Command("achievements"))
async def cmd_achievements(message: Message):
    if message.chat.type != "private":
        return

    user_id = message.from_user.id
    newly_unlocked = await services.achievement.check(user_id)
    all_achs = await services.achievement.get_user_achievements(user_id)

    user_ach_map = {a["achievement_id"]: a for a in all_achs} if all_achs else {}

    categories: dict[str, list[dict]] = {}
    for ach in ACHIEVEMENT_DEFS:
        cat = ach.get("category", "general")
        categories.setdefault(cat, []).append(ach)

    total = len(ACHIEVEMENT_DEFS)
    unlocked_count = sum(
        1 for a in all_achs if a.get("unlocked_at")
    ) if all_achs else 0

    lines: list[str] = []
    lines.append("🏆 <b>Достижения</b>")

    if newly_unlocked:
        lines.append("")
        lines.append("🔓 <b>Новые достижения!</b>")
        for nl in newly_unlocked:
            lines.append(f"🩸 {nl['name']} — {nl['description']}")

    category_order = [
        "combat", "explore", "quests", "progress",
        "wealth", "craft", "pvp", "social", "general"
    ]

    for cat in category_order:
        achs_in_cat = categories.get(cat, [])
        if not achs_in_cat:
            continue

        icon = CATEGORY_ICONS.get(cat, "⭐")
        name = CATEGORY_NAMES.get(cat, cat.capitalize())
        lines.append("")
        lines.append(f"{icon} <b>{name}</b>")

        for ach in achs_in_cat:
            user_data = user_ach_map.get(ach["achievement_id"])
            lines.append(f"    {_format_achievement(ach, user_data)}")

    lines.append("")
    lines.append(f"📊 Прогресс: {unlocked_count}/{total}")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])

    await message.answer(
        "\n".join(lines),
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.message(Command("news"))
async def cmd_news(message: Message):
    if message.chat.type != "private":
        return

    news = await services.world_engine.get_news()
    day = news["day"]
    season = news["season"]
    season_names = {"spring": "Весна", "summer": "Лето", "autumn": "Осень", "winter": "Зима"}
    season_name = season_names.get(season, season)

    lines = [f"📰 <b>Новости мира — День {day}, {season_name}</b>", ""]

    events = news.get("events", [])
    if events:
        for ev in events:
            icon = "🔥" if "fire" in ev["event_type"] else \
                   "🐺" if "wolf" in ev["event_type"] else \
                   "🌾" if "harvest" in ev["event_type"] else \
                   "☀️" if "drought" in ev["event_type"] else \
                   "🔮" if "altar" in ev["event_type"] or "ruin" in ev["event_type"] else \
                   "💀" if "undead" in ev["event_type"] else \
                   "🚢" if "ship" in ev["event_type"] else \
                   "⚔️" if "war" in ev["event_type"] or "bandit" in ev["event_type"] else \
                   "🌫" if "fog" in ev["event_type"] else \
                   "🌸" if "spring" in ev["event_type"] else \
                   "🏮" if "lantern" in ev["event_type"] else \
                   "☄️" if "meteorite" in ev["event_type"] else \
                   "☠️" if "plague" in ev["event_type"] else \
                   "🎭" if "merchant" in ev["event_type"] else \
                   "🌊" if "flood" in ev["event_type"] else \
                   "🏜" if "drought" in ev["event_type"] else "📜"

            status = "✅" if ev.get("is_active") else "⏹"
            lines.append(f"{icon} {status} <b>{ev['name']}</b>")
            lines.append(f"   <i>{ev['description']}</i>")
            lines.append("")
    else:
        lines.append("Здесь ничего особенного не произошло.")
        lines.append("")

    active = news.get("active", [])
    if active:
        lines.append("<b>📊 Активные события:</b>")
        for a in active[:5]:
            lines.append(f"  • {a['name']}")
        lines.append("")

    dangerous = news.get("dangerous_locations", [])
    if dangerous:
        lines.append("<b>⚠️ Самые опасные места:</b>")
        for d in dangerous[:3]:
            lines.append(f"  • {d['name']} — ⚠️ {d['danger_level']}")
        lines.append("")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")]
    ])
    await message.answer("\n".join(lines), reply_markup=kb)


@router.callback_query(F.data == "commands")
async def cb_commands(callback: CallbackQuery):
    text = "🤖 <b>Команды MIST</b>\n\n"

    text += "<b>Основные команды:</b>\n"
    for cmd, desc in COMMANDS_INFO.items():
        text += f"  • <code>/{cmd}</code> — {desc}\n"

    text += "\n<b>Примеры использования:</b>\n"
    for cmd, example in COMMANDS_EXAMPLES.items():
        text += f"  {example}\n"

    text += "\n<b>Дополнительные возможности:</b>\n"
    text += "  • Нажимайте кнопки в меню для быстрого доступа\n"
    text += "  • Следите за шёпотами тумана (кнопка 🔮 Шёпот тумана)\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
