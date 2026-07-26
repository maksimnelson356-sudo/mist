import pytest
from unittest.mock import AsyncMock, MagicMock


class MockChronicle:
    def __init__(self):
        self.events = []

    async def publish(self, event_type, message, player_id=None, importance=None, metadata=None):
        self.events.append({
            "event_type": event_type,
            "message": message,
            "player_id": player_id,
            "importance": importance,
            "metadata": metadata,
        })


@pytest.fixture
def chronicle():
    return MockChronicle()
