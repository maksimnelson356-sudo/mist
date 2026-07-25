from sqlalchemy import select, update
from sqlalchemy.sql import func

from database.base import get_db
from database.models.user import UserModel
from domain.events import EventType, Importance


class PlayerService:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def get_or_create(self, user_id: int, username: str = None) -> dict:
        async for db in get_db():
            stmt = select(UserModel).where(UserModel.user_id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                display_name = username or f"Путник_{user_id % 10000}"
                user = UserModel(
                    user_id=user_id,
                    username=username,
                    display_name=display_name,
                )
                db.add(user)
                await db.commit()
                await self.chronicle.publish(
                    EventType.NEW_USER,
                    f"Новый путник: {display_name}",
                    player_id=user_id,
                    importance=Importance.TRIVIAL,
                )

            return self._to_dict(user)
        return {}

    async def get(self, user_id: int) -> dict | None:
        async for db in get_db():
            stmt = select(UserModel).where(UserModel.user_id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            return self._to_dict(user) if user else None
        return None

    async def update(self, user_id: int, **kwargs):
        async for db in get_db():
            stmt = select(UserModel).where(UserModel.user_id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                for key, val in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, val)
                await db.commit()
            break

    async def update_last_seen(self, user_id: int):
        async for db in get_db():
            stmt = update(UserModel).where(UserModel.user_id == user_id).values(
                last_seen=func.now()
            )
            await db.execute(stmt)
            await db.commit()
            break

    async def get_catchup_summary(self, user_id: int) -> dict | None:
        user = await self.get(user_id)
        if not user or not user.get("last_seen"):
            return None

        from services.world_engine import WorldEngine
        async for db in get_db():
            result = await db.execute(
                select(UserModel).where(UserModel.user_id == user_id)
            )
            db_user = result.scalar_one_or_none()
            if not db_user:
                return None

            last_seen = db_user.last_seen
            if last_seen is None:
                return None

            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            diff = now - last_seen
            hours_away = diff.total_seconds() / 3600

            if hours_away < 24:
                return None

            game_days_away = max(1, int(hours_away / 24))

            result = await db.execute(
                text("SELECT game_day, season, world_pressure, prosperity, chaos "
                     "FROM world_state LIMIT 1")
            )
            world = result.mappings().first()
            if not world:
                return None

            result = await db.execute(
                text("SELECT name, description, region_id, start_day "
                     "FROM world_event_records "
                     "WHERE start_day > :start_day AND start_day <= :current_day "
                     "ORDER BY start_day LIMIT 10"),
                {"start_day": world["game_day"] - game_days_away, "current_day": world["game_day"]},
            )
            events = [dict(row) for row in result.mappings().all()]

            result = await db.execute(
                text("SELECT name, danger_level, food_supply, current_weather "
                     "FROM locations WHERE id = :loc_id"),
                {"loc_id": user["current_location"]},
            )
            loc = result.mappings().first()

            return {
                "hours_away": int(hours_away),
                "game_days_away": game_days_away,
                "world_day": world["game_day"],
                "season": world["season"],
                "world_pressure": world["world_pressure"],
                "events": events,
                "location": dict(loc) if loc else None,
            }

    async def revive(self, user_id: int) -> dict:
        async for db in get_db():
            stmt = select(UserModel).where(UserModel.user_id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                return {"success": False, "message": "Пользователь не найден."}
            if user.is_alive:
                return {"success": False, "message": "Ты уже жив."}

            new_hp = max(1, user.max_hp // 2)
            await db.execute(
                update(UserModel).where(UserModel.user_id == user_id).values(
                    is_alive=True, hp=new_hp,
                )
            )
            await db.commit()

            await self.chronicle.publish(
                EventType.PLAYER_REVIVED,
                f"{user.display_name} очнулся",
                player_id=user_id,
                importance=Importance.COMMON,
            )

            return {
                "success": True,
                "message": f"✨ Ты очнулся...\n\n❤️ HP: {new_hp}/{user.max_hp}",
            }
        return {"success": False, "message": "Ошибка базы данных."}

    async def rest_heal(self, user_id: int) -> dict:
        async for db in get_db():
            stmt = select(UserModel).where(UserModel.user_id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                return {"success": False, "message": "Пользователь не найден."}

            heal = max(1, user.max_hp // 10)
            new_hp = min(user.max_hp, user.hp + heal)

            await db.execute(
                update(UserModel).where(UserModel.user_id == user_id).values(hp=new_hp)
            )
            await db.commit()

            return {
                "success": True,
                "message": f"💚 Ты отдохнул и восстановил {new_hp - user.hp} HP.\n❤️ HP: {new_hp}/{user.max_hp}",
            }
        return {"success": False, "message": "Ошибка базы данных."}

    async def decrease_hunger(self, user_id: int, amount: int = 5) -> dict:
        async for db in get_db():
            stmt = select(UserModel).where(UserModel.user_id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                return {"success": False, "message": "Игрок не найден."}

            new_hunger = max(0, user.hunger - amount)
            await db.execute(
                update(UserModel).where(UserModel.user_id == user_id).values(hunger=new_hunger)
            )
            await db.commit()

            msg = ""
            if new_hunger <= 0:
                msg = "\n🍖 Ты очень голоден! -20% атаки!"
            elif new_hunger < 20:
                msg = "\n🍖 Голод нарастает..."
            return {"success": True, "hunger": new_hunger, "message": msg}
        return {"success": False, "message": "Ошибка базы данных."}

    async def feed(self, user_id: int, amount: int = 30) -> dict:
        async for db in get_db():
            stmt = select(UserModel).where(UserModel.user_id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                return {"success": False, "message": "Игрок не найден."}

            new_hunger = min(user.max_hunger, user.hunger + amount)
            restored = new_hunger - user.hunger
            await db.execute(
                update(UserModel).where(UserModel.user_id == user_id).values(hunger=new_hunger)
            )
            await db.commit()
            return {"success": True, "hunger": new_hunger, "message": f"🍖 +{restored} сытости."}
        return {"success": False, "message": "Ошибка базы данных."}

    @staticmethod
    def _to_dict(row: UserModel) -> dict:
        return {
            "user_id": row.user_id,
            "username": row.username,
            "display_name": row.display_name,
            "created_at": row.created_at,
            "last_seen": row.last_seen,
            "current_location": row.current_location,
            "memories": row.memories,
            "karma": row.karma,
            "reputation": row.reputation,
            "days_in_mist": row.days_in_mist,
            "is_alive": row.is_alive,
            "hp": row.hp,
            "max_hp": row.max_hp,
            "attack": row.attack,
            "defense": row.defense,
            "level": row.level,
            "xp": row.xp,
            "gold": row.gold,
            "pvp_wins": row.pvp_wins,
            "pvp_losses": row.pvp_losses,
            "pvp_rating": row.pvp_rating,
            "hunger": row.hunger,
            "max_hunger": row.max_hunger,
        }
