from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from database.base import Base


class WorldStateModel(Base):
    __tablename__ = "world_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_day = Column(Integer, default=1)
    game_hour = Column(Integer, default=8)
    game_minute = Column(Integer, default=0)
    season = Column(String(20), default="spring")
    world_pressure = Column(Integer, default=10)
    prosperity = Column(Integer, default=50)
    chaos = Column(Integer, default=10)
    magic_level = Column(Integer, default=20)
    danger_level = Column(Integer, default=30)
    total_population = Column(Integer, default=0)
    events_count = Column(Integer, default=0)
    last_tick_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
