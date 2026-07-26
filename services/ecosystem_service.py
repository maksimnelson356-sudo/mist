import logging
from sqlalchemy import select, update, text

from database.base import get_db
from database.models.npc import NPCModel
from database.models.creature import CreatureModel

logger = logging.getLogger("MIST.ecosystem")

ECOSYSTEM_FOOD_CHAIN = {
    "herbivore": {"eats": "plants", "eaten_by": ["carnivore", "omnivore"]},
    "carnivore": {"eats": "herbivore", "eaten_by": ["apex"]},
    "omnivore": {"eats": ["plants", "herbivore"], "eaten_by": ["apex", "carnivore"]},
    "apex": {"eats": ["herbivore", "carnivore", "omnivore"], "eaten_by": []},
    "plant": {"eats": None, "eaten_by": ["herbivore", "omnivore"]},
}

CREATURE_ROLES = {
    "wolf_alpha": "apex", "wolf_pack": "carnivore",
    "shadow_stalker": "carnivore", "river_serpent": "carnivore",
    "echo_wraith": "apex", "gargoyle": "apex",
    "blood_tree": "plant", "frost_spirit": "carnivore",
    "mirror_copy": "apex", "the_keeper": "apex",
    "dead_king": "apex", "void_walker": "apex",
    "swamp_witch": "apex", "bogey": "carnivore",
    "grave_sentinel": "apex", "crystal_golem": "apex",
    "harbour_ghost": "carnivore", "ash_wraith": "carnivore",
    "skeleton_mage": "carnivore", "kraken_tentacle": "apex",
    "mine_crawler": "carnivore", "crystal_spider": "carnivore",
    "grove_sprite": "plant", "ancient_warden": "apex",
    "camp_stalker": "omnivore", "portal_phantom": "apex",
}

SEASON_MIGRATION = {
    "spring": {"wolf_pack": "dark_forest", "frost_spirit": "white_forest", "bogey": "witch_swamp"},
    "summer": {"wolf_pack": "blood_meadow", "frost_spirit": "white_forest", "bogey": "witch_swamp"},
    "autumn": {"wolf_pack": "dark_forest", "frost_spirit": "white_forest", "bogey": "abandoned_camp"},
    "winter": {"wolf_pack": "wolf_den", "frost_spirit": "white_forest", "bogey": "witch_swamp"},
}

NPC_EVENT_REACTIONS = {
    "forest_fire": {"state": "fleeing", "flee_to": "fishing_village"},
    "plague": {"state": "hiding", "flee_to": "library_of_echoes"},
    "undead_awakening": {"state": "hiding", "flee_to": "temple_of_shadows"},
    "flood": {"state": "fleeing", "flee_to": "dark_forest"},
    "clan_war": {"state": "hiding", "flee_to": "crystal_cave"},
    "wolf_pack_migration": {"state": "hiding", "flee_to": "fishing_village"},
}


class EcosystemService:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def tick_creature_population(self):
        async for db in get_db():
            result = await db.execute(
                text("SELECT id, creature_id, location, hp, max_hp, is_alive FROM creatures WHERE is_alive = 1")
            )
            creatures = result.mappings().all()

            region_counts = {}
            for c in creatures:
                loc = c["location"]
                if loc not in region_counts:
                    region_counts[loc] = {"total": 0, "herbivore": 0, "carnivore": 0, "apex": 0}
                region_counts[loc]["total"] += 1
                role = CREATURE_ROLES.get(c["creature_id"], "carnivore")
                region_counts[loc][role] = region_counts[loc].get(role, 0) + 1

            for loc, counts in region_counts.items():
                if counts["total"] > 15:
                    excess = counts["total"] - 15
                    await db.execute(
                        text("UPDATE creatures SET is_alive = 0 WHERE location = :loc AND is_alive = 1 LIMIT :limit"),
                        {"loc": loc, "limit": excess},
                    )
                    logger.info(f"Экосистема: перенаселение в {loc}, умерло {excess} существ")

                if counts["total"] < 2 and counts["total"] > 0:
                    missing = 3 - counts["total"]
                    await self._spawn_creatures(db, loc, missing)

            await db.commit()

    async def _spawn_creatures(self, db, location_id: str, count: int):
        import random
        candidates = [cid for cid, role in CREATURE_ROLES.items() if role in ("carnivore", "herbivore")]
        for _ in range(min(count, 3)):
            cid = random.choice(candidates)
            hp = random.randint(30, 60)
            db.add(CreatureModel(
                creature_id=f"{cid}_{random.randint(1000, 9999)}",
                name=f"Дикий {cid.split('_')[0]}",
                location=location_id,
                disposition="hostile",
                hp=hp, max_hp=hp,
                attack=random.randint(5, 12),
                defense=random.randint(2, 6),
                xp_reward=random.randint(10, 25),
            ))

    async def migrate_creatures(self, season: str):
        migration = SEASON_MIGRATION.get(season, {})
        if not migration:
            return

        async for db in get_db():
            for creature_id, target_loc in migration.items():
                result = await db.execute(
                    text("SELECT id FROM creatures WHERE creature_id LIKE :pattern AND is_alive = 1"),
                    {"pattern": f"{creature_id}%"},
                )
                rows = result.fetchall()
                if rows:
                    for row in rows:
                        await db.execute(
                            text("UPDATE creatures SET location = :loc WHERE id = :id"),
                            {"loc": target_loc, "id": row[0]},
                        )
                    logger.info(f"Миграция: {creature_id} → {target_loc} ({season})")
            await db.commit()

    async def react_to_event(self, event_type: str, region_id: str):
        reaction = NPC_EVENT_REACTIONS.get(event_type)
        if not reaction:
            return

        async for db in get_db():
            result = await db.execute(
                text("SELECT id, npc_id, location_str FROM npcs WHERE is_alive = 1 AND location_str LIKE :loc_pattern"),
                {"loc_pattern": f"%{region_id}%"},
            )
            npcs = result.mappings().all()

            for npc in npcs:
                flee_to = reaction["flee_to"]
                await db.execute(
                    update(NPCModel)
                    .where(NPCModel.id == npc["id"])
                    .values(state=reaction["state"], location_str=flee_to)
                )
                logger.info(f"NPC {npc['npc_id']} бежит из {region_id} → {flee_to} ({event_type})")

            await db.commit()

    async def tick(self, game_hour: int, season: str):
        await self.tick_creature_population()

        if 6 <= game_hour <= 8:
            await self.migrate_creatures(season)
