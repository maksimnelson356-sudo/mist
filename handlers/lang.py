from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from utils.translator import set_language, t

router = Router()


@router.message(Command("lang"))
async def cmd_lang(message: Message):
    text = t("lang_title")
    buttons = [
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:set:ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:set:en")],
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("lang:set:"))
async def cb_lang_set(callback: CallbackQuery):
    lang = callback.data.split(":")[2]
    set_language(lang)
    text = t("lang_set")
    await callback.answer(text, show_alert=True)

    from handlers.game import main_menu_kb
    kb = main_menu_kb()
    await callback.message.edit_text("✅", reply_markup=kb)
