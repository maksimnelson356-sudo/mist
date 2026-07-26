import uuid

from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from database.base import Base


class POIModel(Base):
    __tablename__ = "points_of_interest"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    location_id = Column(String(36), ForeignKey("locations.id"), nullable=False)
    poi_type = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    x = Column(Integer, default=0)
    y = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    interaction_data = Column(JSON, default=dict)
    created_at = Column(String(30), server_default=func.now())
