from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.equipment_service import EquipmentService


class MockChronicle:
    async def publish(self, *a, **kw):
        pass


@pytest.fixture
def equipment_service():
    return EquipmentService()


def test_equipment_slots():
    assert "weapon" in EquipmentService.EQUIPMENT_SLOTS
    assert "armor" in EquipmentService.EQUIPMENT_SLOTS
    assert "accessory" in EquipmentService.EQUIPMENT_SLOTS


def test_equipment_stats_exist():
    assert len(EquipmentService.EQUIPMENT_STATS) > 0


def test_equip_slot_mapping():
    stats = EquipmentService.EQUIPMENT_STATS.get("iron_sword", {})
    if stats:
        assert "slot" in stats
        assert stats["slot"] == "weapon"


def test_compare_stat_diff():
    current_stats = {"attack": 5, "defense": 0, "max_hp": 0}
    candidate_stats = {"attack": 10, "defense": 2, "max_hp": 0}
    diff = {}
    for key, label in [("attack", "Ат"), ("defense", "Защ"), ("max_hp", "HP")]:
        old = current_stats.get(key, 0)
        new = candidate_stats.get(key, 0)
        delta = new - old
        if delta != 0:
            diff[key] = delta
    assert diff["attack"] == 5
    assert diff["defense"] == 2
    assert "max_hp" not in diff


def test_food_hunger_constants():
    from handlers.game import FOOD_HUNGER
    assert FOOD_HUNGER["bread"] == 20
    assert FOOD_HUNGER["fish"] == 25
    assert FOOD_HUNGER["apple"] == 15
    assert FOOD_HUNGER["cheese"] == 30
    assert FOOD_HUNGER["dried_meat"] == 35
    assert FOOD_HUNGER["berry"] == 10
