from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.exploration import ExplorationModel


class ExplorationRepository:

    @staticmethod
    async def get(session: AsyncSession, user_id: int, location_id: str) -> dict | None:
        stmt = select(ExplorationModel).where(
            ExplorationModel.user_id == user_id,
            ExplorationModel.location_id == location_id,
        )
        result = await session.execute(stmt)
        row = result.scalars().first()
        return dict(row.__dict__) if row else None

    @staticmethod
    async def get_discoveries(session: AsyncSession, user_id: int) -> list:
        stmt = select(ExplorationModel).where(
            ExplorationModel.user_id == user_id,
            ExplorationModel.first_discovered == True,
        )
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def get_all_visited(session: AsyncSession, user_id: int) -> list:
        stmt = select(ExplorationModel).where(ExplorationModel.user_id == user_id)
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def discover(session: AsyncSession, user_id: int, location_id: str) -> dict:
        stmt = select(ExplorationModel).where(
            ExplorationModel.user_id == user_id,
            ExplorationModel.location_id == location_id,
        )
        result = await session.execute(stmt)
        row = result.scalars().first()

        if row:
            row.visited_count += 1
            row.last_visited = datetime.now()
            await session.commit()
            await session.refresh(row)
            return dict(row.__dict__)
        else:
            exp = ExplorationModel(
                user_id=user_id,
                location_id=location_id,
                first_discovered=True,
                visited_count=1,
                discovered_at=datetime.now(),
            )
            session.add(exp)
            await session.commit()
            await session.refresh(exp)
            return dict(exp.__dict__)

    @staticmethod
    async def visit(session: AsyncSession, user_id: int, location_id: str) -> dict:
        stmt = select(ExplorationModel).where(
            ExplorationModel.user_id == user_id,
            ExplorationModel.location_id == location_id,
        )
        result = await session.execute(stmt)
        row = result.scalars().first()

        if row:
            row.visited_count += 1
            row.last_visited = datetime.now()
            await session.commit()
            await session.refresh(row)
            return dict(row.__dict__)
        else:
            return await ExplorationRepository.discover(session, user_id, location_id)

    @staticmethod
    async def count_discoveries(session: AsyncSession, user_id: int) -> int:
        stmt = select(func.count()).select_from(ExplorationModel).where(
            ExplorationModel.user_id == user_id,
            ExplorationModel.first_discovered == True,
        )
        result = await session.execute(stmt)
        return result.scalar() or 0

    @staticmethod
    async def count_total_visits(session: AsyncSession, user_id: int) -> int:
        stmt = select(func.sum(ExplorationModel.visited_count)).where(
            ExplorationModel.user_id == user_id,
        )
        result = await session.execute(stmt)
        return result.scalar() or 0
