import logging
import random

from sqlalchemy import text, update

from database.base import get_db
from database.models.creature import CreatureModel
from database.models.npc import NPCModel

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
    "drought": {"state": "struggling", "flee_to": None},
    "famine": {"state": "starving", "flee_to": None},
    "bandits": {"state": "scared", "flee_to": "temple_of_shadows"},
    "bandits_on_road": {"state": "scared", "flee_to": "temple_of_shadows"},
    "harvest_festival": {"state": "celebrating", "flee_to": None},
    "lantern_festival": {"state": "celebrating", "flee_to": None},
    "merchant_caravan": {"state": "trading", "flee_to": None},
    "wandering_merchant": {"state": "trading", "flee_to": None},
    "meteorite": {"state": "panicked", "flee_to": "crystal_cave"},
    "fog_storm": {"state": "hiding", "flee_to": None},
    "ship_in_harbour": {"state": "curious", "flee_to": None},
    "ancient_altar_discovered": {"state": "curious", "flee_to": None},
    "ruin_anomaly": {"state": "fleeing", "flee_to": "fishing_village"},
}

CREATURE_WEATHER_BEHAVIOR = {
    "storm": {"aggro_bonus": 0.15, "spawn_bonus": 5, "preferred_roles": ["carnivore", "apex"]},
    "fog": {"aggro_bonus": 0.10, "spawn_bonus": 3, "preferred_roles": ["carnivore"]},
    "snow": {"aggro_bonus": 0.05, "spawn_bonus": 2, "preferred_roles": ["herbivore"]},
    "rain": {"aggro_bonus": 0.0, "spawn_bonus": 0, "preferred_roles": []},
    "clear": {"aggro_bonus": -0.05, "spawn_bonus": 0, "preferred_roles": []},
}

NIGHT_CREATURE_BONUS = {"carnivore": 0.10, "apex": 0.15}


class EcosystemService:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def tick_creature_population(self, game_hour: int = 12):
        async for db in get_db():
            result = await db.execute(
                text("SELECT id, creature_id, location, hp, max_hp, is_alive FROM creatures WHERE is_alive = 1")
            )
            creatures = result.mappings().all()

            region_counts = {}
            for c in creatures:
                loc = c["location"]
                if loc not in region_counts:
                    region_counts[loc] = {"total": 0, "herbivore": 0, "carnivore": 0, "apex": 0, "ids": []}
                region_counts[loc]["total"] += 1
                role = CREATURE_ROLES.get(c["creature_id"].rsplit("_", 1)[0] if "_" in c["creature_id"] else c["creature_id"], "carnivore")
                region_counts[loc][role] = region_counts[loc].get(role, 0) + 1
                region_counts[loc]["ids"].append({"id": c["id"], "creature_id": c["creature_id"], "role": role, "hp": c["hp"]})

            await self._process_food_chain(db, region_counts)

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
                    weather = "clear"
                    try:
                        r = await db.execute(text("SELECT current_weather FROM locations WHERE id = :lid OR location_id = :lid LIMIT 1"), {"lid": loc})
                        row = r.mappings().first()
                        if row:
                            weather = row.get("current_weather", "clear")
                    except Exception:
                        pass
                    await self._spawn_creatures(db, loc, missing, weather, game_hour)

            await db.commit()

    async def _process_food_chain(self, db, region_counts: dict):
        for loc, counts in region_counts.items():
            creatures = counts.get("ids", [])
            herbivores = [c for c in creatures if c["role"] == "herbivore"]
            carnivores = [c for c in creatures if c["role"] in ("carnivore", "apex")]

            if carnivores and herbivores:
                for carnivore in carnivores:
                    if herbivores and random.random() < 0.30:
                        prey = random.choice(herbivores)
                        await db.execute(
                            text("UPDATE creatures SET is_alive = 0 WHERE id = :id"),
                            {"id": prey["id"]},
                        )
                        herbivores.remove(prey)
                        counts["total"] -= 1
                        logger.info(f"Цепь питания: {carnivore['creature_id']} съел {prey['creature_id']} в {loc}")

            if not herbivores and counts.get("herbivore", 0) == 0 and counts["total"] < 8:
                if random.random() < 0.40:
                    await self._spawn_creatures(db, loc, 1, "clear", 12)
                    logger.info(f"Цепь питания: травоядные вымерли в {loc}, спавн нового")

    async def _spawn_creatures(self, db, location_id: str, count: int, weather: str = "clear", game_hour: int = 12):
        weather_behavior = CREATURE_WEATHER_BEHAVIOR.get(weather, CREATURE_WEATHER_BEHAVIOR["clear"])
        preferred = weather_behavior.get("preferred_roles", [])
        is_night = game_hour >= 23 or game_hour <= 5

        candidates = []
        for cid, role in CREATURE_ROLES.items():
            if role in ("carnivore", "herbivore"):
                weight = 1
                if role in preferred:
                    weight = 3
                if is_night and role in NIGHT_CREATURE_BONUS:
                    weight += 2
                candidates.extend([cid] * weight)

        for _ in range(min(count, 3)):
            cid = random.choice(candidates) if candidates else random.choice(list(CREATURE_ROLES.keys()))
            hp = random.randint(30, 60)
            attack = random.randint(5, 12)
            defense = random.randint(2, 6)
            if weather == "storm":
                attack += random.randint(1, 3)
            elif weather == "fog":
                defense += random.randint(1, 2)
            elif is_night:
                attack += random.randint(0, 2)

            db.add(CreatureModel(
                creature_id=f"{cid}_{random.randint(1000, 9999)}",
                name=f"Дикий {cid.split('_')[0]}",
                location=location_id,
                disposition="hostile",
                hp=hp, max_hp=hp,
                attack=attack,
                defense=defense,
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
        await self.tick_creature_population(game_hour)

        if 6 <= game_hour <= 8:
            await self.migrate_creatures(season)
