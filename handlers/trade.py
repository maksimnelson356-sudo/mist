from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from services.container import services

router = Router()


@router.callback_query(F.data == "trade_menu")
async def cb_trade_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    pending = await services.trade.get_pending(user_id)

    if not pending:
        text = (
            "🤝 <b>Трейдинг</b>\n\n"
            "Нет активных предложений трейда.\n\n"
            "<i>Чтобы начать трейд, используй /trade @username</i>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")]
        ])
    else:
        lines = ["🤝 <b>Активные трейды</b>\n"]
        buttons = []
        for t in pending:
            items_str = ""
            if t["items_offered"]:
                items_str = ", ".join(i.get("item_id", "?") for i in t["items_offered"])
            gold_str = f" + {t['gold_offered']} 🪙" if t["gold_offered"] else ""

            lines.append(f"📨 От: {t['from_name']}")
            if items_str or gold_str:
                lines.append(f"   Предлагает: {items_str}{gold_str}")
            if t["gold_wanted"]:
                lines.append(f"   Хочет: {t['gold_wanted']} 🪙")

            buttons.append([
                InlineKeyboardButton(text="✅ Принять", callback_data=f"trade_accept:{t['id']}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"trade_decline:{t['id']}"),
            ])
            lines.append("")

        text = "\n".join(lines)
        buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("trade_accept:"))
async def cb_trade_accept(callback: CallbackQuery):
    trade_id = int(callback.data.split(":")[1])
    result = await services.trade.accept(trade_id, callback.from_user.id)

    if result["success"]:
        text = f"🤝 <b>Трейд завершён!</b>\n\n{result['message']}"
    else:
        text = f"❌ <b>Ошибка</b>\n\n{result['message']}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("trade_decline:"))
async def cb_trade_decline(callback: CallbackQuery):
    trade_id = int(callback.data.split(":")[1])
    result = await services.trade.decline(trade_id, callback.from_user.id)

    if result["success"]:
        text = f"❌ <b>Трейд отклонён</b>\n\n{result['message']}"
    else:
        text = f"❌ <b>Ошибка</b>\n\n{result['message']}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()
