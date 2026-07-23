import aiosqlite
from config import DB_PATH

_db: aiosqlite.Connection = None


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DB_PATH)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA foreign_keys=ON")
    return _db


async def init_db():
    db = await get_db()
    with open("schema.sql", "r", encoding="utf-8") as f:
        await db.executescript(f.read())
    await db.commit()


async def close_db():
    global _db
    if _db:
        await _db.close()
        _db = None
