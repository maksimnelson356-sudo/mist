import os
from pathlib import Path
from aiogram.types import InputFile

# =============================================================
# MIST — ASSET_MAP
# Все пути относительно assets/images/
# Источник иконок: game-icons.net (CC BY 3.0), Kenney (CC0)
# =============================================================

ASSET_MAP = {
    # ────────────── КВЕСТЫ ──────────────
    "quest_accept":       "ui/icons/ffffff/000000/1x1/lorc/scroll-unfurled.svg",
    "quest_complete":     "ui/icons/ffffff/000000/1x1/lorc/trophy.svg",
    "quest_fail":         "ui/icons/ffffff/000000/1x1/lorc/shattered-sword.svg",
    "quest_give":         "ui/icons/ffffff/000000/1x1/lorc/tied-scroll.svg",

    # ────────────── ЛОКАЦИИ ──────────────
    "loc_dark_forest":    "ui/icons/ffffff/000000/1x1/delapouite/forest-entrance.svg",
    "loc_riverbank":      "ui/icons/ffffff/000000/1x1/delapouite/forest-camp.svg",
    "loc_ancient_ruins":  "ui/icons/ffffff/000000/1x1/delapouite/temple-door.svg",
    "loc_fishing_village":"ui/icons/ffffff/000000/1x1/delapouite/mountain-cave.svg",
    "loc_wolf_den":       "ui/icons/ffffff/000000/1x1/lorc/wolf-head.svg",
    "loc_temple_shadows": "ui/icons/ffffff/000000/1x1/lorc/greek-temple.svg",
    "loc_crystal_cave":   "ui/icons/ffffff/000000/1x1/lorc/crystal-cluster.svg",
    "loc_white_forest":   "ui/icons/ffffff/000000/1x1/lorc/evil-tree.svg",
    "loc_library_echoes": "ui/icons/ffffff/000000/1x1/lorc/open-book.svg",
    "loc_obsidian_tower": "ui/icons/ffffff/000000/1x1/lorc/evil-tower.svg",
    "loc_tower_summit":   "ui/icons/ffffff/000000/1x1/lorc/stone-tower.svg",
    "loc_blood_meadow":   "ui/icons/ffffff/000000/1x1/delapouite/burning-forest.svg",
    "loc_shadow_market":  "ui/icons/ffffff/000000/1x1/delapouite/coins.svg",
    "loc_heart_mist":     "ui/icons/ffffff/000000/1x1/lorc/magic-swirl.svg",
    "loc_witch_swamp":    "ui/icons/ffffff/000000/1x1/lorc/poison-cloud.svg",
    "loc_forgotten_grave":"ui/icons/ffffff/000000/1x1/sbed/death-skull.svg",
    "loc_dark_harbour":   "ui/icons/ffffff/000000/1x1/lorc/campfire.svg",
    "loc_ash_fields":     "ui/icons/ffffff/000000/1x1/lorc/fire.svg",
    "loc_abandoned_mine": "ui/icons/ffffff/000000/1x1/delapouite/cave-entrance.svg",
    "loc_enchanted_grove":"ui/icons/ffffff/000000/1x1/delapouite/forest.svg",
    "loc_abandoned_camp": "ui/icons/ffffff/000000/1x1/delapouite/forest-camp.svg",
    "loc_portal_nexus":   "ui/icons/ffffff/000000/1x1/lorc/magic-gate.svg",

    # ────────────── NPC ──────────────
    "npc_merchant":       "ui/icons/ffffff/000000/1x1/delapouite/coins-pile.svg",
    "npc_elder":          "ui/icons/ffffff/000000/1x1/lorc/wizard-staff.svg",
    "npc_guard":          "ui/icons/ffffff/000000/1x1/sbed/shield.svg",
    "npc_healer":         "ui/icons/ffffff/000000/1x1/delapouite/healing.svg",
    "npc_bartender":      "ui/icons/ffffff/000000/1x1/lorc/standing-potion.svg",
    "npc_shady":          "ui/icons/ffffff/000000/1x1/lorc/skull-mask.svg",
    "npc_guild_master":   "ui/icons/ffffff/000000/1x1/lorc/crown.svg",
    "npc_quest_giver":    "ui/icons/ffffff/000000/1x1/lorc/scroll-quill.svg",

    # ────────────── МОБЫ ──────────────
    "mob_skeleton":       "ui/icons/ffffff/000000/1x1/skoll/skeleton.svg",
    "mob_zombie":         "ui/icons/ffffff/000000/1x1/delapouite/shambling-zombie.svg",
    "mob_ghost":          "ui/icons/ffffff/000000/1x1/lorc/ghost.svg",
    "mob_wolf":           "ui/icons/ffffff/000000/1x1/lorc/wolf-head.svg",
    "mob_spider":         "ui/icons/ffffff/000000/1x1/carl-olsen/spider-face.svg",
    "mob_dragon":         "ui/icons/ffffff/000000/1x1/delapouite/dragon-shield.svg",
    "mob_demon":          "ui/icons/ffffff/000000/1x1/lorc/daemon-skull.svg",
    "mob_boss":           "ui/icons/ffffff/000000/1x1/lorc/diablo-skull.svg",
    "mob_undead":         "ui/icons/ffffff/000000/1x1/skoll/raise-skeleton.svg",
    "mob_beast":          "ui/icons/ffffff/000000/1x1/lorc/beast-eye.svg",

    # ────────────── БОЙ ──────────────
    "combat_attack":      "ui/icons/ffffff/000000/1x1/lorc/crossed-swords.svg",
    "combat_defend":      "ui/icons/ffffff/000000/1x1/sbed/shield.svg",
    "combat_magic":       "ui/icons/ffffff/000000/1x1/lorc/magic-palm.svg",
    "combat_critical":    "ui/icons/ffffff/000000/1x1/lorc/bullseye.svg",
    "combat_miss":        "ui/icons/ffffff/000000/1x1/lorc/shattered-sword.svg",
    "combat_dodge":       "ui/icons/ffffff/000000/1x1/delapouite/crosshair-arrow.svg",

    # ────────────── ЭФФЕКТЫ ──────────────
    "effect_fire":        "ui/icons/ffffff/000000/1x1/sbed/fire.svg",
    "effect_ice":         "ui/icons/ffffff/000000/1x1/lorc/ice-shield.svg",
    "effect_heal":        "ui/icons/ffffff/000000/1x1/zeromancer/heart-plus.svg",
    "effect_poison":      "ui/icons/ffffff/000000/1x1/sbed/poison.svg",
    "effect_burn":        "ui/icons/ffffff/000000/1x1/lorc/flame.svg",
    "effect_bleed":       "ui/icons/ffffff/000000/1x1/lorc/heart-drop.svg",
    "effect_stun":        "ui/icons/ffffff/000000/1x1/lorc/dizzy.svg",
    "effect_haste":       "ui/icons/ffffff/000000/1x1/lorc/punch.svg",
    "effect_shield":      "ui/icons/ffffff/000000/1x1/lorc/energy-shield.svg",

    # ────────────── КЛАССЫ ──────────────
    "class_warrior":      "ui/icons/ffffff/000000/1x1/lorc/battle-axe.svg",
    "class_mage":         "ui/icons/ffffff/000000/1x1/delapouite/spell-book.svg",
    "class_scout":        "ui/icons/ffffff/000000/1x1/delapouite/bow-arrow.svg",
    "class_craftsman":    "ui/icons/ffffff/000000/1x1/delapouite/hammer.svg",

    # ────────────── ПРЕДМЕТЫ ──────────────
    "item_sword":         "ui/icons/ffffff/000000/1x1/lorc/shining-sword.svg",
    "item_shield":        "ui/icons/ffffff/000000/1x1/lorc/winged-shield.svg",
    "item_helmet":        "ui/icons/ffffff/000000/1x1/sbed/helmet.svg",
    "item_armor":         "ui/icons/ffffff/000000/1x1/lorc/layered-armor.svg",
    "item_potion":        "ui/icons/ffffff/000000/1x1/delapouite/health-potion.svg",
    "item_key":           "ui/icons/ffffff/000000/1x1/sbed/key.svg",
    "item_chest":         "ui/icons/ffffff/000000/1x1/lorc/locked-chest.svg",
    "item_scroll":        "ui/icons/ffffff/000000/1x1/lorc/scroll-unfurled.svg",
    "item_crystal":       "ui/icons/ffffff/000000/1x1/lorc/floating-crystal.svg",
    "item_coin":          "ui/icons/ffffff/000000/1x1/delapouite/coins.svg",
    "item_gold_bar":      "ui/icons/ffffff/000000/1x1/willdabeast/gold-bar.svg",
    "item_wand":          "ui/icons/ffffff/000000/1x1/lorc/crystal-wand.svg",
    "item_staff":         "ui/icons/ffffff/000000/1x1/lorc/wizard-staff.svg",
    "item_book":          "ui/icons/ffffff/000000/1x1/lorc/spell-book.svg",

    # ────────────── СТАТУСЫ / UI ──────────────
    "ui_level_up":        "ui/icons/ffffff/000000/1x1/lorc/crown.svg",
    "ui_xp":              "ui/icons/ffffff/000000/1x1/delapouite/star-medal.svg",
    "ui_gold":            "ui/icons/ffffff/000000/1x1/delapouite/coins-pile.svg",
    "ui_hp":              "ui/icons/ffffff/000000/1x1/zeromancer/heart-plus.svg",
    "ui_mp":              "ui/icons/ffffff/000000/1x1/lorc/crystal-ball.svg",
    "ui_danger":          "ui/icons/ffffff/000000/1x1/lorc/dread-skull.svg",
    "ui_safe":            "ui/icons/ffffff/000000/1x1/lorc/winged-shield.svg",
    "ui_map":             "ui/icons/ffffff/000000/1x1/lorc/treasure-map.svg",
    "ui_compass":         "ui/icons/ffffff/000000/1x1/lorc/compass.svg",
    "ui_hourglass":       "ui/icons/ffffff/000000/1x1/lorc/hourglass.svg",
    "ui_lore":            "ui/icons/ffffff/000000/1x1/lorc/evil-book.svg",
    "ui_legend":          "ui/icons/ffffff/000000/1x1/lorc/book-aura.svg",
    "ui_achievement":     "ui/icons/ffffff/000000/1x1/lorc/medal.svg",
    "ui_pvp":             "ui/icons/ffffff/000000/1x1/lorc/crossed-swords.svg",
    "ui_guild":           "ui/icons/ffffff/000000/1x1/lorc/winged-emblem.svg",
    "ui_trade":           "ui/icons/ffffff/000000/1x1/lorc/trade.svg",
    "ui_craft":           "ui/icons/ffffff/000000/1x1/delapouite/hammer.svg",
    "ui_explore":         "ui/icons/ffffff/000000/1x1/delapouite/forest-entrance.svg",
    "ui_rest":            "ui/icons/ffffff/000000/1x1/lorc/campfire.svg",
    "ui_death":           "ui/icons/ffffff/000000/1x1/sbed/death-skull.svg",
    "ui_victory":         "ui/icons/ffffff/000000/1x1/lorc/laurel-crown.svg",
    "ui_defeat":          "ui/icons/ffffff/000000/1x1/lorc/shattered-sword.svg",
    "ui_event":           "ui/icons/ffffff/000000/1x1/lorc/magic-portal.svg",
    "ui_news":            "ui/icons/ffffff/000000/1x1/lorc/scroll-quill.svg",
    "ui_warning":         "ui/icons/ffffff/000000/1x1/lorc/dread-skull.svg",
    "ui_info":            "ui/icons/ffffff/000000/1x1/lorc/third-eye.svg",
    "ui_success":         "ui/icons/ffffff/000000/1x1/lorc/justice-star.svg",
    "ui_error":           "ui/icons/ffffff/000000/1x1/lorc/broken-shield.svg",
    "ui_menu":            "ui/icons/ffffff/000000/1x1/delapouite/secret-book.svg",
    "ui_back":            "ui/icons/ffffff/000000/1x1/lorc/treasure-map.svg",

    # ────────────── ЭЛЕМЕНТЫ / СОБЫТИЯ ──────────────
    "event_fire":         "ui/icons/ffffff/000000/1x1/lorc/fireball.svg",
    "event_flood":        "ui/icons/ffffff/000000/1x1/lorc/waves.svg",
    "event_earthquake":   "ui/icons/ffffff/000000/1x1/lorc/mountains.svg",
    "event_storm":        "ui/icons/ffffff/000000/1x1/lorc/thunderball.svg",
    "event_mist":         "ui/icons/ffffff/000000/1x1/lorc/magic-swirl.svg",
    "event_plague":       "ui/icons/ffffff/000000/1x1/lorc/poison-cloud.svg",
    "event_invasion":     "ui/icons/ffffff/000000/1x1/lorc/skull-crossed-bones.svg",
    "event_blessing":     "ui/icons/ffffff/000000/1x1/lorc/shining-heart.svg",
    "event_curse":        "ui/icons/ffffff/000000/1x1/lorc/dread-skull.svg",

    # ────────────── СОЗДАНИЕ / РЕМЕСЛО ──────────────
    "craft_smith":        "ui/icons/ffffff/000000/1x1/delapouite/hammer.svg",
    "craft_alchemy":      "ui/icons/ffffff/000000/1x1/lorc/standing-potion.svg",
    "craft_enchant":      "ui/icons/ffffff/000000/1x1/lorc/crystal-wand.svg",
    "craft_cook":         "ui/icons/ffffff/000000/1x1/lorc/campfire.svg",

    # ────────────── ДОСТИЖЕНИЯ ──────────────
    "achieve_first_kill": "ui/icons/ffffff/000000/1x1/lorc/crossed-swords.svg",
    "achieve_explorer":   "ui/icons/ffffff/000000/1x1/delapouite/all-seeing-eye.svg",
    "achieve_wealthy":    "ui/icons/ffffff/000000/1x1/delapouite/gold-stack.svg",
    "achieve_legendary":  "ui/icons/ffffff/000000/1x1/lorc/laurel-crown.svg",
    "achieve_survivor":   "ui/icons/ffffff/000000/1x1/lorc/winged-shield.svg",
    "achieve_hunter":     "ui/icons/ffffff/000000/1x1/delapouite/hunter-eyes.svg",
    "achieve_mage":       "ui/icons/ffffff/000000/1x1/lorc/crystal-ball.svg",
    "achieve_crafter":    "ui/icons/ffffff/000000/1x1/delapouite/hammer.svg",
    "achieve_social":     "ui/icons/ffffff/000000/1x1/lorc/winged-emblem.svg",
    "achieve_quests_5":   "ui/icons/ffffff/000000/1x1/lorc/tied-scroll.svg",
    "achieve_quests_all": "ui/icons/ffffff/000000/1x1/lorc/book-aura.svg",
}

def get_asset_path(key: str) -> str | None:
    """Возвращает абсолютный путь к файлу или None, если ключ не найден."""
    relative = ASSET_MAP.get(key)
    if not relative:
        return None
    base_path = Path(__file__).resolve().parent.parent / "assets" / "images" / relative
    return str(base_path) if base_path.is_file() else None

async def send_visual(callback, key: str, caption: str = ""):
    """
    Отправляет указанный asset как документ (SVG) в текущий чат.
    :param callback: aiogram CallbackQuery
    :param key:      Ключ из ASSET_MAP
    :param caption:  Текст подписи
    """
    asset_path = get_asset_path(key)
    if not asset_path:
        return  # Не найдено – молча выходим

    await callback.bot.send_document(
        chat_id=callback.from_user.id,
        document=InputFile(asset_path),
        caption=caption,
    )
