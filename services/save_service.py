from datetime import datetime

from sqlalchemy import select

from database.base import get_db
from database.models.chronicle import ChronicleEventModel
from database.models.user import UserModel


class SaveService:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def get_world_stats(self) -> dict:
        async for db in get_db():
            from sqlalchemy import func as sa_func

            player_count = (await db.execute(
                select(sa_func.count()).select_from(UserModel)
            )).scalar() or 0

            alive_count = (await db.execute(
                select(sa_func.count()).select_from(UserModel).where(UserModel.is_alive == True)
            )).scalar() or 0

            avg_level = (await db.execute(
                select(sa_func.avg(UserModel.level))
            )).scalar() or 0

            total_gold = (await db.execute(
                select(sa_func.sum(UserModel.gold))
            )).scalar() or 0

            event_count = (await db.execute(
                select(sa_func.count()).select_from(ChronicleEventModel)
            )).scalar() or 0

            return {
                "player_count": player_count,
                "alive_count": alive_count,
                "avg_level": round(avg_level, 1),
                "total_gold": total_gold,
                "event_count": event_count,
                "timestamp": datetime.utcnow().isoformat(),
            }
        return {}
