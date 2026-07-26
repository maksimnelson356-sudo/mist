from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from .types import EventType, Importance


@dataclass
class ChronicleEvent:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType = EventType.WORLD_EVENT
    importance: Importance = Importance.COMMON
    title: str = ""
    description: str | None = None
    player_id: int | None = None
    region_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    metadata: dict = field(default_factory=dict)
