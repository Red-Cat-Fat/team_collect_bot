from bot.handlers.admin import router as admin_router
from bot.handlers.callbacks import router as callbacks_router
from bot.handlers.scheduler import setup_scheduler

__all__ = ["admin_router", "callbacks_router", "setup_scheduler"]