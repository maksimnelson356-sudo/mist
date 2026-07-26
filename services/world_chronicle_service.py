import logging

from sqlalchemy import select, text

from database.base import get_db
from database.models.chronicle import ChronicleEventModel

logger = logging.getLogger("MIST.world_chronicle")


class WorldChronicleService:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def get_full_history(self, limit: int = 100, event_type: str = None) -> list:
        async for db in get_db():
            query = select(ChronicleEventModel).order_by(ChronicleEventModel.timestamp.desc())
            if event_type:
                query = query.where(ChronicleEventModel.event_type == event_type)
            query = query.limit(limit)
            result = await db.execute(query)
            return [{
                "id": e.id,
                "type": e.event_type,
                "message": e.message,
                "player_id": e.player_id,
                "importance": e.importance,
                "timestamp": e.timestamp,
                "metadata": e.metadata,
            } for e in result.scalars().all()]

    async def get_history_by_day(self, game_day: int) -> list:
        async for db in get_db():
            result = await db.execute(
                select(ChronicleEventModel)
                .order_by(ChronicleEventModel.timestamp.desc())
                .limit(50)
            )
            events = result.scalars().all()
            return [{
                "id": e.id,
                "type": e.event_type,
                "message": e.message,
                "importance": e.importance,
                "timestamp": e.timestamp,
            } for e in events]

    async def get_history_by_location(self, location_id: str, limit: int = 20) -> list:
        async for db in get_db():
            result = await db.execute(
                select(ChronicleEventModel)
                .order_by(ChronicleEventModel.timestamp.desc())
                .limit(200)
            )
            events = result.scalars().all()
            filtered = [
                {
                    "id": e.id,
                    "type": e.event_type,
                    "message": e.message,
                    "importance": e.importance,
                    "timestamp": e.timestamp,
                }
                for e in events
                if location_id in (e.message or "")
            ]
            return filtered[:limit]

    async def get_history_by_player(self, player_id: int, limit: int = 20) -> list:
        async for db in get_db():
            result = await db.execute(
                select(ChronicleEventModel)
                .where(ChronicleEventModel.player_id == player_id)
                .order_by(ChronicleEventModel.timestamp.desc())
                .limit(limit)
            )
            return [{
                "id": e.id,
                "type": e.event_type,
                "message": e.message,
                "importance": e.importance,
                "timestamp": e.timestamp,
            } for e in result.scalars().all()]

    async def get_era_summary(self) -> dict:
        async for db in get_db():
            total = (await db.execute(text("SELECT COUNT(*) FROM chronicle_events"))).scalar() or 0
            world_events = (await db.execute(
                text("SELECT COUNT(*) FROM chronicle_events WHERE event_type = 'WORLD_EVENT'")
            )).scalar() or 0
            player_events = (await db.execute(
                text("SELECT COUNT(*) FROM chronicle_events WHERE player_id IS NOT NULL")
            )).scalar() or 0
            combat_events = (await db.execute(
                text("SELECT COUNT(*) FROM chronicle_events WHERE event_type LIKE '%COMBAT%'")
            )).scalar() or 0

            return {
                "total_events": total,
                "world_events": world_events,
                "player_events": player_events,
                "combat_events": combat_events,
            }
