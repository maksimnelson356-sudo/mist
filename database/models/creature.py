from sqlalchemy import Column, String, Integer, Text, Boolean
from database.base import Base


class CreatureModel(Base):
    __tablename__ = "creatures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creature_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(50), nullable=True)
    disposition = Column(String(20), default="neutral")
    memory_with_users = Column(Text, default="{}")
    is_alive = Column(Boolean, default=True)
    spawn_data = Column(Text, default="{}")
    hp = Column(Integer, default=50)
    max_hp = Column(Integer, default=50)
    attack = Column(Integer, default=8)
    defense = Column(Integer, default=3)
    xp_reward = Column(Integer, default=20)
    loot_table = Column(Text, default="[]")
