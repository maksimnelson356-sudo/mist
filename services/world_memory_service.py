import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, text

from database.base import get_db
from database.models.world_memory import WorldMemoryModel

logger = logging.getLogger("MIST.world_memory")

MEMORY_TYPES = {
    "battle": {"permanent": False, "ttl_days": 10, "impact": 2},
    "discovery": {"permanent": True, "ttl_days": None, "impact": 3},
    "death": {"permanent": False, "ttl_days": 15, "impact": 2},
    "construction": {"permanent": True, "ttl_days": None, "impact": 3},
    "trade": {"permanent": False, "ttl_days": 5, "impact": 1},
    "quest_complete": {"permanent": False, "ttl_days": 7, "impact": 2},
    "npc_death": {"permanent": False, "ttl_days": 20, "impact": 2},
    "guild_action": {"permanent": True, "ttl_days": None, "impact": 3},
    "world_event": {"permanent": False, "ttl_days": 30, "impact": 2},
    "artifact_found": {"permanent": True, "ttl_days": None, "impact": 4},
    "player_death": {"permanent": False, "ttl_days": 10, "impact": 1},
    "home_built": {"permanent": True, "ttl_days": None, "impact": 3},
}


class WorldMemoryService:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def add_memory(self, memory_type: str, location_id: str, title: str,
                         description: str = None, player_id: int = None,
                         impact_level: int = None, extra_data: dict = None) -> dict:
        type_def = MEMORY_TYPES.get(memory_type, {"permanent": False, "ttl_days": 7, "impact": 1})

        expires_at = None
        if not type_def["permanent"] and type_def.get("ttl_days"):
            expires_at = datetime.now(UTC) + timedelta(days=type_def["ttl_days"])

        if impact_level is None:
            impact_level = type_def["impact"]

        async for db in get_db():
            memory = WorldMemoryModel(
                memory_type=memory_type,
                location_id=location_id,
                player_id=player_id,
                title=title,
                description=description,
                impact_level=impact_level,
                is_permanent=type_def["permanent"],
                expires_at=expires_at,
                extra_data=extra_data or {},
            )
            db.add(memory)
            await db.commit()

            logger.info(f"World Memory: {title} ({memory_type}) в {location_id}")
            return {
                "id": memory.id,
                "type": memory_type,
                "title": title,
                "permanent": type_def["permanent"],
            }

    async def get_memories_at_location(self, location_id: str, limit: int = 10) -> list:
        async for db in get_db():
            result = await db.execute(
                select(WorldMemoryModel)
                .where(WorldMemoryModel.location_id == location_id)
                .where(WorldMemoryModel.expires_at > datetime.now(UTC))
                .order_by(WorldMemoryModel.impact_level.desc())
                .limit(limit)
            )
            return [{
                "id": m.id,
                "type": m.memory_type,
                "title": m.title,
                "description": m.description,
                "impact": m.impact_level,
                "permanent": m.is_permanent,
                "player_id": m.player_id,
                "created_at": m.created_at,
            } for m in result.scalars().all()]

    async def get_player_memories(self, player_id: int, limit: int = 20) -> list:
        async for db in get_db():
            result = await db.execute(
                select(WorldMemoryModel)
                .where(WorldMemoryModel.player_id == player_id)
                .order_by(WorldMemoryModel.created_at.desc())
                .limit(limit)
            )
            return [{
                "id": m.id,
                "type": m.memory_type,
                "title": m.title,
                "location": m.location_id,
                "created_at": m.created_at,
            } for m in result.scalars().all()]

    async def get_global_memories(self, limit: int = 50) -> list:
        async for db in get_db():
            result = await db.execute(
                select(WorldMemoryModel)
                .where(WorldMemoryModel.expires_at > datetime.now(UTC))
                .order_by(WorldMemoryModel.created_at.desc())
                .limit(limit)
            )
            return [{
                "id": m.id,
                "type": m.memory_type,
                "title": m.title,
                "location": m.location_id,
                "impact": m.impact_level,
                "permanent": m.is_permanent,
                "created_at": m.created_at,
            } for m in result.scalars().all()]

    async def expire_old_memories(self):
        async for db in get_db():
            await db.execute(
                delete(WorldMemoryModel)
                .where(WorldMemoryModel.is_permanent == False)
                .where(WorldMemoryModel.expires_at < datetime.now(UTC))
            )
            await db.commit()

    async def get_memory_stats(self) -> dict:
        async for db in get_db():
            total = (await db.execute(text("SELECT COUNT(*) FROM world_memories"))).scalar() or 0
            permanent = (await db.execute(text("SELECT COUNT(*) FROM world_memories WHERE is_permanent = 1"))).scalar() or 0
            active = (await db.execute(
                text("SELECT COUNT(*) FROM world_memories WHERE expires_at > :now"),
                {"now": datetime.now(UTC)},
            )).scalar() or 0
            return {"total": total, "permanent": permanent, "active": active}
