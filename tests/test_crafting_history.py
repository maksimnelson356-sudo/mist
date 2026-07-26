import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.crafting_service import CraftingService


class MockChronicle:
    async def publish(self, *a, **kw):
        pass


class MockUserCraftingModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.fixture
def crafting_service():
    return CraftingService(MockChronicle(), MagicMock(), MagicMock())


def _mock_get_db(session):
    async def gen():
        yield session
    return gen


def test_get_history_empty(crafting_service):
    async def run():
        mock_session = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result
        with patch("services.crafting_service.get_db", return_value=_mock_get_db(mock_session)()):
            return await crafting_service.get_history(123)
    result = asyncio.run(run())
    assert result == []


def test_get_history_with_data(crafting_service):
    async def run():
        mock_session = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [
            MockUserCraftingModel(recipe_id="recipe_1", times_crafted=5),
            MockUserCraftingModel(recipe_id="recipe_2", times_crafted=2),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result
        with patch("services.crafting_service.get_db", return_value=_mock_get_db(mock_session)()):
            return await crafting_service.get_history(123)
    history = asyncio.run(run())
    assert len(history) == 2
    assert history[0]["recipe_id"] == "recipe_1"
    assert history[0]["times_crafted"] == 5


def test_get_history_limit(crafting_service):
    async def run():
        mock_session = AsyncMock()
        mock_scalars = MagicMock()
        items = [MockUserCraftingModel(recipe_id=f"r_{i}", times_crafted=i) for i in range(20)]
        mock_scalars.all.return_value = items[:5]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result
        with patch("services.crafting_service.get_db", return_value=_mock_get_db(mock_session)()):
            return await crafting_service.get_history(123, limit=5)
    history = asyncio.run(run())
    assert len(history) == 5
