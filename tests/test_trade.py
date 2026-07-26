from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import MockChronicle, mock_get_db


def _mock_user_service(loc1="dark_forest", loc2="dark_forest", gold=100):
    svc = AsyncMock()

    async def get_side(user_id):
        if user_id == 123:
            return {"user_id": 123, "gold": gold, "display_name": "Player1", "current_location": loc1}
        return {"user_id": 456, "gold": 50, "display_name": "Player2", "current_location": loc2}

    svc.get = AsyncMock(side_effect=get_side)
    return svc


def _mock_inventory_service(has_items=True):
    svc = AsyncMock()
    svc.has.return_value = has_items
    return svc


@pytest.fixture
def trade_service():
    from services.trade_service import TradeService
    return TradeService(MockChronicle(), _mock_user_service(), _mock_inventory_service())


@pytest.mark.asyncio
async def test_create_self_trade(trade_service):
    result = await trade_service.create(123, 123, [], 0, [], 0)
    assert result["success"] is False
    assert "самим собой" in result["message"]


@pytest.mark.asyncio
async def test_create_different_locations(trade_service):
    ts = trade_service.__class__(MockChronicle(), _mock_user_service(loc1="forest", loc2="village"), _mock_inventory_service())
    result = await ts.create(123, 456, [], 0, [], 0)
    assert result["success"] is False
    assert "одной локации" in result["message"]


@pytest.mark.asyncio
async def test_create_same_location(trade_service):
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    session.execute.return_value = result_mock
    session.commit = AsyncMock()
    session.add = MagicMock()

    async def fake_get_db():
        yield session

    with patch("services.trade_service.get_db", side_effect=lambda: fake_get_db()):
        result = await trade_service.create(123, 456, [], 10, [], 0)

    assert result["success"] is True


@pytest.mark.asyncio
async def test_create_insufficient_gold(trade_service):
    ts = trade_service.__class__(MockChronicle(), _mock_user_service(gold=5), _mock_inventory_service())
    result = await ts.create(123, 456, [], 50, [], 0)
    assert result["success"] is False
    assert "золота" in result["message"]


@pytest.mark.asyncio
async def test_create_missing_item(trade_service):
    ts = trade_service.__class__(MockChronicle(), _mock_user_service(), _mock_inventory_service(has_items=False))
    result = await ts.create(123, 456, [{"item_id": "wolf_fang", "qty": 1}], 0, [], 0)
    assert result["success"] is False
    assert "wolf_fang" in result["message"]


@pytest.mark.asyncio
async def test_accept_wrong_user(trade_service):
    session = AsyncMock()
    trade_mock = MagicMock()
    trade_mock.to_user = 999
    trade_mock.status = "pending"
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = trade_mock
    session.execute.return_value = result_mock

    async def fake_get_db():
        yield session

    with patch("services.trade_service.get_db", side_effect=lambda: fake_get_db()):
        result = await trade_service.accept(1, 456)

    assert result["success"] is False
    assert "не для тебя" in result["message"]


@pytest.mark.asyncio
async def test_accept_trade_not_found(trade_service):
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    session.execute.return_value = result_mock

    async def fake_get_db():
        yield session

    with patch("services.trade_service.get_db", side_effect=lambda: fake_get_db()):
        result = await trade_service.accept(999, 456)

    assert result["success"] is False
    assert "не найден" in result["message"]


@pytest.mark.asyncio
async def test_decline_trade(trade_service):
    session = AsyncMock()
    trade_mock = MagicMock()
    trade_mock.to_user = 456
    trade_mock.status = "pending"
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = trade_mock
    session.execute.return_value = result_mock
    session.commit = AsyncMock()

    async def fake_get_db():
        yield session

    with patch("services.trade_service.get_db", side_effect=lambda: fake_get_db()):
        result = await trade_service.decline(1, 456)

    assert result["success"] is True
    assert trade_mock.status == "declined"


@pytest.mark.asyncio
async def test_cancel_trade_wrong_user(trade_service):
    session = AsyncMock()
    trade_mock = MagicMock()
    trade_mock.from_user = 999
    trade_mock.status = "pending"
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = trade_mock
    session.execute.return_value = result_mock

    async def fake_get_db():
        yield session

    with patch("services.trade_service.get_db", side_effect=lambda: fake_get_db()):
        result = await trade_service.cancel(1, 456)

    assert result["success"] is False
    assert "отправитель" in result["message"]


@pytest.mark.asyncio
async def test_cancel_trade_success(trade_service):
    session = AsyncMock()
    trade_mock = MagicMock()
    trade_mock.from_user = 123
    trade_mock.status = "pending"
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = trade_mock
    session.execute.return_value = result_mock
    session.commit = AsyncMock()

    async def fake_get_db():
        yield session

    with patch("services.trade_service.get_db", side_effect=lambda: fake_get_db()):
        result = await trade_service.cancel(1, 123)

    assert result["success"] is True
    assert trade_mock.status == "cancelled"
