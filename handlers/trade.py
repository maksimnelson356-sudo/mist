import json
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
import game_engine as ge

router = Router()


@router.callback_query(F.data == "trade_menu")
async def cb_trade_menu(callback: CallbackQuery):
    user = await ge.get_or_create_user(callback.from_user.id)
    if not user["is_alive"]:
        await callback.message.edit_text("💀 Ты мёртв.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
        ]))
        await callback.answer()
        return

    pending = await ge.get_pending_trades(callback.from_user.id)
    nearby = await ge.get_nearby_players(callback.from_user.id)

    loc = await ge.get_location(user["current_location"])
    text = (
        f"🤝 <b>Трейдинг</b>\n\n"
        f"📍 <i>{loc['name']}</i>\n"
        f"🪙 Золото: {user['gold']}\n\n"
    )

    if pending:
        text += "📨 <b>Входящие предложения:</b>\n"
        for t in pending:
            items_off = json.loads(t["items_offered"]) if isinstance(t["items_offered"], str) else t["items_offered"]
            items_wan = json.loads(t["items_wanted"]) if isinstance(t["items_wanted"], str) else t["items_wanted"]
            offered_names = ", ".join(i["item_id"] for i in items_off)
            wanted_names = ", ".join(i["item_id"] for i in items_wan)
            text += f"  • От <b>{t['from_name']}</b>: {t['gold_offered']}🪙\n"
            if offered_names:
                text += f"    Предлагает: {offered_names}\n"
            if wanted_names:
                text += f"    Хочет: {wanted_names}\n"

    text += "\n👥 <b>Рядом:</b>\n"
    buttons = []

    if pending:
        for t in pending:
            text += f"  • {t['from_name']} (Ур.{t.get('level', '?')})\n"
            buttons.append([InlineKeyboardButton(
                text=f"✅ Принять от {t['from_name']}",
                callback_data=f"trade_accept:{t['id']}"
            )])
            buttons.append([InlineKeyboardButton(
                text=f"❌ Отклонить от {t['from_name']}",
                callback_data=f"trade_decline:{t['id']}"
            )])

    for p in nearby:
        name = p.get("display_name") or f"Путник_{p['user_id'] % 10000}"
        text += f"  • <b>{name}</b> — Ур.{p['level']} | ❤️{p['hp']}/{p['max_hp']}\n"
        buttons.append([InlineKeyboardButton(
            text=f"📨 Предложить трейд: {name}",
            callback_data=f"trade_offer:{p['user_id']}"
        )])

    if not nearby:
        text += "  <i>Никого рядом нет.</i>"

    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("trade_offer:"))
async def cb_trade_offer(callback: CallbackQuery):
    target_id = int(callback.data.split(":")[1])
    user = await ge.get_or_create_user(callback.from_user.id)
    target = await ge.get_or_create_user(target_id)

    if user["current_location"] != target["current_location"]:
        await callback.message.edit_text("Вы больше не в одной локации.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")]
        ]))
        await callback.answer()
        return

    target_name = target.get("display_name") or f"Путник_{target_id % 10000}"
    text = (
        f"📨 <b>Трейд с {target_name}</b>\n\n"
        "Отправь команду:\n"
        f"<code>/trade {target_id} золото_отправить предмет_id_количество предмет_id_количество</code>\n\n"
        "<i>Пример:\n"
        f"/trade {target_id} 10 wolf_fang 3 old_coin 2</code>\n\n"
        "Это отправит 10 золота, 3 клыка волка и 2 старые монеты.\n"
        "Ты не получаешь ничего в ответ (простой трейд).\n\n"
        "Для полноценного трейда используй:\n"
        f"<code>/tradeoffer {target_id} gold:10 wolf_fang:3</code>\n"
        f"<i>(предлагаешь, получаешь = 0)</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="trade_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("trade_accept:"))
async def cb_trade_accept(callback: CallbackQuery):
    trade_id = int(callback.data.split(":")[1])
    result = await ge.accept_trade(trade_id, callback.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤝 Трейдинг", callback_data="trade_menu")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])
    await callback.message.edit_text(result["message"], reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("trade_decline:"))
async def cb_trade_decline(callback: CallbackQuery):
    trade_id = int(callback.data.split(":")[1])
    result = await ge.decline_trade(trade_id, callback.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤝 Трейдинг", callback_data="trade_menu")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])
    await callback.message.edit_text(result["message"], reply_markup=kb)
    await callback.answer()
