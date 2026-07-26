import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.crafting_service import CraftingService


class MockChronicle:
    async def publish(self, *a, **kw):
        pass


def _make_session(query_return=None):
    session = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.add = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = query_return
    result.scalars.return_value.all.return_value = []
    session.execute.return_value = result
    return session


def _mock_inventory():
    svc = MagicMock()
    svc.has = AsyncMock(return_value=True)
    svc.remove = AsyncMock()
    return svc


def test_crafting_service_init():
    svc = CraftingService(MockChronicle(), MagicMock(), _mock_inventory())
    assert svc is not None


def test_get_recipes_with_no_location():
    svc = CraftingService(MockChronicle(), MagicMock(), _mock_inventory())
    session = _make_session()

    async def fake_get_db():
        yield session

    with patch("services.crafting_service.get_db", side_effect=lambda: fake_get_db()):
        result = asyncio.run(svc.get_recipes())

    assert isinstance(result, list)


def test_get_recipes_with_location():
    svc = CraftingService(MockChronicle(), MagicMock(), _mock_inventory())
    session = _make_session()

    async def fake_get_db():
        yield session

    with patch("services.crafting_service.get_db", side_effect=lambda: fake_get_db()):
        result = asyncio.run(svc.get_recipes(location="market_square"))

    assert isinstance(result, list)


def test_get_history_returns_list():
    svc = CraftingService(MockChronicle(), MagicMock(), _mock_inventory())
    session = _make_session()

    async def fake_get_db():
        yield session

    with patch("services.crafting_service.get_db", side_effect=lambda: fake_get_db()):
        result = asyncio.run(svc.get_history(123))

    assert isinstance(result, list)


def test_craft_requires_ingredients():
    inv = MagicMock()
    inv.has = AsyncMock(return_value=False)
    svc = CraftingService(MockChronicle(), MagicMock(), inv)
    session = _make_session()

    async def fake_get_db():
        yield session

    with patch("services.crafting_service.get_db", side_effect=lambda: fake_get_db()):
        result = asyncio.run(svc.craft(123, "nonexistent_recipe"))

    assert result["success"] is False