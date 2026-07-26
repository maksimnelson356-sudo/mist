from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from services.container import services

router = Router()

REGION_NAMES = {
    "civilization": "Цивилизация",
    "dark_forest": "Тёмный лес",
    "mountains": "Горы",
    "coast": "Побережье",
}

CATEGORY_NAMES = {
    "food": "🍞 Еда",
    "weapons": "⚔️ Оружие",
    "armor": "🛡️ Броня",
    "potions": "🧪 Зелья",
    "tools": "🔧 Инструменты",
    "resources": "🪵 Ресурсы",
    "magic": "🔮 Магия",
}


@router.callback_query(F.data == "market_menu")
async def cb_market_menu(callback: CallbackQuery):
    user = await services.player.get(callback.from_user.id)
    current_loc = user.get("location_id", "") if user else ""

    region_id = None
    for reg, locs in {
        "civilization": ["fishing_village", "market_square", "abandoned_camp"],
        "dark_forest": ["dark_forest", "enchanted_grove", "white_forest"],
        "mountains": ["mountain_pass", "frost_hollow", "ruins"],
        "coast": ["coast", "shipyard", "lighthouse"],
    }.items():
        if current_loc in locs:
            region_id = reg
            break

    overview = await services.market.get_market_overview(region_id)

    text = f"📊 <b>Рынок — {overview['region']}</b>\n\n"

    buttons = []
    for cat, info in overview["categories"].items():
        name = CATEGORY_NAMES.get(cat, cat)
        text += f"{name}: {info['status']} ({info['modifier']:.0%})\n"
        buttons.append([InlineKeyboardButton(
            text=f"{name} {info['status']}",
            callback_data=f"market_category:{cat}"
        )])

    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("market_category:"))
async def cb_market_category(callback: CallbackQuery):
    category = callback.data.split(":")[1]
    overview = await services.market.get_market_overview()

    info = overview["categories"].get(category)
    if not info:
        await callback.answer("Категория не найдена.", show_alert=True)
        return

    name = CATEGORY_NAMES.get(category, category)
    mod = info["modifier"]

    text = (
        f"{name}\n\n"
        f"Спрос: {info['demand']}\n"
        f"Модификатор цены: {mod:.0%}\n"
        f"Статус: {info['status']}\n\n"
    )

    if mod < 0.9:
        text += "💡 Хороший момент для покупки!"
    elif mod > 1.1:
        text += "💡 Подожди — цены высокие."
    else:
        text += "💡 Цены стабильны."

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="market_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
