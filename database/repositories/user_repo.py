from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import UserModel


class UserRepository:

    @staticmethod
    async def get_or_create(session: AsyncSession, user_id: int, username: str = None) -> dict:
        stmt = select(UserModel).where(UserModel.user_id == user_id)
        result = await session.execute(stmt)
        row = result.scalars().first()
        if not row:
            display_name = username or f"Путник_{user_id % 10000}"
            user = UserModel(user_id=user_id, username=username, display_name=display_name)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return dict(user.__dict__)
        return dict(row.__dict__)

    @staticmethod
    async def get(session: AsyncSession, user_id: int) -> dict | None:
        stmt = select(UserModel).where(UserModel.user_id == user_id)
        result = await session.execute(stmt)
        row = result.scalars().first()
        return dict(row.__dict__) if row else None

    @staticmethod
    async def update(session: AsyncSession, user_id: int, **kwargs):
        stmt = update(UserModel).where(UserModel.user_id == user_id).values(**kwargs)
        await session.execute(stmt)
        await session.commit()
