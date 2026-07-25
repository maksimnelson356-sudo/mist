import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from services.player_service import PlayerService
from services.profile_service import ProfileService
from services.reputation_service import ReputationService


class MockChronicle:
    def __init__(self):
        self.events = []

    async def publish(self, event_type, message, player_id=None, importance=None):
        self.events.append({
            "event_type": event_type,
            "message": message,
            "player_id": player_id,
            "importance": importance,
        })


class MockUserModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.__dict__["_sa_instance_state"] = MagicMock()


@pytest.fixture
def chronicle():
    return MockChronicle()


@pytest.fixture
def player_service(chronicle):
    return PlayerService(chronicle)


@pytest.fixture
def profile_service(chronicle, player_service):
    return ProfileService(chronicle, player_service)


@pytest.fixture
def reputation_service(chronicle, player_service):
    return ReputationService(chronicle, player_service)


def test_reputation_levels(reputation_service):
    assert reputation_service.get_level(-60) == "Враг"
    assert reputation_service.get_level(-25) == "Подозрительный"
    assert reputation_service.get_level(0) == "Нейтральный"
    assert reputation_service.get_level(75) == "Доброжелательный"
    assert reputation_service.get_level(150) == "Герой"


def test_reputation_level_edges(reputation_service):
    assert reputation_service.get_level(-100) == "Враг"
    assert reputation_service.get_level(-51) == "Враг"
    assert reputation_service.get_level(-50) == "Подозрительный"
    assert reputation_service.get_level(-1) == "Подозрительный"
    assert reputation_service.get_level(49) == "Нейтральный"
    assert reputation_service.get_level(50) == "Доброжелательный"
    assert reputation_service.get_level(99) == "Доброжелательный"
    assert reputation_service.get_level(100) == "Герой"


def test_profile_level_display(profile_service):
    assert profile_service._get_reputation_level(-60) == "Враг"
    assert profile_service._get_reputation_level(25) == "Нейтральный"
    assert profile_service._get_reputation_level(75) == "Доброжелательный"
    assert profile_service._get_reputation_level(150) == "Герой"


def test_player_service_to_dict(player_service):
    mock_user = MockUserModel(
        user_id=123,
        username="testuser",
        display_name="TestPlayer",
        created_at=None,
        last_seen=None,
        current_location="dark_forest",
        memories=5,
        karma=10,
        reputation=25,
        days_in_mist=7,
        is_alive=True,
        hp=100,
        max_hp=100,
        attack=15,
        defense=8,
        level=3,
        xp=250,
        gold=150,
        pvp_wins=5,
        pvp_losses=2,
        pvp_rating=1100,
        hunger=100,
        max_hunger=100,
    )

    result = player_service._to_dict(mock_user)

    assert result["user_id"] == 123
    assert result["display_name"] == "TestPlayer"
    assert result["reputation"] == 25
    assert result["last_seen"] is None
    assert result["level"] == 3
    assert result["hp"] == 100


def test_reputation_constants():
    from services.reputation_service import REPUTATION_LEVELS

    assert len(REPUTATION_LEVELS) == 5

    min_rep, max_rep, name, desc = REPUTATION_LEVELS[0]
    assert name == "Враг"
    assert min_rep == -100
    assert max_rep == -51

    min_rep, max_rep, name, desc = REPUTATION_LEVELS[-1]
    assert name == "Герой"
    assert min_rep == 100
