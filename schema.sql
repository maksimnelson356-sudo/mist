-- MIST: Схема базы данных (SQLite)
-- Вселенная, которая помнит ВСЁ

-- Пользователи
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    display_name TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    current_location TEXT DEFAULT 'dark_forest',
    memories INTEGER DEFAULT 0,
    karma INTEGER DEFAULT 0,
    days_in_mist INTEGER DEFAULT 0,
    is_alive INTEGER DEFAULT 1,
    extra_data TEXT DEFAULT '{}',
    hp INTEGER DEFAULT 100,
    max_hp INTEGER DEFAULT 100,
    attack INTEGER DEFAULT 10,
    defense INTEGER DEFAULT 5,
    level INTEGER DEFAULT 1,
    xp INTEGER DEFAULT 0,
    gold INTEGER DEFAULT 0,
    pvp_wins INTEGER DEFAULT 0,
    pvp_losses INTEGER DEFAULT 0,
    pvp_rating INTEGER DEFAULT 1000
);

-- Инвентарь
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(user_id),
    item_id TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    is_magic INTEGER DEFAULT 0,
    enchantments TEXT DEFAULT '{}',
    created_at TEXT DEFAULT (datetime('now'))
);

-- Все действия (память мира)
CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(user_id),
    action_type TEXT NOT NULL,
    action_data TEXT DEFAULT '{}',
    location TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Локации
CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    discovered INTEGER DEFAULT 0,
    discovered_by INTEGER REFERENCES users(user_id),
    discovered_at TEXT,
    connections TEXT DEFAULT '[]',
    state_data TEXT DEFAULT '{}',
    is_secret INTEGER DEFAULT 0,
    required_karma INTEGER DEFAULT 0
);

-- Существа
CREATE TABLE IF NOT EXISTS creatures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creature_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    location TEXT,
    disposition TEXT DEFAULT 'neutral',
    memory_with_users TEXT DEFAULT '{}',
    is_alive INTEGER DEFAULT 1,
    spawn_data TEXT DEFAULT '{}',
    hp INTEGER DEFAULT 50,
    max_hp INTEGER DEFAULT 50,
    attack INTEGER DEFAULT 8,
    defense INTEGER DEFAULT 3,
    xp_reward INTEGER DEFAULT 20,
    loot_table TEXT DEFAULT '[]'
);

-- Секреты и тайны
CREATE TABLE IF NOT EXISTS secrets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    secret_id TEXT UNIQUE NOT NULL,
    secret_type TEXT NOT NULL,
    name TEXT,
    description TEXT,
    trigger_condition TEXT DEFAULT '{}',
    reward TEXT DEFAULT '{}',
    discovered_by INTEGER REFERENCES users(user_id),
    discovered_at TEXT,
    is_active INTEGER DEFAULT 1
);

-- Мировые события
CREATE TABLE IF NOT EXISTS world_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    name TEXT,
    description TEXT,
    trigger_time TEXT,
    duration_minutes INTEGER DEFAULT 60,
    is_active INTEGER DEFAULT 0,
    affected_locations TEXT DEFAULT '[]',
    event_data TEXT DEFAULT '{}',
    created_at TEXT DEFAULT (datetime('now'))
);

-- Предметы
CREATE TABLE IF NOT EXISTS item_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    rarity TEXT DEFAULT 'common',
    is_usable INTEGER DEFAULT 0,
    use_effect TEXT DEFAULT '{}',
    lore TEXT
);

-- Квесты
CREATE TABLE IF NOT EXISTS quests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quest_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    giver TEXT,
    location TEXT,
    requirements TEXT DEFAULT '{}',
    objectives TEXT DEFAULT '[]',
    rewards TEXT DEFAULT '{}',
    is_active INTEGER DEFAULT 1,
    is_repeating INTEGER DEFAULT 0,
    cooldown_hours INTEGER DEFAULT 0
);

-- Прогресс квестов
CREATE TABLE IF NOT EXISTS user_quests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(user_id),
    quest_id TEXT REFERENCES quests(quest_id),
    status TEXT DEFAULT 'active',
    progress TEXT DEFAULT '{}',
    started_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT,
    UNIQUE(user_id, quest_id)
);

-- Бои
CREATE TABLE IF NOT EXISTS combat_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(user_id),
    creature_id TEXT,
    result TEXT NOT NULL,
    damage_dealt INTEGER DEFAULT 0,
    damage_taken INTEGER DEFAULT 0,
    xp_gained INTEGER DEFAULT 0,
    loot_dropped TEXT DEFAULT '[]',
    duration_seconds INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Легенды
CREATE TABLE IF NOT EXISTS legends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    legend_id TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    discovered_by INTEGER REFERENCES users(user_id),
    discovered_at TEXT,
    times_discovered INTEGER DEFAULT 0
);

-- Предметы на земле
CREATE TABLE IF NOT EXISTS ground_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    respawn_hours INTEGER DEFAULT 0,
    spawned_at TEXT DEFAULT (datetime('now'))
);

-- Репутация существ с игроками (кто кого кормил/атаковал)
CREATE TABLE IF NOT EXISTS creature_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creature_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    relation INTEGER DEFAULT 0,
    last_action TEXT,
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(creature_id, user_id)
);

-- Магазин
CREATE TABLE IF NOT EXISTS shop_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    price INTEGER NOT NULL,
    stock INTEGER DEFAULT -1,
    required_level INTEGER DEFAULT 0,
    required_karma INTEGER DEFAULT 0,
    UNIQUE(shop_id, item_id)
);

-- Крафт: рецепты
CREATE TABLE IF NOT EXISTS crafting_recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    result_item TEXT NOT NULL,
    result_qty INTEGER DEFAULT 1,
    ingredients TEXT NOT NULL DEFAULT '[]',
    required_location TEXT,
    required_level INTEGER DEFAULT 1,
    xp_reward INTEGER DEFAULT 10,
    is_active INTEGER DEFAULT 1
);

-- Крафт: прогресс игрока
CREATE TABLE IF NOT EXISTS user_crafting (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(user_id),
    recipe_id TEXT NOT NULL,
    times_crafted INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, recipe_id)
);

-- Гильдии
CREATE TABLE IF NOT EXISTS guilds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    leader_id INTEGER REFERENCES users(user_id),
    level INTEGER DEFAULT 1,
    xp INTEGER DEFAULT 0,
    gold INTEGER DEFAULT 0,
    motto TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now'))
);

-- Гильдии: участники
CREATE TABLE IF NOT EXISTS guild_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT REFERENCES guilds(guild_id),
    user_id INTEGER REFERENCES users(user_id),
    role TEXT DEFAULT 'member',
    contribution INTEGER DEFAULT 0,
    joined_at TEXT DEFAULT (datetime('now')),
    UNIQUE(guild_id, user_id)
);

-- Трейдинг между игроками
CREATE TABLE IF NOT EXISTS player_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_user INTEGER REFERENCES users(user_id),
    to_user INTEGER REFERENCES users(user_id),
    items_offered TEXT DEFAULT '[]',
    gold_offered INTEGER DEFAULT 0,
    items_wanted TEXT DEFAULT '[]',
    gold_wanted INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT
);

-- Эффекты статуса игроков
CREATE TABLE IF NOT EXISTS user_status_effects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(user_id),
    effect_type TEXT NOT NULL,
    potency INTEGER DEFAULT 1,
    duration INTEGER DEFAULT 3,
    applied_at TEXT DEFAULT (datetime('now')),
    source TEXT,
    UNIQUE(user_id, effect_type)
);

-- Экипировка игроков
CREATE TABLE IF NOT EXISTS user_equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(user_id),
    slot TEXT NOT NULL,
    item_id TEXT NOT NULL,
    equipped_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, slot)
);

-- Достижения
CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    achievement_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT DEFAULT '🏅',
    category TEXT DEFAULT 'general',
    requirement TEXT DEFAULT '{}',
    reward_xp INTEGER DEFAULT 50,
    reward_gold INTEGER DEFAULT 0,
    reward_item TEXT,
    is_secret INTEGER DEFAULT 0
);

-- Разблокированные достижения
CREATE TABLE IF NOT EXISTS user_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(user_id),
    achievement_id TEXT REFERENCES achievements(achievement_id),
    unlocked_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, achievement_id)
);

-- Ежедневные квесты
CREATE TABLE IF NOT EXISTS daily_quests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(user_id),
    quest_id TEXT NOT NULL,
    day TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    progress TEXT DEFAULT '{}',
    completed_at TEXT,
    UNIQUE(user_id, quest_id, day)
);

-- Спавны боссов
CREATE TABLE IF NOT EXISTS boss_spawns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    boss_id TEXT UNIQUE NOT NULL,
    creature_id TEXT NOT NULL,
    location TEXT NOT NULL,
    respawn_hours INTEGER DEFAULT 24,
    last_killed_at TEXT,
    killed_by INTEGER REFERENCES users(user_id)
);
