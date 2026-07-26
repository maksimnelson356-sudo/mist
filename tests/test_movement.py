import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tests.conftest import MockChronicle, mock_get_db


def _mock_user_service(loc="dark_forest", karma=0):
    svc = AsyncMock()
    svc.get.return_value = {
        "user_id": 123, "current_location": loc, "karma": karma,
        "hunger": 100, "max_hunger": 100,
    }
    return svc


def _make_location(location_id="dark_forest", name="Тёмный лес", connections=None, discovered=True,
                   is_secret=False, required_karma=0, current_weather="clear", description="desc"):
    mock = MagicMock()
    mock.location_id = location_id
    mock.name = name
    mock.connections = connections or ["light_meadow"]
    mock.discovered = discovered
    mock.discovered_by = None
    mock.discovered_at = None
    mock.is_secret = is_secret
    mock.required_karma = required_karma
    mock.current_weather = current_weather
    mock.description = description
    mock.state_data = {}
    mock.x = 0
    mock.y = 0
    mock.z = 0
    return mock


@pytest.fixture
def movement_service():
    from services.movement_service import MovementService
    return MovementService(MockChronicle(), _mock_user_service())


@pytest.mark.asyncio
async def test_get_location(movement_service):
    loc = _make_location()
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = loc
    session.execute.return_value = result_mock

    async def fake_get_db():
        yield session

    with patch("services.movement_service.get_db", side_effect=lambda: fake_get_db()):
        result = await movement_service.get_location("dark_forest")

    assert result is not None
    assert result["location_id"] == "dark_forest"
    assert result["name"] == "Тёмный лес"


@pytest.mark.asyncio
async def test_get_location_not_found(movement_service):
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    session.execute.return_value = result_mock

    async def fake_get_db():
        yield session

    with patch("services.movement_service.get_db", side_effect=lambda: fake_get_db()):
        result = await movement_service.get_location("nonexistent")

    assert result is None


@pytest.mark.asyncio
async def test_get_location_name(movement_service):
    loc = _make_location(name="Тёмный лес")
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = loc
    session.execute.return_value = result_mock

    async def fake_get_db():
        yield session

    with patch("services.movement_service.get_db", side_effect=lambda: fake_get_db()):
        name = await movement_service.get_location_name("dark_forest")

    assert name == "Тёмный лес"


@pytest.mark.asyncio
async def test_move_not_connected(movement_service):
    loc = _make_location(connections=["light_meadow"])
    ms = movement_service.__class__(MockChronicle(), _mock_user_service(loc="dark_forest"))

    session = AsyncMock()

    async def execute_side(stmt):
        r = MagicMock()
        r.scalar_one_or_none.return_value = loc
        return r

    session.execute = AsyncMock(side_effect=execute_side)

    async def fake_get_db():
        yield session

    with patch("services.movement_service.get_db", side_effect=lambda: fake_get_db()):
        result = await ms.move(123, "dark_forest")

    assert result["success"] is False
    assert "напрямую" in result["message"]


@pytest.mark.asyncio
async def test_move_secret_location_karma_check(movement_service):
    loc = _make_location(is_secret=True, required_karma=50, connections=["dark_forest"])

    session = AsyncMock()

    async def execute_side(stmt):
        r = MagicMock()
        r.scalar_one_or_none.return_value = loc
        return r

    session.execute = AsyncMock(side_effect=execute_side)

    async def fake_get_db():
        yield session

    with patch("services.movement_service.get_db", side_effect=lambda: fake_get_db()):
        result = await movement_service.move(123, "secret_cave")

    assert result["success"] is False
    assert "не пускает" in result["message"]


@pytest.mark.asyncio
async def test_talk_to_creature_friendly(movement_service):
    creature = MagicMock()
    creature.name = "Мудрец"
    creature.disposition = "friendly"
    creature.description = "Добрый старик"
    creature.memory_with_users = None

    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = creature
    session.execute.return_value = result_mock

    async def fake_get_db():
        yield session

    with patch("services.movement_service.get_db", side_effect=lambda: fake_get_db()):
        result = await movement_service.talk_to_creature(123, "wise_man")

    assert "Мудрец" in result["message"]
    assert "Добрый старик" in result["message"]


@pytest.mark.asyncio
async def test_talk_to_creature_hostile(movement_service):
    creature = MagicMock()
    creature.name = "Волк"
    creature.disposition = "hostile"
    creature.description = "Голодный зверь"
    creature.memory_with_users = None

    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = creature
    session.execute.return_value = result_mock

    async def fake_get_db():
        yield session

    with patch("services.movement_service.get_db", side_effect=lambda: fake_get_db()):
        result = await movement_service.talk_to_creature(123, "wolf")

    assert "бесполезно" in result["message"]


@pytest.mark.asyncio
async def test_find_next_step_same_location(movement_service):
    result = await movement_service.find_next_step("a", "a")
    assert result is None
