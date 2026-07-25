from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from services.container import services

router = Router()

EVENT_ICONS = {
    "WORLD_EVENT": "🌍",
    "COMBAT_VICTORY": "⚔️",
    "COMBAT_DEFEAT": "💀",
    "QUEST_COMPLETED": "📜",
    "QUEST_ACCEPTED": "📋",
    "PLAYER_LEVEL_UP": "⭐",
    "PLAYER_DEATH": "💀",
    "LEGEND_DISCOVERED": "🏆",
    "ACHIEVEMENT_UNLOCKED": "🎯",
    "NPC_TALKED": "🗣",
    "NPC_KILLED": "🗡",
    "TRADE_COMPLETED": "🤝",
    "GUILD_CREATED": "🏰",
    "SECRET_FOUND": "🔮",
}


@router.callback_query(F.data == "world_chronicle")
async def cb_world_chronicle(callback: CallbackQuery):
    era = await services.world_chronicle.get_era_summary()

    text = (
        f"📜 <b>Хроника мира MIST</b>\n\n"
        f"📊 Всего событий: {era['total_events']}\n"
        f"🌍 Мировых: {era['world_events']}\n"
        f"👤 Игроков: {era['player_events']}\n"
        f"⚔️ Боевых: {era['combat_events']}\n"
    )

    recent = await services.world_chronicle.get_full_history(limit=10)

    if recent:
        text += "\n<b>Последние события:</b>\n"
        for ev in recent:
            icon = EVENT_ICONS.get(ev["type"], "📜")
            msg = ev.get("message", "")[:80]
            text += f"{icon} {msg}\n"

    buttons = [
        [InlineKeyboardButton(text="🌍 Мировые", callback_data="chronicle_filter:WORLD_EVENT")],
        [InlineKeyboardButton(text="⚔️ Боевые", callback_data="chronicle_filter:COMBAT")],
        [InlineKeyboardButton(text="📜 Квесты", callback_data="chronicle_filter:QUEST")],
        [InlineKeyboardButton(text="👤 Мои", callback_data="chronicle_filter:MY")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("chronicle_filter:"))
async def cb_chronicle_filter(callback: CallbackQuery):
    filter_type = callback.data.split(":")[1]

    if filter_type == "MY":
        events = await services.world_chronicle.get_history_by_player(callback.from_user.id, limit=15)
        title = "👤 Мои события"
    elif filter_type == "WORLD_EVENT":
        events = await services.world_chronicle.get_full_history(limit=15, event_type="WORLD_EVENT")
        title = "🌍 Мировые события"
    elif filter_type == "COMBAT":
        events = await services.world_chronicle.get_full_history(limit=15, event_type="COMBAT_VICTORY")
        title = "⚔️ Боевые события"
    elif filter_type == "QUEST":
        events = await services.world_chronicle.get_full_history(limit=15, event_type="QUEST_COMPLETED")
        title = "📜 Завершённые квесты"
    else:
        events = await services.world_chronicle.get_full_history(limit=15)
        title = "📜 Все события"

    text = f"{title}\n\n"

    if not events:
        text += "Пока ничего."
    else:
        for ev in events:
            icon = EVENT_ICONS.get(ev["type"], "📜")
            msg = ev.get("message", "")[:100]
            text += f"{icon} {msg}\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="world_chronicle")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
