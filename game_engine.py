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


# ──────────────────────────────────────────────
#  Бой
# ──────────────────────────────────────────────

async def get_creature(creature_id: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM creatures WHERE creature_id = $1", creature_id
        )
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

        # Атака игрока
        user_dmg = max(1, user["attack"] - creature["defense"] + random.randint(-3, 5))
        if action == "strong_attack":
            user_dmg = int(user_dmg * 1.5)
            action = "attack"
        elif action == "defend":
            user_dmg = 0
            result_log["user_hp"] = min(user["max_hp"], user_hp + 5)
            user_hp = result_log["user_hp"]

        creature_hp -= user_dmg
        round_data["user_damage"] = user_dmg

        # Атака существа
        creature_dmg = max(1, creature["attack"] - user["defense"] + random.randint(-2, 4))
        user_hp -= creature_dmg
        round_data["creature_damage"] = creature_dmg

        result_log["rounds"].append(round_data)

    result_log["user_hp"] = max(0, user_hp)
    result_log["creature_hp"] = max(0, creature_hp)

    # Определяем исход
    if creature_hp <= 0 and user_hp > 0:
        result_log["outcome"] = "victory"
        result_log["xp_gained"] = creature["xp_reward"]

        # Лут
        loot_table = json.loads(creature["loot_table"]) if isinstance(creature["loot_table"], str) else creature["loot_table"]
        for loot_item in loot_table:
            if random.random() < loot_item.get("chance", 0.5):
                await add_item(user_id, loot_item["item_id"], loot_item.get("qty", 1))
                result_log["loot"].append(loot_item["item_id"])

        # Обновляем XP и HP игрока
        new_xp = user["xp"] + creature["xp_reward"]
        new_level = user["level"]
        xp_needed = new_level * 100
        if new_xp >= xp_needed:
            new_level += 1
            new_xp -= xp_needed

        await update_user(user_id,
            xp=new_xp,
            level=new_level,
            hp=min(user["max_hp"], user_hp + 20)
        )

        # Убиваем существо
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE creatures SET is_alive = FALSE WHERE creature_id = $1",
                creature_id
            )

        await creature_remember(creature_id, user_id, "killed_by")
        await _log_action(user_id, "combat_victory", {
            "creature": creature_id,
            "xp": creature["xp_reward"],
            "loot": result_log["loot"]
        })

        # Энциклопедия
        await discover_legend(
            f"creature_{creature_id}", "creature",
            creature["name"], creature["description"],
            user_id
        )

    elif user_hp <= 0:
        result_log["outcome"] = "defeat"
        await update_user(user_id, hp=0, is_alive=False)
        await creature_remember(creature_id, user_id, "killed_player")
        await _log_action(user_id, "combat_defeat", {"creature": creature_id})

    else:
        result_log["outcome"] = "draw"
        await update_user(user_id, hp=max(1, user_hp))

    # Лог боя
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO combat_log (user_id, creature_id, result, damage_dealt, damage_taken, xp_gained, loot_dropped)
               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            user_id, creature_id, result_log["outcome"],
            sum(r.get("user_damage", 0) for r in result_log["rounds"]),
            sum(r.get("creature_damage", 0) for r in result_log["rounds"]),
            result_log["xp_gained"],
            json.dumps(result_log["loot"])
        )

    return result_log


def format_combat_result(result: dict, creature_name: str) -> str:
    if not result["success"]:
        return result["message"]

    text = f"⚔️ *Бой с {creature_name}*\n\n"

    for round_data in result.get("rounds", [])[:5]:
        ud = round_data.get("user_damage", 0)
        cd = round_data.get("creature_damage", 0)
        text += f"Раунд {round_data['round']}: Ты нанёс {ud} урона, получил {cd}\n"

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
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE creatures SET is_alive = TRUE WHERE creature_id = $1",
            creature_id
        )


async def get_combat_history(user_id: int, limit: int = 10) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT * FROM combat_log WHERE user_id = $1
               ORDER BY created_at DESC LIMIT $2""",
            user_id, limit
        )
        return [dict(r) for r in rows]


# ──────────────────────────────────────────────
#  Квесты
# ──────────────────────────────────────────────

async def get_available_quests(user_id: int, location: str = None) -> list:
    pool = await get_pool()
    user = await get_or_create_user(user_id)
    async with pool.acquire() as conn:
        if location:
            rows = await conn.fetch(
                """SELECT q.* FROM quests q
                   WHERE q.is_active = TRUE AND q.location = $1
                   AND NOT EXISTS (
                       SELECT 1 FROM user_quests uq
                       WHERE uq.user_id = $2 AND uq.quest_id = q.quest_id AND uq.status = 'active'
                   )""",
                location, user_id
            )
        else:
            rows = await conn.fetch(
                """SELECT q.* FROM quests q
                   WHERE q.is_active = TRUE
                   AND NOT EXISTS (
                       SELECT 1 FROM user_quests uq
                       WHERE uq.user_id = $1 AND uq.quest_id = q.quest_id AND uq.status = 'active'
                   )""",
                user_id
            )
        return [dict(r) for r in rows]


async def accept_quest(user_id: int, quest_id: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        quest = await conn.fetchrow(
            "SELECT * FROM quests WHERE quest_id = $1 AND is_active = TRUE",
            quest_id
        )
        if not quest:
            return {"success": False, "message": "Квест не найден."}

        existing = await conn.fetchrow(
            """SELECT * FROM user_quests
               WHERE user_id = $1 AND quest_id = $2 AND status = 'active'""",
            user_id, quest_id
        )
        if existing:
            return {"success": False, "message": "Ты уже выполняешь этот квест."}

        completed = await conn.fetchrow(
            """SELECT * FROM user_quests
               WHERE user_id = $1 AND quest_id = $2 AND status = 'completed'""",
            user_id, quest_id
        )
        if completed and not quest["is_repeating"]:
            return {"success": False, "message": "Ты уже выполнил этот квест."}

        objectives = json.loads(quest["objectives"]) if isinstance(quest["objectives"], str) else quest["objectives"]
        progress = {}
        for obj in objectives:
            progress[obj["id"]] = {"current": 0, "target": obj["target"]}

        await conn.execute(
            """INSERT INTO user_quests (user_id, quest_id, progress)
               VALUES ($1, $2, $3)""",
            user_id, quest_id, json.dumps(progress)
        )

        await _log_action(user_id, "quest_accept", {"quest_id": quest_id, "name": quest["name"]})

        return {
            "success": True,
            "quest": dict(quest),
            "message": f"📜 Квест принят: *{quest['name']}*"
        }


async def update_quest_progress(user_id: int, quest_id: str, objective_id: str, amount: int = 1) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        uq = await conn.fetchrow(
            """SELECT uq.*, q.objectives, q.rewards, q.name
               FROM user_quests uq
               JOIN quests q ON uq.quest_id = q.quest_id
               WHERE uq.user_id = $1 AND uq.quest_id = $2 AND uq.status = 'active'""",
            user_id, quest_id
        )
        if not uq:
            return {"success": False}

        progress = json.loads(uq["progress"])
        if objective_id not in progress:
            return {"success": False}

        progress[objective_id]["current"] = min(
            progress[objective_id]["current"] + amount,
            progress[objective_id]["target"]
        )

        all_done = all(
            p["current"] >= p["target"]
            for p in progress.values()
        )

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

            await conn.execute(
                """UPDATE user_quests SET status = 'completed', progress = $1, completed_at = NOW()
                   WHERE user_id = $2 AND quest_id = $3""",
                json.dumps(progress), user_id, quest_id
            )

            await _log_action(user_id, "quest_complete", {"quest_id": quest_id, "name": uq["name"]})

            return {
                "success": True,
                "completed": True,
                "rewards": rewards,
                "message": f"🏆 Квест выполнен: *{uq['name']}*!"
            }
        else:
            await conn.execute(
                "UPDATE user_quests SET progress = $1 WHERE user_id = $2 AND quest_id = $3",
                json.dumps(progress), user_id, quest_id
            )
            return {"success": True, "completed": False}


async def get_user_quests(user_id: int) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT uq.*, q.name, q.description, q.objectives, q.rewards
               FROM user_quests uq
               JOIN quests q ON uq.quest_id = q.quest_id
               WHERE uq.user_id = $1
               ORDER BY uq.started_at DESC""",
            user_id
        )
        return [dict(r) for r in rows]


async def create_quest(quest_id: str, name: str, description: str, giver: str,
                       location: str, objectives: list, rewards: dict,
                       is_active: bool = True, is_repeating: bool = False):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO quests (quest_id, name, description, giver, location, objectives, rewards, is_active, is_repeating)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
               ON CONFLICT (quest_id) DO UPDATE SET
                   name = $2, description = $3, objectives = $6, rewards = $7""",
            quest_id, name, description, giver, location,
            json.dumps(objectives), json.dumps(rewards),
            is_active, is_repeating
        )
