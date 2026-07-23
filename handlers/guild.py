import json
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command, CommandStart
import game_engine as ge

router = Router()


@router.callback_query(F.data == "guild_menu")
async def cb_guild_menu(callback: CallbackQuery):
    user = await ge.get_or_create_user(callback.from_user.id)
    if not user["is_alive"]:
        await callback.message.edit_text("💀 Ты мёртв.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
        ]))
        await callback.answer()
        return

    guild = await ge.get_user_guild(callback.from_user.id)

    if not guild:
        text = (
            "🏰 <b>Гильдии</b>\n\n"
            "Ты не состояишь ни в одной гильдии.\n\n"
            "<i>Создай свою за 50 🪙 или вступи в чужую.</i>"
        )
        buttons = [
            [InlineKeyboardButton(text="➕ Создать гильдию", callback_data="guild_create")],
            [InlineKeyboardButton(text="📋 Все гильдии", callback_data="guild_list")],
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
        ]
    else:
        member_count = 0
        db = await ge.get_db()
        cursor = await db.execute(
            "SELECT COUNT(*) FROM guild_members WHERE guild_id = ?", (guild["guild_id"],)
        )
        row = await cursor.fetchone()
        if row:
            member_count = row[0]

        role_icon = {"leader": "👑", "officer": "⭐", "member": "👤"}.get(guild["role"], "👤")
        text = (
            f"🏰 <b>{guild['name']}</b>\n\n"
            f"{guild.get('description', '')}\n"
            f"📜 <i>{guild.get('motto', '')}</i>\n\n"
            f"👑 Лидер: #{guild['leader_id']}\n"
            f"👥 Участников: {member_count}\n"
            f"⭐ Уровень: {guild['level']} (XP: {guild['xp']})\n"
            f"🪙 Казна: {guild['gold']} 🪙\n\n"
            f"Ты: {role_icon} {guild['role']} | Вклад: {guild['contribution']} 🪙"
        )
        buttons = [
            [InlineKeyboardButton(text="👥 Участники", callback_data="guild_members")],
            [InlineKeyboardButton(text="💰 Пожертвовать", callback_data="guild_donate_menu")],
            [InlineKeyboardButton(text="🚪 Покинуть", callback_data="guild_leave")],
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
        ]

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data == "guild_create")
async def cb_guild_create(callback: CallbackQuery):
    text = "🏰 <b>Создание гильдии</b>\n\nСтоимость: 50 🪙\n\nОтправь название гильдии в чат:"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="guild_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.message(F.text, ~F.text.startswith("/"))
async def handle_guild_name_input(message: Message, bot_username: str):
    if message.chat.type != "private":
        return
    text = message.text.strip()
    if len(text) < 3 or len(text) > 30:
        await message.answer("Название должно быть 3-30 символов.")
        return

    result = await ge.create_guild(message.from_user.id, text, description=f"Гильдия «{text}»")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏰 Гильдия", callback_data="guild_menu")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])
    await message.answer(result["message"], reply_markup=kb)


@router.callback_query(F.data == "guild_list")
async def cb_guild_list(callback: CallbackQuery):
    guilds = await ge.get_all_guilds()

    if not guilds:
        text = "📋 <b>Гильдий пока нет.</b>\n\nБудь первым!"
    else:
        text = "📋 <b>Гильдии MIST</b>\n\n"
        for g in guilds:
            text += f"🏰 <b>{g['name']}</b> — Ур.{g['level']} | {g['member_count']} чел. | {g['gold']} 🪙\n"
            text += f"   <i>{g.get('motto', '')}</i>\n\n"

    buttons = []
    for g in guilds:
        buttons.append([InlineKeyboardButton(
            text=f"➕ Вступить: {g['name']}",
            callback_data=f"guild_join:{g['guild_id']}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="guild_menu")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("guild_join:"))
async def cb_guild_join(callback: CallbackQuery):
    guild_id = callback.data.split(":")[1]
    result = await ge.join_guild(callback.from_user.id, guild_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏰 Гильдия", callback_data="guild_menu")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])
    await callback.message.edit_text(result["message"], reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "guild_members")
async def cb_guild_members(callback: CallbackQuery):
    guild = await ge.get_user_guild(callback.from_user.id)
    if not guild:
        await callback.message.edit_text("Ты не в гильдии.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")]
        ]))
        await callback.answer()
        return

    members = await ge.get_guild_members(guild["guild_id"])

    text = f"👥 <b>Участники «{guild['name']}»</b>\n\n"
    for m in members:
        role_icon = {"leader": "👑", "officer": "⭐", "member": "👤"}.get(m["role"], "👤")
        name = m.get("display_name") or f"Путник_{m['user_id'] % 10000}"
        text += f"{role_icon} <b>{name}</b> — Ур.{m.get('level', 1)} | 📊{m.get('pvp_rating', 1000)} | Вклад: {m['contribution']} 🪙\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="guild_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "guild_donate_menu")
async def cb_guild_donate_menu(callback: CallbackQuery):
    user = await ge.get_or_create_user(callback.from_user.id)
    text = f"💰 <b>Пожертвовать в казну</b>\n\n🪙 У тебя: {user['gold']}\n\nОтправь сумму в чат:"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="guild_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "guild_leave")
async def cb_guild_leave(callback: CallbackQuery):
    result = await ge.leave_guild(callback.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏰 Гильдии", callback_data="guild_menu")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])
    await callback.message.edit_text(result["message"], reply_markup=kb)
    await callback.answer()


@router.message(Command("guild_donate"))
async def cmd_guild_donate(message: Message):
    if message.chat.type != "private":
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "📝 <b>Использование:</b>\n<code>/guild_donate сумма</code>\n\n"
            "<i>Пример: /guild_donate 20</i>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")]
            ])
        )
        return

    try:
        amount = int(parts[1])
    except ValueError:
        await message.answer("Сумма должна быть числом.")
        return

    result = await ge.guild_donate(message.from_user.id, amount)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏰 Гильдия", callback_data="guild_menu")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])
    await message.answer(result["message"], reply_markup=kb)
