import pytest
from services.economy_service import EconomyService, VALID_CURRENCIES


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


class MockPlayerService:
    def __init__(self, users=None):
        self._users = users or {}

    async def get(self, user_id):
        return self._users.get(user_id)


@pytest.fixture
def chronicle():
    return MockChronicle()


@pytest.fixture
def users():
    return {
        1: {"user_id": 1, "gold": 100, "gems": 10, "tokens": 5},
        2: {"user_id": 2, "gold": 50, "gems": 0, "tokens": 20},
    }


@pytest.fixture
def player(users):
    return MockPlayerService(users)


@pytest.fixture
def economy(chronicle, player):
    return EconomyService(chronicle, player)


def test_valid_currencies():
    assert "gold" in VALID_CURRENCIES
    assert "gems" in VALID_CURRENCIES
    assert "tokens" in VALID_CURRENCIES
    assert len(VALID_CURRENCIES) == 3


def test_get_balance(economy):
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        balance = loop.run_until_complete(economy.get_balance(1))
        assert balance["gold"] == 100
        assert balance["gems"] == 10
        assert balance["tokens"] == 5
    finally:
        loop.close()


def test_get_balance_unknown_user(economy):
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        balance = loop.run_until_complete(economy.get_balance(999))
        assert balance == {"gold": 0, "gems": 0, "tokens": 0}
    finally:
        loop.close()


def test_can_afford(economy):
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        assert loop.run_until_complete(economy.can_afford(1, "gold", 100)) is True
        assert loop.run_until_complete(economy.can_afford(1, "gold", 101)) is False
        assert loop.run_until_complete(economy.can_afford(1, "gems", 5)) is True
        assert loop.run_until_complete(economy.can_afford(1, "gems", 11)) is False
    finally:
        loop.close()


def test_can_afford_unknown_currency(economy):
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        assert loop.run_until_complete(economy.can_afford(1, "bitcoin", 1)) is False
    finally:
        loop.close()


def test_add_invalid_currency(economy):
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(economy.add(1, "bitcoin", 10))
        assert result["success"] is False
    finally:
        loop.close()


def test_add_invalid_amount(economy):
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(economy.add(1, "gold", 0))
        assert result["success"] is False

        result = loop.run_until_complete(economy.add(1, "gold", -5))
        assert result["success"] is False
    finally:
        loop.close()


def test_remove_insufficient(economy):
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(economy.remove(1, "gold", 200))
        assert result["success"] is False
        assert "Недостаточно" in result["message"]
    finally:
        loop.close()


def test_transfer_self(economy):
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(economy.transfer(1, 1, "gold", 10))
        assert result["success"] is False
        assert "самому себе" in result["message"]
    finally:
        loop.close()


def test_transfer_unknown_user(economy):
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(economy.transfer(1, 999, "gold", 10))
        assert result["success"] is False
    finally:
        loop.close()


def test_events_published(chronicle):
    assert len(chronicle.events) == 0
