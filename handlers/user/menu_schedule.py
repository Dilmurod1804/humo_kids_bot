# """
# Guruh menyusidagi "Bugungi taomnoma" va "Bugungi dars jadvali" tugmalari.
# """
from aiogram import Router
from aiogram.types import CallbackQuery

from database.requests import get_active_menu_items, get_active_schedule_items, get_group_by_id
from keyboards.user_kb import ShowCB, back_to_group_kb

router = Router(name="user_menu_schedule")


# @router.callback_query(ShowCB.filter())
# async def cb_show_menu_or_schedule(callback: CallbackQuery, callback_data: ShowCB) -> None:
#     group = await get_group_by_id(callback_data.group_id)
#     if group is None:
#         await callback.answer("Guruh topilmadi.", show_alert=True)
#         return

#     if callback_data.action == "menu":
#         items = await get_active_menu_items()
#         title = f"🍽 <b>{group.name}</b> — bugungi taomnoma"
#         empty_text = "Bugungi taomnoma hali kiritilmagan."
#     else:
#         items = await get_active_schedule_items()
#         title = f"📅 <b>{group.name}</b> — bugungi dars jadvali"
#         empty_text = "Bugungi dars jadvali hali kiritilmagan."

#     if not items:
#         text = f"{title}\n\n{empty_text}"
#     else:
#         body = "\n\n".join(f"• {item.text}" for item in items)
#         text = f"{title}\n\n{body}"

#     photo_item = next((item for item in items if item.photo_file_id), None) 

#     await callback.message.edit_text(text, reply_markup=back_to_group_kb(group.id))

#     # Agar yozuvlardan birortasida rasm biriktirilgan bo'lsa, alohida yuboriladi
#     for item in items:
#         if item.photo_file_id:
#             await callback.message.answer_photo(photo=item.photo_file_id)

#     await callback.answer()




@router.callback_query(ShowCB.filter())
async def cb_show_menu_or_schedule(callback: CallbackQuery, callback_data: ShowCB) -> None:
    group = await get_group_by_id(callback_data.group_id)
    if group is None:
        await callback.answer("Guruh topilmadi.", show_alert=True)
        return

    if callback_data.action == "menu":
        items = await get_active_menu_items()
        title = f"🍽 <b>{group.name}</b> — bugungi taomnoma"
        empty_text = "Bugungi taomnoma hali kiritilmagan."
    else:
        items = await get_active_schedule_items()
        title = f"📅 <b>{group.name}</b> — bugungi dars jadvali"
        empty_text = "Bugungi dars jadvali hali kiritilmagan."

    if not items:
        text = f"{title}\n\n{empty_text}"
        await callback.message.edit_text(text, reply_markup=back_to_group_kb(group.id), parse_mode="HTML")
        await callback.answer()
        return

    body = "\n\n".join(f"• {item.text}" for item in items)
    text = f"{title}\n\n{body}"

    # Agar rasmli item mavjud bo'lsa
    photo_item = next((item for item in items if item.photo_file_id), None)
    
    if photo_item:
        # Eski xabarni o'chiramiz (chunki rasm bilan matnni bitta xabarda birlashtirish toza chiqadi)
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer_photo(
            photo=photo_item.photo_file_id,
            caption=text,
            reply_markup=back_to_group_kb(group.id),
            parse_mode="HTML"
        )
    else:
        # Faqat matn bo'lsa — o'rnida tahrirlaymiz
        await callback.message.edit_text(
            text, 
            reply_markup=back_to_group_kb(group.id), 
            parse_mode="HTML"
        )

    await callback.answer()