from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from services.container import services

router = Router()


@router.callback_query(F.data == "guild_ext_menu")
async def cb_guild_ext_menu(callback: CallbackQuery):
    guild = await services.guild.get_user_guild(callback.from_user.id)
    if not guild:
        await callback.answer("Ты не в гильдии.", show_alert=True)
        return

    text = (
        f"🏰 <b>{guild['name']}</b>\n"
        f"Ур. {guild['level']} | 💰 {guild['gold']} | ⭐ {guild['xp']} XP\n\n"
        f"Выбери действие:"
    )

    buttons = [
        [InlineKeyboardButton(text="📦 Склад", callback_data="guild_storage")],
        [InlineKeyboardButton(text="💰 Казна", callback_data="guild_bank")],
        [InlineKeyboardButton(text="📜 Квесты гильдии", callback_data="guild_quests")],
        [InlineKeyboardButton(text="◀️ Гильдия", callback_data="guild_menu")],
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "guild_storage")
async def cb_guild_storage(callback: CallbackQuery):
    result = await services.guild_ext.get_storage(callback.from_user.id)

    if not result["success"]:
        await callback.answer(result["message"], show_alert=True)
        return

    text = f"📦 <b>Склад гильдии</b> ({len(result['items'])}/{result['limit']})\n\n"

    if not result["items"]:
        text += "Склад пуст."
    else:
        for item in result["items"]:
            text += f"• {item['item_id']}: {item['quantity']}\n"

    buttons = [
        [InlineKeyboardButton(text="📥 Положить", callback_data="guild_storage_deposit")],
        [InlineKeyboardButton(text="📤 Забрать", callback_data="guild_storage_withdraw")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="guild_ext_menu")],
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "guild_storage_deposit")
async def cb_guild_storage_deposit(callback: CallbackQuery):
    text = (
        "📥 <b>Положить на склад</b>\n\n"
        "Отправь сообщение:\n"
        "📦 <code>положить [предмет] [количество]</code>\n\n"
        "Пример: <code>положить wood 10</code>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="guild_storage")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "guild_storage_withdraw")
async def cb_guild_storage_withdraw(callback: CallbackQuery):
    text = (
        "📤 <b>Забрать со склада</b>\n\n"
        "Отправь сообщение:\n"
        "📦 <code>забрать [предмет] [количество]</code>\n\n"
        "Пример: <code>забрать wood 5</code>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="guild_storage")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "guild_bank")
async def cb_guild_bank(callback: CallbackQuery):
    result = await services.guild_ext.get_bank_info(callback.from_user.id)

    if not result["success"]:
        await callback.answer(result["message"], show_alert=True)
        return

    text = (
        f"💰 <b>Казна гильдии</b>\n\n"
        f"Золото: {result['gold']}\n"
        f"Лимит: {result['limit']}\n\n"
    )

    buttons = [
        [InlineKeyboardButton(text="📥 Пожертвовать", callback_data="guild_bank_deposit")],
    ]

    if result["role"] in ("leader", "officer"):
        buttons.append([InlineKeyboardButton(text="📤 Снять", callback_data="guild_bank_withdraw")])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="guild_ext_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "guild_bank_deposit")
async def cb_guild_bank_deposit(callback: CallbackQuery):
    text = (
        "📥 <b>Пожертвовать в казну</b>\n\n"
        "Отправь сообщение:\n"
        "💰 <code>пожертвовать [сумма]</code>\n\n"
        "Пример: <code>пожертвовать 50</code>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="guild_bank")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "guild_bank_withdraw")
async def cb_guild_bank_withdraw(callback: CallbackQuery):
    text = (
        "📤 <b>Снять из казны</b>\n\n"
        "Отправь сообщение:\n"
        "💰 <code>снять [сумма]</code>\n\n"
        "Пример: <code>снять 30</code>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="guild_bank")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "guild_quests")
async def cb_guild_quests(callback: CallbackQuery):
    result = await services.guild_ext.get_guild_quests(callback.from_user.id)

    if not result["success"]:
        await callback.answer(result["message"], show_alert=True)
        return

    text = "📜 <b>Квесты гильдии</b>\n\n"

    if not result["quests"]:
        text += "Нет активных квестов."
    else:
        for q in result["quests"]:
            progress = q["progress"]
            target = q["objective"]["target"]
            pct = min(100, int(progress / target * 100)) if target > 0 else 0
            text += (
                f"📋 {q['name']}\n"
                f"   {q['description']}\n"
                f"   Прогресс: {progress}/{target} ({pct}%)\n"
                f"   Награда: {q['rewards']['xp']} XP, {q['rewards']['gold']} Gold\n\n"
            )

    buttons = [[InlineKeyboardButton(text="◀️ Назад", callback_data="guild_ext_menu")]]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.message(F.text.startswith("положить"))
async def cmd_guild_deposit_item(message: Message):
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Формат: <code>положить [предмет] [количество]</code>\nПример: <code>положить wood 10</code>")
        return

    item_id = parts[1]
    try:
        quantity = int(parts[2])
    except ValueError:
        await message.answer("Количество должно быть числом.")
        return

    result = await services.guild_ext.deposit_item(message.from_user.id, item_id, quantity)
    await message.answer(result["message"])


@router.message(F.text.startswith("забрать"))
async def cmd_guild_withdraw_item(message: Message):
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Формат: <code>забрать [предмет] [количество]</code>\nПример: <code>забрать wood 5</code>")
        return

    item_id = parts[1]
    try:
        quantity = int(parts[2])
    except ValueError:
        await message.answer("Количество должно быть числом.")
        return

    result = await services.guild_ext.withdraw_item(message.from_user.id, item_id, quantity)
    await message.answer(result["message"])


@router.message(F.text.startswith("пожертвовать"))
async def cmd_guild_donate_gold(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Формат: <code>пожертвовать [сумма]</code>\nПример: <code>пожертвовать 50</code>")
        return

    try:
        amount = int(parts[1])
    except ValueError:
        await message.answer("Сумма должна быть числом.")
        return

    result = await services.guild_ext.deposit_gold(message.from_user.id, amount)
    await message.answer(result["message"])


@router.message(F.text.startswith("снять"))
async def cmd_guild_withdraw_gold(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Формат: <code>снять [сумма]</code>\nПример: <code>снять 30</code>")
        return

    try:
        amount = int(parts[1])
    except ValueError:
        await message.answer("Сумма должна быть числом.")
        return

    result = await services.guild_ext.withdraw_gold(message.from_user.id, amount)
    await message.answer(result["message"])
