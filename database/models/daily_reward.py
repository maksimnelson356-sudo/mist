import uuid
from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.sql import func
from database.base import Base


class DailyRewardModel(Base):
    __tablename__ = "daily_rewards"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, index=True, nullable=False)
    streak = Column(Integer, default=0)
    last_claim_day = Column(Integer, default=0)
    total_claims = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
