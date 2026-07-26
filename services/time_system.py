from datetime import datetime

from domain.events import EventType, Importance

TIME_PERIODS = {
    "morning": {"name": "Утро", "icon": "🌅", "hours": (6, 11)},
    "afternoon": {"name": "День", "icon": "☀️", "hours": (12, 17)},
    "evening": {"name": "Вечер", "icon": "🌆", "hours": (18, 22)},
    "night": {"name": "Ночь", "icon": "🌙", "hours": (23, 5)},
}


class TimeSystem:

    def __init__(self, chronicle):
        self.chronicle = chronicle
        self._day = 1
        self._hour = 8
        self._minute = 0
        self._time_scale = 60
        self._last_tick = datetime.now()

    def get_current_time(self) -> dict:
        period = self._get_period()
        period_info = TIME_PERIODS[period]

        return {
            "day": self._day,
            "hour": self._hour,
            "minute": self._minute,
            "period": period,
            "period_name": period_info["name"],
            "period_icon": period_info["icon"],
            "display": f"День {self._day}, {self._hour:02d}:{self._minute:02d}",
            "display_short": f"{self._hour:02d}:{self._minute:02d}",
        }

    def _get_period(self) -> str:
        for period, info in TIME_PERIODS.items():
            start, end = info["hours"]
            if start <= end:
                if start <= self._hour <= end:
                    return period
            else:
                if self._hour >= start or self._hour <= end:
                    return period
        return "morning"

    async def tick(self, minutes: int = 1):
        self._minute += minutes

        while self._minute >= 60:
            self._minute -= 60
            self._hour += 1

        old_period = self._get_period()

        while self._hour >= 24:
            self._hour -= 24
            self._day += 1
            await self.chronicle.publish(
                EventType.WORLD_EVENT,
                f"Наступил день {self._day}",
                importance=Importance.COMMON,
            )

        new_period = self._get_period()
        if old_period != new_period:
            await self.chronicle.publish(
                EventType.WORLD_EVENT,
                f"Сменилось время суток: {TIME_PERIODS[old_period]['name']} → {TIME_PERIODS[new_period]['name']}",
                importance=Importance.TRIVIAL,
            )

    def set_time(self, day: int = None, hour: int = None, minute: int = None):
        if day is not None:
            self._day = max(1, day)
        if hour is not None:
            self._hour = max(0, min(23, hour))
        if minute is not None:
            self._minute = max(0, min(59, minute))

    def advance_to_period(self, target_period: str):
        target_hours = TIME_PERIODS.get(target_period, {}).get("hours", (8, 8))
        start, end = target_hours
        if start <= end:
            self._hour = start
        else:
            self._hour = start
        self._minute = 0

    def get_day_of_week(self) -> str:
        days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        return days[(self._day - 1) % 7]

    def is_night(self) -> bool:
        return self._get_period() == "night"

    def is_day(self) -> bool:
        return self._get_period() in ("morning", "afternoon")
