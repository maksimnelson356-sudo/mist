import uuid
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.sql import func
from database.base import Base


class LocationModel(Base):
    __tablename__ = "locations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    location_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    region_id = Column(String(36), ForeignKey("regions.id"), nullable=True)
    x = Column(Integer, default=0)
    y = Column(Integer, default=0)
    z = Column(Integer, default=0)
    discovered = Column(Boolean, default=False)
    discovered_by = Column(Integer, nullable=True)
    discovered_at = Column(DateTime, nullable=True)
    connections = Column(JSON, default=list)
    state_data = Column(JSON, default=dict)
    is_secret = Column(Boolean, default=False)
    required_karma = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
