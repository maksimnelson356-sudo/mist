import uuid

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from database.base import Base


class ArtifactModel(Base):
    __tablename__ = "artifacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    artifact_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    lore = Column(Text, nullable=True)
    rarity = Column(String(20), default="common")
    artifact_type = Column(String(30), default="weapon")
    owner_id = Column(Integer, nullable=True)
    location_found = Column(String(50), nullable=True)
    times_used = Column(Integer, default=0)
    kills_with = Column(Integer, default=0)
    saves_with = Column(Integer, default=0)
    events_witnessed = Column(JSON, default=list)
    created_at = Column(DateTime, server_default=func.now())
    found_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    stats = Column(JSON, default=dict)
    curse = Column(Text, nullable=True)
    blessing = Column(Text, nullable=True)
