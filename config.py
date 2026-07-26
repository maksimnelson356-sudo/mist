import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = os.getenv("DB_PATH", "mist.db")

ADMIN_IDS = []
_raw_admins = os.getenv("ADMIN_IDS", "")
if _raw_admins:
    ADMIN_IDS = [int(x.strip()) for x in _raw_admins.split(",") if x.strip().isdigit()]

GUILD_CREATE_COST = 50
GUILD_MAX_NAME_LENGTH = 30
GUILD_MIN_NAME_LENGTH = 3

HEAL_HP_AMOUNT = 50

COMBAT_XP_BASE = 10
COMBAT_GOLD_BASE = 5

EXPLORATION_XP_FIRST_DISCOVERY = 50

DAILY_QUEST_COUNT = 3

SHOP_TAX_SELL = 0.1

NPC_RELATION_MIN = -100
NPC_RELATION_MAX = 100

NPC_PRICE_MULTIPLIER_MIN = 0.8
NPC_PRICE_MULTIPLIER_MAX = 1.5

WEATHER_TICK_MINUTES = 30

WORLD_EVENT_MAX_ACTIVE = 3

QUEST_MAX_ACTIVE = 5

INVENTORY_MAX_SLOTS = 50

PVP_RATING_CHANGE = 25
PVP_MIN_LEVEL = 5

CRAFT_SUCCESS_BASE_CHANCE = 0.8

CURRENCY_NAMES = {
    "gold": "Золото",
    "gems": "Камни",
    "tokens": "Токены",
}

CURRENCY_ICONS = {
    "gold": "🪙",
    "gems": "💎",
    "tokens": "🎫",
}
