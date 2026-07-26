from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from services.container import services

router = Router()


@router.callback_query(F.data == "faction_menu")
async def cb_faction_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    factions = await services.faction.get_all_factions()
    player_factions = await services.faction.get_player_factions(user_id)
    faction_map = {pf["faction_id"]: pf for pf in player_factions}

    text = "🏴 <b>Фракции мира MIST</b>\n\n"

    buttons = []
    for f in factions:
        pf = faction_map.get(f["id"])
        if pf:
            status = f"✅ Ур. репутации: {pf['reputation']} ({pf['rank']})"
        else:
            status = "⬜ Не в фракции"

        text += f"{f['icon']} <b>{f['name']}</b>\n"
        text += f"   {status}\n\n"

        buttons.append([InlineKeyboardButton(
            text=f"{f['icon']} {f['name']}",
            callback_data=f"faction_view:{f['id']}"
        )])

    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("faction_view:"))
async def cb_faction_view(callback: CallbackQuery):
    faction_id = callback.data.split(":")[1]
    user_id = callback.from_user.id

    info = await services.faction.get_faction_info(faction_id)
    if not info:
        await callback.answer("Фракция не найдена.", show_alert=True)
        return

    player_factions = await services.faction.get_player_factions(user_id)
    pf = next((pf for pf in player_factions if pf["faction_id"] == faction_id), None)

    loc_name = await services.movement.get_location_name(info["location"])

    text = (
        f"{info['icon']} <b>{info['name']}</b>\n\n"
        f"{info['description']}\n\n"
        f"📍 Локация: {loc_name}\n"
        f"👥 Участников: {info['member_count']}\n\n"
    )

    if pf:
        text += f"📊 Твоя репутация: {pf['reputation']} ({pf['rank']})\n"
        text += f"📅 Вступил: {pf['joined_at'].strftime('%d.%m.%Y') if pf['joined_at'] else '?'}\n"

        buttons = [
            [InlineKeyboardButton(text="📈 Репутация +10", callback_data=f"faction_rep:{faction_id}:10")],
            [InlineKeyboardButton(text="📉 Репутация -10", callback_data=f"faction_rep:{faction_id}:-10")],
            [InlineKeyboardButton(text="🚪 Покинуть", callback_data=f"faction_leave:{faction_id}")],
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="🏴 Вступить", callback_data=f"faction_join:{faction_id}")],
        ]

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="faction_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("faction_join:"))
async def cb_faction_join(callback: CallbackQuery):
    faction_id = callback.data.split(":")[1]
    result = await services.faction.join_faction(callback.from_user.id, faction_id)

    if result["success"]:
        text = f"✅ {result['message']}"
    else:
        text = f"❌ {result['message']}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="faction_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("faction_leave:"))
async def cb_faction_leave(callback: CallbackQuery):
    faction_id = callback.data.split(":")[1]
    result = await services.faction.leave_faction(callback.from_user.id, faction_id)

    if result["success"]:
        text = f"✅ {result['message']}"
    else:
        text = f"❌ {result['message']}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="faction_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("faction_rep:"))
async def cb_faction_rep(callback: CallbackQuery):
    parts = callback.data.split(":")
    faction_id = parts[1]
    amount = int(parts[2])

    result = await services.faction.add_reputation(callback.from_user.id, faction_id, amount)

    if result["success"]:
        text = f"📈 Репутация изменена: {result['new_reputation']} ({result['new_rank']})"
    else:
        text = f"❌ {result['message']}"

    await callback.answer(text, show_alert=True)
    await cb_faction_view(callback)
