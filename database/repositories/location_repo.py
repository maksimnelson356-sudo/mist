import json
from datetime import UTC

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.location import LocationModel


class LocationRepository:

    @staticmethod
    async def get(session: AsyncSession, location_id: str) -> dict | None:
        stmt = select(LocationModel).where(LocationModel.location_id == location_id)
        result = await session.execute(stmt)
        row = result.scalars().first()
        if not row:
            return None
        d = dict(row.__dict__)
        if isinstance(d.get("connections"), str):
            d["connections"] = json.loads(d["connections"])
        return d

    @staticmethod
    async def get_all(session: AsyncSession) -> list:
        stmt = select(LocationModel)
        result = await session.execute(stmt)
        rows = result.scalars().all()
        out = []
        for r in rows:
            d = dict(r.__dict__)
            if isinstance(d.get("connections"), str):
                d["connections"] = json.loads(d["connections"])
            out.append(d)
        return out

    @staticmethod
    async def update(session: AsyncSession, location_id: str, **kwargs):
        if "connections" in kwargs and isinstance(kwargs["connections"], list):
            kwargs["connections"] = json.dumps(kwargs["connections"])
        stmt = update(LocationModel).where(
            LocationModel.location_id == location_id
        ).values(**kwargs)
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def set_discovered(session: AsyncSession, location_id: str, user_id: int):
        from datetime import datetime
        stmt = update(LocationModel).where(
            LocationModel.location_id == location_id
        ).values(
            discovered=True,
            discovered_by=user_id,
            discovered_at=datetime.now(UTC),
        )
        await session.execute(stmt)
        await session.commit()
