import json
import random
from datetime import datetime
from database.db import get_db


# ──────────────────────────────────────────────
#  Пользователи
# ──────────────────────────────────────────────

async def _apply_level_up(user_id: int, new_level: int):
    db = await get_db()
    new_max_hp = 100 + (new_level - 1) * 15
    new_attack = 10 + (new_level - 1) * 3
    new_defense = 5 + (new_level - 1) * 2
    await db.execute(
        "UPDATE users SET level = ?, max_hp = ?, attack = ?, defense = ? WHERE user_id = ?",
        (new_level, new_max_hp, new_attack, new_defense, user_id)
    )
    await db.commit()


async def get_or_create_user(user_id: int, username: str = None) -> dict:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = await cursor.fetchone()
    if not row:
        display_name = username or f"Путник_{user_id % 10000}"
        await db.execute(
            "INSERT INTO users (user_id, username, display_name) VALUES (?, ?, ?)",
            (user_id, username, display_name)
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        await _log_action(user_id, "new_user", {"username": username})
    return dict(row)


async def update_user(user_id: int, **kwargs):
    db = await get_db()
    sets = []
    values = []
    for key, val in kwargs.items():
        if isinstance(val, dict):
            val = json.dumps(val)
        sets.append(f"{key} = ?")
        values.append(val)
    values.append(user_id)
    await db.execute(f"UPDATE users SET {', '.join(sets)} WHERE user_id = ?", values)
    await db.commit()


# ──────────────────────────────────────────────
#  Действия (память мира)
# ──────────────────────────────────────────────

async def _log_action(user_id: int, action_type: str, action_data: dict = None, location: str = None):
    db = await get_db()
    await db.execute(
        "INSERT INTO actions (user_id, action_type, action_data, location) VALUES (?, ?, ?, ?)",
        (user_id, action_type, json.dumps(action_data or {}), location)
    )
    await db.commit()


async def get_user_actions(user_id: int, action_type: str = None, limit: int = 50) -> list:
    db = await get_db()
    if action_type:
        cursor = await db.execute(
            "SELECT * FROM actions WHERE user_id = ? AND action_type = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, action_type, limit)
        )
    else:
        cursor = await db.execute(
            "SELECT * FROM actions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def count_actions(action_type: str = None) -> int:
    db = await get_db()
    if action_type:
        cursor = await db.execute("SELECT COUNT(*) FROM actions WHERE action_type = ?", (action_type,))
    else:
        cursor = await db.execute("SELECT COUNT(*) FROM actions")
    row = await cursor.fetchone()
    return row[0]


# ──────────────────────────────────────────────
#  Инвентарь
# ──────────────────────────────────────────────

async def add_item(user_id: int, item_id: str, quantity: int = 1, is_magic: bool = False):
    db = await get_db()
    magic_int = 1 if is_magic else 0
    cursor = await db.execute(
        "SELECT id, quantity FROM inventory WHERE user_id = ? AND item_id = ? AND is_magic = ?",
        (user_id, item_id, magic_int)
    )
    existing = await cursor.fetchone()
    if existing:
        await db.execute(
            "UPDATE inventory SET quantity = quantity + ? WHERE id = ?",
            (quantity, existing["id"])
        )
    else:
        await db.execute(
            "INSERT INTO inventory (user_id, item_id, quantity, is_magic) VALUES (?, ?, ?, ?)",
            (user_id, item_id, quantity, magic_int)
        )
    await db.commit()
    await _log_action(user_id, "item_gain", {"item_id": item_id, "qty": quantity})
    t = await get_item_template(item_id)
    if t:
        await discover_legend(f"item_{item_id}", "item", t["name"], t["description"], user_id)


async def remove_item(user_id: int, item_id: str, quantity: int = 1) -> bool:
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, quantity FROM inventory WHERE user_id = ? AND item_id = ?",
        (user_id, item_id)
    )
    existing = await cursor.fetchone()
    if not existing or existing["quantity"] < quantity:
        return False
    if existing["quantity"] == quantity:
        await db.execute("DELETE FROM inventory WHERE id = ?", (existing["id"],))
    else:
        await db.execute(
            "UPDATE inventory SET quantity = quantity - ? WHERE id = ?",
            (quantity, existing["id"])
        )
    await db.commit()
    await _log_action(user_id, "item_loss", {"item_id": item_id, "qty": quantity})
    return True


async def get_inventory(user_id: int) -> list:
    db = await get_db()
    cursor = await db.execute(
        """SELECT i.*, t.name, t.description, t.rarity
           FROM inventory i
           LEFT JOIN item_templates t ON i.item_id = t.item_id
           WHERE i.user_id = ? ORDER BY i.created_at""",
        (user_id,)
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


# ──────────────────────────────────────────────
#  Локации
# ──────────────────────────────────────────────

async def get_location(location_id: str) -> dict:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM locations WHERE location_id = ?", (location_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def move_user(user_id: int, target_location: str) -> dict:
    db = await get_db()
    cursor = await db.execute("SELECT current_location FROM users WHERE user_id = ?", (user_id,))
    user = await cursor.fetchone()
    cursor = await db.execute("SELECT * FROM locations WHERE location_id = ?", (target_location,))
    loc = await cursor.fetchone()

    if not loc:
        return {"success": False, "message": "Эта область не существует... или ещё не открыта."}

    loc = dict(loc)
    if loc["is_secret"] and loc["discovered_by"] and loc["discovered_by"] != user_id:
        cursor = await db.execute("SELECT karma FROM users WHERE user_id = ?", (user_id,))
        user_obj = await cursor.fetchone()
        if user_obj["karma"] < loc.get("required_karma", 0):
            return {"success": False, "message": "Туман не пускает тебя дальше..."}

    connections = json.loads(loc["connections"]) if isinstance(loc["connections"], str) else loc["connections"]
    if user["current_location"] not in connections and target_location not in connections:
        return {"success": False, "message": "Ты не можешь попасть отсюда напрямую."}

    await db.execute(
        "UPDATE users SET current_location = ? WHERE user_id = ?",
        (target_location, user_id)
    )
    await db.commit()

    if not loc["discovered"]:
        await db.execute(
            "UPDATE locations SET discovered = 1, discovered_by = ?, discovered_at = datetime('now') WHERE location_id = ?",
            (user_id, target_location)
        )
        await db.commit()
        await _log_action(user_id, "location_discover", {"location": target_location})
        return {
            "success": True,
            "first_discover": True,
            "name": loc["name"],
            "description": loc["description"]
        }

    await _log_action(user_id, "move", {"from": user["current_location"], "to": target_location})
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
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM creatures WHERE location = ? AND is_alive = 1",
        (location_id,)
    )
    rows = await cursor.fetchall()
    if not rows:
        cursor2 = await db.execute(
            "SELECT creature_id FROM creatures WHERE location = ? AND is_alive = 0",
            (location_id,)
        )
        dead = await cursor2.fetchall()
        for d in dead:
            if random.random() < 0.4:
                await db.execute("UPDATE creatures SET is_alive = 1, hp = max_hp WHERE creature_id = ?", (d["creature_id"],))
        await db.commit()
        cursor = await db.execute(
            "SELECT * FROM creatures WHERE location = ? AND is_alive = 1",
            (location_id,)
        )
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def creature_remember(creature_id: str, user_id: int, action: str):
    db = await get_db()
    cursor = await db.execute(
        "SELECT memory_with_users FROM creatures WHERE creature_id = ?",
        (creature_id,)
    )
    row = await cursor.fetchone()
    if not row:
        return
    memory = json.loads(row["memory_with_users"]) if isinstance(row["memory_with_users"], str) else row["memory_with_users"]
    uid_str = str(user_id)
    if uid_str not in memory:
        memory[uid_str] = []
    memory[uid_str].append({"action": action, "time": datetime.now().isoformat()})
    await db.execute(
        "UPDATE creatures SET memory_with_users = ? WHERE creature_id = ?",
        (json.dumps(memory), creature_id)
    )
    await db.commit()


async def get_creature_memory(creature_id: str, user_id: int) -> list:
    db = await get_db()
    cursor = await db.execute(
        "SELECT memory_with_users FROM creatures WHERE creature_id = ?",
        (creature_id,)
    )
    row = await cursor.fetchone()
    if not row:
        return []
    memory = json.loads(row["memory_with_users"]) if isinstance(row["memory_with_users"], str) else row["memory_with_users"]
    return memory.get(str(user_id), [])


# ──────────────────────────────────────────────
#  Секреты
# ──────────────────────────────────────────────

async def check_secret_trigger(user_id: int, trigger_type: str, trigger_data: dict) -> dict | None:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM secrets WHERE is_active = 1 AND discovered_by IS NULL"
    )
    rows = await cursor.fetchall()
    for row in rows:
        condition = json.loads(row["trigger_condition"]) if isinstance(row["trigger_condition"], str) else row["trigger_condition"]
        if condition.get("type") == trigger_type:
            if _check_condition(condition, trigger_data, user_id):
                await db.execute(
                    "UPDATE secrets SET discovered_by = ?, discovered_at = datetime('now') WHERE id = ?",
                    (user_id, row["id"])
                )
                await db.commit()
                reward = json.loads(row["reward"]) if isinstance(row["reward"], str) else row["reward"]
                await _log_action(user_id, "secret_found", {"secret_id": row["secret_id"], "name": row["name"]})
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
    db = await get_db()
    cursor = await db.execute("SELECT * FROM world_events WHERE is_active = 1")
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def trigger_world_event(event_id: str) -> dict | None:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM world_events WHERE event_id = ?", (event_id,))
    row = await cursor.fetchone()
    if not row:
        return None
    await db.execute("UPDATE world_events SET is_active = 1 WHERE event_id = ?", (event_id,))
    await db.commit()
    return dict(row)


# ──────────────────────────────────────────────
#  Энциклопедия / Легенды
# ──────────────────────────────────────────────

async def discover_legend(legend_id: str, category: str, name: str, description: str, user_id: int):
    db = await get_db()
    cursor = await db.execute("SELECT * FROM legends WHERE legend_id = ?", (legend_id,))
    existing = await cursor.fetchone()
    if existing:
        await db.execute(
            "UPDATE legends SET times_discovered = times_discovered + 1 WHERE legend_id = ?",
            (legend_id,)
        )
        await db.commit()
        return False
    else:
        await db.execute(
            "INSERT INTO legends (legend_id, category, name, description, discovered_by, discovered_at, times_discovered) VALUES (?, ?, ?, ?, ?, datetime('now'), 1)",
            (legend_id, category, name, description, user_id)
        )
        await db.commit()
        await _log_action(user_id, "legend_discover", {"legend_id": legend_id, "name": name})
        return True


async def get_legend_stats() -> dict:
    db = await get_db()
    cursor = await db.execute("SELECT COUNT(*) FROM legends WHERE category = 'creature'")
    creatures = (await cursor.fetchone())[0]
    cursor = await db.execute("SELECT COUNT(*) FROM legends WHERE category = 'item'")
    items = (await cursor.fetchone())[0]
    cursor = await db.execute("SELECT COUNT(*) FROM legends WHERE category = 'location'")
    places = (await cursor.fetchone())[0]
    cursor = await db.execute("SELECT COUNT(*) FROM legends WHERE category = 'lore'")
    lore = (await cursor.fetchone())[0]
    return {"creatures_found": creatures, "items_found": items, "places_found": places, "lore_found": lore}


# ──────────────────────────────────────────────
#  Бой
# ──────────────────────────────────────────────

async def get_creature(creature_id: str) -> dict:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM creatures WHERE creature_id = ?", (creature_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def start_combat(user_id: int, creature_id: str) -> dict:
    user = await get_or_create_user(user_id)
    creature = await get_creature(creature_id)

    if not creature:
        return {"success": False, "message": "Существо не найдено."}
    if not creature["is_alive"]:
        return {"success": False, "message": "Это существо уже мертво."}
    if creature["location"] != user["current_location"]:
        return {"success": False, "message": "Этого существа здесь нет."}
    if creature["disposition"] == "friendly":
        return {"success": False, "message": "Нельзя атаковать дружелюбных существ."}

    return {
        "success": True,
        "user": user,
        "creature": creature,
        "message": f"⚔️ Ты вступаешь в бой с *{creature['name']}*!"
    }


async def resolve_combat(user_id: int, creature_id: str, action: str = "attack") -> dict:
    user = await get_or_create_user(user_id)
    creature = await get_creature(creature_id)

    if not user or not creature:
        return {"success": False, "message": "Ошибка боя."}

    result_log = {
        "rounds": [],
        "user_hp": user["hp"],
        "creature_hp": creature["hp"],
        "xp_gained": 0,
        "loot": [],
        "outcome": None
    }

    user_hp = user["hp"]
    creature_hp = creature["hp"]
    round_num = 0

    while user_hp > 0 and creature_hp > 0 and round_num < 20:
        round_num += 1
        round_data = {"round": round_num}

        user_dmg = max(1, user["attack"] - creature["defense"] + random.randint(-3, 5))
        if action == "strong_attack":
            user_dmg = int(user_dmg * 1.5)
            action = "attack"
        elif action == "defend":
            user_dmg = 0
            user_hp = min(user["max_hp"], user_hp + 5)

        creature_hp -= user_dmg
        round_data["user_damage"] = user_dmg

        creature_dmg = max(1, creature["attack"] - user["defense"] + random.randint(-2, 4))
        user_hp -= creature_dmg
        round_data["creature_damage"] = creature_dmg

        result_log["rounds"].append(round_data)

    result_log["user_hp"] = max(0, user_hp)
    result_log["creature_hp"] = max(0, creature_hp)

    db = await get_db()

    if creature_hp <= 0 and user_hp > 0:
        result_log["outcome"] = "victory"
        result_log["xp_gained"] = creature["xp_reward"]

        loot_table = json.loads(creature["loot_table"]) if isinstance(creature["loot_table"], str) else creature["loot_table"]
        for loot_item in loot_table:
            if random.random() < loot_item.get("chance", 0.5):
                await add_item(user_id, loot_item["item_id"], loot_item.get("qty", 1))
                result_log["loot"].append(loot_item["item_id"])

        gold_reward = random.randint(2, creature["xp_reward"] // 5 + 3)
        new_xp = user["xp"] + creature["xp_reward"]
        new_level = user["level"]
        xp_needed = new_level * 100
        leveled = False
        while new_xp >= xp_needed:
            new_level += 1
            new_xp -= xp_needed
            xp_needed = new_level * 100
            leveled = True

        if leveled:
            await _apply_level_up(user_id, new_level)
        await update_user(user_id, xp=new_xp, level=new_level, hp=min(user["max_hp"], user_hp + 20), gold=user["gold"] + gold_reward)
        result_log["gold_gained"] = gold_reward

        await db.execute("UPDATE creatures SET is_alive = 0 WHERE creature_id = ?", (creature_id,))
        await db.commit()

        await creature_remember(creature_id, user_id, "killed_by")
        await _log_action(user_id, "combat_victory", {
            "creature": creature_id, "xp": creature["xp_reward"], "loot": result_log["loot"]
        })

        await discover_legend(f"creature_{creature_id}", "creature", creature["name"], creature["description"], user_id)

    elif user_hp <= 0:
        result_log["outcome"] = "defeat"
        await update_user(user_id, hp=0, is_alive=0)
        await creature_remember(creature_id, user_id, "killed_player")
        await _log_action(user_id, "combat_defeat", {"creature": creature_id})

    else:
        result_log["outcome"] = "draw"
        await update_user(user_id, hp=max(1, user_hp))

    await db.execute(
        """INSERT INTO combat_log (user_id, creature_id, result, damage_dealt, damage_taken, xp_gained, loot_dropped)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, creature_id, result_log["outcome"],
         sum(r.get("user_damage", 0) for r in result_log["rounds"]),
         sum(r.get("creature_damage", 0) for r in result_log["rounds"]),
         result_log["xp_gained"], json.dumps(result_log["loot"]))
    )
    await db.commit()

    return result_log


async def respawn_creature(creature_id: str):
    db = await get_db()
    await db.execute("UPDATE creatures SET is_alive = 1 WHERE creature_id = ?", (creature_id,))
    await db.commit()


async def get_combat_history(user_id: int, limit: int = 10) -> list:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM combat_log WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


# ──────────────────────────────────────────────
#  Квесты
# ──────────────────────────────────────────────

async def get_available_quests(user_id: int, location: str = None) -> list:
    db = await get_db()
    if location:
        cursor = await db.execute(
            """SELECT q.* FROM quests q
               WHERE q.is_active = 1 AND q.location = ?
               AND NOT EXISTS (
                   SELECT 1 FROM user_quests uq
                   WHERE uq.user_id = ? AND uq.quest_id = q.quest_id AND uq.status = 'active'
               )""",
            (location, user_id)
        )
    else:
        cursor = await db.execute(
            """SELECT q.* FROM quests q
               WHERE q.is_active = 1
               AND NOT EXISTS (
                   SELECT 1 FROM user_quests uq
                   WHERE uq.user_id = ? AND uq.quest_id = q.quest_id
                   AND (uq.status = 'active' OR (uq.status = 'completed' AND q.is_repeating = 0))
               )""",
            (user_id,)
        )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def accept_quest(user_id: int, quest_id: str) -> dict:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM quests WHERE quest_id = ? AND is_active = 1",
        (quest_id,)
    )
    quest = await cursor.fetchone()
    if not quest:
        return {"success": False, "message": "Квест не найден."}

    quest = dict(quest)

    user = await get_or_create_user(user_id)
    if quest["location"] != user["current_location"]:
        return {"success": False, "message": "Ты не в той локации для этого квеста."}

    cursor = await db.execute(
        "SELECT * FROM user_quests WHERE user_id = ? AND quest_id = ? AND status = 'active'",
        (user_id, quest_id)
    )
    if await cursor.fetchone():
        return {"success": False, "message": "Ты уже выполняешь этот квест."}

    cursor = await db.execute(
        "SELECT * FROM user_quests WHERE user_id = ? AND quest_id = ? AND status = 'completed'",
        (user_id, quest_id)
    )
    completed = await cursor.fetchone()
    if completed:
        if not quest["is_repeating"]:
            return {"success": False, "message": "Ты уже выполнил этот квест."}
        await db.execute(
            "DELETE FROM user_quests WHERE user_id = ? AND quest_id = ?",
            (user_id, quest_id)
        )
        await db.commit()

    objectives = json.loads(quest["objectives"]) if isinstance(quest["objectives"], str) else quest["objectives"]
    progress = {}
    for obj in objectives:
        progress[obj["id"]] = {"current": 0, "target": obj["target"]}

    await db.execute(
        "INSERT INTO user_quests (user_id, quest_id, progress) VALUES (?, ?, ?)",
        (user_id, quest_id, json.dumps(progress))
    )
    await db.commit()

    await _log_action(user_id, "quest_accept", {"quest_id": quest_id, "name": quest["name"]})

    return {"success": True, "quest": quest, "message": f"📜 Квест принят: <b>{quest['name']}</b>"}


async def update_quest_progress(user_id: int, quest_id: str, objective_id: str, amount: int = 1) -> dict:
    db = await get_db()
    cursor = await db.execute(
        """SELECT uq.*, q.objectives, q.rewards, q.name
           FROM user_quests uq
           JOIN quests q ON uq.quest_id = q.quest_id
           WHERE uq.user_id = ? AND uq.quest_id = ? AND uq.status = 'active'""",
        (user_id, quest_id)
    )
    uq = await cursor.fetchone()
    if not uq:
        return {"success": False}

    uq = dict(uq)
    progress = json.loads(uq["progress"])
    if objective_id not in progress:
        return {"success": False}

    progress[objective_id]["current"] = min(
        progress[objective_id]["current"] + amount,
        progress[objective_id]["target"]
    )

    all_done = all(p["current"] >= p["target"] for p in progress.values())

    if all_done:
        rewards = json.loads(uq["rewards"]) if isinstance(uq["rewards"], str) else uq["rewards"]

        if "xp" in rewards:
            user = await get_or_create_user(user_id)
            new_xp = user["xp"] + rewards["xp"]
            new_level = user["level"]
            xp_needed = new_level * 100
            leveled = False
            while new_xp >= xp_needed:
                new_level += 1
                new_xp -= xp_needed
                xp_needed = new_level * 100
                leveled = True
            if leveled:
                await _apply_level_up(user_id, new_level)
            await update_user(user_id, xp=new_xp, level=new_level)

        if "memories" in rewards:
            user = await get_or_create_user(user_id)
            await update_user(user_id, memories=user["memories"] + rewards["memories"])

        if "karma" in rewards:
            user = await get_or_create_user(user_id)
            await update_user(user_id, karma=user["karma"] + rewards["karma"])

        if "items" in rewards:
            for item in rewards["items"]:
                await add_item(user_id, item["id"], item.get("qty", 1))

        if "gold" in rewards:
            user = await get_or_create_user(user_id)
            await update_user(user_id, gold=user["gold"] + rewards["gold"])

        await db.execute(
            "UPDATE user_quests SET status = 'completed', progress = ?, completed_at = datetime('now') WHERE user_id = ? AND quest_id = ?",
            (json.dumps(progress), user_id, quest_id)
        )
        await db.commit()

        await _log_action(user_id, "quest_complete", {"quest_id": quest_id, "name": uq["name"]})
        await discover_legend(f"quest_{quest_id}", "lore", uq["name"], uq.get("description", ""), user_id)

        return {"success": True, "completed": True, "rewards": rewards, "message": f"🏆 Квест выполнен: <b>{uq['name']}</b>!"}
    else:
        await db.execute(
            "UPDATE user_quests SET progress = ? WHERE user_id = ? AND quest_id = ?",
            (json.dumps(progress), user_id, quest_id)
        )
        await db.commit()
        return {"success": True, "completed": False}


async def get_user_quests(user_id: int) -> list:
    db = await get_db()
    cursor = await db.execute(
        """SELECT uq.*, q.name, q.description, q.objectives, q.rewards
           FROM user_quests uq
           JOIN quests q ON uq.quest_id = q.quest_id
           WHERE uq.user_id = ?
           ORDER BY uq.started_at DESC""",
        (user_id,)
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def create_quest(quest_id: str, name: str, description: str, giver: str,
                       location: str, objectives: list, rewards: dict,
                       is_active: bool = True, is_repeating: bool = False):
    db = await get_db()
    active_int = 1 if is_active else 0
    repeat_int = 1 if is_repeating else 0
    await db.execute(
        """INSERT OR REPLACE INTO quests (quest_id, name, description, giver, location, objectives, rewards, is_active, is_repeating)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (quest_id, name, description, giver, location,
         json.dumps(objectives), json.dumps(rewards), active_int, repeat_int)
    )
    await db.commit()


# ──────────────────────────────────────────────
#  Предметы на земле
# ──────────────────────────────────────────────

async def get_ground_items(location_id: str) -> list:
    db = await get_db()
    cursor = await db.execute(
        """SELECT g.*, t.name, t.description, t.rarity
           FROM ground_items g
           LEFT JOIN item_templates t ON g.item_id = t.item_id
           WHERE g.location_id = ?""",
        (location_id,)
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def pick_up_item(user_id: int, location_id: str, item_id: str) -> dict:
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, quantity FROM ground_items WHERE location_id = ? AND item_id = ?",
        (location_id, item_id)
    )
    item = await cursor.fetchone()
    if not item:
        return {"success": False, "message": "Этого предмета здесь нет."}

    await add_item(user_id, item_id, item["quantity"])
    await db.execute("DELETE FROM ground_items WHERE id = ?", (item["id"],))
    await db.commit()
    await _log_action(user_id, "pickup", {"item_id": item_id, "qty": item["quantity"]})

    t = await get_item_template(item_id)
    name = t["name"] if t else item_id
    await discover_legend(f"item_{item_id}", "item", name, t["description"] if t else item_id, user_id)
    return {"success": True, "message": f"🤲 Подобрал: {name} x{item['quantity']}"}


async def get_item_template(item_id: str) -> dict:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM item_templates WHERE item_id = ?", (item_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


# ──────────────────────────────────────────────
#  Использование предметов
# ──────────────────────────────────────────────

async def use_item(user_id: int, item_id: str) -> dict:
    db = await get_db()
    t = await get_item_template(item_id)
    if not t:
        return {"success": False, "message": "Предмет не найден."}

    cursor = await db.execute(
        "SELECT id, quantity FROM inventory WHERE user_id = ? AND item_id = ?",
        (user_id, item_id)
    )
    inv_item = await cursor.fetchone()
    if not inv_item or inv_item["quantity"] < 1:
        return {"success": False, "message": "У тебя нет этого предмета."}

    if not t["is_usable"]:
        return {"success": False, "message": f"«{t['name']}» нельзя использовать."}

    effect = json.loads(t["use_effect"]) if isinstance(t["use_effect"], str) else t["use_effect"]
    user = await get_or_create_user(user_id)
    messages = []

    if "heal" in effect:
        heal = effect["heal"]
        old_hp = user["hp"]
        new_hp = min(user["max_hp"], old_hp + heal)
        actual_heal = new_hp - old_hp
        await update_user(user_id, hp=new_hp)
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
            await _apply_level_up(user_id, new_level)
        await update_user(user_id, xp=new_xp, level=new_level)
        messages.append(f"⭐ +{effect['xp']} XP")

    if "level_up" in effect:
        new_level = user["level"] + 1
        await _apply_level_up(user_id, new_level)
        fresh = await get_or_create_user(user_id)
        await update_user(user_id, hp=fresh["max_hp"])
        messages.append("⭐ Уровень Increased!")

    if "light" in effect:
        messages.append("💡 Жемчужина светится тёплым светом. Ты видишь то, что было скрыто.")

    if "reveal_secret" in effect:
        messages.append("🔮 Кристалл шепчет тебе тайну. Ты чувствуешь, как воспоминания проникают в сознание.")
        await _log_action(user_id, "crystal_reveal", {"item_id": item_id})

    if "vision" in effect:
        messages.append("👁 Глаз гаргульи открывается. Ты видишь сквозь стены на мгновение.")
        await _log_action(user_id, "vision", {"item_id": item_id})

    if "resurrect" in effect:
        messages.append("💀 Кольцо мёртвого короля пульсирует. Мёртвые шепчут тебе советы.")

    await remove_item(user_id, item_id, 1)
    await _log_action(user_id, "use_item", {"item_id": item_id, "effect": effect})

    return {"success": True, "message": f"🧪 Использовал «{t['name']}»\n" + "\n".join(messages)}


# ──────────────────────────────────────────────
#  Исцеление / Отдых
# ──────────────────────────────────────────────

async def rest_heal(user_id: int) -> dict:
    user = await get_or_create_user(user_id)
    if user["hp"] >= user["max_hp"]:
        return {"success": False, "message": "❤️ Твоё HP уже максимум."}

    heal = min(25, user["max_hp"] - user["hp"])
    await update_user(user_id, hp=user["hp"] + heal)
    await _log_action(user_id, "rest", {"healed": heal})

    return {"success": True, "message": f"💚 Ты отдохнул и восстановил {heal} HP\n❤️ HP: {user['hp'] + heal}/{user['max_hp']}"}


async def revive_user(user_id: int) -> dict:
    user = await get_or_create_user(user_id)
    if user["is_alive"]:
        return {"success": False, "message": "Ты уже живой."}

    new_hp = max(1, user["max_hp"] // 2)
    await update_user(user_id, is_alive=1, hp=new_hp)
    await _log_action(user_id, "revive", {"hp": new_hp})

    return {"success": True, "message": f"✨ Ты очнулся...\n❤️ HP: {new_hp}/{user['max_hp']}\n<i>Туман дарует тебе вторую жизнь.</i>"}


# ──────────────────────────────────────────────
#  Разговор с существами
# ──────────────────────────────────────────────

CREATURE_DIALOGUES = {
    "elder_fisherman": [
        "Глаза не поднимая: «Вода не прощает. Запомни это.»",
        "Плюёт на берег: «Вижу, ты ищешь ответы. Их тут нет.»",
        "Крутит удочку: «В реке есть то, что тебе нужно. Но ты не готов.»",
        "Шепчет: «Белый лес... я был там. Однажды. Больше — никогда.»",
    ],
    "wolf_alpha": [
        "Волк рычит. Он не доверяет тебе.",
        "Альфа-волк скалится. Ты чувствуешь запах крови.",
    ],
    "echo_wraith": [
        "Голос эха: «Ты — я. Я — ты. Мы оба — ничто.»",
        "Шёпот: «Забери мою память. Мне она не нужна.»",
    ],
    "the_keeper": [
        "Хранитель молчит. Но его молчание говорит больше слов.",
        "«Ты пришёл. Наконец-то. Я ждал. Давно.»",
    ],
}

async def talk_to_creature(user_id: int, creature_id: str) -> dict:
    creature = await get_creature(creature_id)
    if not creature:
        return {"success": False, "message": "Существо не найдено."}

    user = await get_or_create_user(user_id)
    if creature["location"] != user["current_location"]:
        return {"success": False, "message": "Этого существа здесь нет."}

    # Проверяем память существа
    memory = await get_creature_memory(creature_id, user_id)
    hostile_memories = [m for m in memory if m["action"] in ("killed_by", "attacked")]

    dialogues = CREATURE_DIALOGUES.get(creature_id, [])

    if creature["disposition"] == "friendly" or (creature["disposition"] == "neutral" and len(hostile_memories) == 0):
        if dialogues:
            import random
            text = f"🗣 <b>{creature['name']}:</b>\n\n<i>{random.choice(dialogues)}</i>"
        else:
            text = f"🗣 <b>{creature['name']}</b> молчит. Но его взгляд говорит: «Я знаю то, чего не знаешь ты.»"

        await _log_action(user_id, "talk", {"creature": creature_id})
        await discover_legend(f"creature_{creature_id}", "creature", creature["name"], creature["description"], user_id)
        return {"success": True, "message": text}
    elif len(hostile_memories) > 0:
        return {"success": False, "message": f"🗣 {creature['name']} рычит. Он помнит, что ты ему сделал.\n\n<i>Говорить бесполезно.</i>"}
    else:
        return {"success": False, "message": f"🗣 {creature['name']} не в настроении для разговора.\n\n<i>Лучше не дразнить.</i>"}


# ──────────────────────────────────────────────
#  Отношения с существами
# ──────────────────────────────────────────────

async def change_creature_relation(creature_id: str, user_id: int, delta: int, action: str):
    db = await get_db()
    cursor = await db.execute(
        "SELECT relation FROM creature_relations WHERE creature_id = ? AND user_id = ?",
        (creature_id, user_id)
    )
    row = await cursor.fetchone()
    if row:
        new_rel = row["relation"] + delta
        await db.execute(
            "UPDATE creature_relations SET relation = ?, last_action = ?, updated_at = datetime('now') WHERE creature_id = ? AND user_id = ?",
            (new_rel, action, creature_id, user_id)
        )
    else:
        await db.execute(
            "INSERT INTO creature_relations (creature_id, user_id, relation, last_action) VALUES (?, ?, ?, ?)",
            (creature_id, user_id, delta, action)
        )
    await db.commit()


async def get_creature_relation(creature_id: str, user_id: int) -> int:
    db = await get_db()
    cursor = await db.execute(
        "SELECT relation FROM creature_relations WHERE creature_id = ? AND user_id = ?",
        (creature_id, user_id)
    )
    row = await cursor.fetchone()
    return row["relation"] if row else 0


# ──────────────────────────────────────────────
#  Магазин
# ──────────────────────────────────────────────

async def get_shop_items(shop_id: str) -> list:
    db = await get_db()
    cursor = await db.execute(
        """SELECT s.*, t.name, t.description, t.rarity
           FROM shop_items s
           LEFT JOIN item_templates t ON s.item_id = t.item_id
           WHERE s.shop_id = ? AND s.stock != 0""",
        (shop_id,)
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def buy_item(user_id: int, shop_id: str, item_id: str) -> dict:
    db = await get_db()
    user = await get_or_create_user(user_id)

    cursor = await db.execute(
        "SELECT * FROM shop_items WHERE shop_id = ? AND item_id = ?",
        (shop_id, item_id)
    )
    shop_entry = await cursor.fetchone()
    if not shop_entry:
        return {"success": False, "message": "Этого товара нет в магазине."}

    shop_entry = dict(shop_entry)

    if shop_entry["stock"] == 0:
        return {"success": False, "message": "Этот товар закончился."}

    if user["level"] < shop_entry["required_level"]:
        return {"success": False, "message": f"Нужен уровень {shop_entry['required_level']}."}

    if user["karma"] < shop_entry["required_karma"]:
        return {"success": False, "message": "Твоя карма слишком низка для этой покупки."}

    if user["gold"] < shop_entry["price"]:
        return {"success": False, "message": f"Недостаточно золота. Нужно: {shop_entry['price']} 🪙, есть: {user['gold']} 🪙"}

    await update_user(user_id, gold=user["gold"] - shop_entry["price"])
    await add_item(user_id, item_id, 1)

    if shop_entry["stock"] > 0:
        await db.execute(
            "UPDATE shop_items SET stock = stock - 1 WHERE shop_id = ? AND item_id = ?",
            (shop_id, item_id)
        )
        await db.commit()

    t = await get_item_template(item_id)
    name = t["name"] if t else item_id

    await _log_action(user_id, "buy_item", {"item_id": item_id, "shop": shop_id, "price": shop_entry["price"]})

    return {"success": True, "message": f"🛒 Купил «{name}» за {shop_entry['price']} 🪙"}


async def sell_item(user_id: int, item_id: str) -> dict:
    db = await get_db()
    user = await get_or_create_user(user_id)

    t = await get_item_template(item_id)
    if not t:
        return {"success": False, "message": "Предмет не найден."}

    cursor = await db.execute(
        "SELECT id, quantity FROM inventory WHERE user_id = ? AND item_id = ?",
        (user_id, item_id)
    )
    inv_item = await cursor.fetchone()
    if not inv_item or inv_item["quantity"] < 1:
        return {"success": False, "message": "У тебя нет этого предмета."}

    rarity_prices = {"common": 3, "rare": 8, "epic": 20, "legendary": 50}
    price = rarity_prices.get(t["rarity"], 3)

    await remove_item(user_id, item_id, 1)
    await update_user(user_id, gold=user["gold"] + price)
    await _log_action(user_id, "sell_item", {"item_id": item_id, "price": price})

    return {"success": True, "message": f"💰 Продал «{t['name']}» за {price} 🪙"}


async def get_user_gold(user_id: int) -> int:
    user = await get_or_create_user(user_id)
    return user["gold"]


async def seed_shop():
    db = await get_db()
    shop_items_data = [
        # ═══ РЫБАЦКАЯ ДЕРЕВНЯ — базовые зелья ═══
        ("fishing_village", "healing_herb", 5, -1, 1, 0),
        ("fishing_village", "swamp_root", 8, -1, 1, 0),
        ("fishing_village", "wolf_fang", 10, -1, 1, 0),
        # ═══ ТОРГОВАЯ ПЛОЩАДЬ — оружие и броня ═══
        ("market_square", "obsidian_shard", 15, -1, 2, 0),
        ("market_square", "serpent_scale", 12, -1, 2, 0),
        ("market_square", "frost_shard", 18, -1, 3, 0),
        ("market_square", "shadow_essence", 25, 5, 3, 0),
        # ═══ ТЕНЕВОЙ РЫНОК — редкое ═══
        ("shadow_market", "echo_crystal", 40, 3, 5, 5),
        ("shadow_market", "gargoyle_eye", 60, 2, 7, 10),
        ("shadow_market", "mirror_fragment", 55, 2, 6, 8),
        ("shadow_market", "frozen_tear", 35, -1, 4, 3),
        ("shadow_market", "soul_bottle", 100, 1, 10, 15),
        # ═══ ХРАМ ТЕНЕЙ — тёмные предметы ═══
        ("temple_of_shadows", "dark_shard", 20, -1, 3, -5),
        ("temple_of_shadows", "bloodstone", 30, 5, 5, -3),
        ("temple_of_shadows", "arcane_dust", 8, -1, 1, 0),
        # ═══ ШАХТА — кристаллы ═══
        ("abandoned_mine", "raw_crystal", 10, -1, 2, 0),
        ("abandoned_mine", "crystal_thread", 22, 3, 4, 0),
        ("abandoned_mine", "spider_venom", 18, 4, 3, 0),
        # ═══ РЫБАЦКАЯ ДЕРЕВНЯ — обновление ═══
        ("fishing_village", "light_leaf", 12, -1, 2, 0),
    ]

    for shop_id, item_id, price, stock, req_level, req_karma in shop_items_data:
        await db.execute(
            """INSERT OR REPLACE INTO shop_items (shop_id, item_id, price, stock, required_level, required_karma)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (shop_id, item_id, price, stock, req_level, req_karma)
        )
    await db.commit()


# ──────────────────────────────────────────────
#  PvP Арена
# ──────────────────────────────────────────────

async def get_pvp_opponents(user_id: int) -> list:
    db = await get_db()
    user = await get_or_create_user(user_id)
    cursor = await db.execute(
        """SELECT user_id, username, display_name, level, hp, max_hp, attack, defense, pvp_rating
           FROM users WHERE user_id != ? AND is_alive = 1
           ORDER BY ABS(pvp_rating - ?) LIMIT 10""",
        (user_id, user["pvp_rating"])
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def pvp_battle(user_id: int, target_id: int) -> dict:
    user = await get_or_create_user(user_id)
    target = await get_or_create_user(target_id)

    if not user["is_alive"]:
        return {"success": False, "message": "Ты мёртв. Очнись сначала."}
    if not target["is_alive"]:
        return {"success": False, "message": "Противник мёртв."}

    result = {
        "rounds": [],
        "user_hp": user["hp"],
        "target_hp": target["hp"],
        "outcome": None,
        "xp_gained": 0,
        "gold_gained": 0,
    }

    user_hp = user["hp"]
    target_hp = target["hp"]
    round_num = 0

    while user_hp > 0 and target_hp > 0 and round_num < 15:
        round_num += 1
        rd = {"round": round_num}

        user_dmg = max(1, user["attack"] - target["defense"] + random.randint(-2, 4))
        target_hp -= user_dmg
        rd["user_damage"] = user_dmg

        target_dmg = max(1, target["attack"] - user["defense"] + random.randint(-2, 4))
        user_hp -= target_dmg
        rd["target_damage"] = target_dmg

        result["rounds"].append(rd)

    result["user_hp"] = max(0, user_hp)
    result["target_hp"] = max(0, target_hp)

    db = await get_db()

    old_user_rating = user["pvp_rating"]
    old_target_rating = target["pvp_rating"]

    k = 32

    if target_hp <= 0 and user_hp > 0:
        result["outcome"] = "victory"
        result["xp_gained"] = 15 + target["level"] * 3
        result["gold_gained"] = 5 + target["level"] * 2

        rating_change = max(10, (old_target_rating - old_user_rating) // 5 + 15)
        new_user_rating = old_user_rating + rating_change
        new_target_rating = max(100, old_target_rating - rating_change)

        new_xp = user["xp"] + result["xp_gained"]
        new_level = user["level"]
        leveled = False
        while new_xp >= new_level * 100:
            new_level += 1
            new_xp -= (new_level - 1) * 100
            leveled = True
        if leveled:
            await _apply_level_up(user_id, new_level)

        await update_user(user_id,
            xp=new_xp, level=new_level,
            hp=min(user["max_hp"], user_hp + 30),
            gold=user["gold"] + result["gold_gained"],
            pvp_wins=user["pvp_wins"] + 1,
            pvp_rating=new_user_rating
        )
        await update_user(target_id,
            hp=max(1, target_hp),
            pvp_losses=target["pvp_losses"] + 1,
            pvp_rating=new_target_rating
        )

        await _log_action(user_id, "pvp_win", {
            "target": target_id, "xp": result["xp_gained"],
            "gold": result["gold_gained"], "rating_change": rating_change
        })
        await discover_legend(f"pvp_{target_id}", "lore", f"PvP: {target['display_name']}", f"Победил {target['display_name']} в арене", user_id)

    elif user_hp <= 0:
        result["outcome"] = "defeat"

        rating_change = max(10, (old_user_rating - old_target_rating) // 5 + 15)
        new_user_rating = max(100, old_user_rating - rating_change)
        new_target_rating = old_target_rating + rating_change

        await update_user(user_id, hp=0, is_alive=0, pvp_losses=user["pvp_losses"] + 1, pvp_rating=new_user_rating)
        await update_user(target_id, pvp_wins=target["pvp_wins"] + 1, pvp_rating=new_target_rating)

        await _log_action(user_id, "pvp_loss", {"target": target_id, "rating_change": rating_change})

    else:
        result["outcome"] = "draw"
        await update_user(user_id, hp=max(1, user_hp))
        await update_user(target_id, hp=max(1, target_hp))

    await db.execute(
        """INSERT INTO combat_log (user_id, creature_id, result, damage_dealt, damage_taken, xp_gained, loot_dropped)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, f"pvp_{target_id}", result["outcome"],
         sum(r.get("user_damage", 0) for r in result["rounds"]),
         sum(r.get("target_damage", 0) for r in result["rounds"]),
         result["xp_gained"], json.dumps([]))
    )
    await db.commit()

    return result


async def get_pvp_leaderboard(limit: int = 10) -> list:
    db = await get_db()
    cursor = await db.execute(
        """SELECT user_id, username, display_name, level, pvp_rating, pvp_wins, pvp_losses
           FROM users WHERE pvp_wins > 0 OR pvp_losses > 0
           ORDER BY pvp_rating DESC LIMIT ?""",
        (limit,)
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_pvp_stats(user_id: int) -> dict:
    user = await get_or_create_user(user_id)
    db = await get_db()
    cursor = await db.execute(
        "SELECT COUNT(*) FROM combat_log WHERE user_id = ? AND creature_id LIKE 'pvp_%' AND result = 'victory'",
        (user_id,)
    )
    total_pvp_wins = (await cursor.fetchone())[0]
    cursor = await db.execute(
        "SELECT COUNT(*) FROM combat_log WHERE user_id = ? AND creature_id LIKE 'pvp_%'",
        (user_id,)
    )
    total_pvp_fights = (await cursor.fetchone())[0]

    return {
        "rating": user["pvp_rating"],
        "wins": user["pvp_wins"],
        "losses": user["pvp_losses"],
        "total_fights": total_pvp_fights,
        "winrate": round(user["pvp_wins"] / max(1, user["pvp_wins"] + user["pvp_losses"]) * 100, 1),
    }


# ──────────────────────────────────────────────
#  Крафт
# ──────────────────────────────────────────────

async def get_crafting_recipes(location: str = None) -> list:
    db = await get_db()
    if location:
        cursor = await db.execute(
            "SELECT * FROM crafting_recipes WHERE is_active = 1 AND (required_location = ? OR required_location IS NULL)",
            (location,)
        )
    else:
        cursor = await db.execute("SELECT * FROM crafting_recipes WHERE is_active = 1")
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_crafting_recipe(recipe_id: str) -> dict:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM crafting_recipes WHERE recipe_id = ?", (recipe_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def craft_item(user_id: int, recipe_id: str) -> dict:
    recipe = await get_crafting_recipe(recipe_id)
    if not recipe:
        return {"success": False, "message": "Рецепт не найден."}

    user = await get_or_create_user(user_id)
    if user["level"] < recipe["required_level"]:
        return {"success": False, "message": f"Нужен уровень {recipe['required_level']}."}

    if recipe["required_location"] and user["current_location"] != recipe["required_location"]:
        loc = await get_location(recipe["required_location"])
        loc_name = loc["name"] if loc else recipe["required_location"]
        return {"success": False, "message": f"Крафтить можно только в «{loc_name}»."}

    ingredients = json.loads(recipe["ingredients"]) if isinstance(recipe["ingredients"], str) else recipe["ingredients"]
    for ing in ingredients:
        has = await has_item(user_id, ing["item_id"], ing.get("qty", 1))
        if not has:
            t = await get_item_template(ing["item_id"])
            name = t["name"] if t else ing["item_id"]
            return {"success": False, "message": f"Не хватает: {name} x{ing.get('qty', 1)}"}

    for ing in ingredients:
        await remove_item(user_id, ing["item_id"], ing.get("qty", 1))

    await add_item(user_id, recipe["result_item"], recipe["result_qty"])

    new_xp = user["xp"] + recipe["xp_reward"]
    new_level = user["level"]
    leveled = False
    while new_xp >= new_level * 100:
        new_level += 1
        new_xp -= (new_level - 1) * 100
        leveled = True
    if leveled:
        await _apply_level_up(user_id, new_level)
    await update_user(user_id, xp=new_xp, level=new_level)

    db = await get_db()
    cursor = await db.execute(
        "SELECT times_crafted FROM user_crafting WHERE user_id = ? AND recipe_id = ?",
        (user_id, recipe_id)
    )
    existing = await cursor.fetchone()
    if existing:
        await db.execute(
            "UPDATE user_crafting SET times_crafted = times_crafted + 1 WHERE user_id = ? AND recipe_id = ?",
            (user_id, recipe_id)
        )
    else:
        await db.execute(
            "INSERT INTO user_crafting (user_id, recipe_id) VALUES (?, ?)",
            (user_id, recipe_id)
        )
    await db.commit()

    t = await get_item_template(recipe["result_item"])
    result_name = t["name"] if t else recipe["result_item"]
    await _log_action(user_id, "craft", {"recipe_id": recipe_id, "item": recipe["result_item"]})

    return {
        "success": True,
        "message": f"⚒️ Скрафтил «{result_name}» x{recipe['result_qty']}\n⭐ +{recipe['xp_reward']} XP"
    }


async def has_item(user_id: int, item_id: str, qty: int = 1) -> bool:
    db = await get_db()
    cursor = await db.execute(
        "SELECT quantity FROM inventory WHERE user_id = ? AND item_id = ?",
        (user_id, item_id)
    )
    row = await cursor.fetchone()
    return row and row["quantity"] >= qty


# ──────────────────────────────────────────────
#  Гильдии
# ──────────────────────────────────────────────

async def create_guild(user_id: int, name: str, description: str = "", motto: str = "") -> dict:
    db = await get_db()
    user = await get_or_create_user(user_id)
    if user["gold"] < 50:
        return {"success": False, "message": "Нужно 50 золота для создания гильдии."}

    cursor = await db.execute("SELECT user_id FROM guild_members WHERE user_id = ?", (user_id,))
    if await cursor.fetchone():
        return {"success": False, "message": "Ты уже в гильдии. Покинь её сначала."}

    guild_id = f"g_{user_id}_{int(datetime.now().timestamp())}"
    await db.execute(
        "INSERT INTO guilds (guild_id, name, description, leader_id, motto) VALUES (?, ?, ?, ?, ?)",
        (guild_id, name, description, user_id, motto)
    )
    await db.execute(
        "INSERT INTO guild_members (guild_id, user_id, role) VALUES (?, ?, 'leader')",
        (guild_id, user_id)
    )
    await update_user(user_id, gold=user["gold"] - 50)
    await db.commit()
    await _log_action(user_id, "guild_create", {"guild_id": guild_id, "name": name})

    return {"success": True, "message": f"🏰 Гильдия «{name}» создана!", "guild_id": guild_id}


async def join_guild(user_id: int, guild_id: str) -> dict:
    db = await get_db()
    user = await get_or_create_user(user_id)

    cursor = await db.execute("SELECT user_id FROM guild_members WHERE user_id = ?", (user_id,))
    if await cursor.fetchone():
        return {"success": False, "message": "Ты уже в гильдии."}

    cursor = await db.execute("SELECT * FROM guilds WHERE guild_id = ?", (guild_id,))
    guild = await cursor.fetchone()
    if not guild:
        return {"success": False, "message": "Гильдия не найдена."}

    await db.execute(
        "INSERT INTO guild_members (guild_id, user_id) VALUES (?, ?)",
        (guild_id, user_id)
    )
    await db.commit()
    await _log_action(user_id, "guild_join", {"guild_id": guild_id})

    return {"success": True, "message": f"🏰 Ты вступил в «{guild['name']}»!"}


async def leave_guild(user_id: int) -> dict:
    db = await get_db()
    cursor = await db.execute(
        "SELECT gm.guild_id, gm.role, g.name FROM guild_members gm JOIN guilds g ON gm.guild_id = g.guild_id WHERE gm.user_id = ?",
        (user_id,)
    )
    member = await cursor.fetchone()
    if not member:
        return {"success": False, "message": "Ты не в гильдии."}

    if member["role"] == "leader":
        cursor2 = await db.execute(
            "SELECT user_id FROM guild_members WHERE guild_id = ? AND user_id != ? LIMIT 1",
            (member["guild_id"], user_id)
        )
        successor = await cursor2.fetchone()
        if successor:
            await db.execute(
                "UPDATE guild_members SET role = 'leader' WHERE guild_id = ? AND user_id = ?",
                (member["guild_id"], successor["user_id"])
            )
        else:
            await db.execute("DELETE FROM guilds WHERE guild_id = ?", (member["guild_id"],))

    await db.execute("DELETE FROM guild_members WHERE guild_id = ? AND user_id = ?", (member["guild_id"], user_id))
    await db.commit()
    await _log_action(user_id, "guild_leave", {"guild_id": member["guild_id"]})

    return {"success": True, "message": f"Ты покинул «{member['name']}»."}


async def get_user_guild(user_id: int) -> dict | None:
    db = await get_db()
    cursor = await db.execute(
        """SELECT g.*, gm.role, gm.contribution
           FROM guild_members gm
           JOIN guilds g ON gm.guild_id = g.guild_id
           WHERE gm.user_id = ?""",
        (user_id,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_guild_members(guild_id: str) -> list:
    db = await get_db()
    cursor = await db.execute(
        """SELECT gm.*, u.display_name, u.level, u.pvp_rating
           FROM guild_members gm
           LEFT JOIN users u ON gm.user_id = u.user_id
           WHERE gm.guild_id = ?
           ORDER BY gm.role DESC, gm.contribution DESC""",
        (guild_id,)
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_all_guilds(limit: int = 10) -> list:
    db = await get_db()
    cursor = await db.execute(
        """SELECT g.*, 
           (SELECT COUNT(*) FROM guild_members WHERE guild_id = g.guild_id) as member_count
           FROM guilds g
           ORDER BY g.level DESC, g.xp DESC
           LIMIT ?""",
        (limit,)
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def guild_donate(user_id: int, amount: int) -> dict:
    db = await get_db()
    user = await get_or_create_user(user_id)
    guild = await get_user_guild(user_id)
    if not guild:
        return {"success": False, "message": "Ты не в гильдии."}
    if user["gold"] < amount:
        return {"success": False, "message": f"У тебя только {user['gold']} золота."}
    if amount <= 0:
        return {"success": False, "message": "Сумма должна быть больше 0."}

    await update_user(user_id, gold=user["gold"] - amount)
    await db.execute(
        "UPDATE guilds SET gold = gold + ? WHERE guild_id = ?",
        (amount, guild["guild_id"])
    )
    await db.execute(
        "UPDATE guild_members SET contribution = contribution + ? WHERE guild_id = ? AND user_id = ?",
        (amount, guild["guild_id"], user_id)
    )
    guild_xp = amount // 2
    await db.execute(
        "UPDATE guilds SET xp = xp + ? WHERE guild_id = ?",
        (guild_xp, guild["guild_id"])
    )
    await db.commit()
    await _log_action(user_id, "guild_donate", {"amount": amount, "guild_id": guild["guild_id"]})

    return {"success": True, "message": f"💰 Пожертвовал {amount} 🪙 в казну «{guild['name']}»"}


async def get_nearby_players(user_id: int) -> list:
    db = await get_db()
    user = await get_or_create_user(user_id)
    cursor = await db.execute(
        "SELECT user_id, display_name, level, hp, max_hp FROM users WHERE current_location = ? AND user_id != ? AND is_alive = 1",
        (user["current_location"], user_id)
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


# ──────────────────────────────────────────────
#  Трейдинг
# ──────────────────────────────────────────────

async def create_trade(from_user: int, to_user: int, items_offered: list, gold_offered: int,
                       items_wanted: list, gold_wanted: int) -> dict:
    if from_user == to_user:
        return {"success": False, "message": "Нельзя торговать с самим собой."}

    db = await get_db()
    user1 = await get_or_create_user(from_user)
    user2 = await get_or_create_user(to_user)

    if user1["current_location"] != user2["current_location"]:
        return {"success": False, "message": "Вы должны быть в одной локации."}

    if user1["gold"] < gold_offered:
        return {"success": False, "message": "У тебя недостаточно золота."}

    for item in items_offered:
        has = await has_item(from_user, item["item_id"], item.get("qty", 1))
        if not has:
            return {"success": False, "message": f"У тебя нет {item['item_id']}."}

    cursor = await db.execute(
        """SELECT * FROM player_trades
           WHERE from_user = ? AND status = 'pending'""",
        (from_user,)
    )
    if await cursor.fetchone():
        return {"success": False, "message": "У тебя уже есть активный трейд."}

    await db.execute(
        """INSERT INTO player_trades (from_user, to_user, items_offered, gold_offered, items_wanted, gold_wanted)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (from_user, to_user, json.dumps(items_offered), gold_offered,
         json.dumps(items_wanted), gold_wanted)
    )
    await db.commit()
    await _log_action(from_user, "trade_create", {"to_user": to_user, "gold_offered": gold_offered})

    return {"success": True, "message": "📨 Предложение трейда отправлено!"}


async def accept_trade(trade_id: int, user_id: int) -> dict:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM player_trades WHERE id = ? AND status = 'pending'", (trade_id,))
    trade = await cursor.fetchone()
    if not trade:
        return {"success": False, "message": "Трейд не найден или уже закрыт."}

    trade = dict(trade)
    if trade["to_user"] != user_id:
        return {"success": False, "message": "Этот трейд не для тебя."}

    user1 = await get_or_create_user(trade["from_user"])
    user2 = await get_or_create_user(trade["to_user"])

    if user1["current_location"] != user2["current_location"]:
        return {"success": False, "message": "Вы разошлись по локациям."}

    if user1["gold"] < trade["gold_offered"]:
        return {"success": False, "message": "У отправителя недостаточно золота."}

    items_offered = json.loads(trade["items_offered"]) if isinstance(trade["items_offered"], str) else trade["items_offered"]
    for item in items_offered:
        has = await has_item(trade["from_user"], item["item_id"], item.get("qty", 1))
        if not has:
            return {"success": False, "message": f"У отправителя нет {item['item_id']}."}

    if user2["gold"] < trade["gold_wanted"]:
        return {"success": False, "message": "У тебя недостаточно золота."}

    items_wanted = json.loads(trade["items_wanted"]) if isinstance(trade["items_wanted"], str) else trade["items_wanted"]
    for item in items_wanted:
        has = await has_item(trade["to_user"], item["item_id"], item.get("qty", 1))
        if not has:
            return {"success": False, "message": f"У тебя нет {item['item_id']}."}

    if trade["gold_offered"] > 0:
        await update_user(trade["from_user"], gold=user1["gold"] - trade["gold_offered"])
        user2_fresh = await get_or_create_user(trade["to_user"])
        await update_user(trade["to_user"], gold=user2_fresh["gold"] + trade["gold_offered"])

    if trade["gold_wanted"] > 0:
        user2_fresh2 = await get_or_create_user(trade["to_user"])
        await update_user(trade["to_user"], gold=user2_fresh2["gold"] - trade["gold_wanted"])
        user1_fresh = await get_or_create_user(trade["from_user"])
        await update_user(trade["from_user"], gold=user1_fresh["gold"] + trade["gold_wanted"])

    for item in items_offered:
        await remove_item(trade["from_user"], item["item_id"], item.get("qty", 1))
        await add_item(trade["to_user"], item["item_id"], item.get("qty", 1))

    for item in items_wanted:
        await remove_item(trade["to_user"], item["item_id"], item.get("qty", 1))
        await add_item(trade["from_user"], item["item_id"], item.get("qty", 1))

    await db.execute(
        "UPDATE player_trades SET status = 'completed', completed_at = datetime('now') WHERE id = ?",
        (trade_id,)
    )
    await db.commit()
    await _log_action(user_id, "trade_accept", {"trade_id": trade_id})

    return {"success": True, "message": "🤝 Трейд завершён!"}


async def decline_trade(trade_id: int, user_id: int) -> dict:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM player_trades WHERE id = ? AND status = 'pending'", (trade_id,))
    trade = await cursor.fetchone()
    if not trade:
        return {"success": False, "message": "Трейд не найден."}
    trade = dict(trade)
    if trade["to_user"] != user_id and trade["from_user"] != user_id:
        return {"success": False, "message": "Не твой трейд."}

    await db.execute("UPDATE player_trades SET status = 'declined' WHERE id = ?", (trade_id,))
    await db.commit()
    return {"success": True, "message": "❌ Трейд отклонён."}


async def get_pending_trades(user_id: int) -> list:
    db = await get_db()
    cursor = await db.execute(
        """SELECT pt.*, u.display_name as from_name
           FROM player_trades pt
           JOIN users u ON pt.from_user = u.user_id
           WHERE pt.to_user = ? AND pt.status = 'pending'
           ORDER BY pt.created_at DESC""",
        (user_id,)
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]
