from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings


class Base(DeclarativeBase):
    pass


def get_engine():
    url = settings.database_url
    if url.startswith("sqlite"):
        return create_async_engine(url, echo=False)
    return create_async_engine(url, echo=False, pool_size=10, max_overflow=20)


def get_session_factory():
    return async_sessionmaker(get_engine(), class_=AsyncSession, expire_on_commit=False)


async_session_factory = None


async def get_session() -> AsyncSession:
    global async_session_factory
    if async_session_factory is None:
        async_session_factory = get_session_factory()
    async with async_session_factory() as session:
        yield session


async def init_db():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
