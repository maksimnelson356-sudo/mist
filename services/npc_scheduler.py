import asyncio
import logging

from sqlalchemy import select, update

from database.base import get_db
from database.models.npc import NPCModel

logger = logging.getLogger("MIST.npc_scheduler")

TIME_PERIODS = {
    "night": (0, 5),
    "morning": (6, 11),
    "afternoon": (12, 17),
    "evening": (18, 23),
}


class NPCScheduler:

    def __init__(self, npc_service, world_engine=None):
        self.npc_service = npc_service
        self.world_engine = world_engine
        self._running = False

    def get_current_period(self, game_hour: int = None) -> str:
        if game_hour is not None:
            hour = game_hour
        else:
            from datetime import datetime
            hour = datetime.now().hour

        for period, (start, end) in TIME_PERIODS.items():
            if start <= hour <= end:
                return period
        return "night"

    async def tick(self, game_hour: int = None, game_minute: int = 0):
        current_period = self.get_current_period(game_hour)

        async for db in get_db():
            stmt = select(NPCModel).where(NPCModel.is_alive == True)
            result = await db.execute(stmt)
            npcs = result.scalars().all()

            for npc in npcs:
                schedule = npc.schedule if isinstance(npc.schedule, dict) else {}
                if not schedule:
                    continue

                target_location = schedule.get(current_period)
                if target_location and target_location != npc.location_str:
                    await db.execute(
                        update(NPCModel)
                        .where(NPCModel.id == npc.id)
                        .values(location_str=target_location, state="idle")
                    )
                    logger.info(f"NPC {npc.npc_id} перемещается: {npc.location_str} → {target_location} ({current_period})")

                if current_period == "night":
                    new_state = "sleeping"
                elif current_period == "morning":
                    new_state = "idle"
                else:
                    new_state = npc.state

                if new_state != npc.state:
                    await db.execute(
                        update(NPCModel)
                        .where(NPCModel.id == npc.id)
                        .values(state=new_state)
                    )

            await db.commit()
            break

    async def start_loop(self, interval: int = 300):
        self._running = True
        while self._running:
            await self.tick()
            await asyncio.sleep(interval)

    def stop(self):
        self._running = False
