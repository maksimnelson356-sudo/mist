from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import MockChronicle, MockUserModel, make_mock_session, mock_get_db


def _mock_user_service(gold=100):
    svc = AsyncMock()
    svc.get.return_value = {
        "user_id": 123, "gold": gold, "level": 5, "display_name": "Test",
        "current_location": "dark_forest", "karma": 0,
    }
    return svc


@pytest.fixture
def guild_service():
    from services.guild_service import GuildService
    return GuildService(MockChronicle(), _mock_user_service())


def _mock_db_session(guild_exists=False, member_exists=False, guild=None, member=None):
    session = AsyncMock()

    def execute_side_effect(stmt):
        result = MagicMock()
        if hasattr(stmt, 'where'):
            if member_exists:
                mock_m = member or MagicMock()
                mock_m.user_id = 123
                mock_m.guild_id = "g_test"
                mock_m.role = "leader"
                mock_m.contribution = 0
                result.scalar_one_or_none.return_value = mock_m
            elif guild_exists:
                mock_g = guild or MagicMock()
                mock_g.guild_id = "g_test"
                mock_g.name = "Test Guild"
                mock_g.leader_id = 456
                mock_g.gold = 0
                mock_g.xp = 0
                mock_g.level = 1
                mock_g.description = ""
                mock_g.motto = ""
                mock_g.created_at = None
                result.scalar_one_or_none.return_value = mock_g
            else:
                result.scalar_one_or_none.return_value = None
        else:
            result.scalar_one_or_none.return_value = None
        return result

    session.execute = AsyncMock(side_effect=execute_side_effect)
    session.commit = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_create_guild_success(guild_service):
    session = _mock_db_session(member_exists=False, guild_exists=False)
    with patch("services.guild_service.get_db", return_value=mock_get_db(session)):
        result = await guild_service.create(123, "My Guild", description="Test")
    assert result["success"] is True
    assert "guild_id" in result


@pytest.mark.asyncio
async def test_create_guild_already_in_guild(guild_service):
    session = _mock_db_session(member_exists=True)
    with patch("services.guild_service.get_db", return_value=mock_get_db(session)):
        result = await guild_service.create(123, "My Guild")
    assert result["success"] is False
    assert "гильдии" in result["message"]


@pytest.mark.asyncio
async def test_join_guild(guild_service):
    session = AsyncMock()

    calls = [0]

    async def execute_side(stmt):
        calls[0] += 1
        r = MagicMock()
        if calls[0] == 1:
            r.scalar_one_or_none.return_value = None
        elif calls[0] == 2:
            mock_g = MagicMock()
            mock_g.guild_id = "g_test"
            mock_g.name = "Test Guild"
            r.scalar_one_or_none.return_value = mock_g
        return r

    session.execute = AsyncMock(side_effect=execute_side)
    session.commit = AsyncMock()
    session.add = MagicMock()

    with patch("services.guild_service.get_db", return_value=mock_get_db(session)):
        result = await guild_service.join(123, "g_test")
    assert result["success"] is True


@pytest.mark.asyncio
async def test_join_guild_not_found(guild_service):
    session = AsyncMock()

    calls = [0]

    async def execute_side(stmt):
        calls[0] += 1
        r = MagicMock()
        r.scalar_one_or_none.return_value = None
        return r

    session.execute = AsyncMock(side_effect=execute_side)

    with patch("services.guild_service.get_db", return_value=mock_get_db(session)):
        result = await guild_service.join(123, "g_nonexistent")
    assert result["success"] is False
    assert "не найдена" in result["message"]


@pytest.mark.asyncio
async def test_leave_not_in_guild(guild_service):
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.first.return_value = None
    session.execute.return_value = result_mock

    with patch("services.guild_service.get_db", return_value=mock_get_db(session)):
        result = await guild_service.leave(123)
    assert result["success"] is False
    assert "не в гильдии" in result["message"]


@pytest.mark.asyncio
async def test_donate_not_in_guild(guild_service):
    session = _mock_db_session(member_exists=False)
    with patch("services.guild_service.get_db", return_value=mock_get_db(session)):
        result = await guild_service.donate(123, 10)
    assert result["success"] is False
    assert "не в гильдии" in result["message"]


@pytest.mark.asyncio
async def test_donate_insufficient_gold(guild_service):
    svc = _mock_user_service(gold=5)
    from services.guild_service import GuildService
    gs = GuildService(MockChronicle(), svc)
    mock_info = {"guild_id": "g_test", "name": "Test", "role": "leader"}
    with patch.object(gs, "get_user_guild", return_value=mock_info):
        result = await gs.donate(123, 10)
    assert result["success"] is False
    assert "золота" in result["message"]


@pytest.mark.asyncio
async def test_donate_zero_amount(guild_service):
    svc = _mock_user_service(gold=100)
    from services.guild_service import GuildService
    gs = GuildService(MockChronicle(), svc)
    mock_info = {"guild_id": "g_test", "name": "Test", "role": "leader"}
    with patch.object(gs, "get_user_guild", return_value=mock_info):
        result = await gs.donate(123, 0)
    assert result["success"] is False
    assert "больше 0" in result["message"]


@pytest.mark.asyncio
async def test_check_permission_leader(guild_service):
    mock_info = {"guild_id": "g_test", "role": "leader"}
    with patch.object(guild_service, "get_user_guild", return_value=mock_info):
        assert await guild_service.check_permission(123, "invite") is True
        assert await guild_service.check_permission(123, "kick") is True


@pytest.mark.asyncio
async def test_check_permission_member(guild_service):
    mock_info = {"guild_id": "g_test", "role": "member"}
    with patch.object(guild_service, "get_user_guild", return_value=mock_info):
        assert await guild_service.check_permission(123, "invite") is False
        assert await guild_service.check_permission(123, "donate") is True


@pytest.mark.asyncio
async def test_set_role_unknown_role(guild_service):
    result = await guild_service.set_role("g_test", 456, "superadmin", 123)
    assert result["success"] is False
    assert "Неизвестная роль" in result["message"]


@pytest.mark.asyncio
async def test_kick_not_officer_or_leader(guild_service):
    mock_info = {"guild_id": "g_test", "role": "member"}
    with patch.object(guild_service, "get_user_guild", return_value=mock_info):
        result = await guild_service.kick("g_test", 456, 123)
    assert result["success"] is False
    assert "прав" in result["message"]


@pytest.mark.asyncio
async def test_guild_roles_constants():
    from services.guild_service import GUILD_ROLES, ROLE_HIERARCHY
    assert "leader" in GUILD_ROLES
    assert "officer" in GUILD_ROLES
    assert "member" in GUILD_ROLES
    assert ROLE_HIERARCHY == ["leader", "officer", "member"]
