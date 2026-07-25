import logging
from datetime import datetime, timezone
from sqlalchemy import select, update

from database.base import get_db
from database.models.daily_reward import DailyRewardModel
from database.models.user import UserModel

logger = logging.getLogger("MIST.daily_reward")

EPOCH = datetime(2024, 1, 1, tzinfo=timezone.utc)

STREAK_REWARDS = {
    1: {"gold": 10, "xp": 5, "message": "🎁 День 1: 10🪙 + 5XP"},
    2: {"gold": 15, "xp": 8, "message": "🎁 День 2: 15🪙 + 8XP"},
    3: {"gold": 20, "xp": 12, "item": "healing_herb", "item_qty": 2, "message": "🎁 День 3: 20🪙 + 12XP + 2x Трава исцеления"},
    4: {"gold": 25, "xp": 15, "message": "🎁 День 4: 25🪙 + 15XP"},
    5: {"gold": 30, "xp": 20, "message": "🎁 День 5: 30🪙 + 20XP"},
    6: {"gold": 40, "xp": 25, "item": "healing_herb", "item_qty": 5, "message": "🎁 День 6: 40🪙 + 25XP + 5x Трава исцеления"},
    7: {"gold": 100, "xp": 50, "item": "light_leaf", "item_qty": 3, "message": "🎁 День 7 (бонус!): 100🪙 + 50XP + 3x Лист света"},
}


class DailyRewardService:

    def __init__(self, chronicle, user_service, inventory_service):
        self.chronicle = chronicle
        self.user_service = user_service
        self.inventory = inventory_service

    async def claim(self, user_id: int) -> dict:
        today = (datetime.now(timezone.utc) - EPOCH).days + 1

        async for db in get_db():
            stmt = select(DailyRewardModel).where(DailyRewardModel.user_id == user_id)
            result = await db.execute(stmt)
            record = result.scalar_one_or_none()

            if record and record.last_claim_day == today:
                return {"success": False, "message": "📅 Ты уже получил награду сегодня! Загляни завтра."}

            if not record:
                record = DailyRewardModel(user_id=user_id, streak=0, last_claim_day=0, total_claims=0)
                db.add(record)
                await db.flush()

            if record.last_claim_day == today - 1:
                new_streak = record.streak + 1 if record.streak < 7 else 1
            else:
                new_streak = 1

            reward = STREAK_REWARDS.get(new_streak, STREAK_REWARDS[1])

            user_stmt = select(UserModel).where(UserModel.user_id == user_id)
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()

            if user:
                user.gold += reward.get("gold", 0)
                user.xp += reward.get("xp", 0)

                new_level = user.level
                new_xp = user.xp
                while new_xp >= new_level * 100:
                    new_level += 1
                    new_xp -= (new_level - 1) * 100
                if new_level > user.level:
                    user.level = new_level
                    user.xp = new_xp
                    user.max_hp = 100 + (new_level - 1) * 15
                    user.attack = 10 + (new_level - 1) * 3
                    user.defense = 5 + (new_level - 1) * 2

            if reward.get("item"):
                await self.inventory.add(user_id, reward["item"], reward.get("item_qty", 1))

            record.streak = new_streak
            record.last_claim_day = today
            record.total_claims += 1
            await db.commit()

            msg = reward["message"]
            if new_streak == 7:
                msg += "\n\n🔥 Серия 7 дней! Цикл начинается заново!"

            return {
                "success": True,
                "message": msg,
                "streak": new_streak,
                "total_claims": record.total_claims,
            }
        return {"success": False, "message": "Ошибка базы данных."}

    async def get_info(self, user_id: int) -> dict:
        async for db in get_db():
            stmt = select(DailyRewardModel).where(DailyRewardModel.user_id == user_id)
            result = await db.execute(stmt)
            record = result.scalar_one_or_none()

            today = (datetime.now(timezone.utc) - EPOCH).days + 1

            claimed_today = record.last_claim_day == today if record else False
            streak = record.streak if record else 0
            total = record.total_claims if record else 0

            next_day = min(streak + 1, 7)
            next_reward = STREAK_REWARDS.get(next_day, STREAK_REWARDS[1])

            return {
                "streak": streak,
                "total_claims": total,
                "claimed_today": claimed_today,
                "next_reward": next_reward,
                "next_day": next_day,
            }
        return {"streak": 0, "total_claims": 0, "claimed_today": False, "next_reward": STREAK_REWARDS[1], "next_day": 1}
