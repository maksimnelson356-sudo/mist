import json
import random
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.creature import CreatureModel


class CreatureRepository:

    @staticmethod
    async def get(session: AsyncSession, creature_id: str) -> dict | None:
        stmt = select(CreatureModel).where(CreatureModel.creature_id == creature_id)
        result = await session.execute(stmt)
        row = result.scalars().first()
        return dict(row.__dict__) if row else None

    @staticmethod
    async def get_alive_at_location(session: AsyncSession, location_id: str) -> list:
        stmt = select(CreatureModel).where(
            CreatureModel.location == location_id,
            CreatureModel.is_alive == True,
        )
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def get_at_location(session: AsyncSession, location_id: str) -> list:
        stmt = select(CreatureModel).where(CreatureModel.location == location_id)
        result = await session.execute(stmt)
        rows = [dict(r.__dict__) for r in result.scalars().all()]

        alive = [r for r in rows if r["is_alive"]]
        if not alive:
            dead = [r for r in rows if not r["is_alive"]]
            for d in dead:
                if random.random() < 0.4:
                    await CreatureRepository.respawn(session, d["creature_id"])
            stmt2 = select(CreatureModel).where(
                CreatureModel.location == location_id,
                CreatureModel.is_alive == True,
            )
            result2 = await session.execute(stmt2)
            return [dict(r.__dict__) for r in result2.scalars().all()]
        return rows

    @staticmethod
    async def kill(session: AsyncSession, creature_id: str):
        stmt = update(CreatureModel).where(
            CreatureModel.creature_id == creature_id
        ).values(is_alive=False)
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def respawn(session: AsyncSession, creature_id: str):
        creature = await CreatureRepository.get(session, creature_id)
        if not creature:
            return
        stmt = update(CreatureModel).where(
            CreatureModel.creature_id == creature_id
        ).values(is_alive=True, hp=creature["max_hp"])
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def update_hp(session: AsyncSession, creature_id: str, hp: int):
        stmt = update(CreatureModel).where(
            CreatureModel.creature_id == creature_id
        ).values(hp=hp)
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def update_memory(session: AsyncSession, creature_id: str, user_id: int, action: str):
        creature = await CreatureRepository.get(session, creature_id)
        if not creature:
            return
        memory_raw = creature.get("memory_with_users", "{}")
        memory = json.loads(memory_raw) if isinstance(memory_raw, str) else memory_raw
        uid_str = str(user_id)
        if uid_str not in memory:
            memory[uid_str] = []
        memory[uid_str].append({"action": action, "time": datetime.now().isoformat()})
        stmt = update(CreatureModel).where(
            CreatureModel.creature_id == creature_id
        ).values(memory_with_users=json.dumps(memory))
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def get_memory(session: AsyncSession, creature_id: str, user_id: int) -> list:
        creature = await CreatureRepository.get(session, creature_id)
        if not creature:
            return []
        memory_raw = creature.get("memory_with_users", "{}")
        memory = json.loads(memory_raw) if isinstance(memory_raw, str) else memory_raw
        return memory.get(str(user_id), [])
