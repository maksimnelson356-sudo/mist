import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class MockChronicle:
    async def publish(self, *a, **kw):
        pass


class MockQuestModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class MockUserQuestModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class MockUserModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.fixture
def quest_service():
    from services.quest_service import QuestService
    return QuestService(MockChronicle(), MagicMock())


def _mock_get_db(session):
    async def gen():
        yield session
    return gen


def test_complete_all_objectives_met(quest_service):
    async def run():
        quest = MockQuestModel(
            quest_id="q1", name="Test Quest",
            objectives=json.dumps([{"id": "obj1", "type": "kill", "target": 3, "description": "Kill 3 wolves"}]),
            rewards=json.dumps({"xp": 100, "gold": 50}),
        )
        uq = MockUserQuestModel(
            user_id=123, quest_id="q1", status="active",
            progress=json.dumps({"obj1": {"current": 3, "target": 3}}),
            started_at=datetime.utcnow(), completed_at=None,
        )
        user = MockUserModel(user_id=123, xp=0, gold=0, level=1)

        mock_session = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = uq
            elif call_count == 2:
                result.scalar_one_or_none.return_value = quest
            elif call_count == 3:
                result.scalar_one_or_none.return_value = user
            else:
                result.scalar_one_or_none.return_value = None
            return result

        mock_session.execute = mock_execute
        mock_session.commit = AsyncMock()

        with (
            patch("services.quest_service.get_db", return_value=_mock_get_db(mock_session)()),
            patch("services.container.services") as mock_svc,
        ):
            mock_svc.analytics = MagicMock()
            mock_svc.analytics.track = AsyncMock()
            return await quest_service.complete(123, "q1")

    result = asyncio.run(run())
    assert result["success"] is True
    assert result["completed"] is True
    assert "100" in result["message"]


def test_complete_objectives_not_met(quest_service):
    async def run():
        quest = MockQuestModel(
            quest_id="q1", name="Test Quest",
            objectives=json.dumps([{"id": "obj1", "type": "kill", "target": 3, "description": "Kill 3 wolves"}]),
            rewards=json.dumps({"xp": 100}),
        )
        uq = MockUserQuestModel(
            user_id=123, quest_id="q1", status="active",
            progress=json.dumps({"obj1": {"current": 1, "target": 3}}),
            started_at=datetime.utcnow(), completed_at=None,
        )

        mock_session = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = uq
            elif call_count == 2:
                result.scalar_one_or_none.return_value = quest
            else:
                result.scalar_one_or_none.return_value = None
            return result

        mock_session.execute = mock_execute
        mock_session.commit = AsyncMock()

        with patch("services.quest_service.get_db", return_value=_mock_get_db(mock_session)()):
            return await quest_service.complete(123, "q1")

    result = asyncio.run(run())
    assert result["success"] is False
    assert "не выполнены" in result["message"]


def test_complete_not_found(quest_service):
    async def run():
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with patch("services.quest_service.get_db", return_value=_mock_get_db(mock_session)()):
            return await quest_service.complete(123, "nonexistent")

    result = asyncio.run(run())
    assert result["success"] is False
