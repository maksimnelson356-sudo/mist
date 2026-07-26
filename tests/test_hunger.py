import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.player_service import PlayerService


class MockChronicle:
    async def publish(self, *a, **kw):
        pass


class MockUserModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.__dict__["_sa_instance_state"] = MagicMock()


@pytest.fixture
def player_service():
    return PlayerService(MockChronicle())


def _make_user(hunger=100, max_hunger=100, **extra):
    defaults = {
        "user_id": 123, "username": "test", "display_name": "Test",
        "current_location": "dark_forest", "memories": 0, "karma": 0,
        "reputation": 0, "days_in_mist": 0, "is_alive": True,
        "hp": 100, "max_hp": 100, "attack": 10, "defense": 5,
        "level": 1, "xp": 0, "gold": 0, "gems": 0, "tokens": 0,
        "player_class": "warrior", "class_level": 1,
        "pvp_wins": 0, "pvp_losses": 0, "pvp_rating": 1000,
        "hunger": hunger, "max_hunger": max_hunger,
    }
    defaults.update(extra)
    return MockUserModel(**defaults)


def _mock_get_db(session):
    async def gen():
        yield session
    return gen


def test_decrease_hunger_normal(player_service):
    async def run():
        mock_user = _make_user(hunger=80)
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        with patch("services.player_service.get_db", return_value=_mock_get_db(mock_session)()):
            return await player_service.decrease_hunger(123, 5)
    result = asyncio.run(run())
    assert result["success"] is True
    assert result["hunger"] == 75


def test_decrease_hunger_to_zero(player_service):
    async def run():
        mock_user = _make_user(hunger=3)
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        with patch("services.player_service.get_db", return_value=_mock_get_db(mock_session)()):
            return await player_service.decrease_hunger(123, 10)
    result = asyncio.run(run())
    assert result["success"] is True
    assert result["hunger"] == 0
    assert "голоден" in result["message"]


def test_decrease_hunger_low_warning(player_service):
    async def run():
        mock_user = _make_user(hunger=25)
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        with patch("services.player_service.get_db", return_value=_mock_get_db(mock_session)()):
            return await player_service.decrease_hunger(123, 10)
    result = asyncio.run(run())
    assert result["success"] is True
    assert result["hunger"] == 15
    assert "нарастает" in result["message"]


def test_feed_normal(player_service):
    async def run():
        mock_user = _make_user(hunger=50)
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        with patch("services.player_service.get_db", return_value=_mock_get_db(mock_session)()):
            return await player_service.feed(123, 30)
    result = asyncio.run(run())
    assert result["success"] is True
    assert result["hunger"] == 80
    assert "+30" in result["message"]


def test_feed_cap_at_max(player_service):
    async def run():
        mock_user = _make_user(hunger=90, max_hunger=100)
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        with patch("services.player_service.get_db", return_value=_mock_get_db(mock_session)()):
            return await player_service.feed(123, 30)
    result = asyncio.run(run())
    assert result["success"] is True
    assert result["hunger"] == 100
    assert "+10" in result["message"]
