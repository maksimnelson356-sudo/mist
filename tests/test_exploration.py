import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.exploration_service import ExplorationService


class MockChronicle:
    async def publish(self, *a, **kw):
        pass


def test_exploration_service_init():
    svc = ExplorationService(MockChronicle(), MagicMock())
    assert svc is not None


def test_exploration_service_has_discover():
    svc = ExplorationService(MockChronicle(), MagicMock())
    assert hasattr(svc, 'discover')


def test_exploration_service_has_visit():
    svc = ExplorationService(MockChronicle(), MagicMock())
    assert hasattr(svc, 'visit')


def test_exploration_service_has_get_discoveries():
    svc = ExplorationService(MockChronicle(), MagicMock())
    assert hasattr(svc, 'get_discoveries')


def test_exploration_service_has_get_discovery_list():
    svc = ExplorationService(MockChronicle(), MagicMock())
    assert hasattr(svc, 'get_discovery_list')


def test_exploration_service_has_get_stats():
    svc = ExplorationService(MockChronicle(), MagicMock())
    assert hasattr(svc, 'get_stats')


def test_exploration_methods_are_async():
    import inspect
    svc = ExplorationService(MockChronicle(), MagicMock())
    for method in ['discover', 'visit', 'get_discoveries', 'get_discovery_list', 'get_stats']:
        assert inspect.iscoroutinefunction(getattr(svc, method)), f"{method} should be async"


def test_exploration_discover_returns_dict():
    svc = ExplorationService(MockChronicle(), AsyncMock(get=AsyncMock(return_value={})))
    session = MagicMock()
    session.commit = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: None))

    async def fake_get_db():
        yield session

    with patch("services.exploration_service.get_db", side_effect=lambda: fake_get_db()):
        import asyncio
        result = asyncio.run(svc.discover(123, "test_location"))

    assert isinstance(result, dict)