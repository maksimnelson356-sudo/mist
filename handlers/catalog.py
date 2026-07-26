from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from services.container import services

router = Router()

RARITY_ICONS = {
    "common": "⬜",
    "uncommon": "🟩",
    "rare": "🟦",
    "epic": "🟪",
    "legendary": "🟨",
}

_catalog_searching = set()


@router.callback_query(F.data == "catalog_menu")
async def cb_catalog_menu(callback: CallbackQuery):
    _catalog_searching.discard(callback.from_user.id)
    text = (
        "📖 <b>Каталог предметов</b>\n\n"
        "Выбери категорию:"
    )
    buttons = [
        [InlineKeyboardButton(text="📋 Все предметы", callback_data="catalog_list:all")],
        [InlineKeyboardButton(text="⬜ Обычные", callback_data="catalog_list:common")],
        [InlineKeyboardButton(text="🟩 Необычные", callback_data="catalog_list:uncommon")],
        [InlineKeyboardButton(text="🟦 Редкие", callback_data="catalog_list:rare")],
        [InlineKeyboardButton(text="🟪 Эпические", callback_data="catalog_list:epic")],
        [InlineKeyboardButton(text="🟨 Легендарные", callback_data="catalog_list:legendary")],
        [InlineKeyboardButton(text="🔮 Используемые", callback_data="catalog_list:usable")],
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="catalog_search")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data.startswith("catalog_list:"))
async def cb_catalog_list(callback: CallbackQuery):
    _catalog_searching.discard(callback.from_user.id)
    rarity = callback.data.split(":")[1]

    if rarity == "usable":
        items = await services.catalog.get_usable()
        title = "Используемые"
    elif rarity == "all":
        items = await services.catalog.get_all()
        title = "Все предметы"
    else:
        items = await services.catalog.get_by_rarity(rarity)
        title = services.catalog.get_rarity_name(rarity)

    text = f"📖 <b>{title}</b> ({len(items)} шт.)\n\n"
    for item in items[:20]:
        icon = RARITY_ICONS.get(item["rarity"], "❓")
        text += f"{icon} <b>{item['name']}</b>\n"
        if item.get("description"):
            text += f"   {item['description'][:60]}\n"
        text += "\n"

    if len(items) > 20:
        text += f"... и ещё {len(items) - 20} предметов.\n"

    buttons = [[InlineKeyboardButton(text="◀️ Назад", callback_data="catalog_menu")]]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data == "catalog_search")
async def cb_catalog_search(callback: CallbackQuery):
    _catalog_searching.add(callback.from_user.id)
    text = (
        "🔍 <b>Поиск предмета</b>\n\n"
        "Отправь название или часть названия:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="catalog_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
@router.message(F.text)
async def cb_catalog_search_query(message: Message):
    if message.from_user.id not in _catalog_searching:
        return
    if message.text.startswith("/"):
        return

    _catalog_searching.discard(message.from_user.id)
    query = message.text.strip()
    items = await services.catalog.search(query)

    text = f"🔍 Результаты: «{query}»\n\n"
    if not items:
        text += "Ничего не найдено."
    else:
        for item in items[:10]:
            icon = RARITY_ICONS.get(item["rarity"], "❓")
            text += f"{icon} <b>{item['name']}</b>\n"
            if item.get("description"):
                text += f"   {item['description'][:60]}\n"
            text += "\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Ещё поиск", callback_data="catalog_search")],
        [InlineKeyboardButton(text="◀️ Каталог", callback_data="catalog_menu")],
    ])
    await message.answer(text, reply_markup=kb)


@router.message(F.text.startswith("/catalog"))
async def cmd_catalog(message):
    items = await services.catalog.get_all()
    text = f"📖 <b>Каталог</b> — {len(items)} предметов\n\n"
    for item in items[:10]:
        icon = RARITY_ICONS.get(item["rarity"], "❓")
        text += f"{icon} {item['name']} — {item.get('base_value', 0)} 🪙\n"
    if len(items) > 10:
        text += f"... и ещё {len(items) - 10}\n"
    text += "\nПодробнее: /catalog"
    await message.answer(text)
