import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.chronicle_service import ChronicleService, EventType, Importance


class MockChronicle(ChronicleService):
    pass


def test_chronicle_service_init():
    svc = ChronicleService()
    assert svc is not None


def test_event_type_has_values():
    assert EventType.QUEST_COMPLETED.value == "quest_completed"
    assert EventType.QUEST_ACCEPTED.value == "quest_accepted"


def test_importance_has_values():
    assert Importance.TRIVIAL.value == "trivial"
    assert Importance.COMMON.value == "common"
    assert Importance.NOTABLE.value == "notable"


def test_publish_returns_event_id_string():
    session = MagicMock()
    session.commit = AsyncMock()
    session.add = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)

    async def fake_get_db():
        yield session

    svc = ChronicleService()
    with patch("services.chronicle_service.get_db", side_effect=lambda: fake_get_db()):
        event_id = asyncio.run(svc.publish(EventType.QUEST_COMPLETED, "Test"))

    assert isinstance(event_id, str)
    assert len(event_id) > 0


def test_get_latest_returns_list():
    session = MagicMock()
    session.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))
    session.commit = AsyncMock()

    async def fake_get_db():
        yield session

    svc = ChronicleService()
    with patch("services.chronicle_service.get_db", side_effect=lambda: fake_get_db()):
        result = asyncio.run(svc.get_latest(limit=5))

    assert isinstance(result, list)


def test_get_by_type_returns_list():
    session = MagicMock()
    session.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))
    session.commit = AsyncMock()

    async def fake_get_db():
        yield session

    svc = ChronicleService()
    with patch("services.chronicle_service.get_db", side_effect=lambda: fake_get_db()):
        result = asyncio.run(svc.get_by_type(EventType.QUEST_COMPLETED, limit=10))

    assert isinstance(result, list)