from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import MockChronicle, mock_get_db


def _mock_user_service(hp=100, is_alive=True):
    svc = AsyncMock()

    async def get_side(user_id):
        return {
            "user_id": user_id, "hp": hp, "max_hp": 100, "level": 5,
            "attack": 10, "defense": 5, "xp": 0, "gold": 50,
            "is_alive": is_alive, "display_name": f"Player{user_id}",
            "pvp_rating": 1000, "pvp_wins": 0, "pvp_losses": 0,
            "current_location": "dark_forest",
        }

    svc.get = AsyncMock(side_effect=get_side)
    return svc


@pytest.fixture
def pvp_service():
    from services.pvp_service import PvPService
    return PvPService(MockChronicle(), _mock_user_service())


@pytest.mark.asyncio
async def test_battle_dead_user(pvp_service):
    pvp_service.user_service = _mock_user_service(is_alive=False)
    result = await pvp_service.battle(123, 456)
    assert result["success"] is False
    assert "мёртв" in result["message"]


@pytest.mark.asyncio
async def test_battle_dead_target(pvp_service):
    original_get = pvp_service.user_service.get

    async def get_side(user_id):
        if user_id == 456:
            return {"user_id": 456, "is_alive": False, "hp": 0, "max_hp": 100,
                    "level": 5, "attack": 10, "defense": 5, "xp": 0, "gold": 50,
                    "display_name": "Dead", "pvp_rating": 1000, "pvp_wins": 0, "pvp_losses": 0}
        return {"user_id": 123, "is_alive": True, "hp": 100, "max_hp": 100,
                "level": 5, "attack": 10, "defense": 5, "xp": 0, "gold": 50,
                "display_name": "Player", "pvp_rating": 1000, "pvp_wins": 0, "pvp_losses": 0,
                "current_location": "dark_forest"}

    pvp_service.user_service.get = AsyncMock(side_effect=get_side)
    result = await pvp_service.battle(123, 456)
    assert result["success"] is False
    assert "мёртв" in result["message"]


@pytest.mark.asyncio
async def test_battle_runs(pvp_service):
    session = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()

    async def fake_get_db():
        yield session

    with patch("services.pvp_service.get_db", side_effect=lambda: fake_get_db()):
        result = await pvp_service.battle(123, 456)

    assert result["outcome"] in ("victory", "defeat", "draw")
    assert len(result["rounds"]) > 0
    assert result["user_hp"] >= 0
    assert result["target_hp"] >= 0


@pytest.mark.asyncio
async def test_get_stats(pvp_service):
    session = AsyncMock()

    result_mock = MagicMock()
    result_mock.scalar.return_value = 5
    session.execute.return_value = result_mock

    async def fake_get_db():
        yield session

    with patch("services.pvp_service.get_db", side_effect=lambda: fake_get_db()):
        stats = await pvp_service.get_stats(123)

    assert "rating" in stats
    assert "wins" in stats
    assert "losses" in stats
    assert "winrate" in stats


@pytest.mark.asyncio
async def test_get_leaderboard(pvp_service):
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    session.execute.return_value = result_mock

    async def fake_get_db():
        yield session

    with patch("services.pvp_service.get_db", side_effect=lambda: fake_get_db()):
        board = await pvp_service.get_leaderboard()

    assert isinstance(board, list)


@pytest.mark.asyncio
async def test_user_to_dict():
    from services.pvp_service import PvPService
    mock_row = MagicMock()
    mock_row.user_id = 123
    mock_row.username = "test"
    mock_row.display_name = "Test"
    mock_row.level = 5
    mock_row.hp = 100
    mock_row.max_hp = 100
    mock_row.attack = 10
    mock_row.defense = 5
    mock_row.pvp_rating = 1000
    mock_row.pvp_wins = 3
    mock_row.pvp_losses = 1

    d = PvPService._user_to_dict(mock_row)
    assert d["user_id"] == 123
    assert d["pvp_rating"] == 1000
    assert d["pvp_wins"] == 3
