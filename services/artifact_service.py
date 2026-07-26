import logging

from sqlalchemy import select, text, update

from database.base import get_db
from database.models.artifact import ArtifactModel
from domain.events import EventType, Importance

logger = logging.getLogger("MIST.artifact")

ARTIFACT_DEFS = [
    {
        "artifact_id": "blade_of_the_fallen_king",
        "name": "Клинок павшего короля",
        "description": "Клинок, которым был убит последний король Туманных земель.",
        "lore": "Клинок был выкован в горниле Сердца MIST. Первый удар принёс смерть. Второй — забвение.",
        "rarity": "legendary", "artifact_type": "weapon",
        "stats": {"attack": 15, "crit_chance": 0.2},
        "curse": "Привлекает нежить. Владелец видит кошмары.",
        "blessing": "+15 к атаке. Шанс критического удара 20%.",
    },
    {
        "artifact_id": "shield_of_echoes",
        "name": "Щит эхов",
        "description": "Щит, который отражает не только удары, но и воспоминания.",
        "lore": "Щит был создан из осколков зеркала Библиотеки эхов. Он помнит каждого, кто его нёс.",
        "rarity": "epic", "artifact_type": "shield",
        "stats": {"defense": 12, "magic_defense": 8},
        "curse": "Показывает прошлые ошибки владельца.",
        "blessing": "+12 к защите. +% к магической защите.",
    },
    {
        "artifact_id": "amulet_of_tides",
        "name": "Амулет приливов",
        "description": "Амулет, который контролирует воду. Или вод контролирует его?",
        "lore": "Найден в Затонувшем троне. Говорят, он принадлежал королю моря.",
        "rarity": "rare", "artifact_type": "amulet",
        "stats": {"magic_level": 10, "food_supply": 5},
        "curse": "Привлекает кракенов.",
        "blessing": "+10 к магии. Увеличивает улов рыбы.",
    },
    {
        "artifact_id": "crown_of_thorns",
        "name": "Корона шипов",
        "description": "Корона, которая растёт вместе с носителем. И боль тоже.",
        "lore": "Корона была найдена на голове мёртвого короля. Шипы вросли в череп.",
        "rarity": "legendary", "artifact_type": "head",
        "stats": {"level": 5, "max_hp": -20},
        "curse": " -20 к максимальному HP. Боль усиливается.",
        "blessing": "+5 к уровню. Шипы защищают от критических ударов.",
    },
    {
        "artifact_id": "ring_of_whispers",
        "name": "Кольцо шёпотов",
        "description": "Кольцо, которое шепчет на языке мёртвых.",
        "lore": "Кольцо было выточено из пальца скелета в Забытом кладбище. Оно до сих пор шепчет.",
        "rarity": "rare", "artifact_type": "ring",
        "stats": {"magic_level": 8, "danger_sense": True},
        "curse": "Шёпоты не прекращаются. Иногда — правдивые.",
        "blessing": "+8 к магии. Чувствует опасность.",
    },
    {
        "artifact_id": "boots_of_wanderer",
        "name": "Сапоги странника",
        "description": "Сапоги, которые всегда знают дорогу. Даже когда её нет.",
        "lore": "Сапоги были найдены на обочине дороги, которая вела в никуда. Но сапоги вели дальше.",
        "rarity": "uncommon", "artifact_type": "boots",
        "stats": {"speed": 2, "exploration_bonus": 0.1},
        "curse": "Владелец не может остановиться. Всегда идёт.",
        "blessing": "+2 к скорости. +% к исследованию.",
    },
    {
        "artifact_id": "gauntlet_of_flames",
        "name": "Рукавица пламени",
        "description": "Рукавица, которая горит, но не обжигает. Обжигает всё вокруг.",
        "lore": "Рукавица была найдена в пепле лесного пожара. Она всё ещё тёплая.",
        "rarity": "epic", "artifact_type": "gloves",
        "stats": {"attack": 10, "fire_damage": 15},
        "curse": "Поджигает предметы в инвентаре.",
        "blessing": "+10 к атаке. Огненный урон 15.",
    },
    {
        "artifact_id": "compass_of_lost_souls",
        "name": "Компас потерянных душ",
        "description": "Компас, который показывает не север, а то, чего ты хочешь.",
        "lore": "Компас был создан из компаса, который потерял дорогу. Теперь он ищет других потерянных.",
        "rarity": "rare", "artifact_type": "tool",
        "stats": {"quest_detection": True, "danger_sense": True},
        "curse": "Показывает не то, чего ты хочешь, а то, чего ты боишься.",
        "blessing": "Показывает ближайший квест. Чувствует опасность.",
    },
]


class ArtifactService:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def create_artifact(self, artifact_id: str, **kwargs) -> dict:
        async for db in get_db():
            artifact = ArtifactModel(artifact_id=artifact_id, **kwargs)
            db.add(artifact)
            await db.commit()
            return self._to_dict(artifact)
        return {}

    async def get(self, artifact_id: str) -> dict | None:
        async for db in get_db():
            stmt = select(ArtifactModel).where(ArtifactModel.artifact_id == artifact_id)
            result = await db.execute(stmt)
            artifact = result.scalar_one_or_none()
            return self._to_dict(artifact) if artifact else None
        return None

    async def get_by_owner(self, owner_id: int) -> list:
        async for db in get_db():
            stmt = select(ArtifactModel).where(ArtifactModel.owner_id == owner_id, ArtifactModel.is_active == True)
            result = await db.execute(stmt)
            return [self._to_dict(a) for a in result.scalars().all()]
        return []

    async def use_artifact(self, artifact_id: str, user_id: int, action: str = "use") -> dict:
        artifact = await self.get(artifact_id)
        if not artifact:
            return {"success": False, "message": "Артефакт не найден."}

        async for db in get_db():
            new_count = artifact["times_used"] + 1
            new_kills = artifact["kills_with"] + (1 if action == "kill" else 0)
            new_saves = artifact["saves_with"] + (1 if action == "save" else 0)

            events = artifact.get("events_witnessed", [])
            if action not in events:
                events.append(action)

            new_lore = self._evolve_lore(artifact, new_count, new_kills, new_saves, action)

            await db.execute(
                update(ArtifactModel)
                .where(ArtifactModel.artifact_id == artifact_id)
                .values(
                    times_used=new_count,
                    kills_with=new_kills,
                    saves_with=new_saves,
                    events_witnessed=events,
                    lore=new_lore,
                )
            )
            await db.commit()

            return {
                "success": True,
                "times_used": new_count,
                "new_lore": new_lore,
            }

    async def discover_artifact(self, artifact_id: str, user_id: int, location_id: str) -> dict:
        artifact_def = None
        for ad in ARTIFACT_DEFS:
            if ad["artifact_id"] == artifact_id:
                artifact_def = ad
                break

        if not artifact_def:
            return {"success": False, "message": "Артефакт не найден."}

        existing = await self.get(artifact_id)
        if existing:
            return {"success": False, "message": "Артефакт уже найден."}

        async for db in get_db():
            from datetime import datetime
            artifact = ArtifactModel(
                artifact_id=artifact_id,
                name=artifact_def["name"],
                description=artifact_def["description"],
                lore=artifact_def["lore"],
                rarity=artifact_def["rarity"],
                artifact_type=artifact_def["artifact_type"],
                owner_id=user_id,
                location_found=location_id,
                stats=artifact_def.get("stats", {}),
                curse=artifact_def.get("curse"),
                blessing=artifact_def.get("blessing"),
                found_at=datetime.utcnow(),
            )
            db.add(artifact)
            await db.commit()

            await self.chronicle.publish(
                EventType.LEGEND_DISCOVERED,
                f"🏺 Найден артефакт: {artifact_def['name']}",
                player_id=user_id,
                importance=Importance.RARE,
            )

            return self._to_dict(artifact)

    def _evolve_lore(self, artifact: dict, times_used: int, kills: int, saves: int, action: str) -> str:
        base_lore = artifact.get("lore", "")

        additions = []
        if times_used == 1:
            additions.append("Впервые использован.")
        if kills == 1:
            additions.append("Впервые пролита кровь.")
        if kills >= 10:
            additions.append(f"Клинок жаждет крови. Убийств: {kills}.")
        if saves >= 5:
            additions.append(f"Щит спас {saves} жизней.")
        if times_used >= 20:
            additions.append("Артефакт начинает менять владельца.")
        if times_used >= 50:
            additions.append("Артефакт стал частью владельца.")

        if additions:
            return base_lore + " " + " ".join(additions)
        return base_lore

    async def get_all_artifacts(self) -> list:
        async for db in get_db():
            result = await db.execute(
                select(ArtifactModel).where(ArtifactModel.is_active == True)
            )
            return [self._to_dict(a) for a in result.scalars().all()]
        return []

    async def get_artifact_stats(self) -> dict:
        async for db in get_db():
            total = (await db.execute(text("SELECT COUNT(*) FROM artifacts"))).scalar() or 0
            active = (await db.execute(text("SELECT COUNT(*) FROM artifacts WHERE is_active = 1"))).scalar() or 0
            found = (await db.execute(text("SELECT COUNT(*) FROM artifacts WHERE found_at IS NOT NULL"))).scalar() or 0
            return {"total": total, "active": active, "found": found}

    @staticmethod
    def _to_dict(row: ArtifactModel) -> dict:
        return {
            "id": row.id,
            "artifact_id": row.artifact_id,
            "name": row.name,
            "description": row.description,
            "lore": row.lore,
            "rarity": row.rarity,
            "artifact_type": row.artifact_type,
            "owner_id": row.owner_id,
            "location_found": row.location_found,
            "times_used": row.times_used,
            "kills_with": row.kills_with,
            "saves_with": row.saves_with,
            "events_witnessed": row.events_witnessed,
            "found_at": row.found_at,
            "is_active": row.is_active,
            "stats": row.stats,
            "curse": row.curse,
            "blessing": row.blessing,
        }
