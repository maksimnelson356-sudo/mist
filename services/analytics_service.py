import json
from datetime import datetime

from sqlalchemy import func, select

from database.base import get_db
from database.models.analytics import AnalyticsEventModel


class AnalyticsService:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def track(self, event_type: str, user_id: int = None, data: dict = None) -> None:
        async for db in get_db():
            db.add(AnalyticsEventModel(
                event_type=event_type,
                user_id=user_id,
                data=json.dumps(data or {}),
            ))
            await db.commit()
            break

    async def get_count(self, event_type: str, since: datetime = None) -> int:
        async for db in get_db():
            stmt = select(func.count()).select_from(AnalyticsEventModel).where(
                AnalyticsEventModel.event_type == event_type
            )
            if since:
                stmt = stmt.where(AnalyticsEventModel.created_at >= since)
            result = await db.execute(stmt)
            return result.scalar() or 0
        return 0

    async def get_unique_players(self, since: datetime = None) -> int:
        async for db in get_db():
            stmt = select(func.count(func.distinct(AnalyticsEventModel.user_id))).select_from(
                AnalyticsEventModel
            )
            if since:
                stmt = stmt.where(AnalyticsEventModel.created_at >= since)
            result = await db.execute(stmt)
            return result.scalar() or 0
        return 0

    async def get_top_events(self, limit: int = 10) -> list:
        async for db in get_db():
            stmt = (
                select(AnalyticsEventModel.event_type, func.count().label("cnt"))
                .group_by(AnalyticsEventModel.event_type)
                .order_by(func.count().desc())
                .limit(limit)
            )
            result = await db.execute(stmt)
            return [{"event_type": row[0], "count": row[1]} for row in result.all()]
        return []
