import json

from sqlalchemy import select, update

from database.base import get_db
from database.models.crafting import CraftingRecipeModel, UserCraftingModel
from database.models.inventory import InventoryModel
from database.models.user import UserModel
from database.models.location import LocationModel
from domain.events import EventType, Importance


class CraftingService:

    def __init__(self, chronicle, user_service, inventory_service):
        self.chronicle = chronicle
        self.user_service = user_service
        self.inventory = inventory_service

    async def get_recipes(self, location: str = None) -> list:
        async for db in get_db():
            stmt = select(CraftingRecipeModel).where(CraftingRecipeModel.is_active == True)
            if location:
                stmt = stmt.where(
                    (CraftingRecipeModel.required_location == location) |
                    (CraftingRecipeModel.required_location == None)
                )
            result = await db.execute(stmt)
            rows = result.scalars().all()
            return [self._recipe_to_dict(r) for r in rows]
        return []

    async def craft(self, user_id: int, recipe_id: str) -> dict:
        async for db in get_db():
            stmt = select(CraftingRecipeModel).where(CraftingRecipeModel.recipe_id == recipe_id)
            result = await db.execute(stmt)
            recipe = result.scalar_one_or_none()

            if not recipe:
                return {"success": False, "message": "Рецепт не найден."}

            user = await self.user_service.get(user_id)
            if user["level"] < recipe.required_level:
                return {"success": False, "message": f"Нужен уровень {recipe.required_level}."}

            if recipe.required_location and user["current_location"] != recipe.required_location:
                loc_stmt = select(LocationModel).where(LocationModel.location_id == recipe.required_location)
                loc_result = await db.execute(loc_stmt)
                loc = loc_result.scalar_one_or_none()
                loc_name = loc.name if loc else recipe.required_location
                return {"success": False, "message": f"Крафтить можно только в «{loc_name}»."}

            ingredients = json.loads(recipe.ingredients) if isinstance(recipe.ingredients, str) else recipe.ingredients
            for ing in ingredients:
                has = await self.inventory.has(user_id, ing["item_id"], ing.get("qty", 1))
                if not has:
                    t_stmt = select(InventoryModel).where(
                        InventoryModel.user_id == user_id,
                        InventoryModel.item_id == ing["item_id"],
                    )
                    return {"success": False, "message": f"Не хватает: {ing['item_id']} x{ing.get('qty', 1)}"}

            for ing in ingredients:
                await self.inventory.remove(user_id, ing["item_id"], ing.get("qty", 1))

            await self.inventory.add(user_id, recipe.result_item, recipe.result_qty)

            new_xp = user["xp"] + recipe.xp_reward
            new_level = user["level"]
            leveled = False
            while new_xp >= new_level * 100:
                new_level += 1
                new_xp -= (new_level - 1) * 100
                leveled = True
            if leveled:
                await self._apply_level_up(user_id, new_level, db)
            await db.execute(
                update(UserModel).where(UserModel.user_id == user_id).values(xp=new_xp, level=new_level)
            )

            uc_stmt = select(UserCraftingModel).where(
                UserCraftingModel.user_id == user_id,
                UserCraftingModel.recipe_id == recipe_id,
            )
            uc_result = await db.execute(uc_stmt)
            existing = uc_result.scalar_one_or_none()
            if existing:
                existing.times_crafted += 1
            else:
                db.add(UserCraftingModel(user_id=user_id, recipe_id=recipe_id))

            await db.commit()

            await self.chronicle.publish(
                EventType.CRAFT_COMPLETED,
                f"Скрафчен: {recipe.name}",
                player_id=user_id,
                importance=Importance.COMMON,
                metadata={"recipe_id": recipe_id, "item": recipe.result_item},
            )

            return {
                "success": True,
                "message": f"⚒️ Скрафтил «{recipe.name}» x{recipe.result_qty}\n⭐ +{recipe.xp_reward} XP",
            }
        return {"success": False, "message": "Ошибка базы данных."}

    async def _apply_level_up(self, user_id: int, new_level: int, db):
        new_max_hp = 100 + (new_level - 1) * 15
        new_attack = 10 + (new_level - 1) * 3
        new_defense = 5 + (new_level - 1) * 2
        await db.execute(
            update(UserModel).where(UserModel.user_id == user_id).values(
                level=new_level, max_hp=new_max_hp, attack=new_attack, defense=new_defense,
            )
        )
        await db.commit()

    @staticmethod
    def _recipe_to_dict(row: CraftingRecipeModel) -> dict:
        return {
            "id": row.id,
            "recipe_id": row.recipe_id,
            "name": row.name,
            "description": row.description,
            "result_item": row.result_item,
            "result_qty": row.result_qty,
            "ingredients": json.loads(row.ingredients) if isinstance(row.ingredients, str) else row.ingredients,
            "required_location": row.required_location,
            "required_level": row.required_level,
            "xp_reward": row.xp_reward,
            "is_active": row.is_active,
        }

    async def get_history(self, user_id: int, limit: int = 10) -> list:
        async for db in get_db():
            stmt = (
                select(UserCraftingModel)
                .where(UserCraftingModel.user_id == user_id)
                .order_by(UserCraftingModel.id.desc())
                .limit(limit)
            )
            result = await db.execute(stmt)
            rows = result.scalars().all()
            return [
                {"recipe_id": r.recipe_id, "times_crafted": r.times_crafted}
                for r in rows
            ]
        return []
