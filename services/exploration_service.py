import logging
import random

from database.base import get_db
from database.repositories.exploration_repo import ExplorationRepository
from domain.events import EventType, Importance

logger = logging.getLogger("MIST.exploration")

DISCOVERY_XP = 50
DISCOVERY_REPUTATION = 5
VISIT_XP = 5


class ExplorationService:

    def __init__(self, chronicle, player_service):
        self.chronicle = chronicle
        self.player = player_service

    async def _get_weather_modifiers(self, location_id: str) -> dict:
        try:
            from sqlalchemy import text
            async for db in get_db():
                result = await db.execute(
                    text("SELECT current_weather, danger_level, tree_density, food_supply FROM locations WHERE id = :lid OR location_id = :lid"),
                    {"lid": location_id},
                )
                row = result.mappings().first()
                if not row:
                    return {}

                from services.weather_system import WEATHER_EFFECTS
                weather = row.get("current_weather", "clear")
                weather_fx = WEATHER_EFFECTS.get(weather, WEATHER_EFFECTS["clear"])

                danger = row.get("danger_level", 30)
                return {
                    "weather": weather,
                    "xp_modifier": 1.0 + (weather_fx.get("xp_bonus", 0) / 100),
                    "risk_chance": weather_fx.get("exploration_risk", 0.0) + (danger / 500),
                    "danger_level": danger,
                }
        except Exception as e:
            logger.warning(f"Weather modifier error: {e}", exc_info=True)
            return {}

    async def discover(self, user_id: int, location_id: str) -> dict:
        user = await self.player.get(user_id)
        if not user:
            return {"success": False, "message": "Пользователь не найден."}

        async for db in get_db():
            existing = await ExplorationRepository.get(db, user_id, location_id)
            break

        is_first = existing is None or not existing.get("first_discovered", False)

        mods = await self._get_weather_modifiers(location_id)
        risk_chance = mods.get("risk_chance", 0.0)
        xp_mod = mods.get("xp_modifier", 1.0)

        damage_message = ""
        if risk_chance > 0 and random.random() < risk_chance:
            damage = random.randint(5, 15)
            from services.container import services
            from sqlalchemy import update as sa_update
            from database.models.user import UserModel
            async for db in get_db():
                await db.execute(
                    sa_update(UserModel).where(UserModel.user_id == user_id).values(
                        hp=max(1, user["hp"] - damage)
                    )
                )
                await db.commit()
                break
            damage_message = f" (получил {damage} урона при исследовании)"

        async for db in get_db():
            record = await ExplorationRepository.discover(db, user_id, location_id)
            break

        if is_first:
            xp_gained = int(DISCOVERY_XP * xp_mod)
            await self.player.update(user_id, xp=user["xp"] + xp_gained)
            await self.chronicle.publish(
                EventType.LOCATION_DISCOVERED,
                f"Первое открытие: {location_id}",
                player_id=user_id,
                region_id=location_id,
                importance=Importance.NOTABLE,
            )

            return {
                "success": True,
                "first_discover": True,
                "xp_gained": xp_gained,
                "visited_count": record.get("visited_count", 1),
                "weather": mods.get("weather", "clear"),
                "damage": damage_message,
                "message": f"Открыта новая локация! +{xp_gained} XP{damage_message}",
            }

        return {
            "success": True,
            "first_discover": False,
            "xp_gained": VISIT_XP,
            "visited_count": record.get("visited_count", 1),
            "weather": mods.get("weather", "clear"),
            "damage": damage_message,
            "message": f"Ты уже был здесь.{damage_message}",
        }

    async def visit(self, user_id: int, location_id: str) -> dict:
        user = await self.player.get(user_id)
        if not user:
            return {"success": False, "message": "Пользователь не найден."}

        async for db in get_db():
            record = await ExplorationRepository.visit(db, user_id, location_id)
            break

        await self.chronicle.publish(
            EventType.LOCATION_VISITED,
            f"Посещение: {location_id} (всего: {record.get('visited_count', 1)})",
            player_id=user_id,
            region_id=location_id,
            importance=Importance.TRIVIAL,
        )

        return {
            "success": True,
            "visited_count": record.get("visited_count", 1),
            "xp_gained": VISIT_XP,
        }

    async def get_discoveries(self, user_id: int) -> list:
        async for db in get_db():
            discoveries = await ExplorationRepository.get_discoveries(db, user_id)
            break
        return discoveries

    async def get_stats(self, user_id: int) -> dict:
        async for db in get_db():
            discovery_count = await ExplorationRepository.count_discoveries(db, user_id)
            total_visits = await ExplorationRepository.count_total_visits(db, user_id)
            break

        return {
            "discovery_count": discovery_count,
            "total_visits": total_visits,
        }

    async def get_discovery_list(self, user_id: int) -> str:
        discoveries = await self.get_discoveries(user_id)

        if not discoveries:
            return "Ты ещё ничего не открыл."

        lines = [f"🗺 <b>Открытые локации: {len(discoveries)}</b>\n"]
        for d in discoveries:
            lines.append(f"  ✅ {d.get('location_id', '?')} (посещений: {d.get('visited_count', 0)})")

        return "\n".join(lines)
