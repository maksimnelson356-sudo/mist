import json
import logging
import random
from collections import deque

from sqlalchemy import select, update

from database.base import get_db
from database.models.user import UserModel
from database.models.location import LocationModel
from database.models.creature import CreatureModel
from domain.events import EventType, Importance

logger = logging.getLogger("MIST.movement")
from database.models.item import GroundItemModel
from database.models.inventory import InventoryModel
from database.models.poi import POIModel
from domain.events import EventType, Importance


class MovementService:

    def __init__(self, chronicle, user_service):
        self.chronicle = chronicle
        self.user_service = user_service

    async def get_location(self, location_id: str) -> dict | None:
        async for db in get_db():
            stmt = select(LocationModel).where(LocationModel.location_id == location_id)
            result = await db.execute(stmt)
            loc = result.scalar_one_or_none()
            return self._to_dict(loc) if loc else None
        return None

    async def get_location_name(self, location_id: str) -> str:
        loc = await self.get_location(location_id)
        return loc["name"] if loc else location_id

    async def move(self, user_id: int, target_location: str) -> dict:
        async for db in get_db():
            user = await self.user_service.get(user_id)
            if not user:
                return {"success": False, "message": "Пользователь не найден."}

            stmt = select(LocationModel).where(LocationModel.location_id == target_location)
            result = await db.execute(stmt)
            loc = result.scalar_one_or_none()

            if not loc:
                return {"success": False, "message": "Эта область не существует... или ещё не открыта."}

            if loc.is_secret:
                if loc.discovered_by and loc.discovered_by != user_id:
                    if user["karma"] < (loc.required_karma or 0):
                        return {"success": False, "message": "Туман не пускает тебя дальше..."}
                elif not loc.discovered_by:
                    if user["karma"] < (loc.required_karma or 0):
                        return {"success": False, "message": "Туман не пускает тебя дальше..."}

            connections = loc.connections if isinstance(loc.connections, list) else []
            if user["current_location"] not in connections:
                return {"success": False, "message": "Ты не можешь попасть отсюда напрямую."}

            night_encounter = False
            weather_mod = {}
            try:
                from services.container import services as _svc
                world_state = _svc.world_engine.get_state()
                game_hour = world_state["game_hour"] if world_state else 8
                is_night = game_hour >= 23 or game_hour <= 5

                loc_weather = loc.current_weather or "clear"
                from services.weather_system import WEATHER_EFFECTS
                weather_mod = WEATHER_EFFECTS.get(loc_weather, WEATHER_EFFECTS["clear"])

                encounter_roll = weather_mod.get("encounter_chance", 0.0)
                if is_night:
                    encounter_roll += 0.15

                if random.random() < encounter_roll:
                    night_encounter = True
            except Exception as e:
                logger.warning(f"Weather/night encounter check error: {e}", exc_info=True)

            hunger_cost = 5 + weather_mod.get("movement_hunger_cost", 0)
            current_hunger = user.get("hunger", 100)
            new_hunger = max(0, current_hunger - hunger_cost)
            await db.execute(
                update(UserModel)
                .where(UserModel.user_id == user_id)
                .values(current_location=target_location, hunger=new_hunger)
            )
            await db.commit()

            first_discover = False
            if not loc.discovered:
                await db.execute(
                    update(LocationModel)
                    .where(LocationModel.location_id == target_location)
                    .values(discovered=True, discovered_by=user_id)
                )
                await db.commit()
                first_discover = True
                await self.chronicle.publish(
                    EventType.LOCATION_DISCOVERED,
                    f"Открыта новая локация: {loc.name}",
                    player_id=user_id,
                    region_id=target_location,
                    importance=Importance.NOTABLE,
                    description=loc.description,
                )

            if not first_discover:
                await self.chronicle.publish(
                    EventType.LOCATION_VISITED,
                    f"Путешествие в {loc.name}",
                    player_id=user_id,
                    region_id=target_location,
                    importance=Importance.TRIVIAL,
                )

            return {
                "success": True,
                "first_discover": first_discover,
                "name": loc.name,
                "description": loc.description,
                "message": f"Ты прибыл в «{loc.name}».",
                "night_encounter": night_encounter,
                "weather": loc.current_weather or "clear",
                "hunger_cost": hunger_cost,
            }
        return {"success": False, "message": "Ошибка базы данных."}

    async def get_creatures_at(self, location_id: str) -> list:
        async for db in get_db():
            stmt = select(CreatureModel).where(
                CreatureModel.location == location_id,
                CreatureModel.is_alive == True,
            )
            result = await db.execute(stmt)
            rows = result.scalars().all()

            if not rows:
                stmt_dead = select(CreatureModel).where(
                    CreatureModel.location == location_id,
                    CreatureModel.is_alive == False,
                )
                result_dead = await db.execute(stmt_dead)
                dead = result_dead.scalars().all()
                for d in dead:
                    if random.random() < 0.4:
                        d.is_alive = True
                        d.hp = d.max_hp
                if dead:
                    await db.commit()

                stmt_alive = select(CreatureModel).where(
                    CreatureModel.location == location_id,
                    CreatureModel.is_alive == True,
                )
                result_alive = await db.execute(stmt_alive)
                rows = result_alive.scalars().all()

            return [self._creature_to_dict(r) for r in rows]
        return []

    async def get_ground_items(self, location_id: str) -> list:
        async for db in get_db():
            stmt = select(GroundItemModel).where(GroundItemModel.location_id == location_id)
            result = await db.execute(stmt)
            rows = result.scalars().all()
            return [
                {"id": r.id, "item_id": r.item_id, "location_id": r.location_id, "quantity": r.quantity}
                for r in rows
            ]
        return []

    async def pick_up_item(self, user_id: int, location_id: str, item_id: str) -> dict:
        async for db in get_db():
            user = await self.user_service.get(user_id)
            if not user:
                return {"success": False, "message": "Пользователь не найден."}
            if user["current_location"] != location_id:
                return {"success": False, "message": "Ты не на этой локации."}

            stmt = select(GroundItemModel).where(
                GroundItemModel.location_id == location_id,
                GroundItemModel.item_id == item_id,
            )
            result = await db.execute(stmt)
            item = result.scalar_one_or_none()

            if not item:
                return {"success": False, "message": "Этого предмета здесь нет."}

            inv_stmt = select(InventoryModel).where(
                InventoryModel.user_id == user_id,
                InventoryModel.item_id == item_id,
                InventoryModel.is_magic == False,
            )
            inv_result = await db.execute(inv_stmt)
            existing = inv_result.scalar_one_or_none()

            if existing:
                existing.quantity += item.quantity
            else:
                db.add(InventoryModel(
                    user_id=user_id,
                    item_id=item_id,
                    quantity=item.quantity,
                ))

            await db.delete(item)
            await db.commit()

            await self.chronicle.publish(
                EventType.ITEM_OBTAINED,
                f"Подобран предмет: {item_id} x{item.quantity}",
                player_id=user_id,
                region_id=location_id,
                importance=Importance.TRIVIAL,
            )

            return {"success": True, "message": f"Подобрал: {item_id} x{item.quantity}"}
        return {"success": False, "message": "Ошибка базы данных."}

    async def find_next_step(self, from_loc: str, to_loc: str) -> str | None:
        if from_loc == to_loc:
            return None

        async for db in get_db():
            stmt = select(LocationModel.location_id, LocationModel.connections)
            result = await db.execute(stmt)
            rows = result.all()

            graph = {}
            for row in rows:
                conns = row.connections if isinstance(row.connections, list) else []
                graph[row.location_id] = conns

            visited = {from_loc}
            queue = deque([(from_loc, [])])

            while queue:
                current, path = queue.popleft()
                for neighbor in graph.get(current, []):
                    if neighbor == to_loc:
                        return path[0] if path else neighbor
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
            return None
        return None

    async def talk_to_creature(self, user_id: int, creature_id: str) -> dict:
        async for db in get_db():
            from database.models.creature import CreatureModel as CM
            stmt = select(CM).where(CM.creature_id == creature_id)
            result = await db.execute(stmt)
            row = result.scalar_one_or_none()
            if not row:
                return {"message": "Существо не найдено."}

            memory_raw = {}
            if row.memory_with_users:
                try:
                    import json as _j
                    memory_raw = _j.loads(row.memory_with_users) if isinstance(row.memory_with_users, str) else row.memory_with_users
                except Exception as e:
                    logger.warning(f"NPC memory JSON parse error: {e}", exc_info=True)
                    memory_raw = {}

            uid_str = str(user_id)
            user_memories = memory_raw.get(uid_str, [])

            lines = [f"🗣 <b>{row.name}</b>\n"]

            if row.disposition == "friendly":
                lines.append(row.description or "Он дружелюбен.")
                if user_memories:
                    lines.append("\n<i>Он помнит тебя...</i>")
                else:
                    lines.append("\n<i>Он видит тебя впервые.</i>")
            elif row.disposition == "neutral":
                lines.append(row.description or "Он осторожен.")
                if user_memories:
                    killed = any(m.get("action") == "killed_by" for m in user_memories)
                    if killed:
                        lines.append("\n<i>Он помнит, что ты его убивал. Он настороже.</i>")
                    else:
                        lines.append("\n<i>Он что-то помнит о тебе...</i>")
                else:
                    lines.append("\n<i>Он смотрит на тебя с любопытством.</i>")
            else:
                lines.append(row.description or "Он враждебен.")
                lines.append("\n<i>Разговаривать с ним бесполезно.</i>")

            return {"message": "\n".join(lines)}
        return {"message": "Ошибка базы данных."}

    @staticmethod
    def _to_dict(row: LocationModel) -> dict:
        return {
            "id": row.id,
            "location_id": row.location_id,
            "name": row.name,
            "description": row.description,
            "region_id": row.region_id,
            "x": row.x,
            "y": row.y,
            "z": row.z,
            "discovered": row.discovered,
            "discovered_by": row.discovered_by,
            "discovered_at": row.discovered_at,
            "connections": row.connections if isinstance(row.connections, list) else [],
            "state_data": row.state_data if isinstance(row.state_data, dict) else {},
            "current_weather": row.current_weather or "clear",
            "is_secret": row.is_secret,
            "required_karma": row.required_karma,
        }

    @staticmethod
    def _creature_to_dict(row: CreatureModel) -> dict:
        return {
            "id": row.id,
            "creature_id": row.creature_id,
            "name": row.name,
            "description": row.description,
            "location": row.location,
            "disposition": row.disposition,
            "is_alive": row.is_alive,
            "hp": row.hp,
            "max_hp": row.max_hp,
            "attack": row.attack,
            "defense": row.defense,
            "xp_reward": row.xp_reward,
            "spawn_data": json.loads(row.spawn_data) if isinstance(row.spawn_data, str) else row.spawn_data,
            "loot_table": json.loads(row.loot_table) if isinstance(row.loot_table, str) else row.loot_table,
        }
