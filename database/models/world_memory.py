import uuid

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from database.base import Base


class WorldMemoryModel(Base):
    __tablename__ = "world_memories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    memory_type = Column(String(30), nullable=False, index=True)
    location_id = Column(String(50), nullable=True, index=True)
    player_id = Column(Integer, nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    impact_level = Column(Integer, default=1)
    is_permanent = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    extra_data = Column(JSON, default=dict)
