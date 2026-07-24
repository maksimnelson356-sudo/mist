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
        }
