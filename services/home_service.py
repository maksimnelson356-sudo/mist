import logging
from sqlalchemy import select, update, text
from datetime import datetime, timezone

from database.base import get_db
from database.models.player_home import PlayerHomeModel
from database.models.user import UserModel
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
                .values(last_visited_at=datetime.now(timezone.utc))
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

                if income > 0:
                    user_result = await db.execute(
                        select(UserModel).where(UserModel.user_id == home.owner_id)
                    )
                    user = user_result.scalar_one_or_none()
                    if user:
                        new_gold = user.gold + income
                        await db.execute(
                            update(UserModel)
                            .where(UserModel.user_id == home.owner_id)
                            .values(gold=new_gold)
                        )

                await db.execute(
                    update(PlayerHomeModel)
                    .where(PlayerHomeModel.id == home.id)
                    .values(condition=new_condition, mood=new_mood, income_per_day=income)
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
            "storage": row.storage or [],
        }

    async def storage_deposit(self, user_id: int, item_id: str, qty: int = 1) -> dict:
        async for db in get_db():
            stmt = select(PlayerHomeModel).where(
                PlayerHomeModel.owner_id == user_id,
                PlayerHomeModel.is_active == True,
            )
            result = await db.execute(stmt)
            home = result.scalar_one_or_none()
            if not home:
                return {"success": False, "message": "У тебя нет дома."}

            storage = home.storage or []
            total_qty = sum(s.get("qty", 1) for s in storage)
            if total_qty >= home.storage_capacity:
                return {"success": False, "message": f"Нет места. Занято {total_qty}/{home.storage_capacity}"}

            for s in storage:
                if s.get("item_id") == item_id:
                    s["qty"] = s.get("qty", 1) + qty
                    break
            else:
                storage.append({"item_id": item_id, "qty": qty})

            home.storage = storage
            await db.commit()
            return {"success": True, "message": f"📦 Положил {item_id} x{qty} в хранилище."}
        return {"success": False, "message": "Ошибка базы данных."}

    async def storage_withdraw(self, user_id: int, item_id: str, qty: int = 1) -> dict:
        async for db in get_db():
            stmt = select(PlayerHomeModel).where(
                PlayerHomeModel.owner_id == user_id,
                PlayerHomeModel.is_active == True,
            )
            result = await db.execute(stmt)
            home = result.scalar_one_or_none()
            if not home:
                return {"success": False, "message": "У тебя нет дома."}

            storage = home.storage or []
            existing = next((s for s in storage if s.get("item_id") == item_id), None)
            if not existing or existing.get("qty", 1) < qty:
                avail = existing.get("qty", 1) if existing else 0
                return {"success": False, "message": f"Нет {item_id} x{qty} (есть x{avail})."}

            existing["qty"] -= qty
            if existing["qty"] <= 0:
                storage = [s for s in storage if s.get("item_id") != item_id]

            home.storage = storage
            await db.commit()
            return {"success": True, "message": f"📦 Забрал {item_id} x{qty} из хранилища."}
        return {"success": False, "message": "Ошибка базы данных."}

    REPAIR_COSTS = {
        "wood": {"gold": 20, "condition_gain": 10},
        "stone": {"gold": 30, "condition_gain": 15},
        "iron": {"gold": 50, "condition_gain": 25},
    }

    async def repair_home(self, owner_id: int, material: str = "wood") -> dict:
        home = await self.get_home(owner_id)
        if not home:
            return {"success": False, "message": "У тебя нет дома."}

        if home["condition"] >= 100:
            return {"success": False, "message": "Дом уже в идеальном состоянии."}

        cost_def = self.REPAIR_COSTS.get(material)
        if not cost_def:
            return {"success": False, "message": f"Неизвестный материал: {material}. Доступные: wood, stone, iron."}

        from services.container import services
        user = await services.player.get(owner_id)
        if not user:
            return {"success": False, "message": "Пользователь не найден."}

        if user["gold"] < cost_def["gold"]:
            return {"success": False, "message": f"Недостаточно золота. Нужно: {cost_def['gold']} 🪙, есть: {user['gold']} 🪙"}

        new_condition = min(100, home["condition"] + cost_def["condition_gain"])

        async for db in get_db():
            from sqlalchemy import update as sa_update
            await db.execute(
                sa_update(PlayerHomeModel)
                .where(PlayerHomeModel.owner_id == owner_id)
                .values(condition=new_condition)
            )
            await db.execute(
                sa_update(UserModel)
                .where(UserModel.user_id == owner_id)
                .values(gold=user["gold"] - cost_def["gold"])
            )
            await db.commit()

        material_names = {"wood": "дерево", "stone": "камень", "iron": "железо"}
        await self.chronicle.publish(
            EventType.LEGEND_DISCOVERED,
            f"🔧 Дом отремонтирован ({material_names.get(material, material)}). Состояние: {new_condition}%",
            player_id=owner_id,
            importance=Importance.TRIVIAL,
        )

        return {
            "success": True,
            "message": f"🔧 Дом отремонтирован! +{cost_def['condition_gain']}% ({material_names.get(material, material)}). Состояние: {new_condition}%",
            "condition": new_condition,
            "gold_spent": cost_def["gold"],
        }

    async def build_defense(self, owner_id: int, defense_type: str) -> dict:
        DEFENSE_BUILDINGS = {
            "wall": {"name": "Стена", "defenses": 10, "gold": 100, "condition_gain": 0},
            "dam": {"name": "Плотина", "defenses": 15, "gold": 150, "condition_gain": 5},
            "firebreak": {"name": "Противопожарный разрыв", "defenses": 8, "gold": 80, "condition_gain": 0},
        }

        building = DEFENSE_BUILDINGS.get(defense_type)
        if not building:
            return {"success": False, "message": f"Неизвестный тип: {defense_type}. Доступные: {', '.join(DEFENSE_BUILDINGS.keys())}"}

        home = await self.get_home(owner_id)
        if not home:
            return {"success": False, "message": "У тебя нет дома."}

        from services.container import services
        user = await services.player.get(owner_id)
        if not user:
            return {"success": False, "message": "Пользователь не найден."}

        if user["gold"] < building["gold"]:
            return {"success": False, "message": f"Недостаточно золота. Нужно: {building['gold']} 🪙, есть: {user['gold']} 🪙"}

        new_defenses = home["defenses"] + building["defenses"]
        new_condition = min(100, home["condition"] + building["condition_gain"])

        async for db in get_db():
            from sqlalchemy import update as sa_update
            await db.execute(
                sa_update(PlayerHomeModel)
                .where(PlayerHomeModel.owner_id == owner_id)
                .values(defenses=new_defenses, condition=new_condition)
            )
            await db.execute(
                sa_update(UserModel)
                .where(UserModel.user_id == owner_id)
                .values(gold=user["gold"] - building["gold"])
            )
            await db.commit()

        upgrades = home.get("upgrades", {})
        upgrades[defense_type] = upgrades.get(defense_type, 0) + 1

        async for db in get_db():
            from sqlalchemy import update as sa_update
            await db.execute(
                sa_update(PlayerHomeModel)
                .where(PlayerHomeModel.owner_id == owner_id)
                .values(upgrades=upgrades)
            )
            await db.commit()

        await self.chronicle.publish(
            EventType.LEGEND_DISCOVERED,
            f"🏗 Построено: {building['name']}! Защита: +{building['defenses']}",
            player_id=owner_id,
            importance=Importance.COMMON,
        )

        return {
            "success": True,
            "message": f"🏗 {building['name']} построена! Защита: +{building['defenses']}. Состояние: {new_condition}%",
            "defenses": new_defenses,
            "condition": new_condition,
            "gold_spent": building["gold"],
        }

    async def repair_location(self, user_id: int, location_id: str, material: str = "wood") -> dict:
        REPAIR_COSTS = {"wood": 50, "stone": 80, "iron": 120}
        REPAIR_GAIN = {"wood": 10, "stone": 15, "iron": 25}

        gold_cost = REPAIR_COSTS.get(material, 50)
        condition_gain = REPAIR_GAIN.get(material, 10)

        from services.container import services
        user = await services.player.get(user_id)
        if not user:
            return {"success": False, "message": "Пользователь не найден."}

        if user["gold"] < gold_cost:
            return {"success": False, "message": f"Недостаточно золота. Нужно: {gold_cost} 🪙"}

        async for db in get_db():
            result = await db.execute(
                text("SELECT id, name, danger_level, food_supply, population FROM locations WHERE id = :lid OR location_id = :lid"),
                {"lid": location_id},
            )
            loc = result.mappings().first()
            if not loc:
                return {"success": False, "message": "Локация не найдена."}

            new_danger = max(0, loc["danger_level"] - condition_gain)
            await db.execute(
                text("UPDATE locations SET danger_level = :d WHERE id = :id"),
                {"d": new_danger, "id": loc["id"]},
            )
            await db.execute(
                update(UserModel)
                .where(UserModel.user_id == user_id)
                .values(gold=user["gold"] - gold_cost)
            )
            await db.commit()

        material_names = {"wood": "дерево", "stone": "камень", "iron": "железо"}
        await self.chronicle.publish(
            EventType.LEGEND_DISCOVERED,
            f"🏗 Локация «{loc['name']}» восстановлена ({material_names.get(material, material)}). Опасность: -{condition_gain}",
            player_id=user_id,
            importance=Importance.COMMON,
        )

        return {
            "success": True,
            "message": f"🏗 «{loc['name']}» восстановлена! Опасность: {new_danger}. Потрачено: {gold_cost} 🪙",
            "danger_level": new_danger,
            "gold_spent": gold_cost,
        }
