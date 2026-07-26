from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from services.container import services

from . import _shared as G

router = G.router

FOOD_HUNGER = {
    "bread": 20, "fish": 25, "apple": 15, "cheese": 30,
    "dried_meat": 35, "berry": 10,
}


@router.callback_query(F.data == "heal")
async def cb_heal(callback: CallbackQuery):
    user = await services.player.get_or_create(callback.from_user.id)

    if not user["is_alive"]:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
        ])
        await callback.message.edit_text("💀 Ты мёртв. Очнись сначала.", reply_markup=kb)
        return

    free_heal = False
    try:
        bonuses = await services.daily_event.get_active_daily_bonuses()
        free_heal = bonuses.get("free_heal", False)
    except Exception:
        pass

    if free_heal:
        result = await services.player.rest_heal(callback.from_user.id)
        text = "💚 " + result["message"] + "\n\n<i>Целебные источники исцеляют бесплатно!</i>"
    else:
        inv = await services.inventory.get(callback.from_user.id)
        healing_items = [i for i in inv if i["item_id"] in ("healing_herb", "shadow_essence", "frozen_tear")]

        if healing_items:
            item = healing_items[0]
            result = await services.inventory.use_item(callback.from_user.id, item["item_id"])
            text = result["message"]
        else:
            result = await services.player.rest_heal(callback.from_user.id)
            text = result["message"]

    kb = G.post_action_kb()
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "eat_food")
async def cb_eat_food(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await services.player.get_or_create(user_id)

    if not user["is_alive"]:
        await callback.answer("💀 Ты мёртв.", show_alert=True)
        return

    inventory = await services.inventory.get(user_id)
    food_items = [i for i in inventory if i["item_id"] in FOOD_HUNGER]

    if not food_items:
        await callback.answer("Нет еды в инвентаре! Купи на рынке.", show_alert=True)
        return

    buttons = []
    for item in food_items:
        hunger_restore = FOOD_HUNGER[item["item_id"]]
        qty = item.get("quantity", 1)
        buttons.append([InlineKeyboardButton(
            text=f"🍖 {item['name']} ×{qty} (+{hunger_restore} 🍖)",
            callback_data=f"eat:{item['item_id']}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")])

    text = "🍖 <b>Поесть</b>\n\nВыбери еду:"
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")


@router.callback_query(F.data.startswith("eat:"))
async def cb_eat(callback: CallbackQuery):
    item_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id

    if not await services.inventory.has(user_id, item_id):
        await callback.answer("Предмет не найден!", show_alert=True)
        return

    hunger_restore = FOOD_HUNGER.get(item_id, 10)
    await services.inventory.remove(user_id, item_id)
    result = await services.player.feed(user_id, hunger_restore)

    await callback.answer(result["message"], show_alert=True)

    from .menu import cb_main_menu
    await cb_main_menu(callback)


@router.callback_query(F.data == "inventory")
async def cb_inventory(callback: CallbackQuery):
    items = await services.inventory.get(callback.from_user.id)

    if not items:
        text = "🎒 <b>Инвентарь пуст</b>\n\nТы ничего не несёшь. Пока."
        kb = G.back_menu_kb()
    else:
        text = "🎒 <b>Твой инвентарь:</b>\n\n"
        buttons = []
        for item in items:
            magic = " ✨" if item["is_magic"] else ""
            rarity_map = {"common": "", "rare": "🔵", "epic": "🟣", "legendary": "🟡"}
            rarity = rarity_map.get(item.get("rarity", ""), "")
            name = item.get("name") or item["item_id"]
            text += f"• {rarity} {name} x{item['quantity']}{magic}\n"

            if item.get("is_usable"):
                buttons.append([InlineKeyboardButton(
                    text=f"🧪 Использовать: {name}",
                    callback_data=f"use_item:{item['item_id']}"
                )])

        buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.startswith("use_item:"))
async def cb_use_item(callback: CallbackQuery):
    item_id = callback.data.split(":", 1)[1]
    result = await services.inventory.use_item(callback.from_user.id, item_id)
    kb = G.post_action_kb()
    await callback.message.edit_text(result["message"], reply_markup=kb)
