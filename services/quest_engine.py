import json
from datetime import datetime
from sqlalchemy import select, update

from database.base import get_db
from database.models.quest import QuestModel, UserQuestModel
from domain.events import EventType, Importance


QUEST_TYPES = {
    "kill": {"name": "Убить", "icon": "⚔️"},
    "collect": {"name": "Собрать", "icon": "🎒"},
    "explore": {"name": "Исследовать", "icon": "🗺️"},
    "talk": {"name": "Поговорить", "icon": "🗣️"},
    "deliver": {"name": "Доставить", "icon": "📦"},
    "craft": {"name": "Скрафти", "icon": "⚒️"},
}

QUEST_STATUS = {
    "active": "Активный",
    "completed": "Завершён",
    "failed": "Провален",
    "turned_in": "Сдан",
}


class QuestEngine:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def get_quest(self, quest_id: str) -> dict | None:
        async for db in get_db():
            stmt = select(QuestModel).where(QuestModel.quest_id == quest_id)
            result = await db.execute(stmt)
            quest = result.scalar_one_or_none()
            return self._to_dict(quest) if quest else None
        return None

    async def get_available_quests(self, location_id: str = None) -> list:
        async for db in get_db():
            stmt = select(QuestModel).where(QuestModel.is_active == True)
            if location_id:
                stmt = stmt.where(QuestModel.location == location_id)
            result = await db.execute(stmt)
            quests = result.scalars().all()
            return [self._to_dict(q) for q in quests]
        return []

    async def get_user_quests(self, user_id: int) -> list:
        async for db in get_db():
            stmt = select(UserQuestModel).where(
                UserQuestModel.user_id == user_id,
                UserQuestModel.status == "active",
            )
            result = await db.execute(stmt)
            user_quests = result.scalars().all()

            quests = []
            for uq in user_quests:
                quest = await self.get_quest(uq.quest_id)
                if quest:
                    quest["progress"] = json.loads(uq.progress) if isinstance(uq.progress, str) else uq.progress
                    quest["status"] = uq.status
                    quest["started_at"] = uq.started_at.isoformat() if uq.started_at else None
                    quests.append(quest)
            return quests
        return []

    async def accept_quest(self, user_id: int, quest_id: str) -> dict:
        quest = await self.get_quest(quest_id)
        if not quest:
            return {"success": False, "message": "Квест не найден."}

        async for db in get_db():
            stmt = select(UserQuestModel).where(
                UserQuestModel.user_id == user_id,
                UserQuestModel.quest_id == quest_id,
                UserQuestModel.status == "active",
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                return {"success": False, "message": "У тебя уже есть этот квест."}

            uq = UserQuestModel(
                user_id=user_id,
                quest_id=quest_id,
                status="active",
                progress=json.dumps({"current": 0, "target": quest.get("objectives", [{}])[0].get("target", 1)}),
            )
            db.add(uq)
            await db.commit()

            await self.chronicle.publish(
                EventType.QUEST_ACCEPTED,
                f"Квест принят: {quest['name']}",
                player_id=user_id,
                importance=Importance.COMMON,
            )

            return {
                "success": True,
                "message": f"Квест принят: {quest['name']}",
                "quest": quest,
            }
        return {"success": False, "message": "Ошибка базы данных."}

    async def update_progress(self, user_id: int, quest_id: str, action_type: str, amount: int = 1) -> dict:
        async for db in get_db():
            stmt = select(UserQuestModel).where(
                UserQuestModel.user_id == user_id,
                UserQuestModel.quest_id == quest_id,
                UserQuestModel.status == "active",
            )
            result = await db.execute(stmt)
            uq = result.scalar_one_or_none()

            if not uq:
                return {"success": False, "message": "Квест не найден у игрока."}

            progress = json.loads(uq.progress) if isinstance(uq.progress, str) else uq.progress
            quest = await self.get_quest(quest_id)
            if not quest:
                return {"success": False, "message": "Квест не найден."}

            objectives = quest.get("objectives", [])
            if objectives:
                obj = objectives[0]
                if obj.get("type") == action_type:
                    current = progress.get("current", 0) + amount
                    target = obj.get("target", 1)
                    progress["current"] = min(current, target)

            uq.progress = json.dumps(progress)
            await db.commit()

            if progress.get("current", 0) >= progress.get("target", 1):
                await self.complete_quest(user_id, quest_id)

            return {"success": True, "progress": progress}
        return {"success": False, "message": "Ошибка базы данных."}

    async def complete_quest(self, user_id: int, quest_id: str) -> dict:
        async for db in get_db():
            stmt = update(UserQuestModel).where(
                UserQuestModel.user_id == user_id,
                UserQuestModel.quest_id == quest_id,
            ).values(status="completed", completed_at=datetime.now())
            await db.execute(stmt)
            await db.commit()

            quest = await self.get_quest(quest_id)
            rewards = quest.get("rewards", {}) if quest else {}

            await self.chronicle.publish(
                EventType.QUEST_COMPLETED,
                f"Квест завершён: {quest['name'] if quest else quest_id}",
                player_id=user_id,
                importance=Importance.NOTABLE,
            )

            return {
                "success": True,
                "message": f"Квест завершён: {quest['name'] if quest else quest_id}",
                "rewards": rewards,
            }
        return {"success": False, "message": "Ошибка базы данных."}

    def get_quest_type_info(self, quest_type: str) -> dict:
        return QUEST_TYPES.get(quest_type, {"name": "Неизвестный", "icon": "❓"})

    def get_status_name(self, status: str) -> str:
        return QUEST_STATUS.get(status, "Неизвестный")

    @staticmethod
    def _to_dict(row: QuestModel) -> dict:
        return {
            "id": row.id,
            "quest_id": row.quest_id,
            "name": row.name,
            "description": row.description,
            "giver": row.giver,
            "location": row.location,
            "requirements": json.loads(row.requirements) if isinstance(row.requirements, str) else row.requirements,
            "objectives": json.loads(row.objectives) if isinstance(row.objectives, str) else row.objectives,
            "rewards": json.loads(row.rewards) if isinstance(row.rewards, str) else row.rewards,
            "is_active": row.is_active,
            "is_repeating": row.is_repeating,
            "cooldown_hours": row.cooldown_hours,
        }
