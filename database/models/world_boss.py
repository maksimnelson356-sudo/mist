import uuid

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from database.base import Base


class WorldBossModel(Base):
    __tablename__ = "world_bosses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    boss_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    location_id = Column(String(50), nullable=False)
    region_id = Column(String(50), nullable=True)
    hp = Column(Integer, default=1000)
    max_hp = Column(Integer, default=1000)
    attack = Column(Integer, default=50)
    defense = Column(Integer, default=30)
    xp_reward = Column(Integer, default=500)
    gold_reward = Column(Integer, default=200)
    is_alive = Column(Boolean, default=True)
    spawned_at = Column(DateTime, server_default=func.now())
    killed_at = Column(DateTime, nullable=True)
    killed_by = Column(Integer, nullable=True)
    participants = Column(JSON, default=list)
    phase = Column(String(20), default="idle")
    abilities = Column(JSON, default=list)
    loot_table = Column(JSON, default=list)
    respawn_hours = Column(Integer, default=72)
    event_trigger = Column(String(50), nullable=True)
