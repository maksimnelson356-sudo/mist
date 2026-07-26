from sqlalchemy import Column, Integer, String

from database.base import Base


class ShopItemModel(Base):
    __tablename__ = "shop_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shop_id = Column(String(50), nullable=False)
    item_id = Column(String(50), nullable=False)
    price = Column(Integer, nullable=False)
    stock = Column(Integer, default=-1)
    required_level = Column(Integer, default=0)
    required_karma = Column(Integer, default=0)
