import json
import random
from datetime import datetime

from sqlalchemy import select, update

from database.base import get_db
from database.models.daily import DailyQuestModel
from database.models.user import UserModel
from domain.events import EventType, Importance


DAILY_QUEST_POOL = [
    {"quest_id": "daily_kill_3", "name": "Охота дня", "description": "Убей 3 существ", "objective": {"type": "kill_count", "target": 3}, "reward_xp": 50, "reward_gold": 20},
    {"quest_id": "daily_collect_5", "name": "Сбор дня", "description": "Подбери 5 предметов", "objective": {"type": "pickup_count", "target": 5}, "reward_xp": 30, "reward_gold": 15},
    {"quest_id": "daily_visit_3", "name": "Странник дня", "description": "Посети 3 локации", "objective": {"type": "visit_count", "target": 3}, "reward_xp": 40, "reward_gold": 10},
    {"quest_id": "daily_craft_1", "name": "Ремесло дня", "description": "Скрафти 1 предмет", "objective": {"type": "craft_count", "target": 1}, "reward_xp": 40, "reward_gold": 25},
    {"quest_id": "daily_kill_5", "name": "Расправа дня", "description": "Убей 5 существ", "objective": {"type": "kill_count", "target": 5}, "reward_xp": 80, "reward_gold": 40},
]


class DailyService:

    def __init__(self, chronicle, user_service):
        self.chronicle = chronicle
        self.user_service = user_service

    async def get_or_create(self, user_id: int) -> list:
        today = datetime.utcnow().strftime("%Y-%m-%d")

        async for db in get_db():
            stmt = select(DailyQuestModel).where(
                DailyQuestModel.user_id == user_id,
                DailyQuestModel.day == today,
            )
            result = await db.execute(stmt)
            existing = result.scalars().all()

            if existing:
                return [self._daily_to_dict(r) for r in existing]

            pool = random.sample(DAILY_QUEST_POOL, min(3, len(DAILY_QUEST_POOL)))
            quests = []
            for q in pool:
                dq = DailyQuestModel(
                    user_id=user_id,
                    quest_id=q["quest_id"],
                    day=today,
                    progress=json.dumps({"current": 0, "target": q["objective"]["target"]}),
                )
                db.add(dq)
                quests.append({
                    "user_id": user_id,
                    "quest_id": q["quest_id"],
                    "day": today,
                    "status": "active",
                    "progress": {"current": 0, "target": q["objective"]["target"]},
                    "name": q["name"],
                    "description": q["description"],
                    "objective": q["objective"],
                    "reward_xp": q["reward_xp"],
                    "reward_gold": q["reward_gold"],
                })
            await db.commit()
            return quests
        return []

    async def update_progress(self, user_id: int, progress_type: str, amount: int = 1) -> list:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        completed = []

        async for db in get_db():
            stmt = select(DailyQuestModel).where(
                DailyQuestModel.user_id == user_id,
                DailyQuestModel.day == today,
                DailyQuestModel.status == "active",
            )
            result = await db.execute(stmt)
            rows = result.scalars().all()

            for row in rows:
                progress = json.loads(row.progress) if isinstance(row.progress, str) else row.progress
                daily_q = next((q for q in DAILY_QUEST_POOL if q["quest_id"] == row.quest_id), None)
                if not daily_q:
                    continue
                if daily_q["objective"]["type"] == progress_type:
                    progress["current"] = min(progress["current"] + amount, progress["target"])
                    if progress["current"] >= progress["target"]:
                        row.status = "completed"
                        row.progress = json.dumps(progress)
                        row.completed_at = datetime.utcnow()

                        user = await self.user_service.get(user_id)
                        await db.execute(
                            update(UserModel).where(UserModel.user_id == user_id).values(
                                xp=user["xp"] + daily_q["reward_xp"],
                                gold=user["gold"] + daily_q["reward_gold"],
                            )
                        )
                        completed.append(daily_q)

                        await self.chronicle.publish(
                            EventType.DAILY_COMPLETED,
                            f"Ежедневный квест: {daily_q['name']}",
                            player_id=user_id,
                            importance=Importance.COMMON,
                            metadata={"quest_id": daily_q["quest_id"]},
                        )
                    else:
                        row.progress = json.dumps(progress)

            await db.commit()
            break

        return completed

    @staticmethod
    def _daily_to_dict(row: DailyQuestModel) -> dict:
        progress = json.loads(row.progress) if isinstance(row.progress, str) else row.progress
        daily_q = next((q for q in DAILY_QUEST_POOL if q["quest_id"] == row.quest_id), None)
        return {
            "user_id": row.user_id,
            "quest_id": row.quest_id,
            "day": row.day,
            "status": row.status,
            "progress": progress,
            "completed_at": row.completed_at,
            "name": daily_q["name"] if daily_q else row.quest_id,
            "description": daily_q["description"] if daily_q else "",
            "objective": daily_q["objective"] if daily_q else {},
            "reward_xp": daily_q["reward_xp"] if daily_q else 0,
            "reward_gold": daily_q["reward_gold"] if daily_q else 0,
        }
