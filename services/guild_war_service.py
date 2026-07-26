import logging
from datetime import datetime

from sqlalchemy import select, text, update

from database.base import get_db
from database.models.guild import GuildModel
from database.models.guild_war import GuildWarModel
from database.models.location import LocationModel
from domain.events import EventType, Importance

logger = logging.getLogger("MIST.guild_war")


class GuildWarService:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def declare_war(self, attacker_guild_id: str, defender_guild_id: str, location_id: str) -> dict:
        async for db in get_db():
            existing = await db.execute(
                select(GuildWarModel).where(
                    GuildWarModel.attacker_guild_id == attacker_guild_id,
                    GuildWarModel.defender_guild_id == defender_guild_id,
                    GuildWarModel.location_id == location_id,
                    GuildWarModel.status == "active",
                )
            )
            if existing.scalar_one_or_none():
                return {"success": False, "message": "Война уже объявлена."}

            result = await db.execute(
                select(GuildModel).where(GuildModel.guild_id == attacker_guild_id)
            )
            attacker = result.scalar_one_or_none()
            result = await db.execute(
                select(GuildModel).where(GuildModel.guild_id == defender_guild_id)
            )
            defender = result.scalar_one_or_none()

            if not attacker or not defender:
                return {"success": False, "message": "Одна из гильдий не найдена."}

            war = GuildWarModel(
                attacker_guild_id=attacker_guild_id,
                defender_guild_id=defender_guild_id,
                location_id=location_id,
            )
            db.add(war)
            await db.commit()

            await self.chronicle.publish(
                EventType.WORLD_EVENT,
                f"⚔️ {attacker.name} объявила войну {defender.name} за контроль над локацией!",
                importance=Importance.RARE,
            )

            return {"success": True, "message": "⚔️ Война объявлена!", "war_id": war.id}

    async def resolve_battle(self, war_id: str, winner: str) -> dict:
        async for db in get_db():
            result = await db.execute(
                select(GuildWarModel).where(GuildWarModel.id == war_id)
            )
            war = result.scalar_one_or_none()
            if not war:
                return {"success": False, "message": "Война не найдена."}

            if winner == "attacker":
                new_wins = war.attacker_wins + 1
                await db.execute(
                    update(GuildWarModel)
                    .where(GuildWarModel.id == war_id)
                    .values(attacker_wins=new_wins)
                )
            elif winner == "defender":
                new_wins = war.defender_wins + 1
                await db.execute(
                    update(GuildWarModel)
                    .where(GuildWarModel.id == war_id)
                    .values(defender_wins=new_wins)
                )

            events = war.events or []
            events.append({
                "winner": winner,
                "day": datetime.utcnow().isoformat(),
            })
            if len(events) > 20:
                events = events[-20:]

            await db.execute(
                update(GuildWarModel)
                .where(GuildWarModel.id == war_id)
                .values(events=events)
            )

            await db.commit()
            return {"success": True, "winner": winner}

    async def end_war(self, war_id: str, result: str = "surrender") -> dict:
        async for db in get_db():
            war_result = await db.execute(
                select(GuildWarModel).where(GuildWarModel.id == war_id)
            )
            war = war_result.scalar_one_or_none()
            if not war:
                return {"success": False, "message": "Война не найдена."}

            await db.execute(
                update(GuildWarModel)
                .where(GuildWarModel.id == war_id)
                .values(status="ended", ended_at=datetime.utcnow())
            )

            if war.attacker_wins > war.defender_wins:
                new_owner = war.attacker_guild_id
            else:
                new_owner = war.defender_guild_id

            await db.execute(
                update(LocationModel)
                .where(LocationModel.id == war.location_id)
                .values(owner_guild_id=new_owner)
            )

            await db.commit()

            result_result = await db.execute(
                select(GuildModel).where(GuildModel.guild_id == new_owner)
            )
            winner_guild = result_result.scalar_one_or_none()
            winner_name = winner_guild.name if winner_guild else new_owner

            await self.chronicle.publish(
                EventType.WORLD_EVENT,
                f"🏆 Война завершена! {winner_name} захватила территорию!",
                importance=Importance.RARE,
            )

            return {"success": True, "winner": new_owner}

    async def get_active_wars(self) -> list:
        async for db in get_db():
            result = await db.execute(
                select(GuildWarModel).where(GuildWarModel.status == "active")
            )
            return [{
                "id": w.id,
                "attacker": w.attacker_guild_id,
                "defender": w.defender_guild_id,
                "location": w.location_id,
                "attacker_wins": w.attacker_wins,
                "defender_wins": w.defender_wins,
                "started_at": w.started_at,
            } for w in result.scalars().all()]

    async def get_war_stats(self) -> dict:
        async for db in get_db():
            total = (await db.execute(text("SELECT COUNT(*) FROM guild_wars"))).scalar() or 0
            active = (await db.execute(text("SELECT COUNT(*) FROM guild_wars WHERE status = 'active'"))).scalar() or 0
            return {"total": total, "active": active}
