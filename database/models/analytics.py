from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from database.base import Base


class AnalyticsEventModel(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    data = Column(Text, default="{}")
    created_at = Column(DateTime, server_default=func.now())
