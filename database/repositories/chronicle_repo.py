import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.chronicle import ChronicleEventModel


class ChronicleRepository:

    @staticmethod
    async def add(session: AsyncSession, event_data: dict) -> str:
        event_id = str(uuid.uuid4())
        model = ChronicleEventModel(
            id=event_id,
            type=event_data["type"],
            importance=event_data["importance"],
            title=event_data["title"],
            description=event_data.get("description"),
            player_id=event_data.get("player_id"),
            region_id=event_data.get("region_id"),
            created_at=event_data.get("created_at", datetime.now(UTC)),
            expires_at=event_data.get("expires_at"),
            metadata_=event_data.get("metadata"),
        )
        session.add(model)
        await session.commit()
        return event_id

    @staticmethod
    async def get_latest(session: AsyncSession, limit: int = 20) -> list:
        stmt = select(ChronicleEventModel).order_by(
            ChronicleEventModel.created_at.desc()
        ).limit(limit)
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def get_by_player(session: AsyncSession, player_id: int, limit: int = 50) -> list:
        stmt = (
            select(ChronicleEventModel)
            .where(ChronicleEventModel.player_id == player_id)
            .order_by(ChronicleEventModel.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def get_by_region(session: AsyncSession, region_id: str, limit: int = 50) -> list:
        stmt = (
            select(ChronicleEventModel)
            .where(ChronicleEventModel.region_id == region_id)
            .order_by(ChronicleEventModel.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def get_by_type(session: AsyncSession, event_type: str, limit: int = 50) -> list:
        stmt = (
            select(ChronicleEventModel)
            .where(ChronicleEventModel.type == event_type)
            .order_by(ChronicleEventModel.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def cleanup_expired(session: AsyncSession) -> int:
        now = datetime.now(UTC)
        stmt = (
            select(ChronicleEventModel)
            .where(ChronicleEventModel.expires_at.isnot(None))
            .where(ChronicleEventModel.expires_at < now)
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        count = len(rows)
        for row in rows:
            await session.delete(row)
        await session.commit()
        return count
