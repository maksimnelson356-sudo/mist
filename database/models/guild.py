from sqlalchemy import Column, String, Integer, DateTime, Text
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
