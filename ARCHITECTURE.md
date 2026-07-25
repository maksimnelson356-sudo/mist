# MIST — Архитектура

## Обзор

Telegram RPG бот MIST — Clean Architecture с ChronicleEvent как центральной шиной событий.
Мир живёт автономно: WorldEngine тикает каждые 15 минут, меняя время, погоду и состояние локаций.

**Версия**: 0.7.0 (Living World Systems)  
**Движок**: SQLite + SQLAlchemy async + aiosqlite  
**Бот**: aiogram 3.12

---

## Структура проекта

```
mist-master/
├── main.py                          # точка входа
├── config.py                        # конфигурация + игровые настройки
├── scenes.py                        # ASCII-арт сцены
├── seed.py                          # заполнение БД
├── requirements.txt                 # зависимости
│
├── domain/events/
│   ├── types.py                     # EventType (45 типов), Importance (5 уровней)
│   └── chronicle.py                 # ChronicleEvent dataclass
│
├── database/
│   ├── base.py                      # async engine, sessionmaker
│   ├── models/                      # 31 SQLAlchemy моделей
│   │   ├── user.py                  # UserModel (gold, gems, tokens)
│   │   ├── continent.py             # ContinentModel
│   │   ├── region.py                # RegionModel
│   │   ├── location.py              # LocationModel (UUID, coords, danger, food, magic...)
│   │   ├── poi.py                   # POIModel
│   │   ├── creature.py              # CreatureModel
│   │   ├── npc.py                   # NPCModel (types, states)
│   │   ├── npc_memory.py            # NPCMemoryModel (relation)
│   │   ├── exploration.py           # ExplorationModel
│   │   ├── item.py                  # ItemTemplateModel, GroundItemModel, SecretModel
│   │   ├── inventory.py             # InventoryModel, UserEquipmentModel, UserStatusEffectModel
│   │   ├── quest.py                 # QuestModel, UserQuestModel, WorldEventModel, LegendModel
│   │   ├── combat.py                # CombatLogModel, BossSpawnModel
│   │   ├── guild.py                 # GuildModel, GuildMemberModel
│   │   ├── trade.py                 # PlayerTradeModel
│   │   ├── achievement.py           # AchievementModel, UserAchievementModel
│   │   ├── daily.py                 # DailyQuestModel
│   │   ├── shop.py                  # ShopItemModel
│   │   ├── crafting.py              # CraftingRecipeModel, UserCraftingModel
│   │   ├── chronicle.py             # ChronicleEventModel
│   │   ├── analytics.py             # AnalyticsEventModel
│   │   ├── world_state.py           # WorldStateModel (пульс мира)
│   │   ├── world_event_record.py    # WorldEventRecordModel (события в БД)
│   │   ├── artifact.py              # ArtifactModel (артефакты с историей)
│   │   ├── player_home.py           # PlayerHomeModel (дом игрока)
│   │   ├── npc_relationship.py      # NPCRelationshipModel (отношения NPC)
│   │   ├── world_memory.py          # WorldMemoryModel (следы действий)
│   │   ├── guild_war.py             # GuildWarModel (войны гильдий)
│   │   └── world_boss.py            # WorldBossModel (мировые боссы)
│   └── repositories/                # 18 репозиториев
│
├── services/                        # 43 сервиса
│   ├── container.py                 # ServiceContainer
│   ├── chronicle_service.py         # publish(), get_latest()
│   ├── player_service.py            # get_or_create(), get()
│   ├── profile_service.py           # get_profile()
│   ├── reputation_service.py        # get_level()
│   ├── movement_service.py          # move(), get_location()
│   ├── combat_service.py            # start(), resolve()
│   ├── quest_service.py             # accept(), update_progress()
│   ├── quest_engine.py              # get, accept, complete
│   ├── inventory_service.py         # add(), remove(), get()
│   ├── shop_service.py              # buy(), sell()
│   ├── equipment_service.py         # equip(), unequip()
│   ├── pvp_service.py               # battle(), get_stats()
│   ├── guild_service.py             # create(), join(), leave(), set_role(), kick(), promote()
│   ├── trade_service.py             # create(), accept(), decline(), cancel()
│   ├── achievement_service.py       # check(), on_kill(), on_level_up(), ...
│   ├── daily_service.py             # get_or_create(), update_progress()
│   ├── crafting_service.py          # get_recipes(), craft()
│   ├── npc_service.py               # get(), get_at_location()
│   ├── npc_memory_service.py        # get_relation(), update_relation()
│   ├── npc_scheduler.py             # get_current_period()
│   ├── exploration_service.py       # discover(), get_visited()
│   ├── catalog_service.py           # get_item_value(), search()
│   ├── economy_service.py           # get_balance(), add(), remove(), transfer()
│   ├── admin_service.py             # set_level(), set_gold(), revive(), teleport()
│   ├── analytics_service.py         # track(), get_count()
│   ├── save_service.py              # get_world_stats()
│   ├── weather_system.py            # set_weather(), tick()
│   ├── time_system.py               # set_time(), get_current_time()
│   ├── world_event_system.py        # start(), end(), tick()
│   ├── world_event_defs.py          # 25 определений событий
│   ├── world_engine.py              # tick(), get_state(), start_loop(), generate_world_events() — ядро живого мира
│   ├── ecosystem_service.py         # экосистема: цепи питания, миграция, спавн
│   ├── artifact_service.py          # артефакты с растущей историей
│   ├── guild_territory.py           # захват локаций гильдиями
│   ├── home_service.py              # дом игрока (уровни, комнаты, настроение)
│   ├── npc_life_engine.py           # NPC Life Engine (отношения, рождение/смерть, цели)
│   ├── world_memory_service.py      # следы действий игрока
│   ├── guild_war_service.py         # войны гильдий за территории
│   ├── npc_quest_service.py         # NPC proactively дают квесты
│   ├── seasonal_quest_service.py    # квесты по сезонам
│   ├── world_chronicle_service.py   # лента всей истории
│   └── world_boss_service.py        # мировые боссы (дракон, лич, кракен, тень)
│
├── handlers/                        # 16 хэндлеров
│   ├── game.py                      # старт, осмотр, движение
│   ├── commands.py                  # /help, /status
│   ├── admin.py                     # /admin_level, /admin_gold, /admin_revive, /admin_tp
│   ├── combat.py                    # (бой в game.py)
│   ├── quests.py                    # квесты
│   ├── shop.py                      # магазин
│   ├── pvp.py                       # PvP арена
│   ├── crafting.py                  # крафт
│   ├── guild.py                     # гильдии + roles/kick/promote
│   ├── trade.py                     # трейдинг UI
│   ├── equipment.py                 # экипировка
│   ├── achievements.py              # достижения
│   ├── daily.py                     # ежедневные квесты
│   ├── npc.py                       # NPC взаимодействие
│   ├── exploration.py               # исследования
│   └── whisper.py                   # шёпот тумана
│
├── ui/                              # UI компоненты
│   ├── keyboards.py                 # генератор клавиатур
│   ├── messages.py                  # шаблоны сообщений
│   └── formatter.py                 # форматирование (HP/XP бары, иконки)
│
├── utils/                           # Утилиты
│   ├── logger.py                    # логирование с correlation ID
│   ├── correlation.py               # генерация correlation ID
│   └── validation.py                # валидация ввода, sanitize
│
├── locale/                          # Локализация
│   ├── ru.json                      # русский
│   └── en.json                      # английский
│
├── tests/                           # 72 теста
│   ├── conftest.py                  # фикстуры
│   ├── test_player_core.py          # 5 тестов
│   ├── test_world_model.py          # 9 тестов
│   ├── test_npc_exploration.py      # 11 тестов
│   ├── test_game_systems.py         # 14 тестов
│   ├── test_economy.py              # 11 тестов
│   ├── test_ui.py                   # 19 тестов
│   └── test_admin.py                # 3 теста
│
├── scripts/
│   └── build.py                     # скрипт сборки
│
├── docs/
│   ├── GAME_RULES.md                # игровые правила
│   └── DEV_STANDARDS.md             # стандарты разработки
│
├── CHANGELOG.md                     # история версий
├── ARCHITECTURE.md                  # этот файл
└── SMOKE_TEST.md                    # результаты тестирования
```

---

## Модели (25)

```
database/models/
├── user.py                  # UserModel (gold, gems, tokens)
├── continent.py             # ContinentModel
├── region.py                # RegionModel
├── location.py              # LocationModel (UUID, coords, danger, food, magic, weather...)
├── poi.py                   # POIModel
├── creature.py              # CreatureModel
├── npc.py                   # NPCModel (types, states)
├── npc_memory.py            # NPCMemoryModel (relation)
├── exploration.py           # ExplorationModel
├── item.py                  # ItemTemplateModel, GroundItemModel, SecretModel
├── inventory.py             # InventoryModel, UserEquipmentModel, UserStatusEffectModel
├── quest.py                 # QuestModel, UserQuestModel, WorldEventModel, LegendModel
├── combat.py                # CombatLogModel, BossSpawnModel
├── guild.py                 # GuildModel, GuildMemberModel
├── trade.py                 # PlayerTradeModel
├── achievement.py           # AchievementModel, UserAchievementModel
├── daily.py                 # DailyQuestModel
├── shop.py                  # ShopItemModel
├── crafting.py              # CraftingRecipeModel, UserCraftingModel
├── chronicle.py             # ChronicleEventModel
├── analytics.py             # AnalyticsEventModel
├── world_state.py           # WorldStateModel (пульс мира)
└── world_event_record.py    # WorldEventRecordModel (события мира в БД)
```

---

## Сервисы (31)

```
services/
├── container.py             # ServiceContainer
├── chronicle_service.py     # publish(), get_latest()
├── player_service.py        # get_or_create(), get()
├── profile_service.py       # get_profile()
├── reputation_service.py    # get_level()
├── movement_service.py      # move(), get_location()
├── combat_service.py        # start(), resolve()
├── quest_service.py         # accept(), update_progress()
├── quest_engine.py          # get, accept, complete
├── inventory_service.py     # add(), remove(), get()
├── shop_service.py          # buy(), sell()
├── equipment_service.py     # equip(), unequip()
├── pvp_service.py           # battle(), get_stats()
├── guild_service.py         # create(), join(), leave(), set_role(), kick(), promote()
├── trade_service.py         # create(), accept(), decline(), cancel()
├── achievement_service.py   # check(), on_kill(), on_level_up(), ...
├── daily_service.py         # get_or_create(), update_progress()
├── crafting_service.py      # get_recipes(), craft()
├── npc_service.py           # get(), get_at_location()
├── npc_memory_service.py    # get_relation(), update_relation()
├── npc_scheduler.py         # get_current_period()
├── exploration_service.py   # discover(), get_visited()
├── catalog_service.py       # get_item_value(), search()
├── economy_service.py       # get_balance(), add(), remove(), transfer()
├── admin_service.py         # set_level(), set_gold(), revive(), teleport()
├── analytics_service.py     # track(), get_count()
├── save_service.py          # get_world_stats()
├── weather_system.py        # set_weather(), tick()
├── time_system.py           # set_time(), get_current_time()
├── world_event_system.py    # start(), end(), tick()
├── world_event_defs.py      # 25 определений событий (вероятности, эффекты, цепочки)
├── world_engine.py          # tick(), start_loop(), generate_world_events() — ядро живого мира
├── ecosystem_service.py     # экосистема: цепи питания, миграция, спавн
├── artifact_service.py      # артефакты с растущей историей
├── guild_territory.py       # захват локаций гильдиями
├── home_service.py          # дом игрока (уровни, комнаты, настроение)
├── npc_life_engine.py       # NPC Life Engine (отношения, рождение/смерть, цели)
├── world_memory_service.py  # следы действий игрока
├── guild_war_service.py     # войны гильдий за территории
├── npc_quest_service.py     # NPC proactively дают квесты
├── seasonal_quest_service.py # квесты по сезонам
├── world_chronicle_service.py # лента всей истории
└── world_boss_service.py    # мировые боссы
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

## Запуск

```bash
pip install -r requirements.txt
python seed.py
python main.py
```
