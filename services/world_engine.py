import asyncio
import logging
import random
from datetime import datetime
from sqlalchemy import text
from database.base import get_db
from database.models.world_state import WorldStateModel
from database.models.world_event_record import WorldEventRecordModel
from services.world_event_defs import WORLD_EVENT_DEFS, get_random_events
from domain.events import EventType, Importance

logger = logging.getLogger("MIST.world_engine")

SEASONS = ["spring", "summer", "autumn", "winter"]
SEASON_NAMES = {
    "spring": "Весна",
    "summer": "Лето",
    "autumn": "Осень",
    "winter": "Зима",
}
DAYS_PER_SEASON = 30
TIME_SCALE = 10  # 1 реальная минута = 10 игровых минут

SEASON_MODIFIERS = {
    "spring": {"food_supply": 10, "tree_density": 5, "danger_level": -5, "magic_level": 5},
    "summer": {"food_supply": 15, "tree_density": 0, "danger_level": 0, "magic_level": 0},
    "autumn": {"food_supply": -10, "tree_density": -5, "danger_level": 5, "magic_level": -5},
    "winter": {"food_supply": -25, "tree_density": -10, "danger_level": 10, "magic_level": -10},
}

WEATHER_STATES = ["clear", "rain", "storm", "fog", "snow"]
WEATHER_TRANSITIONS = {
    "clear": {"clear": 0.50, "rain": 0.30, "fog": 0.20},
    "rain": {"clear": 0.30, "rain": 0.40, "storm": 0.20, "fog": 0.10},
    "storm": {"rain": 0.50, "storm": 0.30, "clear": 0.20},
    "fog": {"clear": 0.40, "fog": 0.40, "rain": 0.20},
    "snow": {"snow": 0.50, "clear": 0.30, "fog": 0.20},
}

WEATHER_SEASON_BIAS = {
    "spring": {"clear": 0.40, "rain": 0.35, "fog": 0.15, "storm": 0.10},
    "summer": {"clear": 0.60, "rain": 0.20, "storm": 0.15, "fog": 0.05},
    "autumn": {"clear": 0.25, "rain": 0.35, "fog": 0.25, "storm": 0.15},
    "winter": {"clear": 0.20, "snow": 0.45, "fog": 0.20, "storm": 0.15},
}


class WorldEngine:

    def __init__(self, chronicle, ecosystem=None, guild_territory=None, home_service=None,
                 npc_life=None, world_memory=None, seasonal_quest=None, world_boss=None,
                 seasonal_event=None, daily_event=None, npc_scheduler=None):
        self.chronicle = chronicle
        self._running = False
        self._state = None
        self.ecosystem = ecosystem
        self.guild_territory = guild_territory
        self.home_service = home_service
        self.npc_life = npc_life
        self.world_memory = world_memory
        self.seasonal_quest = seasonal_quest
        self.world_boss = world_boss
        self.seasonal_event = seasonal_event
        self.daily_event = daily_event
        self.npc_scheduler = npc_scheduler

    async def _load_state(self):
        async for db in get_db():
            result = await db.execute(
                text("SELECT * FROM world_state ORDER BY id LIMIT 1")
            )
            row = result.mappings().first()
            if row:
                self._state = dict(row)
            else:
                self._state = None
            return self._state

    async def _save_state(self):
        async for db in get_db():
            state = self._state
            await db.execute(
                text("""
                    UPDATE world_state SET
                        game_day = :game_day,
                        game_hour = :game_hour,
                        game_minute = :game_minute,
                        season = :season,
                        world_pressure = :world_pressure,
                        prosperity = :prosperity,
                        chaos = :chaos,
                        magic_level = :magic_level,
                        danger_level = :danger_level,
                        total_population = :total_population,
                        events_count = :events_count,
                        last_tick_at = :last_tick_at
                    WHERE id = :id
                """),
                {
                    "id": state["id"],
                    "game_day": state["game_day"],
                    "game_hour": state["game_hour"],
                    "game_minute": state["game_minute"],
                    "season": state["season"],
                    "world_pressure": state["world_pressure"],
                    "prosperity": state["prosperity"],
                    "chaos": state["chaos"],
                    "magic_level": state["magic_level"],
                    "danger_level": state["danger_level"],
                    "total_population": state["total_population"],
                    "events_count": state["events_count"],
                    "last_tick_at": datetime.utcnow(),
                },
            )
            await db.commit()

    async def init(self):
        if self._state is None:
            await self._load_state()
        if self._state is None:
            await self._create_initial_state()

    async def _create_initial_state(self):
        async for db in get_db():
            db.add(WorldStateModel(
                game_day=1,
                game_hour=8,
                game_minute=0,
                season="spring",
                world_pressure=10,
                prosperity=50,
                chaos=10,
                magic_level=20,
                danger_level=30,
                events_count=0,
                last_tick_at=datetime.utcnow(),
            ))
            await db.commit()
            logger.info("Создано начальное состояние мира: День 1, 08:00, Весна")

        await self._load_state()

    def get_state(self) -> dict:
        if not self._state:
            return None
        return {
            "game_day": self._state["game_day"],
            "game_hour": self._state["game_hour"],
            "game_minute": self._state["game_minute"],
            "season": self._state["season"],
            "season_name": SEASON_NAMES.get(self._state["season"], "???"),
            "world_pressure": self._state["world_pressure"],
            "prosperity": self._state["prosperity"],
            "chaos": self._state["chaos"],
            "magic_level": self._state["magic_level"],
            "danger_level": self._state["danger_level"],
            "total_population": self._state["total_population"],
            "events_count": self._state["events_count"],
            "display": self._display(),
        }

    def _display(self) -> str:
        s = self._state
        season = SEASON_NAMES.get(s["season"], "???")
        return f"День {s['game_day']}, {s['game_hour']:02d}:{s['game_minute']:02d} — {season}"

    async def tick(self, real_minutes: int = None):
        if self._state is None:
            await self._load_state()
        if self._state is None:
            return

        if real_minutes is None:
            real_minutes = 15

        game_minutes = real_minutes * TIME_SCALE
        s = self._state
        old_day = s["game_day"]
        old_season = s["season"]

        s["game_minute"] += game_minutes
        while s["game_minute"] >= 60:
            s["game_minute"] -= 60
            s["game_hour"] += 1

        while s["game_hour"] >= 24:
            s["game_hour"] -= 24
            s["game_day"] += 1

        new_day = s["game_day"]
        if new_day > old_day:
            await self._on_new_day(old_day, new_day)

        new_season = SEASONS[((s["game_day"] - 1) // DAYS_PER_SEASON) % 4]
        if new_season != old_season:
            s["season"] = new_season
            await self._on_season_change(old_season, new_season)

        await self._update_location_weather()
        await self._save_state()

    async def _on_new_day(self, old_day: int, new_day: int):
        events_today = await self._generate_world_events(new_day)
        await self._expire_events(new_day)
        await self._trigger_chain_events(new_day)
        await self._recalc_world_pressure()

        if self.ecosystem:
            await self.ecosystem.tick(self._state["game_hour"], self._state["season"])

        if self.guild_territory:
            await self.guild_territory.recalculate_territory_bonus()

        if self.home_service:
            await self.home_service.tick_homes(self._state["game_hour"], self._state["season"])

        if self.npc_life:
            await self.npc_life.tick(new_day, self._state["game_hour"], self._state["season"])

        if self.npc_scheduler:
            await self.npc_scheduler.tick(self._state["game_hour"], self._state["game_minute"])

        if self.world_memory:
            await self.world_memory.expire_old_memories()

        if self.seasonal_quest:
            await self.seasonal_quest.activate_seasonal_quests(self._state["season"])

        if self.world_boss:
            await self.world_boss.check_respawns(self._state["game_hour"])

        if self.daily_event:
            await self.daily_event.trigger_daily_event(new_day)

        if events_today:
            await self.chronicle.publish(
                EventType.WORLD_EVENT,
                f"Наступил день {new_day}",
                importance=Importance.TRIVIAL,
            )
        else:
            await self.chronicle.publish(
                EventType.WORLD_EVENT,
                f"День {new_day} — тишина. Ничего особенного не произошло.",
                importance=Importance.TRIVIAL,
            )

    async def _generate_world_events(self, current_day: int) -> int:
        regions = {}
        async for db in get_db():
            result = await db.execute(text("SELECT id, region_id, name FROM locations"))
            for row in result.mappings().all():
                rid = row["region_id"]
                if rid not in regions:
                    regions[rid] = []
                regions[rid].append({"id": row["id"], "name": row["name"]})

        events_count = 0
        async for db in get_db():
            for region_id, locs in regions.items():
                event_keys = get_random_events(
                    region_id=region_id,
                    current_day=current_day,
                    world_pressure=self._state.get("world_pressure", 10),
                )
                for event_key in event_keys:
                    ev_def = WORLD_EVENT_DEFS[event_key]
                    target_loc = random.choice(locs)
                    record = WorldEventRecordModel(
                        event_type=event_key,
                        name=ev_def["name"],
                        description=ev_def["description"],
                        region_id=region_id,
                        location_id=target_loc["id"],
                        start_day=current_day,
                        end_day=current_day + ev_def["duration_days"] if ev_def["duration_days"] > 0 else None,
                        is_active=True,
                        effects=ev_def.get("effects", {}),
                        chain_events=ev_def.get("chain_events", []),
                    )
                    db.add(record)
                    await self._apply_event_effects(target_loc["id"], ev_def.get("effects", {}), db)

                    if self.ecosystem:
                        await self.ecosystem.react_to_event(event_key, region_id)

                    if self.home_service:
                        await self.home_service.react_to_world_event(event_key)

                    icon = ev_def.get("icon", "")
                    await self.chronicle.publish(
                        EventType.WORLD_EVENT,
                        f"{icon} {ev_def['name']}: {ev_def['description']}",
                        importance=Importance.COMMON,
                    )
                    logger.info(f"Событие мира: {ev_def['name']} в {target_loc['name']} ({region_id})")
                    events_count += 1

            await db.commit()
        return events_count

    async def _apply_event_effects(self, location_id: str, effects: dict, db=None):
        if not effects:
            return

        if db:
            for field, delta in effects.items():
                await db.execute(
                    text(f"UPDATE locations SET {field} = MIN(100, MAX(0, {field} + :delta)) WHERE id = :loc_id"),
                    {"delta": delta, "loc_id": location_id},
                )
        else:
            async for _db in get_db():
                for field, delta in effects.items():
                    await _db.execute(
                        text(f"UPDATE locations SET {field} = MIN(100, MAX(0, {field} + :delta)) WHERE id = :loc_id"),
                        {"delta": delta, "loc_id": location_id},
                    )
                await _db.commit()

    async def _expire_events(self, current_day: int):
        async for db in get_db():
            await db.execute(
                text("UPDATE world_event_records SET is_active = 0 WHERE is_active = 1 AND end_day IS NOT NULL AND end_day <= :day"),
                {"day": current_day},
            )
            await db.commit()

    async def _trigger_chain_events(self, current_day: int):
        async for db in get_db():
            result = await db.execute(
                text("SELECT event_type, region_id, location_id, start_day FROM world_event_records "
                     "WHERE is_active = 1 AND chain_events IS NOT NULL AND json_array_length(chain_events) > 0")
            )
            active_with_chains = result.mappings().all()

            for rec in active_with_chains:
                ev_def = WORLD_EVENT_DEFS.get(rec["event_type"])
                if not ev_def:
                    continue
                chain_delay = ev_def.get("chain_delay_days", 3)
                trigger_day = rec["start_day"] + chain_delay

                if current_day >= trigger_day:
                    for chain_key in (rec["chain_events"] or []):
                        chain_def = WORLD_EVENT_DEFS.get(chain_key)
                        if not chain_def:
                            continue
                        exists = await db.execute(
                            text("SELECT id FROM world_event_records WHERE event_type = :etype AND region_id = :rid AND is_active = 1"),
                            {"etype": chain_key, "rid": rec["region_id"]},
                        )
                        if exists.first():
                            continue

                        target_loc = rec["location_id"]
                        new_record = WorldEventRecordModel(
                            event_type=chain_key,
                            name=chain_def["name"],
                            description=chain_def["description"],
                            region_id=rec["region_id"],
                            location_id=target_loc,
                            start_day=current_day,
                            end_day=current_day + chain_def["duration_days"] if chain_def["duration_days"] > 0 else None,
                            is_active=True,
                            effects=chain_def.get("effects", {}),
                            chain_events=chain_def.get("chain_events", []),
                            triggered_by=rec.get("event_type"),
                        )
                        db.add(new_record)
                        await self._apply_event_effects(target_loc, chain_def.get("effects", {}), db)

                        icon = chain_def.get("icon", "")
                        await self.chronicle.publish(
                            EventType.WORLD_EVENT,
                            f"{icon} {chain_def['name']}: {chain_def['description']}",
                            importance=Importance.COMMON,
                        )
                        logger.info(f"Цепная реакция: {chain_def['name']} после {rec['event_type']}")

            await db.commit()

    async def _recalc_world_pressure(self):
        async for db in get_db():
            result = await db.execute(
                text("SELECT COUNT(*) as cnt FROM world_event_records WHERE is_active = 1")
            )
            active_count = result.scalar() or 0

            new_pressure = min(100, max(0, 10 + active_count * 5))
            self._state["world_pressure"] = new_pressure
            await db.execute(
                text("UPDATE world_state SET world_pressure = :p WHERE id = :id"),
                {"p": new_pressure, "id": self._state["id"]},
            )
            await db.commit()

    async def _on_season_change(self, old_season: str, new_season: str):
        old_name = SEASON_NAMES.get(old_season, old_season)
        new_name = SEASON_NAMES.get(new_season, new_season)
        mods = SEASON_MODIFIERS.get(new_season, {})

        if mods:
            async for db in get_db():
                for field, delta in mods.items():
                    await db.execute(
                        text(f"UPDATE locations SET {field} = MIN(100, MAX(0, {field} + :delta))"),
                        {"delta": delta},
                    )
                await db.commit()

        await self.chronicle.publish(
            EventType.WORLD_EVENT,
            f"Сменился сезон: {old_name} → {new_name}",
            importance=Importance.COMMON,
        )
        logger.info(f"Сезон: {old_name} → {new_name}")

        if self.seasonal_event:
            await self.seasonal_event.trigger_season_event(new_season, self._state["game_day"])

    async def _update_location_weather(self):
        season = self._state["season"]
        season_bias = WEATHER_SEASON_BIAS.get(season, WEATHER_SEASON_BIAS["spring"])

        async for db in get_db():
            result = await db.execute(text("SELECT id, location_id, current_weather FROM locations"))
            locations = result.mappings().all()

            for loc in locations:
                current = loc["current_weather"] or "clear"
                transitions = WEATHER_TRANSITIONS.get(current, {})
                biased = {}
                for w, base_prob in transitions.items():
                    season_factor = season_bias.get(w, 0.1)
                    biased[w] = (base_prob + season_factor) / 2

                total = sum(biased.values())
                if total > 0:
                    biased = {w: p / total for w, p in biased.items()}

                roll = random.random()
                cumulative = 0.0
                new_weather = current
                for w, chance in biased.items():
                    cumulative += chance
                    if roll <= cumulative:
                        new_weather = w
                        break

                if new_weather != current:
                    await db.execute(
                        text("UPDATE locations SET current_weather = :weather WHERE id = :id"),
                        {"weather": new_weather, "id": loc["id"]},
                    )

            await db.commit()

    async def get_location_states(self, limit: int = 50) -> list:
        async for db in get_db():
            result = await db.execute(
                text("SELECT location_id, name, danger_level, food_supply, tree_density, "
                     "magic_level, creature_count, population, wealth, current_weather, "
                     "current_event, reputation "
                     "FROM locations ORDER BY location_id LIMIT :limit"),
                {"limit": limit},
            )
            locations = [dict(row) for row in result.mappings().all()]

            for loc in locations:
                ev_result = await db.execute(
                    text("SELECT event_type, name FROM world_event_records "
                         "WHERE location_id = :loc_id AND is_active = 1 LIMIT 3"),
                    {"loc_id": loc["location_id"]},
                )
                loc["active_events"] = [dict(r) for r in ev_result.mappings().all()]

            return locations

    async def get_active_events(self, region_id: str = None) -> list:
        async for db in get_db():
            if region_id:
                result = await db.execute(
                    text("SELECT * FROM world_event_records WHERE is_active = 1 AND region_id = :rid ORDER BY start_day DESC"),
                    {"rid": region_id},
                )
            else:
                result = await db.execute(
                    text("SELECT * FROM world_event_records WHERE is_active = 1 ORDER BY start_day DESC")
                )
            return [dict(row) for row in result.mappings().all()]

    async def get_event_stats(self) -> dict:
        async for db in get_db():
            total = (await db.execute(text("SELECT COUNT(*) FROM world_event_records"))).scalar() or 0
            active = (await db.execute(text("SELECT COUNT(*) FROM world_event_records WHERE is_active = 1"))).scalar() or 0
            return {"total_events": total, "active_events": active}

    async def get_news(self, day: int = None) -> dict:
        if day is None:
            day = self._state["game_day"] if self._state else 1

        async for db in get_db():
            events_result = await db.execute(
                text("SELECT event_type, name, description, region_id, location_id, "
                     "start_day, end_day, is_active, effects, triggered_by "
                     "FROM world_event_records WHERE start_day = :day ORDER BY id"),
                {"day": day},
            )
            events = [dict(row) for row in events_result.mappings().all()]

            active_result = await db.execute(
                text("SELECT event_type, name, region_id, is_active, end_day "
                     "FROM world_event_records WHERE is_active = 1 ORDER BY start_day DESC LIMIT 10")
            )
            active = [dict(row) for row in active_result.mappings().all()]

            loc_result = await db.execute(
                text("SELECT name, danger_level, food_supply, current_weather "
                     "FROM locations ORDER BY danger_level DESC LIMIT 5")
            )
            dangerous = [dict(row) for row in loc_result.mappings().all()]

            return {
                "day": day,
                "season": self._state["season"] if self._state else "spring",
                "events": events,
                "active": active,
                "dangerous_locations": dangerous,
            }

    async def start_loop(self, interval_seconds: int = 900):
        await self.init()
        self._running = True
        logger.info(f"WorldEngine запущен (tick каждые {interval_seconds}с)")

        while self._running:
            try:
                await asyncio.sleep(interval_seconds)
                await self.tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"WorldEngine tick error: {e}", exc_info=True)
                await asyncio.sleep(60)

    def stop(self):
        self._running = False

    def get_silence_whisper(self) -> str:
        import random as _random
        whispers = [
            "Сегодня тихо. Мир отдыхает.",
            "Тишина. Даже туман замер.",
            "Ничего не происходит. Пока.",
            "Мир дышит ровно. Без штормов.",
            "Спокойный день. Настораживает.",
            "Туман плывёт тихо. Без шёпотов.",
            "Мир помнит всё. Сегодня он помнит покой.",
            "Ни одного крика. Ни одного звука. Только тишина.",
            "День как день. Но в MIST так не бывает.",
            "Мир ждёт. Он всегда ждёт.",
        ]
        return _random.choice(whispers)
