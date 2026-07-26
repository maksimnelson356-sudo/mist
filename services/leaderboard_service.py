import logging

from sqlalchemy import text

from database.base import get_db

logger = logging.getLogger("MIST.leaderboard")

LEADERBOARD_TYPES = {
    "level": {"name": "Уровень", "icon": "⭐", "field": "level", "order": "DESC"},
    "gold": {"name": "Золото", "icon": "💰", "field": "gold", "order": "DESC"},
    "xp": {"name": "Опыт", "icon": "📊", "field": "xp", "order": "DESC"},
    "reputation": {"name": "Репутация", "icon": "🏅", "field": "reputation", "order": "DESC"},
    "kills": {"name": "Убийства", "icon": "⚔️", "field": "kills", "order": "DESC"},
    "deaths": {"name": "Смерти", "icon": "💀", "field": "deaths", "order": "ASC"},
    "quests_done": {"name": "Квесты", "icon": "📜", "field": "quests_done", "order": "DESC"},
}


class LeaderboardService:

    def __init__(self, chronicle):
        self.chronicle = chronicle

    async def get_leaderboard(self, board_type: str, limit: int = 10) -> dict:
        info = LEADERBOARD_TYPES.get(board_type)
        if not info:
            return {"success": False, "message": "Неизвестный тип лидерборда."}

        async for db in get_db():
            order = "DESC" if info["order"] == "DESC" else "ASC"
            result = await db.execute(
                text(f"SELECT user_id, name, level, gold, xp, reputation, kills, deaths, quests_done "
                     f"FROM users WHERE is_alive = 1 "
                     f"ORDER BY {info['field']} {order} LIMIT :limit"),
                {"limit": limit},
            )
            rows = result.mappings().all()

            players = []
            for i, row in enumerate(rows, 1):
                players.append({
                    "rank": i,
                    "user_id": row["user_id"],
                    "name": row["name"],
                    "value": row[info["field"]],
                })

            return {
                "success": True,
                "board_type": board_type,
                "name": info["name"],
                "icon": info["icon"],
                "players": players,
            }

    async def get_player_rank(self, user_id: int, board_type: str) -> dict:
        info = LEADERBOARD_TYPES.get(board_type)
        if not info:
            return {"rank": 0, "total": 0}

        async for db in get_db():
            user_result = await db.execute(
                text(f"SELECT {info['field']} FROM users WHERE user_id = :uid"),
                {"uid": user_id},
            )
            user_row = user_result.mappings().first()
            if not user_row:
                return {"rank": 0, "total": 0}

            user_val = user_row[info["field"]]
            order = "DESC" if info["order"] == "DESC" else "ASC"

            if order == "DESC":
                count_result = await db.execute(
                    text(f"SELECT COUNT(*) as cnt FROM users WHERE {info['field']} > :val AND is_alive = 1"),
                    {"val": user_val},
                )
            else:
                count_result = await db.execute(
                    text(f"SELECT COUNT(*) as cnt FROM users WHERE {info['field']} < :val AND is_alive = 1"),
                    {"val": user_val},
                )

            rank = count_result.scalar() + 1

            total_result = await db.execute(
                text("SELECT COUNT(*) FROM users WHERE is_alive = 1")
            )
            total = total_result.scalar() or 0

            return {"rank": rank, "total": total, "value": user_val}

    async def get_all_boards_summary(self, user_id: int) -> dict:
        summary = {}
        for board_type, info in LEADERBOARD_TYPES.items():
            rank_info = await self.get_player_rank(user_id, board_type)
            summary[board_type] = {
                "name": info["name"],
                "icon": info["icon"],
                "rank": rank_info["rank"],
                "total": rank_info["total"],
                "value": rank_info.get("value", 0),
            }
        return summary
