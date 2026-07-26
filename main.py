import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest

from config import BOT_TOKEN
from database.base import init_db, close_db
from handlers import (
    game, whisper, quests, shop, pvp, crafting, guild, trade, equipment,
    achievements, daily, commands, admin, npc, exploration, home, artifact, boss,
    war, profile, world_chronicle, class_handler, dialogue, faction, raid, event,
    market, leaderboard, guild_ext, npc_trade, npc_quests, catalog, balance,
    territory, lang,
)
from middleware import CallbackAnswerMiddleware
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
    dp.include_router(quests.router)
    dp.include_router(shop.router)
    dp.include_router(pvp.router)
    dp.include_router(crafting.router)
    dp.include_router(guild.router)
    dp.include_router(trade.router)
    dp.include_router(equipment.router)
    dp.include_router(achievements.router)
    dp.include_router(daily.router)
    dp.include_router(commands.router)
    dp.include_router(admin.router)
    dp.include_router(npc.router)
    dp.include_router(exploration.router)
    dp.include_router(home.router)
    dp.include_router(artifact.router)
    dp.include_router(boss.router)
    dp.include_router(war.router)
    dp.include_router(profile.router)
    dp.include_router(world_chronicle.router)
    dp.include_router(class_handler.router)
    dp.include_router(dialogue.router)
    dp.include_router(faction.router)
    dp.include_router(raid.router)
    dp.include_router(event.router)
    dp.include_router(market.router)
    dp.include_router(leaderboard.router)
    dp.include_router(guild_ext.router)
    dp.include_router(npc_trade.router)
    dp.include_router(npc_quests.router)
    dp.include_router(catalog.router)
    dp.include_router(balance.router)
    dp.include_router(territory.router)
    dp.include_router(lang.router)

    dp.callback_query.middleware(CallbackAnswerMiddleware())

    @dp.errors()
    async def handle_errors(event):
        try:
            exception = event.update.exception if event.update else event.exception
        except Exception:
            exception = getattr(event, "exception", None)
        if isinstance(exception, TelegramBadRequest):
            msg = str(exception)
            if "message is not modified" in msg:
                return True
            if "message to edit not found" in msg:
                return True
            if "query is too old" in msg:
                return True
        return False

    world_engine_task = asyncio.create_task(
        services.world_engine.start_loop(interval_seconds=900)
    )
    logger.info("WorldEngine tick запущ (каждые 15 минут).")

    logger.info("MIST запущен. Туман поднимается...")
    try:
        await dp.start_polling(bot)
    finally:
        services.world_engine.stop()
        world_engine_task.cancel()
        try:
            await world_engine_task
        except asyncio.CancelledError:
            pass
        await close_db()
        logger.info("MIST закрыт.")


if __name__ == "__main__":
    asyncio.run(main())
