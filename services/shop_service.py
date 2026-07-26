import json
import logging

from sqlalchemy import select, update

from database.base import get_db
from database.models.shop import ShopItemModel
from database.models.item import ItemTemplateModel
from database.models.user import UserModel
from database.models.inventory import InventoryModel
from database.models.location import LocationModel
from domain.events import EventType, Importance

logger = logging.getLogger("MIST.shop")


class ShopService:

    SHOP_LOCATIONS = {
        "fishing_village": "Рыбацкая деревня",
        "market_square": "Торговая площадь",
        "shadow_market": "Теневой рынок",
        "temple_of_shadows": "Храм теней",
    }

    FOOD_ITEMS = {"berry", "fish", "bread", "cheese", "dried_meat", "apple", "food_ration"}

    def __init__(self, chronicle, user_service, inventory_service):
        self.chronicle = chronicle
        self.user_service = user_service
        self.inventory = inventory_service

    async def _get_world_price_modifier(self, item_id: str) -> float:
        modifier = 1.0
        try:
            from services.container import services
            world_state = services.world_engine.get_state()
            if not world_state:
                return modifier

            season = world_state.get("season", "spring")
            from sqlalchemy import text
            async for db in get_db():
                result = await db.execute(
                    text("SELECT food_supply, wealth, danger_level FROM locations ORDER BY RANDOM() LIMIT 1")
                )
                row = result.mappings().first()
                if not row:
                    break

                food = row.get("food_supply", 50)
                wealth = row.get("wealth", 30)
                danger = row.get("danger_level", 30)

                if item_id in self.FOOD_ITEMS:
                    if food < 30:
                        modifier *= 1.5
                    elif food < 50:
                        modifier *= 1.2
                    elif food > 70:
                        modifier *= 0.8

                if danger > 60:
                    modifier *= 1.15

                if season == "winter":
                    modifier *= 1.10
                elif season == "summer":
                    modifier *= 0.95

                break

            from services.weather_system import WEATHER_EFFECTS
            async for db in get_db():
                result = await db.execute(
                    text("SELECT current_weather FROM locations ORDER BY RANDOM() LIMIT 1")
                )
                row = result.mappings().first()
                if row:
                    weather = row.get("current_weather", "clear")
                    weather_mod = WEATHER_EFFECTS.get(weather, {}).get("price_modifier", 1.0)
                    modifier *= weather_mod
                break

        except Exception as e:
            logger.warning(f"World price modifier error: {e}", exc_info=True)

        return modifier

    async def get_shop_items(self, shop_id: str) -> list:
        async for db in get_db():
            stmt = select(ShopItemModel).where(
                ShopItemModel.shop_id == shop_id,
                ShopItemModel.stock != 0,
            )
            result = await db.execute(stmt)
            rows = result.scalars().all()
            items = []
            for row in rows:
                t = await self._get_item_template(row.item_id)
                items.append({
                    "id": row.id,
                    "shop_id": row.shop_id,
                    "item_id": row.item_id,
                    "price": row.price,
                    "stock": row.stock,
                    "required_level": row.required_level,
                    "required_karma": row.required_karma,
                    "name": t["name"] if t else row.item_id,
                    "description": t["description"] if t else "",
                    "rarity": t["rarity"] if t else "common",
                })
            return items
        return []

    async def buy(self, user_id: int, shop_id: str, item_id: str) -> dict:
        async for db in get_db():
            user = await self.user_service.get(user_id)

            stmt = select(ShopItemModel).where(
                ShopItemModel.shop_id == shop_id,
                ShopItemModel.item_id == item_id,
            )
            result = await db.execute(stmt)
            shop_entry = result.scalar_one_or_none()

            if not shop_entry:
                return {"success": False, "message": "Этого товара нет в магазине."}

            if shop_entry.stock == 0:
                return {"success": False, "message": "Этот товар закончился."}

            if user["level"] < shop_entry.required_level:
                return {"success": False, "message": f"Нужен уровень {shop_entry.required_level}."}

            if user["karma"] < shop_entry.required_karma:
                return {"success": False, "message": "Твоя карма слишком низка для этой покупки."}

            if user["gold"] < shop_entry.price:
                return {"success": False, "message": f"Недостаточно золота. Нужно: {shop_entry.price} 🪙, есть: {user['gold']} 🪙"}

            reputation = user.get("reputation", 0)
            if reputation >= 100:
                rep_mod = 0.85
            elif reputation >= 50:
                rep_mod = 0.90
            elif reputation >= 0:
                rep_mod = 1.0
            elif reputation >= -50:
                rep_mod = 1.10
            else:
                rep_mod = 1.25

            world_mod = await self._get_world_price_modifier(item_id)

            npc_mod = 1.0
            try:
                from services.npc_life_engine import get_trade_multiplier
                npc_mod = await get_trade_multiplier(user_id, shop_id)
            except Exception:
                pass

            event_mod = 1.0
            try:
                from services.container import services
                if services.daily_event:
                    bonuses = await services.daily_event.get_active_daily_bonuses()
                    if "shop_discount" in bonuses:
                        event_mod = bonuses["shop_discount"]
            except Exception:
                pass

            price = int(shop_entry.price * rep_mod * world_mod * npc_mod * event_mod)

            if user["gold"] < price:
                return {"success": False, "message": f"Недостаточно золота. Нужно: {price} 🪙, есть: {user['gold']} 🪙"}

            await db.execute(
                update(UserModel).where(UserModel.user_id == user_id).values(gold=user["gold"] - price)
            )

            inv_stmt = select(InventoryModel).where(
                InventoryModel.user_id == user_id,
                InventoryModel.item_id == item_id,
                InventoryModel.is_magic == False,
            )
            inv_result = await db.execute(inv_stmt)
            existing = inv_result.scalar_one_or_none()
            if existing:
                existing.quantity += 1
            else:
                db.add(InventoryModel(user_id=user_id, item_id=item_id, quantity=1))

            if shop_entry.stock > 0:
                shop_entry.stock -= 1

            await db.commit()

            t = await self._get_item_template(item_id)
            name = t["name"] if t else item_id

            await self.chronicle.publish(
                EventType.ITEM_BOUGHT,
                f"Куплен: {name}",
                player_id=user_id,
                importance=Importance.TRIVIAL,
                metadata={"item_id": item_id, "shop": shop_id, "price": shop_entry.price},
            )

            from services.container import services
            await services.analytics.track(
                "item_bought",
                user_id=user_id,
                data={"item_id": item_id, "price": shop_entry.price},
            )

            return {"success": True, "message": f"🛒 Купил «{name}» за {shop_entry.price} 🪙"}
        return {"success": False, "message": "Ошибка базы данных."}

    async def sell(self, user_id: int, item_id: str) -> dict:
        rarity_prices = {"common": 3, "rare": 8, "epic": 20, "legendary": 50}

        async for db in get_db():
            t = await self._get_item_template(item_id)
            if not t:
                return {"success": False, "message": "Предмет не найден."}

            stmt = select(InventoryModel).where(
                InventoryModel.user_id == user_id,
                InventoryModel.item_id == item_id,
            )
            result = await db.execute(stmt)
            inv_item = result.scalar_one_or_none()
            if not inv_item or inv_item.quantity < 1:
                return {"success": False, "message": "У тебя нет этого предмета."}

            base_price = rarity_prices.get(t["rarity"], 3)
            world_mod = await self._get_world_price_modifier(item_id)
            price = max(1, int(base_price * world_mod))

            if inv_item.quantity == 1:
                await db.delete(inv_item)
            else:
                inv_item.quantity -= 1

            user_stmt = select(UserModel).where(UserModel.user_id == user_id)
            user_result = await db.execute(user_stmt)
            user_row = user_result.scalar_one_or_none()
            user_row.gold += price

            await db.commit()

            await self.chronicle.publish(
                EventType.ITEM_SOLD,
                f"Продан: {t['name']}",
                player_id=user_id,
                importance=Importance.TRIVIAL,
                metadata={"item_id": item_id, "price": price},
            )

            return {"success": True, "message": f"💰 Продал «{t['name']}» за {price} 🪙"}
        return {"success": False, "message": "Ошибка базы данных."}

    async def is_nearby(self, loc1: str, loc2: str) -> bool:
        if loc1 == loc2:
            return True
        async for db in get_db():
            stmt = select(LocationModel).where(LocationModel.location_id == loc1)
            result = await db.execute(stmt)
            loc = result.scalar_one_or_none()
            if not loc:
                return False
            connections = json.loads(loc.connections) if isinstance(loc.connections, str) else loc.connections
            return loc2 in connections
        return False

    async def _get_item_template(self, item_id: str) -> dict | None:
        async for db in get_db():
            stmt = select(ItemTemplateModel).where(ItemTemplateModel.item_id == item_id)
            result = await db.execute(stmt)
            row = result.scalar_one_or_none()
            if not row:
                return None
            return {
                "item_id": row.item_id, "name": row.name,
                "description": row.description, "rarity": row.rarity,
            }
        return None

    SEASONAL_ITEMS = {
        "spring": [
            {"item_id": "healing_herb", "name": "Трава исцеления", "price": 8, "description": "Весенняя трава, полная жизни."},
            {"item_id": "light_leaf", "name": "Лист света", "price": 15, "description": "Сияющий лист, появляющийся весной."},
            {"item_id": "berry", "name": "Ягоды", "price": 3, "description": "Свежие ягоды первых цветов."},
        ],
        "summer": [
            {"item_id": "dried_meat", "name": "Сушёное мясо", "price": 12, "description": "Летний запас белка."},
            {"item_id": "fish", "name": "Рыба", "price": 6, "description": "Свежая летняя рыба."},
            {"item_id": "apple", "name": "Яблоко", "price": 4, "description": "Спелое летнее яблоко."},
        ],
        "autumn": [
            {"item_id": "swamp_root", "name": "Болотный корень", "price": 10, "description": "Осенний корень с целебными свойствами."},
            {"item_id": "wolf_fang", "name": "Волчий клык", "price": 18, "description": "Клык голодного волка."},
            {"item_id": "cheese", "name": "Сыр", "price": 8, "description": "Домашний сыр из осеннего молока."},
        ],
        "winter": [
            {"item_id": "frozen_tear", "name": "Замёрзшая слеза", "price": 25, "description": "Редкий зимний кристалл."},
            {"item_id": "shadow_essence", "name": "Суть тени", "price": 20, "description": "Сконденсированная теневая энергия."},
            {"item_id": "bread", "name": "Хлеб", "price": 5, "description": "Тёплый хлеб для холодных вечеров."},
        ],
    }

    async def get_seasonal_items(self, season: str) -> list:
        items = self.SEASONAL_ITEMS.get(season, [])
        if not items:
            return []
        item_ids = [item["item_id"] for item in items]
        templates = {}
        async for db in get_db():
            stmt = select(ItemTemplateModel).where(ItemTemplateModel.item_id.in_(item_ids))
            result = await db.execute(stmt)
            for row in result.scalars().all():
                templates[row.item_id] = {"item_id": row.item_id, "name": row.name, "description": row.description, "rarity": row.rarity}
            break
        return [{**item, **templates.get(item["item_id"], {"rarity": "common"})} for item in items]
