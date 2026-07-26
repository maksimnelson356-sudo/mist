from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from services.container import services
from scenes import LOC_SCENES, SCENE_DIVIDER
from . import _shared as G

router = G.router


@router.callback_query(F.data == "look")
async def cb_look(callback: CallbackQuery):
    user = await services.player.get_or_create(callback.from_user.id)
    if not user["is_alive"]:
        await callback.message.edit_text("💀 Ты мёртв.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
        ]))
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
    try:
        from services.npc_life_engine import get_npc_location_bonuses
        npc_bonuses = await get_npc_location_bonuses(user["current_location"])
        if npc_bonuses["danger_reduction"] > 0:
            danger = max(0, danger - npc_bonuses["danger_reduction"])
    except Exception:
        pass
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
        name = await G._loc_name(loc_id)
        buttons.append([InlineKeyboardButton(text=f"🚶 {name}", callback_data=f"move:{loc_id}")])

    if creatures:
        buttons.append([InlineKeyboardButton(text=f"👁 Взаимодействие ({len(creatures)})", callback_data="creature_menu")])

    if ground:
        buttons.append([InlineKeyboardButton(text=f"📦 Подобрать ({len(ground)})", callback_data="ground_menu")])

    if danger > 0:
        buttons.append([InlineKeyboardButton(text="🔧 Восстановить локацию", callback_data=f"restore_loc:{user['current_location']}")])

    try:
        memories = await services.world_memory.get_memories_at_location(user["current_location"], limit=3)
        if memories:
            mem_icons = {"battle": "⚔️", "discovery": "✨", "death": "💀", "construction": "🏗",
                         "trade": "🤝", "quest_complete": "📜", "npc_death": "☠️", "guild_action": "🏰",
                         "world_event": "🌍", "artifact_found": "💎", "player_death": "🩸", "home_built": "🏠"}
            text += "\n\n🌫 <b>Воспоминания места:</b>\n"
            for m in memories:
                icon = mem_icons.get(m["type"], "💭")
                desc = m.get("description", "") or m["title"]
                if len(desc) > 60:
                    desc = desc[:57] + "..."
                text += f"  {icon} <i>{desc}</i>\n"
    except Exception:
        pass

    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        await callback.message.answer(text, reply_markup=kb)


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

    kb = await G.nav_kb(connections)
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.startswith("move:"))
async def cb_move(callback: CallbackQuery):
    user = await services.player.get_or_create(callback.from_user.id)
    if not user["is_alive"]:
        await callback.message.edit_text("💀 Ты мёртв.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
        ]))
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
            name = await G._loc_name(loc_id)
            buttons.append([InlineKeyboardButton(text=f"🚶 {name}", callback_data=f"move:{loc_id}")])

        if creatures:
            buttons.append([InlineKeyboardButton(text=f"👁 Существа ({len(creatures)})", callback_data="creature_menu")])
        if ground:
            buttons.append([InlineKeyboardButton(text=f"📦 На земле ({len(ground)})", callback_data="ground_menu")])

        buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    else:
        text = result["message"]
        kb = G.back_menu_kb()

    await callback.message.edit_text(text, reply_markup=kb)
