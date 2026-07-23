import json
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
import game_engine as ge

router = Router()


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


@router.callback_query(F.data == "quests")
async def cb_quests(callback: CallbackQuery):
    user = await ge.get_or_create_user(callback.from_user.id)
    active_quests = await ge.get_user_quests(callback.from_user.id)
    available_here = await ge.get_available_quests(callback.from_user.id, user["current_location"])
    all_available_quests = await ge.get_available_quests(callback.from_user.id)

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
                text += f"  📜 <b>{q['name']}</b>\n"
                text += f"    🗺️ {loc_name}\n"
                for obj in objectives:
                    p = progress.get(obj["id"], {"current": 0, "target": obj["target"]})
                    done = "✅" if p["current"] >= p["target"] else "✨"
                    text += f"    {done} {obj['description']}: {p['current']}/{p['target']}\n"

    if available_here:
        text += "\n<⚡> <b>Доступны здесь:</b>\n"
        for q in available_here:
            text += f"  🌟 {q['name']}\n"

    remote = [q for q in all_available_quests if q["quest_id"] not in active_ids and q["quest_id"] not in available_quest_ids]
    if remote:
        text += "\n<🗺️> <b>Другие квесты:</b>\n"
        for q in remote:
            loc_name = LOC_NAMES.get(q["location"], q["location"])
            text += f"  🌍 {q['name']} <i>({loc_name})</i>\n"

    if not active_quests and not available_here and not remote:
        text += "Пока ничего. Иди исследуй мир — квесты найдутся."

    buttons = []

    if available_here:
        for q in available_here:
            buttons.append([InlineKeyboardButton(
                text=f"📜 Принять: {q['name']}",
                callback_data=f"accept:{q['quest_id']}"
            )])

    nav_targets = set()
    if active_quests:
        active_list = [q for q in active_quests if q["status"] == "active"]
        for q in active_list:
            q_loc = q.get("location", "")
            if q_loc and q_loc != user["current_location"] and q_loc not in nav_targets:
                progress = json.loads(q["progress"]) if isinstance(q["progress"], str) else q["progress"]
                objectives = json.loads(q["objectives"]) if isinstance(q["objectives"], str) else q["objectives"]
                all_done = all(
                    progress.get(obj["id"], {}).get("current", 0) >= obj["target"]
                    for obj in objectives
                )
                next_step = await ge.find_next_step(user["current_location"], q_loc)
                if not next_step:
                    continue
                loc_name = LOC_NAMES.get(q_loc, q_loc)
                next_name = LOC_NAMES.get(next_step, next_step)
                if all_done:
                    buttons.append([InlineKeyboardButton(
                        text=f"🏆 Сдать: {q['name']} → {next_name}",
                        callback_data=f"move:{next_step}"
                    )])
                else:
                    buttons.append([InlineKeyboardButton(
                        text=f"🚶 {q['name']} → {next_name}",
                        callback_data=f"move:{next_step}"
                    )])
                nav_targets.add(q_loc)

    if remote:
        shown = 0
        for q in remote:
            if shown >= 3:
                break
            q_loc = q["location"]
            if q_loc not in nav_targets and q_loc != user["current_location"]:
                next_step = await ge.find_next_step(user["current_location"], q_loc)
                if not next_step:
                    continue
                loc_name = LOC_NAMES.get(q_loc, q_loc)
                next_name = LOC_NAMES.get(next_step, next_step)
                buttons.append([InlineKeyboardButton(
                    text=f"🗺 {q['name']} ({loc_name}) → {next_name}",
                    callback_data=f"move:{next_step}"
                )])
                nav_targets.add(q_loc)
                shown += 1

    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("accept:"))
async def cb_accept(callback: CallbackQuery):
    quest_id = callback.data.split(":")[1]
    result = await ge.accept_quest(callback.from_user.id, quest_id)

    text = result["message"]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Квесты", callback_data="quests")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
