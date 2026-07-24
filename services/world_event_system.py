import random
from datetime import datetime
from domain.events import EventType, Importance


WORLD_EVENT_TYPES = {
    "festival": {"name": "Праздник", "icon": "🎉", "duration_hours": 24, "xp_bonus": 1.5},
    "invasion": {"name": "Вторжение", "icon": "⚔️", "duration_hours": 12, "xp_bonus": 2.0},
    "anomaly": {"name": "Аномалия", "icon": "🔮", "duration_hours": 6, "xp_bonus": 1.0},
    "harvest": {"name": "Урожай", "icon": "🌾", "duration_hours": 48, "gold_bonus": 1.5},
    "fog": {"name": "Туманный шторм", "icon": "🌫️", "duration_hours": 8, "hidden_bonus": True},
}


class WorldEvent:

    def __init__(self, event_type: str, name: str, region_id: str = None, duration_hours: int = 24):
        self.event_type = event_type
        self.name = name
        self.region_id = region_id
        self.duration_hours = duration_hours
        self.start_time = datetime.now()
        self.end_time = None
        self.is_active = True
        self.participants = []
        self.data = {}

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "name": self.name,
            "region_id": self.region_id,
            "duration_hours": self.duration_hours,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "is_active": self.is_active,
            "participants": self.participants,
            "data": self.data,
        }


class WorldEventSystem:

    def __init__(self, chronicle):
        self.chronicle = chronicle
        self._active_events = []
        self._event_history = []

    async def start_event(self, event_type: str, name: str = None, region_id: str = None) -> dict:
        type_info = WORLD_EVENT_TYPES.get(event_type, {})
        if not name:
            name = type_info.get("name", event_type)

        duration = type_info.get("duration_hours", 24)
        event = WorldEvent(event_type, name, region_id, duration)
        self._active_events.append(event)

        await self.chronicle.publish(
            EventType.WORLD_EVENT,
            f"Мировое событие начато: {type_info.get('icon', '❓')} {name}",
            region_id=region_id,
            importance=Importance.NOTABLE,
        )

        return event.to_dict()

    async def end_event(self, event_type: str, region_id: str = None) -> bool:
        for event in self._active_events:
            if event.event_type == event_type and event.region_id == region_id:
                event.is_active = False
                event.end_time = datetime.now()
                self._event_history.append(event)
                self._active_events.remove(event)

                await self.chronicle.publish(
                    EventType.WORLD_EVENT,
                    f"Мировое событие завершено: {event.name}",
                    region_id=region_id,
                    importance=Importance.COMMON,
                )
                return True
        return False

    async def tick(self):
        now = datetime.now()
        expired = []
        for event in self._active_events:
            elapsed = (now - event.start_time).total_seconds() / 3600
            if elapsed >= event.duration_hours:
                expired.append(event)

        for event in expired:
            await self.end_event(event.event_type, event.region_id)

    def get_active_events(self, region_id: str = None) -> list:
        if region_id:
            return [e.to_dict() for e in self._active_events if e.region_id == region_id or e.region_id is None]
        return [e.to_dict() for e in self._active_events]

    def get_event_history(self, limit: int = 10) -> list:
        return [e.to_dict() for e in self._event_history[-limit:]]

    def get_event_types(self) -> list:
        return [
            {"type": k, "name": v["name"], "icon": v["icon"], "duration": v["duration_hours"]}
            for k, v in WORLD_EVENT_TYPES.items()
        ]

    def has_active_event(self, event_type: str, region_id: str = None) -> bool:
        for e in self._active_events:
            if e.event_type == event_type:
                if region_id is None or e.region_id == region_id or e.region_id is None:
                    return True
        return False

    def get_xp_multiplier(self, region_id: str = None) -> float:
        multiplier = 1.0
        for e in self._active_events:
            if region_id and e.region_id and e.region_id != region_id:
                continue
            type_info = WORLD_EVENT_TYPES.get(e.event_type, {})
            xp_bonus = type_info.get("xp_bonus", 1.0)
            multiplier = max(multiplier, xp_bonus)
        return multiplier
