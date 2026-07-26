import json
import logging
import random
from sqlalchemy import select, text
from datetime import datetime

from database.base import get_db
from database.models.npc import NPCModel
from database.models.quest import QuestModel

logger = logging.getLogger("MIST.npc_quests")

NPC_QUEST_TEMPLATES = {
    "merchant": [
        {"name": "Доставка товара", "desc": "Доставь товар в {location}. Будь осторожен.", "type": "visit", "reward_xp": 20, "reward_gold": 30},
        {"name": "Найти редкий товар", "desc": "В {location} видели редкий товар. Привези мне.", "type": "visit", "reward_xp": 30, "reward_gold": 50},
    ],
    "guard": [
        {"name": "Очистить территорию", "desc": "В {location} заселись твари. Изгони их.", "type": "kill", "reward_xp": 25, "reward_gold": 20},
        {"name": "Патруль", "desc": "Обыщи {location}. Сообщи о проблемах.", "type": "visit", "reward_xp": 15, "reward_gold": 10},
    ],
    "elder": [
        {"name": "Исследовать руины", "desc": "Старые руины в {location}... Ты найдёшь ответы.", "type": "visit", "reward_xp": 35, "reward_gold": 15},
        {"name": "Найти артефакт", "desc": "В {location} спрятан древний артефакт.", "type": "visit", "reward_xp": 40, "reward_gold": 25},
    ],
    "healer": [
        {"name": "Собрать травы", "desc": "В {location} растёт лечебная трава.", "type": "collect", "reward_xp": 15, "reward_gold": 10},
        {"name": "Помочь раненому", "desc": "В {location} раненый. Помоги ему.", "type": "visit", "reward_xp": 20, "reward_gold": 15},
    ],
    "bartender": [
        {"name": "Доставить напиток", "desc": "Доставь бутылку в {location}. Только аккуратно.", "type": "visit", "reward_xp": 15, "reward_gold": 20},
        {"name": "Собрать слухи", "desc": "Побывай в {location} и расскажи, что слышал.", "type": "visit", "reward_xp": 10, "reward_gold": 5},
    ],
    "shady": [
        {"name": "Кража", "desc": "В {location} есть то, что мне нужно. Достань.", "type": "visit", "reward_xp": 30, "reward_gold": 40},
        {"name": "Устранение", "desc": "В {location} проблема. Устрани её.", "type": "kill", "reward_xp": 35, "reward_gold": 35},
    ],
    "quest_giver": [
        {"name": "Исследование", "desc": "В {location} происходит что-то странное. Расследуй.", "type": "visit", "reward_xp": 25, "reward_gold": 15},
        {"name": "Защита", "desc": "Нужно защитить {location} от угрозы.", "type": "kill", "reward_xp": 30, "reward_gold": 20},
    ],
}


class NPCQuestService:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def generate_quest_for_npc(self, npc_id: str, game_day: int) -> dict | None:
        async for db in get_db():
            result = await db.execute(
                select(NPCModel).where(NPCModel.npc_id == npc_id, NPCModel.is_alive == True)
            )
            npc = result.scalar_one_or_none()
            if not npc:
                return None

            templates = NPC_QUEST_TEMPLATES.get(npc.npc_type, NPC_QUEST_TEMPLATES["quest_giver"])
            template = random.choice(templates)

            result = await db.execute(
                text("SELECT id, location_id FROM locations ORDER BY RANDOM() LIMIT 1")
            )
            loc = result.mappings().first()
            if not loc:
                return None

            location_name = loc["location_id"]
            quest_name = template["name"]
            quest_desc = template["desc"].replace("{location}", location_name)

            quest_id = f"npc_{npc.npc_id}_{game_day}_{random.randint(100, 999)}"

            quest = QuestModel(
                quest_id=quest_id,
                name=quest_name,
                description=quest_desc,
                giver=npc.npc_id,
                location=location_name,
                objectives=json.dumps([{"id": "main", "type": template["type"], "location": location_name, "target": 1, "description": quest_desc}]),
                rewards=json.dumps({"xp": template["reward_xp"], "gold": template["reward_gold"], "memories": 2}),
                is_active=True,
                is_repeating=True,
                cooldown_hours=24,
            )
            db.add(quest)
            await db.commit()

            return {
                "quest_id": quest_id,
                "name": quest_name,
                "description": quest_desc,
                "giver": npc.npc_id,
                "location": location_name,
                "rewards": {"xp": template["reward_xp"], "gold": template["reward_gold"]},
            }

    async def get_available_npc_quests(self, location_id: str) -> list:
        async for db in get_db():
            result = await db.execute(
                select(NPCModel).where(
                    NPCModel.location_str == location_id,
                    NPCModel.is_alive == True,
                )
            )
            npcs = result.scalars().all()

            quests = []
            for npc in npcs:
                result = await db.execute(
                    select(QuestModel).where(
                        QuestModel.giver == npc.npc_id,
                        QuestModel.is_active == True,
                        QuestModel.is_repeating == True,
                    )
                )
                npc_quests = result.scalars().all()
                for q in npc_quests:
                    quests.append({
                        "quest_id": q.quest_id,
                        "name": q.name,
                        "description": q.description,
                        "giver": npc.name,
                    })

            return quests

    async def get_quest_stats(self) -> dict:
        async for db in get_db():
            total = (await db.execute(text("SELECT COUNT(*) FROM quests"))).scalar() or 0
            active = (await db.execute(text("SELECT COUNT(*) FROM quests WHERE is_active = 1"))).scalar() or 0
            return {"total": total, "active": active}
