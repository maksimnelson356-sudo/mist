import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database.db import init_db, close_db
from handlers import game, whisper, combat, quests, shop, pvp, crafting, guild, trade

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MIST")


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не задан! Создай .env файл.")
        return

    await init_db()
    logger.info("База данных инициализирована.")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    me = await bot.get_me()
    bot_username = me.username
    logger.info(f"Бот: @{bot_username}")

    dp = Dispatcher()

    dp["bot_username"] = bot_username

    dp.include_router(game.router)
    dp.include_router(whisper.router)
    dp.include_router(combat.router)
    dp.include_router(quests.router)
    dp.include_router(shop.router)
    dp.include_router(pvp.router)
    dp.include_router(crafting.router)
    dp.include_router(guild.router)
    dp.include_router(trade.router)

    logger.info("MIST запущен. Туман поднимается...")
    try:
        await dp.start_polling(bot)
    finally:
        await close_db()
        logger.info("MIST закрыт.")


if __name__ == "__main__":
    asyncio.run(main())
