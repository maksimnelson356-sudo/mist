import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database.db import init_db, close_db
from handlers import game, whisper, combat, quests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MIST")


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не задан! Создай .env файл.")
        return

    await init_db()
    logger.info("База данных инициализирована.")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
    dp = Dispatcher()

    dp.include_router(game.router)
    dp.include_router(whisper.router)
    dp.include_router(combat.router)
    dp.include_router(quests.router)

    logger.info("MIST запущен. Туман поднимается...")
    try:
        await dp.start_polling(bot)
    finally:
        await close_db()
        logger.info("MIST закрыт.")


if __name__ == "__main__":
    asyncio.run(main())
