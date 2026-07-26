import uuid

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.sql import func

from database.base import Base


class ContinentModel(Base):
    __tablename__ = "continents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    x = Column(Integer, default=0)
    y = Column(Integer, default=0)
    created_at = Column(String(30), server_default=func.now())
