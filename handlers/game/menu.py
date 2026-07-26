from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from scenes import LOC_SCENES, SCENE_DIVIDER
from services.container import services

from . import _shared as G

router = G.router


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    user = await services.player.get_or_create(callback.from_user.id, callback.from_user.username)
    await services.player.update_last_seen(callback.from_user.id)

    if not user["is_alive"]:
        text = "<pre>💀\n🕯️👁🕯️\n💀</pre>\n💀 <b>Ты мёртв.</b>\n\nТуман накрыл тебя."
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
        ])
        await callback.message.edit_text(text, reply_markup=kb)
        return

    catchup = await services.player.get_catchup_summary(callback.from_user.id)

    if catchup and catchup.get("hunger_loss", 0) > 0:
        new_hunger = catchup["new_hunger"]
        from sqlalchemy import update as sa_update

        from database.base import get_db
        from database.models.user import UserModel
        async for db in get_db():
            await db.execute(
                sa_update(UserModel).where(UserModel.user_id == callback.from_user.id).values(hunger=new_hunger)
            )
            await db.commit()
            break
        user["hunger"] = new_hunger

    loc = await services.movement.get_location(user["current_location"])
    loc_name = loc["name"] if loc else await services.movement.get_location_name(user["current_location"])
    scene = LOC_SCENES.get(user["current_location"], "")

    text = ""
    if scene:
        text += f"<pre>{scene}</pre>\n{SCENE_DIVIDER}\n"

    ws = services.world_engine.get_state()
    if ws:
        season_names = {"spring": "Весна", "summer": "Лето", "autumn": "Осень", "winter": "Зима"}
        season = season_names.get(ws.get("season", ""), ws.get("season", ""))
        text += f"🌍 День {ws.get('game_day', '?')}, {ws.get('game_hour', 8):02d}:00 — {season}\n"

    try:
        daily_bonuses = await services.daily_event.get_active_daily_bonuses()
        if daily_bonuses:
            bonus_text = []
            if "shop_discount" in daily_bonuses:
                bonus_text.append(f"🛒 -{int((1 - daily_bonuses['shop_discount']) * 100)}% в магазинах")
            if "xp_mult" in daily_bonuses:
                bonus_text.append(f"⚔️ +{int((daily_bonuses['xp_mult'] - 1) * 100)}% XP")
            if "gold_mult" in daily_bonuses:
                bonus_text.append(f"🪙 x{daily_bonuses['gold_mult']} золота")
            if "free_heal" in daily_bonuses:
                bonus_text.append("💚 Бесплатное лечение")
            if bonus_text:
                text += f"📜 Сегодня: {' | '.join(bonus_text)}\n"
    except Exception:
        pass

    try:
        seasonal_rewards = await services.seasonal_event.get_active_seasonal_rewards()
        if seasonal_rewards:
            sr_text = []
            if "xp_bonus" in seasonal_rewards:
                sr_text.append(f"+{int((seasonal_rewards['xp_bonus'] - 1) * 100)}% XP")
            if "gold_bonus" in seasonal_rewards:
                sr_text.append(f"+{int((seasonal_rewards['gold_bonus'] - 1) * 100)}% золота")
            if sr_text:
                text += f"🌿 Сезон: {' | '.join(sr_text)}\n"
    except Exception:
        pass

    if catchup:
        season_names = {"spring": "Весна", "summer": "Лето", "autumn": "Осень", "winter": "Зима"}
        season = season_names.get(catchup["season"], catchup["season"])
        text += f"⏰ <b>Пока тебя не было: {catchup['game_days_away']} дн. ({catchup['hours_away']} ч.)</b>\n"
        text += f"🌍 Мир: День {catchup['world_day']}, {season}\n"

        if catchup.get("events"):
            text += "\n<b>Что произошло:</b>\n"
            for ev in catchup["events"][:5]:
                text += f"  📜 {ev['name']}\n"
        else:
            text += "\nНичего особенного не случилось.\n"

        if catchup.get("hunger_loss", 0) > 0:
            text += f"\n🍖 Голод: -{catchup['hunger_loss']} (было {user.get('hunger', 100)}, стало {catchup['new_hunger']})\n"

        if catchup.get("location"):
            loc_data = catchup["location"]
            text += f"\n📍 Локация: {loc_data['name']}\n"
            text += f"  ⚠️ Опасность: {loc_data['danger_level']} | 🍖 Еда: {loc_data['food_supply']}\n"
        text += "\n"

    text += (
        f"📍 <b>{loc_name}</b>\n"
        f"❤️ HP: {user['hp']}/{user['max_hp']} | ⭐ Ур. {user['level']}\n"
        f"🍖 Голод: {user.get('hunger', 100)}/{user.get('max_hunger', 100)}\n"
        f"🎒 Воспоминаний: {user['memories']} | ⚖️ Карма: {user['karma']}"
    )
    try:
        await callback.message.edit_text(text, reply_markup=G.main_menu_kb())
    except Exception:
        await callback.message.answer(text, reply_markup=G.main_menu_kb())
