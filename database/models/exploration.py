from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from database.base import Base


class ExplorationModel(Base):
    __tablename__ = "explorations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    location_id = Column(String(36), ForeignKey("locations.id"), nullable=False)
    first_discovered = Column(Boolean, default=False)
    visited_count = Column(Integer, default=0)
    discovered_at = Column(DateTime, nullable=True)
    last_visited = Column(DateTime, server_default=func.now())
