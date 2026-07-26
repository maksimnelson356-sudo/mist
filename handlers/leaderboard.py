from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from services.container import services

router = Router()

BOARD_NAMES = {
    "level": "⭐ Уровень",
    "gold": "💰 Золото",
    "xp": "📊 Опыт",
    "reputation": "🏅 Репутация",
    "kills": "⚔️ Убийства",
    "deaths": "💀 Смерти",
    "quests_done": "📜 Квесты",
}


@router.callback_query(F.data == "leaderboard_menu")
async def cb_leaderboard_menu(callback: CallbackQuery):
    summary = await services.leaderboard.get_all_boards_summary(callback.from_user.id)

    text = "🏆 <b>Таблица лидеров</b>\n\n"
    text += "<b>Твоя позиция:</b>\n"
    for _board_type, info in summary.items():
        text += f"{info['icon']} {info['name']}: #{info['rank']}/{info['total']} ({info['value']})\n"

    buttons = []
    for board_type, name in BOARD_NAMES.items():
        buttons.append([InlineKeyboardButton(text=name, callback_data=f"leaderboard:{board_type}")])

    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data.startswith("leaderboard:"))
async def cb_leaderboard(callback: CallbackQuery):
    board_type = callback.data.split(":")[1]
    result = await services.leaderboard.get_leaderboard(board_type, limit=10)

    if not result["success"]:
        await callback.answer(result["message"], show_alert=True)
        return

    text = f"{result['icon']} <b>Топ-10: {result['name']}</b>\n\n"

    medals = ["🥇", "🥈", "🥉"]
    for p in result["players"]:
        medal = medals[p["rank"] - 1] if p["rank"] <= 3 else f"#{p['rank']}"
        text += f"{medal} {p['name']} — {p['value']}\n"

    if not result["players"]:
        text += "Пока нет данных."

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="leaderboard_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
