from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.item import GroundItemModel, ItemTemplateModel


class ItemRepository:

    @staticmethod
    async def get_template(session: AsyncSession, item_id: str) -> dict | None:
        stmt = select(ItemTemplateModel).where(ItemTemplateModel.item_id == item_id)
        result = await session.execute(stmt)
        row = result.scalars().first()
        return dict(row.__dict__) if row else None

    @staticmethod
    async def get_all_templates(session: AsyncSession) -> list:
        stmt = select(ItemTemplateModel)
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def get_ground_items(session: AsyncSession, location_id: str) -> list:
        stmt = select(GroundItemModel).where(GroundItemModel.location_id == location_id)
        result = await session.execute(stmt)
        rows = [dict(r.__dict__) for r in result.scalars().all()]

        enriched = []
        for g in rows:
            t = await ItemRepository.get_template(session, g["item_id"])
            if t:
                g["name"] = t.get("name")
                g["description"] = t.get("description")
                g["rarity"] = t.get("rarity")
            enriched.append(g)
        return enriched

    @staticmethod
    async def add_ground_item(session: AsyncSession, location_id: str, item_id: str, qty: int = 1):
        from datetime import datetime
        item = GroundItemModel(
            location_id=location_id,
            item_id=item_id,
            quantity=qty,
            spawned_at=datetime.utcnow().isoformat(),
        )
        session.add(item)
        await session.commit()

    @staticmethod
    async def remove_ground_item(session: AsyncSession, ground_item_id: int):
        stmt = delete(GroundItemModel).where(GroundItemModel.id == ground_item_id)
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def remove_ground_item_by_coords(session: AsyncSession, location_id: str, item_id: str):
        stmt = delete(GroundItemModel).where(
            GroundItemModel.location_id == location_id,
            GroundItemModel.item_id == item_id,
        )
        await session.execute(stmt)
        await session.commit()
