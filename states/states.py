"""
Botning barcha FSM (Finite State Machine) holatlari shu yerda to'plangan.
"""
from aiogram.fsm.state import State, StatesGroup


class AdminAuth(StatesGroup):
    """Admin panelga kirish kodi so'ralayotgan holat."""
    waiting_for_code = State()


class AddMenu(StatesGroup):
    """Taomnoma qo'shish."""
    waiting_for_text = State()


class AddSchedule(StatesGroup):
    """Dars jadvali qo'shish."""
    waiting_for_text = State()


class AddGroup(StatesGroup):
    """Yangi guruh va unga bolalar qo'shish jarayoni."""
    waiting_for_group_name = State()
    waiting_for_child_name = State()


class ManageChildren(StatesGroup):
    """Mavjud guruhga yangi bola qo'shish."""
    waiting_for_child_name = State()


class DeleteGroup(StatesGroup):
    """Guruhni o'chirish jarayoni."""
    waiting_for_group_name = State()
    waiting_for_confirmation = State()
