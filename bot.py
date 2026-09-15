"""
Humo Kids — bog'cha Telegram boti.
Ishga tushirish: python bot.py
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database.db import init_db
from handlers.admin import auth, children, groups, menu, schedule
from handlers.user import home, menu_schedule
from scheduler.cleanup import setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    await init_db()
    logger.info("Ma'lumotlar bazasi tayyor.")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # --- Routerlarni ulash ---
    # Foydalanuvchi (Home) qismi
    dp.include_router(home.router)
    dp.include_router(menu_schedule.router)

    # Admin qismi
    dp.include_router(auth.router)
    dp.include_router(menu.router)
    dp.include_router(schedule.router)
    dp.include_router(groups.router)
    dp.include_router(children.router)

    # --- Scheduler (24 soatlik avtomatik tozalash) ---
    scheduler = setup_scheduler()
    scheduler.start()
    logger.info("Scheduler ishga tushdi (har 5 daqiqada muddati o'tgan yozuvlar tekshiriladi).")

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Humo Kids bot ishga tushdi. Polling boshlandi...")

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
