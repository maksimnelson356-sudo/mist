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

    world_state = services.world_engine.get_state()
    game_hour = world_state["game_hour"] if world_state else 8
    season = world_state["season"] if world_state else "spring"

    from services.time_system import TIME_PERIODS
    period = "morning"
    for p, info in TIME_PERIODS.items():
        start, end = info["hours"]
        if start <= end:
            if start <= game_hour <= end:
                period = p
                break
        else:
            if game_hour >= start or game_hour <= end:
                period = p
                break
    period_info = TIME_PERIODS[period]

    loc_id = user["current_location"]
    loc_weather = "clear"
    try:
        from database.base import get_db as _get_db
        from sqlalchemy import text
        async for _db in _get_db():
            r = await _db.execute(text("SELECT current_weather FROM locations WHERE id = :lid"), {"lid": loc_id})
            row = r.mappings().first()
            if row:
                loc_weather = row["current_weather"] or "clear"
    except Exception:
        pass
    weather_info = WEATHER_STATES.get(loc_weather, WEATHER_STATES["clear"])

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

    loc_name = await services.movement.get_location_name(user["current_location"])

    text = (
        f"👤 <b>{user['display_name']}</b>\n\n"
        f"📍 {loc_name}\n"
        f"📅 Дней в MIST: {user.get('days_in_mist', 0)}\n\n"
        f"☀️ Погода: {weather_info['name']} {weather_info.get('icon', '')}\n"
        f"🕐 Время: {period_info['name']}\n\n"
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
