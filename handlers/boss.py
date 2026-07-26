import random

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from services.container import services
from services.world_boss_service import WORLD_BOSS_DEFS

router = Router()

PHASE_ICONS = {
    "idle": "🟢",
    "fighting": "🟡",
    "wounded": "🟠",
    "enraged": "🔴",
    "dead": "💀",
}


@router.callback_query(F.data == "boss_menu")
async def cb_boss_menu(callback: CallbackQuery):
    active = await services.world_boss.get_active_bosses()
    stats = await services.world_boss.get_boss_stats()

    text = (
        f"💀 <b>Мировые боссы</b>\n\n"
        f"Активных: {stats['alive']} | Повержено: {stats['dead']}\n\n"
    )

    if not active:
        text += (
            "Сейчас нет активных боссов.\n\n"
            "Боссы пробуждаются по событиям мира.\n"
            "Следи за новостями — когда босс появится, он будет здесь."
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📜 История", callback_data="boss_history")],
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
        ])
    else:
        buttons = []
        for b in active:
            hp_pct = int(b["hp"] / b["max_hp"] * 100)
            phase = PHASE_ICONS.get(b["phase"], "⚪")
            text += (
                f"{phase} <b>{b['name']}</b>\n"
                f"   ❤️ {b['hp']}/{b['max_hp']} ({hp_pct}%) | "
                f"👥 {b['participants']} участников\n\n"
            )
            buttons.append([InlineKeyboardButton(
                text=f"⚔️ {b['name']} ({hp_pct}%)",
                callback_data=f"boss_fight:{b['boss_id']}"
            )])

        buttons.append([InlineKeyboardButton(text="📜 История", callback_data="boss_history")])
        buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data.startswith("boss_fight:"))
async def cb_boss_fight(callback: CallbackQuery):
    boss_id = callback.data.split(":")[1]
    user_id = callback.from_user.id

    user = await services.player.get_or_create(user_id)
    if not user["is_alive"]:
        await callback.answer("Ты мёртв. Очнись сначала.", show_alert=True)
        return

    active = await services.world_boss.get_active_bosses()
    boss = next((b for b in active if b["boss_id"] == boss_id), None)

    if not boss:
        await callback.answer("Босс не найден или уже мёртв.", show_alert=True)
        return

    boss_def = next((bd for bd in WORLD_BOSS_DEFS if bd["boss_id"] == boss_id), None)
    if not boss_def:
        await callback.answer("Определение босса не найдено.", show_alert=True)
        return

    damage = max(1, user["attack"] - boss_def.get("defense", 0) // 2)
    result = await services.world_boss.damage_boss(boss_id, damage, user_id)

    if not result["success"]:
        await callback.answer(result["message"], show_alert=True)
        return

    text = f"⚔️ <b>Бой с {boss['name']}</b>\n\n"
    text += f"Ты наносишь: {damage} урона\n"

    if result["killed"]:
        text += (
            f"\n<pre>🏆💀🏆\n🔥🐉🔥\n🏆💀🏆</pre>\n"
            f"🏆 <b>БОСС ПОВЕРЖЕН!</b>\n\n"
            f"XP: +{boss_def.get('xp_reward', 0)}\n"
            f"Gold: +{boss_def.get('gold_reward', 0)}"
        )

        loot = boss_def.get("loot_table", [])
        dropped = [entry for entry in loot if random.random() < entry.get("chance", 0.5)]
        if dropped:
            text += "\n\n📦 <b>Лут:</b>\n"
            for entry in dropped:
                await services.inventory.add(user_id, entry["item"], entry.get("qty", 1))
                text += f"  • {entry['item']} x{entry['qty']}\n"

        xp_reward = boss_def.get("xp_reward", 0)
        gold_reward = boss_def.get("gold_reward", 0)

        await services.player.update(user_id, xp=user["xp"] + xp_reward, gold=user["gold"] + gold_reward)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💀 Боссы", callback_data="boss_menu")],
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
        ])
    else:
        hp_pct = int(result["hp_left"] / boss["max_hp"] * 100)
        phase = result.get("phase", "fighting")
        phase_name = {"fighting": "Бой", "wounded": "Ранен", "enraged": "В ярости"}.get(phase, phase)

        text += f"\n❤️ Босс: {result['hp_left']}/{boss['max_hp']} ({hp_pct}%)\n"
        text += f"📊 Фаза: {phase_name}\n"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"⚔️ Ещё удар ({hp_pct}%)", callback_data=f"boss_fight:{boss_id}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="boss_menu")],
        ])

    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data == "boss_history")
async def cb_boss_history(callback: CallbackQuery):
    history = await services.world_boss.get_boss_history()

    text = "📜 <b>История битв</b>\n\n"

    if not history:
        text += "Пока никто не повалил ни одного босса.\nБудь первым!"
    else:
        for h in history:
            killed = h.get("killed_at")
            date_str = killed.strftime("%d.%m.%Y %H:%M") if killed else "?"
            text += f"💀 {h['name']} — {date_str}\n"
            text += f"   👥 Участников: {h['participants']}\n\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="boss_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
