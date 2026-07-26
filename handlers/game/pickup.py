from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardButton

from services.container import services

from . import _shared as G

router = G.router


@router.callback_query(F.data == "ground_menu")
async def cb_ground_menu(callback: CallbackQuery):
    user = await services.player.get_or_create(callback.from_user.id)
    ground = await services.movement.get_ground_items(user["current_location"])

    if not ground:
        await callback.message.edit_text("На земле ничего нет.", reply_markup=G.back_menu_kb())
        return

    text = "📦 <b>На земле:</b>\n\n"
    for g in ground:
        name = g.get("name") or g["item_id"]
        rarity = g.get("rarity", "")
        icon = {"rare": "🔵", "epic": "🟣", "legendary": "🟡"}.get(rarity, "⚪")
        text += f"{icon} {name} x{g['quantity']}\n"

    kb = G.ground_items_kb(ground)
    kb.inline_keyboard.append([InlineKeyboardButton(text="🤲 Всё", callback_data="pickup_all")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])

    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.startswith("pickup:"))
async def cb_pickup(callback: CallbackQuery):
    item_id = callback.data.split(":")[1]
    user = await services.player.get_or_create(callback.from_user.id)
    result = await services.movement.pick_up_item(callback.from_user.id, user["current_location"], item_id)

    if result["success"]:
        user_quests = await services.quest.get_user_quests(callback.from_user.id)
        for uq in user_quests:
            if uq["status"] != "active":
                continue
            objectives = uq.get("objectives", [])
            for obj in objectives:
                if obj.get("type") == "collect" and obj.get("item") == item_id:
                    await services.quest.update_progress(callback.from_user.id, uq["quest_id"], obj["id"])

    await callback.message.edit_text(result["message"], reply_markup=G.post_action_kb())


@router.callback_query(F.data == "pickup_all")
async def cb_pickup_all(callback: CallbackQuery):
    user = await services.player.get_or_create(callback.from_user.id)
    ground = await services.movement.get_ground_items(user["current_location"])

    if not ground:
        await callback.message.edit_text("На земле ничего нет.", reply_markup=G.back_menu_kb())
        return

    picked = []
    for g in ground:
        result = await services.movement.pick_up_item(callback.from_user.id, user["current_location"], g["item_id"])
        if result["success"]:
            name = g.get("name") or g["item_id"]
            picked.append(f"{name} x{g['quantity']}")

            user_quests = await services.quest.get_user_quests(callback.from_user.id)
            for uq in user_quests:
                if uq["status"] != "active":
                    continue
                objectives = uq.get("objectives", [])
                for obj in objectives:
                    if obj.get("type") == "collect" and obj.get("item") == g["item_id"]:
                        await services.quest.update_progress(callback.from_user.id, uq["quest_id"], obj["id"])

    text = "🤲 <b>Подобрано:</b>\n\n" + "\n".join(f"• {p}" for p in picked)
    await callback.message.edit_text(text, reply_markup=G.post_action_kb())
