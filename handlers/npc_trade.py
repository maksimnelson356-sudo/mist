from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from services.container import services

router = Router()


@router.callback_query(F.data.startswith("npc_trade:"))
async def cb_npc_trade(callback: CallbackQuery):
    npc_id = callback.data.split(":", 1)[1]
    npc = await services.npc.get(npc_id)
    if not npc:
        await callback.answer("NPC не найден.", show_alert=True)
        return

    shop_id = npc_id
    items = await services.shop.get_shop_items(shop_id)

    text = f"🛒 <b>Торговля с {npc['name']}</b>\n\n"
    if not items:
        text += "Нет товаров в наличии."
    else:
        for item in items:
            stock = f"({item['stock']})" if item['stock'] > 0 else "(нет)"
            text += f"• {item['name']} — {item['price']} 🪙 {stock}\n"

    buttons = []
    for item in items:
        if item['stock'] != 0:
            buttons.append([InlineKeyboardButton(
                text=f"🛒 {item['name']} — {item['price']} 🪙",
                callback_data=f"npc_buy:{npc_id}:{item['item_id']}"
            )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"npc_talk:{npc_id}")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data.startswith("npc_buy:"))
async def cb_npc_buy(callback: CallbackQuery):
    parts = callback.data.split(":", 2)
    npc_id = parts[1]
    item_id = parts[2]

    result = await services.shop.buy(callback.from_user.id, npc_id, item_id)

    if result["success"]:
        text = f"✅ {result['message']}"
    else:
        text = f"❌ {result['message']}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Ещё товары", callback_data=f"npc_trade:{npc_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"npc_talk:{npc_id}")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
