import asyncio
import logging
import random
from datetime import UTC, datetime

from sqlalchemy import select, text, update

from database.base import get_db
from database.models.npc import NPCModel
from database.models.npc_relationship import NPCRelationshipModel
from domain.events import EventType, Importance

logger = logging.getLogger("MIST.npc_life")

NPC_GOALS = {
    "merchant": ["sell_goods", "find_rare_item", "expand_trade", "make_friend"],
    "guard": ["patrol_area", "train_fight", "protect_npcs", "scout_danger"],
    "elder": ["tell_lore", "settle_disputes", "plan_festival", "remember_history"],
    "healer": ["gather_herbs", "heal_wounded", "study_medicine", "protect_grove"],
    "bartender": ["serve_drinks", "listen_gossip", "keep_peace", "find_stories"],
    "shady": ["gather_info", "make_deal", "steal_something", "blackmail"],
    "quest_giver": ["find_adventurer", "research_ruins", "track_creature", "protect_artifact"],
}

RELATION_TYPES = {
    "friend": {"min": 30, "max": 100, "bonuses": {"trade": 0.8, "quest": True}},
    "rival": {"min": -100, "max": -30, "penalties": {"trade": 1.5, "combat": True}},
    "neutral": {"min": -29, "max": 29},
    "trade_partner": {"min": 10, "max": 50, "bonuses": {"trade": 0.9}},
    "mentor": {"min": 40, "max": 80, "bonuses": {"xp": 1.2}},
    "enemy": {"min": -100, "max": -60, "penalties": {"combat": True, "danger": 2.0}},
}


async def get_npc_relation_to_player(npc_id: str, player_id: int) -> dict:
    try:
        async for db in get_db():
            result = await db.execute(
                select(NPCRelationshipModel)
                .where(NPCRelationshipModel.npc_id == npc_id)
                .where(NPCRelationshipModel.target_id == str(player_id))
            )
            rel = result.scalar_one_or_none()
            if not rel:
                return {"type": "neutral", "value": 0, "bonuses": {}, "penalties": {}}

            rel_type = rel.relation_type or "neutral"
            rdef = RELATION_TYPES.get(rel_type, {})
            return {
                "type": rel_type,
                "value": rel.value,
                "bonuses": rdef.get("bonuses", {}),
                "penalties": rdef.get("penalties", {}),
            }
    except Exception:
        return {"type": "neutral", "value": 0, "bonuses": {}, "penalties": {}}


async def get_trade_multiplier(player_id: int, npc_id: str = None) -> float:
    if not npc_id:
        return 1.0
    rel = await get_npc_relation_to_player(npc_id, player_id)
    return rel["bonuses"].get("trade", 1.0) * rel["penalties"].get("trade", 1.0)


async def get_xp_multiplier(player_id: int) -> float:
    try:
        async for db in get_db():
            result = await db.execute(
                select(NPCRelationshipModel)
                .where(NPCRelationshipModel.target_id == str(player_id))
            )
            rels = result.scalars().all()
            for rel in rels:
                rdef = RELATION_TYPES.get(rel.relation_type or "neutral", {})
                if "xp" in rdef.get("bonuses", {}):
                    return rdef["bonuses"]["xp"]
            return 1.0
    except Exception:
        return 1.0


async def is_enemy_nearby(player_id: int, location_id: str) -> bool:
    try:
        async for db in get_db():
            result = await db.execute(
                select(NPCRelationshipModel)
                .where(NPCRelationshipModel.target_id == str(player_id))
                .where(NPCRelationshipModel.relation_type == "enemy")
            )
            enemies = result.scalars().all()
            for e in enemies:
                npc_result = await db.execute(
                    select(NPCModel).where(NPCModel.npc_id == e.npc_id)
                )
                npc = npc_result.scalar_one_or_none()
                if npc and npc.location_str == location_id:
                    return True
            return False
    except Exception:
        return False


async def get_npc_location_bonuses(location_id: str) -> dict:
    bonuses = {"danger_reduction": 0, "trade_bonus": 0.0, "heal_amount": 0}
    try:
        async for db in get_db():
            result = await db.execute(
                select(NPCModel).where(
                    NPCModel.location_str == location_id,
                    NPCModel.is_alive == True,
                )
            )
            npcs = result.scalars().all()
            for npc in npcs:
                state = npc.state or ""
                if state == "working:patrol_area":
                    bonuses["danger_reduction"] += 2
                elif state == "working:sell_goods":
                    bonuses["trade_bonus"] += 0.05
                elif state == "working:heal_wounded":
                    bonuses["heal_amount"] += 10
    except Exception:
        pass
    return bonuses

DEATH_REASONS = [
    "старость", "болезнь", "отравление", "убийство", "стихия",
    "бандиты", "нежить", "дракон", "голод", "пропажа",
]

BIRTH_REASONS = [
    "переселение", "рождение", "прибытие каравана", "бегство из города",
    "поиск лучшей жизни", "приказ гильдии", "изгнание",
]


class NPCLifeEngine:

    def __init__(self, chronicle):
        self.chronicle = chronicle
        self._running = False

    async def tick(self, game_day: int, game_hour: int, season: str):
        await self._process_npc_goals(game_hour)
        await self._process_relationships()
        if game_hour == 0:
            await self._process_lifecycle(game_day, season)

    async def _process_npc_goals(self, game_hour: int):
        weather = "clear"
        try:
            from sqlalchemy import text
            async for db_check in get_db():
                r = await db_check.execute(text("SELECT current_weather FROM locations ORDER BY RANDOM() LIMIT 1"))
                row = r.mappings().first()
                if row:
                    weather = row.get("current_weather", "clear")
                break
        except Exception:
            pass

        from services.weather_system import WEATHER_EFFECTS
        weather_fx = WEATHER_EFFECTS.get(weather, {})
        npc_shelter = weather_fx.get("npc_shelter", False)

        async for db in get_db():
            result = await db.execute(
                select(NPCModel).where(NPCModel.is_alive == True)
            )
            npcs = result.scalars().all()

            for npc in npcs:
                npc_type = npc.npc_type
                goals = NPC_GOALS.get(npc_type, ["idle"])
                current_state = npc.state

                if current_state == "sleeping":
                    continue

                if npc_shelter:
                    new_state = "sheltering"
                elif game_hour >= 6 and game_hour <= 11:
                    new_goal = random.choice(goals)
                    new_state = f"working:{new_goal}"
                elif game_hour >= 12 and game_hour <= 17:
                    new_state = current_state if current_state.startswith("working:") else "idle"
                elif game_hour >= 18 and game_hour <= 23:
                    new_state = "socializing"
                else:
                    new_state = "idle"

                if new_state != npc.state:
                    await db.execute(
                        update(NPCModel)
                        .where(NPCModel.id == npc.id)
                        .values(state=new_state)
                    )

            await db.commit()
            break

    async def _process_relationships(self):
        async for db in get_db():
            result = await db.execute(
                select(NPCModel).where(NPCModel.is_alive == True)
            )
            npcs = result.scalars().all()

            npc_list = [dict(row) for row in [
                {"id": n.id, "npc_id": n.npc_id, "location_str": n.location_str, "npc_type": n.npc_type}
                for n in npcs
            ]]

            if len(npc_list) < 2:
                return

            for i in range(len(npc_list)):
                for j in range(i + 1, len(npc_list)):
                    npc_a = npc_list[i]
                    npc_b = npc_list[j]

                    if npc_a["location_str"] != npc_b["location_str"]:
                        continue

                    existing = await db.execute(
                        select(NPCRelationshipModel).where(
                            NPCRelationshipModel.npc_a_id == npc_a["npc_id"],
                            NPCRelationshipModel.npc_b_id == npc_b["npc_id"],
                        )
                    )
                    rel = existing.scalar_one_or_none()

                    delta = random.randint(-3, 5)
                    if npc_a["npc_type"] == npc_b["npc_type"]:
                        delta += 2
                    if npc_a["npc_type"] == "shady" or npc_b["npc_type"] == "shady":
                        delta -= 1

                    if rel:
                        new_value = max(-100, min(100, rel.value + delta))
                        events = rel.events or []
                        if abs(delta) > 2:
                            events.append({
                                "day": datetime.now(UTC).isoformat(),
                                "delta": delta,
                                "reason": "встреча в локации",
                            })
                            if len(events) > 10:
                                events = events[-10:]

                        await db.execute(
                            update(NPCRelationshipModel)
                            .where(NPCRelationshipModel.id == rel.id)
                            .values(value=new_value, events=events, last_interaction_at=datetime.now(UTC))
                        )
                    else:
                        new_rel = NPCRelationshipModel(
                            npc_a_id=npc_a["npc_id"],
                            npc_b_id=npc_b["npc_id"],
                            value=delta,
                            events=[{"day": datetime.now(UTC).isoformat(), "delta": delta, "reason": "первая встреча"}],
                        )
                        db.add(new_rel)

            await db.commit()

    async def _process_lifecycle(self, game_day: int, season: str):
        async for db in get_db():
            result = await db.execute(
                select(NPCModel).where(NPCModel.is_alive == True)
            )
            npcs = result.scalars().all()

            for npc in npcs:
                if random.random() < 0.02:
                    reason = random.choice(DEATH_REASONS)
                    await db.execute(
                        update(NPCModel)
                        .where(NPCModel.id == npc.id)
                        .values(is_alive=False, state="dead")
                    )
                    await self.chronicle.publish(
                        EventType.WORLD_EVENT,
                        f"💀 NPC {npc.name} погиб: {reason}",
                        importance=Importance.COMMON,
                    )
                    logger.info(f"NPC {npc.name} погиб: {reason}")

            total_result = await db.execute(text("SELECT COUNT(*) FROM npcs"))
            total_npcs = total_result.scalar() or 0
            if random.random() < 0.03 and total_npcs < 15:
                reason = random.choice(BIRTH_REASONS)
                npc_type = random.choice(["merchant", "guard", "healer", "bartender", "shady"])
                names = ["Путник", "Странник", "Торговец", "Охотник", "Целитель", "Страж"]
                name = f"{random.choice(names)}_{random.randint(100, 999)}"
                location = random.choice([
                    "fishing_village", "market_square", "dark_harbour",
                    "riverbank", "enchanted_grove", "fog_village",
                ])

                new_npc = NPCModel(
                    npc_id=f"npc_{name.lower()}",
                    name=name,
                    description=f"Прибыл: {reason}",
                    npc_type=npc_type,
                    location_str=location,
                    state="idle",
                    disposition="neutral",
                    schedule={
                        "morning": location,
                        "afternoon": location,
                        "evening": location,
                        "night": location,
                    },
                )
                db.add(new_npc)
                await self.chronicle.publish(
                    EventType.WORLD_EVENT,
                    f"👶 Новый NPC: {name} ({npc_type}) в {location} — {reason}",
                    importance=Importance.TRIVIAL,
                )
                logger.info(f"Новый NPC: {name} ({npc_type}) в {location}")

            await db.commit()

    async def get_relationship(self, npc_a_id: str, npc_b_id: str) -> dict | None:
        async for db in get_db():
            result = await db.execute(
                select(NPCRelationshipModel).where(
                    NPCRelationshipModel.npc_a_id == npc_a_id,
                    NPCRelationshipModel.npc_b_id == npc_b_id,
                )
            )
            rel = result.scalar_one_or_none()
            if rel:
                return {
                    "npc_a": rel.npc_a_id,
                    "npc_b": rel.npc_b_id,
                    "value": rel.value,
                    "type": self._get_relation_type(rel.value),
                    "events": rel.events or [],
                }
            return None

    async def get_npc_relationships(self, npc_id: str) -> list:
        async for db in get_db():
            result = await db.execute(
                select(NPCRelationshipModel).where(
                    (NPCRelationshipModel.npc_a_id == npc_id) |
                    (NPCRelationshipModel.npc_b_id == npc_id)
                )
            )
            return [{
                "npc_a": r.npc_a_id,
                "npc_b": r.npc_b_id,
                "value": r.value,
                "type": self._get_relation_type(r.value),
            } for r in result.scalars().all()]

    def _get_relation_type(self, value: int) -> str:
        for rtype, rdef in RELATION_TYPES.items():
            if "min" in rdef and "max" in rdef:
                if rdef["min"] <= value <= rdef["max"]:
                    return rtype
        return "neutral"

    async def get_npc_stats(self) -> dict:
        async for db in get_db():
            total = (await db.execute(text("SELECT COUNT(*) FROM npcs"))).scalar() or 0
            alive = (await db.execute(text("SELECT COUNT(*) FROM npcs WHERE is_alive = 1"))).scalar() or 0
            dead = total - alive
            rels = (await db.execute(text("SELECT COUNT(*) FROM npc_relationships"))).scalar() or 0
            return {"total": total, "alive": alive, "dead": dead, "relationships": rels}

    async def start_loop(self, interval: int = 900):
        self._running = True
        while self._running:
            await asyncio.sleep(interval)

    def stop(self):
        self._running = False
