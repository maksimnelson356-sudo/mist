from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from database.base import Base


class NPCMemoryModel(Base):
    __tablename__ = "npc_memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    npc_id = Column(String(36), ForeignKey("npcs.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    relation = Column(Integer, default=0)
    last_seen = Column(DateTime, server_default=func.now())
    interaction_count = Column(Integer, default=0)
    last_action = Column(String(50), nullable=True)
    memory_data = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())
