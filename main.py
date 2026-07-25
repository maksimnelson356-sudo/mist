import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database.base import init_db, close_db
from handlers import game, whisper, combat, quests, shop, pvp, crafting, guild, trade, equipment, achievements, daily, commands
from services.container import services

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MIST")


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не задан! Создай .env файл.")
        return

    await init_db()
    logger.info("База данных инициализирована.")

    await services.world_engine.init()
    logger.info("WorldEngine инициализирован.")

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
    dp.include_router(equipment.router)
    dp.include_router(achievements.router)
    dp.include_router(daily.router)

    world_engine_task = asyncio.create_task(
        services.world_engine.start_loop(interval_seconds=900)
    )
    logger.info("WorldEngine tick запущ (каждые 15 минут).")

    ecosystem_task = asyncio.create_task(
        services.ecosystem.start_loop(interval_seconds=900)
    )
    logger.info("EcosystemService tick запущ.")

    logger.info("MIST запущен. Туман поднимается...")
    try:
        await dp.start_polling(bot)
    finally:
        services.world_engine.stop()
        services.ecosystem.stop()
        world_engine_task.cancel()
        ecosystem_task.cancel()
        try:
            await world_engine_task
        except asyncio.CancelledError:
            pass
        try:
            await ecosystem_task
        except asyncio.CancelledError:
            pass
        await close_db()
        logger.info("MIST закрыт.")


if __name__ == "__main__":
    asyncio.run(main())
