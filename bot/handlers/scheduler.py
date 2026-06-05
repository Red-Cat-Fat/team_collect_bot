from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot

from bot.config import config
from bot.database import Database
from bot.handlers.admin import send_or_update_poll


async def check_schedules(bot: Bot, db: Database):
    now = datetime.now()
    today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

    pending_schedule = await db.get_pending_schedule()
    if pending_schedule:
        game_date = pending_schedule.game_date.replace(hour=0, minute=0, second=0, microsecond=0)

        if game_date >= today_midnight:
            await send_or_update_poll(bot, db, pending_schedule.id, pending_schedule.game_date)


def setup_scheduler(bot: Bot, db: Database) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=config.timezone)
    scheduler.add_job(
        check_schedules,
        CronTrigger(hour=10, minute=0, timezone=config.timezone),
        args=[bot, db],
        id="daily_poll_update",
        replace_existing=True
    )
    return scheduler