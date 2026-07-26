from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from services.container import services
from services.npc_service import NPC_TYPES

router = Router()


@router.callback_query(F.data.startswith("dialogue_start:"))
async def cb_dialogue_start(callback: CallbackQuery):
    npc_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id

    npc = await services.npc.get(npc_id)
    if not npc:
        await callback.answer("NPC не найден.", show_alert=True)
        return

    npc_type = npc.get("npc_type", "quest_giver")
    dialogue = await services.dialogue.get_dialogue(npc_id, npc_type, user_id)

    type_info = NPC_TYPES.get(npc_type, {})
    icon = type_info.get("icon", "🗣")

    text = f"{icon} <b>{npc['name']}</b>\n\n{dialogue['text']}"

    buttons = []
    for _i, opt in enumerate(dialogue.get("options", [])):
        buttons.append([InlineKeyboardButton(
            text=opt["text"],
            callback_data=f"dialogue:{npc_type}:{opt.get('next', 'end')}:{npc_id}"
        )])

    if not buttons:
        buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="creature_menu")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data.startswith("dialogue:"))
async def cb_dialogue_continue(callback: CallbackQuery):
    parts = callback.data.split(":")
    npc_type = parts[1]
    choice_id = parts[2]
    npc_id = parts[3] if len(parts) > 3 else None
    user_id = callback.from_user.id

    if choice_id == "end":
        await callback.message.edit_text("Диалог завершён.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="creature_menu")],
        ]))
        return

    result = await services.dialogue.continue_dialogue(npc_type, choice_id, user_id)

    npc = await services.npc.get(npc_id) if npc_id else None
    npc_name = npc["name"] if npc else "NPC"
    type_info = NPC_TYPES.get(npc_type, {})
    icon = type_info.get("icon", "🗣")

    text = f"{icon} <b>{npc_name}</b>\n\n{result['text']}"

    buttons = []
    for opt in result.get("options", []):
        buttons.append([InlineKeyboardButton(
            text=opt["text"],
            callback_data=f"dialogue:{npc_type}:{opt.get('next', 'end')}:{npc_id}"
        )])

    if not buttons:
        buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="creature_menu")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
