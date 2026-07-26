from datetime import datetime

from sqlalchemy import func, select, update

from database.base import get_db
from database.models.guild import GuildMemberModel, GuildModel
from database.models.user import UserModel
from domain.events import EventType, Importance

GUILD_ROLES = {
    "leader": {"name": "Лидер", "permissions": ["all"]},
    "officer": {"name": "Офицер", "permissions": ["invite", "kick", "donate"]},
    "member": {"name": "Участник", "permissions": ["donate"]},
}

ROLE_HIERARCHY = ["leader", "officer", "member"]


class GuildService:

    def __init__(self, chronicle, user_service):
        self.chronicle = chronicle
        self.user_service = user_service

    async def create(self, user_id: int, name: str, description: str = "", motto: str = "") -> dict:
        async for db in get_db():
            user = await self.user_service.get(user_id)
            if user["gold"] < 50:
                return {"success": False, "message": "Нужно 50 золота для создания гильдии."}

            stmt = select(GuildMemberModel).where(GuildMemberModel.user_id == user_id)
            result = await db.execute(stmt)
            if result.scalar_one_or_none():
                return {"success": False, "message": "Ты уже в гильдии. Покинь её сначала."}

            guild_id = f"g_{user_id}_{int(datetime.now().timestamp())}"
            db.add(GuildModel(
                guild_id=guild_id,
                name=name,
                description=description,
                leader_id=user_id,
                motto=motto,
            ))
            db.add(GuildMemberModel(
                guild_id=guild_id,
                user_id=user_id,
                role="leader",
            ))

            await db.execute(
                update(UserModel).where(UserModel.user_id == user_id).values(gold=user["gold"] - 50)
            )
            await db.commit()

            await self.chronicle.publish(
                EventType.GUILD_CREATED,
                f"Создана гильдия: {name}",
                player_id=user_id,
                importance=Importance.NOTABLE,
                metadata={"guild_id": guild_id, "name": name},
            )

            return {"success": True, "message": f"🏰 Гильдия «{name}» создана!", "guild_id": guild_id}
        return {"success": False, "message": "Ошибка базы данных."}

    async def join(self, user_id: int, guild_id: str) -> dict:
        async for db in get_db():
            stmt_member = select(GuildMemberModel).where(GuildMemberModel.user_id == user_id)
            result_member = await db.execute(stmt_member)
            if result_member.scalar_one_or_none():
                return {"success": False, "message": "Ты уже в гильдии."}

            stmt_guild = select(GuildModel).where(GuildModel.guild_id == guild_id)
            result_guild = await db.execute(stmt_guild)
            guild = result_guild.scalar_one_or_none()
            if not guild:
                return {"success": False, "message": "Гильдия не найдена."}

            db.add(GuildMemberModel(guild_id=guild_id, user_id=user_id))
            await db.commit()

            await self.chronicle.publish(
                EventType.GUILD_JOINED,
                f"Вступление в «{guild.name}»",
                player_id=user_id,
                importance=Importance.COMMON,
                metadata={"guild_id": guild_id},
            )

            return {"success": True, "message": f"🏰 Ты вступил в «{guild.name}»!"}
        return {"success": False, "message": "Ошибка базы данных."}

    async def leave(self, user_id: int) -> dict:
        async for db in get_db():
            stmt = (
                select(GuildMemberModel, GuildModel)
                .join(GuildModel, GuildMemberModel.guild_id == GuildModel.guild_id)
                .where(GuildMemberModel.user_id == user_id)
            )
            result = await db.execute(stmt)
            row = result.first()
            if not row:
                return {"success": False, "message": "Ты не в гильдии."}

            member, guild = row

            if member.role == "leader":
                stmt_successor = select(GuildMemberModel).where(
                    GuildMemberModel.guild_id == member.guild_id,
                    GuildMemberModel.user_id != user_id,
                ).limit(1)
                result_successor = await db.execute(stmt_successor)
                successor = result_successor.scalar_one_or_none()
                if successor:
                    successor.role = "leader"
                else:
                    await db.delete(guild)

            await db.delete(member)
            await db.commit()

            return {"success": True, "message": f"Ты покинул «{guild.name}»."}
        return {"success": False, "message": "Ошибка базы данных."}

    async def get_user_guild(self, user_id: int) -> dict | None:
        async for db in get_db():
            stmt = (
                select(GuildModel, GuildMemberModel)
                .join(GuildMemberModel, GuildModel.guild_id == GuildMemberModel.guild_id)
                .where(GuildMemberModel.user_id == user_id)
            )
            result = await db.execute(stmt)
            row = result.first()
            if not row:
                return None
            guild, member = row
            return {
                "guild_id": guild.guild_id,
                "name": guild.name,
                "description": guild.description,
                "leader_id": guild.leader_id,
                "level": guild.level,
                "xp": guild.xp,
                "gold": guild.gold,
                "motto": guild.motto,
                "created_at": guild.created_at,
                "role": member.role,
                "contribution": member.contribution,
            }
        return None

    async def get_members(self, guild_id: str) -> list:
        async for db in get_db():
            stmt = (
                select(GuildMemberModel, UserModel)
                .outerjoin(UserModel, GuildMemberModel.user_id == UserModel.user_id)
                .where(GuildMemberModel.guild_id == guild_id)
                .order_by(GuildMemberModel.role.desc(), GuildMemberModel.contribution.desc())
            )
            result = await db.execute(stmt)
            rows = result.all()
            members = []
            for member, user in rows:
                members.append({
                    "guild_id": member.guild_id,
                    "user_id": member.user_id,
                    "role": member.role,
                    "contribution": member.contribution,
                    "joined_at": member.joined_at,
                    "display_name": user.display_name if user else None,
                    "level": user.level if user else 0,
                    "pvp_rating": user.pvp_rating if user else 0,
                })
            return members
        return []

    async def get_all(self, limit: int = 10) -> list:
        async for db in get_db():
            stmt = (
                select(GuildModel, func.count(GuildMemberModel.id).label("member_count"))
                .outerjoin(GuildMemberModel, GuildModel.guild_id == GuildMemberModel.guild_id)
                .group_by(GuildModel.id)
                .order_by(GuildModel.level.desc(), GuildModel.xp.desc())
                .limit(limit)
            )
            result = await db.execute(stmt)
            rows = result.all()
            guilds = []
            for guild, member_count in rows:
                guilds.append({
                    "guild_id": guild.guild_id,
                    "name": guild.name,
                    "description": guild.description,
                    "leader_id": guild.leader_id,
                    "level": guild.level,
                    "xp": guild.xp,
                    "gold": guild.gold,
                    "motto": guild.motto,
                    "member_count": member_count,
                })
            return guilds
        return []

    async def donate(self, user_id: int, amount: int) -> dict:
        async for db in get_db():
            user = await self.user_service.get(user_id)
            guild_info = await self.get_user_guild(user_id)

            if not guild_info:
                return {"success": False, "message": "Ты не в гильдии."}
            if user["gold"] < amount:
                return {"success": False, "message": f"У тебя только {user['gold']} золота."}
            if amount <= 0:
                return {"success": False, "message": "Сумма должна быть больше 0."}

            await db.execute(
                update(UserModel).where(UserModel.user_id == user_id).values(gold=user["gold"] - amount)
            )
            await db.execute(
                update(GuildModel).where(GuildModel.guild_id == guild_info["guild_id"]).values(
                    gold=GuildModel.gold + amount,
                    xp=GuildModel.xp + amount // 2,
                )
            )
            await db.execute(
                update(GuildMemberModel).where(
                    GuildMemberModel.guild_id == guild_info["guild_id"],
                    GuildMemberModel.user_id == user_id,
                ).values(contribution=GuildMemberModel.contribution + amount)
            )
            await db.commit()

            await self.chronicle.publish(
                EventType.GUILD_DONATED,
                f"Пожертвование в «{guild_info['name']}»: {amount} 🪙",
                player_id=user_id,
                importance=Importance.COMMON,
                metadata={"guild_id": guild_info["guild_id"], "amount": amount},
            )

            return {"success": True, "message": f"💰 Пожертвовал {amount} 🪙 в казну «{guild_info['name']}»"}
        return {"success": False, "message": "Ошибка базы данных."}

    async def check_permission(self, user_id: int, permission: str) -> bool:
        guild_info = await self.get_user_guild(user_id)
        if not guild_info:
            return False
        role = guild_info.get("role", "member")
        perms = GUILD_ROLES.get(role, {}).get("permissions", [])
        return "all" in perms or permission in perms

    async def set_role(self, guild_id: str, target_user_id: int, new_role: str, operator_id: int) -> dict:
        if new_role not in GUILD_ROLES:
            return {"success": False, "message": f"Неизвестная роль: {new_role}"}

        operator_guild = await self.get_user_guild(operator_id)
        if not operator_guild or operator_guild["guild_id"] != guild_id:
            return {"success": False, "message": "Ты не в этой гильдии."}

        operator_role = operator_guild["role"]
        operator_idx = ROLE_HIERARCHY.index(operator_role) if operator_role in ROLE_HIERARCHY else 99
        new_role_idx = ROLE_HIERARCHY.index(new_role) if new_role in ROLE_HIERARCHY else 99

        if operator_role != "leader" and new_role == "leader":
            return {"success": False, "message": "Только лидер может назначать лидером."}

        if operator_idx >= new_role_idx:
            return {"success": False, "message": "Нельзя назначить роль своего уровня или выше."}

        async for db in get_db():
            stmt = select(GuildMemberModel).where(
                GuildMemberModel.guild_id == guild_id,
                GuildMemberModel.user_id == target_user_id,
            )
            result = await db.execute(stmt)
            member = result.scalar_one_or_none()
            if not member:
                return {"success": False, "message": "Игрок не в этой гильдии."}

            member.role = new_role
            await db.commit()

            role_name = GUILD_ROLES[new_role]["name"]
            await self.chronicle.publish(
                EventType.GUILD_ROLE_CHANGED,
                f"Роль изменена: #{target_user_id} → {role_name}",
                player_id=operator_id,
                importance=Importance.COMMON,
                metadata={"guild_id": guild_id, "target": target_user_id, "role": new_role},
            )

            return {"success": True, "message": f"⭐ Роль игрока изменена на «{role_name}»"}
        return {"success": False, "message": "Ошибка базы данных."}

    async def kick(self, guild_id: str, target_user_id: int, operator_id: int) -> dict:
        operator_guild = await self.get_user_guild(operator_id)
        if not operator_guild or operator_guild["guild_id"] != guild_id:
            return {"success": False, "message": "Ты не в этой гильдии."}

        operator_role = operator_guild["role"]
        if operator_role not in ("leader", "officer"):
            return {"success": False, "message": "Нет прав на исключение."}

        async for db in get_db():
            stmt = select(GuildMemberModel).where(
                GuildMemberModel.guild_id == guild_id,
                GuildMemberModel.user_id == target_user_id,
            )
            result = await db.execute(stmt)
            member = result.scalar_one_or_none()
            if not member:
                return {"success": False, "message": "Игрок не в этой гильдии."}

            if member.role == "leader":
                return {"success": False, "message": "Нельзя исключить лидера."}

            if operator_role == "officer" and member.role == "officer":
                return {"success": False, "message": "Офицер не может исключить офицера."}

            await db.delete(member)
            await db.commit()

            await self.chronicle.publish(
                EventType.GUILD_LEFT,
                f"Исключён из гильдии: #{target_user_id}",
                player_id=operator_id,
                importance=Importance.COMMON,
                metadata={"guild_id": guild_id, "kicked": target_user_id},
            )

            return {"success": True, "message": "🚫 Игрок исключён из гильдии."}
        return {"success": False, "message": "Ошибка базы данных."}

    async def promote(self, guild_id: str, target_user_id: int, operator_id: int) -> dict:
        operator_guild = await self.get_user_guild(operator_id)
        if not operator_guild or operator_guild["guild_id"] != guild_id:
            return {"success": False, "message": "Ты не в этой гильдии."}

        if operator_guild["role"] != "leader":
            return {"success": False, "message": "Только лидер может повышать."}

        async for db in get_db():
            stmt = select(GuildMemberModel).where(
                GuildMemberModel.guild_id == guild_id,
                GuildMemberModel.user_id == target_user_id,
            )
            result = await db.execute(stmt)
            member = result.scalar_one_or_none()
            if not member:
                return {"success": False, "message": "Игрок не в этой гильдии."}

            current_idx = ROLE_HIERARCHY.index(member.role) if member.role in ROLE_HIERARCHY else 99
            if current_idx <= 0:
                return {"success": False, "message": "Уже максимальный ранг."}

            new_role = ROLE_HIERARCHY[current_idx - 1]
            member.role = new_role
            await db.commit()

            role_name = GUILD_ROLES[new_role]["name"]
            await self.chronicle.publish(
                EventType.GUILD_ROLE_CHANGED,
                f"Повышение: #{target_user_id} → {role_name}",
                player_id=operator_id,
                importance=Importance.NOTABLE,
                metadata={"guild_id": guild_id, "target": target_user_id, "role": new_role},
            )

            return {"success": True, "message": f"⬆️ Игрок повышен до «{role_name}»"}
        return {"success": False, "message": "Ошибка базы данных."}
