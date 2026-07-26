WEATHER_STATES = {
    "clear": {"name": "Ясно", "icon": "☀️", "description": "Солнце светит сквозь туман."},
    "rain": {"name": "Дождь", "icon": "🌧️", "description": "Мелкий дождь стучит по листьям."},
    "storm": {"name": "Гроза", "icon": "⛈️", "description": "Молнии разрывают небо."},
    "fog": {"name": "Туман", "icon": "🌫️", "description": "Густой туман скрывает всё."},
    "snow": {"name": "Снег", "icon": "❄️", "description": "Снежинки кружатся в воздухе."},
}

WEATHER_EFFECTS = {
    "clear": {
        "xp_bonus": 0, "movement_penalty": 0,
        "movement_hunger_cost": 0, "encounter_chance": 0.0,
        "danger_modifier": 0, "npc_shelter": False,
        "price_modifier": 1.0, "exploration_risk": 0.0,
    },
    "rain": {
        "xp_bonus": 0, "movement_penalty": 0,
        "movement_hunger_cost": 1, "encounter_chance": 0.05,
        "danger_modifier": 5, "npc_shelter": False,
        "price_modifier": 1.05, "exploration_risk": 0.05,
    },
    "storm": {
        "xp_bonus": -5, "movement_penalty": 2,
        "movement_hunger_cost": 3, "encounter_chance": 0.15,
        "danger_modifier": 15, "npc_shelter": True,
        "price_modifier": 1.20, "exploration_risk": 0.20,
    },
    "fog": {
        "xp_bonus": 10, "movement_penalty": 1,
        "movement_hunger_cost": 1, "encounter_chance": 0.10,
        "danger_modifier": 10, "npc_shelter": False,
        "price_modifier": 1.10, "exploration_risk": 0.15,
    },
    "snow": {
        "xp_bonus": 0, "movement_penalty": 2,
        "movement_hunger_cost": 4, "encounter_chance": 0.05,
        "danger_modifier": 10, "npc_shelter": True,
        "price_modifier": 1.15, "exploration_risk": 0.10,
    },
}

WEATHER_TRANSITIONS = {
    "clear": {"clear": 0.5, "rain": 0.3, "fog": 0.2},
    "rain": {"clear": 0.3, "rain": 0.4, "storm": 0.2, "fog": 0.1},
    "storm": {"rain": 0.5, "storm": 0.3, "clear": 0.2},
    "fog": {"clear": 0.4, "fog": 0.4, "rain": 0.2},
    "snow": {"snow": 0.5, "clear": 0.3, "fog": 0.2},
}
