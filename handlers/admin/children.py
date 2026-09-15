"""
Admin panel — mavjud guruhga bola qo'shish yoki guruhdan bola o'chirish.
("Guruhlar ro'yxati" -> biror guruh -> "Bola qo'shish" / "Bola o'chirish")
"""
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.requests import (
    add_child,
    delete_child,
    get_child_by_id,
    get_children_by_group,
    get_group_by_id,
)
from filters.admin_filter import IsVerifiedAdmin
from keyboards.admin_kb import (
    ConfirmCB,
    DeleteChildCB,
    GroupActionCB,
    children_delete_list_kb,
    confirm_kb,
    group_manage_kb,
)
from states.states import ManageChildren

logger = logging.getLogger(__name__)
router = Router(name="admin_children")
router.message.filter(IsVerifiedAdmin())
router.callback_query.filter(IsVerifiedAdmin())


# ---------------------------------------------------------------------------
# Bola qo'shish (mavjud guruhga)
# ---------------------------------------------------------------------------

@router.callback_query(GroupActionCB.filter(F.action == "add_child"))
async def cb_add_child_start(callback: CallbackQuery, callback_data: GroupActionCB, state: FSMContext) -> None:
    group = await get_group_by_id(callback_data.group_id)
    if group is None:
        await callback.answer("Guruh topilmadi.", show_alert=True)
        return

    await state.set_state(ManageChildren.waiting_for_child_name)
    await state.update_data(group_id=group.id)
    await callback.message.edit_text(
        f"✍️ <b>{group.name}</b> guruhiga qo'shiladigan bolaning F.I.O sini kiriting:"
    )
    await callback.answer()


@router.message(ManageChildren.waiting_for_child_name, F.text)
async def process_add_child_existing_group(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    group_id = data.get("group_id")
    group = await get_group_by_id(group_id)

    if group is None:
        await message.answer("⚠️ Guruh topilmadi. Amal bekor qilindi.")
        await state.clear()
        return

    await add_child(group_id=group.id, full_name=message.text.strip())
    await state.clear()

    await message.answer(
        f"✅ <b>{message.text.strip()}</b> — <b>{group.name}</b> guruhiga qo'shildi.",
        reply_markup=group_manage_kb(group.id),
    )


# ---------------------------------------------------------------------------
# Bola o'chirish
# ---------------------------------------------------------------------------

@router.callback_query(GroupActionCB.filter(F.action == "remove_child_menu"))
async def cb_remove_child_menu(callback: CallbackQuery, callback_data: GroupActionCB, state: FSMContext) -> None:
    group = await get_group_by_id(callback_data.group_id)
    if group is None:
        await callback.answer("Guruh topilmadi.", show_alert=True)
        return

    children = await get_children_by_group(group.id)
    if not children:
        await callback.answer("Bu guruhda hozircha bolalar yo'q.", show_alert=True)
        return

    await callback.message.edit_text(
        f"➖ <b>{group.name}</b> guruhidan o'chiriladigan bolani tanlang:",
        reply_markup=children_delete_list_kb(children, group.id),
    )
    await callback.answer()


@router.callback_query(DeleteChildCB.filter())
async def cb_delete_child_confirm_ask(callback: CallbackQuery, callback_data: DeleteChildCB, state: FSMContext) -> None:
    child = await get_child_by_id(callback_data.child_id)
    if child is None:
        await callback.answer("Bola topilmadi.", show_alert=True)
        return

    await callback.message.edit_text(
        f"⚠️ Rostdan ham <b>{child.full_name}</b> ni guruhdan o'chirmoqchimisiz?",
        reply_markup=confirm_kb(action="delete_child", target_id=child.id),
    )
    await callback.answer()


@router.callback_query(ConfirmCB.filter(F.action == "delete_child"))
async def cb_delete_child_confirmed(callback: CallbackQuery, callback_data: ConfirmCB, state: FSMContext) -> None:
    child = await get_child_by_id(callback_data.target_id)

    if callback_data.decision == "no" or child is None:
        if child is not None:
            group = await get_group_by_id(child.group_id)
            await callback.message.edit_text(
                "🔙 Bekor qilindi.", reply_markup=group_manage_kb(group.id)
            )
        await callback.answer()
        return

    group_id = child.group_id
    child_name = child.full_name
    await delete_child(child.id)

    group = await get_group_by_id(group_id)
    await callback.message.edit_text(
        f"✅ <b>{child_name}</b> guruhdan o'chirildi.",
        reply_markup=group_manage_kb(group_id) if group else None,
    )
    await callback.answer()
