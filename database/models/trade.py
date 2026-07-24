from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.sql import func
from database.base import Base


class PlayerTradeModel(Base):
    __tablename__ = "player_trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_user = Column(Integer, nullable=False, index=True)
    to_user = Column(Integer, nullable=False, index=True)
    items_offered = Column(Text, default="[]")
    gold_offered = Column(Integer, default=0)
    items_wanted = Column(Text, default="[]")
    gold_wanted = Column(Integer, default=0)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
