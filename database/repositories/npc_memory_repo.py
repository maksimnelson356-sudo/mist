from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.npc_memory import NPCMemoryModel


class NPCMemoryRepository:

    @staticmethod
    async def get(session: AsyncSession, npc_id: str, player_id: int) -> dict | None:
        stmt = select(NPCMemoryModel).where(
            NPCMemoryModel.npc_id == npc_id,
            NPCMemoryModel.player_id == player_id,
        )
        result = await session.execute(stmt)
        row = result.scalars().first()
        return dict(row.__dict__) if row else None

    @staticmethod
    async def get_all_for_npc(session: AsyncSession, npc_id: str) -> list:
        stmt = select(NPCMemoryModel).where(NPCMemoryModel.npc_id == npc_id)
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def get_all_for_player(session: AsyncSession, player_id: int) -> list:
        stmt = select(NPCMemoryModel).where(NPCMemoryModel.player_id == player_id)
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def create_or_update(session: AsyncSession, npc_id: str, player_id: int, action: str, delta: int = 0) -> dict:
        stmt = select(NPCMemoryModel).where(
            NPCMemoryModel.npc_id == npc_id,
            NPCMemoryModel.player_id == player_id,
        )
        result = await session.execute(stmt)
        row = result.scalars().first()

        if row:
            new_relation = max(-100, min(100, row.relation + delta))
            row.interaction_count += 1
            row.last_seen = datetime.now()
            row.last_action = action
            row.relation = new_relation
            await session.commit()
            await session.refresh(row)
            return dict(row.__dict__)
        else:
            mem = NPCMemoryModel(
                npc_id=npc_id,
                player_id=player_id,
                relation=delta,
                interaction_count=1,
                last_action=action,
            )
            session.add(mem)
            await session.commit()
            await session.refresh(mem)
            return dict(mem.__dict__)

    @staticmethod
    async def modify_relation(session: AsyncSession, npc_id: str, player_id: int, delta: int) -> dict:
        stmt = select(NPCMemoryModel).where(
            NPCMemoryModel.npc_id == npc_id,
            NPCMemoryModel.player_id == player_id,
        )
        result = await session.execute(stmt)
        row = result.scalars().first()

        if row:
            row.relation = max(-100, min(100, row.relation + delta))
            await session.commit()
            await session.refresh(row)
            return dict(row.__dict__)
        else:
            return await NPCMemoryRepository.create_or_update(
                session, npc_id, player_id, "unknown", delta
            )
