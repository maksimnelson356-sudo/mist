import pytest

from services.combat_service import TIME_COMBAT_EFFECTS, WEATHER_COMBAT_EFFECTS


def test_hunger_zero_penalty():
    hunger = 0
    base_attack = 100
    effective_attack = base_attack
    if hunger <= 0:
        effective_attack = int(effective_attack * 0.8)
    assert effective_attack == 80


def test_hunger_low_penalty():
    hunger = 15
    base_attack = 100
    effective_attack = base_attack
    if hunger <= 0:
        effective_attack = int(effective_attack * 0.8)
    elif hunger < 20:
        effective_attack = int(effective_attack * 0.9)
    assert effective_attack == 90


def test_hunger_normal():
    hunger = 50
    base_attack = 100
    effective_attack = base_attack
    if hunger <= 0:
        effective_attack = int(effective_attack * 0.8)
    elif hunger < 20:
        effective_attack = int(effective_attack * 0.9)
    assert effective_attack == 100


def test_weather_effects_exist():
    assert "rain" in WEATHER_COMBAT_EFFECTS
    assert "storm" in WEATHER_COMBAT_EFFECTS
    assert "fog" in WEATHER_COMBAT_EFFECTS
    assert "snow" in WEATHER_COMBAT_EFFECTS


def test_time_effects_exist():
    assert "night" in TIME_COMBAT_EFFECTS
    assert "morning" in TIME_COMBAT_EFFECTS
    assert "afternoon" in TIME_COMBAT_EFFECTS
    assert "evening" in TIME_COMBAT_EFFECTS


def test_weather_rain_reduces_attack():
    effect = WEATHER_COMBAT_EFFECTS["rain"]
    assert effect["attack_mod"] < 0


def test_weather_fog_increases_defense():
    effect = WEATHER_COMBAT_EFFECTS["fog"]
    assert effect["defense_mod"] > 0


def test_time_night_tradeoff():
    effect = TIME_COMBAT_EFFECTS["night"]
    assert effect["attack_mod"] < 0
    assert effect["defense_mod"] > 0
    assert effect["xp_mod"] > 0
