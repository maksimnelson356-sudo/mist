import logging
from sqlalchemy import select, update, text
from datetime import datetime

from database.base import get_db
from database.models.player_home import PlayerHomeModel
from domain.events import EventType, Importance

logger = logging.getLogger("MIST.home")

HOME_TYPES = {
    "hut": {"name": "Хижина", "max_level": 5, "base_comfort": 10, "base_defenses": 5, "base_storage": 20},
    "cabin": {"name": "Изба", "max_level": 7, "base_comfort": 20, "base_defenses": 10, "base_storage": 40},
    "house": {"name": "Дом", "max_level": 8, "base_comfort": 30, "base_defenses": 15, "base_storage": 60},
    "tower": {"name": "Башня", "max_level": 10, "base_comfort": 40, "base_defenses": 25, "base_storage": 80},
    "fortress": {"name": "Крепость", "max_level": 10, "base_comfort": 50, "base_defenses": 40, "base_storage": 100},
}

ROOM_DEFS = {
    "bedroom": {"name": "Спальня", "comfort": 10, "cost_gold": 50},
    "kitchen": {"name": "Кухня", "comfort": 8, "food_per_day": 5, "cost_gold": 30},
    "workshop": {"name": "Мастерская", "workshop_level": 1, "cost_gold": 100},
    "library": {"name": "Библиотека", "library_level": 1, "cost_gold": 80},
    "garden": {"name": "Сад", "garden_level": 1, "food_per_day": 10, "cost_gold": 40},
    "armory": {"name": "Оружейная", "defenses": 10, "cost_gold": 120},
    "cellar": {"name": "Погреб", "storage": 20, "cost_gold": 25},
    "tower_room": {"name": "Башня", "defenses": 5, "comfort": 5, "cost_gold": 60},
}

HOME_MOODS = {
    "calm": "Тихо. Дом стоит.",
    "happy": "Дом сияет. Что-то хорошее произошло.",
    "scared": "Дом содрогается. Опасность рядом.",
    "angry": "Дом гудит. Что-то не так.",
    "sleepy": "Дом затих. Ночь.",
    "hungry": "Дом трещит. Нет еды.",
}

HOME_EVENTS = {
    "forest_fire": {"condition": -20, "mood": "scared", "message": "Дом задымился от лесного пожара."},
    "flood": {"condition": -15, "mood": "scared", "message": "Вода поднимается. Дом под угрозой."},
    "plague": {"mood": "scared", "message": "Дом замкнулся. Никого не впускает."},
    "harvest_festival": {"mood": "happy", "message": "Дом украшен. Праздник!"},
    "good_harvest": {"mood": "happy", "message": "Дом полон еды. Запасы растут."},
    "drought": {"condition": -5, "mood": "hungry", "message": "Дом трещит от жары. Нет воды."},
    "undead_awakening": {"condition": -25, "mood": "scared", "message": "Дом окружён нежитью. Стены дрожат."},
    "meteorite": {"condition": -30, "mood": "angry", "message": "Ударная волна тряслась домом."},
    "spring_bloom": {"mood": "happy", "message": "Цветы растут сквозь стены. Дом радуется."},
    "fog_storm": {"mood": "scared", "message": "Туман проникает в щели. Дом не видит."},
}


class HomeService:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def create_home(self, owner_id: int, location_id: str, home_type: str = "hut", name: str = "Мой дом") -> dict:
        async for db in get_db():
            existing = await db.execute(
                select(PlayerHomeModel).where(
                    PlayerHomeModel.owner_id == owner_id,
                    PlayerHomeModel.is_active == True,
                )
            )
            if existing.scalar_one_or_none():
                return {"success": False, "message": "У тебя уже есть дом."}

            type_def = HOME_TYPES.get(home_type, HOME_TYPES["hut"])
            home = PlayerHomeModel(
                owner_id=owner_id,
                location_id=location_id,
                name=name,
                home_type=home_type,
                max_level=type_def["max_level"],
                comfort=type_def["base_comfort"],
                defenses=type_def["base_defenses"],
                storage_capacity=type_def["base_storage"],
            )
            db.add(home)
            await db.commit()

            await self.chronicle.publish(
                EventType.LEGEND_DISCOVERED,
                f"🏠 {name} построен в {location_id}",
                player_id=owner_id,
                importance=Importance.COMMON,
            )

            return {
                "success": True,
                "message": f"🏠 {name} построен!",
                "home": self._to_dict(home),
            }

    async def get_home(self, owner_id: int) -> dict | None:
        async for db in get_db():
            result = await db.execute(
                select(PlayerHomeModel).where(
                    PlayerHomeModel.owner_id == owner_id,
                    PlayerHomeModel.is_active == True,
                )
            )
            home = result.scalar_one_or_none()
            return self._to_dict(home) if home else None
        return None

    async def visit_home(self, owner_id: int) -> dict:
        home = await self.get_home(owner_id)
        if not home:
            return {"success": False, "message": "У тебя нет дома."}

        async for db in get_db():
            await db.execute(
                update(PlayerHomeModel)
                .where(PlayerHomeModel.owner_id == owner_id)
                .values(last_visited_at=datetime.utcnow())
            )
            await db.commit()

        mood_text = HOME_MOODS.get(home["mood"], "Тихо.")
        rooms = home.get("rooms", [])
        room_text = ", ".join([r.get("name", "?") for r in rooms]) if rooms else "Пусто"

        return {
            "success": True,
            "home": home,
            "mood_text": mood_text,
            "rooms_text": room_text,
            "message": f"🏠 {home['name']}\n{mood_text}\n\nКомнаты: {room_text}\nУровень: {home['level']}/{home['max_level']}\nКомфорт: {home['comfort']}\nЗащита: {home['defenses']}\nСостояние: {home['condition']}%",
        }

    async def add_room(self, owner_id: int, room_type: str) -> dict:
        home = await self.get_home(owner_id)
        if not home:
            return {"success": False, "message": "У тебя нет дома."}

        room_def = ROOM_DEFS.get(room_type)
        if not room_def:
            return {"success": False, "message": f"Комната '{room_type}' не найдена."}

        rooms = home.get("rooms", [])
        existing_types = [r.get("type") for r in rooms]
        if room_type in existing_types:
            return {"success": False, "message": "Такая комната уже есть."}

        rooms.append({
            "type": room_type,
            "name": room_def["name"],
            "level": 1,
        })

        new_comfort = home["comfort"] + room_def.get("comfort", 0)
        new_defenses = home["defenses"] + room_def.get("defenses", 0)
        new_storage = home["storage_capacity"] + room_def.get("storage", 0)

        async for db in get_db():
            await db.execute(
                update(PlayerHomeModel)
                .where(PlayerHomeModel.owner_id == owner_id)
                .values(
                    rooms=rooms,
                    comfort=new_comfort,
                    defenses=new_defenses,
                    storage_capacity=new_storage,
                )
            )
            await db.commit()

        return {
            "success": True,
            "message": f"🏠 Комната '{room_def['name']}' добавлена!",
            "rooms": rooms,
        }

    async def upgrade_home(self, owner_id: int) -> dict:
        home = await self.get_home(owner_id)
        if not home:
            return {"success": False, "message": "У тебя нет дома."}

        if home["level"] >= home["max_level"]:
            return {"success": False, "message": "Дом уже максимального уровня."}

        new_level = home["level"] + 1
        new_comfort = home["comfort"] + 5
        new_defenses = home["defenses"] + 3
        new_storage = home["storage_capacity"] + 10

        async for db in get_db():
            await db.execute(
                update(PlayerHomeModel)
                .where(PlayerHomeModel.owner_id == owner_id)
                .values(
                    level=new_level,
                    comfort=new_comfort,
                    defenses=new_defenses,
                    storage_capacity=new_storage,
                )
            )
            await db.commit()

        return {
            "success": True,
            "message": f"🏠 Дом улучшен до уровня {new_level}!",
        }

    async def react_to_world_event(self, event_type: str, owner_id: int = None):
        event_def = HOME_EVENTS.get(event_type)
        if not event_def:
            return

        query = select(PlayerHomeModel).where(PlayerHomeModel.is_active == True)
        if owner_id:
            query = query.where(PlayerHomeModel.owner_id == owner_id)

        async for db in get_db():
            result = await db.execute(query)
            homes = result.scalars().all()

            for home in homes:
                new_condition = max(0, min(100, home.condition + event_def.get("condition", 0)))
                new_mood = event_def.get("mood", home.mood)
                history = home.events_history or []
                history.append({
                    "event": event_type,
                    "message": event_def["message"],
                    "condition_change": event_def.get("condition", 0),
                })
                if len(history) > 20:
                    history = history[-20:]

                await db.execute(
                    update(PlayerHomeModel)
                    .where(PlayerHomeModel.id == home.id)
                    .values(
                        condition=new_condition,
                        mood=new_mood,
                        events_history=history,
                    )
                )

            await db.commit()

    async def tick_homes(self, game_hour: int, season: str):
        async for db in get_db():
            result = await db.execute(
                select(PlayerHomeModel).where(PlayerHomeModel.is_active == True)
            )
            homes = result.scalars().all()

            for home in homes:
                new_condition = home.condition
                if home.condition < 50:
                    new_condition = min(100, home.condition + 1)

                new_mood = "calm"
                if game_hour >= 22 or game_hour <= 5:
                    new_mood = "sleepy"
                elif season == "winter" and home.condition < 60:
                    new_mood = "scared"

                income = home.income_per_day
                rooms = home.get("rooms", [])
                for room in rooms:
                    if room.get("type") == "garden":
                        if season in ("spring", "summer"):
                            income += 5
                        elif season == "autumn":
                            income += 10

                await db.execute(
                    update(PlayerHomeModel)
                    .where(PlayerHomeModel.id == home.id)
                    .values(condition=new_condition, mood=new_mood)
                )

            await db.commit()

    @staticmethod
    def _to_dict(row: PlayerHomeModel) -> dict:
        return {
            "id": row.id,
            "owner_id": row.owner_id,
            "location_id": row.location_id,
            "name": row.name,
            "description": row.description,
            "home_type": row.home_type,
            "level": row.level,
            "max_level": row.max_level,
            "rooms": row.rooms or [],
            "decorations": row.decorations or [],
            "defenses": row.defenses,
            "comfort": row.comfort,
            "storage_capacity": row.storage_capacity,
            "garden_level": row.garden_level,
            "workshop_level": row.workshop_level,
            "library_level": row.library_level,
            "is_active": row.is_active,
            "created_at": row.created_at,
            "last_visited_at": row.last_visited_at,
            "upgrades": row.upgrades or {},
            "events_history": row.events_history or [],
            "condition": row.condition,
            "mood": row.mood,
            "income_per_day": row.income_per_day,
        }
