from sqlalchemy import Column, String, Integer, Text, Boolean
from database.base import Base


class CraftingRecipeModel(Base):
    __tablename__ = "crafting_recipes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    result_item = Column(String(50), nullable=False)
    result_qty = Column(Integer, default=1)
    ingredients = Column(Text, default="[]")
    required_location = Column(String(50), nullable=True)
    required_level = Column(Integer, default=1)
    xp_reward = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)


class UserCraftingModel(Base):
    __tablename__ = "user_crafting"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    recipe_id = Column(String(50), nullable=False)
    times_crafted = Column(Integer, default=1)
