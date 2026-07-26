import json

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from services.container import services
from services.shop_service import ShopService

router = Router()

SHOP_LOCATIONS = ShopService.SHOP_LOCATIONS


def _shop_main_kb(user_gold: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💰 Золото: {user_gold} 🪙", callback_data="shop_balance")],
        [InlineKeyboardButton(text="🛒 Купля", callback_data="shop_buy")],
        [InlineKeyboardButton(text="💰 Продажа", callback_data="shop_sell")],
        [InlineKeyboardButton(text="🌸 Сезонные товары", callback_data="shop_seasonal")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])


@router.callback_query(F.data == "shop")
async def cb_shop(callback: CallbackQuery):
    user = await services.player.get_or_create(callback.from_user.id)
    loc = user["current_location"]

    available_shops = []
    for shop_id in SHOP_LOCATIONS:
        if loc == shop_id or _is_nearby(loc, shop_id):
            available_shops.append(shop_id)

    if not available_shops:
        text = "🛒 <b>Здесь нет магазинов.</b>\n\nПопробуй Торговую площадь или Теневой рынок."
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")]
        ])
        await callback.message.edit_text(text, reply_markup=kb)
        return

    text = f"🛒 <b>Магазин</b>\n\n💰 Золото: {user['gold']} 🪙\n\n"
    text += "🎯 Доступны торговые точки:\n"
    for shop_id in available_shops:
        text += f"  🏪 {SHOP_LOCATIONS[shop_id]}\n"

    buttons = []
    for shop_id in available_shops:
        buttons.append([InlineKeyboardButton(
            text=f"🏪 {SHOP_LOCATIONS[shop_id]}",
            callback_data=f"shop_open:{shop_id}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
@router.callback_query(F.data.startswith("shop_open:"))
async def cb_shop_open(callback: CallbackQuery):
    shop_id = callback.data.split(":")[1]
    user = await services.player.get_or_create(callback.from_user.id)

    items = await services.shop.get_shop_items(shop_id)

    text = f"🏪 <b>{SHOP_LOCATIONS.get(shop_id, shop_id)}</b>\n\n"
    text += f"💰 Золото: {user['gold']} 🪙\n\n"

    if not items:
        text += "Товаров пока нет."
    else:
        text += "<b>Товары:</b>\n\n"
        for item in items:
            rarity_map = {"common": "", "rare": "🔵", "epic": "🟣", "legendary": "🟡"}
            icon = rarity_map.get(item.get("rarity", ""), "⚪")
            stock_text = f" (осталось: {item['stock']})" if item["stock"] > 0 else ""
            req = ""
            if item["required_level"] > 1:
                req += f" 📊ур.{item['required_level']}"
            if item["required_karma"] > 0:
                req += f" ⚖️+{item['required_karma']}"
            text += f"{icon} <b>{item['name']}</b> — {item['price']} 🪙{stock_text}{req}\n"
            text += f"    <i>{item['description']}</i>\n\n"

    buttons = []
    for item in items:
        buttons.append([InlineKeyboardButton(
            text=f"🛒 {item['name']} — {item['price']} 🪙",
            callback_data=f"shop_buy_item:{shop_id}:{item['item_id']}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"shop_open:{shop_id}")])
    buttons.append([InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
@router.callback_query(F.data.startswith("shop_buy_item:"))
async def cb_shop_buy(callback: CallbackQuery):
    parts = callback.data.split(":")
    shop_id = parts[1]
    item_id = parts[2]

    result = await services.shop.buy(callback.from_user.id, shop_id, item_id)

    if result["success"]:
        user_quests = await services.quest.get_user_quests(callback.from_user.id)
        for uq in user_quests:
            if uq["status"] != "active":
                continue
            objectives = json.loads(uq["objectives"]) if isinstance(uq["objectives"], str) else uq["objectives"]
            for obj in objectives:
                if obj.get("type") == "collect" and obj.get("item") == item_id:
                    await services.quest.update_progress(callback.from_user.id, uq["quest_id"], obj["id"])

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Ещё", callback_data=f"shop_open:{shop_id}")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])

    await callback.message.edit_text(result["message"], reply_markup=kb)
@router.callback_query(F.data == "shop_sell")
async def cb_shop_sell(callback: CallbackQuery):
    items = await services.inventory.get(callback.from_user.id)

    if not items:
        text = "🎒 <b>Инвентарь пуст.</b>\nНечего продавать."
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")]
        ])
        await callback.message.edit_text(text, reply_markup=kb)
        return

    rarity_prices = {"common": 3, "rare": 8, "epic": 20, "legendary": 50}

    text = "💰 <b>Продать предметы</b>\n\n"
    buttons = []
    for item in items:
        name = item.get("name") or item["item_id"]
        price = rarity_prices.get(item.get("rarity", ""), 3)
        text += f"• {name} x{item['quantity']} — {price} 🪙\n"

        buttons.append([InlineKeyboardButton(
            text=f"💰 {name} — {price} 🪙",
            callback_data=f"shop_sell_item:{item['item_id']}"
        )])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="shop_sell")])
    buttons.append([InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
@router.callback_query(F.data.startswith("shop_sell_item:"))
async def cb_shop_sell_item(callback: CallbackQuery):
    item_id = callback.data.split(":")[1]
    result = await services.shop.sell(callback.from_user.id, item_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Ещё продать", callback_data="shop_sell")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])

    await callback.message.edit_text(result["message"], reply_markup=kb)
@router.callback_query(F.data == "shop_balance")
async def cb_shop_balance(callback: CallbackQuery):
    user = await services.player.get_or_create(callback.from_user.id)
    text = f"💰 <b>Золото:</b> {user['gold']} 🪙\n\n"
    text += "<i>Золото можно заработать квестами, продажей предметов или PvP.</i>"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="shop")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
def _is_nearby(loc1: str, loc2: str) -> bool:
    connections = {
        "fishing_village": ["riverbank", "market_square"],
        "market_square": ["fishing_village", "temple_of_shadows", "shadow_market"],
        "shadow_market": ["market_square", "temple_of_shadows"],
        "temple_of_shadows": ["market_square", "void_gate", "shadow_market"],
        "riverbank": ["dark_forest", "fishing_village", "underwater_cave", "dark_harbour", "abandoned_camp"],
        "dark_harbour": ["dark_forest", "forgotten_graveyard", "riverbank"],
        "abandoned_mine": ["crystal_cave", "ash_fields"],
        "crystal_cave": ["ancient_ruins", "underwater_cave", "ash_fields", "abandoned_mine"],
    }
    return loc2 in connections.get(loc1, []) or loc1 in connections.get(loc2, [])


@router.callback_query(F.data == "shop_seasonal")
async def cb_shop_seasonal(callback: CallbackQuery):
    user = await services.player.get_or_create(callback.from_user.id)
    state = services.world_engine.get_state()
    season = state.get("season", "spring") if state else "spring"

    SEASON_NAMES = {"spring": "Весна", "summer": "Лето", "autumn": "Осень", "winter": "Зима"}
    SEASON_ICONS = {"spring": "🌸", "summer": "☀️", "autumn": "🍂", "winter": "❄️"}

    items = await services.shop.get_seasonal_items(season)

    text = f"{SEASON_ICONS.get(season, '')} <b>Сезонные товары — {SEASON_NAMES.get(season, season)}</b>\n\n"

    buttons = []
    for item in items:
        text += f"• <b>{item['name']}</b> — {item['price']} 🪙\n  <i>{item['description']}</i>\n"
        can_buy = user["gold"] >= item["price"]
        icon = "✅" if can_buy else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{icon} {item['name']} ({item['price']} 🪙)",
            callback_data=f"shop_buy_seasonal:{item['item_id']}"
        )])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="shop")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
@router.callback_query(F.data.startswith("shop_buy_seasonal:"))
async def cb_shop_buy_seasonal(callback: CallbackQuery):
    item_id = callback.data.split(":", 1)[1]
    user = await services.player.get_or_create(callback.from_user.id)

    state = services.world_engine.get_state()
    season = state.get("season", "spring") if state else "spring"
    items = await services.shop.get_seasonal_items(season)
    item = next((i for i in items if i["item_id"] == item_id), None)

    if not item:
        await callback.answer("Товар не найден.", show_alert=True)
        return

    if user["gold"] < item["price"]:
        await callback.answer(f"Нужно {item['price']} 🪙, у тебя {user['gold']} 🪙", show_alert=True)
        return

    await services.economy.remove(callback.from_user.id, "gold", item["price"])
    await services.inventory.add(callback.from_user.id, item_id)

    await callback.answer(f"✅ Купил «{item['name']}» за {item['price']} 🪙", show_alert=True)
    await cb_shop(callback)
