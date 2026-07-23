import json
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
import game_engine as ge

router = Router()


@router.callback_query(F.data == "pvp_menu")
async def cb_pvp_menu(callback: CallbackQuery):
    user = await ge.get_or_create_user(callback.from_user.id)
    stats = await ge.get_pvp_stats(callback.from_user.id)

    text = (
        f"⚔️ <b>PvP Арена</b>\n\n"
        f"📊 Рейтинг: {stats['rating']}\n"
        f"🏆 Побед: {stats['wins']} | 💀 Поражений: {stats['losses']}\n"
        f"📈 Винрейт: {stats['winrate']}%\n\n"
        f"❤️ HP: {user['hp']}/{user['max_hp']}\n"
        f"🗡 Атака: {user['attack']} | 🛡 Защита: {user['defense']}\n\n"
        "🌫 <i>Противники подбираются по рейтингу.</i>"
    )

    buttons = [
        [InlineKeyboardButton(text="⚔️ Найти противника", callback_data="pvp_find")],
        [InlineKeyboardButton(text="🏆 Таблица лидеров", callback_data="pvp_leaderboard")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ]

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data == "pvp_find")
async def cb_pvp_find(callback: CallbackQuery):
    user = await ge.get_or_create_user(callback.from_user.id)

    if not user["is_alive"]:
        await callback.message.edit_text(
            "💀 Ты мёртв. Очнись, чтобы сражаться.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
            ])
        )
        await callback.answer()
        return

    if user["hp"] < user["max_hp"] * 0.3:
        await callback.message.edit_text(
            "⚠️ <b>Ты слишком ослаблен.</b>\n\nВосстанови HP перед боем.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💚 Исцелиться", callback_data="heal")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="pvp_menu")],
            ])
        )
        await callback.answer()
        return

    opponents = await ge.get_pvp_opponents(callback.from_user.id)

    if not opponents:
        await callback.message.edit_text(
            "🔍 <b>Противников не найдено.</b>\n\nПопробуй позже.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="pvp_menu")]
            ])
        )
        await callback.answer()
        return

    text = "⚔️ <b>Выбери противника:</b>\n\n"
    buttons = []
    for opp in opponents:
        display = opp.get("display_name") or opp.get("username") or f"Путник_{opp['user_id'] % 10000}"
        rating_diff = opp["pvp_rating"] - user["pvp_rating"]
        diff_text = f"+{rating_diff}" if rating_diff > 0 else str(rating_diff)
        text += f"👤 <b>{display}</b> — Ур.{opp['level']} | 📊{opp['pvp_rating']} ({diff_text})\n"
        text += f"   ❤️ {opp['hp']}/{opp['max_hp']} | 🗡 {opp['attack']} | 🛡 {opp['defense']}\n\n"

        buttons.append([InlineKeyboardButton(
            text=f"⚔️ {display} (Ур.{opp['level']}, 📊{opp['pvp_rating']})",
            callback_data=f"pvp_attack:{opp['user_id']}"
        )])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="pvp_menu")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("pvp_attack:"))
async def cb_pvp_attack(callback: CallbackQuery):
    target_id = int(callback.data.split(":")[1])

    if target_id == callback.from_user.id:
        await callback.answer("Нельзя сражаться с самим собой!", show_alert=True)
        return

    result = await ge.pvp_battle(callback.from_user.id, target_id)

    if not result["success"]:
        await callback.message.edit_text(result["message"], reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="pvp_menu")]
        ]))
        await callback.answer()
        return

    target = await ge.get_or_create_user(target_id)
    target_name = target.get("display_name") or target.get("username") or f"Путник_{target_id % 10000}"

    text = f"⚔️ <b>PvP: {target_name}</b>\n\n"

    for rd in result.get("rounds", [])[:5]:
        ud = rd.get("user_damage", 0)
        td = rd.get("target_damage", 0)
        text += f"Раунд {rd['round']}: -{ud} HP, -{td} HP\n"

    text += f"\n❤️ Твоё HP: {result['user_hp']}\n"

    if result["outcome"] == "victory":
        text += f"\n🏆 <b>ПОБЕДА!</b>\n+{result['xp_gained']} XP"
        if result.get("gold_gained"):
            text += f"\n+{result['gold_gained']} 🪙"
        text += "\n\n📊 Рейтинг increased!"
    elif result["outcome"] == "defeat":
        text += "\n💀 <b>ПОРАЖЕНИЕ</b>\nТы очнулся... где-то раньше.\n\n📊 Рейтинг decreased."
    else:
        text += "\n🤝 <b>НИЧЬЯ</b>\nОба отступили."

    if result["outcome"] == "defeat":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")],
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
        ])
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚔️ Ещё бой", callback_data="pvp_find")],
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
        ])

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "pvp_leaderboard")
async def cb_pvp_leaderboard(callback: CallbackQuery):
    leaders = await ge.get_pvp_leaderboard()

    if not leaders:
        text = "🏆 <b>Таблица лидеров</b>\n\nПока никто не сражался. Будь первым!"
    else:
        text = "🏆 <b>Таблица лидеров PvP</b>\n\n"
        medals = ["🥇", "🥈", "🥉"]
        for i, leader in enumerate(leaders):
            medal = medals[i] if i < 3 else f"#{i+1}"
            display = leader.get("display_name") or leader.get("username") or f"Путник_{leader['user_id'] % 10000}"
            text += f"{medal} <b>{display}</b>\n"
            text += f"   📊 {leader['pvp_rating']} | 🏆 {leader['pvp_wins']}W / 💀 {leader['pvp_losses']}L | ⭐ Ур.{leader['level']}\n\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Найти противника", callback_data="pvp_find")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="pvp_menu")],
    ])

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
