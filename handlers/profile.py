from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from services.container import services
from services.home_service import HOME_MOODS
from services.weather_system import WEATHER_STATES
from services.time_system import TIME_PERIODS

router = Router()


@router.callback_query(F.data == "profile")
async def cb_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await services.player.get_or_create(user_id)
    home = await services.home.get_home(user_id)
    artifacts = await services.artifact.get_by_owner(user_id)
    guild = await services.guild.get_user_guild(user_id)
    weather_data = await services.weather.get_weather()
    time_data = services.time.get_current_time()

    xp_needed = user["level"] * 100
    xp_progress = int(user["xp"] / xp_needed * 100) if xp_needed > 0 else 0
    xp_bar = "█" * (xp_progress // 10) + "░" * (10 - xp_progress // 10)

    reputation = user.get("reputation", 0)
    if reputation <= -51:
        rep_name = "Враг"
    elif reputation <= -1:
        rep_name = "Подозрительный"
    elif reputation <= 49:
        rep_name = "Нейтральный"
    elif reputation <= 99:
        rep_name = "Доброжелательный"
    else:
        rep_name = "Герой"

    text = (
        f"👤 <b>{user['display_name']}</b>\n\n"
        f"📍 {user['current_location']}\n"
        f"📅 Дней в MIST: {user.get('days_in_mist', 0)}\n\n"
        f"☀️ Погода: {weather_data['name']} {weather_data.get('icon', '')}\n"
        f"🕐 Время: {time_data.get('name', '?')}\n\n"
        f"⭐ Уровень: {user['level']}\n"
        f"   [{xp_bar}] {user['xp']}/{xp_needed} XP\n\n"
        f"❤️ HP: {user['hp']}/{user['max_hp']}\n"
        f"🍖 Сытость: {user.get('hunger', 100)}/{user.get('max_hunger', 100)}\n"
        f"🗡 Атака: {user['attack']}\n"
        f"🛡 Защита: {user['defense']}\n"
        f"🪙 Золото: {user['gold']}\n\n"
        f"⭐ Репутация: {reputation} ({rep_name})\n"
        f"⚖️ Карма: {user['karma']}\n"
    )

    if user.get("pvp_wins") or user.get("pvp_losses"):
        text += f"\n⚔️ PvP: {user['pvp_wins']}W / {user['pvp_losses']}L\n"
        text += f"🏆 Рейтинг: {user.get('pvp_rating', 1000)}\n"

    if home:
        home_type = {"hut": "Хижина", "cabin": "Изба", "house": "Дом", "tower": "Башня", "fortress": "Крепость"}.get(home["home_type"], home["home_type"])
        mood = HOME_MOODS.get(home["mood"], "Тихо.")
        text += f"\n🏠 {home['name']} ({home_type}, ур. {home['level']})\n"
        text += f"   {mood}\n"

    if artifacts:
        text += f"\n🏺 Артефактов: {len(artifacts)}\n"
        for a in artifacts[:3]:
            text += f"   • {a['name']}\n"

    if guild:
        text += f"\n🏰 Гильдия: {guild['name']}\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
