"""
Admin panel — Guruh qo'shish, guruhlar ro'yxati va guruhni o'chirish.

Yangi guruh yaratish jarayoni (5.6-band, TZ):
  1) Guruh nomi so'raladi
  2) "Bola qo'shish" tugmasi bilan bolalar ketma-ket qo'shiladi
  3) Admin "Tugatish" tugmasini bosgach:
     - Channel Service orqali yangi Telegram kanal avtomatik yaratiladi
     - Guruh va bolalar bazaga yoziladi
"""
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.requests import (
    create_group,
    delete_group as db_delete_group,
    get_active_groups,
    get_group_by_id,
    get_group_by_name,
    set_group_channel,
)
from filters.admin_filter import IsVerifiedAdmin
from keyboards.admin_kb import (
    AdminGroupCB,
    AdminNavCB,
    ConfirmCB,
    GroupActionCB,
    add_child_or_finish_kb,
    back_to_admin_main_kb,
    confirm_kb,
    group_manage_kb,
    groups_list_kb,
)
from services.channel_client import ChannelServiceError, channel_client
from states.states import AddGroup, DeleteGroup

logger = logging.getLogger(__name__)
router = Router(name="admin_groups")
router.message.filter(IsVerifiedAdmin())
router.callback_query.filter(IsVerifiedAdmin())


# ---------------------------------------------------------------------------
# Yangi guruh qo'shish
# ---------------------------------------------------------------------------

@router.callback_query(AdminNavCB.filter(F.action == "add_group"))
async def cb_add_group_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddGroup.waiting_for_group_name)
    await state.update_data(children_names=[])
    await callback.message.edit_text(
        "✍️ Yangi guruh nomini kiriting (masalan: 4-guruh):",
        reply_markup=back_to_admin_main_kb(),
    )
    await callback.answer()


@router.message(AddGroup.waiting_for_group_name, F.text)
async def process_group_name(message: Message, state: FSMContext) -> None:
    group_name = message.text.strip()

    existing = await get_group_by_name(group_name)
    if existing is not None:
        await message.answer(
            "⚠️ Bu nomdagi guruh allaqachon mavjud. Boshqa nom kiriting:"
        )
        return

    await state.update_data(group_name=group_name)
    await message.answer(
        f"✅ Guruh nomi: <b>{group_name}</b>\n\n"
        f"Endi shu guruh uchun bolalarni qo'shishingiz mumkin.",
        reply_markup=add_child_or_finish_kb(),
    )


@router.callback_query(AddGroup.waiting_for_group_name, AdminNavCB.filter(F.action == "add_child_to_new_group"))
@router.callback_query(AddGroup.waiting_for_child_name, AdminNavCB.filter(F.action == "add_child_to_new_group"))
async def cb_add_child_to_new_group(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddGroup.waiting_for_child_name)
    await callback.message.edit_text("✍️ Bolaning to'liq ismini (F.I.O) kiriting:")
    await callback.answer()


@router.message(AddGroup.waiting_for_child_name, F.text)
async def process_child_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    children_names: list[str] = data.get("children_names", [])
    children_names.append(message.text.strip())
    await state.update_data(children_names=children_names)
    await state.set_state(AddGroup.waiting_for_group_name)  # "kutish" holatiga qaytish

    await message.answer(
        f"✅ Qo'shildi: <b>{message.text.strip()}</b>\n"
        f"Jami bolalar soni: {len(children_names)}\n\n"
        f"Yana bola qo'shasizmi yoki yakunlaysizmi?",
        reply_markup=add_child_or_finish_kb(),
    )


@router.callback_query(AddGroup.waiting_for_group_name, AdminNavCB.filter(F.action == "finish_add_group"))
async def cb_finish_add_group(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    group_name: str | None = data.get("group_name")
    children_names: list[str] = data.get("children_names", [])

    if not group_name:
        await callback.answer("Xatolik: guruh nomi topilmadi. Qaytadan boshlang.", show_alert=True)
        await state.clear()
        return

    await callback.message.edit_text("⏳ Kanal yaratilmoqda, biroz kuting...")

    try:
        result = await channel_client.create_channel(
            title=group_name,
            description=f"Humo Kids bog'chasi — {group_name} rasmiy kanali",
        )
    except ChannelServiceError as e:
        logger.exception("Kanal yaratishda xatolik")
        await callback.message.edit_text(
            f"❌ Kanal yaratishda xatolik yuz berdi:\n{e}\n\n"
            f"Guruh bazaga saqlanmadi. Qaytadan urinib ko'ring.",
            reply_markup=back_to_admin_main_kb(),
        )
        await state.clear()
        return

    group = await create_group(name=group_name)
    await set_group_channel(
        group_id=group.id,
        channel_id=result["channel_id"],
        invite_link=result["invite_link"],
    )

    from database.requests import add_child
    for child_name in children_names:
        await add_child(group_id=group.id, full_name=child_name)

    await state.clear()
    await callback.message.edit_text(
        f"✅ <b>{group_name}</b> guruhi muvaffaqiyatli yaratildi!\n\n"
        f"👶 Bolalar soni: {len(children_names)}\n"
        f"📢 Kanal: {result['invite_link']}",
        reply_markup=back_to_admin_main_kb(),
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Guruhlar ro'yxati
# ---------------------------------------------------------------------------

@router.callback_query(AdminNavCB.filter(F.action == "groups_list"))
async def cb_groups_list(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    groups = await get_active_groups()
    if not groups:
        await callback.message.edit_text(
            "📋 Guruhlar ro'yxati bo'sh.", reply_markup=back_to_admin_main_kb()
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "📋 Guruhni tanlang:", reply_markup=groups_list_kb(groups)
    )
    await callback.answer()


@router.callback_query(AdminGroupCB.filter())
async def cb_group_manage(callback: CallbackQuery, callback_data: AdminGroupCB, state: FSMContext) -> None:
    await state.clear()
    group = await get_group_by_id(callback_data.group_id)
    if group is None:
        await callback.answer("Guruh topilmadi.", show_alert=True)
        return

    from database.requests import get_children_by_group
    children = await get_children_by_group(group.id)

    text = (
        f"📌 <b>{group.name}</b>\n\n"
        f"👶 Bolalar soni: {len(children)}\n"
        f"📢 Kanal: {group.channel_invite_link or 'sozlanmagan'}\n\n"
        f"Amalni tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=group_manage_kb(group.id))
    await callback.answer()


# ---------------------------------------------------------------------------
# Guruhni o'chirish
# ---------------------------------------------------------------------------

@router.callback_query(GroupActionCB.filter(F.action == "delete_group"))
async def cb_delete_group_confirm_ask(callback: CallbackQuery, callback_data: GroupActionCB, state: FSMContext) -> None:
    group = await get_group_by_id(callback_data.group_id)
    if group is None:
        await callback.answer("Guruh topilmadi.", show_alert=True)
        return

    await callback.message.edit_text(
        f"⚠️ Rostdan ham <b>{group.name}</b> guruhini o'chirmoqchimisiz?\n\n"
        f"Bu amal guruhga bog'liq barcha bolalar va Telegram kanalini ham o'chiradi. "
        f"Bu amalni ortga qaytarib bo'lmaydi.",
        reply_markup=confirm_kb(action="delete_group", target_id=group.id),
    )
    await callback.answer()


@router.callback_query(ConfirmCB.filter(F.action == "delete_group"))
async def cb_delete_group_confirmed(callback: CallbackQuery, callback_data: ConfirmCB, state: FSMContext) -> None:
    if callback_data.decision == "no":
        await callback.message.edit_text(
            "🔙 Guruh o'chirilmadi. Admin panel bosh menyusi.",
            reply_markup=admin_main_menu_kb_safe(),
        )
        await callback.answer()
        return

    group = await get_group_by_id(callback_data.target_id)
    if group is None:
        await callback.answer("Guruh allaqachon topilmadi.", show_alert=True)
        return

    group_name = group.name
    channel_id = group.channel_id

    if channel_id is not None:
        try:
            await channel_client.delete_channel(channel_id)
        except ChannelServiceError as e:
            logger.exception("Kanalni o'chirishda xatolik")
            await callback.message.edit_text(
                f"❌ Kanalni o'chirishda xatolik yuz berdi:\n{e}\n\n"
                f"Guruh bazadan o'chirilmadi, qaytadan urinib ko'ring.",
                reply_markup=back_to_admin_main_kb(),
            )
            await callback.answer()
            return

    await db_delete_group(group.id)

    await callback.message.edit_text(
        f"✅ <b>{group_name}</b> guruhi, unga bog'liq barcha bolalar va kanal muvaffaqiyatli o'chirildi.",
        reply_markup=back_to_admin_main_kb(),
    )
    await callback.answer()


def admin_main_menu_kb_safe():
    """auth.py dagi asosiy menyuni qayta ishlatish uchun yordamchi import."""
    from keyboards.admin_kb import admin_main_menu_kb
    return admin_main_menu_kb()


@router.callback_query(AdminNavCB.filter(F.action == "main"))
async def cb_admin_main(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "🔐 Admin panel bosh menyusi.", reply_markup=admin_main_menu_kb_safe()
    )
    await callback.answer()
