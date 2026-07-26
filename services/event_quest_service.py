import logging
import random
from sqlalchemy import select, text
from datetime import datetime, timezone

from database.base import get_db
from database.models.quest import QuestModel
from domain.events import EventType, Importance

logger = logging.getLogger("MIST.event_quests")

EVENT_QUEST_TEMPLATES = {
    "plague": [
        {
            "quest_id": "evt_plague_cure",
            "name": "Найти лекарство",
            "description": "Эпидемия бушует. Целитель ищет редкую траву в лесу.",
            "giver": "healer",
            "location": "enchanted_grove",
            "objectives": [{"id": "herbs", "type": "collect", "item": "healing_herb", "target": 5, "description": "Собери 5 лечебных трав"}],
            "rewards": {"xp": 80, "gold": 60, "memories": 5},
        },
        {
            "quest_id": "evt_plague_supply",
            "name": "Доставить лекарство",
            "description": "Лекарство готово. Доставь его в деревню.",
            "giver": "healer",
            "location": "fishing_village",
            "objectives": [{"id": "deliver", "type": "visit", "location": "fishing_village", "target": 1, "description": "Доставь лекарство в деревню"}],
            "rewards": {"xp": 50, "gold": 40, "memories": 3},
        },
    ],
    "flood": [
        {
            "quest_id": "evt_flood_rescue",
            "name": "Спасение жителей",
            "description": "Вода поднимается. Люди застряли на крышах.",
            "giver": "guard",
            "location": "fishing_village",
            "objectives": [{"id": "rescue", "type": "visit", "location": "riverbank", "target": 3, "description": "Спаси 3 групп жителей"}],
            "rewards": {"xp": 70, "gold": 50, "memories": 4},
        },
        {
            "quest_id": "evt_flood_build",
            "name": "Построить плотину",
            "description": "Нужно остановить воду. Собери камни и древесину.",
            "giver": "elder",
            "location": "fishing_village",
            "objectives": [{"id": "stones", "type": "collect", "item": "stone", "target": 10, "description": "Собери 10 камней"}],
            "rewards": {"xp": 90, "gold": 70, "memories": 6},
        },
    ],
    "forest_fire": [
        {
            "quest_id": "evt_fire_fight",
            "name": "Тушить пожар",
            "description": "Лес горит. Нужна вода и помощь.",
            "giver": "guard",
            "location": "dark_forest",
            "objectives": [{"id": "water", "type": "collect", "item": "water_flask", "target": 5, "description": "Принеси 5 фляг воды"}],
            "rewards": {"xp": 60, "gold": 45, "memories": 4},
        },
    ],
    "undead_awakening": [
        {
            "quest_id": "evt_undead_siege",
            "name": "Оборона кладбища",
            "description": "Нежить штурмует кладбище. Сражайся за покой мёртвых.",
            "giver": "elder",
            "location": "forgotten_graveyard",
            "objectives": [{"id": "kill", "type": "kill", "target_creature": "skeleton", "target": 5, "description": "Убей 5 скелетов"}],
            "rewards": {"xp": 100, "gold": 80, "memories": 6},
        },
    ],
    "drought": [
        {
            "quest_id": "evt_drought_water",
            "name": "Найти воду",
            "description": "Реки мелеют. Нужно найти подземный источник.",
            "giver": "healer",
            "location": "enchanted_grove",
            "objectives": [{"id": "visit", "type": "visit", "location": "crystal_cave", "target": 1, "description": "Найди подземный источник в Кристальной пещере"}],
            "rewards": {"xp": 55, "gold": 35, "memories": 3},
        },
    ],
    "bandits": [
        {
            "quest_id": "evt_bandits_clear",
            "name": "Очистить дорогу",
            "description": "Бандиты перекрыли торговый путь. Гильдия ищет героев.",
            "giver": "guard",
            "location": "market_square",
            "objectives": [{"id": "kill", "type": "kill", "target_creature": "bandit", "target": 3, "description": "Убей 3 бандитов"}],
            "rewards": {"xp": 65, "gold": 55, "memories": 4},
        },
    ],
    "famine": [
        {
            "quest_id": "evt_famine_food",
            "name": "Найти пропитание",
            "description": "Люди голодают. Собери любую еду.",
            "giver": "merchant",
            "location": "market_square",
            "objectives": [{"id": "food", "type": "collect", "item": "food_ration", "target": 8, "description": "Собери 8 порций еды"}],
            "rewards": {"xp": 45, "gold": 30, "memories": 3},
        },
    ],
    "wolf_pack_migration": [
        {
            "quest_id": "evt_wolves_scout",
            "name": "Разведать путь волков",
            "description": "Огромная стая движется через лес. Нужно узнать, куда они идут.",
            "giver": "guard",
            "location": "dark_forest",
            "objectives": [{"id": "visit", "type": "visit", "location": "wolf_den", "target": 1, "description": "Доберись до волчьего логова"}],
            "rewards": {"xp": 50, "gold": 25, "memories": 3},
        },
    ],
    "clan_war": [
        {
            "quest_id": "evt_clan_mediate",
            "name": "Посредничество",
            "description": "Два клана сошлись в смертельной битве. Попробуй остановить.",
            "giver": "elder",
            "location": "market_square",
            "objectives": [{"id": "visit", "type": "visit", "location": "blood_meadow", "target": 1, "description": "Доберись до поля боя"}],
            "rewards": {"xp": 75, "gold": 50, "memories": 5},
        },
    ],
    "meteorite": [
        {
            "quest_id": "evt_meteorite_research",
            "name": "Исследовать кратер",
            "description": "Метеорит упал. В кратере странные кристаллы.",
            "giver": "elder",
            "location": "mountains",
            "objectives": [{"id": "visit", "type": "visit", "location": "crystal_cave", "target": 1, "description": "Исследуй кратер"}],
            "rewards": {"xp": 120, "gold": 90, "memories": 7},
        },
    ],
    "merchant_caravan": [
        {
            "quest_id": "evt_caravan_escort",
            "name": "Эскорт каравана",
            "description": "Торговый караван ищет защитников для дороги.",
            "giver": "merchant",
            "location": "market_square",
            "objectives": [{"id": "visit", "type": "visit", "location": "dark_harbour", "target": 1, "description": "Проведи караван до гавани"}],
            "rewards": {"xp": 40, "gold": 60, "memories": 3},
        },
    ],
}


class EventQuestService:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def generate_quests_for_event(self, event_type: str, region_id: str = None, current_day: int = 1) -> int:
        templates = EVENT_QUEST_TEMPLATES.get(event_type, [])
        if not templates:
            return 0

        created = 0
        async for db in get_db():
            for tpl in templates:
                existing = await db.execute(
                    select(QuestModel).where(QuestModel.quest_id == tpl["quest_id"])
                )
                if existing.scalar_one_or_none():
                    continue

                quest = QuestModel(
                    quest_id=tpl["quest_id"],
                    name=tpl["name"],
                    description=tpl["description"],
                    giver=tpl.get("giver", "quest_giver"),
                    location=tpl.get("location", region_id or "market_square"),
                    objectives=tpl["objectives"],
                    rewards=tpl["rewards"],
                    is_active=True,
                    is_repeating=False,
                    cooldown_hours=0,
                )
                db.add(quest)
                created += 1

                await self.chronicle.publish(
                    EventType.QUEST_ACCEPTED,
                    f"📜 Новый квест: {tpl['name']} — {tpl['description']}",
                    importance=Importance.COMMON,
                )
                logger.info(f"Event quest created: {tpl['quest_id']} ({event_type})")

            await db.commit()
        return created

    async def generate_chain_quest(self, chain_event_key: str, parent_event_type: str, region_id: str = None, current_day: int = 1) -> int:
        from services.world_event_defs import WORLD_EVENT_DEFS
        chain_def = WORLD_EVENT_DEFS.get(chain_event_key)
        if not chain_def:
            return 0

        quest_id = f"chain_{chain_event_key}_{current_day}"
        quest_templates = {
            "refugees": {"name": "Помочь беженцам", "desc": "Беженцы ищут укрытие. Помоги им найти дом.", "type": "visit", "xp": 50, "gold": 35},
            "wood_scarcity": {"name": "Найти древесину", "desc": "Древесина стала дефицитом. Найди лесной склад.", "type": "visit", "xp": 40, "gold": 30},
            "village_attack": {"name": "Защитить деревню", "desc": "Деревня атакована. Помоги отстроить стены.", "type": "visit", "xp": 60, "gold": 45},
            "healer_quest": {"name": "Найти целителя", "desc": "Болезнь обрела масштаб. Нужен герой-целитель.", "type": "visit", "xp": 70, "gold": 50},
            "crater_resources": {"name": "Добыть кристаллы", "desc": "В кратере обнаружены редкие кристаллы.", "type": "visit", "xp": 80, "gold": 60},
            "graveyard_siege": {"name": "Оборона кладбища", "desc": "Нежить штурмует кладбище.", "type": "kill", "xp": 90, "gold": 70},
        }

        tpl = quest_templates.get(chain_event_key)
        if not tpl:
            return 0

        async for db in get_db():
            existing = await db.execute(
                select(QuestModel).where(QuestModel.quest_id == quest_id)
            )
            if existing.scalar_one_or_none():
                return 0

            quest = QuestModel(
                quest_id=quest_id,
                name=tpl["name"],
                description=tpl["desc"],
                giver="quest_giver",
                location=region_id or "market_square",
                objectives=[{"id": "main", "type": tpl["type"], "location": region_id or "market_square", "target": 1, "description": tpl["desc"]}],
                rewards={"xp": tpl["xp"], "gold": tpl["gold"], "memories": 3},
                is_active=True,
                is_repeating=False,
            )
            db.add(quest)
            await db.commit()

            await self.chronicle.publish(
                EventType.QUEST_ACCEPTED,
                f"📜 Цепной квест: {tpl['name']}",
                importance=Importance.COMMON,
            )
            logger.info(f"Chain quest created: {quest_id} (from {parent_event_type})")
            return 1
        return 0

    async def get_event_quests(self) -> list:
        async for db in get_db():
            result = await db.execute(
                select(QuestModel).where(
                    QuestModel.quest_id.like("evt_%"),
                    QuestModel.is_active == True,
                )
            )
            return [{
                "quest_id": q.quest_id,
                "name": q.name,
                "description": q.description,
                "giver": q.giver,
                "location": q.location,
            } for q in result.scalars().all()]
