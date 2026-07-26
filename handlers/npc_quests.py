from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from services.container import services

router = Router()


@router.callback_query(F.data.startswith("npc_quests:"))
async def cb_npc_quests(callback: CallbackQuery):
    npc_id = callback.data.split(":", 1)[1]
    npc = await services.npc.get(npc_id)
    if not npc:
        await callback.answer("NPC не найден.", show_alert=True)
        return

    user = await services.player.get(callback.from_user.id)
    location_id = user.get("current_location", "")

    quests = await services.npc_quest.get_available_npc_quests(location_id)
    npc_quests = [q for q in quests if q["giver"] == npc["name"]]

    text = f"📜 <b>Квесты от {npc['name']}</b>\n\n"
    if not npc_quests:
        text += "Нет доступных квестов."
    else:
        for q in npc_quests:
            text += f"📋 {q['name']}\n   {q['description']}\n\n"

    buttons = []
    for q in npc_quests:
        buttons.append([InlineKeyboardButton(
            text=f"📋 {q['name']}",
            callback_data=f"npc_quest_accept:{npc_id}:{q['quest_id']}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"npc_talk:{npc_id}")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data.startswith("npc_quest_accept:"))
async def cb_npc_quest_accept(callback: CallbackQuery):
    parts = callback.data.split(":", 2)
    npc_id = parts[1]
    quest_id = parts[2]

    result = await services.quest.accept(callback.from_user.id, quest_id)

    if result["success"]:
        text = f"✅ Квест принят!\n\n{result.get('message', '')}"
    else:
        text = f"❌ {result['message']}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"npc_talk:{npc_id}")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
