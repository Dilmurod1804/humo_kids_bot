"""
Admin panel — "Ovqatlar" (taomnoma) bo'limi.
"""
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.requests import add_menu_item, get_active_menu_items
from filters.admin_filter import IsVerifiedAdmin
from keyboards.admin_kb import AdminNavCB, back_to_admin_main_kb, menu_section_kb
from services.broadcast import broadcast_to_all_channels
from states.states import AddMenu

logger = logging.getLogger(__name__)
router = Router(name="admin_menu")
router.message.filter(IsVerifiedAdmin())
router.callback_query.filter(IsVerifiedAdmin())


@router.callback_query(AdminNavCB.filter(F.action == "menu_section"))
async def cb_menu_section(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    items = await get_active_menu_items()
    if items:
        body = "\n\n".join(f"• {item.text}" for item in items)
        text = f"🍽 <b>Joriy taomnoma</b> (barcha guruhlar uchun):\n\n{body}"
    else:
        text = "🍽 <b>Ovqatlar</b>\n\nHozircha taomnoma kiritilmagan."

    await callback.message.edit_text(text, reply_markup=menu_section_kb())
    await callback.answer()


@router.callback_query(AdminNavCB.filter(F.action == "add_menu"))
async def cb_add_menu_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddMenu.waiting_for_text)
    await callback.message.edit_text(
        "✍️ Bugungi taomnoma matnini yuboring.\n\n"
        "Agar rasm biriktirmoqchi bo'lsangiz, rasmni tavsif (caption) bilan birga yuboring.",
        reply_markup=back_to_admin_main_kb(),
    )
    await callback.answer()


@router.message(AddMenu.waiting_for_text, F.photo)
async def process_add_menu_photo(message: Message, state: FSMContext) -> None:
    text = message.caption or "Taomnoma (rasm ilova qilingan)"
    photo_file_id = message.photo[-1].file_id
    await _save_and_broadcast_menu(message, state, text, photo_file_id)


@router.message(AddMenu.waiting_for_text, F.text)
async def process_add_menu_text(message: Message, state: FSMContext) -> None:
    await _save_and_broadcast_menu(message, state, message.text, None)


async def _save_and_broadcast_menu(
    message: Message, state: FSMContext, text: str, photo_file_id: str | None
) -> None:
    await add_menu_item(text=text, photo_file_id=photo_file_id)
    success, failed = await broadcast_to_all_channels(message.bot, text=f"🍽 Bugungi taomnoma:\n\n{text}", photo_file_id=photo_file_id)
    await state.clear()

    result_note = f"\n\n📡 {success} ta guruh kanaliga yuborildi."
    if failed:
        result_note += f" ({failed} tasiga yuborishda xatolik yuz berdi)"

    await message.answer(
        "✅ Taomnoma muvaffaqiyatli qo'shildi va barcha guruhlar uchun amal qiladi." + result_note,
        reply_markup=back_to_admin_main_kb(),
    )
