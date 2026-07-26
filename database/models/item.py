from sqlalchemy import Column, String, Integer, Text, Boolean, Float
from database.base import Base


class ItemTemplateModel(Base):
    __tablename__ = "item_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    rarity = Column(String(20), default="common")
    weight = Column(Float, default=1.0)
    base_value = Column(Integer, default=0)
    is_usable = Column(Boolean, default=False)
    use_effect = Column(Text, default="{}")
    lore = Column(Text, nullable=True)


class GroundItemModel(Base):
    __tablename__ = "ground_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    location_id = Column(String(50), nullable=False)
    item_id = Column(String(50), nullable=False)
    quantity = Column(Integer, default=1)
    respawn_hours = Column(Integer, default=0)
    spawned_at = Column(Text, nullable=True)


class SecretModel(Base):
    __tablename__ = "secrets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    secret_id = Column(String(50), unique=True, nullable=False)
    secret_type = Column(String(30), nullable=False)
    name = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    trigger_condition = Column(Text, default="{}")
    reward = Column(Text, default="{}")
    discovered_by = Column(Integer, nullable=True)
    discovered_at = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
