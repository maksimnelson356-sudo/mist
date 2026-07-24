import random
from datetime import datetime
from domain.events import EventType, Importance


WEATHER_STATES = {
    "clear": {"name": "Ясно", "icon": "☀️", "description": "Солнце светит сквозь туман."},
    "rain": {"name": "Дождь", "icon": "🌧️", "description": "Мелкий дождь стучит по листьям."},
    "storm": {"name": "Гроза", "icon": "⛈️", "description": "Молнии разрывают небо."},
    "fog": {"name": "Туман", "icon": "🌫️", "description": "Густой туман скрывает всё."},
    "snow": {"name": "Снег", "icon": "❄️", "description": "Снежинки кружатся в воздухе."},
}

WEATHER_EFFECTS = {
    "clear": {"xp_bonus": 0, "movement_penalty": 0},
    "rain": {"xp_bonus": 0, "movement_penalty": 0},
    "storm": {"xp_bonus": 0, "movement_penalty": 1},
    "fog": {"xp_bonus": 5, "movement_penalty": 1},
    "snow": {"xp_bonus": 0, "movement_penalty": 1},
}

WEATHER_TRANSITIONS = {
    "clear": {"clear": 0.5, "rain": 0.3, "fog": 0.2},
    "rain": {"clear": 0.3, "rain": 0.4, "storm": 0.2, "fog": 0.1},
    "storm": {"rain": 0.5, "storm": 0.3, "clear": 0.2},
    "fog": {"clear": 0.4, "fog": 0.4, "rain": 0.2},
    "snow": {"snow": 0.5, "clear": 0.3, "fog": 0.2},
}


class WeatherSystem:

    def __init__(self, chronicle):
        self.chronicle = chronicle
        self._current_weather = "clear"
        self._last_change = datetime.now()
        self._region_weather = {}

    async def get_weather(self, region_id: str = None) -> dict:
        if region_id and region_id in self._region_weather:
            weather = self._region_weather[region_id]
        else:
            weather = self._current_weather

        info = WEATHER_STATES.get(weather, WEATHER_STATES["clear"])
        effects = WEATHER_EFFECTS.get(weather, WEATHER_EFFECTS["clear"])

        return {
            "state": weather,
            "name": info["name"],
            "icon": info["icon"],
            "description": info["description"],
            "effects": effects,
        }

    async def tick(self, region_id: str = None):
        current = self._region_weather.get(region_id, self._current_weather) if region_id else self._current_weather
        transitions = WEATHER_TRANSITIONS.get(current, {})

        roll = random.random()
        cumulative = 0.0
        new_weather = current

        for weather, chance in transitions.items():
            cumulative += chance
            if roll <= cumulative:
                new_weather = weather
                break

        if region_id:
            self._region_weather[region_id] = new_weather
        else:
            self._current_weather = new_weather

        if new_weather != current:
            await self.chronicle.publish(
                EventType.WORLD_EVENT,
                f"Погода изменилась: {WEATHER_STATES[current]['name']} → {WEATHER_STATES[new_weather]['name']}",
                importance=Importance.TRIVIAL,
            )

    def set_weather(self, weather: str, region_id: str = None):
        if weather not in WEATHER_STATES:
            return
        if region_id:
            self._region_weather[region_id] = weather
        else:
            self._current_weather = weather

    def get_weather_info(self, weather: str) -> dict:
        return WEATHER_STATES.get(weather, WEATHER_STATES["clear"])

    def get_all_weather_states(self) -> list:
        return [
            {"state": k, "name": v["name"], "icon": v["icon"]}
            for k, v in WEATHER_STATES.items()
        ]
