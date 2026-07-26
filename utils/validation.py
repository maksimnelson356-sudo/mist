from services.admin_service import is_admin


def check_admin(user_id: int) -> bool:
    return is_admin(user_id)


def sanitize_input(text: str, max_length: int = 500) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) > max_length:
        text = text[:max_length]
    dangerous = ["<script", "javascript:", "onerror=", "onload="]
    for d in dangerous:
        text = text.replace(d, "")
    return text


def validate_user_id(user_id) -> int | None:
    try:
        uid = int(user_id)
        if uid <= 0:
            return None
        return uid
    except (ValueError, TypeError):
        return None


def validate_amount(amount) -> int | None:
    try:
        a = int(amount)
        if a < 0 or a > 1_000_000:
            return None
        return a
    except (ValueError, TypeError):
        return None
