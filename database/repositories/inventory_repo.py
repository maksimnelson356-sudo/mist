import json
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.inventory import InventoryModel, UserEquipmentModel, UserStatusEffectModel


class InventoryRepository:

    @staticmethod
    async def add_item(session: AsyncSession, user_id: int, item_id: str, qty: int = 1, is_magic: bool = False):
        magic_int = 1 if is_magic else 0
        stmt = select(InventoryModel).where(
            InventoryModel.user_id == user_id,
            InventoryModel.item_id == item_id,
            InventoryModel.is_magic == magic_int,
        )
        result = await session.execute(stmt)
        existing = result.scalars().first()
        if existing:
            existing.quantity += qty
        else:
            session.add(InventoryModel(
                user_id=user_id, item_id=item_id, quantity=qty, is_magic=magic_int
            ))
        await session.commit()

    @staticmethod
    async def remove_item(session: AsyncSession, user_id: int, item_id: str, qty: int = 1) -> bool:
        stmt = select(InventoryModel).where(
            InventoryModel.user_id == user_id,
            InventoryModel.item_id == item_id,
        )
        result = await session.execute(stmt)
        existing = result.scalars().first()
        if not existing or existing.quantity < qty:
            return False
        if existing.quantity == qty:
            await session.delete(existing)
        else:
            existing.quantity -= qty
        await session.commit()
        return True

    @staticmethod
    async def get_inventory(session: AsyncSession, user_id: int) -> list:
        stmt = select(InventoryModel).where(InventoryModel.user_id == user_id)
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def has_item(session: AsyncSession, user_id: int, item_id: str, qty: int = 1) -> bool:
        stmt = select(InventoryModel).where(
            InventoryModel.user_id == user_id,
            InventoryModel.item_id == item_id,
        )
        result = await session.execute(stmt)
        row = result.scalars().first()
        return row is not None and row.quantity >= qty


class EquipmentRepository:

    @staticmethod
    async def get_equipment(session: AsyncSession, user_id: int) -> list:
        stmt = select(UserEquipmentModel).where(UserEquipmentModel.user_id == user_id)
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def equip(session: AsyncSession, user_id: int, slot: str, item_id: str):
        existing = await EquipmentRepository.get_in_slot(session, user_id, slot)
        if existing:
            await session.delete(existing)
            await session.commit()
        session.add(UserEquipmentModel(user_id=user_id, slot=slot, item_id=item_id))
        await session.commit()

    @staticmethod
    async def unequip(session: AsyncSession, user_id: int, slot: str) -> str | None:
        existing = await EquipmentRepository.get_in_slot(session, user_id, slot)
        if not existing:
            return None
        item_id = existing.item_id
        await session.delete(existing)
        await session.commit()
        return item_id

    @staticmethod
    async def get_in_slot(session: AsyncSession, user_id: int, slot: str) -> UserEquipmentModel | None:
        stmt = select(UserEquipmentModel).where(
            UserEquipmentModel.user_id == user_id,
            UserEquipmentModel.slot == slot,
        )
        result = await session.execute(stmt)
        return result.scalars().first()


class StatusEffectRepository:

    @staticmethod
    async def get_active(session: AsyncSession, user_id: int) -> list:
        stmt = select(UserStatusEffectModel).where(
            UserStatusEffectModel.user_id == user_id,
            UserStatusEffectModel.duration > 0,
        )
        result = await session.execute(stmt)
        return [dict(r.__dict__) for r in result.scalars().all()]

    @staticmethod
    async def apply(session: AsyncSession, user_id: int, effect_type: str,
                    potency: int = 1, duration: int = 3, source: str = "combat"):
        stmt = select(UserStatusEffectModel).where(
            UserStatusEffectModel.user_id == user_id,
            UserStatusEffectModel.effect_type == effect_type,
        )
        result = await session.execute(stmt)
        existing = result.scalars().first()
        if existing:
            existing.potency = potency
            existing.duration = duration
        else:
            session.add(UserStatusEffectModel(
                user_id=user_id, effect_type=effect_type,
                potency=potency, duration=duration, source=source,
            ))
        await session.commit()

    @staticmethod
    async def tick(session: AsyncSession, user_id: int) -> list:
        effects = await StatusEffectRepository.get_active(session, user_id)
        expired = []
        for e in effects:
            new_dur = e["duration"] - 1
            if new_dur <= 0:
                stmt = select(UserStatusEffectModel).where(
                    UserStatusEffectModel.user_id == user_id,
                    UserStatusEffectModel.effect_type == e["effect_type"],
                )
                result = await session.execute(stmt)
                row = result.scalars().first()
                if row:
                    await session.delete(row)
                expired.append(e["effect_type"])
            else:
                stmt = update(UserStatusEffectModel).where(
                    UserStatusEffectModel.user_id == user_id,
                    UserStatusEffectModel.effect_type == e["effect_type"],
                ).values(duration=new_dur)
                await session.execute(stmt)
        await session.commit()
        return expired

    @staticmethod
    async def clear_all(session: AsyncSession, user_id: int):
        from sqlalchemy import delete
        stmt = delete(UserStatusEffectModel).where(UserStatusEffectModel.user_id == user_id)
        await session.execute(stmt)
        await session.commit()
