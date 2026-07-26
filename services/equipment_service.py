from sqlalchemy import select

from database.base import get_db
from database.models.inventory import InventoryModel, UserEquipmentModel
from database.models.item import ItemTemplateModel


class EquipmentService:

    EQUIPMENT_SLOTS = {"weapon": "⚔️ Оружие", "armor": "🛡️ Броня", "accessory": "💍 Аксессуар"}

    EQUIPMENT_STATS = {
        "wolf_fang_dagger": {"slot": "weapon", "attack": 3, "defense": 0, "max_hp": 0},
        "crystal_blade": {"slot": "weapon", "attack": 8, "defense": 0, "max_hp": 0},
        "grove_amulet": {"slot": "accessory", "attack": 0, "defense": 2, "max_hp": 15},
        "obsidian_armour": {"slot": "armor", "attack": 0, "defense": 7, "max_hp": 0},
        "mine_pickaxe": {"slot": "weapon", "attack": 4, "defense": 1, "max_hp": 0},
        "enchanted_compass": {"slot": "accessory", "attack": 1, "defense": 1, "max_hp": 10},
        "soul_bottle": {"slot": "accessory", "attack": 2, "defense": 0, "max_hp": 20},
        "shadow_cloak": {"slot": "armor", "attack": 0, "defense": 5, "max_hp": 10},
        "bone_sword": {"slot": "weapon", "attack": 5, "defense": 0, "max_hp": 0},
        "witch_brew": {"slot": "accessory", "attack": 0, "defense": 0, "max_hp": 30},
        "frost_ring": {"slot": "accessory", "attack": 2, "defense": 2, "max_hp": 0},
        "iron_shield": {"slot": "armor", "attack": 0, "defense": 4, "max_hp": 5},
    }

    def __init__(self):
        pass

    async def get_equipment(self, user_id: int) -> dict:
        async for db in get_db():
            stmt = select(UserEquipmentModel).where(UserEquipmentModel.user_id == user_id)
            result = await db.execute(stmt)
            rows = result.scalars().all()
            equip = {}
            for row in rows:
                tmpl = await self._get_item_template(row.item_id, db)
                equip[row.slot] = {
                    "id": row.id,
                    "user_id": row.user_id,
                    "slot": row.slot,
                    "item_id": row.item_id,
                    "equipped_at": row.equipped_at,
                    "name": tmpl["name"] if tmpl else row.item_id,
                    "stats": self.EQUIPMENT_STATS.get(row.item_id, {}),
                }
            return equip
        return {}

    async def equip(self, user_id: int, item_id: str) -> dict:
        info = self.EQUIPMENT_STATS.get(item_id)
        if not info:
            return {"success": False, "message": "Этот предмет нельзя экипировать."}

        slot = info["slot"]

        async for db in get_db():
            inv_stmt = select(InventoryModel).where(
                InventoryModel.user_id == user_id,
                InventoryModel.item_id == item_id,
                InventoryModel.quantity > 0,
            )
            inv_result = await db.execute(inv_stmt)
            inv_item = inv_result.scalar_one_or_none()
            if not inv_item:
                return {"success": False, "message": "У тебя нет этого предмета."}

            existing_stmt = select(UserEquipmentModel).where(
                UserEquipmentModel.user_id == user_id,
                UserEquipmentModel.slot == slot,
            )
            existing_result = await db.execute(existing_stmt)
            existing = existing_result.scalar_one_or_none()
            if existing:
                await self.unequip(user_id, slot)

            db.add(UserEquipmentModel(user_id=user_id, slot=slot, item_id=item_id))

            if inv_item.quantity == 1:
                await db.delete(inv_item)
            else:
                inv_item.quantity -= 1

            await db.commit()

            slot_name = self.EQUIPMENT_SLOTS.get(slot, slot)
            item_tmpl = await self._get_item_template(item_id, db)
            item_name = item_tmpl["name"] if item_tmpl else item_id

            return {"success": True, "message": f"⚔️ Экипировано: {slot_name} → {item_name}"}
        return {"success": False, "message": "Ошибка базы данных."}

    async def unequip(self, user_id: int, slot: str) -> dict:
        async for db in get_db():
            existing_stmt = select(UserEquipmentModel).where(
                UserEquipmentModel.user_id == user_id,
                UserEquipmentModel.slot == slot,
            )
            existing_result = await db.execute(existing_stmt)
            existing = existing_result.scalar_one_or_none()
            if not existing:
                return {"success": False, "message": "В этом слоте ничего нет."}

            inv_stmt = select(InventoryModel).where(
                InventoryModel.user_id == user_id,
                InventoryModel.item_id == existing.item_id,
                InventoryModel.is_magic == False,
            )
            inv_result = await db.execute(inv_stmt)
            inv_item = inv_result.scalar_one_or_none()

            if inv_item:
                inv_item.quantity += 1
            else:
                db.add(InventoryModel(
                    user_id=user_id, item_id=existing.item_id, quantity=1,
                ))

            await db.delete(existing)
            await db.commit()

            return {"success": True, "message": f"Снято из слота {self.EQUIPMENT_SLOTS.get(slot, slot)}."}
        return {"success": False, "message": "Ошибка базы данных."}

    async def get_bonuses(self, user_id: int) -> dict:
        equip = await self.get_equipment(user_id)
        bonuses = {"attack": 0, "defense": 0, "max_hp": 0}
        for slot, item in equip.items():
            stats = item.get("stats", {})
            bonuses["attack"] += stats.get("attack", 0)
            bonuses["defense"] += stats.get("defense", 0)
            bonuses["max_hp"] += stats.get("max_hp", 0)
        return bonuses

    async def _get_item_template(self, item_id: str, db) -> dict | None:
        stmt = select(ItemTemplateModel).where(ItemTemplateModel.item_id == item_id)
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return None
        return {"item_id": row.item_id, "name": row.name, "description": row.description, "rarity": row.rarity}
