"""
Admin tomonidan kiritilgan taomnoma/dars jadvalini barcha faol guruh
kanallariga avtomatik yuborish uchun xizmat funksiyalari.
"""
import logging
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from database.requests import get_active_groups

logger = logging.getLogger(__name__)


async def broadcast_to_all_channels(
    bot: Bot,
    text: str,
    photo_file_id: Optional[str] = None,
) -> tuple[int, int]:
    """Matn (va ixtiyoriy rasm)ni barcha faol guruh kanallariga yuboradi.

    Returns:
        (muvaffaqiyatli_yuborilgan_soni, xatolik_soni)
    """
    groups = await get_active_groups()
    success, failed = 0, 0

    for group in groups:
        if group.channel_id is None:
            continue
        try:
            if photo_file_id:
                await bot.send_photo(chat_id=group.channel_id, photo=photo_file_id, caption=text)
            else:
                await bot.send_message(chat_id=group.channel_id, text=text)
            success += 1
        except TelegramAPIError as e:
            logger.error(f"'{group.name}' kanaliga yuborishda xatolik: {e}")
            failed += 1

    return success, failed
