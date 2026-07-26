from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.shop import ShopItemModel


class ShopRepository:

    @staticmethod
    async def get_shop_items(session: AsyncSession, shop_id: str) -> list:
        stmt = select(ShopItemModel).where(
            ShopItemModel.shop_id == shop_id,
            ShopItemModel.stock != 0,
        )
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def get_shop_entry(session: AsyncSession, shop_id: str, item_id: str) -> dict | None:
        stmt = select(ShopItemModel).where(
            ShopItemModel.shop_id == shop_id,
            ShopItemModel.item_id == item_id,
        )
        result = await session.execute(stmt)
        row = result.scalars().first()
        return dict(row.__dict__) if row else None

    @staticmethod
    async def reduce_stock(session: AsyncSession, shop_id: str, item_id: str):
        stmt = select(ShopItemModel).where(
            ShopItemModel.shop_id == shop_id,
            ShopItemModel.item_id == item_id,
        )
        result = await session.execute(stmt)
        row = result.scalars().first()
        if row and row.stock > 0:
            row.stock -= 1
            await session.commit()

    @staticmethod
    async def seed_shop(session: AsyncSession):
        items = [
            ("fishing_village", "healing_herb", 5, -1, 1, 0),
            ("fishing_village", "swamp_root", 8, -1, 1, 0),
            ("fishing_village", "wolf_fang", 10, -1, 1, 0),
            ("fishing_village", "light_leaf", 12, -1, 2, 0),
            ("market_square", "obsidian_shard", 15, -1, 2, 0),
            ("market_square", "serpent_scale", 12, -1, 2, 0),
            ("market_square", "frost_shard", 18, -1, 3, 0),
            ("market_square", "shadow_essence", 25, 5, 3, 0),
            ("shadow_market", "echo_crystal", 40, 3, 5, 5),
            ("shadow_market", "gargoyle_eye", 60, 2, 7, 10),
            ("shadow_market", "mirror_fragment", 55, 2, 6, 8),
            ("shadow_market", "frozen_tear", 35, -1, 4, 3),
            ("shadow_market", "soul_bottle", 100, 1, 10, 15),
            ("temple_of_shadows", "dark_shard", 20, -1, 3, -5),
            ("temple_of_shadows", "bloodstone", 30, 5, 5, -3),
            ("temple_of_shadows", "arcane_dust", 8, -1, 1, 0),
            ("abandoned_mine", "raw_crystal", 10, -1, 2, 0),
            ("abandoned_mine", "crystal_thread", 22, 3, 4, 0),
            ("abandoned_mine", "spider_venom", 18, 4, 3, 0),
        ]
        for shop_id, item_id, price, stock, req_level, req_karma in items:
            existing = await ShopRepository.get_shop_entry(session, shop_id, item_id)
            if not existing:
                session.add(ShopItemModel(
                    shop_id=shop_id, item_id=item_id, price=price,
                    stock=stock, required_level=req_level, required_karma=req_karma,
                ))
        await session.commit()
