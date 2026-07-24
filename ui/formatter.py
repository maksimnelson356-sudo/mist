def hp_bar(current: int, max_val: int, length: int = 10) -> str:
    if max_val <= 0:
        return "❤️" * length
    filled = min(length, round(current / max_val * length))
    empty = length - filled
    return "❤️" * filled + "🤍" * empty + f" ({current}/{max_val})"


def xp_bar(current: int, needed: int, length: int = 10) -> str:
    if needed <= 0:
        return "⭐" * length
    filled = min(length, round(current / needed * length))
    empty = length - filled
    return "⭐" * filled + "☆" * empty + f" ({current}/{needed})"


def gold_fmt(amount: int) -> str:
    if amount >= 10000:
        return f"{amount // 1000}k 🪙"
    return f"{amount} 🪙"


def location_fmt(name: str, region: str = None) -> str:
    if region:
        return f"📍 {name} [{region}]"
    return f"📍 {name}"


def level_fmt(level: int) -> str:
    return f"⭐ Ур. {level}"


def reputation_fmt(rep: int, level: str) -> str:
    return f"📊 {level} ({rep})"


def role_icon(role: str) -> str:
    return {"leader": "👑", "officer": "⭐", "member": "👤"}.get(role, "👤")


def rarity_icon(rarity: str) -> str:
    return {
        "common": "⬜",
        "uncommon": "🟢",
        "rare": "🔵",
        "epic": "🟣",
        "legendary": "🟠",
    }.get(rarity, "⬜")


def weather_icon(state: str) -> str:
    return {
        "clear": "☀️",
        "rain": "🌧️",
        "storm": "⛈️",
        "fog": "🌫️",
        "snow": "❄️",
    }.get(state, "❓")


def time_icon(period: str) -> str:
    return {
        "morning": "🌅",
        "afternoon": "☀️",
        "evening": "🌆",
        "night": "🌙",
    }.get(period, "❓")
