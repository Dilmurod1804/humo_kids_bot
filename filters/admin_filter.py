"""
Faqat tasdiqlangan adminlarga ruxsat beruvchi filter.
Admin panelning barcha routerlariga (auth.py dan tashqari) ulanadi.
"""
from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from database.requests import is_admin_verified


class IsVerifiedAdmin(BaseFilter):
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        if event.from_user is None:
            return False
        return await is_admin_verified(event.from_user.id)
