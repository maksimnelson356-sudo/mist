import json
from sqlalchemy import select

from database.base import get_db
from database.models.item import ItemTemplateModel
from domain.events import EventType, Importance


RARITY_WEIGHTS = {
    "common": 1.0,
    "uncommon": 1.5,
    "rare": 2.5,
    "epic": 4.0,
    "legendary": 8.0,
}

RARITY_NAMES = {
    "common": "Обычный",
    "uncommon": "Необычный",
    "rare": "Редкий",
    "epic": "Эпический",
    "legendary": "Легендарный",
}


class CatalogService:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def get(self, item_id: str) -> dict | None:
        async for db in get_db():
            stmt = select(ItemTemplateModel).where(ItemTemplateModel.item_id == item_id)
            result = await db.execute(stmt)
            item = result.scalar_one_or_none()
            return self._to_dict(item) if item else None
        return None

    async def get_all(self, rarity: str = None) -> list:
        async for db in get_db():
            stmt = select(ItemTemplateModel)
            if rarity:
                stmt = stmt.where(ItemTemplateModel.rarity == rarity)
            result = await db.execute(stmt)
            items = result.scalars().all()
            return [self._to_dict(i) for i in items]
        return []

    async def search(self, query: str) -> list:
        async for db in get_db():
            stmt = select(ItemTemplateModel)
            result = await db.execute(stmt)
            items = result.scalars().all()
            query_lower = query.lower()
            return [
                self._to_dict(i) for i in items
                if query_lower in i.name.lower() or query_lower in (i.description or "").lower()
            ]
        return []

    async def get_by_rarity(self, rarity: str) -> list:
        return await self.get_all(rarity=rarity)

    async def get_usable(self) -> list:
        async for db in get_db():
            stmt = select(ItemTemplateModel).where(ItemTemplateModel.is_usable == True)
            result = await db.execute(stmt)
            items = result.scalars().all()
            return [self._to_dict(i) for i in items]
        return []

    def get_rarity_name(self, rarity: str) -> str:
        return RARITY_NAMES.get(rarity, "Неизвестный")

    def get_rarity_weight(self, rarity: str) -> float:
        return RARITY_WEIGHTS.get(rarity, 1.0)

    def get_item_value(self, item: dict, quantity: int = 1) -> int:
        base = item.get("base_value", 0)
        weight = RARITY_WEIGHTS.get(item.get("rarity", "common"), 1.0)
        return int(base * weight * quantity)

    @staticmethod
    def _to_dict(row: ItemTemplateModel) -> dict:
        return {
            "id": row.id,
            "item_id": row.item_id,
            "name": row.name,
            "description": row.description,
            "rarity": row.rarity,
            "weight": row.weight,
            "base_value": row.base_value,
            "is_usable": row.is_usable,
            "use_effect": json.loads(row.use_effect) if isinstance(row.use_effect, str) else row.use_effect,
            "lore": row.lore,
        }
