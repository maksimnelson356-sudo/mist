from database.base import get_db
from database.repositories.exploration_repo import ExplorationRepository
from domain.events import EventType, Importance


DISCOVERY_XP = 50
DISCOVERY_REPUTATION = 5
VISIT_XP = 5


class ExplorationService:

    def __init__(self, chronicle, player_service):
        self.chronicle = chronicle
        self.player = player_service

    async def discover(self, user_id: int, location_id: str) -> dict:
        user = await self.player.get(user_id)
        if not user:
            return {"success": False, "message": "Пользователь не найден."}

        async for db in get_db():
            existing = await ExplorationRepository.get(db, user_id, location_id)
            break

        is_first = existing is None or not existing.get("first_discovered", False)

        async for db in get_db():
            record = await ExplorationRepository.discover(db, user_id, location_id)
            break

        if is_first:
            await self.player.update(user_id, xp=user["xp"] + DISCOVERY_XP)
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
                "xp_gained": DISCOVERY_XP,
                "visited_count": record.get("visited_count", 1),
                "message": f"Открыта новая локация! +{DISCOVERY_XP} XP",
            }

        return {
            "success": True,
            "first_discover": False,
            "xp_gained": VISIT_XP,
            "visited_count": record.get("visited_count", 1),
            "message": "Ты уже был здесь.",
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
