"""
Ma'lumotlar bazasi bilan ishlash uchun barcha CRUD funksiyalari.
Handlerlar to'g'ridan-to'g'ri SQLAlchemy bilan ishlamasligi, faqat shu
funksiyalarni chaqirishi kerak — bu kodni toza va tartibli saqlaydi.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

from sqlalchemy import delete, select

from config import settings
from database.db import async_session
from database.models import Admin, Child, Group, MenuItem, ScheduleItem


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# ADMIN
# ---------------------------------------------------------------------------

async def is_admin_verified(telegram_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(Admin).where(Admin.telegram_id == telegram_id, Admin.is_verified.is_(True))
        )
        return result.scalar_one_or_none() is not None


async def verify_admin(telegram_id: int) -> None:
    async with async_session() as session:
        result = await session.execute(select(Admin).where(Admin.telegram_id == telegram_id))
        admin = result.scalar_one_or_none()
        if admin is None:
            admin = Admin(telegram_id=telegram_id, is_verified=True, verified_at=_now())
            session.add(admin)
        else:
            admin.is_verified = True
            admin.verified_at = _now()
        await session.commit()


# ---------------------------------------------------------------------------
# GROUPS
# ---------------------------------------------------------------------------

async def get_active_groups() -> Sequence[Group]:
    async with async_session() as session:
        result = await session.execute(
            select(Group).where(Group.is_active.is_(True)).order_by(Group.id)
        )
        return result.scalars().all()


async def get_group_by_id(group_id: int) -> Optional[Group]:
    async with async_session() as session:
        result = await session.execute(select(Group).where(Group.id == group_id))
        return result.scalar_one_or_none()


async def get_group_by_name(name: str) -> Optional[Group]:
    async with async_session() as session:
        result = await session.execute(
            select(Group).where(Group.name.ilike(name.strip()))
        )
        return result.scalar_one_or_none()


async def create_group(name: str) -> Group:
    async with async_session() as session:
        group = Group(name=name.strip(), is_active=True)
        session.add(group)
        await session.commit()
        await session.refresh(group)
        return group


async def set_group_channel(group_id: int, channel_id: int, invite_link: str) -> None:
    async with async_session() as session:
        result = await session.execute(select(Group).where(Group.id == group_id))
        group = result.scalar_one()
        group.channel_id = channel_id
        group.channel_invite_link = invite_link
        await session.commit()


async def delete_group(group_id: int) -> Optional[Group]:
    """Guruhni (va cascade orqali unga bog'liq bolalarni) bazadan o'chiradi."""
    async with async_session() as session:
        result = await session.execute(select(Group).where(Group.id == group_id))
        group = result.scalar_one_or_none()
        if group is None:
            return None
        await session.delete(group)
        await session.commit()
        return group


# ---------------------------------------------------------------------------
# CHILDREN
# ---------------------------------------------------------------------------

async def add_child(group_id: int, full_name: str) -> Child:
    async with async_session() as session:
        child = Child(group_id=group_id, full_name=full_name.strip())
        session.add(child)
        await session.commit()
        await session.refresh(child)
        return child


async def get_children_by_group(group_id: int) -> Sequence[Child]:
    async with async_session() as session:
        result = await session.execute(
            select(Child).where(Child.group_id == group_id).order_by(Child.full_name)
        )
        return result.scalars().all()


async def get_child_by_id(child_id: int) -> Optional[Child]:
    async with async_session() as session:
        result = await session.execute(select(Child).where(Child.id == child_id))
        return result.scalar_one_or_none()


async def delete_child(child_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(select(Child).where(Child.id == child_id))
        child = result.scalar_one_or_none()
        if child is None:
            return False
        await session.delete(child)
        await session.commit()
        return True


# ---------------------------------------------------------------------------
# MENU ITEMS (taomnoma)
# ---------------------------------------------------------------------------

async def add_menu_item(text: str, photo_file_id: Optional[str] = None) -> MenuItem:
    async with async_session() as session:
        item = MenuItem(
            text=text,
            photo_file_id=photo_file_id,
            created_at=_now(),
            expires_at=_now() + timedelta(hours=settings.menu_schedule_ttl_hours),
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item


async def get_active_menu_items() -> Sequence[MenuItem]:
    async with async_session() as session:
        result = await session.execute(
            select(MenuItem).where(MenuItem.expires_at > _now()).order_by(MenuItem.created_at)
        )
        return result.scalars().all()


# ---------------------------------------------------------------------------
# SCHEDULE ITEMS (dars jadvali)
# ---------------------------------------------------------------------------

async def add_schedule_item(text: str, photo_file_id: Optional[str] = None) -> ScheduleItem:
    async with async_session() as session:
        item = ScheduleItem(
            text=text,
            photo_file_id=photo_file_id,
            created_at=_now(),
            expires_at=_now() + timedelta(hours=settings.menu_schedule_ttl_hours),
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item


async def get_active_schedule_items() -> Sequence[ScheduleItem]:
    async with async_session() as session:
        result = await session.execute(
            select(ScheduleItem).where(ScheduleItem.expires_at > _now()).order_by(ScheduleItem.created_at)
        )
        return result.scalars().all()


# ---------------------------------------------------------------------------
# CLEANUP (scheduler uchun)
# ---------------------------------------------------------------------------

async def delete_expired_items() -> tuple[int, int]:
    """Muddati o'tgan taomnoma va dars jadvali yozuvlarini o'chiradi.

    Returns:
        (o'chirilgan_taomnoma_soni, o'chirilgan_jadval_soni)
    """
    async with async_session() as session:
        menu_result = await session.execute(
            delete(MenuItem).where(MenuItem.expires_at <= _now())
        )
        schedule_result = await session.execute(
            delete(ScheduleItem).where(ScheduleItem.expires_at <= _now())
        )
        await session.commit()
        return menu_result.rowcount or 0, schedule_result.rowcount or 0
