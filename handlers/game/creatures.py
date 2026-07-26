from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from services.container import services
from scenes import CREATURE_SCENES, SCENE_DIVIDER
from . import _shared as G

router = G.router


@router.callback_query(F.data == "creature_menu")
async def cb_creature_menu(callback: CallbackQuery):
    user = await services.player.get_or_create(callback.from_user.id)
    creatures = await services.movement.get_creatures_at(user["current_location"])

    if not creatures:
        await callback.message.edit_text("Здесь никого нет.", reply_markup=G.back_menu_kb())
        return

    text = "👁 <b>К кому подойти?</b>\n\n"
    for c in creatures:
        icon = {"hostile": "⚔️", "neutral": "🗣", "friendly": "💚"}.get(c["disposition"], "❓")
        text += f"{icon} {c['name']}\n"

    await callback.message.edit_text(text, reply_markup=G.creature_action_kb(creatures))


@router.callback_query(F.data.startswith("creature_action:"))
async def cb_creature_action(callback: CallbackQuery):
    creature_id = callback.data.split(":")[1]
    user = await services.player.get_or_create(callback.from_user.id)
    creatures = await services.movement.get_creatures_at(user["current_location"])
    creature = next((c for c in creatures if c["creature_id"] == creature_id), None)

    if not creature or not creature["is_alive"]:
        await callback.message.edit_text("Этого существа здесь нет.", reply_markup=G.back_menu_kb())
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


@router.callback_query(F.data.startswith("talk:"))
async def cb_talk(callback: CallbackQuery):
    creature_id = callback.data.split(":")[1]
    result = await services.movement.talk_to_creature(callback.from_user.id, creature_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="creature_menu")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
    ])

    await callback.message.edit_text(result["message"], reply_markup=kb)
