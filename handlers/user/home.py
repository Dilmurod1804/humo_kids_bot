# """
# Home menyusi: /start buyrug'i, guruhlar ro'yxati, guruh tanlash,
# va admin panelga o'tish tugmasi.
# """
# import logging

# from aiogram import F, Router
# from aiogram.filters import CommandStart
# from aiogram.fsm.context import FSMContext
# from aiogram.types import CallbackQuery, Message

# from database.requests import get_active_groups, get_group_by_id
# from keyboards.user_kb import GroupCB, NavCB, group_menu_kb, home_menu_kb
# from states.states import AdminAuth

# logger = logging.getLogger(__name__)
# router = Router(name="user_home")


# async def show_home_menu(message: Message) -> None:
#     groups = await get_active_groups()
#     if groups:
#         text = "👋 Xush kelibsiz, <b>Humo Kids</b> bog'chasi botiga!\n\nQuyidagi guruhlardan birini tanlang:"
#     else:
#         text = (
#             "👋 Xush kelibsiz, <b>Humo Kids</b> bog'chasi botiga!\n\n"
#             "Hozircha hech qanday guruh qo'shilmagan."
#         )
#     await message.answer(text, reply_markup=home_menu_kb(groups))


# @router.message(CommandStart())
# async def cmd_start(message: Message, state: FSMContext) -> None:
#     await state.clear()
#     await show_home_menu(message)


# @router.callback_query(NavCB.filter(F.action == "home"))
# async def cb_back_home(callback: CallbackQuery, state: FSMContext) -> None:
#     await state.clear()
#     groups = await get_active_groups()
#     if groups:
#         text = "🏠 Bosh menyu.\n\nQuyidagi guruhlardan birini tanlang:"
#     else:
#         text = "🏠 Bosh menyu.\n\nHozircha hech qanday guruh qo'shilmagan."
#     await callback.message.edit_text(text, reply_markup=home_menu_kb(groups))
#     await callback.answer()


# @router.callback_query(GroupCB.filter())
# async def cb_select_group(callback: CallbackQuery, callback_data: GroupCB, state: FSMContext) -> None:
#     await state.clear()
#     group = await get_group_by_id(callback_data.group_id)

#     if group is None or not group.is_active:
#         await callback.answer("Bu guruh topilmadi yoki o'chirilgan.", show_alert=True)
#         return

#     if group.channel_invite_link:
#         text = (
#             f"📌 <b>{group.name}</b>\n\n"
#             f"Guruh kanali: {group.channel_invite_link}\n\n"
#             f"Quyidagi bo'limlardan birini tanlang:"
#         )
#     else:
#         text = (
#             f"📌 <b>{group.name}</b>\n\n"
#             f"⚠️ Bu guruh uchun kanal hali sozlanmagan.\n\n"
#             f"Quyidagi bo'limlardan birini tanlang:"
#         )

#     await callback.message.edit_text(text, reply_markup=group_menu_kb(group.id))
#     await callback.answer()


# @router.callback_query(NavCB.filter(F.action == "admin_panel"))
# async def cb_admin_panel_entry(callback: CallbackQuery, state: FSMContext) -> None:
#     """Home menyusidan 'Admin panel' tugmasi bosilganda — kirish kodi so'raladi."""
#     await state.set_state(AdminAuth.waiting_for_code)
#     await callback.message.edit_text(
#         "🔐 Admin panelga kirish uchun kirish kodini yuboring:"
#     )
#     await callback.answer()



import logging
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.requests import get_active_groups, get_group_by_id
from keyboards.user_kb import GroupCB, NavCB, group_menu_kb, home_menu_kb
from states.states import AdminAuth

logger = logging.getLogger(__name__)
router = Router(name="user_home")


async def safe_edit_or_answer(callback: CallbackQuery, text: str, reply_markup=None):
    """Xabarni xavfsiz tahrirlash (agar media bo'lib qolgan bo'lsa, o'chirib yuboradi)."""
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    except TelegramBadRequest:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(text, reply_markup=reply_markup, parse_mode="HTML")


async def show_home_menu(message: Message) -> None:
    groups = await get_active_groups()
    if groups:
        text = "👋 Xush kelibsiz, <b>Humo Kids</b> bog'chasi botiga!\n\nQuyidagi guruhlardan birini tanlang:"
    else:
        text = (
            "👋 Xush kelibsiz, <b>Humo Kids</b> bog'chasi botiga!\n\n"
            "Hozircha hech qanday guruh qo'shilmagan."
        )
    await message.answer(text, reply_markup=home_menu_kb(groups), parse_mode="HTML")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await show_home_menu(message)


@router.callback_query(NavCB.filter(F.action == "home"))
async def cb_back_home(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    groups = await get_active_groups()
    if groups:
        text = "🏠 Bosh menyu.\n\nQuyidagi guruhlardan birini tanlang:"
    else:
        text = "🏠 Bosh menyu.\n\nHozircha hech qanday guruh qo'shilmagan."
    
    await safe_edit_or_answer(callback, text, reply_markup=home_menu_kb(groups))
    await callback.answer()


@router.callback_query(GroupCB.filter())
async def cb_select_group(callback: CallbackQuery, callback_data: GroupCB, state: FSMContext) -> None:
    await state.clear()
    group = await get_group_by_id(callback_data.group_id)

    if group is None or not group.is_active:
        await callback.answer("Bu guruh topilmadi yoki o'chirilgan.", show_alert=True)
        return

    if group.channel_invite_link:
        text = (
            f"📌 <b>{group.name}</b>\n\n"
            f"Guruh kanali: {group.channel_invite_link}\n\n"
            f"Quyidagi bo'limlardan birini tanlang:"
        )
    else:
        text = (
            f"📌 <b>{group.name}</b>\n\n"
            f"⚠️ Bu guruh uchun kanal hali sozlanmagan.\n\n"
            f"Quyidagi bo'limlardan birini tanlang:"
        )

    await safe_edit_or_answer(callback, text, reply_markup=group_menu_kb(group.id))
    await callback.answer()


@router.callback_query(NavCB.filter(F.action == "admin_panel"))
async def cb_admin_panel_entry(callback: CallbackQuery, state: FSMContext) -> None:
    """Home menyusidan 'Admin panel' tugmasi bosilganda — kirish kodi so'raladi."""
    await state.set_state(AdminAuth.waiting_for_code)
    text = "🔐 Admin panelga kirish uchun kirish kodini yuboring:"
    await safe_edit_or_answer(callback, text)
    await callback.answer()
