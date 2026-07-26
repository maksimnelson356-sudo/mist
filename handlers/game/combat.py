from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from scenes import CREATURE_SCENES, SCENE_DIVIDER
from services.container import services

from . import _shared as G

router = G.router


@router.callback_query(F.data == "fight_menu")
async def cb_fight_menu(callback: CallbackQuery):
    user = await services.player.get_or_create(callback.from_user.id)
    if not user["is_alive"]:
        await callback.message.edit_text("💀 Ты мёртв.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
        ]))
        return
    creatures = await services.movement.get_creatures_at(user["current_location"])

    hostile = [c for c in creatures if c["disposition"] in ("hostile", "neutral") and c["is_alive"]]

    if not hostile:
        text = "⚔️ <b>Здесь никого нет для боя.</b>\n\nПопробуй осмотреться или перейти в другое место."
        kb = G.post_action_kb()
    else:
        text = "⚔️ <b>Кого атакуем?</b>\n\n"
        for c in hostile:
            icon = "🔴" if c["disposition"] == "hostile" else "🟡"
            scene = CREATURE_SCENES.get(c["creature_id"], "")
            if scene:
                text += f"<pre>{scene}</pre>\n"
            text += f"{icon} {c['name']} — HP: {c['hp']}, Атака: {c['attack']}\n\n"
        kb = G.combat_kb(hostile)

    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.startswith("attack:"))
async def cb_attack(callback: CallbackQuery):
    creature_id = callback.data.split(":")[1]
    result = await services.combat.start(callback.from_user.id, creature_id)

    if not result["success"]:
        await callback.message.edit_text(result["message"], reply_markup=G.post_action_kb())
        return

    combat = await services.combat.resolve(callback.from_user.id, creature_id)

    scene = CREATURE_SCENES.get(creature_id, "")
    text = ""
    if scene:
        text += f"<pre>{scene}</pre>\n{SCENE_DIVIDER}\n"
    text += f"⚔️ <b>Бой с {result['creature']['name']}</b>\n\n"

    for rd in combat.get("rounds", [])[:5]:
        ud = rd.get("user_damage", 0)
        cd = rd.get("creature_damage", 0)
        text += f"Раунд {rd['round']}: -{ud} HP, -{cd} HP\n"

    text += f"\n❤️ Твоё HP: {combat['user_hp']}\n"

    if combat["outcome"] == "victory":
        text += "\n<pre>🏆⚔️🏆\n🔥🐺🔥\n🏆⚔️🏆</pre>\n"
        text += f"🏆 <b>ПОБЕДА!</b>\n+{combat['xp_gained']} XP"
        if combat.get("leveled"):
            text += f"\n\n<pre>⭐\n🔥⚔️🔥\n⭐</pre>\n⭐ <b>УРОВЕНЬ → {combat['new_level']}</b>!"
        if combat.get("gold_gained"):
            text += f"\n+{combat['gold_gained']} 🪙"
        if combat["loot"]:
            text += f"\n📦 Лут: {', '.join(combat['loot'])}"
    elif combat["outcome"] == "defeat":
        text += "\n<pre>💀\n🕯️👁🕯️\n💀</pre>\n"
        text += "\n💀 <b>ПОРАЖЕНИЕ</b>\nТы очнулся... где-то раньше."
    else:
        text += "\n🤝 <b>НИЧЬЯ</b>\nОба отступили."

    if combat.get("outcome") == "victory":
        user_quests = await services.quest.get_user_quests(callback.from_user.id)
        for uq in user_quests:
            if uq["status"] != "active":
                continue
            objectives = uq.get("objectives", [])
            for obj in objectives:
                if obj.get("type") == "kill" and obj.get("creature") == creature_id:
                    await services.quest.update_progress(callback.from_user.id, uq["quest_id"], obj["id"])

    if combat["outcome"] == "defeat":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
        ])
    else:
        kb = G.post_action_kb()

    await callback.message.edit_text(text, reply_markup=kb)
