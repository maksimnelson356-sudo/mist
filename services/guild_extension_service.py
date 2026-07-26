import logging
import random

from sqlalchemy import select, update

from database.base import get_db
from database.models.guild import GuildMemberModel, GuildModel, GuildQuestModel, GuildStorageModel
from database.models.user import UserModel
from domain.events import EventType, Importance

logger = logging.getLogger("MIST.guild_ext")

GUILD_QUESTS = [
    {"id": "guild_gather_wood", "name": "Сбор древесины", "description": "Собери 50 древесины для гильдии.",
     "objective": {"type": "collect", "item": "wood", "target": 50}, "rewards": {"xp": 100, "gold": 50, "guild_xp": 50}},
    {"id": "guild_hunt_wolves", "name": "Охота на волков", "description": "Убей 10 волков.",
     "objective": {"type": "kill", "creature": "wolf", "target": 10}, "rewards": {"xp": 80, "gold": 40, "guild_xp": 40}},
    {"id": "guild_deliver", "name": "Доставка", "description": "Доставь товар в другую локацию.",
     "objective": {"type": "visit", "location": "market_square", "target": 1}, "rewards": {"xp": 60, "gold": 30, "guild_xp": 30}},
    {"id": "guild_defend", "name": "Защита территории", "description": "Победи 5 врагов на территории гильдии.",
     "objective": {"type": "kill", "creature": "any", "target": 5}, "rewards": {"xp": 120, "gold": 60, "guild_xp": 60}},
    {"id": "guild_craft", "name": "Крафт для гильдии", "description": "Создай 3 предмета.",
     "objective": {"type": "craft", "target": 3}, "rewards": {"xp": 90, "gold": 45, "guild_xp": 45}},
    {"id": "guild_explore", "name": "Исследование", "description": "Исследуй 3 новые локации.",
     "objective": {"type": "explore", "target": 3}, "rewards": {"xp": 70, "gold": 35, "guild_xp": 35}},
    {"id": "guild_fish", "name": "Рыбалка", "description": "Поймай 10 рыб.",
     "objective": {"type": "collect", "item": "fish", "target": 10}, "rewards": {"xp": 50, "gold": 25, "guild_xp": 25}},
    {"id": "guild_donate_gold", "name": "Пожертвование", "description": "Пожертвуй 100 золота в казну.",
     "objective": {"type": "donate", "target": 100}, "rewards": {"xp": 40, "gold": 0, "guild_xp": 80}},
]

GUILD_STORAGE_LIMIT = 50
GUILD_BANK_LIMIT = 10000


class GuildExtensionService:

    def __init__(self, chronicle, player):
        self.chronicle = chronicle
        self.player = player

    async def deposit_item(self, user_id: int, item_id: str, quantity: int = 1) -> dict:
        guild = await self._get_user_guild(user_id)
        if not guild:
            return {"success": False, "message": "Ты не в гильдии."}

        storage = await self._get_storage(guild["guild_id"])
        if len(storage) >= GUILD_STORAGE_LIMIT:
            return {"success": False, "message": "Склад полон."}

        existing = next((s for s in storage if s["item_id"] == item_id), None)
        async for db in get_db():
            if existing:
                existing.quantity += quantity
            else:
                db.add(GuildStorageModel(
                    guild_id=guild["guild_id"],
                    item_id=item_id,
                    quantity=quantity,
                    deposited_by=user_id,
                ))
            await db.commit()

        await self.chronicle.publish(
            EventType.GUILD_DONATED,
            f"Предмет добавлен на склад: {item_id} x{quantity}",
            player_id=user_id,
            importance=Importance.TRIVIAL,
        )

        return {"success": True, "message": f"📦 Добавлено на склад: {item_id} x{quantity}"}

    async def withdraw_item(self, user_id: int, item_id: str, quantity: int = 1) -> dict:
        guild = await self._get_user_guild(user_id)
        if not guild:
            return {"success": False, "message": "Ты не в гильдии."}

        storage = await self._get_storage(guild["guild_id"])
        existing = next((s for s in storage if s["item_id"] == item_id), None)

        if not existing or existing.quantity < quantity:
            return {"success": False, "message": "Недостаточно предметов на складе."}

        async for db in get_db():
            if existing.quantity <= quantity:
                await db.delete(existing)
            else:
                existing.quantity -= quantity
            await db.commit()

        return {"success": True, "message": f"📦 Забрано со склада: {item_id} x{quantity}"}

    async def get_storage(self, user_id: int) -> dict:
        guild = await self._get_user_guild(user_id)
        if not guild:
            return {"success": False, "message": "Ты не в гильдии.", "items": []}

        items = await self._get_storage(guild["guild_id"])
        return {"success": True, "items": items, "limit": GUILD_STORAGE_LIMIT}

    async def _get_storage(self, guild_id: str) -> list:
        async for db in get_db():
            result = await db.execute(
                select(GuildStorageModel).where(GuildStorageModel.guild_id == guild_id)
            )
            return result.scalars().all()

    async def deposit_gold(self, user_id: int, amount: int) -> dict:
        guild = await self._get_user_guild(user_id)
        if not guild:
            return {"success": False, "message": "Ты не в гильдии."}

        user = await self.player.get(user_id)
        if user["gold"] < amount:
            return {"success": False, "message": f"У тебя только {user['gold']} золота."}

        async for db in get_db():
            await db.execute(
                update(UserModel).where(UserModel.user_id == user_id).values(gold=UserModel.gold - amount)
            )
            await db.execute(
                update(GuildModel).where(GuildModel.guild_id == guild["guild_id"]).values(gold=GuildModel.gold + amount)
            )
            await db.commit()

        return {"success": True, "message": f"💰 Пожертвовано {amount} золота в казну."}

    async def withdraw_gold(self, user_id: int, amount: int) -> dict:
        guild = await self._get_user_guild(user_id)
        if not guild:
            return {"success": False, "message": "Ты не в гильдии."}

        if guild["role"] not in ("leader", "officer"):
            return {"success": False, "message": "Только офицер или лидер может снимать золото."}

        async for db in get_db():
            result = await db.execute(
                select(GuildModel.gold).where(GuildModel.guild_id == guild["guild_id"])
            )
            gold = result.scalar()
            if gold is None or gold < amount:
                return {"success": False, "message": "Недостаточно золота в казне."}

            await db.execute(
                update(GuildModel).where(GuildModel.guild_id == guild["guild_id"]).values(gold=GuildModel.gold - amount)
            )
            await db.execute(
                update(UserModel).where(UserModel.user_id == user_id).values(gold=UserModel.gold + amount)
            )
            await db.commit()

        return {"success": True, "message": f"💰 Снято {amount} золота из казны."}

    async def get_bank_info(self, user_id: int) -> dict:
        guild = await self._get_user_guild(user_id)
        if not guild:
            return {"success": False, "message": "Ты не в гильдии."}

        async for db in get_db():
            result = await db.execute(
                select(GuildModel.gold).where(GuildModel.guild_id == guild["guild_id"])
            )
            gold = result.scalar() or 0
            return {"success": True, "gold": gold, "limit": GUILD_BANK_LIMIT, "role": guild["role"]}

    async def get_guild_quests(self, user_id: int) -> dict:
        guild = await self._get_user_guild(user_id)
        if not guild:
            return {"success": False, "message": "Ты не в гильдии.", "quests": []}

        active = await self._get_active_quests(guild["guild_id"])
        if not active:
            available = random.sample(GUILD_QUESTS, min(3, len(GUILD_QUESTS)))
            async for db in get_db():
                for q in available:
                    db.add(GuildQuestModel(
                        guild_id=guild["guild_id"],
                        quest_id=q["id"],
                        status="active",
                        progress=0,
                    ))
                await db.commit()
            active = await self._get_active_quests(guild["guild_id"])

        quests = []
        for aq in active:
            q_def = next((q for q in GUILD_QUESTS if q["id"] == aq.quest_id), None)
            if q_def:
                quests.append({
                    "quest_id": aq.quest_id,
                    "name": q_def["name"],
                    "description": q_def["description"],
                    "objective": q_def["objective"],
                    "rewards": q_def["rewards"],
                    "progress": aq.progress,
                    "status": aq.status,
                })

        return {"success": True, "quests": quests}

    async def _get_active_quests(self, guild_id: str) -> list:
        async for db in get_db():
            result = await db.execute(
                select(GuildQuestModel).where(
                    GuildQuestModel.guild_id == guild_id,
                    GuildQuestModel.status == "active",
                )
            )
            return result.scalars().all()

    async def _get_user_guild(self, user_id: int) -> dict | None:
        async for db in get_db():
            result = await db.execute(
                select(GuildModel, GuildMemberModel)
                .join(GuildMemberModel, GuildModel.guild_id == GuildMemberModel.guild_id)
                .where(GuildMemberModel.user_id == user_id)
            )
            row = result.first()
            if not row:
                return None
            guild, member = row
            return {
                "guild_id": guild.guild_id,
                "name": guild.name,
                "gold": guild.gold,
                "role": member.role,
            }
