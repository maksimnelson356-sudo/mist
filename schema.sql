-- MIST: Схема базы данных
-- Вселенная, которая помнит ВСЁ

-- Пользователи
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(100),
    display_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    current_location VARCHAR(100) DEFAULT 'dark_forest',
    memories INTEGER DEFAULT 0,
    karma INTEGER DEFAULT 0,
    days_in_mist INTEGER DEFAULT 0,
    is_alive BOOLEAN DEFAULT TRUE,
    extra_data JSONB DEFAULT '{}',
    -- Боевые характеристики
    hp INTEGER DEFAULT 100,
    max_hp INTEGER DEFAULT 100,
    attack INTEGER DEFAULT 10,
    defense INTEGER DEFAULT 5,
    level INTEGER DEFAULT 1,
    xp INTEGER DEFAULT 0
);

-- Инвентарь
CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    item_id VARCHAR(100) NOT NULL,
    quantity INTEGER DEFAULT 1,
    is_magic BOOLEAN DEFAULT FALSE,
    enchantments JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Все действия (ключевая таблица — память мира)
CREATE TABLE IF NOT EXISTS actions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    action_type VARCHAR(50) NOT NULL,
    action_data JSONB DEFAULT '{}',
    location VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Локации
CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    location_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    discovered BOOLEAN DEFAULT FALSE,
    discovered_by BIGINT REFERENCES users(user_id),
    discovered_at TIMESTAMP,
    connections JSONB DEFAULT '[]',
    state_data JSONB DEFAULT '{}',
    is_secret BOOLEAN DEFAULT FALSE,
    required_karma INTEGER DEFAULT 0
);

-- Существа
CREATE TABLE IF NOT EXISTS creatures (
    id SERIAL PRIMARY KEY,
    creature_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    location VARCHAR(100),
    disposition VARCHAR(20) DEFAULT 'neutral',
    memory_with_users JSONB DEFAULT '{}',
    is_alive BOOLEAN DEFAULT TRUE,
    spawn_data JSONB DEFAULT '{}',
    -- Боевые характеристики
    hp INTEGER DEFAULT 50,
    max_hp INTEGER DEFAULT 50,
    attack INTEGER DEFAULT 8,
    defense INTEGER DEFAULT 3,
    xp_reward INTEGER DEFAULT 20,
    loot_table JSONB DEFAULT '[]'
);

-- Секреты и тайны
CREATE TABLE IF NOT EXISTS secrets (
    id SERIAL PRIMARY KEY,
    secret_id VARCHAR(100) UNIQUE NOT NULL,
    secret_type VARCHAR(50) NOT NULL,
    name VARCHAR(200),
    description TEXT,
    trigger_condition JSONB DEFAULT '{}',
    reward JSONB DEFAULT '{}',
    discovered_by BIGINT REFERENCES users(user_id),
    discovered_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Мировые события
CREATE TABLE IF NOT EXISTS world_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200),
    description TEXT,
    trigger_time TIMESTAMP,
    duration_minutes INTEGER DEFAULT 60,
    is_active BOOLEAN DEFAULT FALSE,
    affected_locations JSONB DEFAULT '[]',
    event_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Предметы (описания всех возможных предметов)
CREATE TABLE IF NOT EXISTS item_templates (
    id SERIAL PRIMARY KEY,
    item_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    rarity VARCHAR(20) DEFAULT 'common',
    is_usable BOOLEAN DEFAULT FALSE,
    use_effect JSONB DEFAULT '{}',
    lore TEXT
);

-- Квесты
CREATE TABLE IF NOT EXISTS quests (
    id SERIAL PRIMARY KEY,
    quest_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    giver VARCHAR(100),
    location VARCHAR(100),
    requirements JSONB DEFAULT '{}',
    objectives JSONB DEFAULT '[]',
    rewards JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    is_repeating BOOLEAN DEFAULT FALSE,
    cooldown_hours INTEGER DEFAULT 0
);

-- Прогресс квестов игроков
CREATE TABLE IF NOT EXISTS user_quests (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    quest_id VARCHAR(100) REFERENCES quests(quest_id),
    status VARCHAR(20) DEFAULT 'active',
    progress JSONB DEFAULT '{}',
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    UNIQUE(user_id, quest_id)
);

-- Бои (лог сражений)
CREATE TABLE IF NOT EXISTS combat_log (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    creature_id VARCHAR(100),
    result VARCHAR(20) NOT NULL,
    damage_dealt INTEGER DEFAULT 0,
    damage_taken INTEGER DEFAULT 0,
    xp_gained INTEGER DEFAULT 0,
    loot_dropped JSONB DEFAULT '[]',
    duration_seconds INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Легенды (записи в энциклопедии)
CREATE TABLE IF NOT EXISTS legends (
    id SERIAL PRIMARY KEY,
    legend_id VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    discovered_by BIGINT REFERENCES users(user_id),
    discovered_at TIMESTAMP,
    times_discovered INTEGER DEFAULT 0
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_actions_user_id ON actions(user_id);
CREATE INDEX IF NOT EXISTS idx_actions_created_at ON actions(created_at);
CREATE INDEX IF NOT EXISTS idx_actions_action_type ON actions(action_type);
CREATE INDEX IF NOT EXISTS idx_inventory_user_id ON inventory(user_id);
CREATE INDEX IF NOT EXISTS idx_creatures_location ON creatures(location);
CREATE INDEX IF NOT EXISTS idx_users_current_location ON users(current_location);
CREATE INDEX IF NOT EXISTS idx_user_quests_user_id ON user_quests(user_id);
CREATE INDEX IF NOT EXISTS idx_user_quests_status ON user_quests(status);
CREATE INDEX IF NOT EXISTS idx_combat_log_user_id ON combat_log(user_id);
