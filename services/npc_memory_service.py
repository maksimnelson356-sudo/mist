from database.base import get_db
from database.repositories.npc_memory_repo import NPCMemoryRepository
from domain.events import EventType, Importance


ACTION_DELTAS = {
    "talked": 1,
    "traded": 2,
    "helped": 5,
    "gifted": 3,
    "attacked": -10,
    "killed_by": -20,
    "ignored": -1,
    "quest_completed": 8,
}

RELATION_LEVELS = [
    (-100, -51, "Враг", "Не торгует, атакует"),
    (-50, -1, "Подозрительный", "Дорогие цены"),
    (0, 49, "Нейтральный", "Базовые цены"),
    (50, 99, "Дружелюбный", "Скидки, подсказки"),
    (100, 100, "Доверенный", "Уникальные квесты"),
]


class NPCMemoryService:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def update(self, npc_id: str, player_id: int, action: str) -> dict:
        delta = ACTION_DELTAS.get(action, 0)

        async for db in get_db():
            memory = await NPCMemoryRepository.create_or_update(
                db, npc_id, player_id, action, delta
            )
            break

        if delta != 0:
            await self.chronicle.publish(
                EventType.NPC_TALKED,
                f"Память NPC обновлена: {action} (delta={delta})",
                player_id=player_id,
                importance=Importance.TRIVIAL,
            )

        return memory

    async def get(self, npc_id: str, player_id: int) -> dict:
        async for db in get_db():
            memory = await NPCMemoryRepository.get(db, npc_id, player_id)
            break

        if not memory:
            return {
                "relation": 0,
                "level": "Нейтральный",
                "interaction_count": 0,
                "last_seen": None,
                "last_action": None,
            }

        level = self.get_relation_level(memory.get("relation", 0))
        memory["level"] = level
        return memory

    async def get_relation(self, npc_id: str, player_id: int) -> int:
        async for db in get_db():
            memory = await NPCMemoryRepository.get(db, npc_id, player_id)
            break
        return memory.get("relation", 0) if memory else 0

    async def modify_relation(self, npc_id: str, player_id: int, delta: int) -> dict:
        async for db in get_db():
            memory = await NPCMemoryRepository.modify_relation(db, npc_id, player_id, delta)
            break

        level = self.get_relation_level(memory.get("relation", 0))
        memory["level"] = level
        return memory

    async def get_all_memories(self, npc_id: str) -> list:
        async for db in get_db():
            memories = await NPCMemoryRepository.get_all_for_npc(db, npc_id)
            break

        for m in memories:
            m["level"] = self.get_relation_level(m.get("relation", 0))
        return memories

    async def get_player_npc_relations(self, player_id: int) -> list:
        async for db in get_db():
            memories = await NPCMemoryRepository.get_all_for_player(db, player_id)
            break

        for m in memories:
            m["level"] = self.get_relation_level(m.get("relation", 0))
        return memories

    def get_relation_level(self, relation: int) -> str:
        for min_r, max_r, name, _ in RELATION_LEVELS:
            if min_r <= relation <= max_r:
                return name
        return "Нейтральный"

    def get_price_multiplier(self, relation: int) -> float:
        if relation <= -51:
            return 2.0
        elif relation <= -1:
            return 1.5
        elif relation <= 49:
            return 1.0
        elif relation <= 99:
            return 0.8
        else:
            return 0.6
