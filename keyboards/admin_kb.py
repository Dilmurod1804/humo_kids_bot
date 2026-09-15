"""
Admin panel uchun klaviaturalar va callback-data klasslari.
"""
from typing import Sequence

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import Child, Group


# --------------------------- Callback data klasslari ---------------------------

class AdminNavCB(CallbackData, prefix="anav"):
    """Admin panel ichidagi asosiy navigatsiya."""
    action: str
    # action variantlari:
    # "main"            -> admin panel bosh menyusi
    # "menu_section"    -> Ovqatlar bo'limi
    # "schedule_section"-> Dars jadvali bo'limi
    # "add_menu"        -> Ovqat qo'shish
    # "add_schedule"    -> Dars jadvali qo'shish
    # "add_group"       -> Guruh qo'shish
    # "groups_list"     -> Guruhlar ro'yxati
    # "add_child_to_new_group" -> yangi guruhga navbatdagi bolani qo'shish
    # "finish_add_group"       -> yangi guruhni yakunlash (kanal yaratish)


class AdminGroupCB(CallbackData, prefix="agroup"):
    """Guruhlar ro'yxatida biror guruh tanlanganda."""
    group_id: int


class GroupActionCB(CallbackData, prefix="gaction"):
    """Tanlangan guruh uchun amallar: bola qo'shish / o'chirish / guruhni o'chirish."""
    action: str  # "add_child" | "remove_child_menu" | "delete_group"
    group_id: int


class DeleteChildCB(CallbackData, prefix="delchild"):
    """Bola o'chirish ro'yxatida bola tanlanganda."""
    child_id: int
    group_id: int


class ConfirmCB(CallbackData, prefix="confirm"):
    """Ha/Yo'q tasdiqlash tugmalari uchun umumiy callback."""
    action: str  # "delete_group" | "delete_child"
    target_id: int
    decision: str  # "yes" | "no"


# --------------------------- Klaviaturalar ---------------------------

def admin_main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🍽 Ovqatlar", callback_data=AdminNavCB(action="menu_section"))
    builder.button(text="📅 Dars jadvali qo'shish", callback_data=AdminNavCB(action="schedule_section"))
    builder.button(text="➕ Guruh qo'shish", callback_data=AdminNavCB(action="add_group"))
    builder.button(text="📋 Guruhlar ro'yxati", callback_data=AdminNavCB(action="groups_list"))
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="⬅️ Ortga (Home)", callback_data="nav_home_from_admin")
    )
    return builder.as_markup()


def back_to_admin_main_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Ortga", callback_data=AdminNavCB(action="main"))
    return builder.as_markup()


def menu_section_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Ovqat qo'shish", callback_data=AdminNavCB(action="add_menu"))
    builder.button(text="⬅️ Ortga", callback_data=AdminNavCB(action="main"))
    builder.adjust(1)
    return builder.as_markup()


def schedule_section_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Dars jadvali qo'shish", callback_data=AdminNavCB(action="add_schedule"))
    builder.button(text="⬅️ Ortga", callback_data=AdminNavCB(action="main"))
    builder.adjust(1)
    return builder.as_markup()


def add_child_or_finish_kb() -> InlineKeyboardMarkup:
    """Yangi guruh yaratish jarayonida: yana bola qo'shish yoki yakunlash."""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Bola qo'shish", callback_data=AdminNavCB(action="add_child_to_new_group"))
    builder.button(text="✅ Tugatish va kanal yaratish", callback_data=AdminNavCB(action="finish_add_group"))
    builder.adjust(1)
    return builder.as_markup()


def groups_list_kb(groups: Sequence[Group]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for group in groups:
        builder.button(text=group.name, callback_data=AdminGroupCB(group_id=group.id))
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="⬅️ Ortga", callback_data=AdminNavCB(action="main").pack())
    )
    return builder.as_markup()


def group_manage_kb(group_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Bola qo'shish", callback_data=GroupActionCB(action="add_child", group_id=group_id))
    builder.button(text="➖ Bola o'chirish", callback_data=GroupActionCB(action="remove_child_menu", group_id=group_id))
    builder.button(text="🗑 Guruhni o'chirish", callback_data=GroupActionCB(action="delete_group", group_id=group_id))
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="⬅️ Ortga", callback_data=AdminNavCB(action="groups_list").pack())
    )
    return builder.as_markup()


def children_delete_list_kb(children: Sequence[Child], group_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for child in children:
        builder.button(
            text=child.full_name,
            callback_data=DeleteChildCB(child_id=child.id, group_id=group_id),
        )
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="⬅️ Ortga", callback_data=AdminGroupCB(group_id=group_id).pack())
    )
    return builder.as_markup()


def confirm_kb(action: str, target_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha", callback_data=ConfirmCB(action=action, target_id=target_id, decision="yes"))
    builder.button(text="❌ Yo'q", callback_data=ConfirmCB(action=action, target_id=target_id, decision="no"))
    builder.adjust(2)
    return builder.as_markup()
