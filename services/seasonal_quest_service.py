import logging
import random
from sqlalchemy import select, text

from database.base import get_db
from database.models.quest import QuestModel

logger = logging.getLogger("MIST.seasonal_quests")

SEASONAL_QUESTS = {
    "spring": [
        {"quest_id": "season_spring_flowers", "name": "Весенние цветы", "description": "Собери первые цветы весны. Они обещают новую жизнь.",
         "giver": "healer_grove", "location": "enchanted_grove",
         "objectives": [{"id": "flowers", "type": "collect", "item": "spring_flower", "target": 5, "description": "Собери 5 весенних цветов"}],
         "rewards": {"xp": 30, "gold": 20, "memories": 3}},
        {"quest_id": "season_spring_melt", "name": "Таяние", "description": "Река разливается. Помоги жителям.",
         "giver": "elder_fisherman", "location": "fishing_village",
         "objectives": [{"id": "melt", "type": "visit", "location": "riverbank", "target": 1, "description": "Обыщи берег реки"}],
         "rewards": {"xp": 25, "gold": 15, "memories": 2}},
    ],
    "summer": [
        {"quest_id": "season_summer_harvest", "name": "Летний урожай", "description": "Собери урожай. Лето щедро.",
         "giver": "merchant_shadow", "location": "market_square",
         "objectives": [{"id": "harvest", "type": "collect", "item": "summer_fruit", "target": 10, "description": "Собери 10 летних фруктов"}],
         "rewards": {"xp": 35, "gold": 40, "memories": 3}},
        {"quest_id": "season_summer_sun", "name": "Солнечный удар", "description": "Солнце палит. Найди тень для жителей.",
         "giver": "healer_grove", "location": "enchanted_grove",
         "objectives": [{"id": "shade", "type": "visit", "location": "white_forest", "target": 1, "description": "Найди тень в Белом лесу"}],
         "rewards": {"xp": 20, "gold": 10, "memories": 2}},
    ],
    "autumn": [
        {"quest_id": "season_autumn_leaves", "name": "Осенние листья", "description": "Листья падают. Собери их — они полезны.",
         "giver": "healer_grove", "location": "enchanted_grove",
         "objectives": [{"id": "leaves", "type": "collect", "item": "autumn_leaf", "target": 8, "description": "Собери 8 осенних листьев"}],
         "rewards": {"xp": 25, "gold": 15, "memories": 2}},
        {"quest_id": "season_autumn_preparation", "name": "Подготовка к зиме", "description": "Зима близко. Накопи запасы.",
         "giver": "elder_fisherman", "location": "fishing_village",
         "objectives": [{"id": "prepare", "type": "collect", "item": "food_ration", "target": 5, "description": "Собери 5 порций еды"}],
         "rewards": {"xp": 30, "gold": 25, "memories": 3}},
    ],
    "winter": [
        {"quest_id": "season_winter_survival", "name": "Зимнее выживание", "description": "Зима жестока. Выживи.",
         "giver": "shady_informant", "location": "abandoned_camp",
         "objectives": [{"id": "survive", "type": "visit", "location": "frozen_lake", "target": 1, "description": "Доберись до замёрзшего озера"}],
         "rewards": {"xp": 40, "gold": 30, "memories": 4}},
        {"quest_id": "season_winter_frost", "name": "Морозный дух", "description": "Дух мороза бродит. Найди его.",
         "giver": "quest_scholar", "location": "white_forest",
         "objectives": [{"id": "frost", "type": "visit", "location": "frost_hollow", "target": 1, "description": "Найди Морозную лощину"}],
         "rewards": {"xp": 35, "gold": 20, "memories": 3}},
    ],
}


class SeasonalQuestService:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def activate_seasonal_quests(self, season: str):
        quests = SEASONAL_QUESTS.get(season, [])
        if not quests:
            return

        async for db in get_db():
            for q_def in quests:
                existing = await db.execute(
                    select(QuestModel).where(QuestModel.quest_id == q_def["quest_id"])
                )
                if existing.scalar_one_or_none():
                    continue

                quest = QuestModel(
                    quest_id=q_def["quest_id"],
                    name=q_def["name"],
                    description=q_def["description"],
                    giver=q_def["giver"],
                    location=q_def["location"],
                    objectives=q_def["objectives"],
                    rewards=q_def["rewards"],
                    is_active=True,
                    is_repeating=True,
                )
                db.add(quest)
                logger.info(f"Seasonal quest activated: {q_def['name']} ({season})")

            await db.commit()

    async def deactivate_seasonal_quests(self, season: str):
        quests = SEASONAL_QUESTS.get(season, [])
        if not quests:
            return

        async for db in get_db():
            for q_def in quests:
                await db.execute(
                    text("UPDATE quests SET is_active = 0 WHERE quest_id = :qid"),
                    {"qid": q_def["quest_id"]},
                )
            await db.commit()

    async def get_seasonal_quests(self, season: str) -> list:
        quests = SEASONAL_QUESTS.get(season, [])
        return [{
            "quest_id": q["quest_id"],
            "name": q["name"],
            "description": q["description"],
            "location": q["location"],
        } for q in quests]
