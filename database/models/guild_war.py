import uuid

from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from database.base import Base


class GuildWarModel(Base):
    __tablename__ = "guild_wars"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    attacker_guild_id = Column(String(50), nullable=False, index=True)
    defender_guild_id = Column(String(50), nullable=False, index=True)
    location_id = Column(String(50), nullable=False)
    status = Column(String(20), default="active")
    attacker_wins = Column(Integer, default=0)
    defender_wins = Column(Integer, default=0)
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime, nullable=True)
    events = Column(JSON, default=list)
