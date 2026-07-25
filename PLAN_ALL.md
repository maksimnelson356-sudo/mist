# MIST — Полный план реализации (MIST-001 → MIST-030 + Genesis)

**Дата**: 2026-07-25
**Статус**: ✅ Все 30 модулей + Genesis (G1-G6) + Phase 2 (Living World)
**Тесты**: 72/72 проходят

---

## Phase 2 — Living World

Мир оживает: NPC ходят, экосистема работает, гильдии захватывают, артефакты растут.

| Компонент | Описание | Статус |
|---|---|---|
| EcosystemService | Цепи питания, миграция, спавн | ✅ |
| NPC-реакция | Побег при пожаре, прячутся при эпидемии | ✅ |
| GuildTerritory | Захват локаций, снижение опасности | ✅ |
| ArtifactService | Артефакты с растущей историей | ✅ |
| NPC-мigrationBuilder | Использует игровое время | ✅ |

### Что работает (Genesis G1-G6) ✅

- **WorldStateModel** — пульс мира в БД: день, час, сезон, давление, процветание
- **WorldEngine.tick()** — каждые 15 минут: +150 игровых минут, смена дня/сезона
- **Параметры локаций** — 28 локаций с danger, food, tree_density, magic, creatures, population, wealth
- **Погода по локациям** — Markov-цепь с seasonal bias (зимой чаще снег)
- **Сезонные модификаторы** — зимой food -25%, летом food +15%
- **Хроника** — записи при новом дне и смене сезона
- **25 определений событий** — лесные пожары, миграция волков, засуха, эпидемии, аномалии, артефакты...
- **Цепные реакции** — лесной пожар → беженцы, засуха → голод → бандиты
- **Вероятностная генерация** — события появляются с шансом 1-12% за тик по региону
- **Эффекты на локации** — каждое событие меняет параметры (danger, food, wealth, magic...)
- **Хранение в БД** — WorldEventRecordModel с start_day, end_day, chain_events
- **World pressure** — пересчёт давления мира по количеству активных событий
- **/news** — ежедневная газета: события дня, активные процессы, опасные локации
- **Catch-up** — при входе: «Пока тебя не было: 3 дн. Лесной пожар, засуха...»
- **Тишина мира** — дни без событий: «Ничего особенного не произошло.»

### Масштаб

| Компонент | До Genesis | После Genesis |
|---|---|---|
| SQLAlchemy модели | 23 | 25 |
| Сервисы | 30 | 32 |
| Параметры локаций | 0 | 10 |
| WorldEngine tick | — | ✅ (15 мин) |
| Определения событий | 0 | 25 |
| Команды бота | 8 | 9 |

---

## Статус по модулям

| # | Модуль | Название | Статус | Файлы |
|---|---|---|---|---|
| 001 | Project Setup | Структура каталогов | ✅ | main.py, config.py, requirements.txt |
| 002 | Database Layer | SQLAlchemy async | ✅ | database/base.py, database/__init__.py |
| 003 | Event System | ChronicleEvent | ✅ | domain/events/types.py, chronicle.py |
| 004 | Player Core | Player/Profile/Reputation | ✅ | player_service.py, profile_service.py, reputation_service.py |
| 005 | World Model | Continent→Region→Location→POI | ✅ | continent.py, region.py, location.py, poi.py, world_generator.py |
| 006 | Combat System | PvE бой | ✅ | combat_service.py, combat.py model |
| 007 | Exploration | Исследование локаций | ✅ | exploration_service.py, exploration.py model |
| 008 | NPC Framework | NPC типы/состояния | ✅ | npc_service.py, npc_scheduler.py, npc.py model |
| 009 | NPC Memory | Память NPC | ✅ | npc_memory_service.py, npc_memory.py model |
| 010 | Items (Catalog) | Каталог предметов | ✅ | catalog_service.py, item.py model |
| 011 | Inventory | Инвентарь/экипировка | ✅ | inventory_service.py, inventory.py model |
| 012 | Weather System | Погода (5 состояний) | ✅ | weather_system.py |
| 013 | Time System | Игровое время | ✅ | time_system.py |
| 014 | World Events | Мировые события | ✅ | world_event_system.py |
| 015 | Quest Engine | Движок квестов | ✅ | quest_engine.py |
| 016 | Economy | Валюты (gold/gems/tokens) | ✅ | economy_service.py |
| 017 | Trading | Трейдинг игроков | ✅ | trade_service.py, handlers/trade.py |
| 018 | Guild System | Гильдии + роли | ✅ | guild_service.py, handlers/guild.py |
| 019 | Achievements | Достижения (33 шт) | ✅ | achievement_service.py |
| 020 | Telegram UI | UI слой | ✅ | ui/keyboards.py, messages.py, formatter.py |
| 021 | Admin Panel | Админ панель | ✅ | admin_service.py, handlers/admin.py |
| 022 | Configuration | Конфигурация | ✅ | config.py |
| 023 | Logging | Логирование | ✅ | utils/logger.py, correlation.py |
| 024 | Analytics | Аналитика | ✅ | analytics_service.py, analytics.py model |
| 025 | Testing | Тесты | ✅ | tests/conftest.py |
| 026 | Security | Безопасность | ✅ | utils/validation.py |
| 027 | Save System | Сохранение | ✅ | save_service.py |
| 028 | Localization | Локализация (RU/EN) | ✅ | locale/ru.json, en.json, utils/translator.py |
| 029 | Release Pipeline | Релиз | ✅ | scripts/build.py, CHANGELOG.md |
| 030 | Design Bible | Документация | ✅ | docs/GAME_RULES.md, DEV_STANDARDS.md |

---

## Статистика

| Компонент | Количество |
|---|---|
| SQLAlchemy модели | 24 |
| Сервисы | 31 |
| Хэндлеры | 16 |
| UI компоненты | 3 |
| Утилиты | 3 |
| EventType | 45 |
| Importance уровней | 5 |
| Достижения | 33 |
| Тесты | 72 |
| Языка локализации | 2 |
| Параметры локаций | 10 |

---

## Структура проекта

```
mist-master/
├── main.py
├── config.py                         # BOT_TOKEN, DB_PATH, игровые настройки
├── scenes.py
├── seed.py
├── requirements.txt
│
├── domain/events/
│   ├── types.py                      # EventType (45), Importance (5)
│   └── chronicle.py                  # ChronicleEvent dataclass
│
├── database/
│   ├── base.py
│   ├── models/                       # 24 модели
│   │   ├── user.py                   # gold, gems, tokens
│   │   ├── continent.py, region.py, location.py, poi.py
│   │   ├── creature.py, npc.py, npc_memory.py, exploration.py
│   │   ├── item.py, inventory.py
│   │   ├── quest.py, combat.py
│   │   ├── guild.py, trade.py
│   │   ├── achievement.py, daily.py, shop.py, crafting.py
│   │   ├── chronicle.py, analytics.py
│   │   ├── world_state.py            # пульс мира (Genesis)
│   │   └── ...
│   └── repositories/                 # 18 репозиториев
│
├── services/                         # 31 сервис
│   ├── container.py                  # ServiceContainer
│   ├── chronicle_service.py
│   ├── player_service.py, profile_service.py, reputation_service.py
│   ├── movement_service.py, combat_service.py
│   ├── quest_service.py, quest_engine.py
│   ├── inventory_service.py, shop_service.py, equipment_service.py
│   ├── pvp_service.py, guild_service.py, trade_service.py
│   ├── achievement_service.py, daily_service.py, crafting_service.py
│   ├── npc_service.py, npc_memory_service.py, npc_scheduler.py
│   ├── exploration_service.py, catalog_service.py
│   ├── economy_service.py, admin_service.py, analytics_service.py, save_service.py
│   ├── weather_system.py, time_system.py, world_event_system.py
│   ├── world_engine.py               # ядро живого мира (Genesis)
│   └── world_generator.py
│
├── handlers/                         # 16 хэндлеров
│   ├── game.py, commands.py, admin.py
│   ├── combat.py, quests.py, shop.py, pvp.py
│   ├── crafting.py, guild.py, trade.py, equipment.py
│   ├── achievements.py, daily.py, npc.py, exploration.py, whisper.py
│
├── ui/
│   ├── keyboards.py
│   ├── messages.py
│   └── formatter.py
│
├── utils/
│   ├── logger.py
│   ├── correlation.py
│   └── validation.py
│
├── locale/
│   ├── ru.json
│   └── en.json
│
├── tests/                            # 72 теста
│   ├── conftest.py
│   ├── test_player_core.py           # 5
│   ├── test_world_model.py           # 9
│   ├── test_npc_exploration.py       # 11
│   ├── test_game_systems.py          # 14
│   ├── test_economy.py               # 11
│   ├── test_ui.py                    # 19
│   └── test_admin.py                 # 3
│
├── scripts/build.py
├── docs/GAME_RULES.md, DEV_STANDARDS.md
├── CHANGELOG.md
├── ARCHITECTURE.md
└── PLAN_ALL.md                       # этот файл
```

---

## Сервисы (Container)

```python
services.chronicle      # ChronicleService
services.player         # PlayerService
services.profile        # ProfileService
services.reputation     # ReputationService
services.movement       # MovementService
services.combat         # CombatService
services.quest          # QuestService
services.quest_engine   # QuestEngine
services.inventory      # InventoryService
services.shop           # ShopService
services.equipment      # EquipmentService
services.pvp            # PvPService
services.guild          # GuildService
services.trade          # TradeService
services.achievement    # AchievementService
services.daily          # DailyService
services.crafting       # CraftingService
services.npc            # NPCService
services.npc_memory     # NPCMemoryService
services.npc_scheduler  # NPCScheduler
services.exploration    # ExplorationService
services.catalog        # CatalogService
services.economy        # EconomyService
services.admin          # AdminService
services.analytics      # AnalyticsService
services.save           # SaveService
services.weather        # WeatherSystem
services.time           # TimeSystem
services.world_events   # WorldEventSystem
```

---

## EventType (45)

```
COMBAT_VICTORY, COMBAT_DEFEAT, COMBAT_DRAW
LOCATION_DISCOVERED, LOCATION_VISITED
QUEST_ACCEPTED, QUEST_COMPLETED
ITEM_OBTAINED, ITEM_USED, ITEM_SOLD, ITEM_BOUGHT
PLAYER_LEVEL_UP, PLAYER_DEATH, PLAYER_REVIVE, PLAYER_REST
NPC_KILLED, NPC_TALKED, NPC_TRADED, NPC_GREETED
PVP_WIN, PVP_LOSS, PVP_DRAW
TRADE_COMPLETED, TRADE_CREATED
GUILD_CREATED, GUILD_JOINED, GUILD_LEFT, GUILD_DONATED, GUILD_ROLE_CHANGED
CRAFT_COMPLETED
SECRET_FOUND
ACHIEVEMENT_UNLOCKED, ACHIEVEMENT_PROGRESS
WORLD_EVENT
WHISPER
DAILY_COMPLETED
EQUIPMENT_CHANGED
NEW_USER
REPUTATION_CHANGED
PLAYER_RENAMED
LEGEND_DISCOVERED
ECONOMY_TRANSACTION
```

---

## Достижения (33)

### Combat (5)
- first_blood — Первая кровь (1 kill)
- monster_hunter — Охотник (10 kills)
- slayer — Бог убийств (50 kills)
- kill_100 — Мясник (100 kills)
- kill_500 — Палач (500 kills)
- boss_killer — Убийца боссов (1 boss)

### Explore (4)
- explorer_5 — Исследователь (5 локаций)
- explorer_15 — Странник (15 локаций)
- explorer_25 — Первооткрыватель (25 локаций)
- explorer_all — Повелитель тумана (28 локаций, секрет)

### Quests (2)
- quest_5 — Исполнитель (5 квестов)
- quest_all — Хранитель слов (28 квестов, секрет)

### Progress (5)
- level_5 — Новичок
- level_10 — Воин
- level_20 — Легенда
- level_30 — Ветеран
- level_50 — Бессмертный (секрет)

### Wealth (3)
- gold_500 — Скупщик
- gold_5000 — Торговец
- gold_10000 — Магнат

### Craft (3)
- craft_3 — Ремесленник
- craft_10 — Мастер
- craft_50 — Легенда ремесла (секрет)

### PvP (3)
- pvp_5 — Гладиатор
- pvp_10 — Боец
- pvp_50 — Чемпион

### Social (3)
- npc_talk_10 — Знакомец
- npc_trade_20 — Торговец
- social_butterfly — Душа компании

### General (2)
- equipped — Экипирован
- first_day — Первый день
- week_survivor — Выживший

---

## Исправленные баги

1. `quest_service.py:259` — `EventType.LEGEND_DISCOVERED` не существовал → добавлен
2. `trade_service.py:146` — `completed_at` всегда None → исправлено на `datetime.utcnow()`
3. `handlers/trade.py` — был пустой (2 строки) → заполнен UI
4. `ARCHITECTURE.md` — устаревшие данные → обновлен

---

## Зависимости

```
aiogram==3.12.0
aiosqlite==0.20.0
sqlalchemy[asyncio]==2.0.36
python-dotenv==1.0.1
```

---

## Запуск

```bash
pip install -r requirements.txt
python seed.py
python main.py
```
