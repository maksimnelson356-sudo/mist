import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from database.base import Base


class RegionModel(Base):
    __tablename__ = "regions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    continent_id = Column(String(36), ForeignKey("continents.id"), nullable=False)
    x = Column(Integer, default=0)
    y = Column(Integer, default=0)
    created_at = Column(String(30), server_default=func.now())
