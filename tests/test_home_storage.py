import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.home_service import HomeService


class MockChronicle:
    async def publish(self, *a, **kw):
        pass


@pytest.fixture
def home_service():
    return HomeService(MockChronicle())


def _make_home(storage=None, storage_capacity=20):
    mock = MagicMock()
    mock.owner_id = 123
    mock.is_active = True
    mock.storage = storage or []
    mock.storage_capacity = storage_capacity
    return mock


def _mock_get_db(session):
    async def gen():
        yield session
    return gen


def test_storage_deposit_fresh(home_service):
    async def run():
        mock_home = _make_home(storage=[])
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_home
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        with patch("services.home_service.get_db", return_value=_mock_get_db(mock_session)()):
            return await home_service.storage_deposit(123, "bread", 3), mock_home
    result, mock_home = asyncio.run(run())
    assert result["success"] is True
    assert len(mock_home.storage) == 1
    assert mock_home.storage[0]["item_id"] == "bread"
    assert mock_home.storage[0]["qty"] == 3


def test_storage_deposit_stack(home_service):
    async def run():
        mock_home = _make_home(storage=[{"item_id": "bread", "qty": 2}])
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_home
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        with patch("services.home_service.get_db", return_value=_mock_get_db(mock_session)()):
            return await home_service.storage_deposit(123, "bread", 3), mock_home
    result, mock_home = asyncio.run(run())
    assert result["success"] is True
    assert len(mock_home.storage) == 1
    assert mock_home.storage[0]["qty"] == 5


def test_storage_deposit_full(home_service):
    async def run():
        items = [{"item_id": f"item_{i}", "qty": 1} for i in range(20)]
        mock_home = _make_home(storage=items, storage_capacity=20)
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_home
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        with patch("services.home_service.get_db", return_value=_mock_get_db(mock_session)()):
            return await home_service.storage_deposit(123, "bread", 1)
    result = asyncio.run(run())
    assert result["success"] is False
    assert "места" in result["message"]


def test_storage_withdraw_normal(home_service):
    async def run():
        mock_home = _make_home(storage=[{"item_id": "bread", "qty": 5}])
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_home
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        with patch("services.home_service.get_db", return_value=_mock_get_db(mock_session)()):
            return await home_service.storage_withdraw(123, "bread", 2), mock_home
    result, mock_home = asyncio.run(run())
    assert result["success"] is True
    assert mock_home.storage[0]["qty"] == 3


def test_storage_withdraw_all(home_service):
    async def run():
        mock_home = _make_home(storage=[{"item_id": "bread", "qty": 3}])
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_home
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        with patch("services.home_service.get_db", return_value=_mock_get_db(mock_session)()):
            return await home_service.storage_withdraw(123, "bread", 3), mock_home
    result, mock_home = asyncio.run(run())
    assert result["success"] is True
    assert len(mock_home.storage) == 0


def test_storage_withdraw_insufficient(home_service):
    async def run():
        mock_home = _make_home(storage=[{"item_id": "bread", "qty": 2}])
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_home
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        with patch("services.home_service.get_db", return_value=_mock_get_db(mock_session)()):
            return await home_service.storage_withdraw(123, "bread", 5)
    result = asyncio.run(run())
    assert result["success"] is False
    assert "Нет" in result["message"]


def test_storage_withdraw_not_found(home_service):
    async def run():
        mock_home = _make_home(storage=[])
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_home
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        with patch("services.home_service.get_db", return_value=_mock_get_db(mock_session)()):
            return await home_service.storage_withdraw(123, "bread", 1)
    result = asyncio.run(run())
    assert result["success"] is False
