import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.achievement_service import AchievementService, ACHIEVEMENT_DEFS


class MockChronicle:
    async def publish(self, *a, **kw):
        pass


def test_achievement_service_init():
    svc = AchievementService(MockChronicle(), MagicMock())
    assert svc is not None


def test_get_all_definitions_returns_list():
    svc = AchievementService(MockChronicle(), MagicMock())
    import asyncio
    defs = asyncio.run(svc.get_all_definitions())
    assert isinstance(defs, list)
    assert len(defs) == len(ACHIEVEMENT_DEFS)


def test_achievement_definitions_have_required_fields():
    svc = AchievementService(MockChronicle(), MagicMock())
    import asyncio
    defs = asyncio.run(svc.get_all_definitions())
    for defn in defs:
        assert "name" in defn
        assert "description" in defn
        assert "icon" in defn
        assert "category" in defn
        assert "achievement_id" in defn


def test_achievement_categories():
    svc = AchievementService(MockChronicle(), MagicMock())
    import asyncio
    defs = asyncio.run(svc.get_all_definitions())
    categories = set(d["category"] for d in defs)
    assert len(categories) > 0


def test_on_kill_method_exists():
    svc = AchievementService(MockChronicle(), MagicMock())
    assert hasattr(svc, 'on_kill')


def test_on_level_up_method_exists():
    svc = AchievementService(MockChronicle(), MagicMock())
    assert hasattr(svc, 'on_level_up')


def test_on_quest_completed_method_exists():
    svc = AchievementService(MockChronicle(), MagicMock())
    assert hasattr(svc, 'on_quest_completed')


def test_on_gold_changed_method_exists():
    svc = AchievementService(MockChronicle(), MagicMock())
    assert hasattr(svc, 'on_gold_changed')


def test_achievement_defs_constant_is_list():
    assert isinstance(ACHIEVEMENT_DEFS, list)
    assert len(ACHIEVEMENT_DEFS) > 0
    for defn in ACHIEVEMENT_DEFS:
        assert isinstance(defn["achievement_id"], str)
        assert isinstance(defn["name"], str)
        assert isinstance(defn["description"], str)