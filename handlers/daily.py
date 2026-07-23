from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timezone
import game_engine as ge

router = Router()

MONTHS_RU = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря"
]


def _progress_bar(current: int, target: int, width: int = 10) -> str:
    if target <= 0:
        return "░" * width
    ratio = min(current / target, 1.0)
    filled = round(ratio * width)
    return "█" * filled + "░" * (width - filled)


@router.callback_query(F.data == "daily_quests")
async def cb_daily_quests(callback: CallbackQuery):
    user_id = callback.from_user.id
    quests = ge.get_or_create_daily_quests(user_id)

    now = datetime.now(timezone.utc)
    date_str = f"{now.day} {MONTHS_RU[now.month - 1]} {now.year}"

    lines = [f"📅 <b>Ежедневные задания</b>", f"🗓 {date_str}", ""]

    completed_count = 0
    for q in quests:
        done = q["completed"]
        current = q["progress"]
        target = q["objective"]

        if done:
            completed_count += 1
            status_icon = "✅"
        else:
            status_icon = "⬜"

        bar = _progress_bar(current, target)
        reward_parts = []
        if q["reward_xp"]:
            reward_parts.append(f"+{q['reward_xp']} XP")
        if q["reward_gold"]:
            reward_parts.append(f"+{q['reward_gold']} 🪙")
        reward_str = ", ".join(reward_parts)

        lines.append(f"{status_icon} 🎯 <b>{q['name']}</b> — {q['description']}")
        lines.append(f"   {bar} {current}/{target}  {reward_str}")
        lines.append("")

    total = len(quests)
    lines.append(f"📊 Итого: {completed_count}/{total} выполнено")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()
