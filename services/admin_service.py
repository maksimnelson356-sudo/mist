from config import ADMIN_IDS


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


class AdminService:

    def __init__(self, chronicle, player):
        self.chronicle = chronicle
        self.player = player

    async def get_player_info(self, user_id: int) -> dict | None:
        return await self.player.get(user_id)

    async def set_level(self, user_id: int, level: int) -> dict:
        if level < 1 or level > 100:
            return {"success": False, "message": "Уровень должен быть 1-100."}
        from database.base import get_db
        from database.models.user import UserModel
        from sqlalchemy import update
        async for db in get_db():
            await db.execute(
                update(UserModel).where(UserModel.user_id == user_id).values(level=level)
            )
            await db.commit()
            return {"success": True, "message": f"Уровень #{user_id} установлен на {level}."}
        return {"success": False, "message": "Ошибка БД."}

    async def set_gold(self, user_id: int, amount: int) -> dict:
        if amount < 0:
            return {"success": False, "message": "Золото не может быть отрицательным."}
        from database.base import get_db
        from database.models.user import UserModel
        from sqlalchemy import update
        async for db in get_db():
            await db.execute(
                update(UserModel).where(UserModel.user_id == user_id).values(gold=amount)
            )
            await db.commit()
            return {"success": True, "message": f"Золото #{user_id} установлено на {amount}."}
        return {"success": False, "message": "Ошибка БД."}

    async def revive_player(self, user_id: int) -> dict:
        from database.base import get_db
        from database.models.user import UserModel
        from sqlalchemy import update
        async for db in get_db():
            user = await self.player.get(user_id)
            if not user:
                return {"success": False, "message": "Игрок не найден."}
            await db.execute(
                update(UserModel).where(UserModel.user_id == user_id).values(
                    is_alive=True, hp=user.get("max_hp", 100)
                )
            )
            await db.commit()
            return {"success": True, "message": f"Игрок #{user_id} воскрешён."}
        return {"success": False, "message": "Ошибка БД."}

    async def teleport(self, user_id: int, location_id: str) -> dict:
        from database.base import get_db
        from database.models.user import UserModel
        from sqlalchemy import update
        async for db in get_db():
            await db.execute(
                update(UserModel).where(UserModel.user_id == user_id).values(current_location=location_id)
            )
            await db.commit()
            return {"success": True, "message": f"Игрок #{user_id} телепортирован в {location_id}."}
        return {"success": False, "message": "Ошибка БД."}
