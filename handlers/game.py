import json
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
import game_engine as ge

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await ge.get_or_create_user(message.from_user.id, message.from_user.username)

    text = (
        "🌫 *Добро пожаловать в MIST*\n\n"
        "Ты просыпаешься в тумане.\n"
        "Не помнишь, как сюда попал.\n"
        "Рядом — камни, деревья, и что-то шепчет вдали.\n\n"
        "Ты — один из тех, кого MIST выбрал.\n"
        "Здесь каждый шаг имеет значение.\n"
        "Каждое слово. Каждое молчание.\n\n"
        "Туман помнит всё.\n\n"
        "─────────────────\n"
        f"📍 *Локация:* Тёмный лес\n"
        f"🎒 *Воспоминаний:* {user['memories']}\n"
        f"⚖️ *Карма:* {user['karma']}\n\n"
        "Используй /help чтобы узнать команды."
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📋 *Команды MIST*\n\n"
        "🌍 *Исследование:*\n"
        "/look — осмотреться\n"
        "/move — перейти (см. /locations)\n"
        "/locations — список локаций\n\n"
        "⚔️ *Бой:*\n"
        "/fight — показать противников\n"
        "/attack — атаковать существо\n"
        "/heal — восстановить HP\n"
        "/combat_history — история боёв\n\n"
        "📜 *Квесты:*\n"
        "/quests — твои квесты\n"
        "/quest_list — доступные квесты\n"
        "/accept — принять квест\n\n"
        "🎒 *Инвентарь:*\n"
        "/inventory — твой инвентарь\n"
        "/use — использовать предмет\n\n"
        "👤 *Прогресс:*\n"
        "/status — статус персонажа\n"
        "/actions — история действий\n\n"
        "📚 *Энциклопедия:*\n"
        "/legends — что мир уже открыл\n\n"
        "🔮 *Тайны:*\n"
        "/whisper — шёпот тумана\n"
        "/secrets — найденные тайны"
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("look"))
async def cmd_look(message: Message):
    user = await ge.get_or_create_user(message.from_user.id)
    loc = await ge.get_location(user["current_location"])
    creatures = await ge.get_creatures_at_location(user["current_location"])

    text = f"🌍 *{loc['name']}*\n\n{loc['description']}\n"

    if creatures:
        text += "\n👁 *Ты чувствуешь присутствие:*\n"
        for c in creatures:
            text += f"  • {c['name']}\n"

    connections = json.loads(loc["connections"]) if isinstance(loc["connections"], str) else loc["connections"]
    if connections:
        text += f"\n🚪 *Выходы:* {', '.join(connections)}"

    await ge._log_action(message.from_user.id, "look", location=user["current_location"])
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("locations"))
async def cmd_locations(message: Message):
    user = await ge.get_or_create_user(message.from_user.id)
    pool = await ge.get_pool()
    async with pool.acquire() as conn:
        loc = await conn.fetchrow(
            "SELECT connections FROM locations WHERE location_id = $1",
            user["current_location"]
        )
        connections = json.loads(loc["connections"]) if loc and isinstance(loc["connections"], str) else (loc["connections"] if loc else [])

    text = "🗺 *Доступные направления:*\n\n"
    for loc_id in connections:
        loc = await ge.get_location(loc_id)
        if loc:
            status = "✅" if loc["discovered"] else "❓"
            text += f"{status} /move_{loc_id} — {loc['name']}\n"

    await message.answer(text, parse_mode="Markdown")


@router.message(Command("move"))
async def cmd_move(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Куда? Используй /locations чтобы увидеть доступные направления.")
        return

    target = parts[1]
    result = await ge.move_user(message.from_user.id, target)

    if result["success"]:
        text = f"🚶 Ты пришёл в *{result['name']}*\n\n{result['description']}"
        if result.get("first_discover"):
            text += "\n\n⚡ *Ты первый, кто открыл эту область!*"
            await ge.discover_legend(
                f"loc_{target}", "location",
                result["name"], result["description"],
                message.from_user.id
            )

        # Проверяем квесты на посещение локаций
        user_quests = await ge.get_user_quests(message.from_user.id)
        for uq in user_quests:
            if uq["status"] != "active":
                continue
            objectives = json.loads(uq["objectives"]) if isinstance(uq["objectives"], str) else uq["objectives"]
            for obj in objectives:
                if obj.get("type") == "visit" and obj.get("location") == target:
                    await ge.update_quest_progress(
                        message.from_user.id, uq["quest_id"], obj["id"]
                    )
    else:
        text = result["message"]

    await message.answer(text, parse_mode="Markdown")


@router.message(F.text.startswith("/move_"))
async def cmd_move_short(message: Message):
    target = message.text.replace("/move_", "")
    result = await ge.move_user(message.from_user.id, target)

    if result["success"]:
        text = f"🚶 Ты пришёл в *{result['name']}*\n\n{result['description']}"
        if result.get("first_discover"):
            text += "\n\n⚡ *Ты первый, кто открыл эту область!*"
    else:
        text = result["message"]

    await message.answer(text, parse_mode="Markdown")


@router.message(Command("inventory"))
async def cmd_inventory(message: Message):
    items = await ge.get_inventory(message.from_user.id)

    if not items:
        text = "🎒 *Инвентарь пуст*\n\nТы ничего не несёшь. Пока."
    else:
        text = "🎒 *Твой инвентарь:*\n\n"
        for item in items:
            magic = " ✨" if item["is_magic"] else ""
            rarity = f" [{item['rarity']}]" if item.get("rarity") else ""
            text += f"• {item['name'] or item['item_id']} x{item['quantity']}{magic}{rarity}\n"

    await message.answer(text, parse_mode="Markdown")


@router.message(Command("status"))
async def cmd_status(message: Message):
    user = await ge.get_or_create_user(message.from_user.id)
    action_count = await ge.count_actions()
    user_actions = await ge.get_user_actions(message.from_user.id, limit=1000000)
    total = len(user_actions)

    days = user.get("days_in_mist", 0)
    hp_bar = "❤️" * (user["hp"] // 20) + "🖤" * (5 - user["hp"] // 20)

    text = (
        f"👤 *{user['display_name']}*\n\n"
        f"📍 Локация: {user['current_location']}\n"
        f"⏰ Дней в MIST: {days}\n"
        f"🎒 Воспоминаний: {user['memories']}\n"
        f"⚖️ Карма: {user['karma']}\n\n"
        f"⚔️ *Боевые характеристики:*\n"
        f"❤️ HP: {user['hp']}/{user['max_hp']} {hp_bar}\n"
        f"🗡 Атака: {user['attack']}\n"
        f"🛡 Защита: {user['defense']}\n"
        f"⭐ Уровень: {user['level']} (XP: {user['xp']}/{user['level'] * 100})\n\n"
        f"📝 Твоих действий: {total}\n"
        f"🌍 Всего действий в мире: {action_count}"
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("actions"))
async def cmd_actions(message: Message):
    actions = await ge.get_user_actions(message.from_user.id, limit=10)

    if not actions:
        text = "📝 Ты ещё ничего не сделал."
    else:
        text = "📝 *Последние действия:*\n\n"
        type_names = {
            "look": "👀 осмотрелся",
            "move": "🚶 переместился",
            "item_gain": "📦 получил предмет",
            "item_loss": "📭 потерял предмет",
            "location_discover": "🗺 открыл локацию",
            "secret_found": "🔮 нашёл тайну",
            "legend_discover": "📚 открыл легенду",
            "attack": "⚔️ атаковал",
            "feed": "🍖 покормил",
            "new_user": "✨ вошёл в MIST",
            "combat_victory": "🏆 победил в бою",
            "combat_defeat": "💀 проиграл бой",
            "heal": "💚 исцелился",
            "quest_accept": "📜 принял квест",
            "quest_complete": "🏆 выполнил квест",
            "whisper": "🌫 шёпот тумана",
        }
        for a in actions:
            name = type_names.get(a["action_type"], a["action_type"])
            text += f"• {name}\n"

    await message.answer(text, parse_mode="Markdown")


@router.message(Command("legends"))
async def cmd_legends(message: Message):
    stats = await ge.get_legend_stats()

    text = (
        "📚 *Энциклопедия MIST*\n\n"
        f"🐾 Существа: {stats['creatures_found']} найдено\n"
        f"🏺 Предметы: {stats['items_found']} найдено\n"
        f"🗺 Локации: {stats['places_found']} найдено\n"
        f"📜 Легенды: {stats['lore_found']} найдено\n\n"
        "_Каждый первый человек, открывший нечто, навсегда вписан в историю._"
    )
    await message.answer(text, parse_mode="Markdown")
