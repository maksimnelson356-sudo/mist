from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.container import services

router = Router()


@router.message(Command("explore"))
async def cmd_explore(message: Message):
    if message.chat.type != "private":
        return

    user = await services.player.get_or_create(message.from_user.id)
    result = await services.exploration.discover(user["user_id"], user["current_location"])

    text = result["message"]
    if result.get("first_discover"):
        text += "\n\n🌟 Первый исследователь этой области!"
        text += f"\n📊 Всего открыто: {result.get('visited_count', 1)}"

    await message.answer(text)


@router.message(Command("discoveries"))
async def cmd_discoveries(message: Message):
    if message.chat.type != "private":
        return

    user = await services.player.get_or_create(message.from_user.id)
    text = await services.exploration.get_discovery_list(user["user_id"])
    await message.answer(text)


@router.message(Command("exploration_stats"))
async def cmd_exploration_stats(message: Message):
    if message.chat.type != "private":
        return

    user = await services.player.get_or_create(message.from_user.id)
    stats = await services.exploration.get_stats(user["user_id"])

    text = (
        f"📊 <b>Статистика исследований</b>\n\n"
        f"🗺 Открыто локаций: {stats['discovery_count']}\n"
        f"👣 Всего посещений: {stats['total_visits']}"
    )

    await message.answer(text)
