"""
Oddiy foydalanuvchi ("Home") uchun klaviaturalar va callback-data klasslari.
"""
from typing import Sequence

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import Group


# --------------------------- Callback data klasslari ---------------------------

class GroupCB(CallbackData, prefix="group"):
    """Home menyusida biror guruh tugmasi bosilganda ishlatiladi."""
    group_id: int


class ShowCB(CallbackData, prefix="show"):
    """Guruh menyusida 'Bugungi taomnoma' / 'Bugungi dars jadvali' tugmalari."""
    action: str  # "menu" yoki "schedule"
    group_id: int


class NavCB(CallbackData, prefix="nav"):
    """Oddiy navigatsiya tugmalari (Home ga qaytish, admin panelga kirish va h.k.)."""
    action: str  # "home" | "admin_panel"


# --------------------------- Klaviaturalar ---------------------------

def home_menu_kb(groups: Sequence[Group]) -> InlineKeyboardMarkup:
    """Home menyusi: har bir guruh alohida tugma + Admin panel tugmasi."""
    builder = InlineKeyboardBuilder()
    for group in groups:
        builder.button(text=group.name, callback_data=GroupCB(group_id=group.id))
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="🔐 Admin panel", callback_data=NavCB(action="admin_panel").pack())
    )
    return builder.as_markup()


def group_menu_kb(group_id: int) -> InlineKeyboardMarkup:
    """Guruh tanlanganda: taomnoma / dars jadvali / ortga tugmalari."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🍽 Bugungi taomnoma", callback_data=ShowCB(action="menu", group_id=group_id))
    builder.button(text="📅 Bugungi dars jadvali", callback_data=ShowCB(action="schedule", group_id=group_id))
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="⬅️ Ortga", callback_data=NavCB(action="home").pack())
    )
    return builder.as_markup()


def back_to_group_kb(group_id: int) -> InlineKeyboardMarkup:
    """Taomnoma/dars jadvali ko'rsatilgandan keyin guruh menyusiga qaytish tugmasi."""
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Ortga", callback_data=GroupCB(group_id=group_id))
    return builder.as_markup()
