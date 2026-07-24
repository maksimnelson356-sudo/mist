import pytest
from services.npc_service import NPCService, NPC_TYPES, RELATION_LEVELS
from services.npc_memory_service import NPCMemoryService, ACTION_DELTAS
from services.npc_scheduler import NPCScheduler, TIME_PERIODS


def test_npc_types():
    assert "merchant" in NPC_TYPES
    assert "quest_giver" in NPC_TYPES
    assert "guard" in NPC_TYPES
    assert "elder" in NPC_TYPES
    assert "bartender" in NPC_TYPES
    assert "healer" in NPC_TYPES
    assert "shady" in NPC_TYPES

    assert NPC_TYPES["merchant"]["can_trade"] is True
    assert NPC_TYPES["healer"]["can_heal"] is True


def test_npc_type_icons():
    for npc_type, info in NPC_TYPES.items():
        assert "icon" in info
        assert len(info["icon"]) > 0
        assert "name" in info


def test_relation_levels():
    assert len(RELATION_LEVELS) == 5

    min_r, max_r, name, desc = RELATION_LEVELS[0]
    assert name == "Враг"
    assert min_r == -100
    assert max_r == -51

    min_r, max_r, name, desc = RELATION_LEVELS[-1]
    assert name == "Доверенный"
    assert min_r == 100
    assert max_r == 100


def test_action_deltas():
    assert ACTION_DELTAS["talked"] == 1
    assert ACTION_DELTAS["traded"] == 2
    assert ACTION_DELTAS["helped"] == 5
    assert ACTION_DELTAS["attacked"] == -10
    assert ACTION_DELTAS["killed_by"] == -20


def test_npc_memory_service_relation_levels():
    svc = NPCMemoryService(None)
    assert svc.get_relation_level(-60) == "Враг"
    assert svc.get_relation_level(-25) == "Подозрительный"
    assert svc.get_relation_level(25) == "Нейтральный"
    assert svc.get_relation_level(75) == "Дружелюбный"
    assert svc.get_relation_level(100) == "Доверенный"


def test_npc_memory_price_multiplier():
    svc = NPCMemoryService(None)
    assert svc.get_price_multiplier(-60) == 2.0
    assert svc.get_price_multiplier(-25) == 1.5
    assert svc.get_price_multiplier(25) == 1.0
    assert svc.get_price_multiplier(75) == 0.8
    assert svc.get_price_multiplier(100) == 0.6


def test_time_periods():
    assert "night" in TIME_PERIODS
    assert "morning" in TIME_PERIODS
    assert "afternoon" in TIME_PERIODS
    assert "evening" in TIME_PERIODS

    for period, (start, end) in TIME_PERIODS.items():
        assert 0 <= start <= 23
        assert 0 <= end <= 23
        assert start <= end


def test_scheduler_get_current_period():
    scheduler = NPCScheduler(None)
    period = scheduler.get_current_period()
    assert period in TIME_PERIODS


def test_npc_model_fields():
    from database.models.npc import NPCModel

    npc = NPCModel(
        npc_id="test_npc",
        name="Test NPC",
        description="A test NPC",
        npc_type="merchant",
        location_str="market_square",
        disposition="neutral",
    )

    assert npc.npc_id == "test_npc"
    assert npc.name == "Test NPC"
    assert npc.npc_type == "merchant"


def test_npc_memory_model_fields():
    from database.models.npc_memory import NPCMemoryModel

    mem = NPCMemoryModel(
        npc_id="npc-001",
        player_id=123,
        relation=10,
        interaction_count=5,
        last_action="talked",
    )

    assert mem.npc_id == "npc-001"
    assert mem.player_id == 123
    assert mem.relation == 10
    assert mem.interaction_count == 5


def test_exploration_model_fields():
    from database.models.exploration import ExplorationModel

    exp = ExplorationModel(
        user_id=123,
        location_id="loc-001",
        first_discovered=True,
        visited_count=3,
    )

    assert exp.user_id == 123
    assert exp.location_id == "loc-001"
    assert exp.first_discovered is True
    assert exp.visited_count == 3
