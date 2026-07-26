from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import func, select

from database.base import get_db
from database.models.guild import GuildMemberModel
from services.container import services

router = Router()


class GuildCreate(StatesGroup):
    waiting_name = State()


async def _count_guild_members(guild_id: str) -> int:
    async for db in get_db():
        stmt = select(func.count()).select_from(GuildMemberModel).where(GuildMemberModel.guild_id == guild_id)
        result = await db.execute(stmt)
        return result.scalar() or 0
    return 0


@router.callback_query(F.data == "guild_menu")
async def cb_guild_menu(callback: CallbackQuery):
    user = await services.player.get_or_create(callback.from_user.id)
    if not user["is_alive"]:
        await callback.message.edit_text("💀 Ты мёртв.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
        ]))
        return

    guild = await services.guild.get_user_guild(callback.from_user.id)

    if not guild:
        text = (
            "🏰 <b>Гильдии</b>\n\n"
            "Ты не состоишь ни в одной гильдии.\n\n"
            "<i>Создай свою за 50 🪙 или вступи в чужую.</i>"
        )
        buttons = [
            [InlineKeyboardButton(text="➕ Создать гильдию", callback_data="guild_create")],
            [InlineKeyboardButton(text="📋 Все гильдии", callback_data="guild_list")],
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
        ]
    else:
        member_count = await _count_guild_members(guild["guild_id"])

        role_icon = {"leader": "👑", "officer": "⭐", "member": "👤"}.get(guild["role"], "👤")
        bonus_lines = []
        if guild["level"] >= 5:
            bonus_lines.append("✨ VIP-членство — скины мира")
        if guild["level"] >= 10:
            bonus_lines.append("⚔️ Военный бонус — +2 Атаки в PvP")
        if guild["level"] >= 20:
            bonus_lines.append("🪙 Казначей — +5% выпа стака")
        if guild["level"] >= 50:
            bonus_lines.append("🏆 Элитный клан — награды чемпионов")

        bonus_text = ""
        if bonus_lines:
            bonus_text = f"\nБонусы гильдии: {', '.join(bonus_lines)}"

        text = (
            f"🏰 <b>{guild['name']}</b> [{guild['level']}]\n\n"
            f"{guild.get('description', '')}\n"
            f"📜 <i>{guild.get('motto', '')}</i>\n\n"
            f"👑 Лидер: #{guild['leader_id']}\n"
            f"👥 Участников: {member_count}\n"
            f"⭐ Уровень: {guild['level']} (XP: {guild['xp']})\n"
            f"🪙 Казна: {guild['gold']} 🪙\n\n"
            f"Ты: {role_icon} {guild['role']} | Вклад: {guild['contribution']} 🪙"
            f"{bonus_text}"
        )
        buttons = [
            [InlineKeyboardButton(text="👥 Участники", callback_data="guild_members")],
            [InlineKeyboardButton(text="💰 Пожертвовать", callback_data="guild_donate_menu")],
            [InlineKeyboardButton(text="📦 Склад и казна", callback_data="guild_ext_menu")],
            [InlineKeyboardButton(text="🗺️ Территории", callback_data="territory_menu")],
            [InlineKeyboardButton(text="🚪 Покинуть", callback_data="guild_leave")],
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
        ]

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
@router.callback_query(F.data == "guild_create")
async def cb_guild_create(callback: CallbackQuery, state: FSMContext):
    text = "🏰 <b>Создание гильдии</b>\n\nСтоимость: 50 🪙\n\nОтправь название гильдии в чат:"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="guild_menu")]
    ])
    await state.set_state(GuildCreate.waiting_name)
    await callback.message.edit_text(text, reply_markup=kb)
@router.message(GuildCreate.waiting_name)
async def handle_guild_name_input(message: Message, state: FSMContext):
    if message.chat.type != "private":
        return
    text = message.text.strip()
    if len(text) < 3 or len(text) > 30:
        await message.answer("Название должно быть 3-30 символов.")
        return

    await state.clear()
    result = await services.guild.create(message.from_user.id, text, description=f"Гильдия «{text}»")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏰 Гильдия", callback_data="guild_menu")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])
    await message.answer(result["message"], reply_markup=kb)


@router.callback_query(F.data == "guild_list")
async def cb_guild_list(callback: CallbackQuery):
    guilds = await services.guild.get_all()

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
@router.callback_query(F.data.startswith("guild_join:"))
async def cb_guild_join(callback: CallbackQuery):
    guild_id = callback.data.split(":")[1]
    result = await services.guild.join(callback.from_user.id, guild_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏰 Гильдия", callback_data="guild_menu")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])
    await callback.message.edit_text(result["message"], reply_markup=kb)
@router.callback_query(F.data == "guild_members")
async def cb_guild_members(callback: CallbackQuery):
    guild = await services.guild.get_user_guild(callback.from_user.id)
    if not guild:
        await callback.message.edit_text("Ты не в гильдии.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")]
        ]))
        return

    members = await services.guild.get_members(guild["guild_id"])
    can_manage = guild["role"] in ("leader", "officer")

    text = f"👥 <b>Участники «{guild['name']}»</b>\n\n"
    buttons = []
    for m in members:
        role_icon = {"leader": "👑", "officer": "⭐", "member": "👤"}.get(m["role"], "👤")
        name = m.get("display_name") or f"Путник_{m['user_id'] % 10000}"
        text += f"{role_icon} <b>{name}</b> — Ур.{m.get('level', 1)} | 📊{m.get('pvp_rating', 1000)} | Вклад: {m['contribution']} 🪙\n"

        if can_manage and m["user_id"] != callback.from_user.id and m["role"] != "leader":
            buttons.append([
                InlineKeyboardButton(text=f"⬆️ {name}", callback_data=f"guild_promote:{m['user_id']}"),
                InlineKeyboardButton(text=f"🚫 {name}", callback_data=f"guild_kick:{m['user_id']}"),
            ])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="guild_menu")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
@router.callback_query(F.data == "guild_donate_menu")
async def cb_guild_donate_menu(callback: CallbackQuery):
    user = await services.player.get_or_create(callback.from_user.id)
    text = f"💰 <b>Пожертвовать в казну</b>\n\n🪙 У тебя: {user['gold']}\n\nОтправь сумму в чат:"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="guild_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data == "guild_leave")
async def cb_guild_leave(callback: CallbackQuery):
    result = await services.guild.leave(callback.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏰 Гильдии", callback_data="guild_menu")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])
    await callback.message.edit_text(result["message"], reply_markup=kb)
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

    result = await services.guild.donate(message.from_user.id, amount)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏰 Гильдия", callback_data="guild_menu")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])
    await message.answer(result["message"], reply_markup=kb)


@router.callback_query(F.data.startswith("guild_kick:"))
async def cb_guild_kick(callback: CallbackQuery):
    target_id = int(callback.data.split(":")[1])
    guild = await services.guild.get_user_guild(callback.from_user.id)
    if not guild:
        await callback.answer("Ты не в гильдии.", show_alert=True)
        return

    result = await services.guild.kick(guild["guild_id"], target_id, callback.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Участники", callback_data="guild_members")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="guild_menu")],
    ])
    await callback.message.edit_text(result["message"], reply_markup=kb)
@router.callback_query(F.data.startswith("guild_promote:"))
async def cb_guild_promote(callback: CallbackQuery):
    target_id = int(callback.data.split(":")[1])
    guild = await services.guild.get_user_guild(callback.from_user.id)
    if not guild:
        await callback.answer("Ты не в гильдии.", show_alert=True)
        return

    result = await services.guild.promote(guild["guild_id"], target_id, callback.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Участники", callback_data="guild_members")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="guild_menu")],
    ])
    await callback.message.edit_text(result["message"], reply_markup=kb)
