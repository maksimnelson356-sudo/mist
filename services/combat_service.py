import json
import random
from datetime import datetime, timezone

from sqlalchemy import select, update, delete

from database.base import get_db
from database.models.user import UserModel
from database.models.creature import CreatureModel
from database.models.inventory import InventoryModel, UserEquipmentModel, UserStatusEffectModel
from database.models.item import ItemTemplateModel
from database.models.combat import CombatLogModel
from database.models.location import LocationModel
from domain.events import EventType, Importance


STATUS_EFFECTS = {
    "poison": {"name": "Яд", "icon": "🟢", "damage_per_round": 3},
    "bleed": {"name": "Кровотечение", "icon": "🩸", "damage_per_round": 4},
    "burn": {"name": "Ожог", "icon": "🔥", "damage_per_round": 5},
    "stun": {"name": "Оглушение", "icon": "💫", "skip_chance": 1.0},
    "frost": {"name": "Мороз", "icon": "❄️", "attack_reduction": 3},
    "weakness": {"name": "Слабость", "icon": "💀", "defense_reduction": 3},
    "regen": {"name": "Регенерация", "icon": "💚", "heal_per_round": 5},
    "shield": {"name": "Щит", "icon": "🛡️", "damage_absorb": 5},
    "haste": {"name": "Скорость", "icon": "⚡", "attack_bonus": 4},
}


class CombatService:

    def __init__(self, chronicle, user_service):
        self.chronicle = chronicle
        self.user_service = user_service

    async def start(self, user_id: int, creature_id: str) -> dict:
        user = await self.user_service.get(user_id)
        if not user:
            return {"success": False, "message": "Пользователь не найден."}

        creature = await self._get_creature(creature_id)
        if not creature:
            return {"success": False, "message": "Существо не найдено."}

        if not creature["is_alive"]:
            return {"success": False, "message": "Это существо уже мертво."}

        if creature["location"] != user["current_location"]:
            return {"success": False, "message": "Этого существа здесь нет."}

        if creature["disposition"] == "friendly":
            return {"success": False, "message": "Нельзя атаковать дружелюбных существ."}

        equip_bonus = await self._get_equipment_bonuses(user_id)
        effective_attack = user["attack"] + equip_bonus["attack"]
        effective_defense = user["defense"] + equip_bonus["defense"]

        equip_info = ""
        if equip_bonus["attack"] > 0 or equip_bonus["defense"] > 0:
            parts = []
            if equip_bonus["attack"] > 0:
                parts.append(f"⚔️+{equip_bonus['attack']}")
            if equip_bonus["defense"] > 0:
                parts.append(f"🛡️+{equip_bonus['defense']}")
            equip_info = f"\n📦 Снаряжение: {', '.join(parts)}"

        return {
            "success": True,
            "user": user,
            "creature": creature,
            "effective_attack": effective_attack,
            "effective_defense": effective_defense,
            "equipment": equip_bonus,
            "message": f"⚔️ Ты вступаешь в бой с *{creature['name']}*!{equip_info}\n⚔️ Атака: {effective_attack} | 🛡️ Защита: {effective_defense}",
        }

    async def resolve(self, user_id: int, creature_id: str, action: str = "attack") -> dict:
        user = await self.user_service.get(user_id)
        creature = await self._get_creature(creature_id)

        if not user or not creature:
            return {"success": False, "message": "Ошибка боя."}

        equip_bonus = await self._get_equipment_bonuses(user_id)
        effective_attack = user["attack"] + equip_bonus["attack"]
        effective_defense = user["defense"] + equip_bonus["defense"]

        creature_spawn = creature.get("spawn_data", {})
        is_boss = creature_spawn.get("is_boss", False)
        boss_abilities = creature_spawn.get("abilities", [])

        result_log = {
            "rounds": [],
            "user_hp": user["hp"],
            "creature_hp": creature["hp"],
            "xp_gained": 0,
            "loot": [],
            "outcome": None,
            "equipment": equip_bonus,
            "effects_applied": [],
        }

        user_hp = user["hp"]
        creature_hp = creature["hp"]
        round_num = 0

        async for db in get_db():
            while user_hp > 0 and creature_hp > 0 and round_num < 20:
                round_num += 1
                round_data = {"round": round_num}

                effect_result = await self._tick_effects(user_id, db)
                user_hp -= effect_result["damage"]
                user_hp += effect_result["heal"]
                user_hp = min(user["max_hp"], user_hp)
                effective_attack += effect_result["attack_mod"]
                effective_defense += effect_result["defense_mod"]
                effective_attack = max(1, effective_attack)
                effective_defense = max(0, effective_defense)
                round_data["effect_damage"] = effect_result["damage"]
                round_data["effect_heal"] = effect_result["heal"]
                round_data["effect_log"] = effect_result["log"]

                if effect_result["skip_turn"]:
                    round_data["user_damage"] = 0
                    round_data["user_skipped"] = True
                else:
                    user_dmg = max(1, effective_attack - creature["defense"] + random.randint(-3, 5))
                    current_action = action
                    if current_action == "strong_attack":
                        user_dmg = int(user_dmg * 1.5)
                        action = "attack"
                    elif current_action == "defend":
                        user_dmg = 0
                        user_hp = min(user["max_hp"], user_hp + 5)

                    creature_hp -= user_dmg
                    round_data["user_damage"] = user_dmg

                creature_dmg = max(1, creature["attack"] - effective_defense + random.randint(-2, 4))
                creature_dmg = max(0, creature_dmg - effect_result.get("absorbed", 0))
                user_hp -= creature_dmg
                round_data["creature_damage"] = creature_dmg

                if is_boss and boss_abilities and random.random() < 0.3:
                    effect_pool = [a for a in boss_abilities if a in STATUS_EFFECTS]
                    if effect_pool:
                        chosen = random.choice(effect_pool)
                        await self._apply_status_effect(user_id, chosen, potency=1, duration=2, source="creature", db=db)
                        result_log["effects_applied"].append(chosen)
                        effect_info = STATUS_EFFECTS.get(chosen, {})
                        round_data["boss_effect"] = f"{effect_info.get('icon', '?')} {effect_info.get('name', chosen)}"

                result_log["rounds"].append(round_data)

            result_log["user_hp"] = max(0, user_hp)
            result_log["creature_hp"] = max(0, creature_hp)

            if creature_hp <= 0 and user_hp > 0:
                result_log["outcome"] = "victory"
                result_log["xp_gained"] = creature["xp_reward"]

                loot_table = creature.get("loot_table", [])
                for loot_item in loot_table:
                    if random.random() < loot_item.get("chance", 0.5):
                        await self._add_item(user_id, loot_item["item_id"], loot_item.get("qty", 1), db)
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
                    await self._apply_level_up(user_id, new_level, db)
                result_log["leveled"] = leveled
                result_log["new_level"] = new_level if leveled else user["level"]
                await db.execute(
                    update(UserModel).where(UserModel.user_id == user_id).values(
                        xp=new_xp, level=new_level,
                        hp=min(user["max_hp"], user_hp + 20),
                        gold=user["gold"] + gold_reward,
                    )
                )
                result_log["gold_gained"] = gold_reward

                await db.execute(
                    update(CreatureModel).where(CreatureModel.creature_id == creature_id).values(is_alive=False)
                )
                await db.commit()

                await self._creature_remember(creature_id, user_id, "killed_by", db)
                await self.chronicle.publish(
                    EventType.COMBAT_VICTORY,
                    f"Победа над {creature['name']}",
                    player_id=user_id,
                    region_id=creature["location"],
                    importance=Importance.NOTABLE,
                    metadata={"creature": creature_id, "xp": creature["xp_reward"], "loot": result_log["loot"]},
                )
                await self._clear_all_effects(user_id, db)

            elif user_hp <= 0:
                result_log["outcome"] = "defeat"
                await db.execute(
                    update(UserModel).where(UserModel.user_id == user_id).values(hp=0, is_alive=False)
                )
                await db.commit()
                await self._creature_remember(creature_id, user_id, "killed_player", db)
                await self.chronicle.publish(
                    EventType.COMBAT_DEFEAT,
                    f"Поражение от {creature['name']}",
                    player_id=user_id,
                    region_id=creature["location"],
                    importance=Importance.NOTABLE,
                    metadata={"creature": creature_id},
                )
                await self._clear_all_effects(user_id, db)

            else:
                result_log["outcome"] = "draw"
                await db.execute(
                    update(UserModel).where(UserModel.user_id == user_id).values(hp=max(1, user_hp))
                )
                await db.commit()
                await self.chronicle.publish(
                    EventType.COMBAT_DRAW,
                    f"Ничья с {creature['name']}",
                    player_id=user_id,
                    region_id=creature["location"],
                    importance=Importance.COMMON,
                )
                await self._clear_all_effects(user_id, db)

            db.add(CombatLogModel(
                user_id=user_id,
                creature_id=creature_id,
                result=result_log["outcome"],
                damage_dealt=sum(r.get("user_damage", 0) for r in result_log["rounds"]),
                damage_taken=sum(r.get("creature_damage", 0) for r in result_log["rounds"]),
                xp_gained=result_log["xp_gained"],
                loot_dropped=json.dumps(result_log["loot"]),
            ))
            await db.commit()
            break

        return result_log

    async def _get_creature(self, creature_id: str) -> dict | None:
        async for db in get_db():
            stmt = select(CreatureModel).where(CreatureModel.creature_id == creature_id)
            result = await db.execute(stmt)
            row = result.scalar_one_or_none()
            if not row:
                return None
            return {
                "id": row.id,
                "creature_id": row.creature_id,
                "name": row.name,
                "description": row.description,
                "location": row.location,
                "disposition": row.disposition,
                "is_alive": row.is_alive,
                "hp": row.hp,
                "max_hp": row.max_hp,
                "attack": row.attack,
                "defense": row.defense,
                "xp_reward": row.xp_reward,
                "spawn_data": json.loads(row.spawn_data) if isinstance(row.spawn_data, str) else row.spawn_data,
                "loot_table": json.loads(row.loot_table) if isinstance(row.loot_table, str) else row.loot_table,
            }
        return None

    async def _get_equipment_bonuses(self, user_id: int) -> dict:
        bonuses = {"attack": 0, "defense": 0, "max_hp": 0}
        async for db in get_db():
            stmt = select(UserEquipmentModel).where(UserEquipmentModel.user_id == user_id)
            result = await db.execute(stmt)
            rows = result.scalars().all()
            for row in rows:
                from services.equipment_service import EquipmentService
                stats = EquipmentService.EQUIPMENT_STATS.get(row.item_id, {})
                bonuses["attack"] += stats.get("attack", 0)
                bonuses["defense"] += stats.get("defense", 0)
                bonuses["max_hp"] += stats.get("max_hp", 0)
            break
        return bonuses

    async def _tick_effects(self, user_id: int, db) -> dict:
        stmt = select(UserStatusEffectModel).where(
            UserStatusEffectModel.user_id == user_id,
            UserStatusEffectModel.duration > 0,
        )
        result = await db.execute(stmt)
        effects = result.scalars().all()

        total_damage = 0
        total_heal = 0
        skip_turn = False
        attack_mod = 0
        defense_mod = 0
        absorbed = 0
        tick_log = []

        for e in effects:
            info = STATUS_EFFECTS.get(e.effect_type, {})
            if "damage_per_round" in info:
                dmg = info["damage_per_round"] * e.potency
                total_damage += dmg
                tick_log.append(f"{info['icon']} {info['name']}: -{dmg} HP")
            if "heal_per_round" in info:
                heal = info["heal_per_round"] * e.potency
                total_heal += heal
                tick_log.append(f"{info['icon']} {info['name']}: +{heal} HP")
            if info.get("skip_chance", 0) > 0 and random.random() < info["skip_chance"]:
                skip_turn = True
                tick_log.append(f"{info['icon']} {info['name']}: пропуск хода!")
            if "attack_reduction" in info:
                attack_mod -= info["attack_reduction"] * e.potency
            if "attack_bonus" in info:
                attack_mod += info["attack_bonus"] * e.potency
            if "defense_reduction" in info:
                defense_mod -= info["defense_reduction"] * e.potency
            if "damage_absorb" in info:
                absorbed += info["damage_absorb"] * e.potency

            new_dur = e.duration - 1
            if new_dur <= 0:
                await db.delete(e)
                tick_log.append(f"💨 {info['name']} закончился")
            else:
                e.duration = new_dur

        return {
            "damage": total_damage,
            "heal": total_heal,
            "skip_turn": skip_turn,
            "attack_mod": attack_mod,
            "defense_mod": defense_mod,
            "absorbed": absorbed,
            "log": tick_log,
        }

    async def _apply_status_effect(self, user_id: int, effect_type: str, potency: int = 1,
                                   duration: int = 3, source: str = "combat", db=None):
        if db is None:
            async for session in get_db():
                db = session
                break

        stmt = select(UserStatusEffectModel).where(
            UserStatusEffectModel.user_id == user_id,
            UserStatusEffectModel.effect_type == effect_type,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.potency = potency
            existing.duration = duration
        else:
            db.add(UserStatusEffectModel(
                user_id=user_id,
                effect_type=effect_type,
                potency=potency,
                duration=duration,
                source=source,
            ))
        await db.commit()

    async def _clear_all_effects(self, user_id: int, db):
        await db.execute(
            delete(UserStatusEffectModel).where(UserStatusEffectModel.user_id == user_id)
        )
        await db.commit()

    async def _add_item(self, user_id: int, item_id: str, qty: int, db):
        stmt = select(InventoryModel).where(
            InventoryModel.user_id == user_id,
            InventoryModel.item_id == item_id,
            InventoryModel.is_magic == False,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            existing.quantity += qty
        else:
            db.add(InventoryModel(user_id=user_id, item_id=item_id, quantity=qty))
        await db.commit()

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
        await self.chronicle.publish(
            EventType.PLAYER_LEVEL_UP,
            f"Уровень повышен → {new_level}",
            player_id=user_id,
            importance=Importance.RARE,
            metadata={"new_level": new_level},
        )

    async def _creature_remember(self, creature_id: str, user_id: int, action: str, db):
        stmt = select(CreatureModel).where(CreatureModel.creature_id == creature_id)
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return
        memory = json.loads(row.memory_with_users) if isinstance(row.memory_with_users, str) else row.memory_with_users
        uid_str = str(user_id)
        if uid_str not in memory:
            memory[uid_str] = []
        memory[uid_str].append({"action": action, "time": datetime.now(timezone.utc).isoformat()})
        row.memory_with_users = json.dumps(memory)
        await db.commit()
