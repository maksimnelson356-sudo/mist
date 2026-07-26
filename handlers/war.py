from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from services.container import services

router = Router()


@router.callback_query(F.data == "war_menu")
async def cb_war_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_guild = await services.guild.get_user_guild(user_id)

    if not user_guild:
        text = (
            "⚔️ <b>Войны гильдий</b>\n\n"
            "Ты не состояишь ни в одной гильдии.\n"
            "Вступи в гильдию, чтобы участвовать в войнах."
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
        ])
        await callback.message.edit_text(text, reply_markup=kb)
        return

    active = await services.guild_war.get_active_wars()
    stats = await services.guild_war.get_war_stats()

    text = (
        f"⚔️ <b>Войны гильдий</b>\n\n"
        f"Активных войн: {stats['active']} | Всего: {stats['total']}\n"
        f"Твоя гильдия: <b>{user_guild['name']}</b>\n\n"
    )

    buttons = []

    my_wars = [w for w in active if w["attacker"] == user_guild["guild_id"] or w["defender"] == user_guild["guild_id"]]

    all_guilds = await services.guild.get_all(limit=100)
    guild_names = {g["guild_id"]: g["name"] for g in all_guilds}

    if my_wars:
        text += "<b>Твои войны:</b>\n"
        for w in my_wars:
            is_attacker = w["attacker"] == user_guild["guild_id"]
            enemy_id = w["defender"] if is_attacker else w["attacker"]
            enemy_name = guild_names.get(enemy_id, enemy_id[:15])
            text += f"  ⚔️ vs {enemy_name} — {w['attacker_wins']}:{w['defender_wins']}\n"
            buttons.append([InlineKeyboardButton(
                text=f"⚔️ vs {enemy_name[:15]}",
                callback_data=f"war_view:{w['id']}"
            )])
    else:
        text += "У твоей гильдии нет активных войн.\n"

    other_wars = [w for w in active if w["attacker"] != user_guild["guild_id"] and w["defender"] != user_guild["guild_id"]]
    if other_wars:
        text += "\n<b>Другие войны:</b>\n"
        for w in other_wars[:3]:
            atk_name = guild_names.get(w["attacker"], w["attacker"][:15])
            def_name = guild_names.get(w["defender"], w["defender"][:15])
            text += f"  {atk_name} vs {def_name} — {w['attacker_wins']}:{w['defender_wins']}\n"

    buttons.append([InlineKeyboardButton(text="📢 Объявить войну", callback_data="war_declare")])
    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data.startswith("war_view:"))
async def cb_war_view(callback: CallbackQuery):
    war_id = callback.data.split(":")[1]
    active = await services.guild_war.get_active_wars()
    war = next((w for w in active if w["id"] == war_id), None)

    if not war:
        await callback.answer("Война не найдена.", show_alert=True)
        return

    loc_name = await services.movement.get_location_name(war["location"])

    text = (
        f"⚔️ <b>Война</b>\n\n"
        f"👥 {war['attacker']} vs {war['defender']}\n"
        f"📍 Локация: {loc_name}\n\n"
        f"🏆 Счёт: {war['attacker_wins']} : {war['defender_wins']}\n"
    )

    user_guild = await services.guild.get_user_guild(callback.from_user.id)
    if user_guild:
        guild_id = user_guild["guild_id"]
        if guild_id == war["attacker"]:
            buttons = [
                [InlineKeyboardButton(text="⚔️ Напасть", callback_data=f"war_battle:{war_id}:attacker")],
                [InlineKeyboardButton(text="🏳️ Капитулировать", callback_data=f"war_surrender:{war_id}")],
            ]
        elif guild_id == war["defender"]:
            buttons = [
                [InlineKeyboardButton(text="🛡️ Защитить", callback_data=f"war_battle:{war_id}:defender")],
                [InlineKeyboardButton(text="🏳️ Капитулировать", callback_data=f"war_surrender:{war_id}")],
            ]
        else:
            buttons = []
    else:
        buttons = []

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="war_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data.startswith("war_battle:"))
async def cb_war_battle(callback: CallbackQuery):
    parts = callback.data.split(":")
    war_id = parts[1]
    side = parts[2]

    user_id = callback.from_user.id
    user_guild = await services.guild.get_user_guild(user_id)
    if not user_guild:
        await callback.answer("Ты не в гильдии.", show_alert=True)
        return

    active = await services.guild_war.get_active_wars()
    war = next((w for w in active if w["id"] == war_id), None)
    if not war:
        await callback.answer("Война не найдена.", show_alert=True)
        return

    if side == "attacker" and war["attacker"] != user_guild["guild_id"]:
        await callback.answer("Твоя гильдия не атакующая.", show_alert=True)
        return
    if side == "defender" and war["defender"] != user_guild["guild_id"]:
        await callback.answer("Твоя гильдия не защитник.", show_alert=True)
        return

    import random
    winner = side if random.random() > 0.35 else ("defender" if side == "attacker" else "attacker")
    result = await services.guild_war.resolve_battle(war_id, winner)

    winner_name = "атакующие" if winner == "attacker" else "защитники"
    if result["success"]:
        is_my_side = (side == winner)
        emoji = "🏆" if is_my_side else "💀"
        text = f"⚔️ <b>Битва завершена!</b>\n\n{emoji} Победитель: {winner_name}"
    else:
        text = f"❌ {result['message']}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"war_view:{war_id}")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data.startswith("war_surrender:"))
async def cb_war_surrender(callback: CallbackQuery):
    war_id = callback.data.split(":")[1]
    user_id = callback.from_user.id

    user_guild = await services.guild.get_user_guild(user_id)
    if not user_guild:
        await callback.answer("Ты не в гильдии.", show_alert=True)
        return

    active = await services.guild_war.get_active_wars()
    war = next((w for w in active if w["id"] == war_id), None)
    if not war:
        await callback.answer("Война не найдена.", show_alert=True)
        return

    if war["attacker"] != user_guild["guild_id"] and war["defender"] != user_guild["guild_id"]:
        await callback.answer("Твоя гильдия не участвует в этой войне.", show_alert=True)
        return

    result = await services.guild_war.end_war(war_id)

    if result["success"]:
        text = "🏳️ <b>Война завершена. Твоя гильдия капитулировала.</b>"
    else:
        text = f"❌ {result['message']}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Меню", callback_data="war_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data == "war_declare")
async def cb_war_declare(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_guild = await services.guild.get_user_guild(user_id)

    if not user_guild:
        await callback.answer("Ты не в гильдии.", show_alert=True)
        return

    guilds = await services.guild.get_all()
    other_guilds = [g for g in guilds if g["guild_id"] != user_guild["guild_id"]]

    if not other_guilds:
        await callback.answer("Нет других гильдий.", show_alert=True)
        return

    text = "📢 <b>Объявить войну</b>\n\nВыбери цель:\n\n"
    buttons = []
    for g in other_guilds:
        text += f"  ⚔️ {g['name']}\n"
        buttons.append([InlineKeyboardButton(
            text=f"⚔️ {g['name']}",
            callback_data=f"war_declare_target:{g['guild_id']}"
        )])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="war_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data.startswith("war_declare_target:"))
async def cb_war_declare_target(callback: CallbackQuery):
    target_id = callback.data.split(":")[1]
    user_id = callback.from_user.id
    user_guild = await services.guild.get_user_guild(user_id)

    if not user_guild:
        await callback.answer("Ты не в гильдии.", show_alert=True)
        return

    user = await services.player.get_or_create(user_id)
    location = user["current_location"]

    result = await services.guild_war.declare_war(user_guild["guild_id"], target_id, location)

    loc_name = await services.movement.get_location_name(location)

    if result["success"]:
        text = f"✅ {result['message']}\n\n📍 Локация: {loc_name}"
    else:
        text = f"❌ {result['message']}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Меню", callback_data="war_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
