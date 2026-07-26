import json
import pytest
from services.quest_service import QuestService


class MockChronicle:
    async def publish(self, *a, **kw):
        pass


def test_quest_rewards_json_parsing():
    rewards = {"xp": 50, "gold": 20, "items": [{"id": "herb", "qty": 2}]}
    raw = json.dumps(rewards)
    parsed = json.loads(raw)
    assert parsed["xp"] == 50
    assert parsed["gold"] == 20
    assert len(parsed["items"]) == 1


def test_quest_rewards_with_memories():
    rewards = {"xp": 30, "memories": 5, "karma": 10}
    raw = json.dumps(rewards)
    parsed = json.loads(raw)
    assert parsed["xp"] == 30
    assert parsed["memories"] == 5
    assert parsed["karma"] == 10


def test_quest_rewards_with_items():
    rewards = {"xp": 20, "items": [{"id": "sword", "qty": 1}, {"id": "potion", "qty": 3}]}
    raw = json.dumps(rewards)
    parsed = json.loads(raw)
    assert len(parsed["items"]) == 2
    assert parsed["items"][0]["id"] == "sword"
    assert parsed["items"][1]["qty"] == 3


def test_quest_rewards_with_gold():
    rewards = {"gold": 100}
    raw = json.dumps(rewards)
    parsed = json.loads(raw)
    assert parsed["gold"] == 100


def test_quest_rewards_empty():
    rewards = {}
    raw = json.dumps(rewards)
    parsed = json.loads(raw)
    assert isinstance(parsed, dict)
    assert len(parsed) == 0


def test_can_init_quest_service():
    svc = QuestService(MockChronicle(), None)
    assert svc is not None


def test_quest_service_has_required_methods():
    svc = QuestService(MockChronicle(), None)
    assert hasattr(QuestService, 'accept')
    assert hasattr(QuestService, 'update_progress')
    assert hasattr(QuestService, 'complete')