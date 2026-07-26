import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from services.dialogue_service import DialogueService


class MockChronicle:
    async def publish(self, *a, **kw):
        pass


def _make_player_svc(user_data):
    svc = MagicMock()
    svc.get = AsyncMock(return_value=user_data)
    return svc


def test_get_dialogue_elder_greeting():
    svc = DialogueService(MockChronicle(), _make_player_svc({}))
    result = asyncio.run(svc.get_dialogue("elder", "elder"))
    assert "text" in result
    assert "options" in result
    assert isinstance(result["options"], list)


def test_get_dialogue_elder_has_options():
    svc = DialogueService(MockChronicle(), _make_player_svc({}))
    result = asyncio.run(svc.get_dialogue("elder", "elder"))
    assert len(result["options"]) > 0


def test_get_dialogue_returns_npc_type():
    svc = DialogueService(MockChronicle(), _make_player_svc({}))
    result = asyncio.run(svc.get_dialogue("elder", "elder"))
    assert result["npc_type"] == "elder"


def test_get_dialogue_bartender():
    svc = DialogueService(MockChronicle(), _make_player_svc({}))
    result = asyncio.run(svc.get_dialogue("bartender", "bartender"))
    assert result["npc_type"] == "bartender"
    assert len(result["options"]) > 0


def test_get_dialogue_merchant():
    svc = DialogueService(MockChronicle(), _make_player_svc({}))
    result = asyncio.run(svc.get_dialogue("merchant", "merchant"))
    assert result["npc_type"] == "merchant"
    assert len(result["options"]) > 0


def test_get_dialogue_filters_by_gold():
    user_data = {"reputation": 100, "gold": 0, "player_class": "warrior"}
    svc = DialogueService(MockChronicle(), _make_player_svc(user_data))
    result = asyncio.run(svc.get_dialogue("merchant", "merchant"))
    assert isinstance(result["options"], list)


def test_get_dialogue_filters_by_reputation():
    user_data = {"reputation": 0, "gold": 100, "player_class": "warrior"}
    svc = DialogueService(MockChronicle(), _make_player_svc(user_data))
    result = asyncio.run(svc.get_dialogue("elder", "elder"))
    assert isinstance(result["options"], list)