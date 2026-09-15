"""
Admin panelga kirish kodini tekshirish.
"""
import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import settings
from database.requests import verify_admin
from keyboards.admin_kb import admin_main_menu_kb
from states.states import AdminAuth

logger = logging.getLogger(__name__)
router = Router(name="admin_auth")


@router.message(AdminAuth.waiting_for_code)
async def process_admin_code(message: Message, state: FSMContext) -> None:
    entered_code = (message.text or "").strip()

    if entered_code == settings.admin_access_code:
        await verify_admin(message.from_user.id)
        await state.clear()
        await message.answer(
            "✅ Kod to'g'ri! Admin panelga xush kelibsiz.",
            reply_markup=admin_main_menu_kb(),
        )
        logger.info(f"Admin tasdiqlandi: {message.from_user.id}")
    else:
        await message.answer(
            "❌ Kod noto'g'ri. Qaytadan urinib ko'ring yoki /start bosib ortga qayting."
        )


@router.callback_query(lambda c: c.data == "nav_home_from_admin")
async def cb_admin_back_to_home(callback: CallbackQuery, state: FSMContext) -> None:
    from database.requests import get_active_groups
    from keyboards.user_kb import home_menu_kb

    await state.clear()
    groups = await get_active_groups()
    await callback.message.edit_text(
        "🏠 Bosh menyu.\n\nQuyidagi guruhlardan birini tanlang:",
        reply_markup=home_menu_kb(groups),
    )
    await callback.answer()
