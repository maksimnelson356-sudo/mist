import logging
from sqlalchemy import select, update, text

from database.base import get_db
from database.models.guild import GuildModel, GuildMemberModel
from database.models.location import LocationModel

logger = logging.getLogger("MIST.guild_territory")


TERRITORY_INCOME_PER_DAY = 10


class GuildTerritoryService:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def claim_territory(self, guild_id: str, location_id: str) -> dict:
        async for db in get_db():
            result = await db.execute(
                select(GuildModel).where(GuildModel.guild_id == guild_id)
            )
            guild = result.scalar_one_or_none()
            if not guild:
                return {"success": False, "message": "Гильдия не найдена."}

            result = await db.execute(
                select(LocationModel).where(LocationModel.id == location_id)
            )
            location = result.scalar_one_or_none()
            if not location:
                return {"success": False, "message": "Локация не найдена."}

            current_owner = getattr(location, "owner_guild_id", None)
            if current_owner == guild_id:
                return {"success": False, "message": "Эта локация уже ваша."}

            new_danger = max(0, location.danger_level - 15)
            await db.execute(
                update(LocationModel)
                .where(LocationModel.id == location_id)
                .values(danger_level=new_danger, owner_guild_id=guild_id)
            )

            result = await db.execute(
                select(GuildMemberModel).where(GuildMemberModel.guild_id == guild_id)
            )
            members = result.scalars().all()
            for member in members:
                await db.execute(
                    update(GuildMemberModel)
                    .where(GuildMemberModel.id == member.id)
                    .values(contribution=member.contribution + 10)
                )

            await db.commit()

            location_name = getattr(location, "name", location_id)
            logger.info(f"Гильдия {guild_id} захватила {location_name}")
            return {
                "success": True,
                "message": f"Гильдия «{guild.name}» захватила «{location_name}»!",
                "danger_reduction": 15,
            }

    async def get_guild_territories(self, guild_id: str) -> list:
        async for db in get_db():
            result = await db.execute(
                text("SELECT id, name, danger_level FROM locations WHERE owner_guild_id = :gid"),
                {"gid": guild_id},
            )
            return [dict(row) for row in result.mappings().all()]

    async def get_location_owner(self, location_id: str) -> dict | None:
        async for db in get_db():
            result = await db.execute(
                text("SELECT owner_guild_id FROM locations WHERE id = :lid"),
                {"lid": location_id},
            )
            row = result.mappings().first()
            if not row or not row.get("owner_guild_id"):
                return None

            gid = row["owner_guild_id"]
            result = await db.execute(
                select(GuildModel).where(GuildModel.guild_id == gid)
            )
            guild = result.scalar_one_or_none()
            if guild:
                return {"guild_id": gid, "name": guild.name}
            return None

    async def recalculate_territory_bonus(self):
        async for db in get_db():
            result = await db.execute(
                text("SELECT id, owner_guild_id, danger_level FROM locations WHERE owner_guild_id IS NOT NULL")
            )
            territories = result.mappings().all()

            for t in territories:
                result = await db.execute(
                    text("SELECT COUNT(*) FROM guild_members WHERE guild_id = :gid"),
                    {"gid": t["owner_guild_id"]},
                )
                member_count = result.scalar() or 0

                bonus = min(20, member_count * 2)
                new_danger = max(0, t["danger_level"] - bonus)
                if new_danger != t["danger_level"]:
                    await db.execute(
                        update(LocationModel)
                        .where(LocationModel.id == t["id"])
                        .values(danger_level=new_danger)
                    )

            await db.commit()

    async def tick_territory_income(self):
        async for db in get_db():
            result = await db.execute(
                text("SELECT id, owner_guild_id FROM locations WHERE owner_guild_id IS NOT NULL")
            )
            territories = result.mappings().all()

            guild_income = {}
            for t in territories:
                gid = t["owner_guild_id"]
                guild_income[gid] = guild_income.get(gid, 0) + TERRITORY_INCOME_PER_DAY

            for gid, income in guild_income.items():
                result = await db.execute(
                    select(GuildModel).where(GuildModel.guild_id == gid)
                )
                guild = result.scalar_one_or_none()
                if guild:
                    new_gold = (guild.gold or 0) + income
                    await db.execute(
                        update(GuildModel).where(GuildModel.guild_id == gid).values(gold=new_gold)
                    )

            await db.commit()

    async def contest_territory(self, challenger_guild_id: str, location_id: str) -> dict:
        async for db in get_db():
            result = await db.execute(
                select(LocationModel).where(LocationModel.id == location_id)
            )
            location = result.scalar_one_or_none()
            if not location:
                return {"success": False, "message": "Локация не найдена."}

            current_owner = getattr(location, "owner_guild_id", None)
            if not current_owner:
                return {"success": False, "message": "Эта территория ничья. Захвати её бесплатно."}

            if current_owner == challenger_guild_id:
                return {"success": False, "message": "Это уже твоя территория."}

            result = await db.execute(
                select(GuildMemberModel).where(GuildMemberModel.guild_id == challenger_guild_id)
            )
            challengers = result.scalars().all()
            result = await db.execute(
                select(GuildMemberModel).where(GuildMemberModel.guild_id == current_owner)
            )
            defenders = result.scalars().all()

            challenger_power = sum(getattr(m, "contribution", 0) for m in challengers) + len(challengers) * 10
            defender_power = sum(getattr(m, "contribution", 0) for m in defenders) + len(defenders) * 10

            if defender_power > 0:
                win_chance = min(0.8, max(0.2, challenger_power / (challenger_power + defender_power)))
            else:
                win_chance = 1.0

            import random
            won = random.random() < win_chance

            if won:
                await db.execute(
                    update(LocationModel)
                    .where(LocationModel.id == location_id)
                    .values(danger_level=max(0, location.danger_level - 10), owner_guild_id=challenger_guild_id)
                )
                for m in challengers:
                    await db.execute(
                        update(GuildMemberModel)
                        .where(GuildMemberModel.id == m.id)
                        .values(contribution=m.contribution + 20)
                    )
                await db.commit()

                challenger_result = await db.execute(
                    select(GuildModel).where(GuildModel.guild_id == challenger_guild_id)
                )
                challenger_guild = challenger_result.scalar_one_or_none()
                location_name = getattr(location, "name", location_id)

                return {
                    "success": True,
                    "message": f"⚔️ «{challenger_guild.name if challenger_guild else challenger_guild_id}» захватил «{location_name}»!",
                    "won": True,
                }
            else:
                for m in challengers:
                    await db.execute(
                        update(GuildMemberModel)
                        .where(GuildMemberModel.id == m.id)
                        .values(contribution=max(0, m.contribution - 5))
                    )
                await db.commit()

                return {
                    "success": True,
                    "message": "⚔️ Попытка захвата провалилась. Территория осталась за прежним владельцем.",
                    "won": False,
                }
