from sqlalchemy import update

from database.base import get_db
from database.models.user import UserModel
from domain.events import EventType, Importance

REPUTATION_LEVELS = [
    (-100, -51, "Враг", "NPC атакуют первыми"),
    (-50, -1, "Подозрительный", "Нет доступа к светлым локациям"),
    (0, 49, "Нейтральный", "Базовый доступ"),
    (50, 99, "Доброжелательный", "Скидки в магазинах"),
    (100, 999, "Герой", "Уникальные квесты и предметы"),
]


class ReputationService:

    def __init__(self, chronicle, player):
        self.chronicle = chronicle
        self.player = player

    async def add(self, user_id: int, amount: int, reason: str = "") -> dict:
        if amount <= 0:
            return {"success": False, "message": "Количество должно быть положительным."}

        user = await self.player.get(user_id)
        if not user:
            return {"success": False, "message": "Пользователь не найден."}

        old_rep = user.get("reputation", 0)
        new_rep = old_rep + amount

        async for db in get_db():
            await db.execute(
                update(UserModel).where(UserModel.user_id == user_id).values(
                    reputation=new_rep
                )
            )
            await db.commit()
            break

        old_level = self._get_level_name(old_rep)
        new_level = self._get_level_name(new_rep)

        message = f"⭐ Репутация +{amount} → {new_rep}"
        if reason:
            message += f"\n💬 {reason}"
        if old_level != new_level:
            message += f"\n🎉 Новый уровень: {new_level}!"

        await self.chronicle.publish(
            EventType.REPUTATION_CHANGED,
            f"{user['display_name']}: репутация {old_rep} → {new_rep} ({reason})",
            player_id=user_id,
            importance=Importance.COMMON,
        )

        return {"success": True, "message": message, "new_reputation": new_rep}

    async def remove(self, user_id: int, amount: int, reason: str = "") -> dict:
        if amount <= 0:
            return {"success": False, "message": "Количество должно быть положительным."}

        user = await self.player.get(user_id)
        if not user:
            return {"success": False, "message": "Пользователь не найден."}

        old_rep = user.get("reputation", 0)
        new_rep = max(-100, old_rep - amount)

        async for db in get_db():
            await db.execute(
                update(UserModel).where(UserModel.user_id == user_id).values(
                    reputation=new_rep
                )
            )
            await db.commit()
            break

        old_level = self._get_level_name(old_rep)
        new_level = self._get_level_name(new_rep)

        message = f"⭐ Репутация -{amount} → {new_rep}"
        if reason:
            message += f"\n💬 {reason}"
        if old_level != new_level:
            message += f"\n⚠️ Понижение уровня: {new_level}!"

        await self.chronicle.publish(
            EventType.REPUTATION_CHANGED,
            f"{user['display_name']}: репутация {old_rep} → {new_rep} ({reason})",
            player_id=user_id,
            importance=Importance.COMMON,
        )

        return {"success": True, "message": message, "new_reputation": new_rep}

    async def get(self, user_id: int) -> dict:
        user = await self.player.get(user_id)
        if not user:
            return {"reputation": 0, "level": "Нейтральный", "description": ""}

        rep = user.get("reputation", 0)
        level_name, description = self._get_level(rep)

        return {
            "reputation": rep,
            "level": level_name,
            "description": description,
        }

    def get_level(self, reputation: int) -> str:
        return self._get_level_name(reputation)

    def _get_level(self, reputation: int) -> tuple[str, str]:
        for min_rep, max_rep, name, desc in REPUTATION_LEVELS:
            if min_rep <= reputation <= max_rep:
                return name, desc
        return "Нейтральный", "Базовый доступ"

    def _get_level_name(self, reputation: int) -> str:
        for min_rep, max_rep, name, _ in REPUTATION_LEVELS:
            if min_rep <= reputation <= max_rep:
                return name
        return "Нейтральный"
