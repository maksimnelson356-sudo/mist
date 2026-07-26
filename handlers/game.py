import json
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart
from services.container import services
from scenes import LOC_SCENES, CREATURE_SCENES, SCENE_DIVIDER

router = Router()


def is_my_message(message: Message, bot_username: str) -> bool:
    if message.chat.type == "private":
        return True
    if message.text and message.text.startswith("/"):
        cmd = message.text.split()[0].lstrip("/")
        if "@" in cmd:
            return cmd.split("@")[1].lower() == bot_username.lower()
        return False
    if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.username:
        return message.reply_to_message.from_user.username.lower() == bot_username.lower()
    return False


async def _loc_name(loc_id: str) -> str:
    loc = await services.movement.get_location(loc_id)
    return loc["name"] if loc else loc_id


# ─── Клавиатуры ───

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


# ──────────────────────────────────────────────
#  Старт
# ──────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, bot_username: str):
    if not is_my_message(message, bot_username):
        return

    if message.chat.type != "private":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌫 Начать игру", url=f"https://t.me/{bot_username}?start=start")]
        ])
        await message.answer(
            "🌫 <b>MIST</b> — текстовый квест в тумане.\n\n"
            "Играй в личных сообщениях!",
            reply_markup=kb
        )
        return

    user = await services.player.get_or_create(message.from_user.id, message.from_user.username)

    if not user["is_alive"]:
        text = (
            "<pre>💀\n🕯️👁🕯️\n💀</pre>\n"
            "💀 <b>Ты мёртв.</b>\n\n"
            "Туман накрыл тебя. Но он не отпускает.\n"
            "Ты чувствуешь — ты ещё нужен."
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
        ])
        await message.answer(text, reply_markup=kb)
        return

    loc = await services.movement.get_location(user["current_location"])
    loc_name = loc["name"] if loc else await services.movement.get_location_name(user["current_location"])
    scene = LOC_SCENES.get(user["current_location"], "")
    text = ""
    if scene:
        text += f"<pre>{scene}</pre>\n{SCENE_DIVIDER}\n"
    text += (
        "🌫 <b>Добро пожаловать в MIST</b>\n\n"
        "Ты просыпаешься в тумане.\n"
        "Не помнишь, как сюда попал.\n\n"
        "Туман помнит всё.\n\n"
        f"📍 <b>{loc_name}</b>\n"
        f"❤️ HP: {user['hp']}/{user['max_hp']} | ⭐ Ур. {user['level']}\n"
        f"🍖 Голод: {user.get('hunger', 100)}/{user.get('max_hunger', 100)}\n"
        f"🪙 Золото: {user['gold']} | 🎒 Воспоминаний: {user['memories']}\n\n"
        "<i>Нажми 🔍 Осмотреться чтобы увидеть выходы</i>"
    )
    await message.answer(text, reply_markup=main_menu_kb())


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def group_mention(message: Message, bot_username: str):
    if not message.text:
        return
    text_lower = message.text.lower()
    if f"@{bot_username.lower()}" not in text_lower and not (
        message.reply_to_message and message.reply_to_message.from_user
        and message.reply_to_message.from_user.username
        and message.reply_to_message.from_user.username.lower() == bot_username.lower()
    ):
        return

    import random
    whispers = [
        "Туман шепчет... <i>«Играй в личке...»</i>",
        "Из глубины тумана: <i>«/start в личных сообщениях...»</i>",
        "Голос из пустоты: <i>«MIST ждёт тебя в личке...»</i>",
        "Шёпот: <i>«Ты не можешь играть здесь. Туман ведёт к другому входу...»</i>",
    ]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌫 Начать игру", url=f"https://t.me/{bot_username}?start=start")]
    ])

    await message.answer(random.choice(whispers), reply_markup=kb)


@router.callback_query(F.data == "revive")
async def cb_revive(callback: CallbackQuery):
    result = await services.player.revive(callback.from_user.id)
    if result["success"]:
        user = await services.player.get_or_create(callback.from_user.id)
        loc = await services.movement.get_location(user["current_location"])
        loc_name = loc["name"] if loc else await services.movement.get_location_name(user["current_location"])
        text = result["message"] + f"\n\n📍 <b>{loc_name}</b>"
        kb = main_menu_kb()
    else:
        text = result["message"]
        kb = back_menu_kb()
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    user = await services.player.get_or_create(callback.from_user.id, callback.from_user.username)
    await services.player.update_last_seen(callback.from_user.id)

    if not user["is_alive"]:
        text = "<pre>💀\n🕯️👁🕯️\n💀</pre>\n💀 <b>Ты мёртв.</b>\n\nТуман накрыл тебя."
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
        ])
        await callback.message.edit_text(text, reply_markup=kb)
        await callback.answer()
        return

    catchup = await services.player.get_catchup_summary(callback.from_user.id)

    loc = await services.movement.get_location(user["current_location"])
    scene = LOC_SCENES.get(user["current_location"], "")
    text = ""
    if scene:
        text += f"<pre>{scene}</pre>\n{SCENE_DIVIDER}\n"

    if catchup:
        season_names = {"spring": "Весна", "summer": "Лето", "autumn": "Осень", "winter": "Зима"}
        season = season_names.get(catchup["season"], catchup["season"])
        text += f"⏰ <b>Пока тебя не было: {catchup['game_days_away']} дн.</b>\n"
        text += f"🌍 Мир: День {catchup['world_day']}, {season}\n"

        if catchup.get("events"):
            text += "\n<b>Что произошло:</b>\n"
            for ev in catchup["events"][:5]:
                text += f"  📜 {ev['name']}\n"
        else:
            text += "\nНичего особенного не случилось.\n"

        if catchup.get("location"):
            loc_data = catchup["location"]
            text += f"\n📍 Локация: {loc_data['name']}\n"
            text += f"  ⚠️ Опасность: {loc_data['danger_level']} | 🍖 Еда: {loc_data['food_supply']}\n"
        text += "\n"

    text += (
        f"📍 <b>{loc_name}</b>\n"
        f"❤️ HP: {user['hp']}/{user['max_hp']} | ⭐ Ур. {user['level']}\n"
        f"🍖 Голод: {user.get('hunger', 100)}/{user.get('max_hunger', 100)}\n"
        f"🎒 Воспоминаний: {user['memories']} | ⚖️ Карма: {user['karma']}"
    )
    await callback.message.edit_text(text, reply_markup=main_menu_kb())
    await callback.answer()


# ──────────────────────────────────────────────
#  Осмотреться
# ──────────────────────────────────────────────

@router.callback_query(F.data == "look")
async def cb_look(callback: CallbackQuery):
    user = await services.player.get_or_create(callback.from_user.id)
    if not user["is_alive"]:
        await callback.message.edit_text("💀 Ты мёртв.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
        ]))
        await callback.answer()
        return
    loc = await services.movement.get_location(user["current_location"])
    creatures = await services.movement.get_creatures_at(user["current_location"])
    ground = await services.movement.get_ground_items(user["current_location"])

    scene = LOC_SCENES.get(user["current_location"], "")
    text = ""
    if scene:
        text += f"<pre>{scene}</pre>\n{SCENE_DIVIDER}\n"
    loc_name = loc["name"] if loc else await services.movement.get_location_name(user["current_location"])
    text += f"🌍 <b>{loc_name}</b>\n\n{loc.get('description', '') if loc else ''}\n"

    weather = loc.get("current_weather", "clear") if loc else "clear"
    from services.weather_system import WEATHER_STATES
    w_info = WEATHER_STATES.get(weather, WEATHER_STATES["clear"])
    text += f"\n{w_info['icon']} <i>{w_info['name']}</i>\n"

    danger = loc.get("danger_level", 0) if loc else 0
    if danger > 0:
        danger_icon = "🔴" if danger >= 50 else "🟡" if danger >= 20 else "🟢"
        text += f"\n{danger_icon} Опасность: {danger}\n"

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

    connections = loc.get("connections", []) if loc else []
    if connections:
        text += "\n🚪 <b>Выходы:</b>\n"
        for loc_id in connections:
            target = await services.movement.get_location(loc_id)
            if target:
                text += f"  • {target['name']}\n"

    buttons = []
    for loc_id in connections:
        name = await _loc_name(loc_id)
        buttons.append([InlineKeyboardButton(text=f"🚶 {name}", callback_data=f"move:{loc_id}")])

    if creatures:
        buttons.append([InlineKeyboardButton(text=f"👁 Взаимодействие ({len(creatures)})", callback_data="creature_menu")])

    if ground:
        buttons.append([InlineKeyboardButton(text=f"📦 Подобрать ({len(ground)})", callback_data="ground_menu")])

    if danger > 0:
        buttons.append([InlineKeyboardButton(text="🔧 Восстановить локацию", callback_data=f"restore_loc:{user['current_location']}")])

    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ──────────────────────────────────────────────
#  Взаимодействие с существами
# ──────────────────────────────────────────────

@router.callback_query(F.data == "creature_menu")
async def cb_creature_menu(callback: CallbackQuery):
    user = await services.player.get_or_create(callback.from_user.id)
    creatures = await services.movement.get_creatures_at(user["current_location"])

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
    user = await services.player.get_or_create(callback.from_user.id)
    creatures = await services.movement.get_creatures_at(user["current_location"])
    creature = next((c for c in creatures if c["creature_id"] == creature_id), None)

    if not creature or not creature["is_alive"]:
        await callback.message.edit_text("Этого существа здесь нет.", reply_markup=back_menu_kb())
        await callback.answer()
        return

    icon = {"hostile": "🔴", "neutral": "🟡", "friendly": "🟢"}.get(creature["disposition"], "⚪")
    scene = CREATURE_SCENES.get(creature_id, "")
    text = ""
    if scene:
        text += f"<pre>{scene}</pre>\n{SCENE_DIVIDER}\n"
    text += f"{icon} <b>{creature['name']}</b>\n\n{creature['description']}\n"

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
    result = await services.movement.talk_to_creature(callback.from_user.id, creature_id)

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
    user = await services.player.get_or_create(callback.from_user.id)
    ground = await services.movement.get_ground_items(user["current_location"])

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
    user = await services.player.get_or_create(callback.from_user.id)
    result = await services.movement.pick_up_item(callback.from_user.id, user["current_location"], item_id)

    if result["success"]:
        user_quests = await services.quest.get_user_quests(callback.from_user.id)
        for uq in user_quests:
            if uq["status"] != "active":
                continue
            objectives = uq.get("objectives", [])
            for obj in objectives:
                if obj.get("type") == "collect" and obj.get("item") == item_id:
                    await services.quest.update_progress(callback.from_user.id, uq["quest_id"], obj["id"])

    await callback.message.edit_text(result["message"], reply_markup=post_action_kb())
    await callback.answer()


@router.callback_query(F.data == "pickup_all")
async def cb_pickup_all(callback: CallbackQuery):
    user = await services.player.get_or_create(callback.from_user.id)
    ground = await services.movement.get_ground_items(user["current_location"])

    if not ground:
        await callback.message.edit_text("На земле ничего нет.", reply_markup=back_menu_kb())
        await callback.answer()
        return

    picked = []
    for g in ground:
        result = await services.movement.pick_up_item(callback.from_user.id, user["current_location"], g["item_id"])
        if result["success"]:
            name = g.get("name") or g["item_id"]
            picked.append(f"{name} x{g['quantity']}")

            user_quests = await services.quest.get_user_quests(callback.from_user.id)
            for uq in user_quests:
                if uq["status"] != "active":
                    continue
                objectives = uq.get("objectives", [])
                for obj in objectives:
                    if obj.get("type") == "collect" and obj.get("item") == g["item_id"]:
                        await services.quest.update_progress(callback.from_user.id, uq["quest_id"], obj["id"])

    text = "🤲 <b>Подобрано:</b>\n\n" + "\n".join(f"• {p}" for p in picked)
    await callback.message.edit_text(text, reply_markup=post_action_kb())
    await callback.answer()


# ──────────────────────────────────────────────
#  Карта / Движение
# ──────────────────────────────────────────────

@router.callback_query(F.data == "locations")
async def cb_locations(callback: CallbackQuery):
    user = await services.player.get_or_create(callback.from_user.id)
    loc = await services.movement.get_location(user["current_location"])
    loc_name = loc["name"] if loc else await services.movement.get_location_name(user["current_location"])
    connections = loc.get("connections", []) if loc else []

    text = f"🗺 <b>Выходы из «{loc_name}»:</b>\n\n"
    for loc_id in connections:
        target = await services.movement.get_location(loc_id)
        if target:
            icon = "✅" if target["discovered"] else "❓"
            text += f"{icon} {target['name']}\n"

    kb = await nav_kb(connections)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("move:"))
async def cb_move(callback: CallbackQuery):
    user = await services.player.get_or_create(callback.from_user.id)
    if not user["is_alive"]:
        await callback.message.edit_text("💀 Ты мёртв.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
        ]))
        await callback.answer()
        return
    target = callback.data.split(":")[1]
    result = await services.movement.move(callback.from_user.id, target)

    if result["success"]:
        scene = LOC_SCENES.get(target, "")
        text = ""
        if scene:
            text += f"<pre>{scene}</pre>\n{SCENE_DIVIDER}\n"
        text += f"🚶 <b>{result['name']}</b>\n\n{result['description']}"
        if result.get("first_discover"):
            text += "\n\n⚡ <b>Ты первый, кто открыл эту область!</b>"
            await services.quest.discover_legend(
                f"loc_{target}", "location",
                result["name"], result.get("description", ""),
                callback.from_user.id
            )

        user_quests = await services.quest.get_user_quests(callback.from_user.id)
        for uq in user_quests:
            if uq["status"] != "active":
                continue
            objectives = uq.get("objectives", [])
            for obj in objectives:
                if obj.get("type") == "visit" and obj.get("location") == target:
                    await services.quest.update_progress(callback.from_user.id, uq["quest_id"], obj["id"])

        loc = await services.movement.get_location(target)
        connections = loc.get("connections", []) if loc else []

        creatures = await services.movement.get_creatures_at(target)
        ground = await services.movement.get_ground_items(target)

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
    user = await services.player.get_or_create(callback.from_user.id)
    if not user["is_alive"]:
        await callback.message.edit_text("💀 Ты мёртв.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
        ]))
        await callback.answer()
        return
    creatures = await services.movement.get_creatures_at(user["current_location"])

    hostile = [c for c in creatures if c["disposition"] in ("hostile", "neutral") and c["is_alive"]]

    if not hostile:
        text = "⚔️ <b>Здесь никого нет для боя.</b>\n\nПопробуй осмотреться или перейти в другое место."
        kb = post_action_kb()
    else:
        text = "⚔️ <b>Кого атакуем?</b>\n\n"
        for c in hostile:
            icon = "🔴" if c["disposition"] == "hostile" else "🟡"
            scene = CREATURE_SCENES.get(c["creature_id"], "")
            if scene:
                text += f"<pre>{scene}</pre>\n"
            text += f"{icon} {c['name']} — HP: {c['hp']}, Атака: {c['attack']}\n\n"
        kb = combat_kb(hostile)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("attack:"))
async def cb_attack(callback: CallbackQuery):
    creature_id = callback.data.split(":")[1]
    result = await services.combat.start(callback.from_user.id, creature_id)

    if not result["success"]:
        await callback.message.edit_text(result["message"], reply_markup=post_action_kb())
        await callback.answer()
        return

    combat = await services.combat.resolve(callback.from_user.id, creature_id)

    scene = CREATURE_SCENES.get(creature_id, "")
    text = ""
    if scene:
        text += f"<pre>{scene}</pre>\n{SCENE_DIVIDER}\n"
    text += f"⚔️ <b>Бой с {result['creature']['name']}</b>\n\n"

    for rd in combat.get("rounds", [])[:5]:
        ud = rd.get("user_damage", 0)
        cd = rd.get("creature_damage", 0)
        text += f"Раунд {rd['round']}: -{ud} HP, -{cd} HP\n"

    text += f"\n❤️ Твоё HP: {combat['user_hp']}\n"

    if combat["outcome"] == "victory":
        text += "\n<pre>🏆⚔️🏆\n🔥🐺🔥\n🏆⚔️🏆</pre>\n"
        text += f"🏆 <b>ПОБЕДА!</b>\n+{combat['xp_gained']} XP"
        if combat.get("leveled"):
            text += f"\n\n<pre>⭐\n🔥⚔️🔥\n⭐</pre>\n⭐ <b>УРОВЕНЬ → {combat['new_level']}</b>!"
        if combat.get("gold_gained"):
            text += f"\n+{combat['gold_gained']} 🪙"
        if combat["loot"]:
            text += f"\n📦 Лут: {', '.join(combat['loot'])}"
    elif combat["outcome"] == "defeat":
        text += "\n<pre>💀\n🕯️👁🕯️\n💀</pre>\n"
        text += "\n💀 <b>ПОРАЖЕНИЕ</b>\nТы очнулся... где-то раньше."
    else:
        text += "\n🤝 <b>НИЧЬЯ</b>\nОба отступили."

    if combat.get("outcome") == "victory":
        user_quests = await services.quest.get_user_quests(callback.from_user.id)
        for uq in user_quests:
            if uq["status"] != "active":
                continue
            objectives = uq.get("objectives", [])
            for obj in objectives:
                if obj.get("type") == "kill" and obj.get("creature") == creature_id:
                    await services.quest.update_progress(callback.from_user.id, uq["quest_id"], obj["id"])

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
    user = await services.player.get_or_create(callback.from_user.id)

    if not user["is_alive"]:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
        ])
        await callback.message.edit_text("💀 Ты мёртв. Очнись сначала.", reply_markup=kb)
        await callback.answer()
        return

    inv = await services.inventory.get(callback.from_user.id)

    healing_items = [i for i in inv if i["item_id"] in ("healing_herb", "shadow_essence", "frozen_tear")]

    if healing_items:
        item = healing_items[0]
        result = await services.inventory.use_item(callback.from_user.id, item["item_id"])
        text = result["message"]
    else:
        result = await services.player.rest_heal(callback.from_user.id)
        text = result["message"]

    kb = post_action_kb()
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


FOOD_HUNGER = {
    "bread": 20, "fish": 25, "apple": 15, "cheese": 30,
    "dried_meat": 35, "berry": 10,
}


@router.callback_query(F.data == "eat_food")
async def cb_eat_food(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await services.player.get_or_create(user_id)

    if not user["is_alive"]:
        await callback.answer("💀 Ты мёртв.", show_alert=True)
        return

    inventory = await services.inventory.get(user_id)
    food_items = [i for i in inventory if i["item_id"] in FOOD_HUNGER]

    if not food_items:
        await callback.answer("Нет еды в инвентаре! Купи на рынке.", show_alert=True)
        return

    buttons = []
    for item in food_items:
        hunger_restore = FOOD_HUNGER[item["item_id"]]
        qty = item.get("quantity", 1)
        buttons.append([InlineKeyboardButton(
            text=f"🍖 {item['name']} ×{qty} (+{hunger_restore} 🍖)",
            callback_data=f"eat:{item['item_id']}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")])

    text = "🍖 <b>Поесть</b>\n\nВыбери еду:"
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("eat:"))
async def cb_eat(callback: CallbackQuery):
    item_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id

    if not await services.inventory.has(user_id, item_id):
        await callback.answer("Предмет не найден!", show_alert=True)
        return

    hunger_restore = FOOD_HUNGER.get(item_id, 10)
    await services.inventory.remove(user_id, item_id)
    result = await services.player.feed(user_id, hunger_restore)

    await callback.answer(result["message"], show_alert=True)
    await cb_main_menu(callback)


# ──────────────────────────────────────────────
#  Инвентарь
# ──────────────────────────────────────────────

@router.callback_query(F.data == "inventory")
async def cb_inventory(callback: CallbackQuery):
    items = await services.inventory.get(callback.from_user.id)

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
    result = await services.inventory.use_item(callback.from_user.id, item_id)
    kb = post_action_kb()
    await callback.message.edit_text(result["message"], reply_markup=kb)
    await callback.answer()


# ──────────────────────────────────────────────
#  Статус
# ──────────────────────────────────────────────

@router.callback_query(F.data == "status")
async def cb_status(callback: CallbackQuery):
    user = await services.player.get_or_create(callback.from_user.id)
    days = user.get("days_in_mist", 0)
    xp_needed = user["level"] * 100

    loc_name = await services.movement.get_location_name(user["current_location"])
    loc = await services.movement.get_location(user["current_location"])
    weather = loc.get("current_weather", "clear") if loc else "clear"
    from services.weather_system import WEATHER_STATES
    from services.time_system import TIME_PERIODS
    w_info = WEATHER_STATES.get(weather, WEATHER_STATES["clear"])

    text = (
        f"👤 <b>{user['display_name']}</b>\n\n"
        f"📍 Локация: {loc_name}\n"
        f"{w_info['icon']} Погода: {w_info['name']}\n"
        f"⏰ Дней в MIST: {days}\n\n"
        f"❤️ HP: {user['hp']}/{user['max_hp']}\n"
        f"🗡 Атака: {user['attack']}\n"
        f"🛡 Защита: {user['defense']}\n"
        f"⭐ Уровень: {user['level']} (XP: {user['xp']}/{xp_needed})\n"
        f"🪙 Золото: {user['gold']}\n\n"
        f"🎒 Воспоминаний: {user['memories']}\n"
        f"⚖️ Карма: {user['karma']}"
    )
    await callback.message.edit_text(text, reply_markup=back_menu_kb())
    await callback.answer()


# ──────────────────────────────────────────────
#  Энциклопедия
# ──────────────────────────────────────────────

@router.callback_query(F.data == "legends")
async def cb_legends(callback: CallbackQuery):
    stats = await services.quest.get_legend_stats()
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


# ──────────────────────────────────────────────
#  /trade — быстрый трейд
# ──────────────────────────────────────────────

from aiogram.filters import Command

@router.message(Command("trade"))
async def cmd_trade(message: Message):
    if message.chat.type != "private":
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer(
            "📝 <b>Использование:</b>\n"
            "<code>/trade ID золото предмет:кол-во предмет:кол-во</code>\n\n"
            "<i>Пример:\n/trade 123456 10 wolf_fang:3 old_coin:2</i>",
            reply_markup=back_menu_kb()
        )
        return

    try:
        target_id = int(parts[1])
        gold = int(parts[2])
    except ValueError:
        await message.answer("Неверный формат. ID и золото должны быть числами.")
        return

    items_offered = []
    for part in parts[3:]:
        if ":" in part:
            item_id, qty = part.split(":", 1)
            items_offered.append({"item_id": item_id, "qty": int(qty)})
        else:
            items_offered.append({"item_id": part, "qty": 1})

    result = await services.trade.create(
        message.from_user.id, target_id,
        items_offered, gold, [], 0
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤝 Трейдинг", callback_data="trade_menu")],
    ])
    await message.answer(result["message"], reply_markup=kb)
