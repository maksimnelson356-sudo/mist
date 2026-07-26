from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import MockChronicle, mock_get_db


def _mock_user_service(gold=100, level=5, karma=0):
    svc = AsyncMock()
    svc.get.return_value = {
        "user_id": 123, "gold": gold, "level": level, "karma": karma,
        "display_name": "Test", "current_location": "market_square",
        "reputation": 0,
    }
    return svc


def _mock_inventory_service():
    return AsyncMock()


def _make_shop_entry(item_id="wolf_fang", price=10, stock=10, required_level=1, required_karma=0):
    mock = MagicMock()
    mock.id = 1
    mock.shop_id = "market_square"
    mock.item_id = item_id
    mock.price = price
    mock.stock = stock
    mock.required_level = required_level
    mock.required_karma = required_karma
    return mock


def _make_template(item_id="wolf_fang", name="Волчий клык", rarity="common"):
    mock = MagicMock()
    mock.item_id = item_id
    mock.name = name
    mock.description = "desc"
    mock.rarity = rarity
    return mock


@pytest.fixture
def shop_service():
    from services.shop_service import ShopService
    return ShopService(MockChronicle(), _mock_user_service(), _mock_inventory_service())


@pytest.mark.asyncio
async def test_buy_item_not_found(shop_service):
    session = AsyncMock()
    call_count = [0]

    async def execute_side(stmt):
        call_count[0] += 1
        r = MagicMock()
        r.scalar_one_or_none.return_value = None
        return r

    session.execute = AsyncMock(side_effect=execute_side)

    async def fake_get_db():
        yield session

    with patch("services.shop_service.get_db", side_effect=lambda: fake_get_db()):
        result = await shop_service.buy(123, "market_square", "wolf_fang")

    assert result["success"] is False
    assert "нет в магазине" in result["message"]


@pytest.mark.asyncio
async def test_buy_insufficient_gold(shop_service):
    svc = _mock_user_service(gold=5)
    from services.shop_service import ShopService
    ss = ShopService(MockChronicle(), svc, _mock_inventory_service())

    session = AsyncMock()
    call_count = [0]

    async def execute_side(stmt):
        call_count[0] += 1
        r = MagicMock()
        r.scalar_one_or_none.return_value = _make_shop_entry(price=100, required_level=1, required_karma=0)
        return r

    session.execute = AsyncMock(side_effect=execute_side)

    async def fake_get_db():
        yield session

    with patch("services.shop_service.get_db", side_effect=lambda: fake_get_db()):
        result = await ss.buy(123, "market_square", "wolf_fang")

    assert result["success"] is False
    assert "золота" in result["message"]


@pytest.mark.asyncio
async def test_buy_low_level(shop_service):
    svc = _mock_user_service(level=1)
    from services.shop_service import ShopService
    ss = ShopService(MockChronicle(), svc, _mock_inventory_service())

    session = AsyncMock()

    async def execute_side(stmt):
        r = MagicMock()
        r.scalar_one_or_none.return_value = _make_shop_entry(required_level=10, required_karma=0)
        return r

    session.execute = AsyncMock(side_effect=execute_side)

    async def fake_get_db():
        yield session

    with patch("services.shop_service.get_db", side_effect=lambda: fake_get_db()):
        result = await ss.buy(123, "market_square", "wolf_fang")

    assert result["success"] is False
    assert "уровень" in result["message"]


@pytest.mark.asyncio
async def test_buy_low_karma(shop_service):
    svc = _mock_user_service(karma=-100)
    from services.shop_service import ShopService
    ss = ShopService(MockChronicle(), svc, _mock_inventory_service())

    session = AsyncMock()

    async def execute_side(stmt):
        r = MagicMock()
        r.scalar_one_or_none.return_value = _make_shop_entry(required_level=1, required_karma=-50)
        return r

    session.execute = AsyncMock(side_effect=execute_side)

    async def fake_get_db():
        yield session

    with patch("services.shop_service.get_db", side_effect=lambda: fake_get_db()):
        result = await ss.buy(123, "market_square", "wolf_fang")

    assert result["success"] is False
    assert "карма" in result["message"]


@pytest.mark.asyncio
async def test_sell_item_not_found(shop_service):
    session = AsyncMock()

    call_count = [0]

    async def execute_side(stmt):
        call_count[0] += 1
        r = MagicMock()
        if call_count[0] == 1:
            r.scalar_one_or_none.return_value = None
        return r

    session.execute = AsyncMock(side_effect=execute_side)

    async def fake_get_db():
        yield session

    with patch("services.shop_service.get_db", side_effect=lambda: fake_get_db()):
        result = await shop_service.sell(123, "nonexistent")

    assert result["success"] is False
    assert "не найден" in result["message"]


@pytest.mark.asyncio
async def test_sell_no_item_in_inventory(shop_service):
    session = AsyncMock()
    template = _make_template()

    call_count = [0]

    async def execute_side(stmt):
        call_count[0] += 1
        r = MagicMock()
        if call_count[0] == 1:
            r.scalar_one_or_none.return_value = template
        elif call_count[0] == 2:
            r.scalar_one_or_none.return_value = None
        return r

    session.execute = AsyncMock(side_effect=execute_side)

    async def fake_get_db():
        yield session

    with patch("services.shop_service.get_db", side_effect=lambda: fake_get_db()):
        result = await shop_service.sell(123, "wolf_fang")

    assert result["success"] is False
    assert "нет этого предмета" in result["message"]


@pytest.mark.asyncio
async def test_shop_locations():
    from services.shop_service import ShopService
    assert "market_square" in ShopService.SHOP_LOCATIONS
    assert "fishing_village" in ShopService.SHOP_LOCATIONS
