from sqlalchemy import Column, String, Text, DateTime, Integer, JSON
from database.base import Base


class ChronicleEventModel(Base):
    __tablename__ = "chronicle_events"

    id = Column(String(36), primary_key=True)
    type = Column(String(30), nullable=False, index=True)
    importance = Column(String(15), nullable=False)
    title = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    player_id = Column(Integer, nullable=True, index=True)
    region_id = Column(String(50), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
