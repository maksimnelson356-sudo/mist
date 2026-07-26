import uuid
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.sql import func
from database.base import Base


class FactionModel(Base):
    __tablename__ = "factions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    faction_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(10), default="⚔️")
    location_id = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class PlayerFactionModel(Base):
    __tablename__ = "player_factions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    faction_id = Column(String(50), ForeignKey("factions.faction_id"), nullable=False)
    reputation = Column(Integer, default=0)
    rank = Column(String(30), default="novice")
    joined_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)
