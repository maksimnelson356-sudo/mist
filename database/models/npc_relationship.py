import uuid

from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from database.base import Base


class NPCRelationshipModel(Base):
    __tablename__ = "npc_relationships"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    npc_a_id = Column(String(50), nullable=False, index=True)
    npc_b_id = Column(String(50), nullable=False, index=True)
    relation_type = Column(String(30), default="neutral")
    value = Column(Integer, default=0)
    events = Column(JSON, default=list)
    created_at = Column(DateTime, server_default=func.now())
    last_interaction_at = Column(DateTime, nullable=True)
