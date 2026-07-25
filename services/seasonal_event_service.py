import logging
import random
from sqlalchemy import text
from database.base import get_db
from database.models.world_event_record import WorldEventRecordModel
from domain.events import EventType, Importance

logger = logging.getLogger("MIST.seasonal_events")

SEASONAL_EVENTS = {
    "spring": [
        {
            "event_type": "season_spring_bloom",
            "name": "Весеннее пробуждение",
            "icon": "🌸",
            "description": "Земля пробуждается. Леса зеленеют, реки тают, мир наполняется жизнью.",
            "duration_days": 5,
            "effects": {"food_supply": 20, "magic_level": 10, "danger_level": -5},
            "rewards": {"xp_bonus": 1.5, "gold_bonus": 1.2},
        },
        {
            "event_type": "season_spring_floods",
            "name": "Весенние паводки",
            "icon": "🌊",
            "description": "Реки разливаются. Дороги затоплены. Торговля останавливается.",
            "duration_days": 3,
            "effects": {"food_supply": -10, "danger_level": 10},
            "rewards": {"xp_bonus": 1.3, "gold_bonus": 1.0},
        },
    ],
    "summer": [
        {
            "event_type": "season_summer_festival",
            "name": "Летний солнцеворот",
            "icon": "☀️",
            "description": "День最长. Люди празднуют. Магия усиливается.",
            "duration_days": 3,
            "effects": {"magic_level": 15, "danger_level": -10},
            "rewards": {"xp_bonus": 1.5, "gold_bonus": 1.3},
        },
        {
            "event_type": "season_summer_drought",
            "name": "Летняя засуха",
            "icon": "🔥",
            "description": "Земля трескается. Реки мелеют. Запасы тают.",
            "duration_days": 5,
            "effects": {"food_supply": -25, "danger_level": 15},
            "rewards": {"xp_bonus": 1.2, "gold_bonus": 1.0},
        },
    ],
    "autumn": [
        {
            "event_type": "season_autumn_harvest",
            "name": "Жатва",
            "icon": "🌾",
            "description": "Урожай собран. Запасы пополняются. Торговцы радуются.",
            "duration_days": 5,
            "effects": {"food_supply": 30, "wealth": 15},
            "rewards": {"xp_bonus": 1.3, "gold_bonus": 1.5},
        },
        {
            "event_type": "season_autumn_mists",
            "name": "Осенние туманы",
            "icon": "🌫️",
            "description": "Туман окутывает землю. Видимость падает. В лесу слышны голоса.",
            "duration_days": 4,
            "effects": {"danger_level": 10, "magic_level": 5},
            "rewards": {"xp_bonus": 1.4, "gold_bonus": 1.1},
        },
    ],
    "winter": [
        {
            "event_type": "season_winter_frost",
            "name": "Морозный дух",
            "icon": "❄️",
            "description": "Мороз крепнет. Земля стынет. Духи холода бродят среди деревьев.",
            "duration_days": 7,
            "effects": {"danger_level": 15, "food_supply": -20},
            "rewards": {"xp_bonus": 1.5, "gold_bonus": 1.2},
        },
        {
            "event_type": "season_winter_aurora",
            "name": "Зимняя аврора",
            "icon": "🌌",
            "description": "Северное сияние окрашивает небо. Магия усиливается.",
            "duration_days": 3,
            "effects": {"magic_level": 20},
            "rewards": {"xp_bonus": 1.3, "gold_bonus": 1.0},
        },
    ],
}


class SeasonalEventService:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def trigger_season_event(self, season: str, current_day: int):
        events = SEASONAL_EVENTS.get(season, [])
        if not events:
            return

        event = random.choice(events)

        async for db in get_db():
            existing = await db.execute(
                text("SELECT id FROM world_event_records WHERE event_type = :etype AND is_active = 1"),
                {"etype": event["event_type"]},
            )
            if existing.first():
                logger.debug(f"Сезонный ивент уже активен: {event['name']}")
                return

            record = WorldEventRecordModel(
                event_type=event["event_type"],
                name=event["name"],
                description=event["description"],
                region_id=None,
                location_id=None,
                start_day=current_day,
                end_day=current_day + event["duration_days"] if event["duration_days"] > 0 else None,
                is_active=True,
                effects=event.get("effects", {}),
                chain_events=[],
            )
            db.add(record)
            await db.commit()

            icon = event.get("icon", "")
            await self.chronicle.publish(
                EventType.WORLD_EVENT,
                f"{icon} {event['name']}: {event['description']}",
                importance=Importance.NOTABLE,
            )
            logger.info(f"Сезонный ивент: {event['name']} ({season})")

    def get_seasonal_events(self, season: str) -> list:
        events = SEASONAL_EVENTS.get(season, [])
        return [
            {
                "event_type": e["event_type"],
                "name": e["name"],
                "icon": e["icon"],
                "description": e["description"],
                "duration_days": e["duration_days"],
                "effects": e.get("effects", {}),
                "rewards": e.get("rewards", {}),
            }
            for e in events
        ]

    def get_current_season_event(self, season: str) -> dict | None:
        events = SEASONAL_EVENTS.get(season, [])
        if events:
            return random.choice(events)
        return None
