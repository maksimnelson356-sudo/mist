import json
from datetime import datetime

from sqlalchemy import select, update

from database.base import get_db
from database.models.trade import PlayerTradeModel
from database.models.user import UserModel
from database.models.inventory import InventoryModel
from domain.events import EventType, Importance


class TradeService:

    def __init__(self, chronicle, user_service, inventory_service):
        self.chronicle = chronicle
        self.user_service = user_service
        self.inventory = inventory_service

    async def create(self, from_user: int, to_user: int, items_offered: list,
                     gold_offered: int, items_wanted: list, gold_wanted: int) -> dict:
        if from_user == to_user:
            return {"success": False, "message": "Нельзя торговать с самим собой."}

        async for db in get_db():
            user1 = await self.user_service.get(from_user)
            user2 = await self.user_service.get(to_user)

            if not user1 or not user2:
                return {"success": False, "message": "Пользователь не найден."}

            if user1["current_location"] != user2["current_location"]:
                return {"success": False, "message": "Вы должны быть в одной локации."}

            if user1["gold"] < gold_offered:
                return {"success": False, "message": "У тебя недостаточно золота."}

            for item in items_offered:
                has = await self.inventory.has(from_user, item["item_id"], item.get("qty", 1))
                if not has:
                    return {"success": False, "message": f"У тебя нет {item['item_id']}."}

            stmt = select(PlayerTradeModel).where(
                PlayerTradeModel.from_user == from_user,
                PlayerTradeModel.status == "pending",
            )
            result = await db.execute(stmt)
            if result.scalar_one_or_none():
                return {"success": False, "message": "У тебя уже есть активный трейд."}

            db.add(PlayerTradeModel(
                from_user=from_user,
                to_user=to_user,
                items_offered=json.dumps(items_offered),
                gold_offered=gold_offered,
                items_wanted=json.dumps(items_wanted),
                gold_wanted=gold_wanted,
            ))
            await db.commit()

            await self.chronicle.publish(
                EventType.TRADE_CREATED,
                f"Предложение трейда от {user1['display_name']}",
                player_id=from_user,
                importance=Importance.TRIVIAL,
                metadata={"to_user": to_user, "gold_offered": gold_offered},
            )

            return {"success": True, "message": "📨 Предложение трейда отправлено!"}
        return {"success": False, "message": "Ошибка базы данных."}

    async def accept(self, trade_id: int, user_id: int) -> dict:
        async for db in get_db():
            stmt = select(PlayerTradeModel).where(
                PlayerTradeModel.id == trade_id,
                PlayerTradeModel.status == "pending",
            )
            result = await db.execute(stmt)
            trade = result.scalar_one_or_none()
            if not trade:
                return {"success": False, "message": "Трейд не найден или уже закрыт."}

            if trade.to_user != user_id:
                return {"success": False, "message": "Этот трейд не для тебя."}

            user1 = await self.user_service.get(trade.from_user)
            user2 = await self.user_service.get(trade.to_user)

            if user1["current_location"] != user2["current_location"]:
                return {"success": False, "message": "Вы разошлись по локациям."}

            if user1["gold"] < trade.gold_offered:
                return {"success": False, "message": "У отправителя недостаточно золота."}

            items_offered = json.loads(trade.items_offered) if isinstance(trade.items_offered, str) else trade.items_offered
            for item in items_offered:
                has = await self.inventory.has(trade.from_user, item["item_id"], item.get("qty", 1))
                if not has:
                    return {"success": False, "message": f"У отправителя нет {item['item_id']}."}

            if user2["gold"] < trade.gold_wanted:
                return {"success": False, "message": "У тебя недостаточно золота."}

            items_wanted = json.loads(trade.items_wanted) if isinstance(trade.items_wanted, str) else trade.items_wanted
            for item in items_wanted:
                has = await self.inventory.has(trade.to_user, item["item_id"], item.get("qty", 1))
                if not has:
                    return {"success": False, "message": f"У тебя нет {item['item_id']}."}

            if trade.gold_offered > 0:
                await db.execute(
                    update(UserModel).where(UserModel.user_id == trade.from_user).values(
                        gold=user1["gold"] - trade.gold_offered
                    )
                )
                fresh2 = await self.user_service.get(trade.to_user)
                await db.execute(
                    update(UserModel).where(UserModel.user_id == trade.to_user).values(
                        gold=fresh2["gold"] + trade.gold_offered
                    )
                )

            if trade.gold_wanted > 0:
                fresh2b = await self.user_service.get(trade.to_user)
                await db.execute(
                    update(UserModel).where(UserModel.user_id == trade.to_user).values(
                        gold=fresh2b["gold"] - trade.gold_wanted
                    )
                )
                fresh1 = await self.user_service.get(trade.from_user)
                await db.execute(
                    update(UserModel).where(UserModel.user_id == trade.from_user).values(
                        gold=fresh1["gold"] + trade.gold_wanted
                    )
                )

            for item in items_offered:
                await self.inventory.remove(trade.from_user, item["item_id"], item.get("qty", 1))
                await self.inventory.add(trade.to_user, item["item_id"], item.get("qty", 1))

            for item in items_wanted:
                await self.inventory.remove(trade.to_user, item["item_id"], item.get("qty", 1))
                await self.inventory.add(trade.from_user, item["item_id"], item.get("qty", 1))

            trade.status = "completed"
            trade.completed_at = datetime.utcnow()
            await db.commit()

            await self.chronicle.publish(
                EventType.TRADE_COMPLETED,
                "Трейд завершён",
                player_id=user_id,
                importance=Importance.COMMON,
                metadata={"trade_id": trade_id},
            )

            return {"success": True, "message": "🤝 Трейд завершён!"}
        return {"success": False, "message": "Ошибка базы данных."}

    async def decline(self, trade_id: int, user_id: int) -> dict:
        async for db in get_db():
            stmt = select(PlayerTradeModel).where(
                PlayerTradeModel.id == trade_id,
                PlayerTradeModel.status == "pending",
            )
            result = await db.execute(stmt)
            trade = result.scalar_one_or_none()
            if not trade:
                return {"success": False, "message": "Трейд не найден."}

            if trade.to_user != user_id and trade.from_user != user_id:
                return {"success": False, "message": "Не твой трейд."}

            trade.status = "declined"
            await db.commit()

            return {"success": True, "message": "❌ Трейд отклонён."}
        return {"success": False, "message": "Ошибка базы данных."}

    async def cancel(self, trade_id: int, user_id: int) -> dict:
        async for db in get_db():
            stmt = select(PlayerTradeModel).where(
                PlayerTradeModel.id == trade_id,
                PlayerTradeModel.status == "pending",
            )
            result = await db.execute(stmt)
            trade = result.scalar_one_or_none()
            if not trade:
                return {"success": False, "message": "Трейд не найден."}

            if trade.from_user != user_id:
                return {"success": False, "message": "Только отправитель может отменить трейд."}

            trade.status = "cancelled"
            await db.commit()

            return {"success": True, "message": "🚫 Трейд отменён."}
        return {"success": False, "message": "Ошибка базы данных."}

    async def get_pending(self, user_id: int) -> list:
        async for db in get_db():
            stmt = (
                select(PlayerTradeModel, UserModel)
                .join(UserModel, PlayerTradeModel.from_user == UserModel.user_id)
                .where(
                    PlayerTradeModel.to_user == user_id,
                    PlayerTradeModel.status == "pending",
                )
                .order_by(PlayerTradeModel.created_at.desc())
            )
            result = await db.execute(stmt)
            rows = result.all()
            trades = []
            for trade, user in rows:
                trades.append({
                    "id": trade.id,
                    "from_user": trade.from_user,
                    "to_user": trade.to_user,
                    "items_offered": json.loads(trade.items_offered) if isinstance(trade.items_offered, str) else trade.items_offered,
                    "gold_offered": trade.gold_offered,
                    "items_wanted": json.loads(trade.items_wanted) if isinstance(trade.items_wanted, str) else trade.items_wanted,
                    "gold_wanted": trade.gold_wanted,
                    "status": trade.status,
                    "created_at": trade.created_at,
                    "from_name": user.display_name,
                })
            return trades
        return []
