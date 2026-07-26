import uuid
from sqlalchemy import Column, String, Integer, Text, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from database.base import Base


class NPCModel(Base):
    __tablename__ = "npcs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    npc_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    npc_type = Column(String(30), nullable=False)
    state = Column(String(30), default="idle")
    location_id = Column(String(36), ForeignKey("locations.id"), nullable=True)
    location_str = Column(String(50), nullable=True)
    disposition = Column(String(20), default="neutral")
    schedule = Column(JSON, default=dict)
    dialogue_tree = Column(JSON, default=dict)
    is_alive = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
