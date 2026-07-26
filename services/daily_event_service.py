import logging
import random

from sqlalchemy import text

from database.base import get_db
from database.models.world_event_record import WorldEventRecordModel
from domain.events import EventType, Importance

logger = logging.getLogger("MIST.daily_events")

DAILY_EVENTS = [
    {
        "event_type": "daily_merchant_arrival",
        "name": "Прибытие торговца",
        "icon": "🐫",
        "description": "Торговый обоз прибыл. Товары дешевле на 20%.",
        "effects": {"wealth": 10},
        "bonus": {"shop_discount": 0.8},
    },
    {
        "event_type": "daily_hunt",
        "name": "Великая охота",
        "icon": "🏹",
        "description": "Охотники вышли в лес. Опыт за убийства +50%.",
        "effects": {"creature_count": -5},
        "bonus": {"xp_mult": 1.5},
    },
    {
        "event_type": "daily_festival",
        "name": "Деревенский праздник",
        "icon": "🎉",
        "description": "Жители празднуют. Торговцы дарят подарки.",
        "effects": {"wealth": 5, "food_supply": 10},
        "bonus": {"free_gold": 20},
    },
    {
        "event_type": "daily_mystic_fog",
        "name": "Мистический туман",
        "icon": "🌫️",
        "description": "Туман несёт древние знания. Магия усиливается.",
        "effects": {"magic_level": 10},
        "bonus": {"magic_find": 1.3},
    },
    {
        "event_type": "daily_bounty",
        "name": "Награда за голову",
        "icon": "💰",
        "description": "Охотник за головами ищет добычу. Награды за убийства x2.",
        "effects": {"danger_level": 5},
        "bonus": {"gold_mult": 2.0},
    },
    {
        "event_type": "daily_healing_springs",
        "name": "Целебные источники",
        "icon": "💚",
        "description": "Источники наполняются целебной силой. Лечение бесплатно.",
        "effects": {"magic_level": 5},
        "bonus": {"free_heal": True},
    },
    {
        "event_type": "daily_full_moon",
        "icon": "🌕",
        "name": "Полнолуние",
        "description": "Луна полна. Волки воют. Опасность растёт.",
        "effects": {"danger_level": 10, "creature_count": 10},
        "bonus": {"xp_mult": 1.3},
    },
    {
        "event_type": "daily_supply_drop",
        "name": "Сброс припасов",
        "icon": "📦",
        "description": "Неизвестный корабль сбросил припасы в море.",
        "effects": {"food_supply": 15},
        "bonus": {"find_item": True},
    },
    {
        "event_type": "daily_traders_dispute",
        "name": "Спор торговцев",
        "icon": "⚖️",
        "description": "Два торговца спорят. Цены нестабильны.",
        "effects": {"wealth": -5},
        "bonus": {"shop_discount": 0.7},
    },
    {
        "event_type": "daily_spirit_walk",
        "name": "Духовный путь",
        "icon": "👻",
        "description": "Духи предков бродят среди живых. Они несут знания.",
        "effects": {"magic_level": 15},
        "bonus": {"xp_mult": 1.4},
    },
]


class DailyEventService:

    def __init__(self, chronicle, world_engine=None):
        self.chronicle = chronicle
        self.world_engine = world_engine

    async def trigger_daily_event(self, current_day: int):
        event = random.choice(DAILY_EVENTS)

        async for db in get_db():
            existing = await db.execute(
                text("SELECT id FROM world_event_records WHERE event_type = :etype AND start_day = :day AND is_active = 1"),
                {"etype": event["event_type"], "day": current_day},
            )
            if existing.first():
                logger.debug(f"Ежедневный ивент уже создан: {event['name']}")
                return

            loc_result = await db.execute(text("SELECT id FROM locations ORDER BY RANDOM() LIMIT 1"))
            loc_row = loc_result.first()
            target_loc = loc_row[0] if loc_row else None

            record = WorldEventRecordModel(
                event_type=event["event_type"],
                name=event["name"],
                description=event["description"],
                region_id=None,
                location_id=target_loc,
                start_day=current_day,
                end_day=current_day,
                is_active=True,
                effects=event.get("effects", {}),
                chain_events=[],
            )
            db.add(record)
            await db.commit()

            if target_loc and self.world_engine:
                await self.world_engine._apply_event_effects(target_loc, event.get("effects", {}), db)

            icon = event.get("icon", "")
            await self.chronicle.publish(
                EventType.WORLD_EVENT,
                f"{icon} {event['name']}: {event['description']}",
                importance=Importance.COMMON,
            )
            logger.info(f"Ежедневный ивент: {event['name']} (день {current_day})")

    async def get_active_daily_bonuses(self) -> dict:
        bonuses = {}
        try:
            async for db in get_db():
                result = await db.execute(
                    text("SELECT event_type FROM world_event_records WHERE is_active = 1 AND end_day >= :day"),
                    {"day": self._get_current_day()},
                )
                active_types = [row[0] for row in result.all()]
                for etype in active_types:
                    ev_def = next((e for e in DAILY_EVENTS if e["event_type"] == etype), None)
                    if ev_def and "bonus" in ev_def:
                        bonuses.update(ev_def["bonus"])
                break
        except Exception as e:
            logger.warning(f"get_active_daily_bonuses error: {e}")
        return bonuses

    def _get_current_day(self) -> int:
        try:
            from services.container import services
            ws = services.world_engine.get_state()
            return ws["game_day"] if ws else 1
        except Exception:
            return 1

    def get_daily_event_info(self, event_type: str) -> dict | None:
        return next((e for e in DAILY_EVENTS if e["event_type"] == event_type), None)

    def get_all_daily_events(self) -> list:
        return [
            {
                "event_type": e["event_type"],
                "name": e["name"],
                "icon": e["icon"],
                "description": e["description"],
                "effects": e.get("effects", {}),
                "bonus": e.get("bonus", {}),
            }
            for e in DAILY_EVENTS
        ]
