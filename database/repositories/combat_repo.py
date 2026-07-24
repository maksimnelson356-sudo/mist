from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.combat import CombatLogModel, BossSpawnModel


class CombatRepository:

    @staticmethod
    async def log_combat(session: AsyncSession, user_id: int, creature_id: str,
                         result: str, dmg_dealt: int, dmg_taken: int,
                         xp_gained: int, loot: list):
        log = CombatLogModel(
            user_id=user_id, creature_id=creature_id, result=result,
            damage_dealt=dmg_dealt, damage_taken=dmg_taken,
            xp_gained=xp_gained, loot_dropped=str(loot),
        )
        session.add(log)
        await session.commit()

    @staticmethod
    async def get_combat_history(session: AsyncSession, user_id: int, limit: int = 10) -> list:
        stmt = (
            select(CombatLogModel)
            .where(CombatLogModel.user_id == user_id)
            .order_by(CombatLogModel.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def get_kill_count(session: AsyncSession, user_id: int) -> int:
        from sqlalchemy import func
        stmt = select(func.count()).select_from(CombatLogModel).where(
            CombatLogModel.user_id == user_id,
            CombatLogModel.result == "victory",
        )
        result = await session.execute(stmt)
        return result.scalar() or 0


class BossRepository:

    @staticmethod
    async def get_boss_spawn(session: AsyncSession, boss_id: str) -> dict | None:
        stmt = select(BossSpawnModel).where(BossSpawnModel.boss_id == boss_id)
        result = await session.execute(stmt)
        row = result.scalars().first()
        return dict(row.__dict__) if row else None

    @staticmethod
    async def record_kill(session: AsyncSession, boss_id: str, user_id: int):
        from datetime import datetime
        stmt = select(BossSpawnModel).where(BossSpawnModel.boss_id == boss_id)
        result = await session.execute(stmt)
        row = result.scalars().first()
        if row:
            row.last_killed_at = datetime.utcnow()
            row.killed_by = user_id
            await session.commit()
