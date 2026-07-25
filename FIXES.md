# Исправления критических багов

## BUG 1: Продукты питания отсутствуют в базе данных (КРИТИЧЕСКИЙ)
- **Файл:** `seed.py`
- **Проблема:** В `handlers/game.py` добавлен `FOOD_HUNGER` с ключами `bread`, `fish`, `apple`, `cheese`, `dried_meat`, `berry`. Ни один из них не существовал в `item_templates` БД — кнопка "Поесть" была бесполезна.
- **Исправление:** Добавлены 6 записей food в список `items` в `seed.py`:
  - `bread` — Хлеб (+20 сытости)
  - `fish` — Рыба (+25 сытости)
  - `apple` — Яблоко (+15 сытости)
  - `cheese` — Сыр (+30 сытости)
  - `dried_meat` — Сушёное мясо (+35 сытости)
  - `berry` — Ягоды (+10 сытости)

## BUG 2: N+1 запросы в `get_seasonal_items` (ВЫСОКИЙ)
- **Файл:** `services/shop_service.py`
- **Проблема:** `get_seasonal_items` открывает DB-сессию, внутри цикла вызывает `_get_item_template()` который сам открывает отдельную DB-сессию для каждого товара. 3 товара × 3 запроса = 10 соединений вместо 1.
- **Исправление:** Заменён на один батч-запрос `SELECT ... WHERE item_id IN (...)` + маппинг шаблонов в словарь.

## BUG 3: `except Exception: pass` проглатывает ошибки (ВЫСОКИЙ)
- **Файлы:** `services/combat_service.py`, `services/movement_service.py`
- **Проблема:** Ошибки погодных и временных модификаторов боёв, а также проверки ночной встречи и парсинга JSON памяти NPC тихо игнорировались. Не видно, если добавлена новая погода или часовой период.
- **Исправление:** Заменено на `except Exception as e: logger.warning(f"...", exc_info=True)` во всех 4 местах:
  1. `combat_service.py:133` — Weather modifier
  2. `combat_service.py:144` — Time modifier
  3. `movement_service.py:60` — Night encounter check
  4. `movement_service.py:236` — NPC memory JSON parse
- Также добавлены `import logging` и `logger = logging.getLogger("MIST.movement")` в `movement_service.py`.

## BUG 4: NPC Scheduler использует системные часы вместо игрового (ВЫСОКИЙ)
- **Файл:** `handlers/npc.py`
- **Проблема:** `services.npc_scheduler.get_current_period()` без аргумента берёт `datetime.now().hour` — реальное время сервера, а не игровой час из WorldEngine. NPC засыпают/просыпаются по времени сервера, а не по игровому циклу.
- **Исправление:** `services.npc_scheduler.get_current_period(ws.get("game_hour"))` где `ws = services.world_engine.get_state()`.

## BUG 5: Китайские символы в UI (СРЕДНИЙ)
- **Файл:** `handlers/daily.py`
- **Проблема:** `Всего领取` — `领取` китайское слово, должно быть `получено`.
- **Исправление:** Заменено на `Всего получено`.

## BUG 6: `datetime.utcnow()` deprecated + timezone issues (СРЕДНИЙ)
- **Файл:** `services/daily_reward_service.py`
- **Проблема:** `datetime.utcnow()` возвращает timezone-naive datetime и deprecated с Python 3.12. На сервере в не-UTC часовом поясе расчёт `today` может быть смещён на 1 день.
- **Исправление:**
  - Добавлен `from datetime import datetime, timezone` на уровне модуля
  - Добавлен `EPOCH = datetime(2024, 1, 1, tzinfo=timezone.utc)` на уровне модуля
  - Заменены все `datetime.utcnow()` на `datetime.now(timezone.utc)`
  - Убраны inline-импорты `from datetime import datetime`

## BUG 7: Награда дня 7 повторяется бесконечно (СРЕДНИЙ)
- **Файл:** `services/daily_reward_service.py`
- **Проблема:** Когда игрок достигает стрик 7 и награждается снова на следующий день, `new_streak = min(7+1, 7) = 7` — стрик остаётся 7, и игрок получает награду дня 7 бесконечно, хотя сообщение говорит "цикл начинается заново".
- **Исправление:** `new_streak = record.streak + 1 if record.streak < 7 else 1` — после 7-го дня стрик сбрасывается до 1.

## BUG 8: Приватный атрибут `_state` вместо публичного API (НИЗКИЙ)
- **Файл:** `handlers/shop.py`
- **Проблема:** Две строки обращаются к `services.world_engine._state["season"]` напрямую, достигая в приватный атрибут. Существует публичный метод `get_state()`.
- **Исправление:** Заменено на `services.world_engine.get_state().get("season", "spring")`.

## BUG 9: `interval_seconds` vs `interval` в EcosystemService (ВЫСОКИЙ)
- **Файл:** `main.py`
- **Проблема:** `services.ecosystem.start_loop(interval_seconds=900)` — но `EcosystemService.start_loop` принимает параметр `interval`, а не `interval_seconds`. Python выбрасывает `TypeError` при каждом запуске бота.
- **Исправление:** Заменено на `services.ecosystem.start_loop(interval=900)`.

## BUG 10: `loc` может быть `None` в game.py (СРЕДНИЙ)
- **Файл:** `handlers/game.py`
- **Проблема:** При старте бота с устаревшей БД `user["current_location"]` может указывать на несуществующую локацию. `services.movement.get_location()` возвращает `None`, и обращение к `loc['name']` вызывает `TypeError`.
- **Исправление:** Во всех 7 местах где `loc` используется без проверки, добавлена обработка `None`:
  - `loc['name'] if loc else user['current_location']`
  - `loc.get('description', '') if loc else ''`
  - `loc.get("current_weather", "clear") if loc else "clear"`
  - `loc.get("connections", []) if loc else []`

## BUG 11: `timezone-aware` vs `timezone-naive` в `get_catchup_summary` (НИЗКИЙ)
- **Файл:** `services/player_service.py`
- **Проблема:** `datetime.now(timezone.utc)` (aware) минус `last_seen` из SQLite (naive) вызывает `TypeError: can't subtract offset-naive and offset-aware datetimes`.
- **Исправление:** Заменён `datetime.now(timezone.utc)` на `datetime.utcnow()` в `get_catchup_summary` для совместимости с timezone-naive SQLite датами.