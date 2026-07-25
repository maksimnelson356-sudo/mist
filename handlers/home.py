from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import update
from database.base import get_db
from database.models.user import UserModel
from services.container import services
from services.home_service import HOME_TYPES, ROOM_DEFS, HOME_MOODS

router = Router()


@router.callback_query(F.data == "home_menu")
async def cb_home_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    home = await services.home.get_home(user_id)

    if not home:
        text = (
            "🏠 <b>У тебя нет дома</b>\n\n"
            "Ты скитаешься по миру. Но туман помнит — "
            "каждый путник мечтает о крыше над головой.\n\n"
            "Построй дом и у тебя будет место, куда можно вернуться."
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔨 Построить дом", callback_data="home_build")],
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
        ])
        await callback.message.edit_text(text, reply_markup=kb)
        await callback.answer()
        return

    type_def = HOME_TYPES.get(home["home_type"], {})
    type_name = type_def.get("name", home["home_type"])
    mood_text = HOME_MOODS.get(home["mood"], "Тихо.")
    rooms = home.get("rooms", [])
    room_names = [r.get("name", "?") for r in rooms] if rooms else ["Пусто"]

    condition_icon = "🟢" if home["condition"] >= 70 else "🟡" if home["condition"] >= 40 else "🔴"

    text = (
        f"🏠 <b>{home['name']}</b>\n"
        f"<i>{type_name} • Ур. {home['level']}/{home['max_level']}</i>\n\n"
        f"{mood_text}\n\n"
        f"{condition_icon} Состояние: {home['condition']}%\n"
        f"🛏 Комфорт: {home['comfort']}\n"
        f"🛡 Защита: {home['defenses']}\n"
        f"📦 Вместимость: {home['storage_capacity']}\n"
        f"💰 Доход: {home['income_per_day']}/день\n\n"
        f"🚪 Комнаты: {', '.join(room_names)}"
    )

    buttons = [
        [InlineKeyboardButton(text="🚶 Войти", callback_data="home_enter")],
        [InlineKeyboardButton(text="🚪 Комнаты", callback_data="home_rooms")],
        [InlineKeyboardButton(text="📦 Хранилище", callback_data="home_storage")],
        [InlineKeyboardButton(text="⬆️ Улучшить", callback_data="home_upgrade")],
        [InlineKeyboardButton(text="📜 История", callback_data="home_history")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ]

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "home_enter")
async def cb_home_enter(callback: CallbackQuery):
    result = await services.home.visit_home(callback.from_user.id)

    if not result["success"]:
        await callback.answer(result["message"], show_alert=True)
        return

    home = result["home"]
    rooms = home.get("rooms", [])

    text = (
        f"🏠 <b>{home['name']}</b>\n\n"
        f"{result['mood_text']}\n\n"
    )

    if rooms:
        text += "<b>Ты входишь в:</b>\n"
        for r in rooms:
            level = r.get("level", 1)
            text += f"  • {r.get('name', '?')} (ур. {level})\n"
    else:
        text += "Дом пуст. Добавь комнаты.\n"

    text += f"\n📦 Состояние: {home['condition']}%"

    buttons = [
        [InlineKeyboardButton(text="🚪 Комнаты", callback_data="home_rooms")],
        [InlineKeyboardButton(text="⬆️ Улучшить", callback_data="home_upgrade")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="home_menu")],
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "home_build")
async def cb_home_build(callback: CallbackQuery):
    text = (
        "🔨 <b>Построить дом</b>\n\n"
        "Выбери тип постройки:\n\n"
    )

    buttons = []
    for type_id, type_def in HOME_TYPES.items():
        text += f"• <b>{type_def['name']}</b> — макс. ур. {type_def['max_level']}, "
        text += f"комфорт {type_def['base_comfort']}, защита {type_def['base_defenses']}\n"
        buttons.append([InlineKeyboardButton(
            text=f"🔨 {type_def['name']}",
            callback_data=f"home_build:{type_id}"
        )])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="home_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("home_build:"))
async def cb_home_build_confirm(callback: CallbackQuery):
    user_id = callback.from_user.id
    type_id = callback.data.split(":")[1]
    user = await services.player.get_or_create(user_id)
    location = user["current_location"]

    result = await services.home.create_home(user_id, location, type_id)

    if result["success"]:
        text = f"✅ {result['message']}\n\n🏠 Твой новый дом в {location}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Мой дом", callback_data="home_menu")],
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
        ])
    else:
        text = f"❌ {result['message']}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="home_build")],
        ])

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "home_rooms")
async def cb_home_rooms(callback: CallbackQuery):
    user_id = callback.from_user.id
    home = await services.home.get_home(user_id)

    if not home:
        await callback.answer("У тебя нет дома.", show_alert=True)
        return

    rooms = home.get("rooms", [])

    text = f"🚪 <b>Комнаты ({len(rooms)})</b>\n\n"

    if rooms:
        for r in rooms:
            level = r.get("level", 1)
            text += f"• <b>{r.get('name', '?')}</b> — ур. {level}\n"
    else:
        text += "Дом пуст. Добавь первую комнату!\n"

    text += "\n<b>Доступные комнаты:</b>\n"
    buttons = []
    existing_types = [r.get("type") for r in rooms]

    for room_id, room_def in ROOM_DEFS.items():
        if room_id in existing_types:
            continue
        cost = room_def.get("cost_gold", 0)
        text += f"  • {room_def['name']} — {cost} 🪙\n"
        buttons.append([InlineKeyboardButton(
            text=f"➕ {room_def['name']} ({cost} 🪙)",
            callback_data=f"home_add_room:{room_id}"
        )])

    if not buttons:
        text += "\nВсе комнаты построены!"

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="home_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("home_add_room:"))
async def cb_home_add_room(callback: CallbackQuery):
    user_id = callback.from_user.id
    room_type = callback.data.split(":")[1]

    room_def = ROOM_DEFS.get(room_type)
    if not room_def:
        await callback.answer("Комната не найдена.", show_alert=True)
        return

    cost = room_def.get("cost_gold", 0)
    user = await services.player.get_or_create(user_id)

    if user["gold"] < cost:
        await callback.answer(f"Нужно {cost} 🪙, у тебя {user['gold']} 🪙", show_alert=True)
        return

    async for db in get_db():
        await db.execute(
            update(UserModel).where(UserModel.user_id == user_id).values(gold=user["gold"] - cost)
        )
        await db.commit()

    result = await services.home.add_room(user_id, room_type)

    if result["success"]:
        text = f"✅ {result['message']}"
    else:
        text = f"❌ {result['message']}"
        async for db in get_db():
            await db.execute(
                update(UserModel).where(UserModel.user_id == user_id).values(gold=user["gold"])
            )
            await db.commit()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚪 Комнаты", callback_data="home_rooms")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "home_upgrade")
async def cb_home_upgrade(callback: CallbackQuery):
    user_id = callback.from_user.id
    home = await services.home.get_home(user_id)

    if not home:
        await callback.answer("У тебя нет дома.", show_alert=True)
        return

    if home["level"] >= home["max_level"]:
        await callback.answer("Дом уже максимального уровня!", show_alert=True)
        return

    cost = home["level"] * 100
    user = await services.player.get_or_create(user_id)

    text = (
        f"⬆️ <b>Улучшение дома</b>\n\n"
        f"Текущий уровень: {home['level']}/{home['max_level']}\n"
        f"Стоимость: {cost} 🪙\n\n"
        f"После улучшения:\n"
        f"  • Комфорт: {home['comfort']} → {home['comfort'] + 5}\n"
        f"  • Защита: {home['defenses']} → {home['defenses'] + 3}\n"
        f"  • Вместимость: {home['storage_capacity']} → {home['storage_capacity'] + 10}"
    )

    buttons = []
    if user["gold"] >= cost:
        buttons.append([InlineKeyboardButton(
            text=f"⬆️ Улучшить ({cost} 🪙)",
            callback_data="home_upgrade_confirm"
        )])
    else:
        text += f"\n\n❌ У тебя {user['gold']} 🪙"

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="home_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "home_upgrade_confirm")
async def cb_home_upgrade_confirm(callback: CallbackQuery):
    user_id = callback.from_user.id
    home = await services.home.get_home(user_id)

    if not home:
        await callback.answer("У тебя нет дома.", show_alert=True)
        return

    cost = home["level"] * 100
    user = await services.player.get_or_create(user_id)

    if user["gold"] < cost:
        await callback.answer(f"Нужно {cost} 🪙", show_alert=True)
        return

    async for db in get_db():
        await db.execute(
            update(UserModel).where(UserModel.user_id == user_id).values(gold=user["gold"] - cost)
        )
        await db.commit()

    result = await services.home.upgrade_home(user_id)

    if result["success"]:
        text = f"✅ {result['message']}"
    else:
        text = f"❌ {result['message']}"
        async for db in get_db():
            await db.execute(
                update(UserModel).where(UserModel.user_id == user_id).values(gold=user["gold"])
            )
            await db.commit()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Мой дом", callback_data="home_menu")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "home_history")
async def cb_home_history(callback: CallbackQuery):
    user_id = callback.from_user.id
    home = await services.home.get_home(user_id)

    if not home:
        await callback.answer("У тебя нет дома.", show_alert=True)
        return

    events = home.get("events_history", [])

    text = "📜 <b>История дома</b>\n\n"

    if events:
        for ev in events[-10:]:
            text += f"• {ev.get('message', 'Событие')}\n"
    else:
        text += "Пока ничего особенного.\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="home_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "home_storage")
async def cb_home_storage(callback: CallbackQuery):
    user_id = callback.from_user.id
    home = await services.home.get_home(user_id)

    if not home:
        await callback.answer("У тебя нет дома.", show_alert=True)
        return

    storage = home.get("storage", [])
    capacity = home.get("storage_capacity", 20)

    text = f"📦 <b>Хранилище</b> ({len(storage)}/{capacity})\n\n"
    if storage:
        for s in storage:
            text += f"• {s.get('item_id', '?')} ×{s.get('qty', 1)}\n"
    else:
        text += "Пусто.\n"

    text += "\nВыбери предмет из инвентаря для депозита или снятия:"

    buttons = []
    inventory = await services.inventory.get(user_id)
    for inv_item in inventory[:10]:
        buttons.append([
            InlineKeyboardButton(
                text=f"📥 {inv_item['name']} ×{inv_item.get('quantity', 1)}",
                callback_data=f"home_deposit:{inv_item['item_id']}"
            )
        ])

    for s in storage[:10]:
        buttons.append([
            InlineKeyboardButton(
                text=f"📤 {s['item_id']} ×{s.get('qty', 1)}",
                callback_data=f"home_withdraw:{s['item_id']}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="home_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("home_deposit:"))
async def cb_home_deposit(callback: CallbackQuery):
    item_id = callback.data.split(":", 1)[1]
    result = await services.home.storage_deposit(callback.from_user.id, item_id)
    await callback.answer(result["message"], show_alert=True)
    await cb_home_storage(callback)


@router.callback_query(F.data.startswith("home_withdraw:"))
async def cb_home_withdraw(callback: CallbackQuery):
    item_id = callback.data.split(":", 1)[1]
    result = await services.home.storage_withdraw(callback.from_user.id, item_id)
    await callback.answer(result["message"], show_alert=True)
    await cb_home_storage(callback)
