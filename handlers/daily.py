from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timezone
from services.container import services

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


@router.callback_query(F.data == "daily_menu")
async def cb_daily_menu(callback: CallbackQuery):
    info = await services.daily_reward.get_info(callback.from_user.id)

    streak_text = "🔥" * info["streak"] + "⬜" * (7 - info["streak"])
    nr = info["next_reward"]

    text = (
        f"📅 <b>Ежедневные награды</b>\n\n"
        f"🔥 Серия: {info['streak']}/7 дней\n"
        f"{streak_text}\n\n"
        f"📊 Всего получено: {info['total_claims']}\n"
    )

    if info["claimed_today"]:
        text += "\n✅ Награда за сегодня получена!\n"
        text += f"Следующая: День {info['next_day']}"
    else:
        text += f"\n🎁 Сегодня: День {info['next_day']}\n"
        text += f"   {nr['message']}\n"

    buttons = []
    if not info["claimed_today"]:
        buttons.append([InlineKeyboardButton(text="🎁 Получить награду", callback_data="daily_claim")])
    buttons.append([InlineKeyboardButton(text="📋 Ежедневные квесты", callback_data="daily_quests")])
    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "daily_claim")
async def cb_daily_claim(callback: CallbackQuery):
    result = await services.daily_reward.claim(callback.from_user.id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Награды дня", callback_data="daily_menu")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])

    await callback.message.edit_text(result["message"], reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "daily_quests")
async def cb_daily_quests(callback: CallbackQuery):
    user_id = callback.from_user.id
    quests = await services.daily.get_or_create(user_id)

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
