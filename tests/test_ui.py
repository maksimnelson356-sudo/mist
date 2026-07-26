import pytest
from ui.formatter import hp_bar, xp_bar, gold_fmt, location_fmt, level_fmt, reputation_fmt, role_icon, rarity_icon, weather_icon, time_icon
from ui.keyboards import main_menu_kb, back_kb, confirm_kb, list_kb, paginated_kb


def test_hp_bar_full():
    result = hp_bar(100, 100)
    assert "❤️" in result
    assert "100/100" in result


def test_hp_bar_empty():
    result = hp_bar(0, 100)
    assert "🤍" in result
    assert "0/100" in result


def test_hp_bar_partial():
    result = hp_bar(50, 100, length=10)
    assert "❤️" in result
    assert "🤍" in result
    assert "50/100" in result


def test_xp_bar():
    result = xp_bar(50, 100)
    assert "⭐" in result
    assert "50/100" in result


def test_gold_fmt_normal():
    assert gold_fmt(100) == "100 🪙"


def test_gold_fmt_large():
    assert gold_fmt(10000) == "10k 🪙"


def test_gold_fmt_zero():
    assert gold_fmt(0) == "0 🪙"


def test_location_fmt():
    assert location_fmt("Лес") == "📍 Лес"
    assert location_fmt("Лес", "Тёмный") == "📍 Лес [Тёмный]"


def test_level_fmt():
    assert level_fmt(5) == "⭐ Ур. 5"


def test_reputation_fmt():
    result = reputation_fmt(50, "Нейтральный")
    assert "50" in result
    assert "Нейтральный" in result


def test_role_icon():
    assert role_icon("leader") == "👑"
    assert role_icon("officer") == "⭐"
    assert role_icon("member") == "👤"
    assert role_icon("unknown") == "👤"


def test_rarity_icon():
    assert rarity_icon("common") == "⬜"
    assert rarity_icon("legendary") == "🟠"
    assert rarity_icon("unknown") == "⬜"


def test_weather_icon():
    assert weather_icon("clear") == "☀️"
    assert weather_icon("storm") == "⛈️"
    assert weather_icon("unknown") == "❓"


def test_time_icon():
    assert time_icon("morning") == "🌅"
    assert time_icon("night") == "🌙"
    assert time_icon("unknown") == "❓"


def test_main_menu_kb():
    kb = main_menu_kb()
    assert len(kb.inline_keyboard) > 0
    assert kb.inline_keyboard[0][0].text == "🔍 Осмотреться"


def test_back_kb():
    kb = back_kb()
    assert len(kb.inline_keyboard) == 1
    assert kb.inline_keyboard[0][0].callback_data == "main_menu"


def test_confirm_kb():
    kb = confirm_kb("leave_guild")
    assert len(kb.inline_keyboard) == 1
    assert kb.inline_keyboard[0][0].callback_data == "confirm:leave_guild"
    assert kb.inline_keyboard[0][1].callback_data == "main_menu"


def test_list_kb():
    items = [{"id": "1", "label": "Item 1"}, {"id": "2", "label": "Item 2"}]
    kb = list_kb(items, "select")
    assert len(kb.inline_keyboard) == 3
    assert kb.inline_keyboard[0][0].callback_data == "select:1"


def test_paginated_kb():
    items = [{"id": str(i), "label": f"Item {i}"} for i in range(25)]
    kb = paginated_kb(items, 0, 10, "select")
    assert len(kb.inline_keyboard) == 12
