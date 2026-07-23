import json
import random
from datetime import datetime
from database.db import get_pool


# ──────────────────────────────────────────────
#  Пользователи
# ──────────────────────────────────────────────

async def get_or_create_user(user_id: int, username: str = None) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE user_id = $1", user_id
        )
        if not user:
            display_name = username or f"Путник_{user_id % 10000}"
            await conn.execute(
                """INSERT INTO users (user_id, username, display_name)
                   VALUES ($1, $2, $3)""",
                user_id, username, display_name
            )
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1", user_id
            )
            await _log_action(user_id, "new_user", {"username": username})
        return dict(user)


async def update_user(user_id: int, **kwargs):
    pool = await get_pool()
    async with pool.acquire() as conn:
        sets = []
        values = []
        idx = 1
        for key, val in kwargs.items():
            if isinstance(val, dict):
                val = json.dumps(val)
            sets.append(f"{key} = ${idx}")
            values.append(val)
            idx += 1
        values.append(user_id)
        await conn.execute(
            f"UPDATE users SET {', '.join(sets)} WHERE user_id = ${idx}",
            *values
        )


# ──────────────────────────────────────────────
#  Действия (память мира)
# ──────────────────────────────────────────────

async def _log_action(user_id: int, action_type: str, action_data: dict = None, location: str = None):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO actions (user_id, action_type, action_data, location)
               VALUES ($1, $2, $3, $4)""",
            user_id, action_type, json.dumps(action_data or {}), location
        )


async def get_user_actions(user_id: int, action_type: str = None, limit: int = 50) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        if action_type:
            rows = await conn.fetch(
                """SELECT * FROM actions WHERE user_id = $1 AND action_type = $2
                   ORDER BY created_at DESC LIMIT $3""",
                user_id, action_type, limit
            )
        else:
            rows = await conn.fetch(
                """SELECT * FROM actions WHERE user_id = $1
                   ORDER BY created_at DESC LIMIT $2""",
                user_id, limit
            )
        return [dict(r) for r in rows]


async def count_actions(action_type: str = None) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        if action_type:
            row = await conn.fetchrow(
                "SELECT COUNT(*) FROM actions WHERE action_type = $1", action_type
            )
        else:
            row = await conn.fetchrow("SELECT COUNT(*) FROM actions")
        return row[0]


# ──────────────────────────────────────────────
#  Инвентарь
# ──────────────────────────────────────────────

async def add_item(user_id: int, item_id: str, quantity: int = 1, is_magic: bool = False):
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            """SELECT id, quantity FROM inventory
               WHERE user_id = $1 AND item_id = $2 AND is_magic = $3""",
            user_id, item_id, is_magic
        )
        if existing:
            await conn.execute(
                "UPDATE inventory SET quantity = quantity + $1 WHERE id = $2",
                quantity, existing["id"]
            )
        else:
            await conn.execute(
                """INSERT INTO inventory (user_id, item_id, quantity, is_magic)
                   VALUES ($1, $2, $3, $4)""",
                user_id, item_id, quantity, is_magic
            )
        await _log_action(user_id, "item_gain", {"item_id": item_id, "qty": quantity})


async def remove_item(user_id: int, item_id: str, quantity: int = 1) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id, quantity FROM inventory WHERE user_id = $1 AND item_id = $2",
            user_id, item_id
        )
        if not existing or existing["quantity"] < quantity:
            return False
        if existing["quantity"] == quantity:
            await conn.execute("DELETE FROM inventory WHERE id = $1", existing["id"])
        else:
            await conn.execute(
                "UPDATE inventory SET quantity = quantity - $1 WHERE id = $2",
                quantity, existing["id"]
            )
        await _log_action(user_id, "item_loss", {"item_id": item_id, "qty": quantity})
        return True


async def get_inventory(user_id: int) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT i.*, t.name, t.description, t.rarity
               FROM inventory i
               LEFT JOIN item_templates t ON i.item_id = t.item_id
               WHERE i.user_id = $1 ORDER BY i.created_at""",
            user_id
        )
        return [dict(r) for r in rows]


# ──────────────────────────────────────────────
#  Локации
# ──────────────────────────────────────────────

async def get_location(location_id: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM locations WHERE location_id = $1", location_id
        )
        return dict(row) if row else None


async def move_user(user_id: int, target_location: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT current_location FROM users WHERE user_id = $1", user_id
        )
        loc = await conn.fetchrow(
            "SELECT * FROM locations WHERE location_id = $1", target_location
        )

        if not loc:
            return {"success": False, "message": "Эта область не существует... или ещё не открыта."}

        if loc["is_secret"] and loc["discovered_by"] and loc["discovered_by"] != user_id:
            user_obj = await conn.fetchrow(
                "SELECT karma FROM users WHERE user_id = $1", user_id
            )
            if user_obj["karma"] < loc.get("required_karma", 0):
                return {"success": False, "message": "Туман не пускает тебя дальше..."}

        connections = json.loads(loc["connections"]) if isinstance(loc["connections"], str) else loc["connections"]
        if user["current_location"] not in connections and target_location not in connections:
            return {"success": False, "message": "Ты не можешь попасть отсюда directly."}

        await conn.execute(
            "UPDATE users SET current_location = $1 WHERE user_id = $2",
            target_location, user_id
        )

        if not loc["discovered"]:
            await conn.execute(
                """UPDATE locations SET discovered = TRUE, discovered_by = $1, discovered_at = NOW()
                   WHERE location_id = $2""",
                user_id, target_location
            )
            await _log_action(user_id, "location_discover", {"location": target_location})
            return {
                "success": True,
                "first_discover": True,
                "name": loc["name"],
                "description": loc["description"]
            }

        await _log_action(user_id, "move", {
            "from": user["current_location"],
            "to": target_location
        })
        return {
            "success": True,
            "first_discover": False,
            "name": loc["name"],
            "description": loc["description"]
        }


# ──────────────────────────────────────────────
#  Существа
# ──────────────────────────────────────────────

async def get_creatures_at_location(location_id: str) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM creatures WHERE location = $1 AND is_alive = TRUE",
            location_id
        )
        return [dict(r) for r in rows]


async def creature_remember(creature_id: str, user_id: int, action: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT memory_with_users FROM creatures WHERE creature_id = $1",
            creature_id
        )
        if not row:
            return
        memory = json.loads(row["memory_with_users"]) if isinstance(row["memory_with_users"], str) else row["memory_with_users"]
        uid_str = str(user_id)
        if uid_str not in memory:
            memory[uid_str] = []
        memory[uid_str].append({
            "action": action,
            "time": datetime.now().isoformat()
        })
        await conn.execute(
            "UPDATE creatures SET memory_with_users = $1 WHERE creature_id = $2",
            json.dumps(memory), creature_id
        )


async def get_creature_memory(creature_id: str, user_id: int) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT memory_with_users FROM creatures WHERE creature_id = $1",
            creature_id
        )
        if not row:
            return []
        memory = json.loads(row["memory_with_users"]) if isinstance(row["memory_with_users"], str) else row["memory_with_users"]
        return memory.get(str(user_id), [])


# ──────────────────────────────────────────────
#  Секреты
# ──────────────────────────────────────────────

async def check_secret_trigger(user_id: int, trigger_type: str, trigger_data: dict) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM secrets WHERE is_active = TRUE AND discovered_by IS NULL"
        )
        for row in rows:
            condition = json.loads(row["trigger_condition"]) if isinstance(row["trigger_condition"], str) else row["trigger_condition"]
            if condition.get("type") == trigger_type:
                if _check_condition(condition, trigger_data, user_id):
                    await conn.execute(
                        "UPDATE secrets SET discovered_by = $1, discovered_at = NOW() WHERE id = $2",
                        user_id, row["id"]
                    )
                    reward = json.loads(row["reward"]) if isinstance(row["reward"], str) else row["reward"]
                    await _log_action(user_id, "secret_found", {
                        "secret_id": row["secret_id"],
                        "name": row["name"]
                    })
                    return {"name": row["name"], "description": row["description"], "reward": reward}
        return None


def _check_condition(condition: dict, data: dict, user_id: int) -> bool:
    ctype = condition.get("type")
    if ctype == "visit_location":
        return data.get("location") == condition.get("location")
    elif ctype == "collect_item":
        return data.get("item_id") == condition.get("item_id")
    elif ctype == "karma_above":
        return data.get("karma", 0) >= condition.get("value", 0)
    elif ctype == "days_in_mist":
        return data.get("days", 0) >= condition.get("value", 0)
    elif ctype == "action_count":
        return data.get("count", 0) >= condition.get("value", 0)
    return False


# ──────────────────────────────────────────────
#  Мировые события
# ──────────────────────────────────────────────

async def get_active_events() -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM world_events WHERE is_active = TRUE"
        )
        return [dict(r) for r in rows]


async def trigger_world_event(event_id: str) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM world_events WHERE event_id = $1", event_id
        )
        if not row:
            return None
        await conn.execute(
            "UPDATE world_events SET is_active = TRUE WHERE event_id = $1", event_id
        )
        return dict(row)


# ──────────────────────────────────────────────
#  Энциклопедия / Легенды
# ──────────────────────────────────────────────

async def discover_legend(legend_id: str, category: str, name: str, description: str, user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT * FROM legends WHERE legend_id = $1", legend_id
        )
        if existing:
            await conn.execute(
                "UPDATE legends SET times_discovered = times_discovered + 1 WHERE legend_id = $1",
                legend_id
            )
            return False
        else:
            await conn.execute(
                """INSERT INTO legends (legend_id, category, name, description, discovered_by, discovered_at, times_discovered)
                   VALUES ($1, $2, $3, $4, $5, NOW(), 1)""",
                legend_id, category, name, description, user_id
            )
            await _log_action(user_id, "legend_discover", {"legend_id": legend_id, "name": name})
            return True


async def get_legend_stats() -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        creatures = await conn.fetchrow("SELECT COUNT(*) FROM legends WHERE category = 'creature'")
        items = await conn.fetchrow("SELECT COUNT(*) FROM legends WHERE category = 'item'")
        places = await conn.fetchrow("SELECT COUNT(*) FROM legends WHERE category = 'location'")
        lore = await conn.fetchrow("SELECT COUNT(*) FROM legends WHERE category = 'lore'")
        return {
            "creatures_found": creatures[0],
            "items_found": items[0],
            "places_found": places[0],
            "lore_found": lore[0]
        }
