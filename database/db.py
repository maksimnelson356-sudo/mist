import asyncpg
from config import DB_DSN

_pool: asyncpg.Pool = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DB_DSN, min_size=2, max_size=10)
    return _pool


async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        with open("schema.sql", "r", encoding="utf-8") as f:
            await conn.execute(f.read())


async def close_db():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
