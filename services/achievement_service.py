
from sqlalchemy import func, select, update

from database.base import get_db
from database.models.achievement import AchievementModel, UserAchievementModel
from database.models.combat import CombatLogModel
from database.models.crafting import UserCraftingModel
from database.models.guild import GuildMemberModel
from database.models.inventory import UserEquipmentModel
from database.models.location import LocationModel
from database.models.npc_memory import NPCMemoryModel
from database.models.quest import UserQuestModel
from database.models.user import UserModel
from domain.events import EventType, Importance

ACHIEVEMENT_DEFS = [
    {"achievement_id": "first_blood", "name": "Первая кровь", "description": "Убей первое существо", "icon": "🩸", "category": "combat", "requirement": {"type": "kill_count", "target": 1}, "reward_xp": 25, "reward_gold": 0},
    {"achievement_id": "monster_hunter", "name": "Охотник", "description": "Убей 10 существ", "icon": "⚔️", "category": "combat", "requirement": {"type": "kill_count", "target": 10}, "reward_xp": 100, "reward_gold": 50},
    {"achievement_id": "slayer", "name": "Бог убийств", "description": "Убей 50 существ", "icon": "💀", "category": "combat", "requirement": {"type": "kill_count", "target": 50}, "reward_xp": 500, "reward_gold": 200},
    {"achievement_id": "explorer_5", "name": "Исследователь", "description": "Открой 5 локаций", "icon": "🗺️", "category": "explore", "requirement": {"type": "locations_discovered", "target": 5}, "reward_xp": 50, "reward_gold": 0},
    {"achievement_id": "explorer_15", "name": "Странник", "description": "Открой 15 локаций", "icon": "🌍", "category": "explore", "requirement": {"type": "locations_discovered", "target": 15}, "reward_xp": 200, "reward_gold": 100},
    {"achievement_id": "explorer_all", "name": "Повелитель тумана", "description": "Открой все локации", "icon": "👁️", "category": "explore", "requirement": {"type": "locations_discovered", "target": 28}, "reward_xp": 1000, "reward_gold": 500, "is_secret": True},
    {"achievement_id": "quest_5", "name": "Исполнитель", "description": "Выполни 5 квестов", "icon": "📜", "category": "quests", "requirement": {"type": "quests_completed", "target": 5}, "reward_xp": 75, "reward_gold": 0},
    {"achievement_id": "quest_all", "name": "Хранитель слов", "description": "Выполни все квесты", "icon": "📖", "category": "quests", "requirement": {"type": "quests_completed", "target": 28}, "reward_xp": 2000, "reward_gold": 1000, "is_secret": True},
    {"achievement_id": "level_5", "name": "Новичок", "description": "Достигни 5 уровня", "icon": "⭐", "category": "progress", "requirement": {"type": "level", "target": 5}, "reward_xp": 50, "reward_gold": 0},
    {"achievement_id": "level_10", "name": "Воин", "description": "Достигни 10 уровня", "icon": "🌟", "category": "progress", "requirement": {"type": "level", "target": 10}, "reward_xp": 200, "reward_gold": 100},
    {"achievement_id": "level_20", "name": "Легенда", "description": "Достигни 20 уровня", "icon": "💫", "category": "progress", "requirement": {"type": "level", "target": 20}, "reward_xp": 500, "reward_gold": 300},
    {"achievement_id": "gold_500", "name": "Скупщик", "description": "Накопи 500 золота", "icon": "🪙", "category": "wealth", "requirement": {"type": "gold", "target": 500}, "reward_xp": 50, "reward_gold": 0},
    {"achievement_id": "gold_5000", "name": "Торговец", "description": "Накопи 5000 золота", "icon": "💰", "category": "wealth", "requirement": {"type": "gold", "target": 5000}, "reward_xp": 300, "reward_gold": 500},
    {"achievement_id": "craft_3", "name": "Ремесленник", "description": "Скрафти 3 предмета", "icon": "⚒️", "category": "craft", "requirement": {"type": "craft_count", "target": 3}, "reward_xp": 50, "reward_gold": 0},
    {"achievement_id": "boss_killer", "name": "Убийца боссов", "description": "Убей босса", "icon": "👑", "category": "combat", "requirement": {"type": "boss_kills", "target": 1}, "reward_xp": 200, "reward_gold": 100},
    {"achievement_id": "pvp_5", "name": "Гладиатор", "description": "Выиграй 5 PvP боёв", "icon": "🏟️", "category": "pvp", "requirement": {"type": "pvp_wins", "target": 5}, "reward_xp": 100, "reward_gold": 50},
    {"achievement_id": "first_day", "name": "Первый день", "description": "Проведи 1 день в MIST", "icon": "🌅", "category": "progress", "requirement": {"type": "days_in_mist", "target": 1}, "reward_xp": 10, "reward_gold": 0},
    {"achievement_id": "week_survivor", "name": "Выживший", "description": "Проведи 7 дней в MIST", "icon": "🗓️", "category": "progress", "requirement": {"type": "days_in_mist", "target": 7}, "reward_xp": 150, "reward_gold": 75},
    {"achievement_id": "equipped", "name": "Экипирован", "description": "Экипируй предмет", "icon": "🎒", "category": "general", "requirement": {"type": "equipped", "target": 1}, "reward_xp": 10, "reward_gold": 0},
    {"achievement_id": "social_butterfly", "name": "Душа компании", "description": "Вступи в гильдию", "icon": "🏰", "category": "social", "requirement": {"type": "guild_member", "target": 1}, "reward_xp": 25, "reward_gold": 0},
    {"achievement_id": "kill_100", "name": "Мясник", "description": "Убей 100 существ", "icon": "🔪", "category": "combat", "requirement": {"type": "kill_count", "target": 100}, "reward_xp": 1000, "reward_gold": 500},
    {"achievement_id": "kill_500", "name": "Палач", "description": "Убей 500 существ", "icon": "☠️", "category": "combat", "requirement": {"type": "kill_count", "target": 500}, "reward_xp": 5000, "reward_gold": 2000, "is_secret": True},
    {"achievement_id": "gold_10000", "name": "Магнат", "description": "Накопи 10000 золота", "icon": "💎", "category": "wealth", "requirement": {"type": "gold", "target": 10000}, "reward_xp": 1000, "reward_gold": 0},
    {"achievement_id": "craft_10", "name": "Мастер", "description": "Скрафти 10 предметов", "icon": "🔨", "category": "craft", "requirement": {"type": "craft_count", "target": 10}, "reward_xp": 200, "reward_gold": 100},
    {"achievement_id": "craft_50", "name": "Легенда ремесла", "description": "Скрафти 50 предметов", "icon": "⚙️", "category": "craft", "requirement": {"type": "craft_count", "target": 50}, "reward_xp": 2000, "reward_gold": 1000, "is_secret": True},
    {"achievement_id": "level_30", "name": "Ветеран", "description": "Достигни 30 уровня", "icon": "🏅", "category": "progress", "requirement": {"type": "level", "target": 30}, "reward_xp": 2000, "reward_gold": 1000},
    {"achievement_id": "level_50", "name": "Бессмертный", "description": "Достигни 50 уровня", "icon": "🌌", "category": "progress", "requirement": {"type": "level", "target": 50}, "reward_xp": 10000, "reward_gold": 5000, "is_secret": True},
    {"achievement_id": "pvp_10", "name": "Боец", "description": "Выиграй 10 PvP боёв", "icon": "🥊", "category": "pvp", "requirement": {"type": "pvp_wins", "target": 10}, "reward_xp": 300, "reward_gold": 150},
    {"achievement_id": "pvp_50", "name": "Чемпион", "description": "Выиграй 50 PvP боёв", "icon": "🏆", "category": "pvp", "requirement": {"type": "pvp_wins", "target": 50}, "reward_xp": 2000, "reward_gold": 1000},
    {"achievement_id": "npc_talk_10", "name": "Знакомец", "description": "Поговори с 10 NPC", "icon": "🗣️", "category": "social", "requirement": {"type": "npc_talked", "target": 10}, "reward_xp": 50, "reward_gold": 0},
    {"achievement_id": "npc_trade_20", "name": "Торговец", "description": "Торгуй с NPC 20 раз", "icon": "🤝", "category": "social", "requirement": {"type": "npc_traded", "target": 20}, "reward_xp": 100, "reward_gold": 50},
    {"achievement_id": "explorer_25", "name": "Первооткрыватель", "description": "Открой 25 локаций", "icon": "🧭", "category": "explore", "requirement": {"type": "locations_discovered", "target": 25}, "reward_xp": 500, "reward_gold": 250},
]

CATEGORY_ICONS = {
    "combat": "⚔️",
    "explore": "🗺️",
    "quests": "📜",
    "progress": "⭐",
    "wealth": "💰",
    "craft": "⚒️",
    "pvp": "🏟️",
    "general": "🎒",
    "social": "🏰",
}

CATEGORY_NAMES = {
    "combat": "Бой",
    "explore": "Исследование",
    "quests": "Квесты",
    "progress": "Прогресс",
    "wealth": "Богатство",
    "craft": "Ремесло",
    "pvp": "PvP",
    "general": "Общее",
    "social": "Общение",
}


class AchievementService:

    def __init__(self, chronicle, user_service):
        self.chronicle = chronicle
        self.user_service = user_service

    async def check(self, user_id: int) -> list:
        newly_unlocked = []
        user = await self.user_service.get(user_id)
        if not user:
            return []

        async for db in get_db():
            stmt = select(UserAchievementModel.achievement_id).where(UserAchievementModel.user_id == user_id)
            result = await db.execute(stmt)
            unlocked_ids = {r.achievement_id for r in result.all()}

            kill_stmt = select(func.count()).select_from(CombatLogModel).where(
                CombatLogModel.user_id == user_id,
                CombatLogModel.result == "victory",
            )
            kill_count = (await db.execute(kill_stmt)).scalar()

            loc_stmt = select(func.count()).select_from(LocationModel).where(
                LocationModel.discovered == True,
                LocationModel.discovered_by == user_id,
            )
            locs_discovered = (await db.execute(loc_stmt)).scalar()

            quest_stmt = select(func.count()).select_from(UserQuestModel).where(
                UserQuestModel.user_id == user_id,
                UserQuestModel.status == "completed",
            )
            quests_completed = (await db.execute(quest_stmt)).scalar()

            craft_stmt = select(func.count()).select_from(UserCraftingModel).where(
                UserCraftingModel.user_id == user_id,
            )
            craft_count = (await db.execute(craft_stmt)).scalar()

            equip_stmt = select(func.count()).select_from(UserEquipmentModel).where(
                UserEquipmentModel.user_id == user_id,
            )
            has_equipped = (await db.execute(equip_stmt)).scalar() > 0

            guild_stmt = select(func.count()).select_from(GuildMemberModel).where(
                GuildMemberModel.user_id == user_id,
            )
            guild_member = (await db.execute(guild_stmt)).scalar() > 0

            npc_talk_stmt = select(func.count()).select_from(NPCMemoryModel).where(
                NPCMemoryModel.user_id == user_id,
            )
            npc_talked = (await db.execute(npc_talk_stmt)).scalar()

            npc_trade_stmt = select(func.count()).select_from(NPCMemoryModel).where(
                NPCMemoryModel.user_id == user_id,
                NPCMemoryModel.last_action == "trade",
            )
            npc_traded = (await db.execute(npc_trade_stmt)).scalar()

            stats = {
                "kill_count": kill_count,
                "locations_discovered": locs_discovered,
                "quests_completed": quests_completed,
                "level": user["level"],
                "gold": user["gold"],
                "craft_count": craft_count,
                "boss_kills": 0,
                "pvp_wins": user.get("pvp_wins", 0),
                "days_in_mist": user.get("days_in_mist", 0),
                "equipped": 1 if has_equipped else 0,
                "guild_member": 1 if guild_member else 0,
                "npc_talked": npc_talked,
                "npc_traded": npc_traded,
            }

            for ach in ACHIEVEMENT_DEFS:
                if ach["achievement_id"] in unlocked_ids:
                    continue
                req = ach["requirement"]
                val = stats.get(req.get("type", ""), 0)
                target = req.get("target", 1)
                if val >= target:
                    db.add(UserAchievementModel(
                        user_id=user_id,
                        achievement_id=ach["achievement_id"],
                    ))
                    await db.execute(
                        update(UserModel).where(UserModel.user_id == user_id).values(
                            xp=user["xp"] + ach.get("reward_xp", 0),
                        )
                    )
                    if ach.get("reward_gold"):
                        await db.execute(
                            update(UserModel).where(UserModel.user_id == user_id).values(
                                gold=user["gold"] + ach["reward_gold"],
                            )
                        )
                    newly_unlocked.append(ach)

            await db.commit()
            break

        for ach in newly_unlocked:
            await self.chronicle.publish(
                EventType.ACHIEVEMENT_UNLOCKED,
                f"Достижение: {ach['name']}",
                player_id=user_id,
                importance=Importance.RARE,
                metadata={"achievement_id": ach["achievement_id"], "name": ach["name"]},
            )

        return newly_unlocked

    async def get_user_achievements(self, user_id: int) -> list:
        async for db in get_db():
            stmt = (
                select(AchievementModel, UserAchievementModel)
                .outerjoin(UserAchievementModel, (AchievementModel.achievement_id == UserAchievementModel.achievement_id) & (UserAchievementModel.user_id == user_id))
                .order_by(UserAchievementModel.unlocked_at.desc().nulls_last())
            )
            result = await db.execute(stmt)
            rows = result.all()
            achievements = []
            for ach, ua in rows:
                achievements.append({
                    "achievement_id": ach.achievement_id,
                    "name": ach.name,
                    "description": ach.description,
                    "icon": ach.icon,
                    "category": ach.category,
                    "reward_xp": ach.reward_xp,
                    "reward_gold": ach.reward_gold,
                    "is_secret": ach.is_secret,
                    "unlocked_at": ua.unlocked_at if ua else None,
                })
            return achievements
        return []

    async def get_all_definitions(self) -> list:
        return [dict(a) for a in ACHIEVEMENT_DEFS]

    async def on_kill(self, user_id: int):
        return await self.check(user_id)

    async def on_location_discovered(self, user_id: int):
        return await self.check(user_id)

    async def on_quest_completed(self, user_id: int):
        return await self.check(user_id)

    async def on_level_up(self, user_id: int):
        return await self.check(user_id)

    async def on_gold_changed(self, user_id: int):
        return await self.check(user_id)

    async def on_craft(self, user_id: int):
        return await self.check(user_id)

    async def on_guild_joined(self, user_id: int):
        return await self.check(user_id)

    async def on_npc_talk(self, user_id: int):
        return await self.check(user_id)

    async def on_npc_trade(self, user_id: int):
        return await self.check(user_id)

    async def on_pvp_win(self, user_id: int):
        return await self.check(user_id)
