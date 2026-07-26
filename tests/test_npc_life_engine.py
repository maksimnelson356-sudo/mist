import pytest
from unittest.mock import AsyncMock, MagicMock

from services.npc_life_engine import NPCLifeEngine


class MockChronicle:
    async def publish(self, *a, **kw):
        pass


def test_npc_life_engine_init():
    svc = NPCLifeEngine(MockChronicle())
    assert svc is not None


def test_npc_life_engine_has_tick():
    svc = NPCLifeEngine(MockChronicle())
    assert hasattr(svc, 'tick')


def test_npc_life_engine_tick_is_async():
    import inspect
    svc = NPCLifeEngine(MockChronicle())
    assert inspect.iscoroutinefunction(svc.tick)


def test_npc_life_engine_has_start_loop():
    svc = NPCLifeEngine(MockChronicle())
    assert hasattr(svc, 'start_loop')


def test_npc_life_engine_has_stop():
    svc = NPCLifeEngine(MockChronicle())
    assert hasattr(svc, 'stop')


def test_npc_life_engine_has_get_relationship():
    svc = NPCLifeEngine(MockChronicle())
    assert hasattr(svc, 'get_relationship')


def test_npc_life_engine_has_get_npc_relationships():
    svc = NPCLifeEngine(MockChronicle())
    assert hasattr(svc, 'get_npc_relationships')


def test_npc_life_engine_has_get_npc_stats():
    svc = NPCLifeEngine(MockChronicle())
    assert hasattr(svc, 'get_npc_stats')


def test_npc_life_engine_methods_are_async():
    import inspect
    svc = NPCLifeEngine(MockChronicle())
    for method in ['get_relationship', 'get_npc_relationships', 'get_npc_stats']:
        if hasattr(svc, method):
            assert inspect.iscoroutinefunction(getattr(svc, method)), f"{method} should be async"