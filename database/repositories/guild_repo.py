from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.guild import GuildMemberModel, GuildModel


class GuildRepository:

    @staticmethod
    async def create(session: AsyncSession, guild_id: str, name: str,
                     description: str, leader_id: int, motto: str = "") -> dict:
        guild = GuildModel(
            guild_id=guild_id, name=name, description=description,
            leader_id=leader_id, motto=motto,
        )
        session.add(guild)
        member = GuildMemberModel(guild_id=guild_id, user_id=leader_id, role="leader")
        session.add(member)
        await session.commit()
        return dict(guild.__dict__)

    @staticmethod
    async def join(session: AsyncSession, guild_id: str, user_id: int):
        session.add(GuildMemberModel(guild_id=guild_id, user_id=user_id))
        await session.commit()

    @staticmethod
    async def leave(session: AsyncSession, user_id: int) -> dict | None:
        stmt = select(GuildMemberModel).where(GuildMemberModel.user_id == user_id)
        result = await session.execute(stmt)
        member = result.scalars().first()
        if not member:
            return None
        data = dict(member.__dict__)

        if member.role == "leader":
            stmt2 = select(GuildMemberModel).where(
                GuildMemberModel.guild_id == member.guild_id,
                GuildMemberModel.user_id != user_id,
            ).limit(1)
            result2 = await session.execute(stmt2)
            successor = result2.scalars().first()
            if successor:
                successor.role = "leader"
            else:
                await session.delete(member)
                stmt3 = select(GuildModel).where(GuildModel.guild_id == member.guild_id)
                result3 = await session.execute(stmt3)
                guild = result3.scalars().first()
                if guild:
                    await session.delete(guild)
                await session.commit()
                return data

        await session.delete(member)
        await session.commit()
        return data

    @staticmethod
    async def get_user_guild(session: AsyncSession, user_id: int) -> dict | None:
        stmt = (
            select(GuildModel, GuildMemberModel)
            .join(GuildMemberModel, GuildModel.guild_id == GuildMemberModel.guild_id)
            .where(GuildMemberModel.user_id == user_id)
        )
        result = await session.execute(stmt)
        row = result.first()
        if not row:
            return None
        guild, member = row
        d = dict(guild.__dict__)
        d["role"] = member.role
        d["contribution"] = member.contribution
        return d

    @staticmethod
    async def get_members(session: AsyncSession, guild_id: str) -> list:
        stmt = select(GuildMemberModel).where(GuildMemberModel.guild_id == guild_id)
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def get_all(session: AsyncSession, limit: int = 10) -> list:
        stmt = select(GuildModel).order_by(GuildModel.level.desc()).limit(limit)
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def donate(session: AsyncSession, guild_id: str, user_id: int, amount: int):
        stmt = select(GuildModel).where(GuildModel.guild_id == guild_id)
        result = await session.execute(stmt)
        guild = result.scalars().first()
        if guild:
            guild.gold += amount
            guild.xp += amount // 2

        stmt2 = select(GuildMemberModel).where(
            GuildMemberModel.guild_id == guild_id,
            GuildMemberModel.user_id == user_id,
        )
        result2 = await session.execute(stmt2)
        member = result2.scalars().first()
        if member:
            member.contribution += amount
        await session.commit()

    @staticmethod
    async def is_member(session: AsyncSession, user_id: int) -> bool:
        stmt = select(GuildMemberModel).where(GuildMemberModel.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalars().first() is not None

    @staticmethod
    async def member_count(session: AsyncSession, guild_id: str) -> int:
        stmt = select(func.count()).select_from(GuildMemberModel).where(
            GuildMemberModel.guild_id == guild_id
        )
        result = await session.execute(stmt)
        return result.scalar() or 0
