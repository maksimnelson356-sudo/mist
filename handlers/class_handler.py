from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from services.container import services
from services.class_service import CLASSES

router = Router()


@router.callback_query(F.data == "class_menu")
async def cb_class_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_class = await services.player_class.get_class(user_id)
    user = await services.player.get_or_create(user_id)

    is_new = not user.get("player_class") or user["player_class"] == "warrior" and user.get("class_level", 1) == 1

    if is_new:
        text = (
            "⚔️ <b>Выбери свой путь</b>\n\n"
            "Ты просыпаешься в тумане. Не помнишь, кто ты.\n"
            "Но туман шепчет — ты должен выбрать дорогу.\n\n"
            "Каждый класс определяет твой стиль боя и способности."
        )
        buttons = []
        for class_id, class_def in CLASSES.items():
            buttons.append([InlineKeyboardButton(
                text=f"{class_def['icon']} {class_def['name']}",
                callback_data=f"class_select:{class_id}"
            )])
        buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    else:
        text = (
            f"{user_class['icon']} <b>{user_class['name']}</b>\n"
            f"Уровень класса: {user_class['class_level']}\n\n"
            f"{user_class['description']}\n\n"
            f"📊 Базовые характеристики:\n"
            f"  🗡 Атака: {user_class['base_stats']['attack']}\n"
            f"  🛡 Защита: {user_class['base_stats']['defense']}\n"
            f"  ❤️ HP: {user_class['base_stats']['max_hp']}\n\n"
        )

        if user_class["abilities"]:
            text += "🔮 <b>Способности:</b>\n"
            for a in user_class["abilities"]:
                text += f"  • {a['name']} (ур. {a['level']}) — {a['description']}\n"

        buttons = [
            [InlineKeyboardButton(text="🔮 Способности", callback_data="class_abilities")],
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
        ]
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("class_select:"))
async def cb_class_select(callback: CallbackQuery):
    class_id = callback.data.split(":")[1]
    user_id = callback.from_user.id

    result = await services.player_class.select_class(user_id, class_id)

    if result["success"]:
        text = f"✅ {result['message']}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚔️ Мой класс", callback_data="class_menu")],
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
        ])
    else:
        text = f"❌ {result['message']}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="class_menu")],
        ])

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "class_abilities")
async def cb_class_abilities(callback: CallbackQuery):
    user_class = await services.player_class.get_class(callback.from_user.id)

    text = f"🔮 <b>Способности: {user_class['name']}</b>\n\n"

    all_abilities = CLASSES.get(user_class["class_id"], {}).get("abilities", [])

    for a in all_abilities:
        unlocked = a["level"] <= user_class["class_level"]
        icon = "✅" if unlocked else "🔒"
        text += f"{icon} <b>{a['name']}</b> (ур. {a['level']})\n"
        text += f"   {a['description']}\n"
        text += f"   Кулдаун: {a['cooldown']} ходов\n\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="class_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
