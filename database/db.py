"""
Async ma'lumotlar bazasi bilan ulanish (engine, session, init).
"""
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import settings
from database.models import Base

engine = create_async_engine(settings.database_url, echo=False)

async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def init_db() -> None:
    """Bot ishga tushganda jadvallarni (agar mavjud bo'lmasa) yaratadi."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
