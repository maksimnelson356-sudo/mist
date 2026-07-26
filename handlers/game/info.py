from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from services.container import services
from . import _shared as G

router = G.router


@router.callback_query(F.data == "status")
async def cb_status(callback: CallbackQuery):
    user = await services.player.get_or_create(callback.from_user.id)
    days = user.get("days_in_mist", 0)
    xp_needed = user["level"] * 100

    loc_name = await services.movement.get_location_name(user["current_location"])
    loc = await services.movement.get_location(user["current_location"])
    weather = loc.get("current_weather", "clear") if loc else "clear"
    from services.weather_system import WEATHER_STATES
    w_info = WEATHER_STATES.get(weather, WEATHER_STATES["clear"])

    text = (
        f"👤 <b>{user['display_name']}</b>\n\n"
        f"📍 Локация: {loc_name}\n"
        f"{w_info['icon']} Погода: {w_info['name']}\n"
        f"⏰ Дней в MIST: {days}\n\n"
        f"❤️ HP: {user['hp']}/{user['max_hp']}\n"
        f"🗡 Атака: {user['attack']}\n"
        f"🛡 Защита: {user['defense']}\n"
        f"⭐ Уровень: {user['level']} (XP: {user['xp']}/{xp_needed})\n"
        f"🪙 Золото: {user['gold']}\n\n"
        f"🎒 Воспоминаний: {user['memories']}\n"
        f"⚖️ Карма: {user['karma']}"
    )
    await callback.message.edit_text(text, reply_markup=G.back_menu_kb())


@router.callback_query(F.data == "legends")
async def cb_legends(callback: CallbackQuery):
    stats = await services.quest.get_legend_stats()
    text = (
        "🏆 <b>Энциклопедия MIST</b>\n\n"
        f"🐾 Существа: {stats['creatures_found']}\n"
        f"🏺 Предметы: {stats['items_found']}\n"
        f"🗺 Локации: {stats['places_found']}\n"
        f"📜 Легенды: {stats['lore_found']}\n\n"
        "<i>Каждый первый человек, открывший нечто,\nнавсегда вписан в историю.</i>"
    )
    await callback.message.edit_text(text, reply_markup=G.back_menu_kb())


@router.message(Command("trade"))
async def cmd_trade(message: Message):
    if message.chat.type != "private":
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer(
            "📝 <b>Использование:</b>\n"
            "<code>/trade ID золото предмет:кол-во предмет:кол-во</code>\n\n"
            "<i>Пример:\n/trade 123456 10 wolf_fang:3 old_coin:2</i>",
            reply_markup=G.back_menu_kb()
        )
        return

    try:
        target_id = int(parts[1])
        gold = int(parts[2])
    except ValueError:
        await message.answer("Неверный формат. ID и золото должны быть числами.")
        return

    items_offered = []
    for part in parts[3:]:
        if ":" in part:
            item_id, qty = part.split(":", 1)
            items_offered.append({"item_id": item_id, "qty": int(qty)})
        else:
            items_offered.append({"item_id": part, "qty": 1})

    result = await services.trade.create(
        message.from_user.id, target_id,
        items_offered, gold, [], 0
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤝 Трейдинг", callback_data="trade_menu")],
    ])
    await message.answer(result["message"], reply_markup=kb)
