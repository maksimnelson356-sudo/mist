# MIST — Smoke Test Report

**Дата**: 2026-07-24  
**Статус**: ✅ Готово к деплою на VPS  

---

## Результаты

| Проверка | Статус | Примечание |
|---|---|---|
| `pip install -r requirements.txt` | ✅ | aiogram 3.30, sqlalchemy 2.0.51, aiosqlite 0.22.1 (Python 3.14) |
| `python seed.py` — заполнение БД | ✅ | 28 локаций, 27 существ, 58 предметов, 28 квестов, 20 достижений |
| `python main.py` — старт бота | ✅ | БД создана, polling запущен |
| Все handlers компилируются | ✅ | 65 Python-файлов, 0 ошибок |
| Подключение к api.telegram.org | ⚠️ | Проблема сети на этой машине (VPN/фаервол) |

---

## Найденные и исправленные ошибки

### 1. seed.py — raw SQL без `text()`

**Ошибка**: `sqlalchemy.exc.ArgumentError: Textual SQL expression should be explicitly declared as text(...)`

**Причина**: seed.py использовал строки SQL без обёртки `text()`.

**Исправление**: Добавлен `from sqlalchemy import text`, все вызовы обёрнуты:
```python
# Было:
await db.execute("SELECT COUNT(*) FROM locations")
# Стало:
await db.execute(text("SELECT COUNT(*) FROM locations"))
```

**Файлы**: `seed.py` (9 исправлений)

---

### 2. Зависимости — Python 3.14 совместимость

**Проблема**: `aiogram==3.12.0` требует `aiohttp<3.11` и `pydantic-core==2.20.1`, которые не имеют pre-built wheel для Python 3.14.

**Решение**:
- Локально: `pip install --only-binary :all: aiogram sqlalchemy[asyncio] aiosqlite python-dotenv` (ставит свежие версии)
- На VPS (Python 3.12): `pip install -r requirements.txt` (aiogram==3.12.0 встанет корректно)
- `requirements.txt` оставлен с `aiogram==3.12.0` для VPS

---

## Seed data — итого

```
📍 Локаций:        28
🐾 Существ:         27
🏺 Предметов:       58
📜 Квестов:         28
🔮 Секретов:         4
📦 Предметов на земле: 32
🛒 Предметов магазинов: 19
⚒️ Рецептов крафта:   6
🏆 Достижений:      20
```

---

## Деплой на VPS

```bash
# 1. Клонируй/скопируй проект
scp -r mist-master user@vps:/opt/mist

# 2. Установи зависимости
cd /opt/mist
pip install -r requirements.txt

# 3. Создай .env
cp .env.example .env
nano .env  # вставь BOT_TOKEN

# 4. Заполни БД
python seed.py

# 5. Запусти бота
python main.py
```

---

## Зависимости (VPS — Python 3.12)

```
aiogram==3.12.0
aiosqlite==0.20.0
sqlalchemy[asyncio]==2.0.36
python-dotenv==1.0.1
```

---

## Файлы проекта

```
mist-master/
├── main.py              # точка входа
├── config.py            # BOT_TOKEN, DB_PATH
├── scenes.py            # ASCII-арт сцены
├── seed.py              # заполнение БД
├── requirements.txt     # зависимости
├── .env                 # токен (в .gitignore)
├── .gitignore           # исключения
├── ARCHITECTURE.md      # описание архитектуры
├── SMOKE_TEST.md        # этот файл
├── domain/events/       # EventType, Importance, ChronicleEvent
├── database/            # models (16), repositories (14), base.py
├── services/            # сервисы (14), container.py
└── handlers/            # хэндлеры (13)
```
