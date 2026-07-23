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
    xp INTEGER DEFAULT 0
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
