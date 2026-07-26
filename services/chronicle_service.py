import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from database.base import get_db
from database.models.chronicle import ChronicleEventModel
from domain.events import EventType, Importance


class ChronicleService:

    async def publish(
        self,
        event_type: EventType,
        title: str,
        *,
        description: str | None = None,
        player_id: int | None = None,
        region_id: str | None = None,
        importance: Importance = Importance.COMMON,
        expires_at: datetime | None = None,
        metadata: dict | None = None,
    ) -> str:
        event_id = str(uuid.uuid4())
        async for db in get_db():
            event = ChronicleEventModel(
                id=event_id,
                type=event_type.value,
                importance=importance.value,
                title=title,
                description=description,
                player_id=player_id,
                region_id=region_id,
                created_at=datetime.now(UTC),
                expires_at=expires_at,
                metadata_=metadata or {},
            )
            db.add(event)
            await db.commit()
            break
        return event_id

    async def get_latest(self, limit: int = 20) -> list:
        async for db in get_db():
            stmt = (
                select(ChronicleEventModel)
                .order_by(ChronicleEventModel.created_at.desc())
                .limit(limit)
            )
            result = await db.execute(stmt)
            rows = result.scalars().all()
            return [self._to_dict(r) for r in rows]
        return []

    async def get_by_player(self, player_id: int, limit: int = 50) -> list:
        async for db in get_db():
            stmt = (
                select(ChronicleEventModel)
                .where(ChronicleEventModel.player_id == player_id)
                .order_by(ChronicleEventModel.created_at.desc())
                .limit(limit)
            )
            result = await db.execute(stmt)
            rows = result.scalars().all()
            return [self._to_dict(r) for r in rows]
        return []

    async def get_by_region(self, region_id: str, limit: int = 50) -> list:
        async for db in get_db():
            stmt = (
                select(ChronicleEventModel)
                .where(ChronicleEventModel.region_id == region_id)
                .order_by(ChronicleEventModel.created_at.desc())
                .limit(limit)
            )
            result = await db.execute(stmt)
            rows = result.scalars().all()
            return [self._to_dict(r) for r in rows]
        return []

    async def get_by_type(self, event_type: EventType, limit: int = 50) -> list:
        async for db in get_db():
            stmt = (
                select(ChronicleEventModel)
                .where(ChronicleEventModel.type == event_type.value)
                .order_by(ChronicleEventModel.created_at.desc())
                .limit(limit)
            )
            result = await db.execute(stmt)
            rows = result.scalars().all()
            return [self._to_dict(r) for r in rows]
        return []

    async def cleanup_expired(self) -> int:
        now = datetime.now(UTC)
        deleted = 0
        async for db in get_db():
            stmt = select(ChronicleEventModel).where(
                ChronicleEventModel.expires_at != None,
                ChronicleEventModel.expires_at <= now,
            )
            result = await db.execute(stmt)
            expired = result.scalars().all()
            for ev in expired:
                await db.delete(ev)
                deleted += 1
            await db.commit()
            break
        return deleted

    @staticmethod
    def _to_dict(row: ChronicleEventModel) -> dict:
        return {
            "id": row.id,
            "type": row.type,
            "importance": row.importance,
            "title": row.title,
            "description": row.description,
            "player_id": row.player_id,
            "region_id": row.region_id,
            "created_at": row.created_at,
            "expires_at": row.expires_at,
            "metadata": row.metadata_ or {},
        }
