import json
from datetime import datetime

from sqlalchemy import select, update, delete

from database.base import get_db
from database.models.quest import QuestModel, UserQuestModel
from database.models.user import UserModel
from database.models.item import ItemTemplateModel
from database.models.inventory import InventoryModel
from domain.events import EventType, Importance


CLASS_QUESTS = {
    "warrior": [
        {"quest_id": "warrior_trial", "name": "РСЃРїС‹С‚Р°РЅРёРµ РІРѕРёРЅР°", "description": "РџРѕР±РµРґРё 5 РІСЂР°РіРѕРІ РІ Р±Р»РёР¶РЅРµРј Р±РѕСЋ.", "location": "dark_forest", "objectives": [{"id": "kill_5", "type": "kill", "target": 5, "description": "РЈР±РёС‚СЊ 5 РІСЂР°РіРѕРІ"}], "reward_xp": 100, "reward_gold": 50},
        {"quest_id": "warrior_boss", "name": "Р‘РѕР»СЊС€РѕР№ Р±РѕР№", "description": "РџРѕР±РµРґРё Р»СЋР±РѕРіРѕ Р±РѕСЃСЃР°.", "location": "any", "objectives": [{"id": "kill_boss", "type": "kill_boss", "target": 1, "description": "РЈР±РёС‚СЊ Р±РѕСЃСЃР°"}], "reward_xp": 300, "reward_gold": 200},
    ],
    "mage": [
        {"quest_id": "mage_arcane", "name": "РђСЂРєР°РЅС‹ РјР°РіРёРё", "description": "РќР°Р№РґРё 3 Р°СЂС‚РµС„Р°РєС‚Р°.", "location": "any", "objectives": [{"id": "find_3", "type": "find_artifact", "target": 3, "description": "РќР°Р№С‚Рё 3 Р°СЂС‚РµС„Р°РєС‚Р°"}], "reward_xp": 150, "reward_gold": 100},
        {"quest_id": "mage_lib", "name": "Р‘РёР±Р»РёРѕС‚РµРєР° СЌС…РѕРІ", "description": "РџРѕСЃРµС‚Рё Р‘РёР±Р»РёРѕС‚РµРєСѓ СЌС…РѕРІ.", "location": "library_of_echoes", "objectives": [{"id": "visit_lib", "type": "visit", "location": "library_of_echoes", "target": 1, "description": "РџРѕСЃРµС‚РёС‚СЊ Р‘РёР±Р»РёРѕС‚РµРєСѓ СЌС…РѕРІ"}], "reward_xp": 100, "reward_gold": 75},
    ],
    "scout": [
        {"quest_id": "scout_explore", "name": "РџРµСЂРІРѕРѕС‚РєСЂС‹РІР°С‚РµР»СЊ", "description": "РћС‚РєСЂРѕР№ 5 РЅРѕРІС‹С… Р»РѕРєР°С†РёР№.", "location": "any", "objectives": [{"id": "explore_5", "type": "discover", "target": 5, "description": "РћС‚РєСЂС‹С‚СЊ 5 Р»РѕРєР°С†РёР№"}], "reward_xp": 120, "reward_gold": 80},
        {"quest_id": "scout_night", "name": "РќРѕС‡РЅРѕР№ СЃС‚СЂР°РЅРЅРёРє", "description": "Р’С‹Р¶РёРІРё РІ РЅРѕС‡РЅРѕРј РїСѓС‚РµС€РµСЃС‚РІРёРё.", "location": "any", "objectives": [{"id": "survive_night", "type": "survive_night", "target": 1, "description": "Р’С‹Р¶РёС‚СЊ РЅРѕС‡СЊСЋ"}], "reward_xp": 100, "reward_gold": 60},
    ],
    "craftsman": [
        {"quest_id": "craft_master", "name": "РњР°СЃС‚РµСЂ СЂРµРјРµСЃР»Р°", "description": "РЎРєСЂР°С„С‚Рё 5 РїСЂРµРґРјРµС‚РѕРІ.", "location": "any", "objectives": [{"id": "craft_5", "type": "craft", "target": 5, "description": "РЎРєСЂР°С„С‚Рё 5 РїСЂРµРґРјРµС‚РѕРІ"}], "reward_xp": 100, "reward_gold": 120},
        {"quest_id": "craft_gather", "name": "РЎР±РѕСЂ СЂРµСЃСѓСЂСЃРѕРІ", "description": "РЎРѕР±РµСЂРё 10 СЂРµСЃСѓСЂСЃРѕРІ.", "location": "any", "objectives": [{"id": "gather_10", "type": "collect", "target": 10, "description": "РЎРѕР±СЂР°С‚СЊ 10 СЂРµСЃСѓСЂСЃРѕРІ"}], "reward_xp": 80, "reward_gold": 100},
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
                return {"success": False, "message": "РљРІРµСЃС‚ РЅРµ РЅР°Р№РґРµРЅ."}

            user = await self.user_service.get(user_id)
            if quest.location and quest.location != user["current_location"]:
                return {"success": False, "message": "РўС‹ РЅРµ РІ С‚РѕР№ Р»РѕРєР°С†РёРё РґР»СЏ СЌС‚РѕРіРѕ РєРІРµСЃС‚Р°."}

            stmt_check = select(UserQuestModel).where(
                UserQuestModel.user_id == user_id,
                UserQuestModel.quest_id == quest_id,
                UserQuestModel.status == "active",
            )
            result_check = await db.execute(stmt_check)
            if result_check.scalar_one_or_none():
                return {"success": False, "message": "РўС‹ СѓР¶Рµ РІС‹РїРѕР»РЅСЏРµС€СЊ СЌС‚РѕС‚ РєРІРµСЃС‚."}

            stmt_done = select(UserQuestModel).where(
                UserQuestModel.user_id == user_id,
                UserQuestModel.quest_id == quest_id,
                UserQuestModel.status == "completed",
            )
            result_done = await db.execute(stmt_done)
            completed = result_done.scalar_one_or_none()
            if completed:
                if not quest.is_repeating:
                    return {"success": False, "message": "РўС‹ СѓР¶Рµ РІС‹РїРѕР»РЅРёР» СЌС‚РѕС‚ РєРІРµСЃС‚."}
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
                f"РљРІРµСЃС‚ РїСЂРёРЅСЏС‚: {quest.name}",
                player_id=user_id,
                region_id=quest.location,
                importance=Importance.COMMON,
            )

            return {"success": True, "quest": self._quest_to_dict(quest), "message": f"рџ“њ РљРІРµСЃС‚ РїСЂРёРЅСЏС‚: <b>{quest.name}</b>"}
        return {"success": False, "message": "РћС€РёР±РєР° Р±Р°Р·С‹ РґР°РЅРЅС‹С…."}

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
                # Р’РѕСЃСЃС‚Р°РЅР°РІР»РёРІР°РµРј СЃС‚Р°С‚СѓСЃ, РµСЃР»Рё РєРІРµСЃС‚ РЅРµ СѓРґР°С‡РЅРѕ Р·Р°РІРµСЂС€РµРЅ
                uq.status = "active"  # Р”РѕР±Р°РІРёРј РѕР±СЂР°С‚РЅРѕ РїРµСЂРІРѕРЅР°С‡Р°Р»СЊРЅС‹Р№ СЃС‚Р°С‚СѓСЃ
                await db.commit()
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
                    f"РљРІРµСЃС‚ РІС‹РїРѕР»РЅРµРЅ: {quest.name}",
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

                msg = "рџЏ† <b>РљРІРµСЃС‚ РІС‹РїРѕР»РЅРµРЅ</b>\n\n"
                msg += f"рџ“њ <b>{quest.name}</b>!"
                if "xp" in rewards:
                    msg += f"\n\n+{rewards['xp']} XP"
                if leveled:
                    msg += f"\n\nв­ђ РЈР РћР’Р•РќР¬ РџРћР’Р«РЁР•Рќ в†’ {new_level}!"
                return {"success": True, "completed": True, "rewards": rewards, "message": msg}
            else:
                uq.progress = json.dumps(progress)
                await db.commit()
                return {"success": True, "completed": False}
        return {"success": False, "message": "РћС€РёР±РєР° Р±Р°Р·С‹ РґР°РЅРЅС‹С…."}

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
                return {"success": False, "message": "РљРІРµСЃС‚ РЅРµ РЅР°Р№РґРµРЅ РёР»Рё СѓР¶Рµ Р·Р°РІРµСЂС€С‘РЅ."}

            q_stmt = select(QuestModel).where(QuestModel.quest_id == quest_id)
            q_result = await db.execute(q_stmt)
            quest = q_result.scalar_one_or_none()
            if not quest:
                return {"success": False, "message": "Р РµР°Р»РёР·Р°С†РёСЏ РєРІРµСЃС‚Р° РЅРµ РЅР°Р№РґРµРЅР°."}

            progress = json.loads(uq.progress) if isinstance(uq.progress, str) else uq.progress
            objectives = json.loads(quest.objectives) if isinstance(quest.objectives, str) else quest.objectives

            all_done = all(
                progress.get(obj["id"], {}).get("current", 0) >= obj["target"]
                for obj in objectives
            )
            if not all_done:
                return {"success": False, "message": "Р¦РµР»Рё РµС‰С‘ РЅРµ РІС‹РїРѕР»РЅРµРЅС‹."}

            rewards = json.loads(quest.rewards) if isinstance(quest.rewards, str) else quest.rewards
            user_stmt = select(UserModel).where(UserModel.user_id == user_id)
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            if not user:
                return {"success": False, "message": "РРіСЂРѕРє РЅРµ РЅР°Р№РґРµРЅ."}

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

            msg = "рџЏ† <b>РљРІРµСЃС‚ РІС‹РїРѕР»РЅРµРЅ</b>\n\n"
            msg += f"рџ“њ <b>{quest.name}</b>!"
            if "xp" in rewards:
                msg += f"\n\n+{rewards['xp']} XP"
            if leveled:
                msg += f"\n\nв­ђ РЈР РћР’Р•РќР¬ РџРћР’Р«РЁР•Рќ в†’ {new_level}!"
            return {"success": True, "completed": True, "rewards": rewards, "message": msg}
        return {"success": False, "message": "РћС€РёР±РєР° Р±Р°Р·С‹ РґР°РЅРЅС‹С…."}

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
                    "objectives": json.loads(q.objectives) if isinstance(q.objectives, str) else q.objectives,
                    "rewards": json.loads(q.rewards) if isinstance(q.rewards, str) else q.rewards,
                })
            return quests
        return []

    async def discover_legend(self, legend_id: str, legend_type: str, name: str, description: str, player_id: int) -> dict:
        async for db in get_db():
            from database.models.quest import LegendModel
            from sqlalchemy import select as sel
            stmt = sel(LegendModel).where(LegendModel.legend_id == legend_id)
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                return {"success": True, "message": "РЈР¶Рµ РѕС‚РєСЂС‹С‚Рѕ."}

            db.add(LegendModel(
                legend_id=legend_id,
                legend_type=legend_type,
                name=name,
                description=description,
                discovered_by=player_id,
            ))
            await db.commit()

            await self.chronicle.publish(
                EventType.LEGEND_DISCOVERED,
                f"РћС‚РєСЂС‹С‚Р° Р»РµРіРµРЅРґР°: {name}",
                player_id=player_id,
                importance=Importance.RARE,
                metadata={"legend_id": legend_id, "type": legend_type},
            )

            return {"success": True, "message": f"рџ“њ Р›РµРіРµРЅРґР° РѕС‚РєСЂС‹С‚Р°: {name}"}
        return {"success": False, "message": "РћС€РёР±РєР° Р±Р°Р·С‹ РґР°РЅРЅС‹С…."}

    async def get_legend_stats(self) -> dict:
        async for db in get_db():
            from database.models.quest import LegendModel
            from sqlalchemy import func as sa_func

            stmt = select(sa_func.count()).select_from(LegendModel).where(LegendModel.legend_type == "creature")
            creatures_found = (await db.execute(stmt)).scalar() or 0

            stmt = select(sa_func.count()).select_from(LegendModel).where(LegendModel.legend_type == "item")
            items_found = (await db.execute(stmt)).scalar() or 0

            stmt = select(sa_func.count()).select_from(LegendModel).where(LegendModel.legend_type == "location")
            places_found = (await db.execute(stmt)).scalar() or 0

            stmt = select(sa_func.count()).select_from(LegendModel).where(LegendModel.legend_type == "lore")
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
        await db.commit()

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
        await db.commit()

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
