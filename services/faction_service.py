import logging

from sqlalchemy import select, update

from database.base import get_db
from database.models.faction import PlayerFactionModel
from domain.events import EventType, Importance

logger = logging.getLogger("MIST.faction")

FACTIONS = {
    "order_of_mist": {
        "name": "Орден Тумана",
        "icon": "🌫️",
        "description": "Древний орден, хранящий тайны тумана. Они верят, что туман — дыхание мира.",
        "location_id": "heart_of_mist",
        "ranks": ["novice", "acolyte", "priest", "high_priest", "grandmaster"],
        "bonuses": {"magic_level": 5, "quest_detection": True},
    },
    "shadow_clan": {
        "name": "Теневой Клан",
        "icon": "🕵️",
        "description": "Торговцы тенями. Они знают цену всему — даже душе.",
        "location_id": "shadow_market",
        "ranks": ["initiate", "agent", "broker", "shadow_lord", "shadow_king"],
        "bonuses": {"gold_bonus": 0.1, "trade_bonus": True},
    },
    "ancient_council": {
        "name": "Древний Совет",
        "icon": "📜",
        "description": "Хранители знаний. Их библиотека хранит забытые миры.",
        "location_id": "library_of_echoes",
        "ranks": ["scholar", "archivist", "sage", "elder", "oracle"],
        "bonuses": {"xp_bonus": 0.1, "lore_detection": True},
    },
    "free_wanderers": {
        "name": "Свободные",
        "icon": "🏹",
        "description": "Странники без клятв. Они идут туда, куда ведёт туман.",
        "location_id": "abandoned_camp",
        "ranks": ["wanderer", "pathfinder", "ranger", "wayfarer", "legend"],
        "bonuses": {"exploration_bonus": 0.15, "survival_bonus": True},
    },
}

FACTION_REPUTATION = {
    -100: {"rank": "враг", "description": "Враг фракции"},
    -50: {"rank": "враждебный", "description": "Враждебное отношение"},
    0: {"rank": "нейтральный", "description": "Нейтральное отношение"},
    25: {"rank": "дружелюбный", "description": "Дружелюбное отношение"},
    50: {"rank": "уважаемый", "description": "Уважаемый член"},
    75: {"rank": "доверенный", "description": "Доверенное лицо"},
    100: {"rank": "легенда", "description": "Легенда фракции"},
}


class FactionService:

    def __init__(self, chronicle, player):
        self.chronicle = chronicle
        self.player = player

    async def get_all_factions(self) -> list:
        return [{
            "id": fid,
            "name": f["name"],
            "icon": f["icon"],
            "description": f["description"],
            "location": f["location_id"],
        } for fid, f in FACTIONS.items()]

    async def get_player_factions(self, user_id: int) -> list:
        async for db in get_db():
            result = await db.execute(
                select(PlayerFactionModel).where(
                    PlayerFactionModel.user_id == user_id,
                    PlayerFactionModel.is_active == True,
                )
            )
            factions = result.scalars().all()
            return [{
                "faction_id": pf.faction_id,
                "reputation": pf.reputation,
                "rank": pf.rank,
                "joined_at": pf.joined_at,
            } for pf in factions]
        return []

    async def join_faction(self, user_id: int, faction_id: str) -> dict:
        if faction_id not in FACTIONS:
            return {"success": False, "message": "Фракция не найдена."}

        async for db in get_db():
            existing = await db.execute(
                select(PlayerFactionModel).where(
                    PlayerFactionModel.user_id == user_id,
                    PlayerFactionModel.faction_id == faction_id,
                    PlayerFactionModel.is_active == True,
                )
            )
            if existing.scalar_one_or_none():
                return {"success": False, "message": "Ты уже в этой фракции."}

            faction = FACTIONS[faction_id]
            pf = PlayerFactionModel(
                user_id=user_id,
                faction_id=faction_id,
                reputation=0,
                rank=faction["ranks"][0],
            )
            db.add(pf)
            await db.commit()

            await self.chronicle.publish(
                EventType.WORLD_EVENT,
                f"Ты вступил в {faction['name']}",
                player_id=user_id,
                importance=Importance.COMMON,
            )

            return {"success": True, "message": f"Добро пожаловать в {faction['name']}!"}

    async def leave_faction(self, user_id: int, faction_id: str) -> dict:
        async for db in get_db():
            result = await db.execute(
                select(PlayerFactionModel).where(
                    PlayerFactionModel.user_id == user_id,
                    PlayerFactionModel.faction_id == faction_id,
                    PlayerFactionModel.is_active == True,
                )
            )
            pf = result.scalar_one_or_none()
            if not pf:
                return {"success": False, "message": "Ты не в этой фракции."}

            await db.execute(
                update(PlayerFactionModel)
                .where(PlayerFactionModel.id == pf.id)
                .values(is_active=False)
            )
            await db.commit()

            faction = FACTIONS.get(faction_id, {})
            return {"success": True, "message": f"Ты покинул {faction.get('name', faction_id)}."}

    async def add_reputation(self, user_id: int, faction_id: int, amount: int) -> dict:
        async for db in get_db():
            result = await db.execute(
                select(PlayerFactionModel).where(
                    PlayerFactionModel.user_id == user_id,
                    PlayerFactionModel.faction_id == faction_id,
                    PlayerFactionModel.is_active == True,
                )
            )
            pf = result.scalar_one_or_none()
            if not pf:
                return {"success": False, "message": "Ты не в этой фракции."}

            new_rep = max(-100, min(100, pf.reputation + amount))
            new_rank = self._get_rank(new_rep)

            await db.execute(
                update(PlayerFactionModel)
                .where(PlayerFactionModel.id == pf.id)
                .values(reputation=new_rep, rank=new_rank)
            )
            await db.commit()

            return {"success": True, "new_reputation": new_rep, "new_rank": new_rank}

    def _get_rank(self, reputation: int) -> str:
        rank = "novice"
        for min_rep, info in sorted(FACTION_REPUTATION.items()):
            if reputation >= min_rep:
                rank = info["rank"]
        return rank

    async def get_faction_info(self, faction_id: str) -> dict | None:
        faction = FACTIONS.get(faction_id)
        if not faction:
            return None

        async for db in get_db():
            result = await db.execute(
                select(PlayerFactionModel).where(
                    PlayerFactionModel.faction_id == faction_id,
                    PlayerFactionModel.is_active == True,
                )
            )
            members = result.scalars().all()
            return {
                "id": faction_id,
                "name": faction["name"],
                "icon": faction["icon"],
                "description": faction["description"],
                "location": faction["location_id"],
                "member_count": len(members),
                "ranks": faction["ranks"],
                "bonuses": faction["bonuses"],
            }
