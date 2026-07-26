import logging
from sqlalchemy import text, String, Integer, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func
from config import DB_PATH

logger = logging.getLogger("MIST.db")


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory = None

_TYPE_MAP = {
    "VARCHAR": "TEXT",
    "String": "TEXT",
    "TEXT": "TEXT",
    "INTEGER": "INTEGER",
    "Integer": "INTEGER",
    "FLOAT": "REAL",
    "Float": "REAL",
    "REAL": "REAL",
    "BOOLEAN": "INTEGER",
    "Boolean": "INTEGER",
    "DATETIME": "TEXT",
    "DateTime": "TEXT",
    "JSON": "TEXT",
}


def _sqlite_type(col_type):
    name = col_type.__class__.__name__
    return _TYPE_MAP.get(name, "TEXT")


def _sqlite_default(col):
    if col.server_default is not None:
        return ""
    if col.default is not None:
        val = col.default.arg
        if isinstance(val, bool):
            return f"DEFAULT {int(val)}"
        if isinstance(val, (int, float)):
            return f"DEFAULT {val}"
        if isinstance(val, str):
            return f"DEFAULT '{val}'"
    return "DEFAULT NULL"


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


async def _ensure_columns(engine):
    import database.models
    async with engine.begin() as conn:
        tables_result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        db_tables = {row[0] for row in tables_result.fetchall()}

        for table in Base.metadata.sorted_tables:
            if table.name not in db_tables:
                continue
            result = await conn.execute(text(f"PRAGMA table_info({table.name})"))
            existing = {row[1] for row in result.fetchall()}
            for col in table.columns:
                if col.name not in existing:
                    col_type = _sqlite_type(col.type)
                    default = _sqlite_default(col)
                    sql = f"ALTER TABLE {table.name} ADD COLUMN {col.name} {col_type} {default}"
                    logger.info(f"ALTER TABLE {table.name} ADD COLUMN {col.name} {col_type}")
                    await conn.execute(text(sql))


async def init_db():
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _ensure_columns(engine)


async def close_db():
    global _engine, _session_factory
    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None
