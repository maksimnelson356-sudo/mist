from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from database.base import Base


class InventoryModel(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    item_id = Column(String(50), nullable=False)
    quantity = Column(Integer, default=1)
    is_magic = Column(Boolean, default=False)
    enchantments = Column(Text, default="{}")
    created_at = Column(DateTime, server_default=func.now())


class UserEquipmentModel(Base):
    __tablename__ = "user_equipment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    slot = Column(String(20), nullable=False)
    item_id = Column(String(50), nullable=False)
    equipped_at = Column(DateTime, server_default=func.now())


class UserStatusEffectModel(Base):
    __tablename__ = "user_status_effects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    effect_type = Column(String(20), nullable=False)
    potency = Column(Integer, default=1)
    duration = Column(Integer, default=3)
    applied_at = Column(DateTime, server_default=func.now())
    source = Column(String(30), nullable=True)
