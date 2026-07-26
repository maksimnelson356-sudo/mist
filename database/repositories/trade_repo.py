import json
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.trade import PlayerTradeModel


class TradeRepository:

    @staticmethod
    async def create(session: AsyncSession, from_user: int, to_user: int,
                     items_offered: list, gold_offered: int,
                     items_wanted: list, gold_wanted: int) -> int:
        trade = PlayerTradeModel(
            from_user=from_user, to_user=to_user,
            items_offered=json.dumps(items_offered),
            gold_offered=gold_offered,
            items_wanted=json.dumps(items_wanted),
            gold_wanted=gold_wanted,
        )
        session.add(trade)
        await session.commit()
        await session.refresh(trade)
        return trade.id

    @staticmethod
    async def get(session: AsyncSession, trade_id: int) -> dict | None:
        stmt = select(PlayerTradeModel).where(PlayerTradeModel.id == trade_id)
        result = await session.execute(stmt)
        row = result.scalars().first()
        return dict(row.__dict__) if row else None

    @staticmethod
    async def get_pending(session: AsyncSession, user_id: int) -> list:
        stmt = (
            select(PlayerTradeModel)
            .where(PlayerTradeModel.to_user == user_id, PlayerTradeModel.status == "pending")
            .order_by(PlayerTradeModel.created_at.desc())
        )
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def accept(session: AsyncSession, trade_id: int):
        stmt = update(PlayerTradeModel).where(
            PlayerTradeModel.id == trade_id
        ).values(status="completed", completed_at=datetime.utcnow())
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def decline(session: AsyncSession, trade_id: int):
        stmt = update(PlayerTradeModel).where(
            PlayerTradeModel.id == trade_id
        ).values(status="declined")
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def has_pending(session: AsyncSession, user_id: int) -> bool:
        stmt = select(PlayerTradeModel).where(
            PlayerTradeModel.from_user == user_id,
            PlayerTradeModel.status == "pending",
        )
        result = await session.execute(stmt)
        return result.scalars().first() is not None
