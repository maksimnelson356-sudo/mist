import json
import random
from datetime import datetime
from database.db import get_db


# ──────────────────────────────────────────────
#  Пользователи
# ──────────────────────────────────────────────

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

        new_xp = user["xp"] + creature["xp_reward"]
        new_level = user["level"]
        xp_needed = new_level * 100
        if new_xp >= xp_needed:
            new_level += 1
            new_xp -= xp_needed

        await update_user(user_id, xp=new_xp, level=new_level, hp=min(user["max_hp"], user_hp + 20))

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


def format_combat_result(result: dict, creature_name: str) -> str:
    if not result["success"]:
        return result["message"]

    text = f"⚔️ *Бой с {creature_name}*\n\n"

    for round_data in result.get("rounds", [])[:5]:
        ud = round_data.get("user_damage", 0)
        cd = round_data.get("creature_damage", 0)
        text += f"Раунд {round_data['round']}: Ты нанёс {ud}, получил {cd}\n"

    text += f"\n❤️ Твоё HP: {result['user_hp']}\n"

    if result["outcome"] == "victory":
        text += f"\n🏆 *ПОБЕДА!*\n+{result['xp_gained']} XP"
        if result["loot"]:
            text += f"\n📦 Лут: {', '.join(result['loot'])}"
    elif result["outcome"] == "defeat":
        text += "\n💀 *ПОРАЖЕНИЕ*\nТы очнулся... где-то раньше."
    else:
        text += "\n🤝 *НИЧЬЯ*\nОба отступили."

    return text


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
                   WHERE uq.user_id = ? AND uq.quest_id = q.quest_id AND uq.status = 'active'
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
    if completed and not quest["is_repeating"]:
        return {"success": False, "message": "Ты уже выполнил этот квест."}

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

    return {"success": True, "quest": quest, "message": f"📜 Квест принят: *{quest['name']}*"}


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
            if new_xp >= new_level * 100:
                new_level += 1
                new_xp -= new_level * 100
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

        await db.execute(
            "UPDATE user_quests SET status = 'completed', progress = ?, completed_at = datetime('now') WHERE user_id = ? AND quest_id = ?",
            (json.dumps(progress), user_id, quest_id)
        )
        await db.commit()

        await _log_action(user_id, "quest_complete", {"quest_id": quest_id, "name": uq["name"]})

        return {"success": True, "completed": True, "rewards": rewards, "message": f"🏆 Квест выполнен: *{uq['name']}*!"}
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
        new_hp = min(user["max_hp"], user["hp"] + heal)
        await update_user(user_id, hp=new_hp)
        messages.append(f"💚 Восстановлено {new_hp - user['hp']} HP")

    if "damage" in effect:
        messages.append(f"⚔️ Нанесено {effect['damage']} урона (пока не работает в бою)")

    if "xp" in effect:
        new_xp = user["xp"] + effect["xp"]
        new_level = user["level"]
        if new_xp >= new_level * 100:
            new_level += 1
            new_xp -= new_level * 100
        await update_user(user_id, xp=new_xp, level=new_level)
        messages.append(f"⭐ +{effect['xp']} XP")

    if "level_up" in effect:
        await update_user(user_id, level=user["level"] + 1, max_hp=user["max_hp"] + 20, hp=user["max_hp"] + 20)
        messages.append("⭐ Уровень Increased!")

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
