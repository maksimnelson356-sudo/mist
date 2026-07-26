from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from database.base import Base


class AchievementModel(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    achievement_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(10), default="🏅")
    category = Column(String(30), default="general")
    requirement = Column(Text, default="{}")
    reward_xp = Column(Integer, default=50)
    reward_gold = Column(Integer, default=0)
    reward_item = Column(String(50), nullable=True)
    is_secret = Column(Boolean, default=False)


class UserAchievementModel(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    achievement_id = Column(String(50), nullable=False)
    unlocked_at = Column(DateTime, server_default=func.now())
