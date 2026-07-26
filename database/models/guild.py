from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from database.base import Base


class GuildModel(Base):
    __tablename__ = "guilds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    leader_id = Column(Integer, nullable=True)
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    gold = Column(Integer, default=0)
    motto = Column(Text, default="")
    created_at = Column(DateTime, server_default=func.now())


class GuildMemberModel(Base):
    __tablename__ = "guild_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(String(50), nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    role = Column(String(20), default="member")
    contribution = Column(Integer, default=0)
    joined_at = Column(DateTime, server_default=func.now())


class GuildStorageModel(Base):
    __tablename__ = "guild_storage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(String(50), nullable=False, index=True)
    item_id = Column(String(100), nullable=False)
    quantity = Column(Integer, default=1)
    deposited_by = Column(Integer, nullable=True)
    deposited_at = Column(DateTime, server_default=func.now())


class GuildQuestModel(Base):
    __tablename__ = "guild_quests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(String(50), nullable=False, index=True)
    quest_id = Column(String(100), nullable=False)
    status = Column(String(20), default="active")
    progress = Column(Integer, default=0)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
