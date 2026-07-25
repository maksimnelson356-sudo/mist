# MIST Changelog

## [0.5.1] - 2026-07-25 — Visual Assets

### Added
- services/visuals.py — менеджер визуальных ассетов: ASSET_MAP, get_asset_path(), send_visual()
- Отправка SVG/WebP ассетов как документов в Telegram (иконки квестов, эффектов, локаций)
- Интеграция визуала в handlers/quests.py: автоматическая отправка иконок при принятии и завершении квестов
- Структура assets/images/ — тайлы, иконки UI (game-icons.net), спрайты NPC

### Fixed
- services/quest_service.py — исправлен критический баг: переменная rewards не определялась в блоке if all_done
- Удалён лишний await db.commit() перед начислением наград в update_progress()

## [0.4.0] - 2026-07-25 — Genesis

### Added
- WorldStateModel — пульс мира в БД (game_day, hour, minute, season, world_pressure, prosperity...)
- WorldEngine — ядро живого мира: tick() каждые 15 минут, автономный цикл
- WorldEngine.tick() — +150 игровых минут за tick, смена дня/сезона
- WorldEngine._update_location_weather() — погода по локациям (Markov + seasonal bias)
- WorldEngine._on_season_change() — сезонные модификаторы параметров локаций
- WorldEngine.get_location_states() — чтение параметров всех локаций
- LocationModel — 10 новых колонок: danger_level, food_supply, tree_density, magic_level, creature_count, population, wealth, current_weather, current_event, reputation
- seed.py — стартовые параметры для 28 локаций
- WorldEventRecordModel — хранение событий мира в БД
- world_event_defs.py — 25 определений событий с вероятностями, эффектами, цепочками
- WorldEngine._generate_world_events() — генерация случайных событий по регионам
- WorldEngine._apply_event_effects() — применение эффектов к параметрам локаций
- WorldEngine._expire_events() — деактивация завершённых событий
- WorldEngine._trigger_chain_events() — цепные реакции между событиями
- WorldEngine._recalc_world_pressure() — пересчёт давления мира по активным событиям
- WorldEngine.get_active_events() — список активных событий
- WorldEngine.get_event_stats() — статистика событий
- WorldEngine.get_news() — сбор новостей за день
- /news — ежедневная газета мира: события, опасные локации, активные процессы
- PlayerService.get_catchup_summary() — сводка для вернувшихся игроков
- Catch-up блок в /start и main_menu — показывает что произошло пока отсутствовал
- WorldEngine.get_silence_whisper() — тихие шёпоты для дней без событий
- _on_new_day() — запись «тишина» в хронику если событий нет

## [0.5.0] - 2026-07-25 — Phase 2: Living World

### Added
- EcosystemService — экосистема мира: цепи питания, миграция, перенаселение
- ArtifactModel + ArtifactService — артефакты с историей, которая растёт с использованием
- GuildTerritoryService — гильдии захватывают локации, снижают опасность
- NPC-реакция на события — при пожаре NPC бегут, при эпидемии прячутся
- Миграция существ по сезонам — волки зимой в логове, осенью на луг
- Цепи питания — перенаселение → гибель, малочисленность → спавн
- 8 артефактов с уникальными историями (legendary, epic, rare, uncommon)
- Артефакты эволюционируют: +использований → новая лора

## [0.6.0] - 2026-07-25 — Expansion: Living World

### Added
- PlayerHomeModel + HomeService — система дома игрока (уровни, комнаты, настроение, реакция на события)
- 25 новых локаций: Туманная бухта, Шестерёнчатый город, Драконья вершина, Забытая библиотека, Хрустальное озеро, Костяная пустыня, Роща духов, Железная шахта, Лунная поляна, Штормовые утёсы, Древнее поле битвы, Туманная деревня, Теневая пропасть, Поля подсолнухов, Ржавые дocks, Шиповниковый лес, Пещеры эхов, Угольное болото, Долина падших звёзд, Морозная лощина, Золочёный собор, Шепчущий берег, Тухлый рынок
- 24 новых квеста на новые локации
- 11 новых секретов (Победитель драконов, Глубоководный, Странник пустоты, Сердце MIST, Мастер крафта, Лидер гильдии, Чемпион PvP, Домосед, Ночной странник, Охотник за тайнами, Повелитель шёпотов)
- Дом реагирует на мировые события: пожар → дым, наводнение → трещины, цветение → радость
- Дом меняется по времени: ночью спит, зимой боится, при низком HP восстанавливается

## [0.7.0] - 2026-07-25 — Living World Systems

### Added
- NPCLifeEngine — NPC живут автономно: цели по типу, relationships, рождение/смерть
- NPCRelationshipModel — отношения NPC (друг, враг, торговый партнёр, наставник)
- WorldMemoryModel + WorldMemoryService — следы действий игрока (постоянные + временные)
- GuildWarModel + GuildWarService — войны гильдий за территории
- NPCQuestService — NPC proactively дают квесты на основе типа и локации
- SeasonalQuestService — уникальные квесты по сезонам (8 квестов)
- WorldChronicleService — лента всей истории мира (по дням, локациям, игрокам)
- WorldBossModel + WorldBossService — 4 мировых босса (дракон, лич, кракен, теневой король)
- Боссы спавнятся по триггерам, респавнятся через 72ч, имеют фазы и лут

### Changed
- main.py — запуск WorldEngine loop при старте бота
- ServiceContainer — добавлен world_engine

## [0.3.0] - 2026-07-24

### Added
- MIST-016: Economy system (gems, tokens, EconomyService)
- MIST-017: Trading improvements (atomicity, cancel, UI)
- MIST-018: Guild roles (leader/officer/member), permissions, kick/promote
- MIST-019: Achievement auto-triggers, 13 new achievements (33 total)
- MIST-020: UI layer (keyboards, messages, formatter)
- MIST-021: Admin panel (level, gold, revive, teleport)
- MIST-022: Game configuration (no magic numbers)
- MIST-023: Logging with correlation IDs
- MIST-024: Analytics service
- MIST-025: Test conftest, admin tests
- MIST-026: Security (validation, input sanitization)
- MIST-027: Save service (world stats)
- MIST-028: Localization (RU/EN)
- MIST-029: Build/release scripts
- MIST-030: Documentation (ARCHITECTURE, GAME_RULES, DEV_STANDARDS)

### Fixed
- LEGEND_DISCOVERED EventType missing in quest_service.py
- Trade completed_at always set to None
- handlers/trade.py was empty (2 lines)
- handlers/combat.py was empty

### Changed
- UserModel: added gems, tokens fields
- AchievementService: added auto-trigger methods (on_kill, on_level_up, etc.)
- GuildService: added set_role, kick, promote, check_permission
- TradeService: added cancel method
- EventType: added LEGEND_DISCOVERED, NPC_TRADED, NPC_GREETED, ECONOMY_TRANSACTION, GUILD_ROLE_CHANGED

## [0.2.0] - 2026-07-24

### Added
- MIST-010: Items (CatalogService, rarity weights)
- MIST-011: Inventory enhancements
- MIST-012: Weather system (5 states)
- MIST-013: Time system (4 periods)
- MIST-014: World events (5 types)
- MIST-015: Quest engine (6 quest types)

## [0.1.0] - 2026-07-24

### Added
- MIST-001: Project setup (Clean Architecture)
- MIST-002: Database layer (SQLAlchemy async)
- MIST-003: Event system (ChronicleEvent)
- MIST-004: Player core (PlayerService, ProfileService, ReputationService)
- MIST-005: World model (Continent → Region → Location → POI)
- MIST-006: Combat system
- MIST-007: Exploration
- MIST-008: NPC framework
- MIST-009: NPC memory
