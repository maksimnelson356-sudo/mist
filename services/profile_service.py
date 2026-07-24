from sqlalchemy import select, update
from sqlalchemy.sql import func

from database.base import get_db
from database.models.user import UserModel
from domain.events import EventType, Importance


class ProfileService:

    def __init__(self, chronicle, player):
        self.chronicle = chronicle
        self.player = player

    async def get_profile(self, user_id: int) -> str:
        user = await self.player.get(user_id)
        if not user:
            return "❌ Профиль не найден."

        reputation_level = self._get_reputation_level(user.get("reputation", 0))

        profile = (
            f"👤 **{user['display_name']}**\n\n"
            f"📊 Уровень: {user['level']} (XP: {user['xp']})\n"
            f"❤️ HP: {user['hp']}/{user['max_hp']}\n"
            f"⚔️ Атака: {user['attack']} | 🛡️ Защита: {user['defense']}\n"
            f"💰 Золото: {user['gold']}\n\n"
            f"⭐ Репутация: {user['reputation']} ({reputation_level})\n"
            f"🎭 Карма: {user['karma']}\n\n"
            f"📍 Локация: {user['current_location']}\n"
            f"📅 В Мисте: {user['days_in_mist']} дней\n"
        )

        if user.get("pvp_wins") or user.get("pvp_losses"):
            profile += (
                f"\n⚔️ PvP: {user['pvp_wins']} побед / {user['pvp_losses']} поражений\n"
                f"🏆 Рейтинг: {user['pvp_rating']}"
            )

        return profile

    async def update_display_name(self, user_id: int, name: str) -> dict:
        if len(name) < 2 or len(name) > 30:
            return {"success": False, "message": "Имя должно быть от 2 до 30 символов."}

        await self.player.update(user_id, display_name=name)

        await self.chronicle.publish(
            EventType.PLAYER_RENAMED,
            f"Путник сменил имя на {name}",
            player_id=user_id,
            importance=Importance.TRIVIAL,
        )

        return {"success": True, "message": f"✨ Теперь тебя зовут: {name}"}

    async def get_stats(self, user_id: int) -> dict:
        user = await self.player.get(user_id)
        if not user:
            return {}

        return {
            "user_id": user["user_id"],
            "display_name": user["display_name"],
            "level": user["level"],
            "xp": user["xp"],
            "hp": user["hp"],
            "max_hp": user["max_hp"],
            "attack": user["attack"],
            "defense": user["defense"],
            "gold": user["gold"],
            "reputation": user["reputation"],
            "karma": user["karma"],
            "current_location": user["current_location"],
            "days_in_mist": user["days_in_mist"],
            "is_alive": user["is_alive"],
            "pvp_wins": user["pvp_wins"],
            "pvp_losses": user["pvp_losses"],
            "pvp_rating": user["pvp_rating"],
        }

    @staticmethod
    def _get_reputation_level(reputation: int) -> str:
        if reputation <= -51:
            return "Враг"
        elif reputation <= -1:
            return "Подозрительный"
        elif reputation <= 49:
            return "Нейтральный"
        elif reputation <= 99:
            return "Доброжелательный"
        else:
            return "Герой"
