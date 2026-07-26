from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.achievement import AchievementModel, UserAchievementModel


class AchievementRepository:

    @staticmethod
    async def get_all_definitions(session: AsyncSession) -> list:
        stmt = select(AchievementModel)
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def get_user_achievements(session: AsyncSession, user_id: int) -> list:
        stmt = select(UserAchievementModel).where(UserAchievementModel.user_id == user_id)
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def is_unlocked(session: AsyncSession, user_id: int, achievement_id: str) -> bool:
        stmt = select(UserAchievementModel).where(
            UserAchievementModel.user_id == user_id,
            UserAchievementModel.achievement_id == achievement_id,
        )
        result = await session.execute(stmt)
        return result.scalars().first() is not None

    @staticmethod
    async def unlock(session: AsyncSession, user_id: int, achievement_id: str):
        if not await AchievementRepository.is_unlocked(session, user_id, achievement_id):
            session.add(UserAchievementModel(
                user_id=user_id, achievement_id=achievement_id
            ))
            await session.commit()

    @staticmethod
    async def count_user_achievements(session: AsyncSession, user_id: int) -> int:
        stmt = select(func.count()).select_from(UserAchievementModel).where(
            UserAchievementModel.user_id == user_id
        )
        result = await session.execute(stmt)
        return result.scalar() or 0
