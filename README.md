# MIST

Telegram RPG бот с живым миром, квестами, PvP и гильдиями.

**Версия**: 0.7.0  
**Движок**: SQLite + SQLAlchemy async + aiosqlite  
**Бот**: aiogram 3.12

---

## Быстрый старт

```bash
pip install -r requirements.txt
# Создайте .env с BOT_TOKEN и ADMIN_IDS
python seed.py
python main.py
```

## Структура

```
mist/
├── main.py                 # точка входа
├── config.py               # конфигурация
├── scenes.py               # ASCII-арт сцены
├── seed.py                 # заполнение БД
├── domain/events/          # ChronicleEvent, EventType
├── database/models/        # 31 SQLAlchemy модель
├── services/               # бизнес-логика (quest_service, visuals, world_engine...)
├── handlers/               # хендлеры Telegram (quests, movement, combat...)
├── assets/images/          # SVG/WebP иконки (game-icons.net, lorc, skoll)
└── tests/                  # тесты
```

## Визуальные ассеты

Система `services/visuals.py` — маппинг ключей на SVG-иконки в `assets/images/`.

| Ключ | Файл | Описание |
|------|------|----------|
| `quest_accept` | `abstract-001.svg` | Принятие квеста |
| `quest_complete` | `achievement.svg` | Завершение квеста |
| `level_up` | `abstract-002.svg` | Повышение уровня |
| `effect_fire` | `fire.svg` | Огонь |
| `effect_heal` | `water-drop.svg` | Лечение |

Источники иконок:
- [game-icons.net](https://game-icons.net/) — CC BY 3.0
- Kenney — CC0

## Системы

- **WorldEngine** — автономный мир: погода, время, сезонные события
- **Quest Engine** — 28 квестов, 6 типов, прогресс и награды
- **PvP** — дуэли и рейды
- **Гильдии** — создание, роли, квесты гильдий
- **Хроника** — ChronicleEvent шина для всех событий мира

---

*GitHub: [maksimnelson356-sudo/mist](https://github.com/maksimnelson356-sudo/mist)*
