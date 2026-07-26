import json
from datetime import datetime

from sqlalchemy import select, update

from database.base import get_db
from database.models.inventory import InventoryModel
from database.models.quest import QuestModel, UserQuestModel
from database.models.user import UserModel
from domain.events import EventType, Importance

CLASS_QUESTS = {
    "warrior": [
        {"quest_id": "warrior_trial", "name": "Испытание воина", "description": "Победи 5 врагов в ближнем бою.", "location": "dark_forest", "objectives": [{"id": "kill_5", "type": "kill", "target": 5, "description": "Убить 5 врагов"}], "reward_xp": 100, "reward_gold": 50},
        {"quest_id": "warrior_boss", "name": "Большой бой", "description": "Победи любого босса.", "location": "any", "objectives": [{"id": "kill_boss", "type": "kill_boss", "target": 1, "description": "Убить босса"}], "reward_xp": 300, "reward_gold": 200},
    ],
    "mage": [
        {"quest_id": "mage_arcane", "name": "Арканы магии", "description": "Найди 3 артефакта.", "location": "any", "objectives": [{"id": "find_3", "type": "find_artifact", "target": 3, "description": "Найти 3 артефакта"}], "reward_xp": 150, "reward_gold": 100},
        {"quest_id": "mage_lib", "name": "Библиотека эхов", "description": "Посети Библиотеку эхов.", "location": "library_of_echoes", "objectives": [{"id": "visit_lib", "type": "visit", "location": "library_of_echoes", "target": 1, "description": "Посетить Библиотеку эхов"}], "reward_xp": 100, "reward_gold": 75},
    ],
    "scout": [
        {"quest_id": "scout_explore", "name": "Первооткрыватель", "description": "Открой 5 новых локаций.", "location": "any", "objectives": [{"id": "explore_5", "type": "discover", "target": 5, "description": "Открыть 5 локаций"}], "reward_xp": 120, "reward_gold": 80},
        {"quest_id": "scout_night", "name": "Ночной странник", "description": "Выживи в ночном путешествии.", "location": "any", "objectives": [{"id": "survive_night", "type": "survive_night", "target": 1, "description": "Выжить ночью"}], "reward_xp": 100, "reward_gold": 60},
    ],
    "craftsman": [
        {"quest_id": "craft_master", "name": "Мастер ремесла", "description": "Скрафти 5 предметов.", "location": "any", "objectives": [{"id": "craft_5", "type": "craft", "target": 5, "description": "Скрафти 5 предметов"}], "reward_xp": 100, "reward_gold": 120},
        {"quest_id": "craft_gather", "name": "Сбор ресурсов", "description": "Собери 10 ресурсов.", "location": "any", "objectives": [{"id": "gather_10", "type": "collect", "target": 10, "description": "Собрать 10 ресурсов"}], "reward_xp": 80, "reward_gold": 100},
    ],
}


class QuestService:

    def __init__(self, chronicle, user_service):
        self.chronicle = chronicle
        self.user_service = user_service

    async def get_available(self, user_id: int, location: str = None) -> list:
        async for db in get_db():
            stmt = select(QuestModel).where(QuestModel.is_active == True)
            if location:
                stmt = stmt.where(QuestModel.location == location)

            result = await db.execute(stmt)
            all_quests = result.scalars().all()

            stmt_active = select(UserQuestModel.quest_id).where(
                UserQuestModel.user_id == user_id,
                UserQuestModel.status == "active",
            )
            result_active = await db.execute(stmt_active)
            active_ids = {r.quest_id for r in result_active.all()}

            stmt_completed = select(UserQuestModel.quest_id).where(
                UserQuestModel.user_id == user_id,
                UserQuestModel.status == "completed",
            )
            result_completed = await db.execute(stmt_completed)
            completed_ids = {r.quest_id for r in result_completed.all()}

            available = []
            for q in all_quests:
                if q.quest_id in active_ids:
                    continue
                if q.quest_id in completed_ids and not q.is_repeating:
                    continue
                available.append(self._quest_to_dict(q))
            return available
        return []

    async def get_class_quests(self, user_id: int) -> list:
        user = await self.user_service.get(user_id)
        if not user:
            return []

        player_class = user.get("player_class", "warrior")
        quests = CLASS_QUESTS.get(player_class, [])

        async for db in get_db():
            stmt_active = select(UserQuestModel.quest_id).where(
                UserQuestModel.user_id == user_id,
                UserQuestModel.status == "active",
            )
            result_active = await db.execute(stmt_active)
            active_ids = {r.quest_id for r in result_active.all()}

            stmt_completed = select(UserQuestModel.quest_id).where(
                UserQuestModel.user_id == user_id,
                UserQuestModel.status == "completed",
            )
            result_completed = await db.execute(stmt_completed)
            completed_ids = {r.quest_id for r in result_completed.all()}

            available = []
            for q in quests:
                if q["quest_id"] in active_ids:
                    continue
                if q["quest_id"] in completed_ids:
                    continue
                available.append(q)
            return available
        return []

    async def accept(self, user_id: int, quest_id: str) -> dict:
        async for db in get_db():
            stmt = select(QuestModel).where(
                QuestModel.quest_id == quest_id,
                QuestModel.is_active == True,
            )
            result = await db.execute(stmt)
            quest = result.scalar_one_or_none()

            if not quest:
                return {"success": False, "message": "Квест не найден."}

            user = await self.user_service.get(user_id)
            if not user:
                return {"success": False, "message": "Пользователь не найден."}
            if quest.location and quest.location != user["current_location"]:
                return {"success": False, "message": "Ты не в той локации для этого квеста."}

            stmt_check = select(UserQuestModel).where(
                UserQuestModel.user_id == user_id,
                UserQuestModel.quest_id == quest_id,
                UserQuestModel.status == "active",
            )
            result_check = await db.execute(stmt_check)
            if result_check.scalar_one_or_none():
                return {"success": False, "message": "Ты уже выполняешь этот квест."}

            stmt_done = select(UserQuestModel).where(
                UserQuestModel.user_id == user_id,
                UserQuestModel.quest_id == quest_id,
                UserQuestModel.status == "completed",
            )
            result_done = await db.execute(stmt_done)
            completed = result_done.scalar_one_or_none()
            if completed:
                if not quest.is_repeating:
                    return {"success": False, "message": "Ты уже выполнил этот квест."}
                await db.delete(completed)
                await db.commit()

            objectives = json.loads(quest.objectives) if isinstance(quest.objectives, str) else quest.objectives
            progress = {}
            for obj in objectives:
                progress[obj["id"]] = {"current": 0, "target": obj["target"]}

            db.add(UserQuestModel(
                user_id=user_id,
                quest_id=quest_id,
                progress=json.dumps(progress),
            ))
            await db.commit()

            await self.chronicle.publish(
                EventType.QUEST_ACCEPTED,
                f"Квест принят: {quest.name}",
                player_id=user_id,
                region_id=quest.location,
                importance=Importance.COMMON,
            )

            return {"success": True, "quest": self._quest_to_dict(quest), "message": f"📜 Квест принят: <b>{quest.name}</b>"}
        return {"success": False, "message": "Ошибка базы данных."}

    async def update_progress(self, user_id: int, quest_id: str, objective_id: str, amount: int = 1) -> dict:
        async for db in get_db():
            stmt = (
                select(UserQuestModel, QuestModel)
                .join(QuestModel, UserQuestModel.quest_id == QuestModel.quest_id)
                .where(
                    UserQuestModel.user_id == user_id,
                    UserQuestModel.quest_id == quest_id,
                    UserQuestModel.status == "active",
                )
            )
            result = await db.execute(stmt)
            row = result.first()
            if not row:
                return {"success": False}

            uq, quest = row
            progress = json.loads(uq.progress) if isinstance(uq.progress, str) else uq.progress
            if objective_id not in progress:
                return {"success": False}

            progress[objective_id]["current"] = min(
                progress[objective_id]["current"] + amount,
                progress[objective_id]["target"],
            )

            all_done = all(p["current"] >= p["target"] for p in progress.values())

            if all_done:
                rewards = json.loads(quest.rewards) if isinstance(quest.rewards, str) else quest.rewards
                leveled = False
                new_level = None

                if "xp" in rewards:
                    user = await self.user_service.get(user_id)
                    new_xp = user["xp"] + rewards["xp"]
                    new_level = user["level"]
                    xp_needed = new_level * 100
                    while new_xp >= xp_needed:
                        new_level += 1
                        new_xp -= xp_needed
                        xp_needed = new_level * 100
                        leveled = True
                    if leveled:
                        await self._apply_level_up(user_id, new_level, db)
                    await db.execute(
                        update(UserModel).where(UserModel.user_id == user_id).values(xp=new_xp, level=new_level)
                    )

                if "memories" in rewards:
                    user = await self.user_service.get(user_id)
                    await db.execute(
                        update(UserModel).where(UserModel.user_id == user_id).values(memories=user["memories"] + rewards["memories"])
                    )

                if "karma" in rewards:
                    user = await self.user_service.get(user_id)
                    await db.execute(
                        update(UserModel).where(UserModel.user_id == user_id).values(karma=user["karma"] + rewards["karma"])
                    )

                if "items" in rewards:
                    for item in rewards["items"]:
                        await self._add_item(user_id, item["id"], item.get("qty", 1), db)

                if "gold" in rewards:
                    user = await self.user_service.get(user_id)
                    await db.execute(
                        update(UserModel).where(UserModel.user_id == user_id).values(gold=user["gold"] + rewards["gold"])
                    )

                uq.status = "completed"
                uq.progress = json.dumps(progress)
                uq.completed_at = datetime.utcnow()
                await db.commit()

                await self.chronicle.publish(
                    EventType.QUEST_COMPLETED,
                    f"Квест выполнен: {quest.name}",
                    player_id=user_id,
                    importance=Importance.NOTABLE,
                    metadata={"quest_id": quest_id, "rewards": rewards},
                )

                from services.container import services
                await services.analytics.track(
                    "quest_completed",
                    user_id=user_id,
                    data={"quest_id": quest_id, "rewards": rewards},
                )

                msg = "🏆 <b>Квест выполнен</b>\n\n"
                msg += f"📜 <b>{quest.name}</b>!"
                if "xp" in rewards:
                    msg += f"\n\n+{rewards['xp']} XP"
                if leveled:
                    msg += f"\n\n⭐ УРОВЕНЬ ПОВЫШЕН → {new_level}!"
                return {"success": True, "completed": True, "rewards": rewards, "message": msg}
            else:
                uq.progress = json.dumps(progress)
                await db.commit()
                return {"success": True, "completed": False}
        return {"success": False, "message": "Ошибка базы данных."}

    async def complete(self, user_id: int, quest_id: str) -> dict:
        async for db in get_db():
            stmt = select(UserQuestModel).where(
                UserQuestModel.user_id == user_id,
                UserQuestModel.quest_id == quest_id,
                UserQuestModel.status == "active",
            )
            result = await db.execute(stmt)
            uq = result.scalar_one_or_none()
            if not uq:
                return {"success": False, "message": "Квест не найден или уже завершён."}

            q_stmt = select(QuestModel).where(QuestModel.quest_id == quest_id)
            q_result = await db.execute(q_stmt)
            quest = q_result.scalar_one_or_none()
            if not quest:
                return {"success": False, "message": "Реализация квеста не найдена."}

            progress = json.loads(uq.progress) if isinstance(uq.progress, str) else uq.progress
            objectives = json.loads(quest.objectives) if isinstance(quest.objectives, str) else quest.objectives

            all_done = all(
                progress.get(obj["id"], {}).get("current", 0) >= obj["target"]
                for obj in objectives
            )
            if not all_done:
                return {"success": False, "message": "Цели ещё не выполнены."}

            rewards = json.loads(quest.rewards) if isinstance(quest.rewards, str) else quest.rewards
            user_stmt = select(UserModel).where(UserModel.user_id == user_id)
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            if not user:
                return {"success": False, "message": "Игрок не найден."}

            new_xp = user.xp + rewards.get("xp", 0)
            new_gold = user.gold + rewards.get("gold", 0)
            new_level = user.level
            leveled = False
            while new_xp >= new_level * 100:
                new_level += 1
                new_xp -= (new_level - 1) * 100
                leveled = True
            if leveled:
                new_max_hp = 100 + (new_level - 1) * 15
                new_attack = 10 + (new_level - 1) * 3
                new_defense = 5 + (new_level - 1) * 2
                await db.execute(
                    update(UserModel).where(UserModel.user_id == user_id).values(
                        level=new_level, max_hp=new_max_hp, attack=new_attack, defense=new_defense,
                    )
                )
            await db.execute(
                update(UserModel).where(UserModel.user_id == user_id).values(xp=new_xp, gold=new_gold)
            )

            for item_reward in rewards.get("items", []):
                await self._add_item(user_id, item_reward["item_id"], item_reward.get("qty", 1), db)

            uq.status = "completed"
            uq.completed_at = datetime.utcnow()
            await db.commit()

            from services.container import services
            await services.analytics.track(
                "quest_completed",
                user_id=user_id,
                data={"quest_id": quest_id, "rewards": rewards},
            )

            msg = "🏆 <b>Квест выполнен</b>\n\n"
            msg += f"📜 <b>{quest.name}</b>!"
            if "xp" in rewards:
                msg += f"\n\n+{rewards['xp']} XP"
            if leveled:
                msg += f"\n\n⭐ УРОВЕНЬ ПОВЫШЕН → {new_level}!"
            return {"success": True, "completed": True, "rewards": rewards, "message": msg}
        return {"success": False, "message": "Ошибка базы данных."}

    async def get_user_quests(self, user_id: int) -> list:
        async for db in get_db():
            stmt = (
                select(UserQuestModel, QuestModel)
                .join(QuestModel, UserQuestModel.quest_id == QuestModel.quest_id)
                .where(UserQuestModel.user_id == user_id)
                .order_by(UserQuestModel.started_at.desc())
            )
            result = await db.execute(stmt)
            rows = result.all()
            quests = []
            for uq, q in rows:
                quests.append({
                    "user_id": uq.user_id,
                    "quest_id": uq.quest_id,
                    "status": uq.status,
                    "progress": json.loads(uq.progress) if isinstance(uq.progress, str) else uq.progress,
                    "started_at": uq.started_at,
                    "completed_at": uq.completed_at,
                    "name": q.name,
                    "description": q.description,
                    "location": q.location,
                    "objectives": json.loads(q.objectives) if isinstance(q.objectives, str) else q.objectives,
                    "rewards": json.loads(q.rewards) if isinstance(q.rewards, str) else q.rewards,
                })
            return quests
        return []

    async def discover_legend(self, legend_id: str, legend_type: str, name: str, description: str, player_id: int) -> dict:
        async for db in get_db():
            from sqlalchemy import select as sel

            from database.models.quest import LegendModel
            stmt = sel(LegendModel).where(LegendModel.legend_id == legend_id)
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                return {"success": True, "message": "Уже открыто."}

            db.add(LegendModel(
                legend_id=legend_id,
                category=legend_type,
                name=name,
                description=description,
                discovered_by=player_id,
            ))
            await db.commit()

            await self.chronicle.publish(
                EventType.LEGEND_DISCOVERED,
                f"Открыта легенда: {name}",
                player_id=player_id,
                importance=Importance.RARE,
                metadata={"legend_id": legend_id, "type": legend_type},
            )

            return {"success": True, "message": f"📜 Легенда открыта: {name}"}
        return {"success": False, "message": "Ошибка базы данных."}

    async def get_legend_stats(self) -> dict:
        async for db in get_db():
            from sqlalchemy import func as sa_func

            from database.models.quest import LegendModel

            stmt = select(sa_func.count()).select_from(LegendModel).where(LegendModel.category == "creature")
            creatures_found = (await db.execute(stmt)).scalar() or 0

            stmt = select(sa_func.count()).select_from(LegendModel).where(LegendModel.category == "item")
            items_found = (await db.execute(stmt)).scalar() or 0

            stmt = select(sa_func.count()).select_from(LegendModel).where(LegendModel.category == "location")
            places_found = (await db.execute(stmt)).scalar() or 0

            stmt = select(sa_func.count()).select_from(LegendModel).where(LegendModel.category == "lore")
            lore_found = (await db.execute(stmt)).scalar() or 0

            return {
                "creatures_found": creatures_found,
                "items_found": items_found,
                "places_found": places_found,
                "lore_found": lore_found,
            }
        return {"creatures_found": 0, "items_found": 0, "places_found": 0, "lore_found": 0}

    async def _apply_level_up(self, user_id: int, new_level: int, db):
        new_max_hp = 100 + (new_level - 1) * 15
        new_attack = 10 + (new_level - 1) * 3
        new_defense = 5 + (new_level - 1) * 2
        await db.execute(
            update(UserModel).where(UserModel.user_id == user_id).values(
                level=new_level, max_hp=new_max_hp, attack=new_attack, defense=new_defense,
            )
        )

    async def _add_item(self, user_id: int, item_id: str, qty: int, db):
        stmt = select(InventoryModel).where(
            InventoryModel.user_id == user_id,
            InventoryModel.item_id == item_id,
            InventoryModel.is_magic == False,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            existing.quantity += qty
        else:
            db.add(InventoryModel(user_id=user_id, item_id=item_id, quantity=qty))

    @staticmethod
    def _quest_to_dict(q: QuestModel) -> dict:
        return {
            "id": q.id,
            "quest_id": q.quest_id,
            "name": q.name,
            "description": q.description,
            "giver": q.giver,
            "location": q.location,
            "objectives": json.loads(q.objectives) if isinstance(q.objectives, str) else q.objectives,
            "rewards": json.loads(q.rewards) if isinstance(q.rewards, str) else q.rewards,
            "is_active": q.is_active,
            "is_repeating": q.is_repeating,
        }
