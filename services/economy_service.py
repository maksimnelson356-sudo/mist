from sqlalchemy import select, update

from database.base import get_db
from database.models.user import UserModel
from domain.events import EventType, Importance


VALID_CURRENCIES = ("gold", "gems", "tokens")


class EconomyService:

    def __init__(self, chronicle, player_service):
        self.chronicle = chronicle
        self.player = player_service

    async def get_balance(self, user_id: int) -> dict:
        user = await self.player.get(user_id)
        if not user:
            return {"gold": 0, "gems": 0, "tokens": 0}
        return {
            "gold": user.get("gold", 0),
            "gems": user.get("gems", 0),
            "tokens": user.get("tokens", 0),
        }

    async def add(self, user_id: int, currency: str, amount: int) -> dict:
        if currency not in VALID_CURRENCIES:
            return {"success": False, "message": f"Неизвестная валюта: {currency}"}
        if amount <= 0:
            return {"success": False, "message": "Сумма должна быть больше 0."}

        async for db in get_db():
            user = await self.player.get(user_id)
            if not user:
                return {"success": False, "message": "Игрок не найден."}

            current = user.get(currency, 0)
            await db.execute(
                update(UserModel).where(UserModel.user_id == user_id).values(
                    **{currency: current + amount}
                )
            )
            await db.commit()

            await self.chronicle.publish(
                EventType.ECONOMY_TRANSACTION,
                f"+{amount} {currency} игроку #{user_id}",
                player_id=user_id,
                importance=Importance.TRIVIAL,
                metadata={"action": "add", "currency": currency, "amount": amount},
            )

            return {"success": True, "message": f"+{amount} {currency}"}
        return {"success": False, "message": "Ошибка базы данных."}

    async def remove(self, user_id: int, currency: str, amount: int) -> dict:
        if currency not in VALID_CURRENCIES:
            return {"success": False, "message": f"Неизвестная валюта: {currency}"}
        if amount <= 0:
            return {"success": False, "message": "Сумма должна быть больше 0."}

        async for db in get_db():
            user = await self.player.get(user_id)
            if not user:
                return {"success": False, "message": "Игрок не найден."}

            current = user.get(currency, 0)
            if current < amount:
                return {"success": False, "message": f"Недостаточно {currency}."}

            await db.execute(
                update(UserModel).where(UserModel.user_id == user_id).values(
                    **{currency: current - amount}
                )
            )
            await db.commit()

            await self.chronicle.publish(
                EventType.ECONOMY_TRANSACTION,
                f"-{amount} {currency} у игрока #{user_id}",
                player_id=user_id,
                importance=Importance.TRIVIAL,
                metadata={"action": "remove", "currency": currency, "amount": amount},
            )

            return {"success": True, "message": f"-{amount} {currency}"}
        return {"success": False, "message": "Ошибка базы данных."}

    async def transfer(self, from_user: int, to_user: int, currency: str, amount: int) -> dict:
        if currency not in VALID_CURRENCIES:
            return {"success": False, "message": f"Неизвестная валюта: {currency}"}
        if amount <= 0:
            return {"success": False, "message": "Сумма должна быть больше 0."}
        if from_user == to_user:
            return {"success": False, "message": "Нельзя переводить самому себе."}

        async for db in get_db():
            sender = await self.player.get(from_user)
            if not sender:
                return {"success": False, "message": "Отправитель не найден."}

            receiver = await self.player.get(to_user)
            if not receiver:
                return {"success": False, "message": "Получатель не найден."}

            sender_balance = sender.get(currency, 0)
            if sender_balance < amount:
                return {"success": False, "message": f"Недостаточно {currency}."}

            receiver_balance = receiver.get(currency, 0)

            await db.execute(
                update(UserModel).where(UserModel.user_id == from_user).values(
                    **{currency: sender_balance - amount}
                )
            )
            await db.execute(
                update(UserModel).where(UserModel.user_id == to_user).values(
                    **{currency: receiver_balance + amount}
                )
            )
            await db.commit()

            await self.chronicle.publish(
                EventType.ECONOMY_TRANSACTION,
                f"Перевод {amount} {currency}: #{from_user} → #{to_user}",
                player_id=from_user,
                importance=Importance.COMMON,
                metadata={"action": "transfer", "currency": currency, "amount": amount, "to_user": to_user},
            )

            return {"success": True, "message": f"Переведено {amount} {currency}"}
        return {"success": False, "message": "Ошибка базы данных."}

    async def can_afford(self, user_id: int, currency: str, amount: int) -> bool:
        if currency not in VALID_CURRENCIES:
            return False
        user = await self.player.get(user_id)
        if not user:
            return False
        return user.get(currency, 0) >= amount
