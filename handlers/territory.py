from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from services.container import services

router = Router()


@router.callback_query(F.data == "territory_menu")
async def cb_territory_menu(callback: CallbackQuery):
    guild = await services.guild.get_user_guild(callback.from_user.id)
    if not guild:
        await callback.answer("Ты не в гильдии.", show_alert=True)
        return

    territories = await services.guild_territory.get_guild_territories(guild["guild_id"])

    text = f"🗺️ <b>Территории «{guild['name']}»</b>\n\n"
    if not territories:
        text += "Гильдия не владеет территориями.\nЗахвати локацию, чтобы получить бонусы."
    else:
        for t in territories:
            text += f"📍 {t['name']} — опасность: {t['danger_level']}\n"

    text += f"\nБонус: -{min(20, len(territories) * 2)} к опасности на территориях"
    text += f"\nДоход: +{len(territories) * 10} 🪙/день в казну гильдии"

    buttons = [
        [InlineKeyboardButton(text="🏴 Захватить локацию", callback_data="territory_claim")],
        [InlineKeyboardButton(text="⚔️ Оспорить территорию", callback_data="territory_contest")],
        [InlineKeyboardButton(text="◀️ Гильдия", callback_data="guild_menu")],
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data == "territory_claim")
async def cb_territory_claim(callback: CallbackQuery):
    user = await services.player.get(callback.from_user.id)
    loc_id = user.get("location_id", "") if user else ""

    guild = await services.guild.get_user_guild(callback.from_user.id)
    if not guild:
        await callback.answer("Ты не в гильдии.", show_alert=True)
        return

    if guild["role"] not in ("leader", "officer"):
        await callback.answer("Только лидер или офицер может захватывать территории.", show_alert=True)
        return

    result = await services.guild_territory.claim_territory(guild["guild_id"], loc_id)

    if result["success"]:
        text = f"✅ {result['message']}"
    else:
        text = f"❌ {result['message']}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Территории", callback_data="territory_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data == "territory_contest")
async def cb_territory_contest(callback: CallbackQuery):
    user = await services.player.get(callback.from_user.id)
    loc_id = user.get("current_location", "") if user else ""

    guild = await services.guild.get_user_guild(callback.from_user.id)
    if not guild:
        await callback.answer("Ты не в гильдии.", show_alert=True)
        return

    if guild["role"] not in ("leader", "officer"):
        await callback.answer("Только лидер или офицер может оспаривать территории.", show_alert=True)
        return

    result = await services.guild_territory.contest_territory(guild["guild_id"], loc_id)

    if result["success"]:
        text = f"{'✅' if result.get('won') else '❌'} {result['message']}"
    else:
        text = f"❌ {result['message']}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Территории", callback_data="territory_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
