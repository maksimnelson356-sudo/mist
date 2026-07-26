import uuid

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from database.base import Base


class PlayerHomeModel(Base):
    __tablename__ = "player_homes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    location_id = Column(String(50), nullable=False)
    name = Column(String(100), default="Мой дом")
    description = Column(Text, nullable=True)
    home_type = Column(String(30), default="hut")
    level = Column(Integer, default=1)
    max_level = Column(Integer, default=10)
    rooms = Column(JSON, default=list)
    decorations = Column(JSON, default=list)
    defenses = Column(Integer, default=0)
    comfort = Column(Integer, default=10)
    storage_capacity = Column(Integer, default=20)
    garden_level = Column(Integer, default=0)
    workshop_level = Column(Integer, default=0)
    library_level = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    last_visited_at = Column(DateTime, nullable=True)
    upgrades = Column(JSON, default=dict)
    events_history = Column(JSON, default=list)
    condition = Column(Integer, default=100)
    mood = Column(String(20), default="calm")
    income_per_day = Column(Integer, default=0)
    storage = Column(JSON, default=list)
