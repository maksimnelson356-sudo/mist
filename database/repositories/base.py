from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    model = None

    @classmethod
    async def add(cls, session: AsyncSession, obj):
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    @classmethod
    async def get(cls, session: AsyncSession, **filters) -> dict | None:
        stmt = select(cls.model)
        for key, val in filters.items():
            stmt = stmt.where(getattr(cls.model, key) == val)
        result = await session.execute(stmt)
        row = result.scalars().first()
        return dict(row.__dict__) if row else None

    @classmethod
    async def get_all(cls, session: AsyncSession, **filters) -> list:
        stmt = select(cls.model)
        for key, val in filters.items():
            stmt = stmt.where(getattr(cls.model, key) == val)
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @classmethod
    async def update(cls, session: AsyncSession, filters: dict, **kwargs):
        stmt = update(cls.model).where(
            *[getattr(cls.model, k) == v for k, v in filters.items()]
        ).values(**kwargs)
        await session.execute(stmt)
        await session.commit()

    @classmethod
    async def delete(cls, session: AsyncSession, **filters):
        stmt = delete(cls.model).where(
            *[getattr(cls.model, k) == v for k, v in filters.items()]
        )
        await session.execute(stmt)
        await session.commit()
