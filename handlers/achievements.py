from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
import game_engine as ge

router = Router()

CATEGORY_ICONS = {
    "combat": "⚔️",
    "explore": "🗺️",
    "quests": "📜",
    "progress": "📈",
    "wealth": "💰",
    "craft": "🔨",
    "pvp": "🛡️",
    "social": "👥",
    "general": "⭐",
}

CATEGORY_NAMES = {
    "combat": "Бой",
    "explore": "Исследование",
    "quests": "Квесты",
    "progress": "Прогресс",
    "wealth": "Богатство",
    "craft": "Крафт",
    "pvp": "PvP",
    "social": "Социальное",
    "general": "Общее",
}


def _format_achievement(ach: dict, user_data: dict | None) -> str:
    if user_data and user_data.get("unlocked"):
        unlock_date = user_data.get("unlock_date", "")
        date_str = f" ({unlock_date})" if unlock_date else ""
        reward = ""
        if ach.get("reward_xp"):
            reward += f" +{ach['reward_xp']} XP"
        if ach.get("reward_gold"):
            reward += f" +{ach['reward_gold']} Gold"
        return f"✅ {ach['icon']} {ach['name']} — {ach['description']}{reward}{date_str}"
    else:
        if ach.get("is_secret") == 1:
            return "⬜ ❓ ??? (Секрет)"
        else:
            return f"⬜ {ach['icon']} {ach['name']} — {ach['description']}"


@router.callback_query(F.data == "achievements")
async def cb_achievements(callback: CallbackQuery):
    user_id = callback.from_user.id
    newly_unlocked = await ge.check_achievements(user_id)
    all_achs = await ge.get_user_achievements(user_id)

    user_ach_map = {a["achievement_id"]: a for a in all_achs} if all_achs else {}

    ach_defs = ge.ACHIEVEMENT_DEFS
    categories: dict[str, list[dict]] = {}
    for ach in ach_defs:
        cat = ach.get("category", "general")
        categories.setdefault(cat, []).append(ach)

    total = len(ach_defs)
    unlocked_count = sum(
        1 for a in all_achs if a.get("unlocked")
    ) if all_achs else 0

    lines: list[str] = []
    lines.append("🏆 <b>Достижения</b>\n")

    if newly_unlocked:
        lines.append("")
        lines.append("🔓 <b>Новые достижения!</b>")
        for nl in newly_unlocked:
            lines.append(f"🔔 {nl['name']} — {nl['description']}")

    category_order = [
        "combat", "explore", "quests", "progress",
        "wealth", "craft", "pvp", "social", "general"
    ]

    for cat in category_order:
        achs_in_cat = categories.get(cat, [])
        if not achs_in_cat:
            continue

        icon = CATEGORY_ICONS.get(cat, "⭐")
        name = CATEGORY_NAMES.get(cat, cat.capitalize())
        lines.append("")
        lines.append(f"{icon} <b>{name}</b>")

        for ach in achs_in_cat:
            user_data = user_ach_map.get(ach["achievement_id"])
            lines.append(f"    {_format_achievement(ach, user_data)}")

    lines.append("")
    lines.append(f"📊 Прогресс: {unlocked_count}/{total}")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()
