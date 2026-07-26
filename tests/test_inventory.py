import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tests.conftest import MockChronicle, mock_get_db, make_mock_session


def _make_inv_row(item_id="wolf_fang", quantity=5, is_magic=False):
    mock = MagicMock()
    mock.id = 1
    mock.user_id = 123
    mock.item_id = item_id
    mock.quantity = quantity
    mock.is_magic = is_magic
    return mock


def _make_template(item_id="wolf_fang", name="Волчий клык", rarity="common", is_usable=False, use_effect=None):
    mock = MagicMock()
    mock.item_id = item_id
    mock.name = name
    mock.description = "Описание"
    mock.rarity = rarity
    mock.is_usable = is_usable
    mock.use_effect = use_effect or "{}"
    mock.lore = ""
    return mock


def _make_user(hp=100, max_hp=100, level=1, xp=0):
    mock = MagicMock()
    mock.user_id = 123
    mock.hp = hp
    mock.max_hp = max_hp
    mock.level = level
    mock.xp = xp
    mock.gold = 50
    mock.attack = 10
    mock.defense = 5
    return mock


@pytest.fixture
def inv_service():
    from services.inventory_service import InventoryService
    return InventoryService(MockChronicle())


@pytest.mark.asyncio
async def test_add_new_item(inv_service):
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    session.execute.return_value = result_mock
    session.commit = AsyncMock()
    session.add = MagicMock()

    async def fake_get_db():
        yield session

    with patch("services.inventory_service.get_db", side_effect=lambda: fake_get_db()):
        await inv_service.add(123, "wolf_fang", qty=3)

    session.add.assert_called_once()
    call_args = session.add.call_args[0][0]
    assert call_args.item_id == "wolf_fang"
    assert call_args.quantity == 3


@pytest.mark.asyncio
async def test_add_existing_item(inv_service):
    existing = _make_inv_row(quantity=2)
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = existing
    session.execute.return_value = result_mock
    session.commit = AsyncMock()

    async def fake_get_db():
        yield session

    with patch("services.inventory_service.get_db", side_effect=lambda: fake_get_db()):
        await inv_service.add(123, "wolf_fang", qty=1)

    assert existing.quantity == 3


@pytest.mark.asyncio
async def test_remove_item_success(inv_service):
    existing = _make_inv_row(quantity=5)
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = existing
    session.execute.return_value = result_mock
    session.commit = AsyncMock()

    async def fake_get_db():
        yield session

    with patch("services.inventory_service.get_db", side_effect=lambda: fake_get_db()):
        result = await inv_service.remove(123, "wolf_fang", qty=3)

    assert result is True
    assert existing.quantity == 2


@pytest.mark.asyncio
async def test_remove_item_exact(inv_service):
    existing = _make_inv_row(quantity=1)
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = existing
    session.execute.return_value = result_mock
    session.commit = AsyncMock()
    session.delete = AsyncMock()

    async def fake_get_db():
        yield session

    with patch("services.inventory_service.get_db", side_effect=lambda: fake_get_db()):
        result = await inv_service.remove(123, "wolf_fang", qty=1)

    assert result is True
    session.delete.assert_called_once_with(existing)


@pytest.mark.asyncio
async def test_remove_item_not_enough(inv_service):
    existing = _make_inv_row(quantity=1)
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = existing
    session.execute.return_value = result_mock

    async def fake_get_db():
        yield session

    with patch("services.inventory_service.get_db", side_effect=lambda: fake_get_db()):
        result = await inv_service.remove(123, "wolf_fang", qty=5)

    assert result is False


@pytest.mark.asyncio
async def test_has_item(inv_service):
    existing = _make_inv_row(quantity=3)
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = existing
    session.execute.return_value = result_mock

    async def fake_get_db():
        yield session

    with patch("services.inventory_service.get_db", side_effect=lambda: fake_get_db()):
        assert await inv_service.has(123, "wolf_fang", qty=2) is True
        assert await inv_service.has(123, "wolf_fang", qty=5) is False


@pytest.mark.asyncio
async def test_has_item_not_found(inv_service):
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    session.execute.return_value = result_mock

    async def fake_get_db():
        yield session

    with patch("services.inventory_service.get_db", side_effect=lambda: fake_get_db()):
        assert await inv_service.has(123, "nonexistent") is False


@pytest.mark.asyncio
async def test_use_item_not_usable(inv_service):
    template = _make_template(is_usable=False)
    existing = _make_inv_row()

    session = AsyncMock()
    result_mock = MagicMock()

    call_count = [0]

    async def execute_side(stmt):
        nonlocal call_count
        call_count[0] += 1
        r = MagicMock()
        if call_count[0] <= 1:
            r.scalar_one_or_none.return_value = template
        else:
            r.scalar_one_or_none.return_value = existing
        return r

    session.execute = AsyncMock(side_effect=execute_side)

    async def fake_get_db():
        yield session

    with patch("services.inventory_service.get_db", side_effect=lambda: fake_get_db()):
        result = await inv_service.use_item(123, "wolf_fang")

    assert result["success"] is False
    assert "нельзя использовать" in result["message"]
