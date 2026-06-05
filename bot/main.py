import asyncio
import logging
import os
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import config
from bot.database import Database
from bot.handlers import admin_router, callbacks_router, setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan():
    os.makedirs(os.path.dirname(config.db_path), exist_ok=True)
    db = Database(config.db_path)
    await db.init()
    logger.info("Database initialized")

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(admin_router)
    dp.include_router(callbacks_router)

    dp["db"] = db

    scheduler = setup_scheduler(bot, db)
    scheduler.start()
    logger.info("Scheduler started")

    try:
        yield
    finally:
        scheduler.shutdown()
        await db.close()
        await bot.session.close()
        logger.info("Shutdown complete")


async def main():
    async with lifespan():
        bot = Bot(
            token=config.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        dp = Dispatcher(storage=MemoryStorage())
        dp.include_router(admin_router)
        dp.include_router(callbacks_router)

        db = Database(config.db_path)
        await db.init()
        dp["db"] = db

        scheduler = setup_scheduler(bot, db)
        scheduler.start()

        logger.info("Bot started")
        await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")