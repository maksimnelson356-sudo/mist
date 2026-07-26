import uuid

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from database.base import Base


class WorldEventRecordModel(Base):
    __tablename__ = "world_event_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(50), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    region_id = Column(String(50), nullable=True, index=True)
    location_id = Column(String(50), nullable=True)
    start_day = Column(Integer, nullable=False)
    end_day = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    effects = Column(JSON, default=dict)
    chain_events = Column(JSON, default=list)
    triggered_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
