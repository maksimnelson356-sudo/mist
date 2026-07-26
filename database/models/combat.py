from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from database.base import Base


class CombatLogModel(Base):
    __tablename__ = "combat_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    creature_id = Column(String(50), nullable=True)
    result = Column(String(20), nullable=False)
    damage_dealt = Column(Integer, default=0)
    damage_taken = Column(Integer, default=0)
    xp_gained = Column(Integer, default=0)
    loot_dropped = Column(Text, default="[]")
    duration_seconds = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class BossSpawnModel(Base):
    __tablename__ = "boss_spawns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    boss_id = Column(String(50), unique=True, nullable=False)
    creature_id = Column(String(50), nullable=False)
    location = Column(String(50), nullable=False)
    respawn_hours = Column(Integer, default=24)
    last_killed_at = Column(DateTime, nullable=True)
    killed_by = Column(Integer, nullable=True)
