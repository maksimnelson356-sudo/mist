from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from services.container import services

router = Router()


@router.callback_query(F.data == "event_menu")
async def cb_event_menu(callback: CallbackQuery):
    active_events = await services.event.get_active_events()

    season = services.world_engine._state["season"] if services.world_engine._state else "spring"
    seasonal_events = services.seasonal_event.get_seasonal_events(season)
    daily_events_info = services.daily_event.get_all_daily_events()

    text = "🎭 <b>События мира</b>\n\n"

    if seasonal_events:
        text += "🌸 <b>Сезонные события:</b>\n"
        for se in seasonal_events[:2]:
            text += f"  {se['icon']} {se['name']}\n"
        text += "\n"

    if daily_events_info:
        text += "📅 <b>Типы дневных событий:</b>\n"
        for de in daily_events_info[:3]:
            text += f"  {de['icon']} {de['name']}\n"
        text += "\n"

    if not active_events:
        text += "Нет активных событий. Мир отдыхает."
    else:
        text += f"<b>Активных событий: {len(active_events)}</b>\n\n"
        for ev in active_events[:10]:
            icon = ev.get("name", "")[:1]
            days_left = ev.get("end_day")
            if days_left:
                text += f"• {ev['name']} — осталось {days_left} дн.\n"
            else:
                text += f"• {ev['name']} — одноразовое\n"

    buttons = []
    for ev in active_events[:10]:
        buttons.append([InlineKeyboardButton(
            text=f"🎭 {ev['name']}",
            callback_data=f"event_view:{ev['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data.startswith("event_view:"))
async def cb_event_view(callback: CallbackQuery):
    record_id = callback.data.split(":", 1)[1]
    ev = await services.event.get_event(record_id)

    if not ev:
        await callback.answer("Событие не найдено.", show_alert=True)
        return

    participations = ev.get("participations")
    loc_name = await services.movement.get_location_name(ev.get("region_id", "?"))

    text = (
        f"🎭 <b>{ev['name']}</b>\n\n"
        f"{ev.get('description', '')}\n\n"
        f"📍 Регион: {loc_name}\n"
    )

    buttons = []
    if participations and ev["is_active"]:
        text += f"\n<b>{participations['name']}</b>\n"
        text += f"{participations['description']}\n\n"

        for action in participations["actions"]:
            risk = action.get("risk", 0)
            risk_text = f" (риск: {int(risk*100)}%)" if risk > 0 else ""
            buttons.append([InlineKeyboardButton(
                text=f"{action['label']}{risk_text}",
                callback_data=f"event_act:{record_id}:{action['id']}"
            )])
    elif not ev["is_active"]:
        text += "\n<i>Событие завершено.</i>"

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="event_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data.startswith("event_act:"))
async def cb_event_act(callback: CallbackQuery):
    parts = callback.data.split(":", 2)
    record_id = parts[1]
    action_id = parts[2]

    result = await services.event.participate(record_id, callback.from_user.id, action_id)

    if result["success"]:
        text = f"🎭 <b>Результат:</b>\n\n{result['message']}"
    elif result.get("killed"):
        text = f"💀 <b>Ты погиб!</b>\n\n{result['message']}"
    elif result.get("damaged"):
        text = f"⚠️ <b>Ты ранен!</b>\n\n{result['message']}"
    else:
        text = f"❌ {result['message']}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ События", callback_data="event_menu")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
