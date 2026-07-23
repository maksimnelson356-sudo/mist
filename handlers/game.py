import json
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart
import game_engine as ge

router = Router()


def is_my_message(message: Message, bot_username: str) -> bool:
    if message.chat.type == "private":
        return True
    if message.text and message.text.startswith("/"):
        cmd = message.text.split()[0].lstrip("/")
        if "@" in cmd:
            return cmd.split("@")[1].lower() == bot_username.lower()
        return False
    return True


async def _loc_name(loc_id: str) -> str:
    loc = await ge.get_location(loc_id)
    return loc["name"] if loc else loc_id


# ─── Клавиатуры ───

def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Осмотреться", callback_data="look")],
        [InlineKeyboardButton(text="🗺 Карта", callback_data="locations")],
        [InlineKeyboardButton(text="⚔️ Бой", callback_data="fight_menu")],
        [InlineKeyboardButton(text="📜 Квесты", callback_data="quests")],
        [InlineKeyboardButton(text="💚 Исцелиться", callback_data="heal")],
        [InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inventory")],
        [InlineKeyboardButton(text="👤 Статус", callback_data="status")],
        [InlineKeyboardButton(text="🔮 Шёпот тумана", callback_data="whisper")],
        [InlineKeyboardButton(text="🏆 Энциклопедия", callback_data="legends")],
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


# ──────────────────────────────────────────────
#  Старт
# ──────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, bot_username: str):
    if not is_my_message(message, bot_username):
        return

    user = await ge.get_or_create_user(message.from_user.id, message.from_user.username)

    if not user["is_alive"]:
        text = (
            "💀 <b>Ты мёртв.</b>\n\n"
            "Туман накрыл тебя. Но он не отпускает.\n"
            "Ты чувствуешь — ты ещё нужен."
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
        ])
        await message.answer(text, reply_markup=kb)
        return

    loc = await ge.get_location(user["current_location"])
    text = (
        "🌫 <b>Добро пожаловать в MIST</b>\n\n"
        "Ты просыпаешься в тумане.\n"
        "Не помнишь, как сюда попал.\n\n"
        "Туман помнит всё.\n\n"
        f"📍 <b>{loc['name']}</b>\n"
        f"❤️ HP: {user['hp']}/{user['max_hp']} | ⭐ Ур. {user['level']}\n"
        f"🎒 Воспоминаний: {user['memories']} | ⚖️ Карма: {user['karma']}"
    )
    await message.answer(text, reply_markup=main_menu_kb())


@router.callback_query(F.data == "revive")
async def cb_revive(callback: CallbackQuery):
    result = await ge.revive_user(callback.from_user.id)
    if result["success"]:
        user = await ge.get_or_create_user(callback.from_user.id)
        loc = await ge.get_location(user["current_location"])
        text = result["message"] + f"\n\n📍 <b>{loc['name']}</b>"
        kb = main_menu_kb()
    else:
        text = result["message"]
        kb = back_menu_kb()
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    user = await ge.get_or_create_user(callback.from_user.id, callback.from_user.username)

    if not user["is_alive"]:
        text = "💀 <b>Ты мёртв.</b>\n\nТуман накрыл тебя."
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
        ])
        await callback.message.edit_text(text, reply_markup=kb)
        await callback.answer()
        return

    loc = await ge.get_location(user["current_location"])
    text = (
        f"📍 <b>{loc['name']}</b>\n"
        f"❤️ HP: {user['hp']}/{user['max_hp']} | ⭐ Ур. {user['level']}\n"
        f"🎒 Воспоминаний: {user['memories']} | ⚖️ Карма: {user['karma']}"
    )
    await callback.message.edit_text(text, reply_markup=main_menu_kb())
    await callback.answer()


# ──────────────────────────────────────────────
#  Осмотреться
# ──────────────────────────────────────────────

@router.callback_query(F.data == "look")
async def cb_look(callback: CallbackQuery):
    user = await ge.get_or_create_user(callback.from_user.id)
    loc = await ge.get_location(user["current_location"])
    creatures = await ge.get_creatures_at_location(user["current_location"])
    ground = await ge.get_ground_items(user["current_location"])

    text = f"🌍 <b>{loc['name']}</b>\n\n{loc['description']}\n"

    if creatures:
        text += "\n👁 <b>Здесь есть:</b>\n"
        for c in creatures:
            icon = {"hostile": "🔴", "neutral": "🟡", "friendly": "🟢"}.get(c["disposition"], "⚪")
            text += f"  {icon} {c['name']}\n"

    if ground:
        text += "\n📦 <b>На земле:</b>\n"
        for g in ground:
            name = g.get("name") or g["item_id"]
            text += f"  • {name} x{g['quantity']}\n"

    connections = json.loads(loc["connections"]) if isinstance(loc["connections"], str) else loc["connections"]
    if connections:
        text += "\n🚪 <b>Выходы:</b>\n"
        for loc_id in connections:
            target = await ge.get_location(loc_id)
            if target:
                text += f"  • {target['name']}\n"

    await ge._log_action(callback.from_user.id, "look", location=user["current_location"])

    buttons = []
    for loc_id in connections:
        name = await _loc_name(loc_id)
        buttons.append([InlineKeyboardButton(text=f"🚶 {name}", callback_data=f"move:{loc_id}")])

    if creatures:
        buttons.append([InlineKeyboardButton(text=f"👁 Взаимодействие ({len(creatures)})", callback_data="creature_menu")])

    if ground:
        buttons.append([InlineKeyboardButton(text=f"📦 Подобрать ({len(ground)})", callback_data="ground_menu")])

    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ──────────────────────────────────────────────
#  Взаимодействие с существами
# ──────────────────────────────────────────────

@router.callback_query(F.data == "creature_menu")
async def cb_creature_menu(callback: CallbackQuery):
    user = await ge.get_or_create_user(callback.from_user.id)
    creatures = await ge.get_creatures_at_location(user["current_location"])

    if not creatures:
        await callback.message.edit_text("Здесь никого нет.", reply_markup=back_menu_kb())
        await callback.answer()
        return

    text = "👁 <b>К кому подойти?</b>\n\n"
    for c in creatures:
        icon = {"hostile": "⚔️", "neutral": "🗣", "friendly": "💚"}.get(c["disposition"], "❓")
        text += f"{icon} {c['name']}\n"

    await callback.message.edit_text(text, reply_markup=creature_action_kb(creatures))
    await callback.answer()


@router.callback_query(F.data.startswith("creature_action:"))
async def cb_creature_action(callback: CallbackQuery):
    creature_id = callback.data.split(":")[1]
    creature = await ge.get_creature(creature_id)

    if not creature or not creature["is_alive"]:
        await callback.message.edit_text("Этого существа здесь нет.", reply_markup=back_menu_kb())
        await callback.answer()
        return

    icon = {"hostile": "🔴", "neutral": "🟡", "friendly": "🟢"}.get(creature["disposition"], "⚪")
    text = f"{icon} <b>{creature['name']}</b>\n\n{creature['description']}\n"

    buttons = []
    if creature["disposition"] == "friendly":
        buttons.append([InlineKeyboardButton(text="🗣 Поговорить", callback_data=f"talk:{creature_id}")])
    elif creature["disposition"] == "neutral":
        buttons.append([InlineKeyboardButton(text="🗣 Попробовать поговорить", callback_data=f"talk:{creature_id}")])
        buttons.append([InlineKeyboardButton(text="⚔️ Атаковать", callback_data=f"attack:{creature_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="⚔️ Атаковать", callback_data=f"attack:{creature_id}")])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="creature_menu")])
    buttons.append([InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("talk:"))
async def cb_talk(callback: CallbackQuery):
    creature_id = callback.data.split(":")[1]
    result = await ge.talk_to_creature(callback.from_user.id, creature_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="creature_menu")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
    ])

    await callback.message.edit_text(result["message"], reply_markup=kb)
    await callback.answer()


# ──────────────────────────────────────────────
#  Подбор предметов
# ──────────────────────────────────────────────

@router.callback_query(F.data == "ground_menu")
async def cb_ground_menu(callback: CallbackQuery):
    user = await ge.get_or_create_user(callback.from_user.id)
    ground = await ge.get_ground_items(user["current_location"])

    if not ground:
        await callback.message.edit_text("На земле ничего нет.", reply_markup=back_menu_kb())
        await callback.answer()
        return

    text = "📦 <b>На земле:</b>\n\n"
    for g in ground:
        name = g.get("name") or g["item_id"]
        rarity = g.get("rarity", "")
        icon = {"rare": "🔵", "epic": "🟣", "legendary": "🟡"}.get(rarity, "⚪")
        text += f"{icon} {name} x{g['quantity']}\n"

    kb = ground_items_kb(ground)
    kb.inline_keyboard.append([InlineKeyboardButton(text="🤲 Всё", callback_data="pickup_all")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("pickup:"))
async def cb_pickup(callback: CallbackQuery):
    item_id = callback.data.split(":")[1]
    user = await ge.get_or_create_user(callback.from_user.id)
    result = await ge.pick_up_item(callback.from_user.id, user["current_location"], item_id)

    await callback.message.edit_text(result["message"], reply_markup=post_action_kb())
    await callback.answer()


@router.callback_query(F.data == "pickup_all")
async def cb_pickup_all(callback: CallbackQuery):
    user = await ge.get_or_create_user(callback.from_user.id)
    ground = await ge.get_ground_items(user["current_location"])

    if not ground:
        await callback.message.edit_text("На земле ничего нет.", reply_markup=back_menu_kb())
        await callback.answer()
        return

    picked = []
    for g in ground:
        result = await ge.pick_up_item(callback.from_user.id, user["current_location"], g["item_id"])
        if result["success"]:
            name = g.get("name") or g["item_id"]
            picked.append(f"{name} x{g['quantity']}")

    text = "🤲 <b>Подобрано:</b>\n\n" + "\n".join(f"• {p}" for p in picked)
    await callback.message.edit_text(text, reply_markup=post_action_kb())
    await callback.answer()


# ──────────────────────────────────────────────
#  Карта / Движение
# ──────────────────────────────────────────────

@router.callback_query(F.data == "locations")
async def cb_locations(callback: CallbackQuery):
    user = await ge.get_or_create_user(callback.from_user.id)
    loc = await ge.get_location(user["current_location"])
    connections = json.loads(loc["connections"]) if isinstance(loc["connections"], str) else loc["connections"]

    text = f"🗺 <b>Выходы из «{loc['name']}»:</b>\n\n"
    for loc_id in connections:
        target = await ge.get_location(loc_id)
        if target:
            icon = "✅" if target["discovered"] else "❓"
            text += f"{icon} {target['name']}\n"

    kb = await nav_kb(connections)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("move:"))
async def cb_move(callback: CallbackQuery):
    target = callback.data.split(":")[1]
    result = await ge.move_user(callback.from_user.id, target)

    if result["success"]:
        text = f"🚶 <b>{result['name']}</b>\n\n{result['description']}"
        if result.get("first_discover"):
            text += "\n\n⚡ <b>Ты первый, кто открыл эту область!</b>"
            await ge.discover_legend(
                f"loc_{target}", "location",
                result["name"], result["description"],
                callback.from_user.id
            )

        # Прогресс квестов
        user_quests = await ge.get_user_quests(callback.from_user.id)
        for uq in user_quests:
            if uq["status"] != "active":
                continue
            objectives = json.loads(uq["objectives"]) if isinstance(uq["objectives"], str) else uq["objectives"]
            for obj in objectives:
                if obj.get("type") == "visit" and obj.get("location") == target:
                    await ge.update_quest_progress(callback.from_user.id, uq["quest_id"], obj["id"])

        loc = await ge.get_location(target)
        connections = json.loads(loc["connections"]) if isinstance(loc["connections"], str) else loc["connections"]

        # Проверяем существ и предметы
        creatures = await ge.get_creatures_at_location(target)
        ground = await ge.get_ground_items(target)

        buttons = []
        for loc_id in connections:
            name = await _loc_name(loc_id)
            buttons.append([InlineKeyboardButton(text=f"🚶 {name}", callback_data=f"move:{loc_id}")])

        if creatures:
            buttons.append([InlineKeyboardButton(text=f"👁 Существа ({len(creatures)})", callback_data="creature_menu")])
        if ground:
            buttons.append([InlineKeyboardButton(text=f"📦 На земле ({len(ground)})", callback_data="ground_menu")])

        buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    else:
        text = result["message"]
        kb = back_menu_kb()

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ──────────────────────────────────────────────
#  Бой
# ──────────────────────────────────────────────

@router.callback_query(F.data == "fight_menu")
async def cb_fight_menu(callback: CallbackQuery):
    user = await ge.get_or_create_user(callback.from_user.id)
    creatures = await ge.get_creatures_at_location(user["current_location"])

    hostile = [c for c in creatures if c["disposition"] in ("hostile", "neutral") and c["is_alive"]]

    if not hostile:
        text = "⚔️ <b>Здесь никого нет для боя.</b>\n\nПопробуй осмотреться или перейти в другое место."
        kb = post_action_kb()
    else:
        text = "⚔️ <b>Кого атакуем?</b>\n\n"
        for c in hostile:
            icon = "🔴" if c["disposition"] == "hostile" else "🟡"
            text += f"{icon} {c['name']} — HP: {c['hp']}, Атака: {c['attack']}\n"
        kb = combat_kb(hostile)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("attack:"))
async def cb_attack(callback: CallbackQuery):
    creature_id = callback.data.split(":")[1]
    result = await ge.start_combat(callback.from_user.id, creature_id)

    if not result["success"]:
        await callback.message.edit_text(result["message"], reply_markup=post_action_kb())
        await callback.answer()
        return

    combat = await ge.resolve_combat(callback.from_user.id, creature_id)

    text = f"⚔️ <b>Бой с {result['creature']['name']}</b>\n\n"

    for rd in combat.get("rounds", [])[:5]:
        ud = rd.get("user_damage", 0)
        cd = rd.get("creature_damage", 0)
        text += f"Раунд {rd['round']}: -{ud} HP, -{cd} HP\n"

    text += f"\n❤️ Твоё HP: {combat['user_hp']}\n"

    if combat["outcome"] == "victory":
        text += f"\n🏆 <b>ПОБЕДА!</b>\n+{combat['xp_gained']} XP"
        if combat["loot"]:
            text += f"\n📦 Лут: {', '.join(combat['loot'])}"
    elif combat["outcome"] == "defeat":
        text += "\n💀 <b>ПОРАЖЕНИЕ</b>\nТы очнулся... где-то раньше."
    else:
        text += "\n🤝 <b>НИЧЬЯ</b>\nОба отступили."

    # Прогресс квестов
    if combat.get("outcome") == "victory":
        user_quests = await ge.get_user_quests(callback.from_user.id)
        for uq in user_quests:
            if uq["status"] != "active":
                continue
            objectives = json.loads(uq["objectives"]) if isinstance(uq["objectives"], str) else uq["objectives"]
            for obj in objectives:
                if obj.get("type") == "kill" and obj.get("creature") == creature_id:
                    await ge.update_quest_progress(callback.from_user.id, uq["quest_id"], obj["id"])

    if combat["outcome"] == "defeat":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
        ])
    else:
        kb = post_action_kb()

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ──────────────────────────────────────────────
#  Исцеление
# ──────────────────────────────────────────────

@router.callback_query(F.data == "heal")
async def cb_heal(callback: CallbackQuery):
    # Сначала пробуем использовать предмет
    user = await ge.get_or_create_user(callback.from_user.id)
    inv = await ge.get_inventory(callback.from_user.id)

    healing_items = [i for i in inv if i["item_id"] in ("healing_herb", "shadow_essence", "frozen_tear")]

    if healing_items:
        item = healing_items[0]
        result = await ge.use_item(callback.from_user.id, item["item_id"])
        text = result["message"]
    else:
        result = await ge.rest_heal(callback.from_user.id)
        text = result["message"]

    kb = post_action_kb()
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ──────────────────────────────────────────────
#  Инвентарь
# ──────────────────────────────────────────────

@router.callback_query(F.data == "inventory")
async def cb_inventory(callback: CallbackQuery):
    items = await ge.get_inventory(callback.from_user.id)

    if not items:
        text = "🎒 <b>Инвентарь пуст</b>\n\nТы ничего не несёшь. Пока."
        kb = back_menu_kb()
    else:
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

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("use_item:"))
async def cb_use_item(callback: CallbackQuery):
    item_id = callback.data.split(":", 1)[1]
    result = await ge.use_item(callback.from_user.id, item_id)
    kb = post_action_kb()
    await callback.message.edit_text(result["message"], reply_markup=kb)
    await callback.answer()


# ──────────────────────────────────────────────
#  Статус
# ──────────────────────────────────────────────

@router.callback_query(F.data == "status")
async def cb_status(callback: CallbackQuery):
    user = await ge.get_or_create_user(callback.from_user.id)
    user_actions = await ge.get_user_actions(callback.from_user.id, limit=1000000)
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
        f"⭐ Уровень: {user['level']} (XP: {user['xp']}/{xp_needed})\n\n"
        f"🎒 Воспоминаний: {user['memories']}\n"
        f"⚖️ Карма: {user['karma']}\n"
        f"📝 Твоих действий: {total}\n"
        f"🌍 Всего в мире: {action_count}"
    )
    await callback.message.edit_text(text, reply_markup=back_menu_kb())
    await callback.answer()


# ──────────────────────────────────────────────
#  Энциклопедия
# ──────────────────────────────────────────────

@router.callback_query(F.data == "legends")
async def cb_legends(callback: CallbackQuery):
    stats = await ge.get_legend_stats()
    text = (
        "🏆 <b>Энциклопедия MIST</b>\n\n"
        f"🐾 Существа: {stats['creatures_found']}\n"
        f"🏺 Предметы: {stats['items_found']}\n"
        f"🗺 Локации: {stats['places_found']}\n"
        f"📜 Легенды: {stats['lore_found']}\n\n"
        "<i>Каждый первый человек, открывший нечто,\nнавсегда вписан в историю.</i>"
    )
    await callback.message.edit_text(text, reply_markup=back_menu_kb())
    await callback.answer()
