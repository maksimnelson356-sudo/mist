from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from services.container import services
from services.admin_service import is_admin

router = Router()


@router.callback_query(F.data == "admin_menu")
async def cb_admin_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа.", show_alert=True)
        return

    text = (
        "🔧 <b>Панель администратора</b>\n\n"
        "Доступные команды:\n"
        "/admin_info user_id — инфо об игроке\n"
        "/admin_level user_id level — установить уровень\n"
        "/admin_gold user_id amount — установить золото\n"
        "/admin_revive user_id — воскресить\n"
        "/admin_tp user_id location — телепортировать"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
@router.message(F.text.startswith("/admin_level "))
async def cmd_admin_level(message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Использование: /admin_level user_id level")
        return
    try:
        user_id = int(parts[1])
        level = int(parts[2])
    except ValueError:
        await message.answer("user_id и level должны быть числами.")
        return
    result = await services.admin.set_level(user_id, level)
    await message.answer(result["message"])


@router.message(F.text.startswith("/admin_gold "))
async def cmd_admin_gold(message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Использование: /admin_gold user_id amount")
        return
    try:
        user_id = int(parts[1])
        amount = int(parts[2])
    except ValueError:
        await message.answer("user_id и amount должны быть числами.")
        return
    result = await services.admin.set_gold(user_id, amount)
    await message.answer(result["message"])


@router.message(F.text.startswith("/admin_revive "))
async def cmd_admin_revive(message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Использование: /admin_revive user_id")
        return
    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("user_id должен быть числом.")
        return
    result = await services.admin.revive_player(user_id)
    await message.answer(result["message"])


@router.message(F.text.startswith("/admin_tp "))
async def cmd_admin_tp(message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Использование: /admin_tp user_id location_id")
        return
    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("user_id должен быть числом.")
        return
    location_id = parts[2]
    result = await services.admin.teleport(user_id, location_id)
    await message.answer(result["message"])
