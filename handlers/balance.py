from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from services.container import services

router = Router()


@router.callback_query(F.data == "balance_menu")
async def cb_balance_menu(callback: CallbackQuery):
    balance = await services.economy.get_balance(callback.from_user.id)
    rep = await services.reputation.get(callback.from_user.id)

    text = (
        f"💰 <b>Баланс</b>\n\n"
        f"🪙 Золото: {balance['gold']}\n"
        f"💎 Камни: {balance['gems']}\n"
        f"🎟 Токены: {balance['tokens']}\n\n"
        f"⭐ Репутация: {balance['gold']}\n"
        f"📊 Уровень: {rep['level']}\n"
        f"📝 {rep['description']}"
    )

    buttons = [
        [InlineKeyboardButton(text="🔄 Перевести", callback_data="economy_transfer")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data == "economy_transfer")
async def cb_economy_transfer(callback: CallbackQuery):
    text = (
        "🔄 <b>Перевод</b>\n\n"
        "Отправь сообщение:\n"
        "<code>перевести [ID] [сумма]</code>\n\n"
        "Пример: <code>перевести 123456789 50</code>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="balance_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
