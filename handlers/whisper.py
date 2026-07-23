import random
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
import game_engine as ge

router = Router()

WHISPERS = [
    "Ты слышишь? Кто-то шепчет твоё имя...",
    "Туман сгущается. Он помнит, что ты сделал.",
    "Где-тодалеко ломается ветка. Или это шаги?",
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
    user = await ge.get_or_create_user(user_id)
    actions = await ge.get_user_actions(user_id, limit=20)
    karma = user.get("karma", 0)
    days = user.get("days_in_mist", 0)

    if days > 30:
        base = [w for w in WHISPERS if "стар" in w or "помнишь" in w or "время" in w]
    elif karma > 10:
        base = [w for w in WHISPERS if "наблюдает" in w or "жёлт" in w or "помни" in w]
    elif karma < -10:
        base = [w for w in WHISPERS if "тени" in w or "шаги" in w or "помнишь" in w]
    else:
        base = WHISPERS

    return random.choice(base) if base else random.choice(WHISPERS)


@router.message(Command("whisper"))
async def cmd_whisper(message: Message):
    whisper = await _get_whisper_for_user(message.from_user.id)

    await ge._log_action(message.from_user.id, "whisper", {"text": whisper})

    text = (
        f"🌫 _{whisper}_\n\n"
        "_Туман отвечает не всегда. Но когда отвечает — запоминаешь._"
    )
    await message.answer(text, parse_mode="Markdown")
