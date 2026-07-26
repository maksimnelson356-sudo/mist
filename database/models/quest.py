from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean
from sqlalchemy.sql import func
from database.base import Base


class QuestModel(Base):
    __tablename__ = "quests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quest_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    giver = Column(String(50), nullable=True)
    location = Column(String(50), nullable=True)
    requirements = Column(Text, default="{}")
    objectives = Column(Text, default="[]")
    rewards = Column(Text, default="{}")
    is_active = Column(Boolean, default=True)
    is_repeating = Column(Boolean, default=False)
    cooldown_hours = Column(Integer, default=0)


class UserQuestModel(Base):
    __tablename__ = "user_quests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    quest_id = Column(String(50), nullable=False)
    status = Column(String(20), default="active")
    progress = Column(Text, default="{}")
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)


class WorldEventModel(Base):
    __tablename__ = "world_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    trigger_time = Column(Text, nullable=True)
    duration_minutes = Column(Integer, default=60)
    is_active = Column(Boolean, default=False)
    affected_locations = Column(Text, default="[]")
    event_data = Column(Text, default="{}")
    created_at = Column(DateTime, server_default=func.now())


class LegendModel(Base):
    __tablename__ = "legends"

    id = Column(Integer, primary_key=True, autoincrement=True)
    legend_id = Column(String(50), unique=True, nullable=False)
    category = Column(String(30), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    discovered_by = Column(Integer, nullable=True)
    discovered_at = Column(DateTime, nullable=True)
    times_discovered = Column(Integer, default=0)
