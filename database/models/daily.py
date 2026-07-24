from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean
from sqlalchemy.sql import func
from database.base import Base


class DailyQuestModel(Base):
    __tablename__ = "daily_quests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    quest_id = Column(String(50), nullable=False)
    day = Column(String(10), nullable=False)
    status = Column(String(20), default="active")
    progress = Column(Text, default="{}")
    completed_at = Column(DateTime, nullable=True)
