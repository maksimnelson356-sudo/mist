import asyncio
import logging
import random
from datetime import datetime, timedelta
from sqlalchemy import select, update, text

from database.base import get_db
from database.models.world_boss import WorldBossModel
from domain.events import EventType, Importance

logger = logging.getLogger("MIST.world_boss")

WORLD_BOSS_DEFS = [
    {
        "boss_id": "elder_dragon", "name": "Древний дракон",
        "description": "Дракон, пробуждённый метеоритом. Он жрёт деревья и золото.",
        "location_id": "dragon_peak", "region_id": "mountains",
        "hp": 2000, "attack": 60, "defense": 40,
        "xp_reward": 800, "gold_reward": 500,
        "abilities": ["fire_breath", "wing_buffet", "tail_swipe"],
        "loot_table": [
            {"item": "dragon_scale", "qty": 3, "chance": 0.8},
            {"item": "dragon_fang", "qty": 1, "chance": 0.5},
            {"item": "legendary_blade", "qty": 1, "chance": 0.1},
        ],
        "event_trigger": "meteorite",
    },
    {
        "boss_id": "ancient_lich", "name": "Древний лич",
        "description": "Король мёртвых, который отказался умирать. Его армия растёт.",
        "location_id": "forgotten_graveyard", "region_id": "dark_forest",
        "hp": 1500, "attack": 50, "defense": 35,
        "xp_reward": 600, "gold_reward": 300,
        "abilities": ["summon_skeletons", "drain_life", "fear"],
        "loot_table": [
            {"item": "phylactery", "qty": 1, "chance": 0.3},
            {"item": "soul_gem", "qty": 2, "chance": 0.6},
            {"item": "necronomicon", "qty": 1, "chance": 0.1},
        ],
        "event_trigger": "undead_awakening",
    },
    {
        "boss_id": "kraken", "name": "Кракен",
        "description": "Морское чудовище. Его щупальца тянутся к берегу.",
        "location_id": "dark_harbour", "region_id": "coast",
        "hp": 1800, "attack": 55, "defense": 30,
        "xp_reward": 700, "gold_reward": 400,
        "abilities": ["tentacle_slam", "ink_cloud", "drown"],
        "loot_table": [
            {"item": "kraken_eye", "qty": 1, "chance": 0.4},
            {"item": "tentacle_piece", "qty": 5, "chance": 0.7},
            {"item": "trident_of_depths", "qty": 1, "chance": 0.1},
        ],
        "event_trigger": "flood",
    },
    {
        "boss_id": "shadow_king", "name": "Теневой король",
        "description": "Он правит Теневым рынком. Его тень — повсюду.",
        "location_id": "shadow_market", "region_id": "civilization",
        "hp": 1200, "attack": 45, "defense": 25,
        "xp_reward": 500, "gold_reward": 600,
        "abilities": ["shadow_step", "dark_trade", "mind_control"],
        "loot_table": [
            {"item": "shadow_crown", "qty": 1, "chance": 0.2},
            {"item": "dark_gold", "qty": 100, "chance": 0.8},
            {"item": "shadow_cloak", "qty": 1, "chance": 0.15},
        ],
        "event_trigger": "clan_war",
    },
]


class WorldBossService:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def spawn_boss(self, boss_id: str) -> dict:
        boss_def = None
        for bd in WORLD_BOSS_DEFS:
            if bd["boss_id"] == boss_id:
                boss_def = bd
                break

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
                return {"success": False, "message": "Босс уже активен."}

            boss = WorldBossModel(
                boss_id=boss_id,
                name=boss_def["name"],
                description=boss_def["description"],
                location_id=boss_def["location_id"],
                region_id=boss_def.get("region_id"),
                hp=boss_def["hp"],
                max_hp=boss_def["hp"],
                attack=boss_def["attack"],
                defense=boss_def["defense"],
                xp_reward=boss_def["xp_reward"],
                gold_reward=boss_def["gold_reward"],
                abilities=boss_def.get("abilities", []),
                loot_table=boss_def.get("loot_table", []),
                event_trigger=boss_def.get("event_trigger"),
            )
            db.add(boss)
            await db.commit()

            await self.chronicle.publish(
                EventType.WORLD_EVENT,
                f"🐉 МИРОВОЙ БОСС: {boss_def['name']} появился в {boss_def['location_id']}!",
                importance=Importance.RARE,
            )

            return {"success": True, "message": f"🐉 {boss_def['name']} пробудился!"}

    async def damage_boss(self, boss_id: str, damage: int, player_id: int) -> dict:
        async for db in get_db():
            result = await db.execute(
                select(WorldBossModel).where(
                    WorldBossModel.boss_id == boss_id,
                    WorldBossModel.is_alive == True,
                )
            )
            boss = result.scalar_one_or_none()
            if not boss:
                return {"success": False, "message": "Босс не найден или мёртв."}

            new_hp = max(0, boss.hp - damage)
            participants = boss.participants or []
            if player_id not in participants:
                participants.append(player_id)

            await db.execute(
                update(WorldBossModel)
                .where(WorldBossModel.id == boss.id)
                .values(hp=new_hp, participants=participants)
            )

            if new_hp <= 0:
                await self._kill_boss(boss, player_id, db)
                return {"success": True, "killed": True, "damage": damage}

            phase = "enraged" if new_hp < boss.max_hp * 0.3 else "wounded" if new_hp < boss.max_hp * 0.6 else "fighting"
            await db.execute(
                update(WorldBossModel)
                .where(WorldBossModel.id == boss.id)
                .values(phase=phase)
            )

            await db.commit()
            return {"success": True, "killed": False, "damage": damage, "hp_left": new_hp, "phase": phase}

    async def _kill_boss(self, boss, killer_id: int, db):
        await db.execute(
            update(WorldBossModel)
            .where(WorldBossModel.id == boss.id)
            .values(is_alive=False, killed_at=datetime.utcnow(), killed_by=killer_id, phase="dead")
        )

        await self.chronicle.publish(
            EventType.WORLD_EVENT,
            f"🏆 {boss.name} повержен! Награды: {boss.xp_reward} XP, {boss.gold_reward} Gold",
            importance=Importance.RARE,
        )

        for loot in (boss.loot_table or []):
            if random.random() < loot.get("chance", 0.5):
                await self.chronicle.publish(
                    EventType.WORLD_EVENT,
                    f"💎 Выпадает: {loot['item']} x{loot['qty']}",
                    importance=Importance.COMMON,
                )

    async def check_respawns(self, game_hour: int):
        async for db in get_db():
            result = await db.execute(
                select(WorldBossModel).where(WorldBossModel.is_alive == False)
            )
            dead_bosses = result.scalars().all()

            for boss in dead_bosses:
                if boss.killed_at:
                    hours_since_death = (datetime.utcnow() - boss.killed_at).total_seconds() / 3600
                    if hours_since_death >= boss.respawn_hours:
                        await db.execute(
                            update(WorldBossModel)
                            .where(WorldBossModel.id == boss.id)
                            .values(
                                is_alive=True,
                                hp=boss.max_hp,
                                killed_at=None,
                                killed_by=None,
                                participants=[],
                                phase="idle",
                            )
                        )
                        await self.chronicle.publish(
                            EventType.WORLD_EVENT,
                            f"🐉 {boss.name} воскрес! Он вернулся в {boss.location_id}!",
                            importance=Importance.RARE,
                        )

            await db.commit()

    async def get_active_bosses(self) -> list:
        async for db in get_db():
            result = await db.execute(
                select(WorldBossModel).where(WorldBossModel.is_alive == True)
            )
            return [{
                "boss_id": b.boss_id,
                "name": b.name,
                "location": b.location_id,
                "hp": b.hp,
                "max_hp": b.max_hp,
                "phase": b.phase,
                "participants": len(b.participants or []),
            } for b in result.scalars().all()]

    async def get_boss_history(self) -> list:
        async for db in get_db():
            result = await db.execute(
                select(WorldBossModel)
                .where(WorldBossModel.is_alive == False)
                .order_by(WorldBossModel.killed_at.desc())
                .limit(10)
            )
            return [{
                "name": b.name,
                "killed_by": b.killed_by,
                "killed_at": b.killed_at,
                "participants": len(b.participants or []),
            } for b in result.scalars().all()]

    async def get_boss_stats(self) -> dict:
        async for db in get_db():
            total = (await db.execute(text("SELECT COUNT(*) FROM world_bosses"))).scalar() or 0
            alive = (await db.execute(text("SELECT COUNT(*) FROM world_bosses WHERE is_alive = 1"))).scalar() or 0
            dead = total - alive
            return {"total": total, "alive": alive, "dead": dead}

    async def start_loop(self, interval: int = 3600):
        self._running = True
        while self._running:
            await self.check_respawns(datetime.now().hour)
            await asyncio.sleep(interval)

    def stop(self):
        self._running = False
