from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from database.base import Base


class UserModel(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=True)
    display_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    last_seen = Column(DateTime, server_default=func.now(), onupdate=func.now())
    current_location = Column(String(50), default="dark_forest")
    memories = Column(Integer, default=0)
    karma = Column(Integer, default=0)
    reputation = Column(Integer, default=0)
    days_in_mist = Column(Integer, default=0)
    is_alive = Column(Boolean, default=True)
    hp = Column(Integer, default=100)
    max_hp = Column(Integer, default=100)
    attack = Column(Integer, default=10)
    defense = Column(Integer, default=5)
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    gold = Column(Integer, default=0)
    gems = Column(Integer, default=0)
    tokens = Column(Integer, default=0)
    player_class = Column(String(20), default="warrior")
    class_level = Column(Integer, default=1)
    pvp_wins = Column(Integer, default=0)
    pvp_losses = Column(Integer, default=0)
    pvp_rating = Column(Integer, default=1000)
    hunger = Column(Integer, default=100)
    max_hunger = Column(Integer, default=100)
