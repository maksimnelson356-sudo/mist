import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.raid_service import RaidService


class MockChronicle:
    async def publish(self, *a, **kw):
        pass


def test_raid_service_init():
    svc = RaidService(MockChronicle(), MagicMock())
    assert svc is not None


def test_create_raid_is_async():
    import inspect
    assert inspect.iscoroutinefunction(RaidService.create_raid)


def test_get_active_raids_is_async():
    import inspect
    assert inspect.iscoroutinefunction(RaidService.get_active_raids)


def test_join_raid_is_async():
    import inspect
    assert inspect.iscoroutinefunction(RaidService.join_raid)


def test_raid_attack_is_async():
    import inspect
    assert inspect.iscoroutinefunction(RaidService.raid_attack)


def test_raid_service_has_all_methods():
    svc = RaidService(MockChronicle(), MagicMock())
    assert hasattr(svc, 'create_raid')
    assert hasattr(svc, 'get_active_raids')
    assert hasattr(svc, 'join_raid')
    assert hasattr(svc, 'raid_attack')