import logging
from datetime import datetime, timedelta
from sqlalchemy import text
from database.base import get_db

logger = logging.getLogger("MIST.market")

ITEM_CATEGORIES = {
    "food": {"items": ["bread", "fish", "apple", "cheese", "dried_meat", "berry"], "base_demand": 10},
    "weapons": {"items": ["iron_sword", "iron_axe", "hunting_bow", "iron_dagger"], "base_demand": 5},
    "armor": {"items": ["leather_armor", "iron_shield", "wool_cloak"], "base_demand": 5},
    "potions": {"items": ["health_potion", "stamina_potion", "antidote"], "base_demand": 8},
    "tools": {"items": ["rope", "torch", "lockpick"], "base_demand": 6},
    "resources": {"items": ["iron_ore", "wood", "leather", "cloth"], "base_demand": 7},
    "magic": {"items": ["magic_crystal", "enchanted_gem", "arcane_dust"], "base_demand": 3},
}

REGION_PRICE_MODIFIERS = {
    "civilization": {"food": 1.0, "weapons": 0.9, "armor": 0.9, "potions": 1.1, "tools": 0.9, "resources": 1.1, "magic": 1.2},
    "dark_forest": {"food": 1.2, "weapons": 0.8, "armor": 0.8, "potions": 1.3, "tools": 0.7, "resources": 0.8, "magic": 1.5},
    "mountains": {"food": 1.3, "weapons": 0.7, "armor": 0.7, "potions": 1.4, "tools": 0.6, "resources": 0.6, "magic": 0.9},
    "coast": {"food": 0.8, "weapons": 1.0, "armor": 1.0, "potions": 1.2, "tools": 0.9, "resources": 1.0, "magic": 1.1},
}


class MarketService:

    def __init__(self, chronicle):
        self.chronicle = chronicle
        self._demand_cache = {}

    def get_item_category(self, item_id: str) -> str | None:
        for cat, info in ITEM_CATEGORIES.items():
            if item_id in info["items"]:
                return cat
        return None

    async def get_supply_demand(self, shop_id: str, region_id: str = None) -> dict:
        cache_key = f"{shop_id}:{region_id}"
        if cache_key in self._demand_cache:
            cached = self._demand_cache[cache_key]
            if datetime.utcnow() - cached["time"] < timedelta(minutes=5):
                return cached["data"]

        async for db in get_db():
            result = await db.execute(
                text("SELECT event_type, effects FROM world_event_records WHERE is_active = 1")
            )
            events = result.mappings().all()

            event_mods = {}
            for ev in events:
                effects = ev.get("effects", {})
                if "food_supply" in effects:
                    food_delta = effects["food_supply"]
                    event_mods["food"] = event_mods.get("food", 1.0) + (food_delta / 100)
                if "wealth" in effects:
                    wealth_delta = effects["wealth"]
                    event_mods["weapons"] = event_mods.get("weapons", 1.0) - (wealth_delta / 200)
                    event_mods["armor"] = event_mods.get("armor", 1.0) - (wealth_delta / 200)

            supply_demand = {}
            for cat, info in ITEM_CATEGORIES.items():
                base = info["base_demand"]
                event_mod = event_mods.get(cat, 1.0)
                region_mod = REGION_PRICE_MODIFIERS.get(region_id, {}).get(cat, 1.0) if region_id else 1.0

                demand = base * event_mod * region_mod
                supply_demand[cat] = round(demand, 2)

            self._demand_cache[cache_key] = {
                "data": supply_demand,
                "time": datetime.utcnow(),
            }
            return supply_demand

    def get_price_modifier(self, supply_demand: dict, category: str) -> float:
        demand = supply_demand.get(category, 10)
        if demand <= 3:
            return 0.75
        elif demand <= 6:
            return 0.90
        elif demand <= 10:
            return 1.00
        elif demand <= 15:
            return 1.15
        else:
            return 1.30

    def get_buy_price(self, base_price: int, supply_demand: dict, category: str, reputation: int = 0) -> int:
        mod = self.get_price_modifier(supply_demand, category)

        rep_mod = 1.0
        if reputation >= 100:
            rep_mod = 0.85
        elif reputation >= 50:
            rep_mod = 0.90
        elif reputation >= 0:
            rep_mod = 1.00
        elif reputation >= -50:
            rep_mod = 1.10
        else:
            rep_mod = 1.25

        return max(1, int(base_price * mod * rep_mod))

    def get_sell_price(self, base_price: int, supply_demand: dict, category: str) -> int:
        mod = self.get_price_modifier(supply_demand, category)
        sell_mod = 0.4 + (mod - 1.0) * 0.5
        return max(1, int(base_price * sell_mod))

    async def get_market_overview(self, region_id: str = None) -> dict:
        supply_demand = await self.get_supply_demand("global", region_id)

        overview = {}
        for cat, demand in supply_demand.items():
            mod = self.get_price_modifier(supply_demand, cat)
            if mod < 0.9:
                status = "📉 Дешевле обычного"
            elif mod > 1.1:
                status = "📈 Дороже обычного"
            else:
                status = "➡️ Нормальная цена"

            overview[cat] = {
                "demand": demand,
                "modifier": mod,
                "status": status,
            }

        return {
            "region": region_id or "Все регионы",
            "categories": overview,
        }

    async def record_purchase(self, item_id: str, category: str):
        cache_key = f"purchases:{category}"
        count = self._demand_cache.get(cache_key, 0) + 1
        self._demand_cache[cache_key] = count

        if count % 10 == 0:
            logger.info(f"Рынок: {category} — {count} покупок. Спрос растёт.")
