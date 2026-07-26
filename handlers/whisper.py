import random

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from services.container import services

router = Router()

WHISPERS = [
    "Ты слышишь? Кто-то шепчет твоё имя...",
    "Туман сгущается. Он помнит, что ты сделал.",
    "Где-то далеко ломается ветка. Или это шаги?",
    "Они здесь. Они всегда здесь. Просто смотри.",
    "Ты не один. Ты никогда не был один.",
    "Камень под ногой тёплый. Он живой.",
    "Ветер несёт запах чего-то старого. Очень старого.",
    "Тени двигаются. Не так, как должны.",
    "Ты чувствуешь это? Кто-то наблюдает.",
    "Осколок в кармане начал вибрировать.",
    "Мир замедляется. Ты замедляешься.",
    "Что-то блеснуло вдали. Исчезло.",
    "Шёпот усиливается. Ты почти различаешь слова...",
    "Время. Что-то не так со временем.",
    "Он вернётся. Ты знаешь это.",
    "Ты помнишь? Ты точно помнишь?",
    "Здесь были до тебя. Много до тебя.",
    "Туман редеет. На мгновение. Потом — снова.",
    "Кто-то ждёт. Давно ждёт.",
    "Ты сделал выбор. Мир запомнил.",
]


async def _get_whisper_for_user(user_id: int) -> str:
    user = await services.player.get_or_create(user_id)
    days = user.get("days_in_mist", 0)
    karma = user.get("karma", 0)
    loc_id = user.get("current_location", "fishing_village")

    try:
        memories = await services.world_memory.get_memories_at_location(loc_id, limit=5)
        if memories:
            m = random.choice(memories)
            desc = m.get("description", "") or m["title"]
            return f"Туман шепчет о прошлом этого места...\n\n<i>«{desc}»</i>"
    except Exception:
        pass

    if days > 30:
        base = [w for w in WHISPERS if any(k in w for k in ["стар", "помнишь", "время"])]
    elif karma > 10:
        base = [w for w in WHISPERS if any(k in w for k in ["наблюдает", "ждёт", "помни"])]
    elif karma < -10:
        base = [w for w in WHISPERS if any(k in w for k in ["тени", "шаги", "помнишь"])]
    else:
        base = WHISPERS

    return random.choice(base) if base else random.choice(WHISPERS)


def _whisper_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔮 Ещё шёпот", callback_data="whisper")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])


@router.callback_query(F.data == "whisper")
async def cb_whisper(callback: CallbackQuery):
    whisper_text = await _get_whisper_for_user(callback.from_user.id)

    text = (
        f"🌫 <i>{whisper_text}</i>\n\n"
        "<i>Туман отвечает не всегда. Но когда отвечает — запоминаешь.</i>"
    )
    await callback.message.edit_text(text, reply_markup=_whisper_kb())
