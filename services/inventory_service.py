import json

from sqlalchemy import select, update, delete

from database.base import get_db
from database.models.inventory import InventoryModel
from database.models.item import ItemTemplateModel
from database.models.user import UserModel
from domain.events import EventType, Importance


class InventoryService:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def add(self, user_id: int, item_id: str, qty: int = 1, is_magic: bool = False):
        async for db in get_db():
            magic_int = is_magic
            stmt = select(InventoryModel).where(
                InventoryModel.user_id == user_id,
                InventoryModel.item_id == item_id,
                InventoryModel.is_magic == magic_int,
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.quantity += qty
            else:
                db.add(InventoryModel(
                    user_id=user_id,
                    item_id=item_id,
                    quantity=qty,
                    is_magic=magic_int,
                ))
            await db.commit()

            t = await self._get_item_template(item_id)
            if t:
                await self.chronicle.publish(
                    EventType.ITEM_OBTAINED,
                    f"Получен предмет: {t['name']} x{qty}",
                    player_id=user_id,
                    importance=Importance.TRIVIAL,
                    metadata={"item_id": item_id, "qty": qty},
                )
            break

    async def remove(self, user_id: int, item_id: str, qty: int = 1) -> bool:
        async for db in get_db():
            stmt = select(InventoryModel).where(
                InventoryModel.user_id == user_id,
                InventoryModel.item_id == item_id,
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing or existing.quantity < qty:
                return False

            if existing.quantity == qty:
                await db.delete(existing)
            else:
                existing.quantity -= qty

            await db.commit()
            return True
        return False

    async def get(self, user_id: int) -> list:
        async for db in get_db():
            stmt = select(InventoryModel).where(InventoryModel.user_id == user_id)
            result = await db.execute(stmt)
            rows = result.scalars().all()

            items = []
            for row in rows:
                t = await self._get_item_template(row.item_id)
                items.append({
                    "id": row.id,
                    "user_id": row.user_id,
                    "item_id": row.item_id,
                    "quantity": row.quantity,
                    "is_magic": row.is_magic,
                    "name": t["name"] if t else row.item_id,
                    "description": t["description"] if t else "",
                    "rarity": t["rarity"] if t else "common",
                })
            return items
        return []

    async def has(self, user_id: int, item_id: str, qty: int = 1) -> bool:
        async for db in get_db():
            stmt = select(InventoryModel).where(
                InventoryModel.user_id == user_id,
                InventoryModel.item_id == item_id,
            )
            result = await db.execute(stmt)
            row = result.scalar_one_or_none()
            return row is not None and row.quantity >= qty
        return False

    async def use_item(self, user_id: int, item_id: str) -> dict:
        t = await self._get_item_template(item_id)
        if not t:
            return {"success": False, "message": "Предмет не найден."}

        if not await self.has(user_id, item_id, 1):
            return {"success": False, "message": "У тебя нет этого предмета."}

        if not t["is_usable"]:
            return {"success": False, "message": f"«{t['name']}» нельзя использовать."}

        effect = json.loads(t["use_effect"]) if isinstance(t["use_effect"], str) else t["use_effect"]

        async for db in get_db():
            user = await self._get_user(user_id, db)
            messages = []

            if "heal" in effect:
                heal = effect["heal"]
                old_hp = user["hp"]
                new_hp = min(user["max_hp"], old_hp + heal)
                actual_heal = new_hp - old_hp
                await db.execute(
                    update(UserModel).where(UserModel.user_id == user_id).values(hp=new_hp)
                )
                messages.append(f"💚 Восстановлено {actual_heal} HP")

            if "damage" in effect:
                messages.append(f"⚔️ Осколок наносит {effect['damage']} урона окружающим. Воздух дрожит.")

            if "xp" in effect:
                new_xp = user["xp"] + effect["xp"]
                new_level = user["level"]
                xp_needed = new_level * 100
                leveled = False
                while new_xp >= xp_needed:
                    new_level += 1
                    new_xp -= xp_needed
                    xp_needed = new_level * 100
                    leveled = True
                if leveled:
                    await self._apply_level_up(user_id, new_level, db)
                await db.execute(
                    update(UserModel).where(UserModel.user_id == user_id).values(xp=new_xp, level=new_level)
                )
                messages.append(f"⭐ +{effect['xp']} XP")

            if "level_up" in effect:
                new_level = user["level"] + 1
                await self._apply_level_up(user_id, new_level, db)
                fresh = await self._get_user(user_id, db)
                await db.execute(
                    update(UserModel).where(UserModel.user_id == user_id).values(hp=fresh["max_hp"])
                )
                messages.append("⭐ Уровень Increased!")

            if "light" in effect:
                messages.append("💡 Жемчужина светится тёплым светом. Ты видишь то, что было скрыто.")

            if "reveal_secret" in effect:
                messages.append("🔮 Кристалл шепчет тебе тайну. Ты чувствуешь, как воспоминания проникают в сознание.")

            if "vision" in effect:
                messages.append("👁 Глаз гаргульи открывается. Ты видишь сквозь стены на мгновение.")

            if "resurrect" in effect:
                messages.append("💀 Кольцо мёртвого короля пульсирует. Мёртвые шепчут тебе советы.")

            await self.remove(user_id, item_id, 1)

            await self.chronicle.publish(
                EventType.ITEM_USED,
                f"Использован: {t['name']}",
                player_id=user_id,
                importance=Importance.TRIVIAL,
                metadata={"item_id": item_id, "effect": effect},
            )

            await db.commit()
            return {"success": True, "message": f"🧪 Использовал «{t['name']}»\n" + "\n".join(messages)}
        return {"success": False, "message": "Ошибка базы данных."}

    async def _get_item_template(self, item_id: str) -> dict | None:
        async for db in get_db():
            stmt = select(ItemTemplateModel).where(ItemTemplateModel.item_id == item_id)
            result = await db.execute(stmt)
            row = result.scalar_one_or_none()
            if not row:
                return None
            return {
                "item_id": row.item_id,
                "name": row.name,
                "description": row.description,
                "rarity": row.rarity,
                "is_usable": row.is_usable,
                "use_effect": row.use_effect,
                "lore": row.lore,
            }
        return None

    async def _get_user(self, user_id: int, db) -> dict:
        stmt = select(UserModel).where(UserModel.user_id == user_id)
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return {}
        return {
            "user_id": row.user_id, "hp": row.hp, "max_hp": row.max_hp,
            "level": row.level, "xp": row.xp, "gold": row.gold,
            "attack": row.attack, "defense": row.defense,
        }

    async def _apply_level_up(self, user_id: int, new_level: int, db):
        new_max_hp = 100 + (new_level - 1) * 15
        new_attack = 10 + (new_level - 1) * 3
        new_defense = 5 + (new_level - 1) * 2
        await db.execute(
            update(UserModel).where(UserModel.user_id == user_id).values(
                level=new_level, max_hp=new_max_hp, attack=new_attack, defense=new_defense,
            )
        )
        await self.chronicle.publish(
            EventType.PLAYER_LEVEL_UP,
            f"Уровень повышен → {new_level}",
            player_id=user_id,
            importance=Importance.RARE,
            metadata={"new_level": new_level},
        )
