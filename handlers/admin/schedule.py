"""
Admin panel — "Dars jadvali qo'shish" bo'limi.
"""
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.requests import add_schedule_item, get_active_schedule_items
from filters.admin_filter import IsVerifiedAdmin
from keyboards.admin_kb import AdminNavCB, back_to_admin_main_kb, schedule_section_kb
from services.broadcast import broadcast_to_all_channels
from states.states import AddSchedule

logger = logging.getLogger(__name__)
router = Router(name="admin_schedule")
router.message.filter(IsVerifiedAdmin())
router.callback_query.filter(IsVerifiedAdmin())


@router.callback_query(AdminNavCB.filter(F.action == "schedule_section"))
async def cb_schedule_section(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    items = await get_active_schedule_items()
    if items:
        body = "\n\n".join(f"• {item.text}" for item in items)
        text = f"📅 <b>Joriy dars jadvali</b> (barcha guruhlar uchun):\n\n{body}"
    else:
        text = "📅 <b>Dars jadvali</b>\n\nHozircha dars jadvali kiritilmagan."

    await callback.message.edit_text(text, reply_markup=schedule_section_kb())
    await callback.answer()


@router.callback_query(AdminNavCB.filter(F.action == "add_schedule"))
async def cb_add_schedule_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddSchedule.waiting_for_text)
    await callback.message.edit_text(
        "✍️ Bugungi dars jadvali matnini yuboring.\n\n"
        "Agar rasm biriktirmoqchi bo'lsangiz, rasmni tavsif (caption) bilan birga yuboring.",
        reply_markup=back_to_admin_main_kb(),
    )
    await callback.answer()


@router.message(AddSchedule.waiting_for_text, F.photo)
async def process_add_schedule_photo(message: Message, state: FSMContext) -> None:
    text = message.caption or "Dars jadvali (rasm ilova qilingan)"
    photo_file_id = message.photo[-1].file_id
    await _save_and_broadcast_schedule(message, state, text, photo_file_id)


@router.message(AddSchedule.waiting_for_text, F.text)
async def process_add_schedule_text(message: Message, state: FSMContext) -> None:
    await _save_and_broadcast_schedule(message, state, message.text, None)


async def _save_and_broadcast_schedule(
    message: Message, state: FSMContext, text: str, photo_file_id: str | None
) -> None:
    await add_schedule_item(text=text, photo_file_id=photo_file_id)
    success, failed = await broadcast_to_all_channels(
        message.bot, text=f"📅 Bugungi dars jadvali:\n\n{text}", photo_file_id=photo_file_id
    )
    await state.clear()

    result_note = f"\n\n📡 {success} ta guruh kanaliga yuborildi."
    if failed:
        result_note += f" ({failed} tasiga yuborishda xatolik yuz berdi)"

    await message.answer(
        "✅ Dars jadvali muvaffaqiyatli qo'shildi va barcha guruhlar uchun amal qiladi." + result_note,
        reply_markup=back_to_admin_main_kb(),
    )
