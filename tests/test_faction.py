import pytest
from unittest.mock import AsyncMock, MagicMock

from services.faction_service import FactionService


class MockChronicle:
    async def publish(self, *a, **kw):
        pass


def test_faction_service_init():
    svc = FactionService(MockChronicle(), MagicMock())
    assert svc is not None


def test_faction_service_has_join_faction():
    svc = FactionService(MockChronicle(), MagicMock())
    assert hasattr(svc, 'join_faction')


def test_faction_service_has_leave_faction():
    svc = FactionService(MockChronicle(), MagicMock())
    assert hasattr(svc, 'leave_faction')


def test_faction_service_has_get_faction_info():
    svc = FactionService(MockChronicle(), MagicMock())
    assert hasattr(svc, 'get_faction_info')


def test_faction_service_has_get_player_factions():
    svc = FactionService(MockChronicle(), MagicMock())
    assert hasattr(svc, 'get_player_factions')


def test_faction_service_has_get_all_factions():
    svc = FactionService(MockChronicle(), MagicMock())
    assert hasattr(svc, 'get_all_factions')


def test_faction_service_has_add_reputation():
    svc = FactionService(MockChronicle(), MagicMock())
    assert hasattr(svc, 'add_reputation')


def test_faction_methods_are_async():
    import inspect
    svc = FactionService(MockChronicle(), MagicMock())
    for method in ['join_faction', 'leave_faction', 'get_faction_info', 'get_player_factions', 'get_all_factions', 'add_reputation']:
        assert inspect.iscoroutinefunction(getattr(svc, method)), f"{method} should be async"