"""
Bot va Channel Service (backend) o'rtasidagi ichki aloqa uchun HTTP klient.

Channel Service — Pyrogram (MTProto) asosida ishlaydigan, kanallarni
avtomatik yaratish/o'chirish bilan shug'ullanuvchi alohida mikroservis.
Bot bilan FastAPI orqali ichki tarmoqda (Docker network) muloqot qiladi.
"""
import logging
from typing import Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)


class ChannelServiceError(Exception):
    """Channel Service bilan aloqada xatolik yuz berganda ko'tariladi."""


class ChannelServiceClient:
    def __init__(self) -> None:
        self.base_url = settings.channel_service_url.rstrip("/")
        self.headers = {"X-Internal-Token": settings.internal_api_token}

    async def create_channel(self, title: str, description: Optional[str] = None) -> dict:
        """Yangi guruh uchun Telegram kanal yaratishni so'raydi.

        Returns:
            {"channel_id": int, "invite_link": str}
        """
        payload = {"title": title, "description": description}
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/channels/create",
                    json=payload,
                    headers=self.headers,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Channel Service xatoligi (create): {e.response.text}")
                raise ChannelServiceError(
                    f"Kanal yaratib bo'lmadi: {e.response.text}"
                ) from e
            except httpx.RequestError as e:
                logger.error(f"Channel Service ga ulanib bo'lmadi: {e}")
                raise ChannelServiceError(
                    "Channel Service bilan aloqa o'rnatilmadi. Backend ishlab turganini tekshiring."
                ) from e

    async def delete_channel(self, channel_id: int) -> None:
        """Mavjud kanalni o'chirishni so'raydi."""
        payload = {"channel_id": channel_id}
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/channels/delete",
                    json=payload,
                    headers=self.headers,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error(f"Channel Service xatoligi (delete): {e.response.text}")
                raise ChannelServiceError(
                    f"Kanalni o'chirib bo'lmadi: {e.response.text}"
                ) from e
            except httpx.RequestError as e:
                logger.error(f"Channel Service ga ulanib bo'lmadi: {e}")
                raise ChannelServiceError(
                    "Channel Service bilan aloqa o'rnatilmadi. Backend ishlab turganini tekshiring."
                ) from e


channel_client = ChannelServiceClient()
