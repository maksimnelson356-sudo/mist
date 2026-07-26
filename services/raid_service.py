import logging
import random
from datetime import datetime

from sqlalchemy import select, update

from database.base import get_db
from database.models.world_boss import WorldBossModel
from domain.events import EventType, Importance
from services.world_boss_service import WORLD_BOSS_DEFS

logger = logging.getLogger("MIST.raid")

RAID_CONFIG = {
    "min_players": 2,
    "max_players": 5,
    "boss_hp_mult": 1.5,
    "reward_mult": 1.3,
}


class RaidService:

    def __init__(self, chronicle, player):
        self.chronicle = chronicle
        self.player = player

    async def create_raid(self, boss_id: str, leader_id: int) -> dict:
        boss_def = next((bd for bd in WORLD_BOSS_DEFS if bd["boss_id"] == boss_id), None)
        if not boss_def:
            return {"success": False, "message": "Босс не найден."}

        async for db in get_db():
            existing = await db.execute(
                select(WorldBossModel).where(
                    WorldBossModel.boss_id == boss_id,
                    WorldBossModel.is_alive == True,
                )
            )
            if existing.scalar_one_or_none():
                return {"success": False, "message": "Босс уже активен. Присоединяйся!"}

            scaled_hp = int(boss_def["hp"] * RAID_CONFIG["boss_hp_mult"])

            boss = WorldBossModel(
                boss_id=boss_id,
                name=boss_def["name"],
                description=boss_def["description"],
                location_id=boss_def["location_id"],
                region_id=boss_def.get("region_id"),
                hp=scaled_hp,
                max_hp=scaled_hp,
                attack=boss_def["attack"],
                defense=boss_def["defense"],
                xp_reward=int(boss_def["xp_reward"] * RAID_CONFIG["reward_mult"]),
                gold_reward=int(boss_def["gold_reward"] * RAID_CONFIG["reward_mult"]),
                abilities=boss_def.get("abilities", []),
                loot_table=boss_def.get("loot_table", []),
                event_trigger=boss_def.get("event_trigger"),
                participants=[leader_id],
            )
            db.add(boss)
            await db.commit()

            await self.chronicle.publish(
                EventType.WORLD_EVENT,
                f"🐉 РЕЙД: {boss_def['name']} появился! Нужна группа!",
                importance=Importance.RARE,
            )

            return {
                "success": True,
                "message": f"🐉 Рейд на {boss_def['name']} создан! Нужно {RAID_CONFIG['min_players']}-{RAID_CONFIG['max_players']} игроков.",
                "boss_id": boss_id,
            }

    async def join_raid(self, boss_id: str, user_id: int) -> dict:
        async for db in get_db():
            result = await db.execute(
                select(WorldBossModel).where(
                    WorldBossModel.boss_id == boss_id,
                    WorldBossModel.is_alive == True,
                )
            )
            boss = result.scalar_one_or_none()
            if not boss:
                return {"success": False, "message": "Рейд не найден или уже завершён."}

            participants = boss.participants or []
            if len(participants) >= RAID_CONFIG["max_players"]:
                return {"success": False, "message": "Рейд полон."}

            if user_id in participants:
                return {"success": False, "message": "Ты уже в рейде."}

            participants.append(user_id)
            await db.execute(
                update(WorldBossModel)
                .where(WorldBossModel.id == boss.id)
                .values(participants=participants)
            )
            await db.commit()

            return {
                "success": True,
                "message": f"Ты присоединился к рейду! ({len(participants)}/{RAID_CONFIG['max_players']})",
                "participants": len(participants),
            }

    async def raid_attack(self, boss_id: str, user_id: int) -> dict:
        user = await self.player.get(user_id)
        if not user or not user["is_alive"]:
            return {"success": False, "message": "Ты не можешь сражаться."}

        async for db in get_db():
            result = await db.execute(
                select(WorldBossModel).where(
                    WorldBossModel.boss_id == boss_id,
                    WorldBossModel.is_alive == True,
                )
            )
            boss = result.scalar_one_or_none()
            if not boss:
                return {"success": False, "message": "Босс не найден."}

            participants = boss.participants or []
            if user_id not in participants:
                return {"success": False, "message": "Ты не в этом рейде."}

            damage = max(1, user["attack"] - boss.defense // 2 + random.randint(-5, 10))
            new_hp = max(0, boss.hp - damage)

            phase = "enraged" if new_hp < boss.max_hp * 0.3 else "wounded" if new_hp < boss.max_hp * 0.6 else "fighting"

            await db.execute(
                update(WorldBossModel)
                .where(WorldBossModel.id == boss.id)
                .values(hp=new_hp, phase=phase)
            )
            await db.commit()

            if new_hp <= 0:
                xp_reward = boss.xp_reward // len(participants)
                gold_reward = boss.gold_reward // len(participants)

                from database.models.user import UserModel
                for pid in participants:
                    await db.execute(
                        update(UserModel)
                        .where(UserModel.user_id == pid)
                        .values(
                            xp=UserModel.xp + xp_reward,
                            gold=UserModel.gold + gold_reward,
                        )
                    )

                await db.execute(
                    update(WorldBossModel)
                    .where(WorldBossModel.id == boss.id)
                    .values(is_alive=False, killed_at=datetime.utcnow(), killed_by=user_id, phase="dead")
                )
                await db.commit()

                await self.chronicle.publish(
                    EventType.WORLD_EVENT,
                    f"🏆 Рейд победил {boss.name}! Награды: {xp_reward} XP, {gold_reward} Gold каждому!",
                    importance=Importance.RARE,
                )

                return {
                    "success": True,
                    "killed": True,
                    "damage": damage,
                    "xp_reward": xp_reward,
                    "gold_reward": gold_reward,
                }

            return {
                "success": True,
                "killed": False,
                "damage": damage,
                "hp_left": new_hp,
                "phase": phase,
            }

    async def get_active_raids(self) -> list:
        async for db in get_db():
            result = await db.execute(
                select(WorldBossModel).where(WorldBossModel.is_alive == True)
            )
            raids = []
            for b in result.scalars().all():
                participants = b.participants or []
                if len(participants) >= RAID_CONFIG["min_players"]:
                    raids.append({
                        "boss_id": b.boss_id,
                        "name": b.name,
                        "hp": b.hp,
                        "max_hp": b.max_hp,
                        "participants": len(participants),
                        "phase": b.phase,
                    })
            return raids
