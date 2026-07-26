from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.npc import NPCModel


class NPCRepository:

    @staticmethod
    async def get(session: AsyncSession, npc_id: str) -> dict | None:
        stmt = select(NPCModel).where(NPCModel.npc_id == npc_id)
        result = await session.execute(stmt)
        row = result.scalars().first()
        return dict(row.__dict__) if row else None

    @staticmethod
    async def get_by_uuid(session: AsyncSession, npc_uuid: str) -> dict | None:
        stmt = select(NPCModel).where(NPCModel.id == npc_uuid)
        result = await session.execute(stmt)
        row = result.scalars().first()
        return dict(row.__dict__) if row else None

    @staticmethod
    async def get_at_location(session: AsyncSession, location_str: str) -> list:
        stmt = select(NPCModel).where(
            NPCModel.location_str == location_str,
            NPCModel.is_alive == True,
        )
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def get_all(session: AsyncSession) -> list:
        stmt = select(NPCModel)
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def create(session: AsyncSession, **kwargs) -> dict:
        npc = NPCModel(**kwargs)
        session.add(npc)
        await session.commit()
        await session.refresh(npc)
        return dict(npc.__dict__)

    @staticmethod
    async def update_state(session: AsyncSession, npc_id: str, state: str):
        stmt = update(NPCModel).where(NPCModel.npc_id == npc_id).values(state=state)
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def update_location(session: AsyncSession, npc_id: str, location_str: str):
        stmt = update(NPCModel).where(NPCModel.npc_id == npc_id).values(location_str=location_str)
        await session.execute(stmt)
        await session.commit()
