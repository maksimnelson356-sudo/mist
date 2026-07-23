import json
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
import game_engine as ge

router = Router()


@router.callback_query(F.data == "quests")
async def cb_quests(callback: CallbackQuery):
    user = await ge.get_or_create_user(callback.from_user.id)
    active_quests = await ge.get_user_quests(callback.from_user.id)
    available = await ge.get_available_quests(callback.from_user.id, user["current_location"])

    text = "📜 <b>Квесты</b>\n\n"

    if active_quests:
        text += "<b>Активные:</b>\n"
        for q in active_quests:
            if q["status"] != "active":
                continue
            progress = json.loads(q["progress"]) if isinstance(q["progress"], str) else q["progress"]
            objectives = json.loads(q["objectives"]) if isinstance(q["objectives"], str) else q["objectives"]
            text += f"\n📋 <b>{q['name']}</b>\n"
            for obj in objectives:
                p = progress.get(obj["id"], {"current": 0, "target": obj["target"]})
                done = "✅" if p["current"] >= p["target"] else "⬜"
                text += f"  {done} {obj['description']}: {p['current']}/{p['target']}\n"

    if available:
        text += "\n<b>Доступные здесь:</b>\n"
        for q in available:
            text += f"  📜 {q['name']}\n"

    buttons = []
    if available:
        for q in available:
            buttons.append([InlineKeyboardButton(
                text=f"Принять: {q['name']}",
                callback_data=f"accept:{q['quest_id']}"
            )])
    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("accept:"))
async def cb_accept(callback: CallbackQuery):
    quest_id = callback.data.split(":")[1]
    result = await ge.accept_quest(callback.from_user.id, quest_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Квесты", callback_data="quests")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])

    await callback.message.edit_text(result["message"], reply_markup=kb)
    await callback.answer()
