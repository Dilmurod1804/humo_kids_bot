"""
Taomnoma va dars jadvali yozuvlarini 24 soat o'tgach avtomatik
o'chiruvchi fon vazifasi (APScheduler orqali).
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database.requests import delete_expired_items

logger = logging.getLogger(__name__)


async def cleanup_expired_items() -> None:
    menu_deleted, schedule_deleted = await delete_expired_items()
    if menu_deleted or schedule_deleted:
        logger.info(
            f"Avtomatik tozalash: {menu_deleted} ta taomnoma, "
            f"{schedule_deleted} ta dars jadvali yozuvi o'chirildi."
        )


def setup_scheduler() -> AsyncIOScheduler:
    """Scheduler obyektini yaratadi va joblarni ro'yxatdan o'tkazadi.

    Har 5 daqiqada tekshiradi (real vaqt yaqinligida 24 soatlik chegara
    kesib o'tiladi, lekin sekundma-sekund aniqlik talab qilinmagani sababli
    bu interval yetarli va resurs tejaydi).
    """
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        cleanup_expired_items,
        trigger="interval",
        minutes=5,
        id="cleanup_expired_items",
        replace_existing=True,
    )
    return scheduler
