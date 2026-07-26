import random

from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart

from services.container import services
from scenes import LOC_SCENES, SCENE_DIVIDER
from . import _shared as G

router = G.router


def _is_my_message(message: Message, bot_username: str) -> bool:
    if message.chat.type == "private":
        return True
    if message.text and message.text.startswith("/"):
        cmd = message.text.split()[0].lstrip("/")
        if "@" in cmd:
            return cmd.split("@")[1].lower() == bot_username.lower()
        return False
    if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.username:
        return message.reply_to_message.from_user.username.lower() == bot_username.lower()
    return False


@router.message(CommandStart())
async def cmd_start(message: Message, bot_username: str):
    if not _is_my_message(message, bot_username):
        return

    if message.chat.type != "private":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌫 Начать игру", url=f"https://t.me/{bot_username}?start=start")]
        ])
        await message.answer(
            "🌫 <b>MIST</b> — текстовый квест в тумане.\n\n"
            "Играй в личных сообщениях!",
            reply_markup=kb
        )
        return

    user = await services.player.get_or_create(message.from_user.id, message.from_user.username)

    if not user["is_alive"]:
        text = (
            "<pre>💀\n🕯️👁🕯️\n💀</pre>\n"
            "💀 <b>Ты мёртв.</b>\n\n"
            "Туман накрыл тебя. Но он не отпускает.\n"
            "Ты чувствуешь — ты ещё нужен."
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Очнуться", callback_data="revive")]
        ])
        await message.answer(text, reply_markup=kb)
        return

    loc = await services.movement.get_location(user["current_location"])
    loc_name = loc["name"] if loc else await services.movement.get_location_name(user["current_location"])
    scene = LOC_SCENES.get(user["current_location"], "")
    text = ""
    if scene:
        text += f"<pre>{scene}</pre>\n{SCENE_DIVIDER}\n"
    text += (
        "🌫 <b>Добро пожаловать в MIST</b>\n\n"
        "Ты просыпаешься в тумане.\n"
        "Не помнишь, как сюда попал.\n\n"
        "Туман помнит всё.\n\n"
        f"📍 <b>{loc_name}</b>\n"
        f"❤️ HP: {user['hp']}/{user['max_hp']} | ⭐ Ур. {user['level']}\n"
        f"🍖 Голод: {user.get('hunger', 100)}/{user.get('max_hunger', 100)}\n"
        f"🪙 Золото: {user['gold']} | 🎒 Воспоминаний: {user['memories']}\n\n"
        "<i>Нажми 🔍 Осмотреться чтобы увидеть выходы</i>"
    )
    await message.answer(text, reply_markup=G.main_menu_kb())


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def group_mention(message: Message, bot_username: str):
    if not message.text:
        return
    text_lower = message.text.lower()
    if f"@{bot_username.lower()}" not in text_lower and not (
        message.reply_to_message and message.reply_to_message.from_user
        and message.reply_to_message.from_user.username
        and message.reply_to_message.from_user.username.lower() == bot_username.lower()
    ):
        return

    whispers = [
        "Туман шепчет... <i>«Играй в личке...»</i>",
        "Из глубины тумана: <i>«/start в личных сообщениях...»</i>",
        "Голос из пустоты: <i>«MIST ждёт тебя в личке...»</i>",
        "Шёпот: <i>«Ты не можешь играть здесь. Туман ведёт к другому входу...»</i>",
    ]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌫 Начать игру", url=f"https://t.me/{bot_username}?start=start")]
    ])

    await message.answer(random.choice(whispers), reply_markup=kb)


@router.callback_query(F.data == "revive")
async def cb_revive(callback: CallbackQuery):
    result = await services.player.revive(callback.from_user.id)
    if result["success"]:
        user = await services.player.get_or_create(callback.from_user.id)
        loc = await services.movement.get_location(user["current_location"])
        loc_name = loc["name"] if loc else await services.movement.get_location_name(user["current_location"])
        text = result["message"] + f"\n\n📍 <b>{loc_name}</b>"
        kb = G.main_menu_kb()
    else:
        text = result["message"]
        kb = G.back_menu_kb()
    await callback.message.edit_text(text, reply_markup=kb)
