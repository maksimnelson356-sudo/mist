import json
from datetime import datetime
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.quest import (
    QuestModel, UserQuestModel, WorldEventModel, LegendModel
)


class QuestRepository:

    @staticmethod
    async def get(session: AsyncSession, quest_id: str) -> dict | None:
        stmt = select(QuestModel).where(QuestModel.quest_id == quest_id)
        result = await session.execute(stmt)
        row = result.scalars().first()
        return dict(row.__dict__) if row else None

    @staticmethod
    async def get_available(session: AsyncSession, user_id: int, location: str = None) -> list:
        if location:
            stmt = select(QuestModel).where(
                QuestModel.is_active == True,
                QuestModel.location == location,
            )
        else:
            stmt = select(QuestModel).where(QuestModel.is_active == True)
        result = await session.execute(stmt)
        quests = [dict(r.__dict__) for r in result.scalars().all()]

        active_stmt = select(UserQuestModel).where(
            UserQuestModel.user_id == user_id,
            UserQuestModel.status == "active",
        )
        active_result = await session.execute(active_stmt)
        active_ids = {r.quest_id for r in active_result.scalars().all()}

        completed_stmt = select(UserQuestModel).where(
            UserQuestModel.user_id == user_id,
            UserQuestModel.status == "completed",
        )
        completed_result = await session.execute(completed_stmt)
        completed_ids = {r.quest_id for r in completed_result.scalars().all()}

        out = []
        for q in quests:
            if q["quest_id"] in active_ids:
                continue
            if q["quest_id"] in completed_ids and not q["is_repeating"]:
                continue
            out.append(q)
        return out

    @staticmethod
    async def get_user_quests(session: AsyncSession, user_id: int) -> list:
        stmt = (
            select(UserQuestModel, QuestModel)
            .join(QuestModel, UserQuestModel.quest_id == QuestModel.quest_id)
            .where(UserQuestModel.user_id == user_id)
            .order_by(UserQuestModel.started_at.desc())
        )
        result = await session.execute(stmt)
        out = []
        for uq, q in result.all():
            d = dict(uq.__dict__)
            d["name"] = q.name
            d["description"] = q.description
            d["objectives"] = q.objectives
            d["rewards"] = q.rewards
            out.append(d)
        return out

    @staticmethod
    async def accept_quest(session: AsyncSession, user_id: int, quest_id: str, progress_json: str):
        import json
        uq = UserQuestModel(
            user_id=user_id,
            quest_id=quest_id,
            progress=progress_json,
        )
        session.add(uq)
        await session.commit()

    @staticmethod
    async def get_active_quest(session: AsyncSession, user_id: int, quest_id: str) -> dict | None:
        stmt = select(UserQuestModel).where(
            UserQuestModel.user_id == user_id,
            UserQuestModel.quest_id == quest_id,
            UserQuestModel.status == "active",
        )
        result = await session.execute(stmt)
        row = result.scalars().first()
        return dict(row.__dict__) if row else None

    @staticmethod
    async def update_progress(session: AsyncSession, user_id: int, quest_id: str, progress_json: str):
        stmt = update(UserQuestModel).where(
            UserQuestModel.user_id == user_id,
            UserQuestModel.quest_id == quest_id,
            UserQuestModel.status == "active",
        ).values(progress=progress_json)
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def complete_quest(session: AsyncSession, user_id: int, quest_id: str, progress_json: str):
        stmt = update(UserQuestModel).where(
            UserQuestModel.user_id == user_id,
            UserQuestModel.quest_id == quest_id,
            UserQuestModel.status == "active",
        ).values(status="completed", progress=progress_json, completed_at=datetime.utcnow())
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def delete_progress(session: AsyncSession, user_id: int, quest_id: str):
        from sqlalchemy import delete
        stmt = delete(UserQuestModel).where(
            UserQuestModel.user_id == user_id,
            UserQuestModel.quest_id == quest_id,
        )
        await session.execute(stmt)
        await session.commit()


class LegendRepository:

    @staticmethod
    async def discover(session: AsyncSession, legend_id: str, category: str,
                       name: str, description: str, user_id: int) -> bool:
        stmt = select(LegendModel).where(LegendModel.legend_id == legend_id)
        result = await session.execute(stmt)
        existing = result.scalars().first()
        if existing:
            existing.times_discovered += 1
            await session.commit()
            return False
        legend = LegendModel(
            legend_id=legend_id, category=category, name=name,
            description=description, discovered_by=user_id,
            discovered_at=datetime.utcnow(), times_discovered=1,
        )
        session.add(legend)
        await session.commit()
        return True

    @staticmethod
    async def get_stats(session: AsyncSession) -> dict:
        result = {}
        for cat in ("creature", "item", "location", "lore"):
            stmt = select(func.count()).select_from(LegendModel).where(
                LegendModel.category == cat
            )
            r = await session.execute(stmt)
            result[f"{cat}s_found"] = r.scalar() or 0
        return result
