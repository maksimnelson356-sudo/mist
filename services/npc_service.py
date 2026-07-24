from sqlalchemy import select
from sqlalchemy.sql import func

from database.base import get_db
from database.models.npc import NPCModel
from domain.events import EventType, Importance


NPC_TYPES = {
    "merchant": {"name": "Торговец", "icon": "🛒", "can_trade": True},
    "quest_giver": {"name": "Квестодатель", "icon": "📜", "can_give_quests": True},
    "guard": {"name": "Стражник", "icon": "⚔️", "can_fight": True},
    "elder": {"name": "Старейшина", "icon": "👴", "has_lore": True},
    "bartender": {"name": "Кабатчик", "icon": "🍺", "has_rumors": True},
    "healer": {"name": "Целитель", "icon": "💚", "can_heal": True},
    "shady": {"name": "Тёмный тип", "icon": "🕵️", "has_secrets": True},
}

RELATION_LEVELS = [
    (-100, -51, "Враг", "Не торгует, атакует"),
    (-50, -1, "Подозрительный", "Дорогие цены"),
    (0, 49, "Нейтральный", "Базовые цены"),
    (50, 99, "Дружелюбный", "Скидки, подсказки"),
    (100, 100, "Доверенный", "Уникальные квесты"),
]


class NPCService:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def get(self, npc_id: str) -> dict | None:
        async for db in get_db():
            stmt = select(NPCModel).where(NPCModel.npc_id == npc_id)
            result = await db.execute(stmt)
            npc = result.scalar_one_or_none()
            return self._to_dict(npc) if npc else None
        return None

    async def get_at_location(self, location_str: str) -> list:
        async for db in get_db():
            stmt = select(NPCModel).where(
                NPCModel.location_str == location_str,
                NPCModel.is_alive == True,
            )
            result = await db.execute(stmt)
            npcs = result.scalars().all()
            return [self._to_dict(n) for n in npcs]
        return []

    async def interact(self, user_id: int, npc_id: str) -> dict:
        npc = await self.get(npc_id)
        if not npc:
            return {"success": False, "message": "NPC не найден."}

        if not npc["is_alive"]:
            return {"success": False, "message": "Этот NPC мёртв."}

        npc_type = NPC_TYPES.get(npc["npc_type"], {})
        state = npc.get("state", "idle")

        dialogue = npc.get("dialogue_tree", {})
        state_dialogue = dialogue.get(state, dialogue.get("default", {}))

        greeting = state_dialogue.get("greeting", f"«{npc['name']} смотрит на тебя.»")

        await self.chronicle.publish(
            EventType.NPC_TALKED,
            f"Взаимодействие с {npc['name']}: {npc['npc_type']}",
            player_id=user_id,
            importance=Importance.TRIVIAL,
        )

        return {
            "success": True,
            "npc_id": npc_id,
            "name": npc["name"],
            "type": npc_type.get("name", npc["npc_type"]),
            "icon": npc_type.get("icon", "❓"),
            "state": state,
            "message": greeting,
            "can_trade": npc_type.get("can_trade", False),
            "can_give_quests": npc_type.get("can_give_quests", False),
            "can_heal": npc_type.get("can_heal", False),
        }

    async def get_dialogue(self, npc_id: str, state: str = None) -> dict:
        npc = await self.get(npc_id)
        if not npc:
            return {}

        dialogue = npc.get("dialogue_tree", {})
        if state:
            return dialogue.get(state, dialogue.get("default", {}))
        return dialogue

    async def update_state(self, npc_id: str, state: str):
        async for db in get_db():
            from sqlalchemy import update
            stmt = update(NPCModel).where(NPCModel.npc_id == npc_id).values(state=state)
            await db.execute(stmt)
            await db.commit()
            break

    def get_npc_type_info(self, npc_type: str) -> dict:
        return NPC_TYPES.get(npc_type, {"name": "Неизвестный", "icon": "❓"})

    def get_relation_level(self, relation: int) -> str:
        for min_r, max_r, name, _ in RELATION_LEVELS:
            if min_r <= relation <= max_r:
                return name
        return "Нейтральный"

    @staticmethod
    def _to_dict(row: NPCModel) -> dict:
        return {
            "id": row.id,
            "npc_id": row.npc_id,
            "name": row.name,
            "description": row.description,
            "npc_type": row.npc_type,
            "state": row.state,
            "location_id": row.location_id,
            "location_str": row.location_str,
            "disposition": row.disposition,
            "schedule": row.schedule if isinstance(row.schedule, dict) else {},
            "dialogue_tree": row.dialogue_tree if isinstance(row.dialogue_tree, dict) else {},
            "is_alive": row.is_alive,
        }
