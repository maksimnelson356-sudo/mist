import os
from pathlib import Path
from aiogram.types import InputFile

# -------------------------------------------------
# Asset mapping – extend as needed
# -------------------------------------------------
ASSET_MAP = {
    # Квесты
    "quest_accept": "abstract-001.svg",
    "quest_complete": "achievement.svg",
    # Эффекты
    "effect_fire": "fire.svg",
    "effect_heal": "water-drop.svg",
    "effect_poison": "poison.svg",
    # Локации (фоновые картинки)
    "location_dark_forest": "tiles/dark_forest.png",   # ← замените на ваш файл
    "location_ancient_ruins": "tiles/ancient_ruins.png",
    # NPC
    "npc_guild_master": "entities/npc_guild_master.png",
    # Level‑up
    "level_up": "abstract-002.svg",
}

def get_asset_path(key: str) -> str | None:
    """Возвращает абсолютный путь к файлу или None, если ключ не найден."""
    relative = ASSET_MAP.get(key)
    if not relative:
        return None
    # Путь от корня проекта к assets/images/
    base_path = Path(__file__).resolve().parent.parent / "assets" / "images" / relative
    return str(base_path) if base_path.is_file() else None

async def send_visual(callback, key: str, caption: str = ""):
    """
    Отправляет указанный asset как документ (SVG/PNG) в текущий чат.
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