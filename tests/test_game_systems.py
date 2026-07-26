import pytest

from services.catalog_service import RARITY_NAMES, RARITY_WEIGHTS, CatalogService
from services.quest_engine import QUEST_STATUS, QUEST_TYPES, QuestEngine
from services.time_system import TIME_PERIODS, TimeSystem
from services.weather_system import WEATHER_EFFECTS, WEATHER_STATES


def test_rarity_weights():
    assert RARITY_WEIGHTS["common"] == 1.0
    assert RARITY_WEIGHTS["uncommon"] == 1.5
    assert RARITY_WEIGHTS["rare"] == 2.5
    assert RARITY_WEIGHTS["epic"] == 4.0
    assert RARITY_WEIGHTS["legendary"] == 8.0


def test_rarity_names():
    assert RARITY_NAMES["common"] == "Обычный"
    assert RARITY_NAMES["legendary"] == "Легендарный"


def test_catalog_service_value():
    svc = CatalogService(None)
    item = {"item_id": "test", "name": "Test", "rarity": "rare", "base_value": 100}
    assert svc.get_item_value(item, 1) == 250
    assert svc.get_item_value(item, 2) == 500


def test_weather_states():
    assert len(WEATHER_STATES) == 5
    assert "clear" in WEATHER_STATES
    assert "rain" in WEATHER_STATES
    assert "storm" in WEATHER_STATES
    assert "fog" in WEATHER_STATES
    assert "snow" in WEATHER_STATES


def test_weather_effects():
    for state in WEATHER_STATES:
        assert state in WEATHER_EFFECTS
        assert "xp_bonus" in WEATHER_EFFECTS[state]
        assert "movement_penalty" in WEATHER_EFFECTS[state]


def test_time_periods():
    assert len(TIME_PERIODS) == 4
    assert "morning" in TIME_PERIODS
    assert "afternoon" in TIME_PERIODS
    assert "evening" in TIME_PERIODS
    assert "night" in TIME_PERIODS

    for period, info in TIME_PERIODS.items():
        assert "name" in info
        assert "icon" in info
        assert "hours" in info


def test_time_system():
    svc = TimeSystem(None)
    t = svc.get_current_time()
    assert "day" in t
    assert "hour" in t
    assert "minute" in t
    assert "period" in t
    assert "display" in t


def test_time_system_set():
    svc = TimeSystem(None)
    svc.set_time(day=5, hour=14, minute=30)
    t = svc.get_current_time()
    assert t["day"] == 5
    assert t["hour"] == 14
    assert t["minute"] == 30


def test_time_system_day_of_week():
    svc = TimeSystem(None)
    svc.set_time(day=1)
    assert svc.get_day_of_week() == "Понедельник"

    svc.set_time(day=7)
    assert svc.get_day_of_week() == "Воскресенье"

    svc.set_time(day=8)
    assert svc.get_day_of_week() == "Понедельник"


def test_quest_types():
    assert len(QUEST_TYPES) == 6
    assert "kill" in QUEST_TYPES
    assert "collect" in QUEST_TYPES
    assert "explore" in QUEST_TYPES
    assert "talk" in QUEST_TYPES


def test_quest_status():
    assert len(QUEST_STATUS) == 4
    assert "active" in QUEST_STATUS
    assert "completed" in QUEST_STATUS
    assert "failed" in QUEST_STATUS


def test_item_template_model_weight():
    from database.models.item import ItemTemplateModel
    item = ItemTemplateModel(item_id="test", name="Test", weight=2.5)
    assert item.weight == 2.5
