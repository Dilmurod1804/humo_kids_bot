"""
Humo Kids — bog'cha Telegram boti (PythonAnywhere Webhook versiyasi).
"""
import asyncio
import logging
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

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

# PythonAnywhere havolangiz va Webhook yo'li
WEBHOOK_HOST = "https://pythonanywhere.com"
WEBHOOK_PATH = f"/webhook/{settings.bot_token}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher(storage=MemoryStorage())

# Routerlarni ulash
dp.include_router(home.router)
dp.include_router(menu_schedule.router)
dp.include_router(auth.router)
dp.include_router(menu.router)
dp.include_router(schedule.router)
dp.include_router(groups.router)
dp.include_router(children.router)

async def on_startup(app: web.Application) -> None:
    await init_db()
    logger.info("Ma'lumotlar bazasi tayyor.")
    
    # Scheduler ishga tushirish
    scheduler = setup_scheduler()
    scheduler.start()
    app['scheduler'] = scheduler
    logger.info("Scheduler ishga tushdi.")

    # Telegram'ga webhook manzilini bog'lash
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    logger.info(f"Webhook o'rnatildi: {WEBHOOK_URL}")

async def on_shutdown(app: web.Application) -> None:
    logger.info("Bot to'xtatilmoqda...")
    await bot.delete_webhook()
    app['scheduler'].shutdown()
    await bot.session.close()

def main():
    app = web.Application()
    
    # Kelayotgan so'rovlarni aiogram'ga yo'naltirish
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    setup_application(app, dp, bot=bot)
    
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    return app

# PythonAnywhere ASGI/WSGI uchun ob'ekt
application = main()

if __name__ == "__main__":
    # Konsolda test qilib ko'rish uchun (ixtiyoriy)
    web.run_app(application, host="127.0.0.1", port=8080)
