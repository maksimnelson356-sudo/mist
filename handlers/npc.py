from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from services.container import services

router = Router()


@router.message(Command("npc"))
async def cmd_npc_list(message: Message):
    if message.chat.type != "private":
        return

    user = await services.player.get_or_create(message.from_user.id)
    npcs = await services.npc.get_at_location(user["current_location"])

    if not npcs:
        await message.answer("Здесь нет NPC.")
        return

    text = "👥 <b>Жители этой области:</b>\n\n"
    buttons = []

    for npc in npcs:
        from services.npc_service import NPC_TYPES
        npc_type = NPC_TYPES.get(npc["npc_type"], {})
        icon = npc_type.get("icon", "❓")
        state_icon = {"idle": "🟢", "talking": "💬", "trading": "🛒", "sleeping": "😴"}.get(npc.get("state", "idle"), "⚪")

        text += f"{icon} <b>{npc['name']}</b> [{state_icon}]\n"
        text += f"   {npc.get('description', 'Без описания')[:60]}...\n\n"

        buttons.append([InlineKeyboardButton(
            text=f"{icon} {npc['name']}",
            callback_data=f"npc_talk:{npc['npc_id']}"
        )])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("npc_talk:"))
async def cb_npc_talk(callback: CallbackQuery):
    npc_id = callback.data.split(":", 1)[1]

    user = await services.player.get_or_create(callback.from_user.id)
    result = await services.npc.interact(callback.from_user.id, npc_id)

    if not result["success"]:
        await callback.answer(result["message"], show_alert=True)
        return

    await services.npc_memory.update(npc_id, callback.from_user.id, "talked")

    text = (
        f"{result['icon']} <b>{result['name']}</b>\n"
        f"Тип: {result['type']} | Состояние: {result['state']}\n\n"
        f"{result['message']}"
    )

    buttons = []
    if result.get("can_trade"):
        buttons.append([InlineKeyboardButton(text="🛒 Торговать", callback_data=f"npc_trade:{npc_id}")])
    if result.get("can_give_quests"):
        buttons.append([InlineKeyboardButton(text="📜 Квесты", callback_data=f"npc_quests:{npc_id}")])
    if result.get("can_heal"):
        buttons.append([InlineKeyboardButton(text="💚 Исцелить", callback_data=f"npc_heal:{npc_id}")])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("npc_heal:"))
async def cb_npc_heal(callback: CallbackQuery):
    npc_id = callback.data.split(":", 1)[1]
    result = await services.player.rest_heal(callback.from_user.id)
    await services.npc_memory.update(npc_id, callback.from_user.id, "helped")
    await callback.answer(result["message"], show_alert=True)
