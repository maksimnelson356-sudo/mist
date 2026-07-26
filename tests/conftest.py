import pytest
from unittest.mock import AsyncMock, MagicMock


class MockChronicle:
    def __init__(self):
        self.events = []

    async def publish(self, event_type, message, player_id=None, importance=None, metadata=None):
        self.events.append({
            "event_type": event_type,
            "message": message,
            "player_id": player_id,
            "importance": importance,
            "metadata": metadata,
        })


class MockUserModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.__dict__["_sa_instance_state"] = MagicMock()


DEFAULT_USER = {
    "user_id": 123, "username": "test", "display_name": "Test",
    "current_location": "dark_forest", "memories": 0, "karma": 0,
    "reputation": 0, "days_in_mist": 0, "is_alive": True,
    "hp": 100, "max_hp": 100, "attack": 10, "defense": 5,
    "level": 1, "xp": 0, "gold": 0, "gems": 0, "tokens": 0,
    "player_class": "warrior", "class_level": 1,
    "pvp_wins": 0, "pvp_losses": 0, "pvp_rating": 1000,
    "hunger": 100, "max_hunger": 100,
}


@pytest.fixture
def chronicle():
    return MockChronicle()


@pytest.fixture
def mock_user():
    def _make(**overrides):
        data = {**DEFAULT_USER, **overrides}
        return MockUserModel(**data)
    return _make


def mock_get_db(session):
    """Create an async generator that yields a mock DB session."""
    async def gen():
        yield session
    return gen()


def make_mock_session(model_return=None):
    """Create a mock async DB session with a result that returns model_return."""
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = model_return
    result.scalars.return_value = MagicMock(all=MagicMock(return_value=[]))
    session.execute.return_value = result
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    return session
