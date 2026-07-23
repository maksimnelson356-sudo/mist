import json
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
import game_engine as ge

router = Router()

COMMANDS_INFO = {
    "help": "Показать список команд",
    "quests": "Посмотреть доступные квесты",
    "shop": "Открыть магазин",
    "inventory": "Посмотреть инвентарь",
    "locations": "Показать карту локаций",
    "status": "Показать статус персонажа",
    "whisper": "Слушать шёпот тумана",
    "achievements": "Просмотреть достижения",
}

COMMANDS_DESC = {
    "help": "Список всех доступных команд.",
    "quests": "Посмотреть активные квесты и доступные задания.",
    "shop": "Купить или продать предметы в магазине.",
    "inventory": "Переглянути свій інвентар і предмети.",
    "locations": "Показати карту локацій і шляхи.",
    "status": "Показати статистику персонажа, рівень, нагромадження.",
    "whisper": "Слухати таємничі шепоти туману.",
    "achievements": "Переглянути інформацію про досягнення.",
}

COMMANDS_EXAMPLES = {
    "help": "<code>/help</code> - показать все команды",
    "quests": "<code>/quests</code> - показать квесты",
    "shop": "<code>/shop</code> - открыть магазин",
    "inventory": "<code>/inventory</code> - показать инвентарь",
    "locations": "<code>/locations</code> - показать карту",
    "status": "<code>/status</code> - показать статус",
    "whisper": "<code>/whisper</code> - послушать шёпот",
    "achievements": "<code>/achievements</code> - показать достижения",
}


@router.message(Command("start"))
async def cmd_start_general(message: Message):
    if message.chat.type != "private":
        return

    user = await ge.get_or_create_user(message.from_user.id, message.from_user.username)

    if not user["is_alive"]:
        text = (
            "<pre>💀\n🕯️👁🕯️\n💀</pre>\n"
            "💀 <b>Ты мертв.</b>\n\n"
            "Туман накрыл тебя. Но он не отпускает.\n"
            "Ты чувствуешь — ты ещё нужен."
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
        ])
        await message.answer(text, reply_markup=kb)
        return

    loc = await ge.get_location(user["current_location"])
    scene = LOC_SCENES.get(user["current_location"], "")
    text = ""
    if scene:
        text += f"<pre>{scene}</pre>\n{SCENE_DIVIDER}\n"
    text += (
        "🌫 <b>Добро пожаловать в MIST</b>\n\n"
        "Ты просыпаешься в тумане.\n"
        "Не помнишь, как сюда попал.\n\n"
        "Туман помнит всё.\n\n"
        f"📍 <b>{loc['name']}</b>\n"
        f"❤️ HP: {user['hp']}/{user['max_hp']} | ⭐ Ур. {user['level']}\n"
        f"🪙 Золото: {user['gold']} | 🎒 Воспоминаний: {user['memories']}"
    )
    await message.answer(text, reply_markup=main_menu_kb())


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

    await ge._log_action(message.from_user.id, "cmd_quests")

    user = await ge.get_or_create_user(message.from_user.id)
    active_quests = await ge.get_user_quests(message.from_user.id)
    available_here = await ge.get_available_quests(message.from_user.id, user["current_location"])
    all_available_quests = await ge.get_available_quests(message.from_user.id)

    active_ids = {q["quest_id"] for q in active_quests if q["status"] == "active"}
    available_quest_ids = {q["quest_id"] for q in (available_here or [])}

    text = "📜 <b>Квесты</b>\n\n"

    if active_quests:
        active_list = [q for q in active_quests if q["status"] == "active"]
        if active_list:
            text += "<b>Активные:</b>\n"
            for q in active_list:
                progress = json.loads(q["progress"]) if isinstance(q["progress"], str) else q["progress"]
                objectives = json.loads(q["objectives"]) if isinstance(q["objectives"], str) else q["objectives"]
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

    await ge._log_action(message.from_user.id, "cmd_shop")

    user = await ge.get_or_create_user(message.from_user.id)
    loc = user["current_location"]

    available_shops = []
    for shop_id in SHOP_LOCATIONS:
        if loc == shop_id or _is_nearby(loc, shop_id):
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


@router.message(Command("inventory") or Command("inv"))
async def cmd_inventory(message: Message):
    if message.chat.type != "private":
        return

    await ge._log_action(message.from_user.id, "cmd_inventory")

    items = await ge.get_inventory(message.from_user.id)

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


@router.message(Command("locations") or Command("map"))
async def cmd_locations(message: Message):
    if message.chat.type != "private":
        return

    await ge._log_action(message.from_user.id, "cmd_locations")

    user = await ge.get_or_create_user(message.from_user.id)
    loc = await ge.get_location(user["current_location"])
    connections = json.loads(loc["connections"]) if isinstance(loc["connections"], str) else loc["connections"]

    text = f"🗺 <b>Выходы из «{loc['name']}»:</b>\n\n"
    for loc_id in connections:
        target = await ge.get_location(loc_id)
        if target:
            icon = "✅" if target["discovered"] else "❓"
            text += f"{icon} {target['name']}\n"

    kb = await nav_kb(connections)
    await message.answer(text, reply_markup=kb)


@router.message(Command("status") or Command("info"))
async def cmd_status(message: Message):
    if message.chat.type != "private":
        return

    await ge._log_action(message.from_user.id, "cmd_status")

    user = await ge.get_or_create_user(message.from_user.id)
    user_actions = await ge.get_user_actions(message.from_user.id, limit=1000000)
    total = len(user_actions)
    action_count = await ge.count_actions()
    days = user.get("days_in_mist", 0)
    xp_needed = user["level"] * 100

    text = (
        f"👤 <b>{user['display_name']}</b>\n\n"
        f"📍 Локация: {user['current_location']}\n"
        f"⏰ Дней в MIST: {days}\n\n"
        f"❤️ HP: {user['hp']}/{user['max_hp']}\n"
        f"🗡 Атака: {user['attack']}\n"
        f"🛡 Защита: {user['defense']}\n"
        f"⭐ Уровень: {user['level']} (XP: {user['xp']}/{xp_needed})\n"
        f"🪙 Золото: {user['gold']}\n\n"
        f"🎒 Воспоминаний: {user['memories']}\n"
        f"⚖️ Карма: {user['karma']}\n"
        f"📝 Твоих действий: {total}\n"
        f"🌍 Всего в мире: {action_count}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")]
    ])
    await message.answer(text, reply_markup=kb)


@router.message(Command("whisper") or Command("whispers"))
async def cmd_whisper(message: Message):
    if message.chat.type != "private":
        return

    await ge._log_action(message.from_user.id, "cmd_whisper")

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


@router.message(Command("achievements") or Command("ach"))
async def cmd_achievements(message: Message):
    if message.chat.type != "private":
        return

    await ge._log_action(message.from_user.id, "cmd_achievements")

    user_id = message.from_user.id
    newly_unlocked = await ge.check_achievements(user_id)
    all_achs = await ge.get_user_achievements(user_id)

    user_ach_map = {a["achievement_id"]: a for a in all_achs} if all_achs else {}

    ach_defs = ge.ACHIEVEMENT_DEFS
    categories: dict[str, list[dict]] = {}
    for ach in ach_defs:
        cat = ach.get("category", "general")
        categories.setdefault(cat, []).append(ach)

    total = len(ach_defs)
    unlocked_count = sum(
        1 for a in all_achs if a.get("unlocked")
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


def _format_achievement(ach: dict, user_data: dict | None) -> str:
    if user_data and user_data.get("unlocked"):
        unlock_date = user_data.get("unlock_date", "")
        date_str = f" ({unlock_date})" if unlock_date else ""
        reward = ""
        if ach.get("reward_xp"):
            reward += f" +{ach['reward_xp']} XP"
        if ach.get("reward_gold"):
            reward += f" +{ach['reward_gold']} Gold"
        return f"✅ {ach['icon']} {ach['name']} — {ach['description']}{reward}{date_str}"
    else:
        if ach.get("is_secret") == 1:
            return "⬜ ❓ ??? (Секрет)"
        else:
            return f"⬜ {ach['icon']} {ach['name']} — {ach['description']}"