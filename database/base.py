from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from config import DB_PATH


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory = None


def _get_engine():
    global _engine
    if _engine is None:
        url = f"sqlite+aiosqlite:///{DB_PATH}"
        _engine = create_async_engine(url, echo=False)
    return _engine


def _get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _session_factory


async def get_db():
    factory = _get_session_factory()
    async with factory() as session:
        yield session


async def get_session() -> AsyncSession:
    factory = _get_session_factory()
    return factory()


async def init_db():
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    global _engine, _session_factory
    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None
