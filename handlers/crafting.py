import json
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
import game_engine as ge

router = Router()


@router.callback_query(F.data == "crafting_menu")
async def cb_crafting_menu(callback: CallbackQuery):
    user = await ge.get_or_create_user(callback.from_user.id)
    if not user["is_alive"]:
        await callback.message.edit_text("💀 Ты мёртв.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
        ]))
        await callback.answer()
        return

    recipes = await ge.get_crafting_recipes(user["current_location"])

    if not recipes:
        text = (
            "⚒️ <b>Крафт</b>\n\n"
            "Здесь нет верстака для крафта.\n\n"
            "<i>Попробуй Хрустальную пещеру, Топи ведьмы или Библиотеку эхов.</i>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")]
        ])
        await callback.message.edit_text(text, reply_markup=kb)
        await callback.answer()
        return

    text = f"⚒️ <b>Крафт</b>\n\n📍 <i>Доступные рецепты:</i>\n\n"
    buttons = []
    for r in recipes:
        ingredients = json.loads(r["ingredients"]) if isinstance(r["ingredients"], str) else r["ingredients"]
        ing_text = ", ".join(f"{i['item_id']}x{i.get('qty',1)}" for i in ingredients)
        text += f"🔨 <b>{r['name']}</b>\n"
        text += f"   <i>{r['description']}</i>\n"
        text += f"   Материалы: {ing_text}\n"
        text += f"   ⭐ +{r['xp_reward']} XP\n\n"

        can_craft = True
        for ing in ingredients:
            if not await ge.has_item(callback.from_user.id, ing["item_id"], ing.get("qty", 1)):
                can_craft = False
                break

        icon = "✅" if can_craft else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{icon} {r['name']}",
            callback_data=f"craft:{r['recipe_id']}"
        )])

    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("craft:"))
async def cb_craft(callback: CallbackQuery):
    recipe_id = callback.data.split(":")[1]
    result = await ge.craft_item(callback.from_user.id, recipe_id)

    if result["success"]:
        user_quests = await ge.get_user_quests(callback.from_user.id)
        for uq in user_quests:
            if uq["status"] != "active":
                continue
            objectives = json.loads(uq["objectives"]) if isinstance(uq["objectives"], str) else uq["objectives"]
            for obj in objectives:
                if obj.get("type") == "craft" and obj.get("recipe") in ("any", recipe_id):
                    await ge.update_quest_progress(callback.from_user.id, uq["quest_id"], obj["id"])

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚒️ Ещё крафт", callback_data="crafting_menu")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])

    await callback.message.edit_text(result["message"], reply_markup=kb)
    await callback.answer()
