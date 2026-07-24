# MIST Changelog

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
